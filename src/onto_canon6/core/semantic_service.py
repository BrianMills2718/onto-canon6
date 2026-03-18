"""Service layer for the Phase 13 semantic canonicalization slice.

This service repairs promoted graph state deterministically through pack-driven
canonicalization metadata. It is intentionally narrow:

1. it acts on already-promoted assertions, not raw extraction output;
2. it canonicalizes only predicate and role identifiers in the first slice;
3. it validates rewritten state before persisting it;
4. it records an explicit repair event whenever the graph is rewritten.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Mapping

from pydantic import JsonValue, TypeAdapter

from ..config import get_config
from ..ontology_runtime import canonical_assertion_body, load_effective_profile, validate_assertion_payload
from ..ontology_runtime.loaders import LoadedOntologyPack
from .graph_service import CanonicalGraphService
from .graph_store import CanonicalGraphStore, CanonicalGraphStoreError, CanonicalGraphStoreNotFoundError
from .semantic_models import (
    PromotedGraphRecanonicalizationEventRecord,
    SemanticCanonicalizationResult,
)
from .semantic_store import (
    SemanticCanonicalizationStore,
    SemanticCanonicalizationStoreConflictError,
    SemanticCanonicalizationStoreError,
    SemanticCanonicalizationStoreNotFoundError,
)

logger = logging.getLogger(__name__)
_JSON_OBJECT_ADAPTER: TypeAdapter[dict[str, JsonValue]] = TypeAdapter(dict[str, JsonValue])


class SemanticCanonicalizationError(RuntimeError):
    """Base error for semantic canonicalization failures."""


class SemanticCanonicalizationNotFoundError(SemanticCanonicalizationError):
    """Raised when a requested promoted assertion does not exist."""


class SemanticCanonicalizationConflictError(SemanticCanonicalizationError):
    """Raised when semantic repair cannot safely canonicalize the graph state."""


class SemanticCanonicalizationService:
    """Canonicalize and repair promoted assertions through ontology-pack metadata."""

    def __init__(
        self,
        *,
        db_path: Path | None = None,
        overlay_root: Path | None = None,
    ) -> None:
        """Create the semantic repair service over the configured store."""

        config = get_config()
        resolved_db_path = db_path or config.review_db_path()
        self._overlay_root = overlay_root or config.overlay_root()
        self._graph_service = CanonicalGraphService(db_path=resolved_db_path)
        self._graph_store = CanonicalGraphStore(resolved_db_path)
        self._store = SemanticCanonicalizationStore(resolved_db_path)

    @property
    def db_path(self) -> Path:
        """Return the SQLite path shared with the promoted graph."""

        return self._store.db_path

    def recanonicalize_promoted_assertion(
        self,
        *,
        assertion_id: str,
        actor_id: str,
        reason: str | None = None,
    ) -> SemanticCanonicalizationResult:
        """Recanonicalize one promoted assertion and persist the rewrite if needed."""

        normalized_assertion_id = _require_non_empty(assertion_id, field_name="assertion_id")
        normalized_actor_id = _require_non_empty(actor_id, field_name="actor_id")
        normalized_reason = reason.strip() if reason is not None else None
        try:
            with self._store.transaction() as conn:
                promotion = self._graph_store.get_promotion_result(
                    conn,
                    assertion_id=normalized_assertion_id,
                )
                profile = load_effective_profile(
                    promotion.assertion.profile.profile_id,
                    promotion.assertion.profile.profile_version,
                    overlay_root=self._overlay_root,
                )
                if profile.pack is None:
                    raise SemanticCanonicalizationConflictError(
                        "semantic canonicalization requires a profile with an ontology pack"
                    )
                rewritten_body = _canonicalize_body(
                    promotion.assertion.normalized_body,
                    pack=profile.pack,
                )
                validation_outcome = validate_assertion_payload(
                    rewritten_body,
                    profile=profile,
                )
                if validation_outcome.hard_errors:
                    codes = ", ".join(finding.code for finding in validation_outcome.hard_errors)
                    raise SemanticCanonicalizationConflictError(
                        "recanonicalized assertion still fails validation: "
                        f"{promotion.assertion.assertion_id} [{codes}]"
                    )
                if _is_already_canonical(
                    before_body=promotion.assertion.normalized_body,
                    after_body=rewritten_body,
                    current_role_fillers=promotion.role_fillers,
                ):
                    return SemanticCanonicalizationResult(
                        status="already_canonical",
                        assertion=promotion.assertion,
                        role_fillers=promotion.role_fillers,
                        validation_outcome=validation_outcome,
                        event=None,
                    )
                self._store.rewrite_promoted_assertion(
                    conn,
                    assertion_id=normalized_assertion_id,
                    predicate=_require_predicate(rewritten_body),
                    normalized_body=rewritten_body,
                )
                event = self._store.insert_event(
                    conn,
                    assertion_id=normalized_assertion_id,
                    actor_id=normalized_actor_id,
                    reason=normalized_reason,
                    before_predicate=promotion.assertion.predicate,
                    before_body=promotion.assertion.normalized_body,
                    after_predicate=_require_predicate(rewritten_body),
                    after_body=rewritten_body,
                )
                updated = self._graph_store.get_promotion_result(
                    conn,
                    assertion_id=normalized_assertion_id,
                )
        except SemanticCanonicalizationConflictError:
            raise
        except CanonicalGraphStoreNotFoundError as exc:
            raise SemanticCanonicalizationNotFoundError(str(exc)) from exc
        except CanonicalGraphStoreError as exc:
            raise SemanticCanonicalizationError(str(exc)) from exc
        except (SemanticCanonicalizationStoreNotFoundError,) as exc:
            raise SemanticCanonicalizationNotFoundError(str(exc)) from exc
        except SemanticCanonicalizationStoreConflictError as exc:
            raise SemanticCanonicalizationConflictError(str(exc)) from exc
        except SemanticCanonicalizationStoreError as exc:
            raise SemanticCanonicalizationError(str(exc)) from exc

        logger.info(
            "semantic canonicalization completed assertion_id=%s actor_id=%s event_id=%s",
            normalized_assertion_id,
            normalized_actor_id,
            event.event_id,
        )
        return SemanticCanonicalizationResult(
            status="rewritten",
            assertion=updated.assertion,
            role_fillers=updated.role_fillers,
            validation_outcome=validation_outcome,
            event=event,
        )

    def list_recanonicalization_events(
        self,
        *,
        assertion_id: str | None = None,
    ) -> list[PromotedGraphRecanonicalizationEventRecord]:
        """List persisted repair events, optionally for one assertion."""

        normalized_assertion_id = (
            _require_non_empty(assertion_id, field_name="assertion_id")
            if assertion_id is not None
            else None
        )
        with self._store.transaction() as conn:
            return self._store.list_events(conn, assertion_id=normalized_assertion_id)


def _canonicalize_body(
    body: Mapping[str, object],
    *,
    pack: LoadedOntologyPack,
) -> dict[str, JsonValue]:
    """Return the pack-canonical predicate and role identifiers for one body."""

    canonical_body = canonical_assertion_body(body)
    predicate = canonical_body.get("predicate")
    if not isinstance(predicate, str) or not predicate.strip():
        raise SemanticCanonicalizationConflictError("promoted assertion is missing predicate")
    roles_obj = canonical_body.get("roles")
    if not isinstance(roles_obj, dict) or not roles_obj:
        raise SemanticCanonicalizationConflictError("promoted assertion is missing roles")
    canonical_roles: dict[str, object] = {}
    for role_id, fillers_obj in roles_obj.items():
        if not isinstance(role_id, str) or not role_id.strip():
            raise SemanticCanonicalizationConflictError("promoted assertion contains blank role id")
        if not isinstance(fillers_obj, list) or not fillers_obj:
            raise SemanticCanonicalizationConflictError(
                f"promoted assertion contains empty role list: {role_id!r}"
            )
        canonical_role_id = _canonicalize_role(role_id, pack=pack)
        existing = canonical_roles.get(canonical_role_id)
        if existing is None:
            canonical_roles[canonical_role_id] = list(fillers_obj)
            continue
        if not isinstance(existing, list):
            raise SemanticCanonicalizationConflictError(
                f"internal canonical role aggregation failed for {canonical_role_id}"
            )
        existing.extend(fillers_obj)
    canonical_body["predicate"] = _canonicalize_predicate(predicate, pack=pack)
    canonical_body["roles"] = canonical_roles
    return _JSON_OBJECT_ADAPTER.validate_python(canonical_body)


def _canonicalize_predicate(
    predicate: str,
    *,
    pack: LoadedOntologyPack,
) -> str:
    """Resolve one predicate into the pack-canonical identifier."""

    normalized_key = _normalize_lookup_key(predicate)
    canonical = pack.predicate_aliases.get(normalized_key)
    if canonical is None:
        raise SemanticCanonicalizationConflictError(
            f"cannot canonicalize predicate: {predicate}"
        )
    return canonical


def _canonicalize_role(
    role_id: str,
    *,
    pack: LoadedOntologyPack,
) -> str:
    """Resolve one role identifier into the pack-canonical runtime role id."""

    normalized_key = _normalize_lookup_key(role_id)
    canonical = pack.role_aliases.get(normalized_key)
    if canonical is None:
        raise SemanticCanonicalizationConflictError(
            f"cannot canonicalize role: {role_id}"
        )
    return canonical


def _is_already_canonical(
    *,
    before_body: Mapping[str, object],
    after_body: Mapping[str, JsonValue],
    current_role_fillers: tuple[object, ...],
) -> bool:
    """Return `True` when the current promoted graph already matches the canonical body."""

    if before_body != after_body:
        return False
    expected_layout = _role_layout_from_body(after_body)
    current_layout = tuple(
        (getattr(filler, "role_id"), getattr(filler, "filler_index"))
        for filler in current_role_fillers
    )
    return current_layout == expected_layout


def _role_layout_from_body(body: Mapping[str, object]) -> tuple[tuple[str, int], ...]:
    """Return the expected `(role_id, filler_index)` layout for one normalized body."""

    roles_obj = body.get("roles")
    if not isinstance(roles_obj, dict):
        return ()
    layout: list[tuple[str, int]] = []
    for role_id, fillers_obj in sorted(roles_obj.items()):
        if not isinstance(role_id, str) or not isinstance(fillers_obj, list):
            continue
        for filler_index, _filler in enumerate(fillers_obj):
            layout.append((role_id, filler_index))
    return tuple(layout)


def _require_non_empty(value: str, *, field_name: str) -> str:
    """Reject blank string inputs at the semantic repair boundary."""

    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must be a non-empty string")
    return normalized


def _require_predicate(body: Mapping[str, object]) -> str:
    """Return the predicate from one canonicalized body or fail loudly."""

    predicate = body.get("predicate")
    if not isinstance(predicate, str) or not predicate.strip():
        raise SemanticCanonicalizationConflictError("canonicalized body is missing predicate")
    return predicate


def _normalize_lookup_key(value: str) -> str:
    """Normalize one semantic lookup token conservatively."""

    return value.strip().lower()


__all__ = [
    "SemanticCanonicalizationConflictError",
    "SemanticCanonicalizationError",
    "SemanticCanonicalizationNotFoundError",
    "SemanticCanonicalizationService",
]

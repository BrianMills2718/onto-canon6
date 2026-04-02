"""Service layer for the first canonical-graph recovery slice.

This service keeps graph recovery explicit and bounded. It does not replace the
review pipeline or invent missing identity resolution. Instead it:

1. promotes accepted candidates into durable graph assertions;
2. materializes graph entities only when the candidate already references a
   stable entity identifier;
3. leaves governance, artifact, and epistemic context on the candidate side and
   exposes them through separate report surfaces.
"""

from __future__ import annotations

import logging
from pathlib import Path
import sqlite3

from pydantic import JsonValue, TypeAdapter

from ..config import get_config
from ..pipeline import CandidateAssertionRecord, ReviewStore, ReviewStoreNotFoundError
from .graph_models import CanonicalGraphPromotionResult, PromotedGraphAssertionRecord
from .graph_store import (
    CanonicalGraphStore,
    CanonicalGraphStoreConflictError,
    CanonicalGraphStoreError,
)

logger = logging.getLogger(__name__)
_JSON_VALUE_ADAPTER: TypeAdapter[JsonValue] = TypeAdapter(JsonValue)


class CanonicalGraphPromotionError(RuntimeError):
    """Base error for Phase 11 graph-promotion failures."""


class CanonicalGraphPromotionNotFoundError(CanonicalGraphPromotionError):
    """Raised when a requested candidate or promoted assertion does not exist."""


class CanonicalGraphPromotionConflictError(CanonicalGraphPromotionError):
    """Raised when promotion conflicts with persisted review or graph state."""


class CanonicalGraphService:
    """Promote accepted candidates into the narrow durable graph target."""

    def __init__(self, *, db_path: Path | None = None) -> None:
        """Create a graph service over the configured review database."""

        config = get_config()
        resolved_db_path = db_path or config.review_db_path()
        self._review_store = ReviewStore(resolved_db_path)
        self._store = CanonicalGraphStore(resolved_db_path)

    @property
    def db_path(self) -> Path:
        """Return the SQLite path shared by review and graph state."""

        return self._store.db_path

    def promote_candidate(
        self,
        *,
        candidate_id: str,
        promoted_by: str,
    ) -> CanonicalGraphPromotionResult:
        """Promote one accepted candidate into the durable graph.

        The promotion seam is intentionally explicit. It fails loudly if the
        candidate has not already been accepted through the review workflow.
        Re-promoting the same accepted candidate is idempotent and returns the
        existing promoted assertion without mutating the original promoter.
        """

        normalized_candidate_id = _require_non_empty(candidate_id, field_name="candidate_id")
        normalized_promoted_by = _require_non_empty(promoted_by, field_name="promoted_by")
        try:
            with self._store.transaction() as conn:
                candidate = self._review_store.get_candidate_assertion(
                    conn,
                    candidate_id=normalized_candidate_id,
                )
                _require_accepted_candidate(candidate)
                existing = self._store.get_promoted_assertion_by_candidate(
                    conn,
                    source_candidate_id=normalized_candidate_id,
                )
                if existing is not None:
                    return self._store.get_promotion_result(
                        conn,
                        assertion_id=existing.assertion_id,
                    )

                assertion_id = self._store.insert_promoted_assertion(
                    conn,
                    source_candidate_id=normalized_candidate_id,
                    profile=candidate.profile,
                    predicate=_require_predicate(candidate),
                    normalized_body=candidate.normalized_payload,
                    claim_text=candidate.claim_text,
                    promoted_by=normalized_promoted_by,
                )
                _materialize_role_fillers(
                    store=self._store,
                    conn=conn,
                    candidate=candidate,
                    assertion_id=assertion_id,
                )
                promotion = self._store.get_promotion_result(conn, assertion_id=assertion_id)
        except ReviewStoreNotFoundError as exc:
            raise CanonicalGraphPromotionNotFoundError(str(exc)) from exc
        except CanonicalGraphStoreConflictError as exc:
            raise CanonicalGraphPromotionConflictError(str(exc)) from exc
        except CanonicalGraphStoreError as exc:
            raise CanonicalGraphPromotionError(str(exc)) from exc

        logger.info(
            "canonical graph promotion completed candidate_id=%s assertion_id=%s promoted_by=%s entity_count=%d filler_count=%d",
            normalized_candidate_id,
            promotion.assertion.assertion_id,
            normalized_promoted_by,
            len(promotion.entities),
            len(promotion.role_fillers),
        )
        return promotion

    def get_promoted_assertion(
        self,
        *,
        assertion_id: str,
    ) -> PromotedGraphAssertionRecord:
        """Return one promoted assertion by identifier."""

        normalized_assertion_id = _require_non_empty(assertion_id, field_name="assertion_id")
        try:
            with self._store.transaction() as conn:
                return self._store.get_promoted_assertion(conn, assertion_id=normalized_assertion_id)
        except CanonicalGraphStoreError as exc:
            raise CanonicalGraphPromotionNotFoundError(str(exc)) from exc

    def get_promotion_result(
        self,
        *,
        assertion_id: str,
    ) -> CanonicalGraphPromotionResult:
        """Return one promoted assertion together with its role fillers and entities."""

        normalized_assertion_id = _require_non_empty(assertion_id, field_name="assertion_id")
        try:
            with self._store.transaction() as conn:
                return self._store.get_promotion_result(conn, assertion_id=normalized_assertion_id)
        except CanonicalGraphStoreError as exc:
            raise CanonicalGraphPromotionNotFoundError(str(exc)) from exc

    def list_promoted_assertions(self) -> list[PromotedGraphAssertionRecord]:
        """List all promoted assertions in deterministic order."""

        with self._store.transaction() as conn:
            return self._store.list_promoted_assertions(conn)


def _require_non_empty(value: str, *, field_name: str) -> str:
    """Reject blank string inputs at the graph service boundary."""

    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must be a non-empty string")
    return normalized


def _require_accepted_candidate(candidate: CandidateAssertionRecord) -> None:
    """Require that graph promotion only accepts already-reviewed candidates."""

    if candidate.review_status != "accepted":
        raise CanonicalGraphPromotionConflictError(
            f"canonical graph promotion requires accepted candidate: {candidate.candidate_id}"
        )


def _require_predicate(candidate: CandidateAssertionRecord) -> str:
    """Return the normalized predicate from one candidate or fail loudly."""

    predicate = candidate.normalized_payload.get("predicate")
    if not isinstance(predicate, str) or not predicate.strip():
        raise CanonicalGraphPromotionConflictError(
            f"candidate is missing normalized predicate: {candidate.candidate_id}"
        )
    return predicate


def _materialize_role_fillers(
    *,
    store: CanonicalGraphStore,
    conn: sqlite3.Connection,
    candidate: CandidateAssertionRecord,
    assertion_id: str,
) -> None:
    """Persist typed role fillers and any explicit entity rows for one candidate."""

    roles_object = candidate.normalized_payload.get("roles")
    if not isinstance(roles_object, dict) or not roles_object:
        # Statement-only assertions (e.g. imported claims without entity_refs)
        # have a predicate + claim_text but no typed role fillers. They are
        # valid for promotion — skip role materialization silently.
        return

    for role_id, fillers_object in roles_object.items():
        if not isinstance(role_id, str) or not role_id.strip():
            raise CanonicalGraphPromotionConflictError(
                f"candidate contains blank role identifier: {candidate.candidate_id}"
            )
        if not isinstance(fillers_object, list) or not fillers_object:
            raise CanonicalGraphPromotionConflictError(
                f"candidate contains empty role filler list for role {role_id!r}"
            )
        for filler_index, filler_object in enumerate(fillers_object):
            _materialize_role_filler(
                store=store,
                conn=conn,
                candidate=candidate,
                assertion_id=assertion_id,
                role_id=role_id,
                filler_index=filler_index,
                filler_object=filler_object,
            )


def _materialize_role_filler(
    *,
    store: CanonicalGraphStore,
    conn: "sqlite3.Connection",
    candidate: CandidateAssertionRecord,
    assertion_id: str,
    role_id: str,
    filler_index: int,
    filler_object: object,
) -> None:
    """Persist one normalized role filler and any required entity materialization."""

    if not isinstance(filler_object, dict):
        raise CanonicalGraphPromotionConflictError(
            f"candidate contains non-object role filler at {role_id}[{filler_index}]"
        )
    filler_kind = filler_object.get("kind")
    if filler_kind == "entity":
        entity_id = filler_object.get("entity_id")
        if not isinstance(entity_id, str) or not entity_id.strip():
            raise CanonicalGraphPromotionConflictError(
                f"entity filler is missing entity_id at {role_id}[{filler_index}]"
            )
        entity_type = filler_object.get("entity_type")
        normalized_entity_type = entity_type.strip() if isinstance(entity_type, str) else None
        store.upsert_entity(
            conn,
            entity_id=entity_id.strip(),
            entity_type=normalized_entity_type,
            first_candidate_id=candidate.candidate_id,
        )
        store.insert_role_filler(
            conn,
            assertion_id=assertion_id,
            role_id=role_id,
            filler_index=filler_index,
            filler_kind="entity",
            entity_id=entity_id.strip(),
            entity_type=normalized_entity_type,
            value_kind=None,
            value=None,
        )
        return
    if filler_kind == "value":
        value_kind = filler_object.get("value_kind")
        if not isinstance(value_kind, str) or not value_kind.strip():
            raise CanonicalGraphPromotionConflictError(
                f"value filler is missing value_kind at {role_id}[{filler_index}]"
            )
        if "value" in filler_object:
            value = _JSON_VALUE_ADAPTER.validate_python(filler_object["value"])
        elif "normalized" in filler_object:
            value = _JSON_VALUE_ADAPTER.validate_python(filler_object["normalized"])
        else:
            raise CanonicalGraphPromotionConflictError(
                f"value filler is missing value payload at {role_id}[{filler_index}]"
            )
        store.insert_role_filler(
            conn,
            assertion_id=assertion_id,
            role_id=role_id,
            filler_index=filler_index,
            filler_kind="value",
            entity_id=None,
            entity_type=None,
            value_kind=value_kind.strip(),
            value=value,
        )
        return
    raise CanonicalGraphPromotionConflictError(
        f"unsupported filler kind at {role_id}[{filler_index}]: {filler_kind!r}"
    )


__all__ = [
    "CanonicalGraphPromotionConflictError",
    "CanonicalGraphPromotionError",
    "CanonicalGraphPromotionNotFoundError",
    "CanonicalGraphService",
]

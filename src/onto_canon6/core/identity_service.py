"""Service layer for the first stable-identity slice.

This service keeps identity work explicit and bounded. It does not attempt
automatic entity linking. Instead it:

1. creates stable local identities over promoted entities;
2. reuses those identities deterministically for repeated promoted entity ids;
3. attaches alias memberships explicitly;
4. records external references explicitly as attached or unresolved state.
"""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path
import sqlite3

from ..config import get_config
from .graph_store import CanonicalGraphStore, CanonicalGraphStoreError, CanonicalGraphStoreNotFoundError
from .identity_models import (
    ExternalReferenceStatus,
    GraphExternalReferenceRecord,
    GraphIdentityMembershipRecord,
    IdentityBundleRecord,
)
from .identity_store import (
    IdentityStore,
    IdentityStoreConflictError,
    IdentityStoreError,
    IdentityStoreNotFoundError,
)

logger = logging.getLogger(__name__)


class IdentityError(RuntimeError):
    """Base error for stable-identity failures."""


class IdentityNotFoundError(IdentityError):
    """Raised when a requested entity or identity does not exist."""


class IdentityConflictError(IdentityError):
    """Raised when identity state conflicts with existing persisted data."""


class IdentityService:
    """Create and inspect stable local identities over promoted entities."""

    def __init__(self, *, db_path: Path | None = None) -> None:
        """Create an identity service over the configured review database."""

        config = get_config()
        resolved_db_path = db_path or config.review_db_path()
        self._graph_store = CanonicalGraphStore(resolved_db_path)
        self._store = IdentityStore(resolved_db_path)

    @property
    def db_path(self) -> Path:
        """Return the SQLite path shared with graph state."""

        return self._store.db_path

    def create_identity_for_entity(
        self,
        *,
        entity_id: str,
        created_by: str,
        display_label: str | None = None,
    ) -> IdentityBundleRecord:
        """Create or reuse the stable identity for one promoted entity id."""

        normalized_entity_id = _require_non_empty(entity_id, field_name="entity_id")
        normalized_created_by = _require_non_empty(created_by, field_name="created_by")
        normalized_display_label = display_label.strip() if display_label is not None else None
        identity_id = f"gid_{_short_digest(normalized_entity_id)}"
        try:
            with self._store.transaction() as conn:
                self._graph_store.get_promoted_entity(conn, entity_id=normalized_entity_id)
                existing_membership = self._store.get_membership_for_entity(
                    conn,
                    entity_id=normalized_entity_id,
                )
                if existing_membership is not None:
                    return self.get_identity_bundle(identity_id=existing_membership.identity_id)
                self._store.insert_identity(
                    conn,
                    identity_id=identity_id,
                    identity_kind="entity",
                    display_label=normalized_display_label if normalized_display_label else None,
                    created_by=normalized_created_by,
                )
                self._store.insert_membership(
                    conn,
                    identity_id=identity_id,
                    entity_id=normalized_entity_id,
                    membership_kind="canonical",
                    attached_by=normalized_created_by,
                )
                bundle = _build_identity_bundle(
                    identity_store=self._store,
                    graph_store=self._graph_store,
                    conn=conn,
                    identity_id=identity_id,
                )
        except CanonicalGraphStoreNotFoundError as exc:
            raise IdentityNotFoundError(str(exc)) from exc
        except IdentityStoreNotFoundError as exc:
            raise IdentityNotFoundError(str(exc)) from exc
        except IdentityStoreConflictError as exc:
            raise IdentityConflictError(str(exc)) from exc
        except (CanonicalGraphStoreError, IdentityStoreError) as exc:
            raise IdentityError(str(exc)) from exc

        logger.info(
            "identity created or reused entity_id=%s identity_id=%s",
            normalized_entity_id,
            bundle.identity.identity_id,
        )
        return bundle

    def attach_entity_alias(
        self,
        *,
        identity_id: str,
        entity_id: str,
        attached_by: str,
    ) -> GraphIdentityMembershipRecord:
        """Attach another promoted entity id as an explicit alias membership."""

        normalized_identity_id = _require_non_empty(identity_id, field_name="identity_id")
        normalized_entity_id = _require_non_empty(entity_id, field_name="entity_id")
        normalized_attached_by = _require_non_empty(attached_by, field_name="attached_by")
        try:
            with self._store.transaction() as conn:
                self._store.get_identity(conn, identity_id=normalized_identity_id)
                self._graph_store.get_promoted_entity(conn, entity_id=normalized_entity_id)
                membership = self._store.insert_membership(
                    conn,
                    identity_id=normalized_identity_id,
                    entity_id=normalized_entity_id,
                    membership_kind="alias",
                    attached_by=normalized_attached_by,
                )
        except (CanonicalGraphStoreNotFoundError, IdentityStoreNotFoundError) as exc:
            raise IdentityNotFoundError(str(exc)) from exc
        except IdentityStoreConflictError as exc:
            raise IdentityConflictError(str(exc)) from exc
        except (CanonicalGraphStoreError, IdentityStoreError) as exc:
            raise IdentityError(str(exc)) from exc

        logger.info(
            "identity alias attached identity_id=%s entity_id=%s",
            normalized_identity_id,
            normalized_entity_id,
        )
        return membership

    def attach_external_reference(
        self,
        *,
        identity_id: str,
        provider: str,
        external_id: str,
        attached_by: str,
        reference_label: str | None = None,
    ) -> GraphExternalReferenceRecord:
        """Attach one explicit external reference to an identity."""

        return self._insert_external_reference(
            identity_id=identity_id,
            provider=provider,
            reference_status="attached",
            external_id=external_id,
            reference_label=reference_label,
            unresolved_note=None,
            attached_by=attached_by,
        )

    def record_unresolved_external_reference(
        self,
        *,
        identity_id: str,
        provider: str,
        unresolved_note: str,
        attached_by: str,
    ) -> GraphExternalReferenceRecord:
        """Persist one explicit unresolved external-reference record."""

        return self._insert_external_reference(
            identity_id=identity_id,
            provider=provider,
            reference_status="unresolved",
            external_id=None,
            reference_label=None,
            unresolved_note=unresolved_note,
            attached_by=attached_by,
        )

    def list_identities(self) -> list[IdentityBundleRecord]:
        """List identity bundles in deterministic order."""

        with self._store.transaction() as conn:
            identities = self._store.list_identities(conn)
            return [
                _build_identity_bundle(
                    identity_store=self._store,
                    graph_store=self._graph_store,
                    conn=conn,
                    identity_id=identity.identity_id,
                )
                for identity in identities
            ]

    def get_identity_bundle(self, *, identity_id: str) -> IdentityBundleRecord:
        """Return one identity bundle by identifier."""

        normalized_identity_id = _require_non_empty(identity_id, field_name="identity_id")
        try:
            with self._store.transaction() as conn:
                return _build_identity_bundle(
                    identity_store=self._store,
                    graph_store=self._graph_store,
                    conn=conn,
                    identity_id=normalized_identity_id,
                )
        except IdentityStoreNotFoundError as exc:
            raise IdentityNotFoundError(str(exc)) from exc
        except (CanonicalGraphStoreError, IdentityStoreError) as exc:
            raise IdentityError(str(exc)) from exc

    def _insert_external_reference(
        self,
        *,
        identity_id: str,
        provider: str,
        reference_status: ExternalReferenceStatus,
        external_id: str | None,
        reference_label: str | None,
        unresolved_note: str | None,
        attached_by: str,
    ) -> GraphExternalReferenceRecord:
        """Persist one explicit external-reference record."""

        normalized_identity_id = _require_non_empty(identity_id, field_name="identity_id")
        normalized_provider = _require_non_empty(provider, field_name="provider")
        normalized_attached_by = _require_non_empty(attached_by, field_name="attached_by")
        normalized_external_id = external_id.strip() if external_id is not None else None
        normalized_reference_label = (
            reference_label.strip() if reference_label is not None else None
        )
        normalized_unresolved_note = (
            unresolved_note.strip() if unresolved_note is not None else None
        )
        if reference_status == "attached":
            if normalized_external_id is None or not normalized_external_id:
                raise ValueError("attached external references require external_id")
            if normalized_unresolved_note is not None:
                raise ValueError("attached external references must not set unresolved_note")
        if reference_status == "unresolved":
            if normalized_unresolved_note is None or not normalized_unresolved_note:
                raise ValueError("unresolved external references require unresolved_note")
            if normalized_external_id is not None:
                raise ValueError("unresolved external references must not set external_id")

        try:
            with self._store.transaction() as conn:
                self._store.get_identity(conn, identity_id=normalized_identity_id)
                record = self._store.insert_external_reference(
                    conn,
                    identity_id=normalized_identity_id,
                    provider=normalized_provider,
                    reference_status=reference_status,
                    external_id=normalized_external_id,
                    reference_label=(
                        normalized_reference_label if normalized_reference_label else None
                    ),
                    unresolved_note=(
                        normalized_unresolved_note if normalized_unresolved_note else None
                    ),
                    attached_by=normalized_attached_by,
                )
        except IdentityStoreNotFoundError as exc:
            raise IdentityNotFoundError(str(exc)) from exc
        except IdentityStoreConflictError as exc:
            raise IdentityConflictError(str(exc)) from exc
        except IdentityStoreError as exc:
            raise IdentityError(str(exc)) from exc

        logger.info(
            "identity external reference persisted identity_id=%s provider=%s status=%s",
            normalized_identity_id,
            normalized_provider,
            reference_status,
        )
        return record


def _build_identity_bundle(
    *,
    identity_store: IdentityStore,
    graph_store: CanonicalGraphStore,
    conn: sqlite3.Connection,
    identity_id: str,
) -> IdentityBundleRecord:
    """Assemble one identity bundle from persisted identity and graph state."""

    identity = identity_store.get_identity(conn, identity_id=identity_id)
    memberships = identity_store.list_memberships_for_identity(conn, identity_id=identity_id)
    promoted_entities = tuple(
        graph_store.get_promoted_entity(conn, entity_id=membership.entity_id)
        for membership in memberships
    )
    external_references = identity_store.list_external_references_for_identity(
        conn,
        identity_id=identity_id,
    )
    return IdentityBundleRecord(
        identity=identity,
        memberships=memberships,
        promoted_entities=promoted_entities,
        external_references=external_references,
    )


def _require_non_empty(value: str, *, field_name: str) -> str:
    """Reject blank string inputs at the identity service boundary."""

    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must be a non-empty string")
    return normalized


def _short_digest(value: str) -> str:
    """Return a short deterministic digest for stable identity identifiers."""

    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:24]


__all__ = [
    "IdentityConflictError",
    "IdentityError",
    "IdentityNotFoundError",
    "IdentityService",
]

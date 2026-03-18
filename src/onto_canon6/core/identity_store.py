"""SQLite persistence for the first stable-identity slice.

This store keeps Phase 12 bounded and explicit. It owns:

1. local identity rows over promoted entities;
2. explicit identity memberships for promoted entity ids;
3. explicit external-reference records with attached or unresolved state.
"""

from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
import logging
from pathlib import Path
import sqlite3
from typing import Iterator
import uuid

from .identity_models import (
    ExternalReferenceStatus,
    GraphExternalReferenceRecord,
    GraphIdentityMembershipRecord,
    GraphIdentityRecord,
    IdentityKind,
    IdentityMembershipKind,
)

logger = logging.getLogger(__name__)


class IdentityStoreError(RuntimeError):
    """Base error for persisted identity failures."""


class IdentityStoreNotFoundError(IdentityStoreError):
    """Raised when a requested identity row does not exist."""


class IdentityStoreConflictError(IdentityStoreError):
    """Raised when a write conflicts with persisted identity state."""


class IdentityStore:
    """Persist the narrow stable-identity slice in SQLite."""

    def __init__(self, db_path: Path) -> None:
        """Initialize the identity store and ensure its schema exists."""

        self._db_path = db_path.resolve()
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    @property
    def db_path(self) -> Path:
        """Return the SQLite path used by this store."""

        return self._db_path

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        """Yield one transactional SQLite connection."""

        conn = self._connect()
        try:
            with conn:
                yield conn
        finally:
            conn.close()

    def insert_identity(
        self,
        conn: sqlite3.Connection,
        *,
        identity_id: str,
        identity_kind: IdentityKind,
        display_label: str | None,
        created_by: str,
    ) -> GraphIdentityRecord:
        """Insert one identity row or reuse the existing identical row."""

        existing = conn.execute(
            """
            SELECT
                identity_id,
                identity_kind,
                display_label,
                created_by,
                created_at
            FROM graph_identities
            WHERE identity_id = ?
            """,
            (identity_id,),
        ).fetchone()
        if existing is not None:
            existing_label = (
                str(existing["display_label"])
                if existing["display_label"] is not None
                else None
            )
            if (
                str(existing["identity_kind"]) != identity_kind
                or existing_label != display_label
                or str(existing["created_by"]) != created_by
            ):
                raise IdentityStoreConflictError(
                    f"identity already exists with different content: {identity_id}"
                )
            return self._hydrate_identity(existing)

        created_at = _now_iso()
        conn.execute(
            """
            INSERT INTO graph_identities(
                identity_id,
                identity_kind,
                display_label,
                created_by,
                created_at
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (identity_id, identity_kind, display_label, created_by, created_at),
        )
        logger.info(
            "identity persisted identity_id=%s identity_kind=%s created_by=%s",
            identity_id,
            identity_kind,
            created_by,
        )
        return GraphIdentityRecord(
            identity_id=identity_id,
            identity_kind=identity_kind,
            display_label=display_label,
            created_by=created_by,
            created_at=created_at,
        )

    def get_identity(
        self,
        conn: sqlite3.Connection,
        *,
        identity_id: str,
    ) -> GraphIdentityRecord:
        """Return one identity row by identifier."""

        row = conn.execute(
            """
            SELECT
                identity_id,
                identity_kind,
                display_label,
                created_by,
                created_at
            FROM graph_identities
            WHERE identity_id = ?
            """,
            (identity_id,),
        ).fetchone()
        if row is None:
            raise IdentityStoreNotFoundError(f"identity not found: {identity_id}")
        return self._hydrate_identity(row)

    def list_identities(self, conn: sqlite3.Connection) -> list[GraphIdentityRecord]:
        """List identities in deterministic order."""

        rows = conn.execute(
            """
            SELECT
                identity_id,
                identity_kind,
                display_label,
                created_by,
                created_at
            FROM graph_identities
            ORDER BY created_at, identity_id
            """
        ).fetchall()
        return [self._hydrate_identity(row) for row in rows]

    def insert_membership(
        self,
        conn: sqlite3.Connection,
        *,
        identity_id: str,
        entity_id: str,
        membership_kind: IdentityMembershipKind,
        attached_by: str,
    ) -> GraphIdentityMembershipRecord:
        """Insert one identity membership idempotently."""

        existing = conn.execute(
            """
            SELECT
                identity_id,
                entity_id,
                membership_kind,
                attached_by,
                attached_at
            FROM graph_identity_memberships
            WHERE entity_id = ?
            """,
            (entity_id,),
        ).fetchone()
        if existing is not None:
            record = self._hydrate_membership(existing)
            if record.identity_id != identity_id:
                raise IdentityStoreConflictError(
                    f"entity is already attached to a different identity: {entity_id}"
                )
            if record.membership_kind != membership_kind or record.attached_by != attached_by:
                raise IdentityStoreConflictError(
                    "identity membership already exists with different content"
                )
            return record

        attached_at = _now_iso()
        conn.execute(
            """
            INSERT INTO graph_identity_memberships(
                identity_id,
                entity_id,
                membership_kind,
                attached_by,
                attached_at
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (identity_id, entity_id, membership_kind, attached_by, attached_at),
        )
        logger.info(
            "identity membership persisted identity_id=%s entity_id=%s membership_kind=%s",
            identity_id,
            entity_id,
            membership_kind,
        )
        return GraphIdentityMembershipRecord(
            identity_id=identity_id,
            entity_id=entity_id,
            membership_kind=membership_kind,
            attached_by=attached_by,
            attached_at=attached_at,
        )

    def get_membership_for_entity(
        self,
        conn: sqlite3.Connection,
        *,
        entity_id: str,
    ) -> GraphIdentityMembershipRecord | None:
        """Return the membership for one entity id, if any."""

        row = conn.execute(
            """
            SELECT
                identity_id,
                entity_id,
                membership_kind,
                attached_by,
                attached_at
            FROM graph_identity_memberships
            WHERE entity_id = ?
            """,
            (entity_id,),
        ).fetchone()
        if row is None:
            return None
        return self._hydrate_membership(row)

    def list_memberships_for_identity(
        self,
        conn: sqlite3.Connection,
        *,
        identity_id: str,
    ) -> tuple[GraphIdentityMembershipRecord, ...]:
        """List memberships for one identity in deterministic order."""

        rows = conn.execute(
            """
            SELECT
                identity_id,
                entity_id,
                membership_kind,
                attached_by,
                attached_at
            FROM graph_identity_memberships
            WHERE identity_id = ?
            ORDER BY
                CASE membership_kind WHEN 'canonical' THEN 0 ELSE 1 END,
                attached_at,
                entity_id
            """,
            (identity_id,),
        ).fetchall()
        return tuple(self._hydrate_membership(row) for row in rows)

    def insert_external_reference(
        self,
        conn: sqlite3.Connection,
        *,
        identity_id: str,
        provider: str,
        reference_status: ExternalReferenceStatus,
        external_id: str | None,
        reference_label: str | None,
        unresolved_note: str | None,
        attached_by: str,
    ) -> GraphExternalReferenceRecord:
        """Insert one external-reference record idempotently."""

        rows = conn.execute(
            """
            SELECT
                reference_id,
                identity_id,
                provider,
                reference_status,
                external_id,
                reference_label,
                unresolved_note,
                attached_by,
                attached_at
            FROM graph_external_references
            WHERE identity_id = ?
              AND provider = ?
            ORDER BY attached_at, reference_id
            """,
            (identity_id, provider),
        ).fetchall()
        for row in rows:
            record = self._hydrate_external_reference(row)
            if (
                record.reference_status == reference_status
                and record.external_id == external_id
                and record.reference_label == reference_label
                and record.unresolved_note == unresolved_note
                and record.attached_by == attached_by
            ):
                return record

        reference_id = f"gref_{uuid.uuid4().hex[:24]}"
        attached_at = _now_iso()
        conn.execute(
            """
            INSERT INTO graph_external_references(
                reference_id,
                identity_id,
                provider,
                reference_status,
                external_id,
                reference_label,
                unresolved_note,
                attached_by,
                attached_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                reference_id,
                identity_id,
                provider,
                reference_status,
                external_id,
                reference_label,
                unresolved_note,
                attached_by,
                attached_at,
            ),
        )
        logger.info(
            "external reference persisted identity_id=%s provider=%s reference_status=%s",
            identity_id,
            provider,
            reference_status,
        )
        return GraphExternalReferenceRecord(
            reference_id=reference_id,
            identity_id=identity_id,
            provider=provider,
            reference_status=reference_status,
            external_id=external_id,
            reference_label=reference_label,
            unresolved_note=unresolved_note,
            attached_by=attached_by,
            attached_at=attached_at,
        )

    def list_external_references_for_identity(
        self,
        conn: sqlite3.Connection,
        *,
        identity_id: str,
    ) -> tuple[GraphExternalReferenceRecord, ...]:
        """List external-reference records for one identity."""

        rows = conn.execute(
            """
            SELECT
                reference_id,
                identity_id,
                provider,
                reference_status,
                external_id,
                reference_label,
                unresolved_note,
                attached_by,
                attached_at
            FROM graph_external_references
            WHERE identity_id = ?
            ORDER BY attached_at, reference_id
            """,
            (identity_id,),
        ).fetchall()
        return tuple(self._hydrate_external_reference(row) for row in rows)

    def _initialize(self) -> None:
        """Create the SQLite schema for the first stable-identity slice."""

        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS graph_identities(
                    identity_id TEXT PRIMARY KEY,
                    identity_kind TEXT NOT NULL,
                    display_label TEXT,
                    created_by TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS graph_identity_memberships(
                    identity_id TEXT NOT NULL REFERENCES graph_identities(identity_id) ON DELETE CASCADE,
                    entity_id TEXT NOT NULL UNIQUE REFERENCES promoted_graph_entities(entity_id) ON DELETE RESTRICT,
                    membership_kind TEXT NOT NULL,
                    attached_by TEXT NOT NULL,
                    attached_at TEXT NOT NULL,
                    PRIMARY KEY(identity_id, entity_id)
                );

                CREATE TABLE IF NOT EXISTS graph_external_references(
                    reference_id TEXT PRIMARY KEY,
                    identity_id TEXT NOT NULL REFERENCES graph_identities(identity_id) ON DELETE CASCADE,
                    provider TEXT NOT NULL,
                    reference_status TEXT NOT NULL,
                    external_id TEXT,
                    reference_label TEXT,
                    unresolved_note TEXT,
                    attached_by TEXT NOT NULL,
                    attached_at TEXT NOT NULL
                );

                CREATE UNIQUE INDEX IF NOT EXISTS idx_graph_identities_single_canonical
                    ON graph_identity_memberships(identity_id)
                    WHERE membership_kind = 'canonical';
                CREATE INDEX IF NOT EXISTS idx_graph_identity_memberships_identity
                    ON graph_identity_memberships(identity_id, attached_at, entity_id);
                CREATE INDEX IF NOT EXISTS idx_graph_external_references_identity
                    ON graph_external_references(identity_id, attached_at, reference_id);
                """
            )
        logger.info("identity store initialized db_path=%s", self._db_path)

    def _connect(self) -> sqlite3.Connection:
        """Open one SQLite connection with row access and foreign keys enabled."""

        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _hydrate_identity(self, row: sqlite3.Row) -> GraphIdentityRecord:
        """Hydrate one identity row into the typed model."""

        return GraphIdentityRecord(
            identity_id=str(row["identity_id"]),
            identity_kind=_parse_identity_kind(str(row["identity_kind"])),
            display_label=str(row["display_label"]) if row["display_label"] is not None else None,
            created_by=str(row["created_by"]),
            created_at=str(row["created_at"]),
        )

    def _hydrate_membership(self, row: sqlite3.Row) -> GraphIdentityMembershipRecord:
        """Hydrate one identity membership row into the typed model."""

        return GraphIdentityMembershipRecord(
            identity_id=str(row["identity_id"]),
            entity_id=str(row["entity_id"]),
            membership_kind=_parse_membership_kind(str(row["membership_kind"])),
            attached_by=str(row["attached_by"]),
            attached_at=str(row["attached_at"]),
        )

    def _hydrate_external_reference(
        self,
        row: sqlite3.Row,
    ) -> GraphExternalReferenceRecord:
        """Hydrate one external-reference row into the typed model."""

        return GraphExternalReferenceRecord(
            reference_id=str(row["reference_id"]),
            identity_id=str(row["identity_id"]),
            provider=str(row["provider"]),
            reference_status=_parse_reference_status(str(row["reference_status"])),
            external_id=str(row["external_id"]) if row["external_id"] is not None else None,
            reference_label=(
                str(row["reference_label"]) if row["reference_label"] is not None else None
            ),
            unresolved_note=(
                str(row["unresolved_note"]) if row["unresolved_note"] is not None else None
            ),
            attached_by=str(row["attached_by"]),
            attached_at=str(row["attached_at"]),
        )


def _now_iso() -> str:
    """Return the current timestamp in UTC ISO-8601 form."""

    return datetime.now(timezone.utc).isoformat()


def _parse_identity_kind(value: str) -> IdentityKind:
    """Parse one persisted identity kind and fail loudly on bad values."""

    if value == "entity":
        return "entity"
    raise IdentityStoreError(f"unsupported identity kind: {value}")


def _parse_membership_kind(value: str) -> IdentityMembershipKind:
    """Parse one persisted identity membership kind and fail loudly."""

    if value == "canonical":
        return "canonical"
    if value == "alias":
        return "alias"
    raise IdentityStoreError(f"unsupported identity membership kind: {value}")


def _parse_reference_status(value: str) -> ExternalReferenceStatus:
    """Parse one persisted external-reference status and fail loudly."""

    if value == "attached":
        return "attached"
    if value == "unresolved":
        return "unresolved"
    raise IdentityStoreError(f"unsupported external reference status: {value}")


__all__ = [
    "IdentityStore",
    "IdentityStoreConflictError",
    "IdentityStoreError",
    "IdentityStoreNotFoundError",
]

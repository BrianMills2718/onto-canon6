"""SQLite persistence for the first canonical-graph recovery slice.

This store introduces a narrow durable graph target without replacing the
review-oriented pipeline. It persists:

1. promoted assertions, each explicitly sourced from one accepted candidate;
2. promoted graph entities materialized only when the candidate already
   carries explicit entity identifiers;
3. typed role fillers for the promoted assertion body.

The store deliberately keeps proposal, overlay, artifact, and epistemic state
out of the graph tables. Those relationships remain candidate-centered and are
traversed through `source_candidate_id` in report surfaces.
"""

from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import logging
from pathlib import Path
import sqlite3
from typing import Iterator

from pydantic import JsonValue, TypeAdapter

from ..pipeline import ProfileRef
from .graph_models import (
    CanonicalGraphPromotionResult,
    PromotedGraphAssertionRecord,
    PromotedGraphEntityRecord,
    PromotedGraphFillerKind,
    PromotedGraphRoleFillerRecord,
)

logger = logging.getLogger(__name__)
_JSON_OBJECT_ADAPTER: TypeAdapter[dict[str, JsonValue]] = TypeAdapter(dict[str, JsonValue])
_JSON_VALUE_ADAPTER: TypeAdapter[JsonValue] = TypeAdapter(JsonValue)


class CanonicalGraphStoreError(RuntimeError):
    """Base error for persisted canonical-graph failures."""


class CanonicalGraphStoreNotFoundError(CanonicalGraphStoreError):
    """Raised when a requested promoted graph record does not exist."""


class CanonicalGraphStoreConflictError(CanonicalGraphStoreError):
    """Raised when a write would conflict with existing promoted graph state."""


class CanonicalGraphStore:
    """Persist the narrow Phase 11 canonical graph slice in SQLite."""

    def __init__(self, db_path: Path) -> None:
        """Initialize the graph store and ensure its schema exists."""

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

    def upsert_entity(
        self,
        conn: sqlite3.Connection,
        *,
        entity_id: str,
        entity_type: str | None,
        first_candidate_id: str,
    ) -> PromotedGraphEntityRecord:
        """Insert or reuse one materialized graph entity.

        Entity identifiers are already stable at this phase. The store therefore
        uses the explicit `entity_id` as the primary durable key instead of
        inventing a second internal identifier. Reuse is idempotent; conflicting
        type changes fail loudly.
        """

        existing = conn.execute(
            """
            SELECT
                entity_id,
                entity_type,
                first_candidate_id,
                created_at
            FROM promoted_graph_entities
            WHERE entity_id = ?
            """,
            (entity_id,),
        ).fetchone()
        if existing is not None:
            existing_type = str(existing["entity_type"]) if existing["entity_type"] is not None else None
            if existing_type is not None and entity_type is not None and existing_type != entity_type:
                raise CanonicalGraphStoreConflictError(
                    f"promoted entity already exists with different entity_type: {entity_id}"
                )
            return self._hydrate_entity(existing)

        created_at = _now_iso()
        conn.execute(
            """
            INSERT INTO promoted_graph_entities(
                entity_id,
                entity_type,
                first_candidate_id,
                created_at
            ) VALUES (?, ?, ?, ?)
            """,
            (entity_id, entity_type, first_candidate_id, created_at),
        )
        logger.info(
            "canonical graph entity persisted entity_id=%s entity_type=%s first_candidate_id=%s",
            entity_id,
            entity_type,
            first_candidate_id,
        )
        return PromotedGraphEntityRecord(
            entity_id=entity_id,
            entity_type=entity_type,
            first_candidate_id=first_candidate_id,
            created_at=created_at,
        )

    def insert_promoted_assertion(
        self,
        conn: sqlite3.Connection,
        *,
        source_candidate_id: str,
        profile: ProfileRef,
        predicate: str,
        normalized_body: dict[str, JsonValue],
        claim_text: str | None,
        promoted_by: str,
    ) -> str:
        """Persist one promoted assertion and return its identifier.

        Promotion is idempotent by `source_candidate_id`. Re-promoting the same
        accepted candidate returns the original durable assertion instead of
        mutating the earlier row or changing its promoter.
        """

        existing = conn.execute(
            """
            SELECT
                assertion_id,
                predicate,
                normalized_body_json,
                claim_text,
                promoted_by,
                promoted_at
            FROM promoted_graph_assertions
            WHERE source_candidate_id = ?
            """,
            (source_candidate_id,),
        ).fetchone()
        if existing is not None:
            existing_predicate = str(existing["predicate"])
            existing_claim_text = (
                str(existing["claim_text"]) if existing["claim_text"] is not None else None
            )
            existing_body = _load_json_object(
                str(existing["normalized_body_json"]),
                context=(
                    "promoted_graph_assertions"
                    f"[{source_candidate_id}].normalized_body_json"
                ),
            )
            if existing_predicate != predicate or existing_claim_text != claim_text or existing_body != normalized_body:
                raise CanonicalGraphStoreConflictError(
                    "promoted assertion already exists with different content"
                )
            return str(existing["assertion_id"])

        assertion_id = f"gassert_{_short_digest(source_candidate_id)}"
        promoted_at = _now_iso()
        conn.execute(
            """
            INSERT INTO promoted_graph_assertions(
                assertion_id,
                source_candidate_id,
                profile_id,
                profile_version,
                predicate,
                normalized_body_json,
                claim_text,
                promoted_by,
                promoted_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                assertion_id,
                source_candidate_id,
                profile.profile_id,
                profile.profile_version,
                predicate,
                _canonical_json_dumps(normalized_body),
                claim_text,
                promoted_by,
                promoted_at,
            ),
        )
        logger.info(
            "canonical graph assertion persisted assertion_id=%s source_candidate_id=%s predicate=%s promoted_by=%s",
            assertion_id,
            source_candidate_id,
            predicate,
            promoted_by,
        )
        return assertion_id

    def insert_role_filler(
        self,
        conn: sqlite3.Connection,
        *,
        assertion_id: str,
        role_id: str,
        filler_index: int,
        filler_kind: PromotedGraphFillerKind,
        entity_id: str | None,
        entity_type: str | None,
        value_kind: str | None,
        value: JsonValue | None,
    ) -> PromotedGraphRoleFillerRecord:
        """Persist one typed role filler idempotently."""

        existing = conn.execute(
            """
            SELECT
                filler_kind,
                entity_id,
                entity_type,
                value_kind,
                value_json
            FROM promoted_graph_role_fillers
            WHERE assertion_id = ?
              AND role_id = ?
              AND filler_index = ?
            """,
            (assertion_id, role_id, filler_index),
        ).fetchone()
        if existing is not None:
            existing_value = (
                _load_json_scalar_or_composite(
                    str(existing["value_json"]),
                    context=(
                        "promoted_graph_role_fillers"
                        f"[{assertion_id}:{role_id}:{filler_index}].value_json"
                    ),
                )
                if existing["value_json"] is not None
                else None
            )
            record = PromotedGraphRoleFillerRecord(
                assertion_id=assertion_id,
                role_id=role_id,
                filler_index=filler_index,
                filler_kind=_parse_filler_kind(str(existing["filler_kind"])),
                entity_id=str(existing["entity_id"]) if existing["entity_id"] is not None else None,
                entity_type=(
                    str(existing["entity_type"]) if existing["entity_type"] is not None else None
                ),
                value_kind=str(existing["value_kind"]) if existing["value_kind"] is not None else None,
                value=existing_value,
            )
            if (
                record.filler_kind != filler_kind
                or record.entity_id != entity_id
                or record.entity_type != entity_type
                or record.value_kind != value_kind
                or record.value != value
            ):
                raise CanonicalGraphStoreConflictError(
                    "promoted role filler already exists with different content"
                )
            return record

        conn.execute(
            """
            INSERT INTO promoted_graph_role_fillers(
                assertion_id,
                role_id,
                filler_index,
                filler_kind,
                entity_id,
                entity_type,
                value_kind,
                value_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                assertion_id,
                role_id,
                filler_index,
                filler_kind,
                entity_id,
                entity_type,
                value_kind,
                _canonical_json_dumps(value) if value is not None else None,
            ),
        )
        logger.info(
            "canonical graph filler persisted assertion_id=%s role_id=%s filler_index=%d filler_kind=%s",
            assertion_id,
            role_id,
            filler_index,
            filler_kind,
        )
        return PromotedGraphRoleFillerRecord(
            assertion_id=assertion_id,
            role_id=role_id,
            filler_index=filler_index,
            filler_kind=_parse_filler_kind(filler_kind),
            entity_id=entity_id,
            entity_type=entity_type,
            value_kind=value_kind,
            value=value,
        )

    def get_promoted_assertion(
        self,
        conn: sqlite3.Connection,
        *,
        assertion_id: str,
    ) -> PromotedGraphAssertionRecord:
        """Load one promoted assertion by identifier."""

        row = conn.execute(
            """
            SELECT
                assertion_id,
                source_candidate_id,
                profile_id,
                profile_version,
                predicate,
                normalized_body_json,
                claim_text,
                promoted_by,
                promoted_at
            FROM promoted_graph_assertions
            WHERE assertion_id = ?
            """,
            (assertion_id,),
        ).fetchone()
        if row is None:
            raise CanonicalGraphStoreNotFoundError(f"promoted assertion not found: {assertion_id}")
        return self._hydrate_assertion(row)

    def get_promoted_entity(
        self,
        conn: sqlite3.Connection,
        *,
        entity_id: str,
    ) -> PromotedGraphEntityRecord:
        """Return one materialized promoted entity row by identifier."""

        row = conn.execute(
            """
            SELECT
                entity_id,
                entity_type,
                first_candidate_id,
                created_at
            FROM promoted_graph_entities
            WHERE entity_id = ?
            """,
            (entity_id,),
        ).fetchone()
        if row is None:
            raise CanonicalGraphStoreNotFoundError(f"promoted entity not found: {entity_id}")
        return self._hydrate_entity(row)

    def get_promoted_assertion_by_candidate(
        self,
        conn: sqlite3.Connection,
        *,
        source_candidate_id: str,
    ) -> PromotedGraphAssertionRecord | None:
        """Return the promoted assertion for one source candidate, if present."""

        row = conn.execute(
            """
            SELECT
                assertion_id,
                source_candidate_id,
                profile_id,
                profile_version,
                predicate,
                normalized_body_json,
                claim_text,
                promoted_by,
                promoted_at
            FROM promoted_graph_assertions
            WHERE source_candidate_id = ?
            """,
            (source_candidate_id,),
        ).fetchone()
        if row is None:
            return None
        return self._hydrate_assertion(row)

    def list_promoted_assertions(self, conn: sqlite3.Connection) -> list[PromotedGraphAssertionRecord]:
        """List promoted assertions in deterministic order."""

        rows = conn.execute(
            """
            SELECT
                assertion_id,
                source_candidate_id,
                profile_id,
                profile_version,
                predicate,
                normalized_body_json,
                claim_text,
                promoted_by,
                promoted_at
            FROM promoted_graph_assertions
            ORDER BY promoted_at, assertion_id
            """
        ).fetchall()
        return [self._hydrate_assertion(row) for row in rows]

    def list_entities_for_assertion(
        self,
        conn: sqlite3.Connection,
        *,
        assertion_id: str,
    ) -> tuple[PromotedGraphEntityRecord, ...]:
        """List materialized entities referenced by one promoted assertion."""

        rows = conn.execute(
            """
            SELECT DISTINCT
                e.entity_id,
                e.entity_type,
                e.first_candidate_id,
                e.created_at
            FROM promoted_graph_entities e
            JOIN promoted_graph_role_fillers rf
              ON rf.entity_id = e.entity_id
            WHERE rf.assertion_id = ?
            ORDER BY e.created_at, e.entity_id
            """,
            (assertion_id,),
        ).fetchall()
        return tuple(self._hydrate_entity(row) for row in rows)

    def list_role_fillers_for_assertion(
        self,
        conn: sqlite3.Connection,
        *,
        assertion_id: str,
    ) -> tuple[PromotedGraphRoleFillerRecord, ...]:
        """List persisted role fillers for one promoted assertion."""

        rows = conn.execute(
            """
            SELECT
                assertion_id,
                role_id,
                filler_index,
                filler_kind,
                entity_id,
                entity_type,
                value_kind,
                value_json
            FROM promoted_graph_role_fillers
            WHERE assertion_id = ?
            ORDER BY role_id, filler_index
            """,
            (assertion_id,),
        ).fetchall()
        return tuple(self._hydrate_role_filler(row) for row in rows)

    def get_promotion_result(
        self,
        conn: sqlite3.Connection,
        *,
        assertion_id: str,
    ) -> CanonicalGraphPromotionResult:
        """Return one promoted assertion bundle from persisted graph tables."""

        assertion = self.get_promoted_assertion(conn, assertion_id=assertion_id)
        return CanonicalGraphPromotionResult(
            assertion=assertion,
            role_fillers=self.list_role_fillers_for_assertion(conn, assertion_id=assertion_id),
            entities=self.list_entities_for_assertion(conn, assertion_id=assertion_id),
        )

    def _initialize(self) -> None:
        """Create the SQLite schema for the narrow canonical-graph slice."""

        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS promoted_graph_entities(
                    entity_id TEXT PRIMARY KEY,
                    entity_type TEXT,
                    first_candidate_id TEXT NOT NULL REFERENCES candidate_assertions(candidate_id) ON DELETE RESTRICT,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS promoted_graph_assertions(
                    assertion_id TEXT PRIMARY KEY,
                    source_candidate_id TEXT NOT NULL UNIQUE REFERENCES candidate_assertions(candidate_id) ON DELETE RESTRICT,
                    profile_id TEXT NOT NULL,
                    profile_version TEXT NOT NULL,
                    predicate TEXT NOT NULL,
                    normalized_body_json TEXT NOT NULL,
                    claim_text TEXT,
                    promoted_by TEXT NOT NULL,
                    promoted_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS promoted_graph_role_fillers(
                    assertion_id TEXT NOT NULL REFERENCES promoted_graph_assertions(assertion_id) ON DELETE CASCADE,
                    role_id TEXT NOT NULL,
                    filler_index INTEGER NOT NULL,
                    filler_kind TEXT NOT NULL,
                    entity_id TEXT REFERENCES promoted_graph_entities(entity_id) ON DELETE RESTRICT,
                    entity_type TEXT,
                    value_kind TEXT,
                    value_json TEXT,
                    PRIMARY KEY(assertion_id, role_id, filler_index)
                );

                CREATE INDEX IF NOT EXISTS idx_promoted_graph_assertions_candidate
                    ON promoted_graph_assertions(source_candidate_id, promoted_at, assertion_id);
                CREATE INDEX IF NOT EXISTS idx_promoted_graph_assertions_profile
                    ON promoted_graph_assertions(profile_id, profile_version, promoted_at, assertion_id);
                CREATE INDEX IF NOT EXISTS idx_promoted_graph_role_fillers_entity
                    ON promoted_graph_role_fillers(entity_id, assertion_id, role_id, filler_index);
                """
            )
        logger.info("canonical graph store initialized db_path=%s", self._db_path)

    def _connect(self) -> sqlite3.Connection:
        """Open one SQLite connection with row access and foreign keys enabled."""

        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _hydrate_assertion(self, row: sqlite3.Row) -> PromotedGraphAssertionRecord:
        """Hydrate one promoted assertion row into the typed model."""

        source_candidate_id = str(row["source_candidate_id"])
        return PromotedGraphAssertionRecord(
            assertion_id=str(row["assertion_id"]),
            source_candidate_id=source_candidate_id,
            profile=ProfileRef(
                profile_id=str(row["profile_id"]),
                profile_version=str(row["profile_version"]),
            ),
            predicate=str(row["predicate"]),
            normalized_body=_load_json_object(
                str(row["normalized_body_json"]),
                context=(
                    "promoted_graph_assertions"
                    f"[{source_candidate_id}].normalized_body_json"
                ),
            ),
            claim_text=str(row["claim_text"]) if row["claim_text"] is not None else None,
            promoted_by=str(row["promoted_by"]),
            promoted_at=str(row["promoted_at"]),
        )

    def _hydrate_entity(self, row: sqlite3.Row) -> PromotedGraphEntityRecord:
        """Hydrate one materialized graph entity row."""

        return PromotedGraphEntityRecord(
            entity_id=str(row["entity_id"]),
            entity_type=str(row["entity_type"]) if row["entity_type"] is not None else None,
            first_candidate_id=str(row["first_candidate_id"]),
            created_at=str(row["created_at"]),
        )

    def _hydrate_role_filler(self, row: sqlite3.Row) -> PromotedGraphRoleFillerRecord:
        """Hydrate one promoted role-filler row."""

        value = (
            _load_json_scalar_or_composite(
                str(row["value_json"]),
                context=(
                    "promoted_graph_role_fillers"
                    f"[{row['assertion_id']}:{row['role_id']}:{row['filler_index']}].value_json"
                ),
            )
            if row["value_json"] is not None
            else None
        )
        return PromotedGraphRoleFillerRecord(
            assertion_id=str(row["assertion_id"]),
            role_id=str(row["role_id"]),
            filler_index=int(row["filler_index"]),
            filler_kind=_parse_filler_kind(str(row["filler_kind"])),
            entity_id=str(row["entity_id"]) if row["entity_id"] is not None else None,
            entity_type=str(row["entity_type"]) if row["entity_type"] is not None else None,
            value_kind=str(row["value_kind"]) if row["value_kind"] is not None else None,
            value=value,
        )


def _canonical_json_dumps(payload: object) -> str:
    """Return deterministic JSON text for durable storage."""

    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _load_json_object(text: str, *, context: str) -> dict[str, JsonValue]:
    """Load one stored JSON object and fail loudly on malformed content."""

    try:
        loaded = json.loads(text)
    except json.JSONDecodeError as exc:
        raise CanonicalGraphStoreError(f"invalid JSON in {context}") from exc
    try:
        validated: dict[str, JsonValue] = _JSON_OBJECT_ADAPTER.validate_python(loaded)
        return validated
    except ValueError as exc:
        raise CanonicalGraphStoreError(f"expected JSON object in {context}") from exc


def _load_json_scalar_or_composite(text: str, *, context: str) -> JsonValue:
    """Load one stored JSON value and fail loudly on malformed content."""

    try:
        loaded = json.loads(text)
    except json.JSONDecodeError as exc:
        raise CanonicalGraphStoreError(f"invalid JSON in {context}") from exc
    try:
        validated: JsonValue = _JSON_VALUE_ADAPTER.validate_python(loaded)
        return validated
    except ValueError as exc:
        raise CanonicalGraphStoreError(f"invalid JSON value in {context}") from exc


def _now_iso() -> str:
    """Return the current timestamp in UTC ISO-8601 form."""

    return datetime.now(timezone.utc).isoformat()


def _parse_filler_kind(value: str) -> PromotedGraphFillerKind:
    """Parse one persisted filler kind and fail loudly on unsupported values."""

    if value == "entity":
        return "entity"
    if value == "value":
        return "value"
    raise CanonicalGraphStoreError(f"unsupported promoted graph filler kind: {value}")


def _short_digest(value: str) -> str:
    """Return a short deterministic digest for stable graph identifiers."""

    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:24]


__all__ = [
    "CanonicalGraphStore",
    "CanonicalGraphStoreConflictError",
    "CanonicalGraphStoreError",
    "CanonicalGraphStoreNotFoundError",
]

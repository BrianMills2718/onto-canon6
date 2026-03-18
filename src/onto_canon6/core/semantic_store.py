"""SQLite persistence for the Phase 13 semantic canonicalization slice.

This store introduces one explicit repair log and one explicit rewrite path
over promoted graph assertions. It does not replace graph promotion or
identity. Its responsibilities are limited to:

1. persisting recanonicalization events;
2. rewriting promoted assertion predicate/body state explicitly;
3. rebuilding promoted role fillers from the rewritten normalized body.
"""

from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
import json
import logging
from pathlib import Path
import sqlite3
from typing import Iterator
import uuid

from pydantic import JsonValue, TypeAdapter

from .graph_models import PromotedGraphRoleFillerRecord
from .semantic_models import PromotedGraphRecanonicalizationEventRecord

logger = logging.getLogger(__name__)
_JSON_OBJECT_ADAPTER: TypeAdapter[dict[str, JsonValue]] = TypeAdapter(dict[str, JsonValue])
_JSON_VALUE_ADAPTER: TypeAdapter[JsonValue] = TypeAdapter(JsonValue)


class SemanticCanonicalizationStoreError(RuntimeError):
    """Base error for persisted semantic canonicalization failures."""


class SemanticCanonicalizationStoreNotFoundError(SemanticCanonicalizationStoreError):
    """Raised when a requested promoted assertion or event does not exist."""


class SemanticCanonicalizationStoreConflictError(SemanticCanonicalizationStoreError):
    """Raised when semantic repair would persist inconsistent graph state."""


class SemanticCanonicalizationStore:
    """Persist Phase 13 repair events and promoted-graph rewrites."""

    def __init__(self, db_path: Path) -> None:
        """Initialize the store and ensure its schema exists."""

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

    def rewrite_promoted_assertion(
        self,
        conn: sqlite3.Connection,
        *,
        assertion_id: str,
        predicate: str,
        normalized_body: dict[str, JsonValue],
    ) -> None:
        """Rewrite one promoted assertion and rebuild its role fillers.

        The rewrite is explicit and destructive within the transaction scope:
        current role-fillers for the assertion are deleted and rebuilt from the
        provided normalized body. This keeps the persisted promoted graph state
        aligned with the canonicalized body instead of drifting over time.
        """

        existing = conn.execute(
            """
            SELECT assertion_id
            FROM promoted_graph_assertions
            WHERE assertion_id = ?
            """,
            (assertion_id,),
        ).fetchone()
        if existing is None:
            raise SemanticCanonicalizationStoreNotFoundError(
                f"promoted assertion not found: {assertion_id}"
            )
        roles_obj = normalized_body.get("roles")
        if not isinstance(roles_obj, dict) or not roles_obj:
            raise SemanticCanonicalizationStoreConflictError(
                f"recanonicalized assertion is missing roles: {assertion_id}"
            )
        conn.execute(
            """
            UPDATE promoted_graph_assertions
            SET predicate = ?,
                normalized_body_json = ?
            WHERE assertion_id = ?
            """,
            (predicate, _canonical_json_dumps(normalized_body), assertion_id),
        )
        conn.execute(
            """
            DELETE FROM promoted_graph_role_fillers
            WHERE assertion_id = ?
            """,
            (assertion_id,),
        )
        for role_id, fillers_obj in roles_obj.items():
            if not isinstance(role_id, str) or not role_id.strip():
                raise SemanticCanonicalizationStoreConflictError(
                    f"recanonicalized assertion contains blank role id: {assertion_id}"
                )
            if not isinstance(fillers_obj, list) or not fillers_obj:
                raise SemanticCanonicalizationStoreConflictError(
                    f"recanonicalized assertion contains empty role list: {role_id!r}"
                )
            for filler_index, filler_obj in enumerate(fillers_obj):
                record = _build_role_filler_record(
                    assertion_id=assertion_id,
                    role_id=role_id.strip(),
                    filler_index=filler_index,
                    filler_obj=filler_obj,
                    conn=conn,
                )
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
                        record.assertion_id,
                        record.role_id,
                        record.filler_index,
                        record.filler_kind,
                        record.entity_id,
                        record.entity_type,
                        record.value_kind,
                        (
                            _canonical_json_dumps(record.value)
                            if record.value is not None
                            else None
                        ),
                    ),
                )
        logger.info(
            "semantic canonicalization rewrote promoted assertion assertion_id=%s predicate=%s",
            assertion_id,
            predicate,
        )

    def insert_event(
        self,
        conn: sqlite3.Connection,
        *,
        assertion_id: str,
        actor_id: str,
        reason: str | None,
        before_predicate: str,
        before_body: dict[str, JsonValue],
        after_predicate: str,
        after_body: dict[str, JsonValue],
    ) -> PromotedGraphRecanonicalizationEventRecord:
        """Persist one explicit recanonicalization event."""

        event_id = f"grecanon_{uuid.uuid4().hex[:24]}"
        created_at = _now_iso()
        conn.execute(
            """
            INSERT INTO promoted_graph_recanonicalization_events(
                event_id,
                assertion_id,
                actor_id,
                reason,
                before_predicate,
                before_body_json,
                after_predicate,
                after_body_json,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event_id,
                assertion_id,
                actor_id,
                reason,
                before_predicate,
                _canonical_json_dumps(before_body),
                after_predicate,
                _canonical_json_dumps(after_body),
                created_at,
            ),
        )
        logger.info(
            "semantic canonicalization event persisted event_id=%s assertion_id=%s actor_id=%s",
            event_id,
            assertion_id,
            actor_id,
        )
        return PromotedGraphRecanonicalizationEventRecord(
            event_id=event_id,
            assertion_id=assertion_id,
            actor_id=actor_id,
            reason=reason,
            before_predicate=before_predicate,
            before_body=before_body,
            after_predicate=after_predicate,
            after_body=after_body,
            created_at=created_at,
        )

    def list_events(
        self,
        conn: sqlite3.Connection,
        *,
        assertion_id: str | None = None,
    ) -> list[PromotedGraphRecanonicalizationEventRecord]:
        """List recanonicalization events in deterministic order."""

        if assertion_id is None:
            rows = conn.execute(
                """
                SELECT
                    event_id,
                    assertion_id,
                    actor_id,
                    reason,
                    before_predicate,
                    before_body_json,
                    after_predicate,
                    after_body_json,
                    created_at
                FROM promoted_graph_recanonicalization_events
                ORDER BY created_at, event_id
                """
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT
                    event_id,
                    assertion_id,
                    actor_id,
                    reason,
                    before_predicate,
                    before_body_json,
                    after_predicate,
                    after_body_json,
                    created_at
                FROM promoted_graph_recanonicalization_events
                WHERE assertion_id = ?
                ORDER BY created_at, event_id
                """,
                (assertion_id,),
            ).fetchall()
        return [self._hydrate_event(row) for row in rows]

    def _initialize(self) -> None:
        """Create the SQLite schema for the Phase 13 repair slice."""

        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS promoted_graph_recanonicalization_events(
                    event_id TEXT PRIMARY KEY,
                    assertion_id TEXT NOT NULL REFERENCES promoted_graph_assertions(assertion_id) ON DELETE CASCADE,
                    actor_id TEXT NOT NULL,
                    reason TEXT,
                    before_predicate TEXT NOT NULL,
                    before_body_json TEXT NOT NULL,
                    after_predicate TEXT NOT NULL,
                    after_body_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_promoted_graph_recanonicalization_assertion
                    ON promoted_graph_recanonicalization_events(assertion_id, created_at, event_id);
                """
            )
        logger.info("semantic canonicalization store initialized db_path=%s", self._db_path)

    def _connect(self) -> sqlite3.Connection:
        """Open one SQLite connection with row access and foreign keys enabled."""

        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _hydrate_event(
        self,
        row: sqlite3.Row,
    ) -> PromotedGraphRecanonicalizationEventRecord:
        """Hydrate one persisted recanonicalization event row."""

        return PromotedGraphRecanonicalizationEventRecord(
            event_id=str(row["event_id"]),
            assertion_id=str(row["assertion_id"]),
            actor_id=str(row["actor_id"]),
            reason=str(row["reason"]) if row["reason"] is not None else None,
            before_predicate=str(row["before_predicate"]),
            before_body=_load_json_object(
                str(row["before_body_json"]),
                context=(
                    "promoted_graph_recanonicalization_events"
                    f"[{row['event_id']}].before_body_json"
                ),
            ),
            after_predicate=str(row["after_predicate"]),
            after_body=_load_json_object(
                str(row["after_body_json"]),
                context=(
                    "promoted_graph_recanonicalization_events"
                    f"[{row['event_id']}].after_body_json"
                ),
            ),
            created_at=str(row["created_at"]),
        )


def _build_role_filler_record(
    *,
    assertion_id: str,
    role_id: str,
    filler_index: int,
    filler_obj: object,
    conn: sqlite3.Connection,
) -> PromotedGraphRoleFillerRecord:
    """Convert one normalized body filler into a persisted graph role filler."""

    if not isinstance(filler_obj, dict):
        raise SemanticCanonicalizationStoreConflictError(
            f"recanonicalized filler must be an object at {role_id}[{filler_index}]"
        )
    filler_kind_obj = filler_obj.get("kind")
    if filler_kind_obj == "entity":
        entity_id = filler_obj.get("entity_id")
        if not isinstance(entity_id, str) or not entity_id.strip():
            raise SemanticCanonicalizationStoreConflictError(
                f"entity filler is missing entity_id at {role_id}[{filler_index}]"
            )
        entity_row = conn.execute(
            """
            SELECT entity_id
            FROM promoted_graph_entities
            WHERE entity_id = ?
            """,
            (entity_id.strip(),),
        ).fetchone()
        if entity_row is None:
            raise SemanticCanonicalizationStoreConflictError(
                f"entity filler references unknown promoted entity_id: {entity_id}"
            )
        entity_type_obj = filler_obj.get("entity_type")
        entity_type = entity_type_obj.strip() if isinstance(entity_type_obj, str) else None
        return PromotedGraphRoleFillerRecord(
            assertion_id=assertion_id,
            role_id=role_id,
            filler_index=filler_index,
            filler_kind="entity",
            entity_id=entity_id.strip(),
            entity_type=entity_type,
            value_kind=None,
            value=None,
        )
    if filler_kind_obj == "value":
        value_kind = filler_obj.get("value_kind")
        if not isinstance(value_kind, str) or not value_kind.strip():
            raise SemanticCanonicalizationStoreConflictError(
                f"value filler is missing value_kind at {role_id}[{filler_index}]"
            )
        if "value" in filler_obj:
            value = _JSON_VALUE_ADAPTER.validate_python(filler_obj["value"])
        elif "normalized" in filler_obj:
            value = _JSON_VALUE_ADAPTER.validate_python(filler_obj["normalized"])
        else:
            raise SemanticCanonicalizationStoreConflictError(
                f"value filler is missing value payload at {role_id}[{filler_index}]"
            )
        return PromotedGraphRoleFillerRecord(
            assertion_id=assertion_id,
            role_id=role_id,
            filler_index=filler_index,
            filler_kind="value",
            entity_id=None,
            entity_type=None,
            value_kind=value_kind.strip(),
            value=value,
        )
    raise SemanticCanonicalizationStoreConflictError(
        f"unsupported filler kind at {role_id}[{filler_index}]: {filler_kind_obj!r}"
    )


def _canonical_json_dumps(payload: object) -> str:
    """Return deterministic JSON text for durable storage."""

    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _load_json_object(text: str, *, context: str) -> dict[str, JsonValue]:
    """Load one stored JSON object and fail loudly on malformed content."""

    try:
        loaded = json.loads(text)
    except json.JSONDecodeError as exc:
        raise SemanticCanonicalizationStoreError(f"invalid JSON in {context}") from exc
    try:
        return _JSON_OBJECT_ADAPTER.validate_python(loaded)
    except ValueError as exc:
        raise SemanticCanonicalizationStoreError(f"expected JSON object in {context}") from exc


def _now_iso() -> str:
    """Return the current timestamp in UTC ISO-8601 form."""

    return datetime.now(timezone.utc).isoformat()


__all__ = [
    "SemanticCanonicalizationStore",
    "SemanticCanonicalizationStoreConflictError",
    "SemanticCanonicalizationStoreError",
    "SemanticCanonicalizationStoreNotFoundError",
]

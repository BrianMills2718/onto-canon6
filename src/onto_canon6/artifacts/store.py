"""SQLite persistence for the Phase 8 artifact-lineage slice.

This store keeps artifact data bounded and explicit:

1. artifact records;
2. artifact-to-artifact lineage edges;
3. candidate-to-artifact support links.

It intentionally shares the same SQLite file as the review store so lineage can
reference candidate assertions without introducing a second persistence center.
"""

from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
import json
import logging
from pathlib import Path
import sqlite3
from typing import Iterable, Iterator
import uuid

from pydantic import JsonValue

from .models import (
    ArtifactLineageEdge,
    ArtifactLineageRelationship,
    ArtifactKind,
    ArtifactRecord,
    CandidateArtifactLinkRecord,
    CandidateArtifactSupportKind,
)

logger = logging.getLogger(__name__)


class ArtifactStoreError(RuntimeError):
    """Base error for persisted artifact-lineage failures."""


class ArtifactStoreNotFoundError(ArtifactStoreError):
    """Raised when a requested artifact record or link target does not exist."""


class ArtifactStoreConflictError(ArtifactStoreError):
    """Raised when an attempted write conflicts with existing lineage state."""


class ArtifactStore:
    """Persist artifacts, lineage edges, and candidate support links in SQLite."""

    def __init__(self, db_path: Path) -> None:
        """Initialize the artifact store and ensure its schema exists."""

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

    def insert_artifact(
        self,
        conn: sqlite3.Connection,
        *,
        artifact_kind: ArtifactKind,
        uri: str,
        label: str | None,
        metadata: dict[str, JsonValue],
        fingerprint: str | None,
    ) -> str:
        """Insert one artifact record and return its identifier."""

        artifact_id = f"art_{uuid.uuid4().hex[:24]}"
        created_at = _now_iso()
        conn.execute(
            """
            INSERT INTO artifacts(
                artifact_id,
                artifact_kind,
                uri,
                label,
                metadata_json,
                fingerprint,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                artifact_id,
                artifact_kind,
                uri,
                label,
                _canonical_json_dumps(metadata),
                fingerprint,
                created_at,
            ),
        )
        logger.info(
            "artifact persisted artifact_id=%s artifact_kind=%s uri=%s fingerprint=%s",
            artifact_id,
            artifact_kind,
            uri,
            fingerprint,
        )
        return artifact_id

    def get_artifact(
        self,
        conn: sqlite3.Connection,
        *,
        artifact_id: str,
    ) -> ArtifactRecord:
        """Load one artifact record."""

        row = conn.execute(
            """
            SELECT
                artifact_id,
                artifact_kind,
                uri,
                label,
                metadata_json,
                fingerprint,
                created_at
            FROM artifacts
            WHERE artifact_id = ?
            """,
            (artifact_id,),
        ).fetchone()
        if row is None:
            raise ArtifactStoreNotFoundError(f"artifact not found: {artifact_id}")
        return self._hydrate_artifact(row)

    def insert_lineage_edge(
        self,
        conn: sqlite3.Connection,
        *,
        parent_artifact_id: str,
        child_artifact_id: str,
        relationship_type: ArtifactLineageRelationship,
    ) -> ArtifactLineageEdge:
        """Persist one explicit artifact lineage edge idempotently."""

        if parent_artifact_id == child_artifact_id:
            raise ArtifactStoreConflictError("artifact lineage cannot self-reference")

        existing = conn.execute(
            """
            SELECT relationship_type
            FROM artifact_lineage
            WHERE parent_artifact_id = ?
              AND child_artifact_id = ?
              AND relationship_type = ?
            """,
            (parent_artifact_id, child_artifact_id, relationship_type),
        ).fetchone()
        if existing is None:
            conn.execute(
                """
                INSERT INTO artifact_lineage(
                    parent_artifact_id,
                    child_artifact_id,
                    relationship_type
                ) VALUES (?, ?, ?)
                """,
                (parent_artifact_id, child_artifact_id, relationship_type),
            )
            logger.info(
                "artifact lineage persisted parent_artifact_id=%s child_artifact_id=%s relationship_type=%s",
                parent_artifact_id,
                child_artifact_id,
                relationship_type,
            )
        return ArtifactLineageEdge(
            parent_artifact_id=parent_artifact_id,
            child_artifact_id=child_artifact_id,
            relationship_type=relationship_type,
        )

    def insert_candidate_artifact_link(
        self,
        conn: sqlite3.Connection,
        *,
        candidate_id: str,
        artifact_id: str,
        support_kind: CandidateArtifactSupportKind,
        reference_detail: str | None,
    ) -> CandidateArtifactLinkRecord:
        """Persist one explicit candidate-to-artifact support link idempotently."""

        existing = conn.execute(
            """
            SELECT reference_detail, created_at
            FROM candidate_artifact_links
            WHERE candidate_id = ?
              AND artifact_id = ?
              AND support_kind = ?
            """,
            (candidate_id, artifact_id, support_kind),
        ).fetchone()
        if existing is not None:
            existing_detail = (
                str(existing["reference_detail"])
                if existing["reference_detail"] is not None
                else None
            )
            if existing_detail != reference_detail:
                raise ArtifactStoreConflictError(
                    "candidate artifact link already exists with different reference_detail"
                )
            return CandidateArtifactLinkRecord(
                candidate_id=candidate_id,
                artifact_id=artifact_id,
                support_kind=support_kind,
                reference_detail=existing_detail,
                created_at=str(existing["created_at"]),
            )

        created_at = _now_iso()
        conn.execute(
            """
            INSERT INTO candidate_artifact_links(
                candidate_id,
                artifact_id,
                support_kind,
                reference_detail,
                created_at
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (candidate_id, artifact_id, support_kind, reference_detail, created_at),
        )
        logger.info(
            "candidate linked to artifact candidate_id=%s artifact_id=%s support_kind=%s",
            candidate_id,
            artifact_id,
            support_kind,
        )
        return CandidateArtifactLinkRecord(
            candidate_id=candidate_id,
            artifact_id=artifact_id,
            support_kind=support_kind,
            reference_detail=reference_detail,
            created_at=created_at,
        )

    def list_candidate_artifact_links(
        self,
        conn: sqlite3.Connection,
        *,
        candidate_id: str,
    ) -> tuple[CandidateArtifactLinkRecord, ...]:
        """List direct artifact links for one candidate in deterministic order."""

        rows = conn.execute(
            """
            SELECT
                candidate_id,
                artifact_id,
                support_kind,
                reference_detail,
                created_at
            FROM candidate_artifact_links
            WHERE candidate_id = ?
            ORDER BY created_at, artifact_id, support_kind
            """,
            (candidate_id,),
        ).fetchall()
        return tuple(self._hydrate_candidate_link(row) for row in rows)

    def list_artifacts(
        self,
        conn: sqlite3.Connection,
        *,
        artifact_ids: Iterable[str],
    ) -> tuple[ArtifactRecord, ...]:
        """Load multiple artifacts in deterministic order."""

        materialized_ids = tuple(dict.fromkeys(artifact_ids))
        if not materialized_ids:
            return ()
        placeholders = ", ".join("?" for _ in materialized_ids)
        rows = conn.execute(
            f"""
            SELECT
                artifact_id,
                artifact_kind,
                uri,
                label,
                metadata_json,
                fingerprint,
                created_at
            FROM artifacts
            WHERE artifact_id IN ({placeholders})
            ORDER BY created_at, artifact_id
            """,
            materialized_ids,
        ).fetchall()
        return tuple(self._hydrate_artifact(row) for row in rows)

    def list_ancestor_edges(
        self,
        conn: sqlite3.Connection,
        *,
        artifact_ids: Iterable[str],
    ) -> tuple[ArtifactLineageEdge, ...]:
        """Return recursive ancestor edges for the provided artifact identifiers."""

        materialized_ids = tuple(dict.fromkeys(artifact_ids))
        if not materialized_ids:
            return ()
        placeholders = ", ".join("?" for _ in materialized_ids)
        rows = conn.execute(
            f"""
            WITH RECURSIVE ancestor_edges(
                parent_artifact_id,
                child_artifact_id,
                relationship_type
            ) AS (
                SELECT
                    parent_artifact_id,
                    child_artifact_id,
                    relationship_type
                FROM artifact_lineage
                WHERE child_artifact_id IN ({placeholders})
                UNION
                SELECT
                    al.parent_artifact_id,
                    al.child_artifact_id,
                    al.relationship_type
                FROM artifact_lineage al
                JOIN ancestor_edges ae
                  ON al.child_artifact_id = ae.parent_artifact_id
            )
            SELECT
                parent_artifact_id,
                child_artifact_id,
                relationship_type
            FROM ancestor_edges
            ORDER BY parent_artifact_id, child_artifact_id, relationship_type
            """,
            materialized_ids,
        ).fetchall()
        return tuple(
            ArtifactLineageEdge(
                parent_artifact_id=str(row["parent_artifact_id"]),
                child_artifact_id=str(row["child_artifact_id"]),
                relationship_type=_parse_lineage_relationship(
                    str(row["relationship_type"])
                ),
            )
            for row in rows
        )

    def _initialize(self) -> None:
        """Create the SQLite schema for the artifact-lineage slice."""

        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS artifacts(
                    artifact_id TEXT PRIMARY KEY,
                    artifact_kind TEXT NOT NULL,
                    uri TEXT NOT NULL,
                    label TEXT,
                    metadata_json TEXT NOT NULL,
                    fingerprint TEXT,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS artifact_lineage(
                    parent_artifact_id TEXT NOT NULL REFERENCES artifacts(artifact_id) ON DELETE CASCADE,
                    child_artifact_id TEXT NOT NULL REFERENCES artifacts(artifact_id) ON DELETE CASCADE,
                    relationship_type TEXT NOT NULL,
                    PRIMARY KEY(parent_artifact_id, child_artifact_id, relationship_type)
                );

                CREATE TABLE IF NOT EXISTS candidate_artifact_links(
                    candidate_id TEXT NOT NULL REFERENCES candidate_assertions(candidate_id) ON DELETE CASCADE,
                    artifact_id TEXT NOT NULL REFERENCES artifacts(artifact_id) ON DELETE CASCADE,
                    support_kind TEXT NOT NULL,
                    reference_detail TEXT,
                    created_at TEXT NOT NULL,
                    PRIMARY KEY(candidate_id, artifact_id, support_kind)
                );

                CREATE INDEX IF NOT EXISTS idx_artifacts_kind
                    ON artifacts(artifact_kind, created_at, artifact_id);
                CREATE INDEX IF NOT EXISTS idx_artifacts_fingerprint
                    ON artifacts(fingerprint);
                CREATE INDEX IF NOT EXISTS idx_artifact_lineage_child
                    ON artifact_lineage(child_artifact_id, parent_artifact_id, relationship_type);
                CREATE INDEX IF NOT EXISTS idx_candidate_artifact_links_candidate
                    ON candidate_artifact_links(candidate_id, created_at, artifact_id);
                CREATE INDEX IF NOT EXISTS idx_candidate_artifact_links_artifact
                    ON candidate_artifact_links(artifact_id, candidate_id, support_kind);
                """
            )
        logger.info("artifact store initialized db_path=%s", self._db_path)

    def _connect(self) -> sqlite3.Connection:
        """Open one SQLite connection with row access and foreign keys enabled."""

        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _hydrate_artifact(self, row: sqlite3.Row) -> ArtifactRecord:
        """Hydrate one artifact row into the typed record."""

        artifact_id = str(row["artifact_id"])
        return ArtifactRecord(
            artifact_id=artifact_id,
            artifact_kind=_parse_artifact_kind(str(row["artifact_kind"])),
            uri=str(row["uri"]),
            label=str(row["label"]) if row["label"] is not None else None,
            metadata=_load_json_object(
                str(row["metadata_json"]),
                context=f"artifacts[{artifact_id}].metadata_json",
            ),
            fingerprint=str(row["fingerprint"]) if row["fingerprint"] is not None else None,
            created_at=str(row["created_at"]),
        )

    def _hydrate_candidate_link(self, row: sqlite3.Row) -> CandidateArtifactLinkRecord:
        """Hydrate one candidate-artifact link row into the typed record."""

        return CandidateArtifactLinkRecord(
            candidate_id=str(row["candidate_id"]),
            artifact_id=str(row["artifact_id"]),
            support_kind=_parse_support_kind(str(row["support_kind"])),
            reference_detail=(
                str(row["reference_detail"]) if row["reference_detail"] is not None else None
            ),
            created_at=str(row["created_at"]),
        )


def _canonical_json_dumps(payload: object) -> str:
    """Return deterministic JSON text for storage."""

    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _load_json_object(text: str, *, context: str) -> dict[str, JsonValue]:
    """Load one stored JSON object and fail loudly on malformed content."""

    try:
        loaded = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ArtifactStoreError(f"invalid JSON in {context}") from exc
    if not isinstance(loaded, dict):
        raise ArtifactStoreError(f"expected JSON object in {context}")
    return loaded


def _now_iso() -> str:
    """Return the current timestamp in UTC ISO-8601 form."""

    return datetime.now(timezone.utc).isoformat()


def _parse_artifact_kind(value: str) -> ArtifactKind:
    """Parse one persisted artifact kind and fail loudly on unsupported values."""

    if value == "source":
        return "source"
    if value == "derived_dataset":
        return "derived_dataset"
    if value == "analysis_result":
        return "analysis_result"
    raise ArtifactStoreError(f"unsupported artifact kind: {value}")


def _parse_lineage_relationship(value: str) -> ArtifactLineageRelationship:
    """Parse one persisted lineage relationship and fail loudly on bad values."""

    if value == "derived_from":
        return "derived_from"
    raise ArtifactStoreError(f"unsupported artifact lineage relationship: {value}")


def _parse_support_kind(value: str) -> CandidateArtifactSupportKind:
    """Parse one persisted candidate support kind and fail loudly on bad values."""

    if value == "quoted_from":
        return "quoted_from"
    if value == "supported_by_dataset":
        return "supported_by_dataset"
    if value == "supported_by_analysis":
        return "supported_by_analysis"
    raise ArtifactStoreError(f"unsupported candidate artifact support kind: {value}")

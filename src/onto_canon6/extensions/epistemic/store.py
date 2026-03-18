"""SQLite persistence for the epistemic extension slices.

This store keeps epistemic records out of the base review schema. It references
accepted candidate assertions through foreign keys, but it owns its own tables,
its own conflict rules, and its own derived report state over both accepted
candidates and promoted graph assertions.
"""

from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
import logging
from pathlib import Path
import sqlite3
from typing import Iterator
import uuid

from .models import (
    AssertionDispositionRecord,
    AssertionDispositionTargetStatus,
    ConfidenceAssessmentRecord,
    ConfidenceSourceKind,
    PromotedAssertionEpistemicStatus,
    SupersessionRecord,
)

logger = logging.getLogger(__name__)


class EpistemicStoreError(RuntimeError):
    """Base error for persisted epistemic extension failures."""


class EpistemicStoreConflictError(EpistemicStoreError):
    """Raised when new epistemic state conflicts with existing persisted records."""


class EpistemicStore:
    """Persist epistemic records in SQLite without mutating base graph tables."""

    def __init__(self, db_path: Path) -> None:
        """Initialize the epistemic store and ensure its schema exists."""

        self._db_path = db_path.resolve()
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    @property
    def db_path(self) -> Path:
        """Return the SQLite path shared with the review store."""

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

    def insert_confidence_assessment(
        self,
        conn: sqlite3.Connection,
        *,
        candidate_id: str,
        confidence_score: float,
        source_kind: ConfidenceSourceKind,
        actor_id: str,
        rationale: str | None,
    ) -> ConfidenceAssessmentRecord:
        """Persist one confidence assessment idempotently by candidate."""

        existing = conn.execute(
            """
            SELECT
                assessment_id,
                confidence_score,
                source_kind,
                actor_id,
                rationale,
                created_at
            FROM epistemic_confidence_assessments
            WHERE candidate_id = ?
            """,
            (candidate_id,),
        ).fetchone()
        if existing is not None:
            existing_rationale = str(existing["rationale"]) if existing["rationale"] is not None else None
            if (
                float(existing["confidence_score"]) != confidence_score
                or _parse_confidence_source_kind(str(existing["source_kind"])) != source_kind
                or str(existing["actor_id"]) != actor_id
                or existing_rationale != rationale
            ):
                raise EpistemicStoreConflictError(
                    "confidence assessment already exists with different content"
                )
            return ConfidenceAssessmentRecord(
                assessment_id=str(existing["assessment_id"]),
                candidate_id=candidate_id,
                confidence_score=float(existing["confidence_score"]),
                source_kind=_parse_confidence_source_kind(str(existing["source_kind"])),
                actor_id=str(existing["actor_id"]),
                rationale=existing_rationale,
                created_at=str(existing["created_at"]),
            )

        assessment_id = f"econf_{uuid.uuid4().hex[:24]}"
        created_at = _now_iso()
        conn.execute(
            """
            INSERT INTO epistemic_confidence_assessments(
                assessment_id,
                candidate_id,
                confidence_score,
                source_kind,
                actor_id,
                rationale,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                assessment_id,
                candidate_id,
                confidence_score,
                source_kind,
                actor_id,
                rationale,
                created_at,
            ),
        )
        logger.info(
            "epistemic confidence persisted candidate_id=%s confidence_score=%s source_kind=%s actor_id=%s",
            candidate_id,
            confidence_score,
            source_kind,
            actor_id,
        )
        return ConfidenceAssessmentRecord(
            assessment_id=assessment_id,
            candidate_id=candidate_id,
            confidence_score=confidence_score,
            source_kind=source_kind,
            actor_id=actor_id,
            rationale=rationale,
            created_at=created_at,
        )

    def insert_supersession(
        self,
        conn: sqlite3.Connection,
        *,
        prior_candidate_id: str,
        replacement_candidate_id: str,
        actor_id: str,
        rationale: str | None,
    ) -> SupersessionRecord:
        """Persist one supersession relation idempotently by prior candidate."""

        existing = conn.execute(
            """
            SELECT
                supersession_id,
                replacement_candidate_id,
                actor_id,
                rationale,
                created_at
            FROM epistemic_supersessions
            WHERE prior_candidate_id = ?
            """,
            (prior_candidate_id,),
        ).fetchone()
        if existing is not None:
            existing_rationale = str(existing["rationale"]) if existing["rationale"] is not None else None
            if (
                str(existing["replacement_candidate_id"]) != replacement_candidate_id
                or str(existing["actor_id"]) != actor_id
                or existing_rationale != rationale
            ):
                raise EpistemicStoreConflictError(
                    "supersession already exists with different content"
                )
            return SupersessionRecord(
                supersession_id=str(existing["supersession_id"]),
                prior_candidate_id=prior_candidate_id,
                replacement_candidate_id=str(existing["replacement_candidate_id"]),
                actor_id=str(existing["actor_id"]),
                rationale=existing_rationale,
                created_at=str(existing["created_at"]),
            )

        supersession_id = f"esup_{uuid.uuid4().hex[:24]}"
        created_at = _now_iso()
        conn.execute(
            """
            INSERT INTO epistemic_supersessions(
                supersession_id,
                prior_candidate_id,
                replacement_candidate_id,
                actor_id,
                rationale,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                supersession_id,
                prior_candidate_id,
                replacement_candidate_id,
                actor_id,
                rationale,
                created_at,
            ),
        )
        logger.info(
            "epistemic supersession persisted prior_candidate_id=%s replacement_candidate_id=%s actor_id=%s",
            prior_candidate_id,
            replacement_candidate_id,
            actor_id,
        )
        return SupersessionRecord(
            supersession_id=supersession_id,
            prior_candidate_id=prior_candidate_id,
            replacement_candidate_id=replacement_candidate_id,
            actor_id=actor_id,
            rationale=rationale,
            created_at=created_at,
        )

    def get_confidence_assessment(
        self,
        conn: sqlite3.Connection,
        *,
        candidate_id: str,
    ) -> ConfidenceAssessmentRecord | None:
        """Return the current confidence assessment for one candidate, if any."""

        row = conn.execute(
            """
            SELECT
                assessment_id,
                candidate_id,
                confidence_score,
                source_kind,
                actor_id,
                rationale,
                created_at
            FROM epistemic_confidence_assessments
            WHERE candidate_id = ?
            """,
            (candidate_id,),
        ).fetchone()
        if row is None:
            return None
        return ConfidenceAssessmentRecord(
            assessment_id=str(row["assessment_id"]),
            candidate_id=str(row["candidate_id"]),
            confidence_score=float(row["confidence_score"]),
            source_kind=_parse_confidence_source_kind(str(row["source_kind"])),
            actor_id=str(row["actor_id"]),
            rationale=str(row["rationale"]) if row["rationale"] is not None else None,
            created_at=str(row["created_at"]),
        )

    def get_superseded_by(
        self,
        conn: sqlite3.Connection,
        *,
        candidate_id: str,
    ) -> SupersessionRecord | None:
        """Return the supersession record where the candidate is the prior target."""

        row = conn.execute(
            """
            SELECT
                supersession_id,
                prior_candidate_id,
                replacement_candidate_id,
                actor_id,
                rationale,
                created_at
            FROM epistemic_supersessions
            WHERE prior_candidate_id = ?
            """,
            (candidate_id,),
        ).fetchone()
        if row is None:
            return None
        return SupersessionRecord(
            supersession_id=str(row["supersession_id"]),
            prior_candidate_id=str(row["prior_candidate_id"]),
            replacement_candidate_id=str(row["replacement_candidate_id"]),
            actor_id=str(row["actor_id"]),
            rationale=str(row["rationale"]) if row["rationale"] is not None else None,
            created_at=str(row["created_at"]),
        )

    def list_supersedes(
        self,
        conn: sqlite3.Connection,
        *,
        replacement_candidate_id: str,
    ) -> tuple[SupersessionRecord, ...]:
        """Return all supersession records where the candidate is the replacement."""

        rows = conn.execute(
            """
            SELECT
                supersession_id,
                prior_candidate_id,
                replacement_candidate_id,
                actor_id,
                rationale,
                created_at
            FROM epistemic_supersessions
            WHERE replacement_candidate_id = ?
            ORDER BY created_at, supersession_id
            """,
            (replacement_candidate_id,),
        ).fetchall()
        return tuple(
            SupersessionRecord(
                supersession_id=str(row["supersession_id"]),
                prior_candidate_id=str(row["prior_candidate_id"]),
                replacement_candidate_id=str(row["replacement_candidate_id"]),
                actor_id=str(row["actor_id"]),
                rationale=str(row["rationale"]) if row["rationale"] is not None else None,
                created_at=str(row["created_at"]),
            )
            for row in rows
        )

    def insert_assertion_disposition(
        self,
        conn: sqlite3.Connection,
        *,
        assertion_id: str,
        prior_status: PromotedAssertionEpistemicStatus,
        target_status: AssertionDispositionTargetStatus,
        actor_id: str,
        rationale: str | None,
    ) -> AssertionDispositionRecord:
        """Persist one explicit promoted-assertion disposition event."""

        disposition_id = f"edisp_{uuid.uuid4().hex[:24]}"
        created_at = _now_iso()
        conn.execute(
            """
            INSERT INTO epistemic_assertion_dispositions(
                disposition_id,
                assertion_id,
                prior_status,
                target_status,
                actor_id,
                rationale,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                disposition_id,
                assertion_id,
                prior_status,
                target_status,
                actor_id,
                rationale,
                created_at,
            ),
        )
        logger.info(
            "epistemic assertion disposition persisted assertion_id=%s prior_status=%s target_status=%s actor_id=%s",
            assertion_id,
            prior_status,
            target_status,
            actor_id,
        )
        return AssertionDispositionRecord(
            disposition_id=disposition_id,
            assertion_id=assertion_id,
            prior_status=prior_status,
            target_status=target_status,
            actor_id=actor_id,
            rationale=rationale,
            created_at=created_at,
        )

    def get_latest_assertion_disposition(
        self,
        conn: sqlite3.Connection,
        *,
        assertion_id: str,
    ) -> AssertionDispositionRecord | None:
        """Return the latest disposition event for one promoted assertion."""

        row = conn.execute(
            """
            SELECT
                disposition_id,
                assertion_id,
                prior_status,
                target_status,
                actor_id,
                rationale,
                created_at
            FROM epistemic_assertion_dispositions
            WHERE assertion_id = ?
            ORDER BY created_at DESC, disposition_id DESC
            LIMIT 1
            """,
            (assertion_id,),
        ).fetchone()
        if row is None:
            return None
        return _hydrate_assertion_disposition(row)

    def list_assertion_dispositions(
        self,
        conn: sqlite3.Connection,
        *,
        assertion_id: str,
    ) -> tuple[AssertionDispositionRecord, ...]:
        """Return all disposition events for one promoted assertion in order."""

        rows = conn.execute(
            """
            SELECT
                disposition_id,
                assertion_id,
                prior_status,
                target_status,
                actor_id,
                rationale,
                created_at
            FROM epistemic_assertion_dispositions
            WHERE assertion_id = ?
            ORDER BY created_at, disposition_id
            """,
            (assertion_id,),
        ).fetchall()
        return tuple(_hydrate_assertion_disposition(row) for row in rows)

    def _initialize(self) -> None:
        """Create the SQLite schema for the epistemic extension slices."""

        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS epistemic_confidence_assessments(
                    assessment_id TEXT PRIMARY KEY,
                    candidate_id TEXT NOT NULL UNIQUE REFERENCES candidate_assertions(candidate_id) ON DELETE CASCADE,
                    confidence_score REAL NOT NULL,
                    source_kind TEXT NOT NULL,
                    actor_id TEXT NOT NULL,
                    rationale TEXT,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS epistemic_supersessions(
                    supersession_id TEXT PRIMARY KEY,
                    prior_candidate_id TEXT NOT NULL UNIQUE REFERENCES candidate_assertions(candidate_id) ON DELETE CASCADE,
                    replacement_candidate_id TEXT NOT NULL REFERENCES candidate_assertions(candidate_id) ON DELETE CASCADE,
                    actor_id TEXT NOT NULL,
                    rationale TEXT,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS epistemic_assertion_dispositions(
                    disposition_id TEXT PRIMARY KEY,
                    assertion_id TEXT NOT NULL REFERENCES promoted_graph_assertions(assertion_id) ON DELETE CASCADE,
                    prior_status TEXT NOT NULL,
                    target_status TEXT NOT NULL,
                    actor_id TEXT NOT NULL,
                    rationale TEXT,
                    created_at TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_epistemic_confidence_candidate
                    ON epistemic_confidence_assessments(candidate_id, created_at, assessment_id);
                CREATE INDEX IF NOT EXISTS idx_epistemic_supersession_replacement
                    ON epistemic_supersessions(replacement_candidate_id, created_at, supersession_id);
                CREATE INDEX IF NOT EXISTS idx_epistemic_assertion_disposition_assertion
                    ON epistemic_assertion_dispositions(assertion_id, created_at, disposition_id);
                """
            )
        logger.info("epistemic store initialized db_path=%s", self._db_path)

    def _connect(self) -> sqlite3.Connection:
        """Open one SQLite connection with row access and foreign keys enabled."""

        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn


def _now_iso() -> str:
    """Return the current timestamp in UTC ISO-8601 form."""

    return datetime.now(timezone.utc).isoformat()


def _parse_confidence_source_kind(value: str) -> ConfidenceSourceKind:
    """Parse one persisted confidence source kind and fail loudly on bad values."""

    if value == "user":
        return "user"
    if value == "model":
        return "model"
    raise EpistemicStoreError(f"unsupported confidence source kind: {value}")


def _parse_assertion_target_status(value: str) -> AssertionDispositionTargetStatus:
    """Parse one persisted assertion target status and fail loudly on bad values."""

    if value == "active":
        return "active"
    if value == "weakened":
        return "weakened"
    if value == "retracted":
        return "retracted"
    raise EpistemicStoreError(f"unsupported assertion target status: {value}")


def _parse_assertion_epistemic_status(value: str) -> PromotedAssertionEpistemicStatus:
    """Parse one persisted assertion epistemic status and fail loudly on bad values."""

    if value == "active":
        return "active"
    if value == "weakened":
        return "weakened"
    if value == "superseded":
        return "superseded"
    if value == "retracted":
        return "retracted"
    raise EpistemicStoreError(f"unsupported assertion epistemic status: {value}")


def _hydrate_assertion_disposition(row: sqlite3.Row) -> AssertionDispositionRecord:
    """Hydrate one persisted promoted-assertion disposition event."""

    return AssertionDispositionRecord(
        disposition_id=str(row["disposition_id"]),
        assertion_id=str(row["assertion_id"]),
        prior_status=_parse_assertion_epistemic_status(str(row["prior_status"])),
        target_status=_parse_assertion_target_status(str(row["target_status"])),
        actor_id=str(row["actor_id"]),
        rationale=str(row["rationale"]) if row["rationale"] is not None else None,
        created_at=str(row["created_at"]),
    )

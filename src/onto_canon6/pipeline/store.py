"""SQLite persistence for the narrow review pipeline slice.

The store owns only durable state and deterministic hydration. It does not
perform ontology validation or profile loading; those remain in higher layers.

Phase 2 extends the schema from pure validation persistence into explicit
candidate review and provenance tracking. Phase 4 starts adding first-class
text-grounding fields by persisting optional source text, optional claim gloss,
and exact evidence spans. The migration logic is kept local so existing review
databases fail neither silently nor destructively.
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
import uuid

from pydantic import JsonValue

from ..ontology_runtime import PackRef, UnknownItemKind
from .models import (
    CandidateAssertionRecord,
    CandidateProvenance,
    CandidateReviewDecision,
    CandidateReviewRecord,
    CandidateReviewStatus,
    CandidateValidationStatus,
    EvidenceSpan,
    OverlayApplicationRecord,
    PersistedValidationSnapshot,
    ProfileRef,
    ProposalAcceptancePolicy,
    ProposalApplicationStatus,
    ProposalRecord,
    ProposalReviewDecision,
    ProposalReviewRecord,
    ProposalStatus,
    SourceArtifactRef,
)

logger = logging.getLogger(__name__)


class ReviewStoreError(RuntimeError):
    """Base error for persisted review-state failures."""


class ReviewStoreNotFoundError(ReviewStoreError):
    """Raised when a requested candidate or proposal does not exist."""


class ReviewStoreConflictError(ReviewStoreError):
    """Raised when a state transition conflicts with existing persisted state."""


class ReviewStore:
    """Persist candidate assertions and ontology proposals in SQLite.

    The store initializes and migrates its schema eagerly and fails loudly on
    malformed JSON, missing rows, duplicate reviews, or unsupported persisted
    literal values. It intentionally keeps the schema small for the current
    proving slice.
    """

    def __init__(self, db_path: Path) -> None:
        """Initialize the review store and ensure its schema exists."""

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

    def insert_candidate(
        self,
        conn: sqlite3.Connection,
        *,
        profile: ProfileRef,
        validation_status: CandidateValidationStatus,
        review_status: CandidateReviewStatus,
        payload_hash: str,
        payload: dict[str, JsonValue],
        normalized_payload: dict[str, JsonValue],
        validation: PersistedValidationSnapshot,
        provenance: CandidateProvenance,
        claim_text: str | None,
        evidence_spans: tuple[EvidenceSpan, ...],
    ) -> str:
        """Insert one candidate assertion and return its identifier."""

        candidate_id = f"cand_{uuid.uuid4().hex[:24]}"
        submitted_at = _now_iso()
        conn.execute(
            """
            INSERT INTO candidate_assertions(
                candidate_id,
                profile_id,
                profile_version,
                validation_status,
                review_status,
                payload_hash,
                payload_json,
                normalized_payload_json,
                validation_json,
                submitted_by,
                source_kind,
                source_ref,
                source_label,
                source_metadata_json,
                source_text,
                claim_text,
                submitted_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                candidate_id,
                profile.profile_id,
                profile.profile_version,
                validation_status,
                review_status,
                payload_hash,
                _canonical_json_dumps(payload),
                _canonical_json_dumps(normalized_payload),
                validation.model_dump_json(),
                provenance.submitted_by,
                provenance.source_kind,
                provenance.source_ref,
                provenance.source_label,
                _canonical_json_dumps(provenance.source_metadata),
                provenance.content_text,
                claim_text,
                submitted_at,
            ),
        )
        for span_index, span in enumerate(evidence_spans):
            conn.execute(
                """
                INSERT INTO candidate_evidence_spans(
                    candidate_id,
                    span_index,
                    start_char,
                    end_char,
                    text
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    candidate_id,
                    span_index,
                    span.start_char,
                    span.end_char,
                    span.text,
                ),
            )
        logger.info(
            "candidate persisted candidate_id=%s profile=%s/%s validation_status=%s review_status=%s source_kind=%s source_ref=%s evidence_span_count=%d",
            candidate_id,
            profile.profile_id,
            profile.profile_version,
            validation_status,
            review_status,
            provenance.source_kind,
            provenance.source_ref,
            len(evidence_spans),
        )
        return candidate_id

    def insert_candidate_review(
        self,
        conn: sqlite3.Connection,
        *,
        candidate_id: str,
        decision: CandidateReviewDecision,
        actor_id: str,
        note_text: str | None,
    ) -> str:
        """Persist one immutable candidate review and update review status."""

        existing = conn.execute(
            """
            SELECT review_id
            FROM candidate_reviews
            WHERE candidate_id = ?
            """,
            (candidate_id,),
        ).fetchone()
        if existing is not None:
            raise ReviewStoreConflictError(f"candidate already reviewed: {candidate_id}")

        review_id = f"crev_{uuid.uuid4().hex[:24]}"
        created_at = _now_iso()
        conn.execute(
            """
            INSERT INTO candidate_reviews(
                review_id,
                candidate_id,
                decision,
                note_text,
                actor_id,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                review_id,
                candidate_id,
                decision,
                note_text,
                actor_id,
                created_at,
            ),
        )
        conn.execute(
            """
            UPDATE candidate_assertions
            SET review_status = ?
            WHERE candidate_id = ?
            """,
            (decision, candidate_id),
        )
        logger.info(
            "candidate reviewed candidate_id=%s decision=%s actor_id=%s",
            candidate_id,
            decision,
            actor_id,
        )
        return review_id

    def upsert_proposal(
        self,
        conn: sqlite3.Connection,
        *,
        proposal_kind: UnknownItemKind,
        proposed_value: str,
        profile: ProfileRef,
        target_pack: PackRef | None,
        reason: str,
        details: dict[str, JsonValue],
    ) -> str:
        """Insert or reuse one ontology proposal and return its identifier."""

        proposal_key = self.proposal_key(
            proposal_kind=proposal_kind,
            proposed_value=proposed_value,
            profile=profile,
            target_pack=target_pack,
        )
        existing = conn.execute(
            """
            SELECT proposal_id
            FROM ontology_proposals
            WHERE proposal_key = ?
            """,
            (proposal_key,),
        ).fetchone()
        if existing is not None:
            proposal_id = str(existing["proposal_id"])
            logger.info(
                "proposal reused proposal_id=%s proposal_key=%s value=%s",
                proposal_id,
                proposal_key,
                proposed_value,
            )
            return proposal_id

        proposal_id = f"prop_{proposal_key.split(':', maxsplit=1)[1][:24]}"
        created_at = _now_iso()
        conn.execute(
            """
            INSERT INTO ontology_proposals(
                proposal_id,
                proposal_key,
                proposal_kind,
                proposed_value,
                profile_id,
                profile_version,
                target_pack_json,
                reason,
                status,
                application_status,
                details_json,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                proposal_id,
                proposal_key,
                proposal_kind,
                proposed_value,
                profile.profile_id,
                profile.profile_version,
                _canonical_json_dumps(target_pack.model_dump()) if target_pack is not None else None,
                reason,
                "pending",
                "not_requested",
                _canonical_json_dumps(details),
                created_at,
            ),
        )
        logger.info(
            "proposal persisted proposal_id=%s kind=%s value=%s",
            proposal_id,
            proposal_kind,
            proposed_value,
        )
        return proposal_id

    def link_candidate_to_proposal(
        self,
        conn: sqlite3.Connection,
        *,
        candidate_id: str,
        proposal_id: str,
    ) -> None:
        """Persist one candidate-to-proposal link idempotently."""

        conn.execute(
            """
            INSERT OR IGNORE INTO candidate_proposal_links(candidate_id, proposal_id)
            VALUES (?, ?)
            """,
            (candidate_id, proposal_id),
        )
        logger.info(
            "candidate linked to proposal candidate_id=%s proposal_id=%s",
            candidate_id,
            proposal_id,
        )

    def insert_proposal_review(
        self,
        conn: sqlite3.Connection,
        *,
        proposal_id: str,
        decision: ProposalReviewDecision,
        actor_id: str,
        note_text: str | None,
        acceptance_policy: ProposalAcceptancePolicy,
        application_status: ProposalApplicationStatus,
    ) -> str:
        """Persist one immutable review decision and update proposal status."""

        existing = conn.execute(
            """
            SELECT decision_id
            FROM proposal_reviews
            WHERE proposal_id = ?
            """,
            (proposal_id,),
        ).fetchone()
        if existing is not None:
            raise ReviewStoreConflictError(f"proposal already reviewed: {proposal_id}")

        decision_id = f"dec_{uuid.uuid4().hex[:24]}"
        created_at = _now_iso()
        conn.execute(
            """
            INSERT INTO proposal_reviews(
                decision_id,
                proposal_id,
                decision,
                note_text,
                actor_id,
                acceptance_policy,
                application_status,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                decision_id,
                proposal_id,
                decision,
                note_text,
                actor_id,
                acceptance_policy,
                application_status,
                created_at,
            ),
        )
        conn.execute(
            """
            UPDATE ontology_proposals
            SET status = ?, application_status = ?
            WHERE proposal_id = ?
            """,
            (decision, application_status, proposal_id),
        )
        logger.info(
            "proposal reviewed proposal_id=%s decision=%s actor_id=%s acceptance_policy=%s application_status=%s",
            proposal_id,
            decision,
            actor_id,
            acceptance_policy,
            application_status,
        )
        return decision_id

    def upsert_overlay_application(
        self,
        conn: sqlite3.Connection,
        *,
        proposal_id: str,
        profile: ProfileRef,
        overlay_pack: PackRef,
        proposal_kind: UnknownItemKind,
        applied_value: str,
        content_path: str,
        applied_by: str,
    ) -> str:
        """Persist one explicit overlay application and update proposal state.

        This write path is idempotent by `proposal_id`. Re-applying the same
        proposal with a different overlay target or value fails loudly.
        """

        existing = conn.execute(
            """
            SELECT
                application_id,
                overlay_pack_id,
                overlay_pack_version,
                proposal_kind,
                applied_value,
                content_path
            FROM overlay_applications
            WHERE proposal_id = ?
            """,
            (proposal_id,),
        ).fetchone()
        if existing is not None:
            if (
                str(existing["overlay_pack_id"]) != overlay_pack.pack_id
                or str(existing["overlay_pack_version"]) != overlay_pack.pack_version
                or str(existing["proposal_kind"]) != proposal_kind
                or str(existing["applied_value"]) != applied_value
                or str(existing["content_path"]) != content_path
            ):
                raise ReviewStoreConflictError(
                    f"overlay application already exists with different content: {proposal_id}"
                )
            conn.execute(
                """
                UPDATE ontology_proposals
                SET application_status = 'applied_to_overlay'
                WHERE proposal_id = ?
                """,
                (proposal_id,),
            )
            return str(existing["application_id"])

        application_id = f"oapp_{uuid.uuid4().hex[:24]}"
        created_at = _now_iso()
        conn.execute(
            """
            INSERT INTO overlay_applications(
                application_id,
                proposal_id,
                profile_id,
                profile_version,
                overlay_pack_id,
                overlay_pack_version,
                proposal_kind,
                applied_value,
                content_path,
                applied_by,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                application_id,
                proposal_id,
                profile.profile_id,
                profile.profile_version,
                overlay_pack.pack_id,
                overlay_pack.pack_version,
                proposal_kind,
                applied_value,
                content_path,
                applied_by,
                created_at,
            ),
        )
        conn.execute(
            """
            UPDATE ontology_proposals
            SET application_status = 'applied_to_overlay'
            WHERE proposal_id = ?
            """,
            (proposal_id,),
        )
        logger.info(
            "overlay application persisted proposal_id=%s overlay_pack=%s/%s value=%s content_path=%s",
            proposal_id,
            overlay_pack.pack_id,
            overlay_pack.pack_version,
            applied_value,
            content_path,
        )
        return application_id

    def get_candidate_assertion(
        self,
        conn: sqlite3.Connection,
        *,
        candidate_id: str,
    ) -> CandidateAssertionRecord:
        """Load one candidate assertion record."""

        row = conn.execute(
            _CANDIDATE_SELECT + " WHERE c.candidate_id = ?",
            (candidate_id,),
        ).fetchone()
        if row is None:
            raise ReviewStoreNotFoundError(f"candidate assertion not found: {candidate_id}")
        return self._hydrate_candidate(conn, row)

    def list_candidate_assertions(
        self,
        conn: sqlite3.Connection,
        *,
        review_status_filter: CandidateReviewStatus | None = None,
        validation_status_filter: CandidateValidationStatus | None = None,
        profile_id: str | None = None,
        profile_version: str | None = None,
        proposal_status_filter: ProposalStatus | None = None,
    ) -> list[CandidateAssertionRecord]:
        """List candidate assertions in deterministic order with optional filters."""

        query = _CANDIDATE_SELECT
        conditions: list[str] = []
        params: list[str] = []
        if review_status_filter is not None:
            conditions.append("c.review_status = ?")
            params.append(review_status_filter)
        if validation_status_filter is not None:
            conditions.append("c.validation_status = ?")
            params.append(validation_status_filter)
        if profile_id is not None:
            conditions.append("c.profile_id = ?")
            params.append(profile_id)
        if profile_version is not None:
            conditions.append("c.profile_version = ?")
            params.append(profile_version)
        if proposal_status_filter is not None:
            conditions.append(
                """
                EXISTS (
                    SELECT 1
                    FROM candidate_proposal_links cpl
                    JOIN ontology_proposals p
                        ON p.proposal_id = cpl.proposal_id
                    WHERE cpl.candidate_id = c.candidate_id
                      AND p.status = ?
                )
                """
            )
            params.append(proposal_status_filter)
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY c.submitted_at, c.candidate_id"
        rows = conn.execute(query, tuple(params)).fetchall()
        return [self._hydrate_candidate(conn, row) for row in rows]

    def get_proposal(self, conn: sqlite3.Connection, *, proposal_id: str) -> ProposalRecord:
        """Load one proposal record with review and candidate-link state."""

        row = conn.execute(
            _PROPOSAL_SELECT + " WHERE p.proposal_id = ?",
            (proposal_id,),
        ).fetchone()
        if row is None:
            raise ReviewStoreNotFoundError(f"proposal not found: {proposal_id}")
        return self._hydrate_proposal(conn, row)

    def get_overlay_application(
        self,
        conn: sqlite3.Connection,
        *,
        proposal_id: str,
    ) -> OverlayApplicationRecord:
        """Load one overlay application record by proposal identifier."""

        row = conn.execute(
            """
            SELECT
                application_id,
                proposal_id,
                profile_id,
                profile_version,
                overlay_pack_id,
                overlay_pack_version,
                proposal_kind,
                applied_value,
                content_path,
                applied_by,
                created_at
            FROM overlay_applications
            WHERE proposal_id = ?
            """,
            (proposal_id,),
        ).fetchone()
        if row is None:
            raise ReviewStoreNotFoundError(f"overlay application not found for proposal: {proposal_id}")
        return self._hydrate_overlay_application(row)

    def list_proposals(
        self,
        conn: sqlite3.Connection,
        *,
        status_filter: ProposalStatus | None = None,
        profile_id: str | None = None,
        profile_version: str | None = None,
    ) -> list[ProposalRecord]:
        """List proposals in deterministic order with optional filters."""

        query = _PROPOSAL_SELECT
        conditions: list[str] = []
        params: list[str] = []
        if status_filter is not None:
            conditions.append("p.status = ?")
            params.append(status_filter)
        if profile_id is not None:
            conditions.append("p.profile_id = ?")
            params.append(profile_id)
        if profile_version is not None:
            conditions.append("p.profile_version = ?")
            params.append(profile_version)
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY p.created_at, p.proposal_id"
        rows = conn.execute(query, tuple(params)).fetchall()
        return [self._hydrate_proposal(conn, row) for row in rows]

    def list_overlay_applications(
        self,
        conn: sqlite3.Connection,
        *,
        profile_id: str | None = None,
        profile_version: str | None = None,
        overlay_pack: PackRef | None = None,
    ) -> list[OverlayApplicationRecord]:
        """List overlay applications in deterministic order with optional filters."""

        query = """
            SELECT
                application_id,
                proposal_id,
                profile_id,
                profile_version,
                overlay_pack_id,
                overlay_pack_version,
                proposal_kind,
                applied_value,
                content_path,
                applied_by,
                created_at
            FROM overlay_applications
        """
        conditions: list[str] = []
        params: list[str] = []
        if profile_id is not None:
            conditions.append("profile_id = ?")
            params.append(profile_id)
        if profile_version is not None:
            conditions.append("profile_version = ?")
            params.append(profile_version)
        if overlay_pack is not None:
            conditions.append("overlay_pack_id = ?")
            conditions.append("overlay_pack_version = ?")
            params.extend([overlay_pack.pack_id, overlay_pack.pack_version])
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY created_at, application_id"
        rows = conn.execute(query, tuple(params)).fetchall()
        return [self._hydrate_overlay_application(row) for row in rows]

    def proposal_key(
        self,
        *,
        proposal_kind: UnknownItemKind,
        proposed_value: str,
        profile: ProfileRef,
        target_pack: PackRef | None,
    ) -> str:
        """Return the deduplication key for one ontology proposal."""

        digest = _sha256_json(
            {
                "proposal_kind": proposal_kind,
                "proposed_value": proposed_value,
                "profile": profile.model_dump(),
                "target_pack": target_pack.model_dump() if target_pack is not None else None,
            }
        )
        return f"sha256:{digest}"

    def _initialize(self) -> None:
        """Create and migrate the SQLite schema for the current review slice."""

        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS candidate_assertions(
                    candidate_id TEXT PRIMARY KEY,
                    profile_id TEXT NOT NULL,
                    profile_version TEXT NOT NULL,
                    validation_status TEXT NOT NULL,
                    review_status TEXT NOT NULL,
                    payload_hash TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    normalized_payload_json TEXT NOT NULL,
                    validation_json TEXT NOT NULL,
                    submitted_by TEXT NOT NULL,
                    source_kind TEXT NOT NULL,
                    source_ref TEXT NOT NULL,
                    source_label TEXT,
                    source_metadata_json TEXT NOT NULL,
                    source_text TEXT,
                    claim_text TEXT,
                    submitted_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS candidate_evidence_spans(
                    candidate_id TEXT NOT NULL REFERENCES candidate_assertions(candidate_id) ON DELETE CASCADE,
                    span_index INTEGER NOT NULL,
                    start_char INTEGER NOT NULL,
                    end_char INTEGER NOT NULL,
                    text TEXT NOT NULL,
                    PRIMARY KEY(candidate_id, span_index)
                );

                CREATE TABLE IF NOT EXISTS ontology_proposals(
                    proposal_id TEXT PRIMARY KEY,
                    proposal_key TEXT NOT NULL UNIQUE,
                    proposal_kind TEXT NOT NULL,
                    proposed_value TEXT NOT NULL,
                    profile_id TEXT NOT NULL,
                    profile_version TEXT NOT NULL,
                    target_pack_json TEXT,
                    reason TEXT NOT NULL,
                    status TEXT NOT NULL,
                    application_status TEXT NOT NULL,
                    details_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS candidate_proposal_links(
                    candidate_id TEXT NOT NULL REFERENCES candidate_assertions(candidate_id) ON DELETE CASCADE,
                    proposal_id TEXT NOT NULL REFERENCES ontology_proposals(proposal_id) ON DELETE CASCADE,
                    PRIMARY KEY(candidate_id, proposal_id)
                );

                CREATE TABLE IF NOT EXISTS proposal_reviews(
                    decision_id TEXT PRIMARY KEY,
                    proposal_id TEXT NOT NULL UNIQUE REFERENCES ontology_proposals(proposal_id) ON DELETE CASCADE,
                    decision TEXT NOT NULL,
                    note_text TEXT,
                    actor_id TEXT NOT NULL,
                    acceptance_policy TEXT NOT NULL,
                    application_status TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS candidate_reviews(
                    review_id TEXT PRIMARY KEY,
                    candidate_id TEXT NOT NULL UNIQUE REFERENCES candidate_assertions(candidate_id) ON DELETE CASCADE,
                    decision TEXT NOT NULL,
                    note_text TEXT,
                    actor_id TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS overlay_applications(
                    application_id TEXT PRIMARY KEY,
                    proposal_id TEXT NOT NULL UNIQUE REFERENCES ontology_proposals(proposal_id) ON DELETE CASCADE,
                    profile_id TEXT NOT NULL,
                    profile_version TEXT NOT NULL,
                    overlay_pack_id TEXT NOT NULL,
                    overlay_pack_version TEXT NOT NULL,
                    proposal_kind TEXT NOT NULL,
                    applied_value TEXT NOT NULL,
                    content_path TEXT NOT NULL,
                    applied_by TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                """
            )
            self._migrate_candidate_assertions_schema(conn)
            conn.executescript(
                """
                CREATE INDEX IF NOT EXISTS idx_candidate_review_status
                    ON candidate_assertions(review_status, submitted_at, candidate_id);
                CREATE INDEX IF NOT EXISTS idx_candidate_validation_status
                    ON candidate_assertions(validation_status, submitted_at, candidate_id);
                CREATE INDEX IF NOT EXISTS idx_candidate_profile
                    ON candidate_assertions(profile_id, profile_version, submitted_at, candidate_id);
                CREATE INDEX IF NOT EXISTS idx_candidate_evidence_candidate
                    ON candidate_evidence_spans(candidate_id, span_index);
                CREATE INDEX IF NOT EXISTS idx_proposal_status
                    ON ontology_proposals(status, created_at, proposal_id);
                CREATE INDEX IF NOT EXISTS idx_proposal_profile
                    ON ontology_proposals(profile_id, profile_version, created_at, proposal_id);
                CREATE INDEX IF NOT EXISTS idx_overlay_application_profile
                    ON overlay_applications(profile_id, profile_version, created_at, application_id);
                CREATE INDEX IF NOT EXISTS idx_overlay_application_pack
                    ON overlay_applications(overlay_pack_id, overlay_pack_version, created_at, application_id);
                """
            )
        logger.info("review store initialized db_path=%s", self._db_path)

    def _migrate_candidate_assertions_schema(self, conn: sqlite3.Connection) -> None:
        """Bring pre-Phase-2 candidate tables forward without dropping data."""

        existing = _table_columns(conn, "candidate_assertions")
        if "validation_status" not in existing:
            conn.execute(
                """
                ALTER TABLE candidate_assertions
                ADD COLUMN validation_status TEXT NOT NULL DEFAULT 'needs_review'
                """
            )
            logger.info("review store migrated candidate_assertions add_column=validation_status")
        if "review_status" not in existing:
            conn.execute(
                """
                ALTER TABLE candidate_assertions
                ADD COLUMN review_status TEXT NOT NULL DEFAULT 'pending_review'
                """
            )
            logger.info("review store migrated candidate_assertions add_column=review_status")
        if "source_kind" not in existing:
            conn.execute(
                """
                ALTER TABLE candidate_assertions
                ADD COLUMN source_kind TEXT NOT NULL DEFAULT 'legacy_bootstrap'
                """
            )
            logger.info("review store migrated candidate_assertions add_column=source_kind")
        if "source_ref" not in existing:
            conn.execute(
                """
                ALTER TABLE candidate_assertions
                ADD COLUMN source_ref TEXT NOT NULL DEFAULT 'legacy:unspecified'
                """
            )
            conn.execute(
                """
                UPDATE candidate_assertions
                SET source_ref = 'legacy:' || candidate_id
                WHERE source_ref = 'legacy:unspecified'
                """
            )
            logger.info("review store migrated candidate_assertions add_column=source_ref")
        if "source_label" not in existing:
            conn.execute(
                """
                ALTER TABLE candidate_assertions
                ADD COLUMN source_label TEXT
                """
            )
            logger.info("review store migrated candidate_assertions add_column=source_label")
        if "source_metadata_json" not in existing:
            conn.execute(
                """
                ALTER TABLE candidate_assertions
                ADD COLUMN source_metadata_json TEXT NOT NULL DEFAULT '{}'
                """
            )
            conn.execute(
                """
                UPDATE candidate_assertions
                SET source_metadata_json = ?
                WHERE source_kind = 'legacy_bootstrap'
                  AND source_metadata_json = '{}'
                """,
                (_canonical_json_dumps({"migrated_from_phase1": True}),),
            )
            logger.info("review store migrated candidate_assertions add_column=source_metadata_json")
        if "source_text" not in existing:
            conn.execute(
                """
                ALTER TABLE candidate_assertions
                ADD COLUMN source_text TEXT
                """
            )
            logger.info("review store migrated candidate_assertions add_column=source_text")
        if "claim_text" not in existing:
            conn.execute(
                """
                ALTER TABLE candidate_assertions
                ADD COLUMN claim_text TEXT
                """
            )
            logger.info("review store migrated candidate_assertions add_column=claim_text")

        if "candidate_status" in existing:
            conn.execute(
                """
                UPDATE candidate_assertions
                SET validation_status = candidate_status
                WHERE candidate_status IN ('valid', 'invalid', 'needs_review')
                """
            )
            logger.info("review store migrated candidate_assertions copied legacy candidate_status")

    def _connect(self) -> sqlite3.Connection:
        """Open one SQLite connection with row access and foreign keys enabled."""

        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _hydrate_candidate(
        self,
        conn: sqlite3.Connection,
        row: sqlite3.Row,
    ) -> CandidateAssertionRecord:
        """Hydrate one candidate record and its linked review metadata."""

        candidate_id = str(row["candidate_id"])
        proposal_rows = conn.execute(
            """
            SELECT proposal_id
            FROM candidate_proposal_links
            WHERE candidate_id = ?
            ORDER BY proposal_id
            """,
            (candidate_id,),
        ).fetchall()
        proposal_ids = tuple(str(link["proposal_id"]) for link in proposal_rows)
        validation_payload = _load_json_object(
            str(row["validation_json"]),
            context=f"candidate_assertions[{candidate_id}].validation_json",
        )
        payload = _load_json_object(
            str(row["payload_json"]),
            context=f"candidate_assertions[{candidate_id}].payload_json",
        )
        normalized_payload = _load_json_object(
            str(row["normalized_payload_json"]),
            context=f"candidate_assertions[{candidate_id}].normalized_payload_json",
        )
        source_metadata = _load_json_object(
            str(row["source_metadata_json"]),
            context=f"candidate_assertions[{candidate_id}].source_metadata_json",
        )
        evidence_rows = conn.execute(
            """
            SELECT span_index, start_char, end_char, text
            FROM candidate_evidence_spans
            WHERE candidate_id = ?
            ORDER BY span_index
            """,
            (candidate_id,),
        ).fetchall()
        evidence_spans = tuple(
            EvidenceSpan(
                start_char=int(span_row["start_char"]),
                end_char=int(span_row["end_char"]),
                text=str(span_row["text"]),
            )
            for span_row in evidence_rows
        )
        review: CandidateReviewRecord | None = None
        if row["candidate_review_id"] is not None:
            review = CandidateReviewRecord(
                review_id=str(row["candidate_review_id"]),
                candidate_id=candidate_id,
                decision=_parse_candidate_review_decision(str(row["candidate_review_decision"])),
                actor_id=str(row["candidate_review_actor_id"]),
                note_text=(
                    str(row["candidate_review_note_text"])
                    if row["candidate_review_note_text"] is not None
                    else None
                ),
                created_at=str(row["candidate_reviewed_at"]),
            )
        return CandidateAssertionRecord(
            candidate_id=candidate_id,
            profile=ProfileRef(
                profile_id=str(row["profile_id"]),
                profile_version=str(row["profile_version"]),
            ),
            validation_status=_parse_candidate_validation_status(str(row["validation_status"])),
            review_status=_parse_candidate_review_status(str(row["review_status"])),
            payload_hash=str(row["payload_hash"]),
            payload=payload,
            normalized_payload=normalized_payload,
            validation=PersistedValidationSnapshot.model_validate(validation_payload),
            proposal_ids=proposal_ids,
            provenance=CandidateProvenance(
                submitted_by=str(row["submitted_by"]),
                source_artifact=SourceArtifactRef(
                    source_kind=str(row["source_kind"]),
                    source_ref=str(row["source_ref"]),
                    source_label=(
                        str(row["source_label"]) if row["source_label"] is not None else None
                    ),
                    source_metadata=source_metadata,
                    content_text=(
                        str(row["source_text"]) if row["source_text"] is not None else None
                    ),
                ),
            ),
            claim_text=str(row["claim_text"]) if row["claim_text"] is not None else None,
            evidence_spans=evidence_spans,
            submitted_at=str(row["submitted_at"]),
            review=review,
        )

    def _hydrate_proposal(
        self,
        conn: sqlite3.Connection,
        row: sqlite3.Row,
    ) -> ProposalRecord:
        """Hydrate one proposal record and its linked candidate identifiers."""

        proposal_id = str(row["proposal_id"])
        target_pack: PackRef | None = None
        if row["target_pack_json"] is not None:
            target_pack = PackRef.model_validate(
                _load_json_object(
                    str(row["target_pack_json"]),
                    context=f"ontology_proposals[{proposal_id}].target_pack_json",
                )
            )
        candidate_rows = conn.execute(
            """
            SELECT candidate_id
            FROM candidate_proposal_links
            WHERE proposal_id = ?
            ORDER BY candidate_id
            """,
            (proposal_id,),
        ).fetchall()
        candidate_ids = tuple(str(link["candidate_id"]) for link in candidate_rows)
        details = _load_json_object(
            str(row["details_json"]),
            context=f"ontology_proposals[{proposal_id}].details_json",
        )
        review: ProposalReviewRecord | None = None
        if row["decision_id"] is not None:
            review = ProposalReviewRecord(
                decision_id=str(row["decision_id"]),
                proposal_id=proposal_id,
                decision=_parse_proposal_review_decision(str(row["decision"])),
                actor_id=str(row["actor_id"]),
                note_text=str(row["note_text"]) if row["note_text"] is not None else None,
                acceptance_policy=_parse_acceptance_policy(str(row["acceptance_policy"])),
                application_status=_parse_application_status(
                    str(row["review_application_status"])
                ),
                created_at=str(row["reviewed_at"]),
            )
        overlay_application: OverlayApplicationRecord | None = None
        if row["overlay_application_id"] is not None:
            overlay_application = OverlayApplicationRecord(
                application_id=str(row["overlay_application_id"]),
                proposal_id=proposal_id,
                profile=ProfileRef(
                    profile_id=str(row["overlay_profile_id"]),
                    profile_version=str(row["overlay_profile_version"]),
                ),
                overlay_pack=PackRef(
                    pack_id=str(row["overlay_pack_id"]),
                    pack_version=str(row["overlay_pack_version"]),
                ),
                proposal_kind=_parse_proposal_kind(str(row["overlay_proposal_kind"])),
                applied_value=str(row["overlay_applied_value"]),
                content_path=str(row["overlay_content_path"]),
                applied_by=str(row["overlay_applied_by"]),
                created_at=str(row["overlay_created_at"]),
            )
        return ProposalRecord(
            proposal_id=proposal_id,
            proposal_key=str(row["proposal_key"]),
            proposal_kind=_parse_proposal_kind(str(row["proposal_kind"])),
            proposed_value=str(row["proposed_value"]),
            profile=ProfileRef(
                profile_id=str(row["profile_id"]),
                profile_version=str(row["profile_version"]),
            ),
            target_pack=target_pack,
            reason=str(row["reason"]),
            status=_parse_proposal_status(str(row["status"])),
            application_status=_parse_application_status(str(row["application_status"])),
            details=details,
            candidate_ids=candidate_ids,
            created_at=str(row["created_at"]),
            review=review,
            overlay_application=overlay_application,
        )

    def _hydrate_overlay_application(
        self,
        row: sqlite3.Row,
    ) -> OverlayApplicationRecord:
        """Hydrate one overlay application row into the typed record."""

        return OverlayApplicationRecord(
            application_id=str(row["application_id"]),
            proposal_id=str(row["proposal_id"]),
            profile=ProfileRef(
                profile_id=str(row["profile_id"]),
                profile_version=str(row["profile_version"]),
            ),
            overlay_pack=PackRef(
                pack_id=str(row["overlay_pack_id"]),
                pack_version=str(row["overlay_pack_version"]),
            ),
            proposal_kind=_parse_proposal_kind(str(row["proposal_kind"])),
            applied_value=str(row["applied_value"]),
            content_path=str(row["content_path"]),
            applied_by=str(row["applied_by"]),
            created_at=str(row["created_at"]),
        )


_CANDIDATE_SELECT = """
SELECT
    c.candidate_id,
    c.profile_id,
    c.profile_version,
    c.validation_status,
    c.review_status,
    c.payload_hash,
    c.payload_json,
    c.normalized_payload_json,
    c.validation_json,
    c.submitted_by,
    c.source_kind,
    c.source_ref,
    c.source_label,
    c.source_metadata_json,
    c.source_text,
    c.claim_text,
    c.submitted_at,
    r.review_id AS candidate_review_id,
    r.decision AS candidate_review_decision,
    r.note_text AS candidate_review_note_text,
    r.actor_id AS candidate_review_actor_id,
    r.created_at AS candidate_reviewed_at
FROM candidate_assertions c
LEFT JOIN candidate_reviews r
    ON r.candidate_id = c.candidate_id
"""

_PROPOSAL_SELECT = """
SELECT
    p.proposal_id,
    p.proposal_key,
    p.proposal_kind,
    p.proposed_value,
    p.profile_id,
    p.profile_version,
    p.target_pack_json,
    p.reason,
    p.status,
    p.application_status,
    p.details_json,
    p.created_at,
    r.decision_id,
    r.decision,
    r.note_text,
    r.actor_id,
    r.acceptance_policy,
    r.application_status AS review_application_status,
    r.created_at AS reviewed_at,
    oa.application_id AS overlay_application_id,
    oa.profile_id AS overlay_profile_id,
    oa.profile_version AS overlay_profile_version,
    oa.overlay_pack_id,
    oa.overlay_pack_version,
    oa.proposal_kind AS overlay_proposal_kind,
    oa.applied_value AS overlay_applied_value,
    oa.content_path AS overlay_content_path,
    oa.applied_by AS overlay_applied_by,
    oa.created_at AS overlay_created_at
FROM ontology_proposals p
LEFT JOIN proposal_reviews r
    ON r.proposal_id = p.proposal_id
LEFT JOIN overlay_applications oa
    ON oa.proposal_id = p.proposal_id
"""


def _canonical_json_dumps(payload: object) -> str:
    """Return deterministic JSON text for hashing and storage."""

    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _sha256_json(payload: object) -> str:
    """Return the SHA-256 digest of deterministic JSON text."""

    return hashlib.sha256(_canonical_json_dumps(payload).encode("utf-8")).hexdigest()


def _load_json_object(text: str, *, context: str) -> dict[str, JsonValue]:
    """Decode persisted JSON and require an object payload."""

    try:
        decoded = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ReviewStoreError(f"invalid JSON in {context}: {exc}") from exc
    if not isinstance(decoded, dict):
        raise ReviewStoreError(f"{context} must decode to a JSON object")
    return decoded


def _table_columns(conn: sqlite3.Connection, table_name: str) -> set[str]:
    """Return the current column names for one SQLite table."""

    rows = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
    return {str(row["name"]) for row in rows}


def _now_iso() -> str:
    """Return an ISO-8601 UTC timestamp with stable formatting."""

    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _parse_candidate_validation_status(value: str) -> CandidateValidationStatus:
    """Narrow persisted validation status strings to the supported literal set."""

    if value == "valid":
        return "valid"
    if value == "invalid":
        return "invalid"
    if value == "needs_review":
        return "needs_review"
    raise ReviewStoreError(f"unsupported candidate validation status: {value}")


def _parse_candidate_review_status(value: str) -> CandidateReviewStatus:
    """Narrow persisted review status strings to the supported literal set."""

    if value == "pending_review":
        return "pending_review"
    if value == "accepted":
        return "accepted"
    if value == "rejected":
        return "rejected"
    raise ReviewStoreError(f"unsupported candidate review status: {value}")


def _parse_candidate_review_decision(value: str) -> CandidateReviewDecision:
    """Narrow persisted candidate review decisions to the supported literal set."""

    if value == "accepted":
        return "accepted"
    if value == "rejected":
        return "rejected"
    raise ReviewStoreError(f"unsupported candidate review decision: {value}")


def _parse_proposal_review_decision(value: str) -> ProposalReviewDecision:
    """Narrow persisted proposal review decisions to the supported literal set."""

    if value == "accepted":
        return "accepted"
    if value == "rejected":
        return "rejected"
    raise ReviewStoreError(f"unsupported proposal review decision: {value}")


def _parse_acceptance_policy(value: str) -> ProposalAcceptancePolicy:
    """Narrow persisted acceptance policy strings to the supported literal set."""

    if value == "record_only":
        return "record_only"
    if value == "apply_to_overlay":
        return "apply_to_overlay"
    raise ReviewStoreError(f"unsupported acceptance policy: {value}")


def _parse_application_status(value: str) -> ProposalApplicationStatus:
    """Narrow persisted application status strings to the supported literal set."""

    if value == "not_requested":
        return "not_requested"
    if value == "recorded":
        return "recorded"
    if value == "pending_overlay_apply":
        return "pending_overlay_apply"
    if value == "applied_to_overlay":
        return "applied_to_overlay"
    raise ReviewStoreError(f"unsupported proposal application status: {value}")


def _parse_proposal_kind(value: str) -> UnknownItemKind:
    """Narrow persisted proposal kinds to the supported unknown-item kinds."""

    if value == "predicate":
        return "predicate"
    if value == "role":
        return "role"
    if value == "entity_type":
        return "entity_type"
    if value == "value_kind":
        return "value_kind"
    raise ReviewStoreError(f"unsupported proposal kind: {value}")


def _parse_proposal_status(value: str) -> ProposalStatus:
    """Narrow persisted proposal status strings to the supported literal set."""

    if value == "pending":
        return "pending"
    if value == "accepted":
        return "accepted"
    if value == "rejected":
        return "rejected"
    raise ReviewStoreError(f"unsupported proposal status: {value}")


__all__ = [
    "ReviewStore",
    "ReviewStoreConflictError",
    "ReviewStoreError",
    "ReviewStoreNotFoundError",
]

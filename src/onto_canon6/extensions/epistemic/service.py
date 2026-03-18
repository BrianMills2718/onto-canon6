"""Service layer for the first epistemic extension slice.

This service composes the review store with extension-local epistemic state. It
keeps the base workflow optional by referencing accepted candidates through
explicit seams rather than modifying base review tables.
"""

from __future__ import annotations

import logging
from pathlib import Path

from ...config import get_config
from ...pipeline import CandidateAssertionRecord, ReviewStore
from .models import (
    ConfidenceAssessmentRecord,
    ConfidenceSourceKind,
    EpistemicCandidateReport,
    EpistemicCandidateStatus,
    SupersessionRecord,
)
from .store import EpistemicStore, EpistemicStoreConflictError

logger = logging.getLogger(__name__)


class EpistemicService:
    """Assign confidence, record supersession, and build epistemic reports."""

    def __init__(self, *, db_path: Path | None = None) -> None:
        """Create an epistemic service over the configured review database."""

        config = get_config()
        resolved_db_path = db_path or config.review_db_path()
        self._review_store = ReviewStore(resolved_db_path)
        self._store = EpistemicStore(resolved_db_path)

    @property
    def db_path(self) -> Path:
        """Return the SQLite path shared with review state."""

        return self._store.db_path

    def record_confidence(
        self,
        *,
        candidate_id: str,
        confidence_score: float,
        source_kind: ConfidenceSourceKind,
        actor_id: str,
        rationale: str | None = None,
    ) -> ConfidenceAssessmentRecord:
        """Persist one confidence assessment against an accepted candidate."""

        normalized_candidate_id = _require_non_empty(candidate_id, field_name="candidate_id")
        normalized_actor_id = _require_non_empty(actor_id, field_name="actor_id")
        normalized_rationale = rationale.strip() if rationale is not None else None
        with self._store.transaction() as conn:
            candidate = self._review_store.get_candidate_assertion(
                conn,
                candidate_id=normalized_candidate_id,
            )
            _require_accepted_candidate(candidate)
            record = self._store.insert_confidence_assessment(
                conn,
                candidate_id=normalized_candidate_id,
                confidence_score=confidence_score,
                source_kind=source_kind,
                actor_id=normalized_actor_id,
                rationale=normalized_rationale if normalized_rationale else None,
            )
        logger.info(
            "epistemic confidence recorded candidate_id=%s confidence_score=%s source_kind=%s actor_id=%s",
            normalized_candidate_id,
            confidence_score,
            source_kind,
            normalized_actor_id,
        )
        return record

    def record_supersession(
        self,
        *,
        prior_candidate_id: str,
        replacement_candidate_id: str,
        actor_id: str,
        rationale: str | None = None,
    ) -> SupersessionRecord:
        """Persist one supersession from an older accepted candidate to a newer one."""

        normalized_prior_id = _require_non_empty(
            prior_candidate_id,
            field_name="prior_candidate_id",
        )
        normalized_replacement_id = _require_non_empty(
            replacement_candidate_id,
            field_name="replacement_candidate_id",
        )
        normalized_actor_id = _require_non_empty(actor_id, field_name="actor_id")
        normalized_rationale = rationale.strip() if rationale is not None else None
        if normalized_prior_id == normalized_replacement_id:
            raise ValueError("supersession requires different candidate identifiers")

        with self._store.transaction() as conn:
            prior_candidate = self._review_store.get_candidate_assertion(
                conn,
                candidate_id=normalized_prior_id,
            )
            replacement_candidate = self._review_store.get_candidate_assertion(
                conn,
                candidate_id=normalized_replacement_id,
            )
            _require_accepted_candidate(prior_candidate)
            _require_accepted_candidate(replacement_candidate)
            if self._store.get_superseded_by(conn, candidate_id=normalized_replacement_id) is not None:
                raise EpistemicStoreConflictError(
                    "replacement candidate is already superseded and cannot become the replacement"
                )
            record = self._store.insert_supersession(
                conn,
                prior_candidate_id=normalized_prior_id,
                replacement_candidate_id=normalized_replacement_id,
                actor_id=normalized_actor_id,
                rationale=normalized_rationale if normalized_rationale else None,
            )
        logger.info(
            "epistemic supersession recorded prior_candidate_id=%s replacement_candidate_id=%s actor_id=%s",
            normalized_prior_id,
            normalized_replacement_id,
            normalized_actor_id,
        )
        return record

    def build_candidate_report(self, *, candidate_id: str) -> EpistemicCandidateReport:
        """Return one accepted candidate plus its extension-local epistemic state."""

        normalized_candidate_id = _require_non_empty(candidate_id, field_name="candidate_id")
        with self._store.transaction() as conn:
            candidate = self._review_store.get_candidate_assertion(
                conn,
                candidate_id=normalized_candidate_id,
            )
            _require_accepted_candidate(candidate)
            confidence = self._store.get_confidence_assessment(conn, candidate_id=normalized_candidate_id)
            superseded_by = self._store.get_superseded_by(conn, candidate_id=normalized_candidate_id)
            supersedes = self._store.list_supersedes(
                conn,
                replacement_candidate_id=normalized_candidate_id,
            )
        epistemic_status: EpistemicCandidateStatus = "superseded" if superseded_by else "active"
        return EpistemicCandidateReport(
            candidate=candidate,
            epistemic_status=epistemic_status,
            confidence=confidence,
            superseded_by=superseded_by,
            supersedes=supersedes,
        )


def _require_non_empty(value: str, *, field_name: str) -> str:
    """Reject blank string inputs at the extension service boundary."""

    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must be a non-empty string")
    return normalized


def _require_accepted_candidate(candidate: CandidateAssertionRecord) -> None:
    """Require that extension state attaches only to accepted candidates."""

    if candidate.review_status != "accepted":
        raise EpistemicStoreConflictError(
            f"epistemic extension requires accepted candidate: {candidate.candidate_id}"
        )

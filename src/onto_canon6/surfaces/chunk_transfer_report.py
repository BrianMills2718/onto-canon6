"""Chunk-level transfer report surface for reviewed extraction runs.

This surface bridges the gap between sentence-level prompt-eval wins and the
real review workflow over multi-paragraph chunks. It does not rerun
extraction, score semantics independently, or duplicate the full review DB.
Instead, it summarizes one reviewed `source_ref` from one review store and
produces a small typed artifact that can be cited when deciding whether a
prompt family actually transfers to live chunk extraction.
"""

from __future__ import annotations

from collections import Counter
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from ..config import get_config
from ..pipeline import CandidateAssertionRecord, CandidateReviewStatus, ProfileRef, ReviewService

ChunkTransferVerdict = Literal["positive", "mixed", "negative"]


class ChunkTransferCandidateSummary(BaseModel):
    """Compact per-candidate summary for one chunk transfer report.

    The report keeps just enough detail to understand why transfer succeeded or
    failed without embedding the full persisted candidate payload again.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    candidate_id: str = Field(min_length=1)
    review_status: CandidateReviewStatus
    validation_status: str = Field(min_length=1)
    predicate: str = Field(min_length=1)
    claim_text: str | None = None
    evidence_span_count: int = Field(ge=0)


class ChunkTransferReportSummary(BaseModel):
    """Stable summary for one reviewed chunk-level transfer slice."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    total_candidates: int = Field(ge=1)
    accepted_candidates: int = Field(ge=0)
    rejected_candidates: int = Field(ge=0)
    pending_candidates: int = Field(ge=0)
    reviewed_candidates: int = Field(ge=0)
    acceptance_rate: float = Field(ge=0.0, le=1.0)
    review_complete: bool
    verdict: ChunkTransferVerdict
    predicate_counts: dict[str, int] = Field(default_factory=dict)
    review_status_counts: dict[str, int] = Field(default_factory=dict)


class ChunkTransferReport(BaseModel):
    """Typed report over one reviewed source chunk in one review store.

    Prompt metadata is optional because the current review store does not yet
    persist extraction prompt context. The report still records explicit
    caller-supplied prompt annotations when available so run notes can cite the
    exact asset/ref used for the live chunk run.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    review_db_path: str = Field(min_length=1)
    source_ref: str = Field(min_length=1)
    source_kind: str = Field(min_length=1)
    source_label: str | None = None
    profile: ProfileRef
    prompt_template: str | None = None
    prompt_ref: str | None = None
    selection_task: str | None = None
    candidates: tuple[ChunkTransferCandidateSummary, ...]
    summary: ChunkTransferReportSummary


class ChunkTransferReportService:
    """Build a small transfer artifact from reviewed chunk-level candidates."""

    def __init__(
        self,
        *,
        review_service: ReviewService | None = None,
        positive_min_acceptance_rate: float | None = None,
        negative_max_acceptance_rate: float | None = None,
        require_review_complete: bool | None = None,
    ) -> None:
        """Use config-backed defaults unless explicit transfer thresholds are provided."""

        config = get_config()
        chunk_transfer = config.evaluation.chunk_transfer
        self._review_service = review_service or ReviewService()
        self._positive_min_acceptance_rate = (
            positive_min_acceptance_rate
            if positive_min_acceptance_rate is not None
            else chunk_transfer.positive_min_acceptance_rate
        )
        self._negative_max_acceptance_rate = (
            negative_max_acceptance_rate
            if negative_max_acceptance_rate is not None
            else chunk_transfer.negative_max_acceptance_rate
        )
        self._require_review_complete = (
            require_review_complete
            if require_review_complete is not None
            else chunk_transfer.require_review_complete
        )

    def build_report(
        self,
        *,
        source_ref: str,
        prompt_template: str | None = None,
        prompt_ref: str | None = None,
        selection_task: str | None = None,
    ) -> ChunkTransferReport:
        """Return one transfer report for the reviewed candidates under `source_ref`.

        The contract is intentionally strict:

        - `source_ref` must exist in the current review store;
        - all matching candidates must share the same profile and source kind;
        - the report fails loudly if pending-review candidates remain and
          review-complete evidence is required.
        """

        normalized_source_ref = source_ref.strip()
        if not normalized_source_ref:
            raise ValueError("source_ref must be non-empty")

        candidates = tuple(
            candidate
            for candidate in self._review_service.list_candidate_assertions()
            if candidate.provenance.source_ref == normalized_source_ref
        )
        if not candidates:
            raise ValueError(f"no candidates found for source_ref={normalized_source_ref}")

        _require_uniform_profile(candidates)
        _require_uniform_source_kind(candidates)

        pending_candidates = sum(
            1 for candidate in candidates if candidate.review_status == "pending_review"
        )
        review_complete = pending_candidates == 0
        if self._require_review_complete and not review_complete:
            raise ValueError(
                "chunk transfer report requires review-complete candidates for one source_ref"
            )

        accepted_candidates = sum(
            1 for candidate in candidates if candidate.review_status == "accepted"
        )
        rejected_candidates = sum(
            1 for candidate in candidates if candidate.review_status == "rejected"
        )
        total_candidates = len(candidates)
        acceptance_rate = accepted_candidates / total_candidates
        verdict = _derive_verdict(
            acceptance_rate=acceptance_rate,
            positive_min_acceptance_rate=self._positive_min_acceptance_rate,
            negative_max_acceptance_rate=self._negative_max_acceptance_rate,
        )
        first = candidates[0]
        review_db_path = str(self._review_service.store.db_path.resolve())
        return ChunkTransferReport(
            review_db_path=review_db_path,
            source_ref=normalized_source_ref,
            source_kind=first.provenance.source_kind,
            source_label=first.provenance.source_label,
            profile=first.profile,
            prompt_template=prompt_template,
            prompt_ref=prompt_ref,
            selection_task=selection_task,
            candidates=tuple(_candidate_summary(candidate) for candidate in candidates),
            summary=ChunkTransferReportSummary(
                total_candidates=total_candidates,
                accepted_candidates=accepted_candidates,
                rejected_candidates=rejected_candidates,
                pending_candidates=pending_candidates,
                reviewed_candidates=accepted_candidates + rejected_candidates,
                acceptance_rate=acceptance_rate,
                review_complete=review_complete,
                verdict=verdict,
                predicate_counts=dict(
                    Counter(str(candidate.payload.get("predicate", "")) for candidate in candidates)
                ),
                review_status_counts=dict(
                    Counter(candidate.review_status for candidate in candidates)
                ),
            ),
        )


def _candidate_summary(candidate: CandidateAssertionRecord) -> ChunkTransferCandidateSummary:
    """Project one persisted candidate into the compact transfer-report shape."""

    predicate = str(candidate.payload.get("predicate", "")).strip()
    if not predicate:
        raise ValueError(f"candidate payload is missing predicate: {candidate.candidate_id}")
    return ChunkTransferCandidateSummary(
        candidate_id=candidate.candidate_id,
        review_status=candidate.review_status,
        validation_status=candidate.validation_status,
        predicate=predicate,
        claim_text=candidate.claim_text,
        evidence_span_count=len(candidate.evidence_spans),
    )


def _derive_verdict(
    *,
    acceptance_rate: float,
    positive_min_acceptance_rate: float,
    negative_max_acceptance_rate: float,
) -> ChunkTransferVerdict:
    """Classify transfer from the reviewed acceptance rate."""

    if acceptance_rate >= positive_min_acceptance_rate:
        return "positive"
    if acceptance_rate <= negative_max_acceptance_rate:
        return "negative"
    return "mixed"


def _require_uniform_profile(candidates: tuple[CandidateAssertionRecord, ...]) -> None:
    """Fail loudly when one source_ref spans multiple profiles in one report."""

    profiles = {
        (candidate.profile.profile_id, candidate.profile.profile_version)
        for candidate in candidates
    }
    if len(profiles) != 1:
        raise ValueError("chunk transfer report requires one profile per source_ref")


def _require_uniform_source_kind(candidates: tuple[CandidateAssertionRecord, ...]) -> None:
    """Fail loudly when one source_ref spans multiple source kinds in one report."""

    source_kinds = {candidate.provenance.source_kind for candidate in candidates}
    if len(source_kinds) != 1:
        raise ValueError("chunk transfer report requires one source_kind per source_ref")


__all__ = [
    "ChunkTransferCandidateSummary",
    "ChunkTransferReport",
    "ChunkTransferReportService",
    "ChunkTransferReportSummary",
    "ChunkTransferVerdict",
]

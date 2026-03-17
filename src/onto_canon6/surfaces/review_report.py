"""Typed report surface for the Phase 2 review workflow.

This module is intentionally small. It does not own business rules for
validation or review transitions; it turns persisted pipeline state into a
queryable, inspectable report shape suitable for notebooks and future surfaces.
"""

from __future__ import annotations

from collections import Counter

from pydantic import BaseModel, ConfigDict, Field

from ..pipeline import (
    CandidateAssertionRecord,
    CandidateReviewStatus,
    CandidateValidationStatus,
    OverlayApplicationRecord,
    OverlayApplicationService,
    ProposalRecord,
    ProposalStatus,
    ReviewService,
)


class ReviewReportSummary(BaseModel):
    """Summarize the candidate and proposal rows returned by one report."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    total_candidates: int = Field(ge=0)
    total_proposals: int = Field(ge=0)
    total_overlay_applications: int = Field(ge=0)
    candidate_review_status_counts: dict[str, int] = Field(default_factory=dict)
    candidate_validation_status_counts: dict[str, int] = Field(default_factory=dict)
    proposal_status_counts: dict[str, int] = Field(default_factory=dict)
    overlay_pack_counts: dict[str, int] = Field(default_factory=dict)


class ReviewReport(BaseModel):
    """Bundle filtered candidates, filtered proposals, and summary counts."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    candidates: tuple[CandidateAssertionRecord, ...]
    proposals: tuple[ProposalRecord, ...]
    overlay_applications: tuple[OverlayApplicationRecord, ...]
    summary: ReviewReportSummary


class ReviewReportService:
    """Build typed report views over the persisted review store."""

    def __init__(
        self,
        *,
        review_service: ReviewService | None = None,
        overlay_service: OverlayApplicationService | None = None,
    ) -> None:
        """Use provided services or construct matching config-backed defaults."""

        self._review_service = review_service or ReviewService()
        self._overlay_service = overlay_service or OverlayApplicationService(
            db_path=self._review_service.store.db_path,
            overlay_root=self._review_service.overlay_root,
        )

    def build_report(
        self,
        *,
        review_status_filter: CandidateReviewStatus | None = None,
        validation_status_filter: CandidateValidationStatus | None = None,
        proposal_status_filter: ProposalStatus | None = None,
        profile_id: str | None = None,
        profile_version: str | None = None,
    ) -> ReviewReport:
        """Return one inspectable report over candidate and proposal state.

        The report intentionally mirrors the current proving slice:

        - candidates can be filtered by review status, validation status, and
          profile;
        - proposals can be filtered by proposal status and profile;
        - summary counts are computed from the returned rows, not hidden global
          state.
        """

        candidates = tuple(
            self._review_service.list_candidate_assertions(
                review_status_filter=review_status_filter,
                validation_status_filter=validation_status_filter,
                profile_id=profile_id,
                profile_version=profile_version,
                proposal_status_filter=proposal_status_filter,
            )
        )
        proposals = tuple(
            self._review_service.list_proposals(
                status_filter=proposal_status_filter,
                profile_id=profile_id,
                profile_version=profile_version,
            )
        )
        overlay_applications = tuple(
            self._overlay_service.list_overlay_applications(
                profile_id=profile_id,
                profile_version=profile_version,
            )
        )
        return ReviewReport(
            candidates=candidates,
            proposals=proposals,
            overlay_applications=overlay_applications,
            summary=ReviewReportSummary(
                total_candidates=len(candidates),
                total_proposals=len(proposals),
                total_overlay_applications=len(overlay_applications),
                candidate_review_status_counts=dict(
                    Counter(candidate.review_status for candidate in candidates)
                ),
                candidate_validation_status_counts=dict(
                    Counter(candidate.validation_status for candidate in candidates)
                ),
                proposal_status_counts=dict(Counter(proposal.status for proposal in proposals)),
                overlay_pack_counts=dict(
                    Counter(
                        f"{application.overlay_pack.pack_id}@{application.overlay_pack.pack_version}"
                        for application in overlay_applications
                    )
                ),
            ),
        )


__all__ = ["ReviewReport", "ReviewReportService", "ReviewReportSummary"]

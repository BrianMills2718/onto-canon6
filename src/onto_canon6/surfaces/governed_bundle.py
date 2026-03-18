"""Typed product-facing export surface for the first governed workflow.

This surface deliberately composes the already-proved services instead of
creating a new orchestration runtime. It exports one inspectable JSON-friendly
bundle over accepted candidate assertions, linked ontology-governance state,
candidate-centered artifact lineage, and extension-local epistemic state.
"""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field

from ..artifacts import ArtifactLineageEdge, ArtifactLineageService, ArtifactRecord, CandidateArtifactLinkRecord
from ..extensions.epistemic import (
    ConfidenceAssessmentRecord,
    EpistemicCandidateStatus,
    EpistemicService,
    SupersessionRecord,
)
from .epistemic_report import EpistemicReportService
from ..pipeline import CandidateAssertionRecord, OverlayApplicationRecord, ProposalRecord, ReviewService


class GovernedBundleScope(BaseModel):
    """Describe the accepted-candidate slice exported by one bundle."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    review_status_filter: str = Field(default="accepted", min_length=1)
    profile_id: str | None = None
    profile_version: str | None = None
    candidate_ids: tuple[str, ...] = ()


class GovernedCandidateBundle(BaseModel):
    """Bundle one accepted candidate with its linked governance and provenance state."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    candidate: CandidateAssertionRecord
    linked_proposals: tuple[ProposalRecord, ...] = ()
    linked_overlay_applications: tuple[OverlayApplicationRecord, ...] = ()
    artifact_links: tuple[CandidateArtifactLinkRecord, ...] = ()
    artifacts: tuple[ArtifactRecord, ...] = ()
    lineage_edges: tuple[ArtifactLineageEdge, ...] = ()
    epistemic_status: EpistemicCandidateStatus
    confidence: ConfidenceAssessmentRecord | None = None
    superseded_by: SupersessionRecord | None = None
    supersedes: tuple[SupersessionRecord, ...] = ()


class GovernedWorkflowBundleSummary(BaseModel):
    """Summarize one exported governed workflow bundle."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    total_candidates: int = Field(ge=0)
    total_linked_proposals: int = Field(ge=0)
    total_overlay_applications: int = Field(ge=0)
    total_candidates_with_artifacts: int = Field(ge=0)
    total_candidates_with_confidence: int = Field(ge=0)
    total_superseded_candidates: int = Field(ge=0)
    profile_counts: dict[str, int] = Field(default_factory=dict)


class GovernedWorkflowBundle(BaseModel):
    """Export one product-facing governed workflow artifact."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    workflow_id: str = Field(default="governed_text_to_reviewed_assertions", min_length=1)
    generated_at: str = Field(min_length=1)
    scope: GovernedBundleScope
    candidate_bundles: tuple[GovernedCandidateBundle, ...] = ()
    summary: GovernedWorkflowBundleSummary


class GovernedWorkflowBundleService:
    """Export accepted governed assertions through a thin typed surface.

    The service intentionally stays narrow:

    1. accepted candidates remain the only exported subject in this phase;
    2. proposal, overlay, artifact, and epistemic state are gathered through
       already-proved services;
    3. no new business rules for review or ontology mutation are introduced
       here.
    """

    def __init__(
        self,
        *,
        review_service: ReviewService | None = None,
        artifact_service: ArtifactLineageService | None = None,
        epistemic_report_service: EpistemicReportService | None = None,
    ) -> None:
        """Use provided services or construct config-backed defaults."""

        self._review_service = review_service or ReviewService()
        self._artifact_service = artifact_service or ArtifactLineageService(
            db_path=self._review_service.store.db_path,
        )
        self._epistemic_service = epistemic_report_service or EpistemicReportService(
            epistemic_service=EpistemicService(db_path=self._review_service.store.db_path)
        )

    def build_bundle(
        self,
        *,
        profile_id: str | None = None,
        profile_version: str | None = None,
        candidate_ids: tuple[str, ...] = (),
    ) -> GovernedWorkflowBundle:
        """Return one exportable bundle over accepted candidate assertions.

        This fails loudly if explicit `candidate_ids` include rows that are not
        present in the selected accepted-candidate scope.
        """

        normalized_candidate_ids = _normalize_candidate_ids(candidate_ids)
        accepted_candidates = tuple(
            self._review_service.list_candidate_assertions(
                review_status_filter="accepted",
                profile_id=profile_id,
                profile_version=profile_version,
            )
        )
        selected_candidates = _select_candidates(
            accepted_candidates=accepted_candidates,
            candidate_ids=normalized_candidate_ids,
        )
        proposal_lookup = {
            proposal.proposal_id: proposal
            for proposal in self._review_service.list_proposals(
                profile_id=profile_id,
                profile_version=profile_version,
            )
        }
        candidate_bundles = tuple(
            self._build_candidate_bundle(
                candidate=candidate,
                proposal_lookup=proposal_lookup,
            )
            for candidate in selected_candidates
        )
        return GovernedWorkflowBundle(
            generated_at=_now_iso(),
            scope=GovernedBundleScope(
                profile_id=profile_id,
                profile_version=profile_version,
                candidate_ids=normalized_candidate_ids,
            ),
            candidate_bundles=candidate_bundles,
            summary=_build_summary(candidate_bundles),
        )

    def _build_candidate_bundle(
        self,
        *,
        candidate: CandidateAssertionRecord,
        proposal_lookup: dict[str, ProposalRecord],
    ) -> GovernedCandidateBundle:
        """Bundle one accepted candidate with linked proposal, lineage, and epistemic state."""

        linked_proposals = tuple(
            _require_linked_proposal(
                proposal_lookup=proposal_lookup,
                proposal_id=proposal_id,
                candidate_id=candidate.candidate_id,
            )
            for proposal_id in candidate.proposal_ids
        )
        linked_overlay_applications = tuple(
            proposal.overlay_application
            for proposal in linked_proposals
            if proposal.overlay_application is not None
        )
        lineage_report = self._artifact_service.build_candidate_lineage_report(
            candidate_id=candidate.candidate_id,
        )
        epistemic_report = self._epistemic_service.build_candidate_report(
            candidate_id=candidate.candidate_id,
        )
        return GovernedCandidateBundle(
            candidate=candidate,
            linked_proposals=linked_proposals,
            linked_overlay_applications=linked_overlay_applications,
            artifact_links=lineage_report.direct_artifact_links,
            artifacts=lineage_report.artifacts,
            lineage_edges=lineage_report.lineage_edges,
            epistemic_status=epistemic_report.epistemic_status,
            confidence=epistemic_report.confidence,
            superseded_by=epistemic_report.superseded_by,
            supersedes=epistemic_report.supersedes,
        )


def _normalize_candidate_ids(candidate_ids: tuple[str, ...]) -> tuple[str, ...]:
    """Normalize an explicit candidate-id filter while preserving order."""

    normalized: list[str] = []
    for candidate_id in candidate_ids:
        value = candidate_id.strip()
        if not value:
            raise ValueError("candidate_ids must not contain blank values")
        if value not in normalized:
            normalized.append(value)
    return tuple(normalized)


def _select_candidates(
    *,
    accepted_candidates: tuple[CandidateAssertionRecord, ...],
    candidate_ids: tuple[str, ...],
) -> tuple[CandidateAssertionRecord, ...]:
    """Return the selected accepted candidates or fail loudly for missing ids."""

    if not candidate_ids:
        return accepted_candidates
    candidate_lookup = {
        candidate.candidate_id: candidate for candidate in accepted_candidates
    }
    missing = tuple(candidate_id for candidate_id in candidate_ids if candidate_id not in candidate_lookup)
    if missing:
        raise ValueError(
            "candidate_ids must reference accepted candidates in the selected scope: "
            + ", ".join(missing)
        )
    return tuple(candidate_lookup[candidate_id] for candidate_id in candidate_ids)


def _require_linked_proposal(
    *,
    proposal_lookup: dict[str, ProposalRecord],
    proposal_id: str,
    candidate_id: str,
) -> ProposalRecord:
    """Return one linked proposal or fail loudly if review state is inconsistent."""

    try:
        return proposal_lookup[proposal_id]
    except KeyError as exc:
        raise ValueError(
            f"candidate {candidate_id} references missing proposal_id {proposal_id}"
        ) from exc


def _build_summary(
    candidate_bundles: tuple[GovernedCandidateBundle, ...],
) -> GovernedWorkflowBundleSummary:
    """Compute stable summary counts from the exported candidate bundles."""

    linked_proposal_ids = tuple(
        proposal.proposal_id
        for bundle in candidate_bundles
        for proposal in bundle.linked_proposals
    )
    overlay_application_ids = tuple(
        application.application_id
        for bundle in candidate_bundles
        for application in bundle.linked_overlay_applications
    )
    return GovernedWorkflowBundleSummary(
        total_candidates=len(candidate_bundles),
        total_linked_proposals=len(dict.fromkeys(linked_proposal_ids)),
        total_overlay_applications=len(dict.fromkeys(overlay_application_ids)),
        total_candidates_with_artifacts=sum(1 for bundle in candidate_bundles if bundle.artifact_links),
        total_candidates_with_confidence=sum(
            1 for bundle in candidate_bundles if bundle.confidence is not None
        ),
        total_superseded_candidates=sum(
            1 for bundle in candidate_bundles if bundle.epistemic_status == "superseded"
        ),
        profile_counts=dict(
            Counter(
                f"{bundle.candidate.profile.profile_id}@{bundle.candidate.profile.profile_version}"
                for bundle in candidate_bundles
            )
        ),
    )


def _now_iso() -> str:
    """Return an ISO-8601 UTC timestamp with stable formatting."""

    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


__all__ = [
    "GovernedBundleScope",
    "GovernedCandidateBundle",
    "GovernedWorkflowBundle",
    "GovernedWorkflowBundleService",
    "GovernedWorkflowBundleSummary",
]

"""Typed report surface for the first canonical-graph recovery slice.

This report surface keeps the Phase 11 graph layer thin and inspectable. It
does not duplicate governance, artifact, or epistemic data into graph tables.
Instead it bundles:

1. one promoted assertion and its materialized role/entity records;
2. the source accepted candidate that justified promotion;
3. candidate-backed proposal, overlay, lineage, and epistemic context.
"""

from __future__ import annotations

from collections import Counter

from pydantic import BaseModel, ConfigDict, Field

from ..artifacts import ArtifactLineageEdge, ArtifactLineageService, ArtifactRecord, CandidateArtifactLinkRecord
from ..core import CanonicalGraphPromotionResult, CanonicalGraphService, PromotedGraphAssertionRecord, PromotedGraphEntityRecord, PromotedGraphRoleFillerRecord
from ..extensions.epistemic import (
    ConfidenceAssessmentRecord,
    EpistemicCandidateStatus,
    EpistemicService,
    SupersessionRecord,
)
from ..pipeline import CandidateAssertionRecord, OverlayApplicationRecord, ProposalRecord, ReviewService
from .epistemic_report import EpistemicReportService


class PromotedGraphAssertionBundle(BaseModel):
    """Bundle one promoted assertion with candidate-backed governance context."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    assertion: PromotedGraphAssertionRecord
    role_fillers: tuple[PromotedGraphRoleFillerRecord, ...] = ()
    entities: tuple[PromotedGraphEntityRecord, ...] = ()
    source_candidate: CandidateAssertionRecord
    linked_proposals: tuple[ProposalRecord, ...] = ()
    linked_overlay_applications: tuple[OverlayApplicationRecord, ...] = ()
    artifact_links: tuple[CandidateArtifactLinkRecord, ...] = ()
    artifacts: tuple[ArtifactRecord, ...] = ()
    lineage_edges: tuple[ArtifactLineageEdge, ...] = ()
    epistemic_status: EpistemicCandidateStatus
    confidence: ConfidenceAssessmentRecord | None = None
    superseded_by: SupersessionRecord | None = None
    supersedes: tuple[SupersessionRecord, ...] = ()


class PromotedGraphReportSummary(BaseModel):
    """Summarize one promoted-graph report."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    total_assertions: int = Field(ge=0)
    total_entities: int = Field(ge=0)
    total_assertions_with_artifacts: int = Field(ge=0)
    total_assertions_with_confidence: int = Field(ge=0)
    total_overlay_applications: int = Field(ge=0)
    profile_counts: dict[str, int] = Field(default_factory=dict)


class PromotedGraphReport(BaseModel):
    """Bundle promoted assertions plus traversed candidate-backed context."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    assertion_bundles: tuple[PromotedGraphAssertionBundle, ...] = ()
    summary: PromotedGraphReportSummary


class PromotedGraphReportService:
    """Build inspectable reports over the narrow promoted-graph slice."""

    def __init__(
        self,
        *,
        graph_service: CanonicalGraphService | None = None,
        review_service: ReviewService | None = None,
        artifact_service: ArtifactLineageService | None = None,
        epistemic_report_service: EpistemicReportService | None = None,
    ) -> None:
        """Use provided services or construct matching config-backed defaults."""

        self._graph_service = graph_service or CanonicalGraphService()
        self._review_service = review_service or ReviewService(db_path=self._graph_service.db_path)
        self._artifact_service = artifact_service or ArtifactLineageService(
            db_path=self._graph_service.db_path,
        )
        self._epistemic_report_service = (
            epistemic_report_service
            or EpistemicReportService(
                epistemic_service=EpistemicService(db_path=self._graph_service.db_path)
            )
        )

    def build_report(self) -> PromotedGraphReport:
        """Return one promoted-graph report over all persisted graph assertions."""

        promoted_assertions = tuple(self._graph_service.list_promoted_assertions())
        proposal_lookup = {
            proposal.proposal_id: proposal for proposal in self._review_service.list_proposals()
        }
        bundles = tuple(
            self._build_assertion_bundle(
                promotion=self._graph_service.get_promotion_result(
                    assertion_id=assertion.assertion_id
                ),
                proposal_lookup=proposal_lookup,
            )
            for assertion in promoted_assertions
        )
        return PromotedGraphReport(
            assertion_bundles=bundles,
            summary=_build_summary(bundles),
        )

    def _build_assertion_bundle(
        self,
        *,
        promotion: CanonicalGraphPromotionResult,
        proposal_lookup: dict[str, ProposalRecord],
    ) -> PromotedGraphAssertionBundle:
        """Bundle one promoted assertion with traversed candidate-backed state."""

        source_candidate = self._review_service.get_candidate_assertion(
            candidate_id=promotion.assertion.source_candidate_id
        )
        linked_proposals = tuple(
            _require_linked_proposal(
                proposal_lookup=proposal_lookup,
                proposal_id=proposal_id,
                candidate_id=source_candidate.candidate_id,
            )
            for proposal_id in source_candidate.proposal_ids
        )
        linked_overlay_applications = tuple(
            proposal.overlay_application
            for proposal in linked_proposals
            if proposal.overlay_application is not None
        )
        lineage_report = self._artifact_service.build_candidate_lineage_report(
            candidate_id=source_candidate.candidate_id,
        )
        epistemic_report = self._epistemic_report_service.build_candidate_report(
            candidate_id=source_candidate.candidate_id,
        )
        return PromotedGraphAssertionBundle(
            assertion=promotion.assertion,
            role_fillers=promotion.role_fillers,
            entities=promotion.entities,
            source_candidate=source_candidate,
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
    bundles: tuple[PromotedGraphAssertionBundle, ...],
) -> PromotedGraphReportSummary:
    """Compute stable summary counts from the promoted-graph bundles."""

    unique_entity_ids = {
        entity.entity_id for bundle in bundles for entity in bundle.entities
    }
    return PromotedGraphReportSummary(
        total_assertions=len(bundles),
        total_entities=len(unique_entity_ids),
        total_assertions_with_artifacts=sum(1 for bundle in bundles if bundle.artifact_links),
        total_assertions_with_confidence=sum(1 for bundle in bundles if bundle.confidence is not None),
        total_overlay_applications=sum(len(bundle.linked_overlay_applications) for bundle in bundles),
        profile_counts=dict(
            Counter(
                f"{bundle.assertion.profile.profile_id}@{bundle.assertion.profile.profile_version}"
                for bundle in bundles
            )
        ),
    )


__all__ = [
    "PromotedGraphAssertionBundle",
    "PromotedGraphReport",
    "PromotedGraphReportService",
    "PromotedGraphReportSummary",
]

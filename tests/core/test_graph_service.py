"""Tests for the first canonical-graph promotion slice."""

from __future__ import annotations

from pathlib import Path

import pytest

from onto_canon6.artifacts import ArtifactLineageService
from onto_canon6.core import CanonicalGraphPromotionConflictError, CanonicalGraphService
from onto_canon6.extensions.epistemic import EpistemicService
from onto_canon6.pipeline import OverlayApplicationService, ProposalAcceptancePolicy, ReviewService
from onto_canon6.surfaces import EpistemicReportService, PromotedGraphReportService


def _seed_review_service(tmp_path: Path) -> tuple[ReviewService, OverlayApplicationService]:
    """Create isolated review and overlay services for one graph test."""

    review_db_path = tmp_path / "review.sqlite3"
    overlay_root = tmp_path / "ontology_overlays"
    review_service = ReviewService(
        db_path=review_db_path,
        overlay_root=overlay_root,
        default_acceptance_policy="record_only",
    )
    overlay_service = OverlayApplicationService(
        db_path=review_db_path,
        overlay_root=overlay_root,
    )
    return review_service, overlay_service


def _submit_accepted_candidate(
    review_service: ReviewService,
    *,
    source_ref: str = "notes/promoted.txt",
    predicate: str = "oc:hold_command_role",
    profile_id: str = "default",
    profile_version: str = "1.0.0",
    proposal_acceptance_policy: ProposalAcceptancePolicy = "record_only",
) -> str:
    """Persist and accept one candidate suitable for graph promotion."""

    submission = review_service.submit_candidate_assertion(
        payload={
            "predicate": predicate,
            "roles": {
                "commander": [
                    {
                        "entity_id": "ent:person:eric_olson",
                        "entity_type": "oc:person",
                    }
                ],
                "organization": [
                    {
                        "entity_id": "ent:org:ussocom",
                        "entity_type": "oc:organization",
                    }
                ],
                "title": [
                    {
                        "kind": "value",
                        "value_kind": "string",
                        "value": "Commander",
                    }
                ],
            },
        },
        profile_id=profile_id,
        profile_version=profile_version,
        submitted_by="analyst:graph-seed",
        source_kind="text_file",
        source_ref=source_ref,
        source_text="Eric Olson served as commander of USSOCOM.",
        claim_text="Eric Olson held the commander role at USSOCOM.",
        evidence_spans=(
            {
                "start_char": 0,
                "end_char": 10,
                "text": "Eric Olson",
            },
        ),
    )
    if submission.proposals:
        review_service.review_proposal(
            proposal_id=submission.proposals[0].proposal_id,
            decision="accepted",
            actor_id="analyst:reviewer",
            acceptance_policy=proposal_acceptance_policy,
        )
    reviewed = review_service.review_candidate(
        candidate_id=submission.candidate.candidate_id,
        decision="accepted",
        actor_id="analyst:reviewer",
    )
    return reviewed.candidate_id


def test_promote_candidate_materializes_assertion_entities_and_fillers(tmp_path: Path) -> None:
    """Promotion should create deterministic assertion and entity graph records."""

    review_service, _overlay_service = _seed_review_service(tmp_path)
    candidate_id = _submit_accepted_candidate(review_service)

    graph_service = CanonicalGraphService(db_path=review_service.store.db_path)
    promotion = graph_service.promote_candidate(
        candidate_id=candidate_id,
        promoted_by="analyst:graph-promoter",
    )

    assert promotion.assertion.source_candidate_id == candidate_id
    assert promotion.assertion.predicate == "oc:hold_command_role"
    assert promotion.assertion.promoted_by == "analyst:graph-promoter"
    assert len(promotion.role_fillers) == 3
    assert {entity.entity_id for entity in promotion.entities} == {
        "ent:person:eric_olson",
        "ent:org:ussocom",
    }
    commander_filler = next(
        filler for filler in promotion.role_fillers if filler.role_id == "commander"
    )
    assert commander_filler.entity_id == "ent:person:eric_olson"
    assert commander_filler.filler_kind == "entity"
    title_filler = next(filler for filler in promotion.role_fillers if filler.role_id == "title")
    assert title_filler.filler_kind == "value"
    assert title_filler.value_kind == "string"


def test_promote_candidate_is_idempotent_for_same_accepted_candidate(tmp_path: Path) -> None:
    """Repeated promotion should return the existing promoted assertion instead of duplicating it."""

    review_service, _overlay_service = _seed_review_service(tmp_path)
    candidate_id = _submit_accepted_candidate(review_service)
    graph_service = CanonicalGraphService(db_path=review_service.store.db_path)

    first = graph_service.promote_candidate(
        candidate_id=candidate_id,
        promoted_by="analyst:first",
    )
    second = graph_service.promote_candidate(
        candidate_id=candidate_id,
        promoted_by="analyst:second",
    )

    assert second.assertion.assertion_id == first.assertion.assertion_id
    assert second.assertion.promoted_by == "analyst:first"
    assert graph_service.list_promoted_assertions() == [first.assertion]


def test_promote_candidate_fails_loudly_for_non_accepted_candidates(tmp_path: Path) -> None:
    """Only accepted candidates may become promoted graph assertions."""

    review_service, _overlay_service = _seed_review_service(tmp_path)
    pending = review_service.submit_candidate_assertion(
        payload={"predicate": "oc:pending_graph_demo", "roles": {"subject": []}},
        profile_id="default",
        profile_version="1.0.0",
        submitted_by="analyst:graph-seed",
        source_kind="text_file",
        source_ref="notes/pending.txt",
    )
    graph_service = CanonicalGraphService(db_path=review_service.store.db_path)

    with pytest.raises(
        CanonicalGraphPromotionConflictError,
        match="canonical graph promotion requires accepted candidate",
    ):
        graph_service.promote_candidate(
            candidate_id=pending.candidate.candidate_id,
            promoted_by="analyst:graph-promoter",
        )


def test_promoted_graph_report_traverses_candidate_context_without_duplication(
    tmp_path: Path,
) -> None:
    """Graph reports should expose promoted state plus candidate-backed governance context."""

    review_service, overlay_service = _seed_review_service(tmp_path)
    candidate_id = _submit_accepted_candidate(
        review_service,
        predicate="oc:hold_command_role_variant",
        profile_id="psyop_seed",
        profile_version="0.1.0",
        proposal_acceptance_policy="apply_to_overlay",
    )
    proposal = review_service.list_proposals(status_filter="accepted")[0]
    overlay_service.apply_proposal_to_overlay(
        proposal_id=proposal.proposal_id,
        applied_by="analyst:overlay",
    )
    artifact_service = ArtifactLineageService(db_path=review_service.store.db_path)
    artifact = artifact_service.register_artifact(
        artifact_kind="source",
        uri="notes/promoted.txt",
        label="promoted note",
    )
    artifact_service.link_candidate_artifact(
        candidate_id=candidate_id,
        artifact_id=artifact.artifact_id,
        support_kind="quoted_from",
        reference_detail="primary mention",
    )
    epistemic_service = EpistemicService(db_path=review_service.store.db_path)
    epistemic_service.record_confidence(
        candidate_id=candidate_id,
        confidence_score=0.91,
        source_kind="user",
        actor_id="analyst:confidence",
        rationale="Accepted and reviewed before promotion.",
    )
    graph_service = CanonicalGraphService(db_path=review_service.store.db_path)
    promoted = graph_service.promote_candidate(
        candidate_id=candidate_id,
        promoted_by="analyst:graph-promoter",
    )

    report = PromotedGraphReportService(
        graph_service=graph_service,
        review_service=review_service,
        artifact_service=artifact_service,
        epistemic_report_service=EpistemicReportService(epistemic_service=epistemic_service),
    ).build_report()

    assert report.summary.total_assertions == 1
    assert report.summary.total_entities == 2
    assert report.summary.total_assertions_with_artifacts == 1
    assert report.summary.total_assertions_with_confidence == 1
    bundle = report.assertion_bundles[0]
    assert bundle.assertion.assertion_id == promoted.assertion.assertion_id
    assert bundle.source_candidate.candidate_id == candidate_id
    assert bundle.linked_proposals[0].proposal_id == proposal.proposal_id
    assert bundle.linked_overlay_applications[0].proposal_id == proposal.proposal_id
    assert bundle.artifact_links[0].artifact_id == artifact.artifact_id
    assert bundle.epistemic_status == "active"
    assert bundle.confidence is not None
    assert bundle.confidence.confidence_score == pytest.approx(0.91)

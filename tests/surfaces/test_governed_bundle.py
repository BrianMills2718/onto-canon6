"""Tests for the first product-facing governed bundle export surface."""

from __future__ import annotations

from pathlib import Path

import pytest

from onto_canon6.artifacts import ArtifactLineageService
from onto_canon6.extensions.epistemic import EpistemicService
from onto_canon6.pipeline import OverlayApplicationService, ReviewService
from onto_canon6.surfaces import EpistemicReportService, GovernedWorkflowBundleService
from tests.compatibility_helpers import load_json_fixture, normalize_snapshot


def _seed_accepted_candidate_with_overlay(
    *,
    tmp_path: Path,
) -> tuple[Path, Path, str, str]:
    """Persist one accepted mixed-mode candidate plus its accepted overlay proposal."""

    review_db_path = tmp_path / "review.sqlite3"
    overlay_root = tmp_path / "ontology_overlays"
    review_service = ReviewService(db_path=review_db_path, overlay_root=overlay_root)
    overlay_service = OverlayApplicationService(
        db_path=review_db_path,
        overlay_root=overlay_root,
    )
    submission = review_service.submit_candidate_assertion(
        payload={
            "predicate": "oc:signals_alignment",
            "roles": {
                "subject": [{"kind": "value", "value_kind": "string", "value": "Campaign Alpha"}],
                "object": [
                    {
                        "kind": "value",
                        "value_kind": "string",
                        "value": "aligned messaging",
                    }
                ],
            },
        },
        profile_id="psyop_seed",
        profile_version="0.1.0",
        submitted_by="analyst:test",
        source_kind="text_file",
        source_ref="fixture.txt",
        source_text="Campaign Alpha used aligned messaging across channels.",
    )
    candidate = review_service.review_candidate(
        candidate_id=submission.candidate.candidate_id,
        decision="accepted",
        actor_id="analyst:reviewer",
    )
    proposal = review_service.review_proposal(
        proposal_id=submission.proposals[0].proposal_id,
        decision="accepted",
        actor_id="analyst:reviewer",
        acceptance_policy="apply_to_overlay",
    )
    overlay_service.apply_proposal_to_overlay(
        proposal_id=proposal.proposal_id,
        applied_by="analyst:reviewer",
    )
    return review_db_path, overlay_root, candidate.candidate_id, proposal.proposal_id


def test_build_bundle_includes_governance_lineage_and_epistemic_state(tmp_path: Path) -> None:
    """The bundle should export accepted candidates with linked governance and optional enrichments."""

    review_db_path, overlay_root, candidate_id, proposal_id = _seed_accepted_candidate_with_overlay(
        tmp_path=tmp_path,
    )
    artifact_service = ArtifactLineageService(db_path=review_db_path)
    source_artifact = artifact_service.register_artifact(
        artifact_kind="source",
        uri="fixture.txt",
        label="fixture source",
    )
    artifact_service.link_candidate_artifact(
        candidate_id=candidate_id,
        artifact_id=source_artifact.artifact_id,
        support_kind="quoted_from",
        reference_detail="aligned messaging span",
    )
    epistemic_service = EpistemicService(db_path=review_db_path)
    epistemic_service.record_confidence(
        candidate_id=candidate_id,
        confidence_score=0.83,
        source_kind="user",
        actor_id="analyst:reviewer",
        rationale="Reviewed and accepted after governance.",
    )

    bundle = GovernedWorkflowBundleService(
        review_service=ReviewService(db_path=review_db_path, overlay_root=overlay_root),
        artifact_service=artifact_service,
        epistemic_report_service=EpistemicReportService(epistemic_service=epistemic_service),
    ).build_bundle()

    assert bundle.summary.total_candidates == 1
    assert bundle.summary.total_linked_proposals == 1
    assert bundle.summary.total_overlay_applications == 1
    assert bundle.summary.total_candidates_with_artifacts == 1
    assert bundle.summary.total_candidates_with_confidence == 1
    candidate_bundle = bundle.candidate_bundles[0]
    assert candidate_bundle.candidate.candidate_id == candidate_id
    assert candidate_bundle.linked_proposals[0].proposal_id == proposal_id
    assert candidate_bundle.linked_overlay_applications[0].proposal_id == proposal_id
    assert candidate_bundle.artifact_links[0].support_kind == "quoted_from"
    assert candidate_bundle.epistemic_status == "active"
    assert candidate_bundle.confidence is not None
    assert candidate_bundle.confidence.confidence_score == pytest.approx(0.83)
    assert normalize_snapshot(bundle.model_dump(mode="json")) == load_json_fixture(
        "governed_bundle",
        "minimal_governed_bundle.json",
    )


def test_bundle_filter_fails_loud_for_non_accepted_candidate_id(tmp_path: Path) -> None:
    """Explicit candidate filters should reject ids outside the accepted export scope."""

    review_db_path = tmp_path / "review.sqlite3"
    overlay_root = tmp_path / "ontology_overlays"
    review_service = ReviewService(db_path=review_db_path, overlay_root=overlay_root)
    submission = review_service.submit_candidate_assertion(
        payload={"predicate": "oc:pending_candidate", "roles": {}},
        profile_id="default",
        profile_version="1.0.0",
        submitted_by="analyst:test",
        source_kind="text_file",
        source_ref="pending.txt",
    )

    bundle_service = GovernedWorkflowBundleService(
        review_service=review_service,
        artifact_service=ArtifactLineageService(db_path=review_db_path),
        epistemic_report_service=EpistemicReportService(
            epistemic_service=EpistemicService(db_path=review_db_path)
        ),
    )

    with pytest.raises(
        ValueError,
        match="candidate_ids must reference accepted candidates",
    ):
        bundle_service.build_bundle(candidate_ids=(submission.candidate.candidate_id,))

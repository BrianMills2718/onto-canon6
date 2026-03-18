"""Integration tests for the Phase 11 promoted-graph CLI surface."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from onto_canon6.artifacts import ArtifactLineageService
from onto_canon6 import cli as cli_module
from onto_canon6.extensions.epistemic import EpistemicService
from onto_canon6.pipeline import OverlayApplicationService, ReviewService


def test_cli_promotes_and_reports_graph_state(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The CLI should promote accepted candidates and export graph-backed context."""

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
    submission = review_service.submit_candidate_assertion(
        payload={
            "predicate": "oc:hold_command_role_variant",
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
        profile_id="psyop_seed",
        profile_version="0.1.0",
        submitted_by="analyst:cli-graph-seed",
        source_kind="text_file",
        source_ref="notes/promoted.txt",
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
    proposal = review_service.review_proposal(
        proposal_id=submission.proposals[0].proposal_id,
        decision="accepted",
        actor_id="analyst:reviewer",
        acceptance_policy="apply_to_overlay",
    )
    overlay_service.apply_proposal_to_overlay(
        proposal_id=proposal.proposal_id,
        applied_by="analyst:overlay",
    )
    candidate = review_service.review_candidate(
        candidate_id=submission.candidate.candidate_id,
        decision="accepted",
        actor_id="analyst:reviewer",
    )
    artifact_service = ArtifactLineageService(db_path=review_db_path)
    artifact = artifact_service.register_artifact(
        artifact_kind="source",
        uri="notes/promoted.txt",
        label="promoted note",
    )
    artifact_service.link_candidate_artifact(
        candidate_id=candidate.candidate_id,
        artifact_id=artifact.artifact_id,
        support_kind="quoted_from",
        reference_detail="primary mention",
    )
    EpistemicService(db_path=review_db_path).record_confidence(
        candidate_id=candidate.candidate_id,
        confidence_score=0.88,
        source_kind="user",
        actor_id="analyst:confidence",
        rationale="Accepted before promotion.",
    )

    exit_code = cli_module.main(
        [
            "promote-candidate",
            "--candidate-id",
            candidate.candidate_id,
            "--actor-id",
            "analyst:promoter",
            "--review-db-path",
            str(review_db_path),
            "--output",
            "json",
        ]
    )
    assert exit_code == 0
    promotion_output = json.loads(_read_stdout(capsys))
    assert promotion_output["assertion"]["source_candidate_id"] == candidate.candidate_id
    assert promotion_output["assertion"]["promoted_by"] == "analyst:promoter"
    assert len(promotion_output["entities"]) == 2

    exit_code = cli_module.main(
        [
            "list-promoted-assertions",
            "--review-db-path",
            str(review_db_path),
            "--output",
            "json",
        ]
    )
    assert exit_code == 0
    assertions_output = json.loads(_read_stdout(capsys))
    assert len(assertions_output) == 1
    assert assertions_output[0]["source_candidate_id"] == candidate.candidate_id

    exit_code = cli_module.main(
        [
            "export-promoted-graph-report",
            "--review-db-path",
            str(review_db_path),
            "--output",
            "json",
        ]
    )
    assert exit_code == 0
    report_output = json.loads(_read_stdout(capsys))
    assert report_output["summary"]["total_assertions"] == 1
    assert report_output["summary"]["total_entities"] == 2
    assert report_output["summary"]["total_assertions_with_artifacts"] == 1
    assert report_output["summary"]["total_assertions_with_confidence"] == 1
    bundle = report_output["assertion_bundles"][0]
    assert bundle["source_candidate"]["candidate_id"] == candidate.candidate_id
    assert bundle["linked_proposals"][0]["proposal_id"] == proposal.proposal_id
    assert bundle["linked_overlay_applications"][0]["proposal_id"] == proposal.proposal_id
    assert bundle["artifact_links"][0]["artifact_id"] == artifact.artifact_id
    assert bundle["confidence"]["confidence_score"] == 0.88


def _read_stdout(capsys: pytest.CaptureFixture[str]) -> str:
    """Return captured stdout text from a pytest capsys fixture."""

    captured = capsys.readouterr()
    return captured.out

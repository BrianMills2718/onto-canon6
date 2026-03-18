"""Integration tests for the Phase 15 promoted-assertion epistemic CLI surface."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from onto_canon6 import cli as cli_module
from onto_canon6.core import CanonicalGraphService
from onto_canon6.extensions.epistemic import EpistemicService
from onto_canon6.pipeline import ReviewService


def test_cli_records_assertion_disposition_and_exports_epistemic_report(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The CLI should expose promoted-assertion dispositions and report state."""

    review_db_path = tmp_path / "review.sqlite3"
    review_service = ReviewService(
        db_path=review_db_path,
        overlay_root=tmp_path / "ontology_overlays",
        default_acceptance_policy="record_only",
    )
    graph_service = CanonicalGraphService(db_path=review_db_path)
    epistemic_service = EpistemicService(db_path=review_db_path)

    first_candidate_id = _submit_and_accept(
        review_service,
        payload={
            "predicate": "oc:hold_command_role",
            "roles": {
                "commander": [{"entity_id": "ent:person:eric_olson"}],
                "organization": [{"entity_id": "ent:org:ussocom"}],
                "title": [{"kind": "value", "value_kind": "string", "value": "Commander"}],
            },
        },
        source_ref="notes/cli-epistemic-a.txt",
    )
    second_candidate_id = _submit_and_accept(
        review_service,
        payload={
            "predicate": "oc:hold_command_role",
            "roles": {
                "commander": [{"entity_id": "ent:person:eric_olson"}],
                "organization": [{"entity_id": "ent:org:ussocom"}],
                "title": [{"kind": "value", "value_kind": "string", "value": "Director"}],
            },
        },
        source_ref="notes/cli-epistemic-b.txt",
    )
    first_assertion = graph_service.promote_candidate(
        candidate_id=first_candidate_id,
        promoted_by="analyst:graph-promoter",
    ).assertion
    graph_service.promote_candidate(
        candidate_id=second_candidate_id,
        promoted_by="analyst:graph-promoter",
    )
    epistemic_service.record_confidence(
        candidate_id=first_candidate_id,
        confidence_score=0.77,
        source_kind="user",
        actor_id="analyst:confidence",
    )

    exit_code = cli_module.main(
        [
            "record-assertion-disposition",
            "--assertion-id",
            first_assertion.assertion_id,
            "--target-status",
            "weakened",
            "--actor-id",
            "analyst:epistemic",
            "--reason",
            "New contradictory evidence lowered confidence.",
            "--review-db-path",
            str(review_db_path),
            "--output",
            "json",
        ]
    )
    assert exit_code == 0
    disposition_output = json.loads(_read_stdout(capsys))
    assert disposition_output["assertion_id"] == first_assertion.assertion_id
    assert disposition_output["prior_status"] == "active"
    assert disposition_output["target_status"] == "weakened"

    exit_code = cli_module.main(
        [
            "export-assertion-epistemic-report",
            "--review-db-path",
            str(review_db_path),
            "--output",
            "json",
        ]
    )
    assert exit_code == 0
    report_output = json.loads(_read_stdout(capsys))
    assert report_output["summary"]["total_assertions"] == 2
    assert report_output["summary"]["total_weakened"] == 1
    assert report_output["summary"]["total_tension_pairs"] == 1
    weakened_report = next(
        item
        for item in report_output["assertion_reports"]
        if item["assertion"]["assertion_id"] == first_assertion.assertion_id
    )
    assert weakened_report["epistemic_status"] == "weakened"
    assert weakened_report["confidence"]["confidence_score"] == 0.77
    assert weakened_report["current_disposition"]["target_status"] == "weakened"
    assert weakened_report["tensions"][0]["tension_kind"] == "role_filler_conflict"


def _submit_and_accept(
    review_service: ReviewService,
    *,
    payload: dict[str, object],
    source_ref: str,
) -> str:
    """Persist and accept one candidate for the CLI epistemic flow."""

    submission = review_service.submit_candidate_assertion(
        payload=payload,
        profile_id="default",
        profile_version="1.0.0",
        submitted_by="analyst:cli-epistemic",
        source_kind="note",
        source_ref=source_ref,
    )
    return review_service.review_candidate(
        candidate_id=submission.candidate.candidate_id,
        decision="accepted",
        actor_id="analyst:reviewer",
    ).candidate_id


def _read_stdout(capsys: pytest.CaptureFixture[str]) -> str:
    """Return captured stdout text from a pytest capsys fixture."""

    captured = capsys.readouterr()
    return captured.out

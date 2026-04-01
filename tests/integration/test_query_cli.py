"""Integration tests for the read-only query/browse CLI surface."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from onto_canon6 import cli as cli_module
from onto_canon6.artifacts import ArtifactLineageService
from onto_canon6.core import CanonicalGraphService, IdentityService
from onto_canon6.pipeline import ReviewService


def test_cli_query_surface_supports_all_five_operations(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The CLI should expose the first read-only query operations end to end."""

    review_db_path = tmp_path / "review.sqlite3"
    _first_assertion_id, second_assertion_id = _seed_query_cli_state(review_db_path)

    exit_code = cli_module.main(
        [
            "search-entities",
            "--query",
            "Admiral Eric Olson",
            "--review-db-path",
            str(review_db_path),
            "--output",
            "json",
        ]
    )
    assert exit_code == 0
    entity_results = json.loads(_read_stdout(capsys))
    assert entity_results[0]["entity_id"] == "ent:person:admiral_eric_olson"
    assert entity_results[0]["match_reason"] == "alias_exact"

    exit_code = cli_module.main(
        [
            "get-entity",
            "--entity-id",
            "ent:person:eric_olson",
            "--review-db-path",
            str(review_db_path),
            "--output",
            "json",
        ]
    )
    assert exit_code == 0
    entity_detail = json.loads(_read_stdout(capsys))
    assert entity_detail["identity_bundle"]["identity"]["display_label"] == "Eric Olson"
    assert len(entity_detail["linked_assertions"]) == 2

    exit_code = cli_module.main(
        [
            "search-promoted-assertions",
            "--entity-id",
            "ent:person:admiral_eric_olson",
            "--review-db-path",
            str(review_db_path),
            "--output",
            "json",
        ]
    )
    assert exit_code == 0
    assertion_results = json.loads(_read_stdout(capsys))
    assert [result["assertion_id"] for result in assertion_results] == [second_assertion_id]

    exit_code = cli_module.main(
        [
            "get-promoted-assertion",
            "--assertion-id",
            second_assertion_id,
            "--review-db-path",
            str(review_db_path),
            "--output",
            "json",
        ]
    )
    assert exit_code == 0
    assertion_detail = json.loads(_read_stdout(capsys))
    assert assertion_detail["promotion"]["assertion"]["assertion_id"] == second_assertion_id
    assert assertion_detail["evidence"]["source_artifact"]["source_ref"] == "notes/admiral_eric_olson.txt"
    assert assertion_detail["epistemic_report"]["epistemic_status"] == "active"

    exit_code = cli_module.main(
        [
            "get-evidence",
            "--assertion-id",
            second_assertion_id,
            "--review-db-path",
            str(review_db_path),
            "--output",
            "json",
        ]
    )
    assert exit_code == 0
    evidence = json.loads(_read_stdout(capsys))
    assert evidence["evidence_spans"][0]["text"] == "Admiral Eric Olson"
    assert evidence["source_artifact"]["source_ref"] == "notes/admiral_eric_olson.txt"


def test_cli_query_surface_fails_loudly_for_missing_entity(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Missing query-surface objects should produce typed loud failures."""

    review_db_path = tmp_path / "review.sqlite3"
    _seed_query_cli_state(review_db_path)

    exit_code = cli_module.main(
        [
            "get-entity",
            "--entity-id",
            "ent:missing",
            "--review-db-path",
            str(review_db_path),
            "--output",
            "json",
        ]
    )

    assert exit_code == 1
    captured = capsys.readouterr()
    assert "QuerySurfaceNotFoundError" in captured.err
    assert "promoted entity not found" in captured.err


def _seed_query_cli_state(review_db_path: Path) -> tuple[str, str]:
    """Seed a small promoted-state slice for query CLI integration tests."""

    review_service = ReviewService(
        db_path=review_db_path,
        overlay_root=review_db_path.parent / "ontology_overlays",
        default_acceptance_policy="record_only",
    )
    first_assertion_id = _submit_accept_and_promote(
        review_service,
        predicate="oc:hold_command_role",
        person_entity_id="ent:person:eric_olson",
        person_name="Eric Olson",
        source_ref="notes/eric_olson.txt",
        claim_text="Eric Olson held the commander role at USSOCOM.",
    )
    second_assertion_id = _submit_accept_and_promote(
        review_service,
        predicate="oc:hold_command_role",
        person_entity_id="ent:person:admiral_eric_olson",
        person_name="Admiral Eric Olson",
        source_ref="notes/admiral_eric_olson.txt",
        claim_text="Admiral Eric Olson held the commander role at USSOCOM.",
    )

    identity_service = IdentityService(db_path=review_db_path)
    created = identity_service.create_identity_for_entity(
        entity_id="ent:person:eric_olson",
        created_by="analyst:identity",
        display_label="Eric Olson",
    )
    identity_service.attach_entity_alias(
        identity_id=created.identity.identity_id,
        entity_id="ent:person:admiral_eric_olson",
        attached_by="analyst:identity",
    )
    identity_service.attach_external_reference(
        identity_id=created.identity.identity_id,
        provider="analyst_registry",
        external_id="eric-olson-profile",
        attached_by="analyst:identity",
        reference_label="Eric Olson",
    )

    graph_service = CanonicalGraphService(db_path=review_db_path)
    artifact_service = ArtifactLineageService(db_path=review_db_path)
    artifact = artifact_service.register_artifact(
        artifact_kind="source",
        uri="notes/eric_olson.txt",
        label="Eric Olson note",
    )
    first_candidate_id = graph_service.get_promoted_assertion(
        assertion_id=first_assertion_id
    ).source_candidate_id
    artifact_service.link_candidate_artifact(
        candidate_id=first_candidate_id,
        artifact_id=artifact.artifact_id,
        support_kind="quoted_from",
        reference_detail="opening sentence",
    )
    return first_assertion_id, second_assertion_id


def _submit_accept_and_promote(
    review_service: ReviewService,
    *,
    predicate: str,
    person_entity_id: str,
    person_name: str,
    source_ref: str,
    claim_text: str,
) -> str:
    """Seed one accepted and promoted assertion with explicit entity names."""

    source_text = f"{person_name} served as commander of USSOCOM."
    submission = review_service.submit_candidate_assertion(
        payload={
            "predicate": predicate,
            "roles": {
                "commander": [
                    {
                        "entity_id": person_entity_id,
                        "entity_type": "oc:person",
                        "name": person_name,
                    }
                ],
                "organization": [
                    {
                        "entity_id": "ent:org:ussocom",
                        "entity_type": "oc:organization",
                        "name": "USSOCOM",
                    }
                ],
            },
        },
        profile_id="default",
        profile_version="1.0.0",
        submitted_by="analyst:query-seed",
        source_kind="text_file",
        source_ref=source_ref,
        source_text=source_text,
        claim_text=claim_text,
        evidence_spans=(
            {
                "start_char": 0,
                "end_char": len(person_name),
                "text": person_name,
            },
        ),
    )
    accepted = review_service.review_candidate(
        candidate_id=submission.candidate.candidate_id,
        decision="accepted",
        actor_id="analyst:reviewer",
    )
    promotion = CanonicalGraphService(db_path=review_service.store.db_path).promote_candidate(
        candidate_id=accepted.candidate_id,
        promoted_by="analyst:graph-promoter",
    )
    return promotion.assertion.assertion_id


def _read_stdout(capsys: pytest.CaptureFixture[str]) -> str:
    """Return captured stdout text from a pytest capsys fixture."""

    captured = capsys.readouterr()
    return captured.out

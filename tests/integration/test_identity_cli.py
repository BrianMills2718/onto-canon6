"""Integration tests for the Phase 12 stable-identity CLI surface."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from onto_canon6 import cli as cli_module
from onto_canon6.core import CanonicalGraphService
from onto_canon6.pipeline import ReviewService


def test_cli_identity_flow_creates_aliases_and_external_reference_state(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The CLI should drive the first stable-identity flow end to end."""

    review_db_path = tmp_path / "review.sqlite3"
    overlay_root = tmp_path / "ontology_overlays"
    review_service = ReviewService(
        db_path=review_db_path,
        overlay_root=overlay_root,
        default_acceptance_policy="record_only",
    )
    candidate_id_one = _submit_and_promote(
        review_service,
        predicate="oc:identity_cli_one",
        entity_id="ent:person:eric_olson",
        source_ref="notes/identity_cli_one.txt",
    )
    _submit_and_promote(
        review_service,
        predicate="oc:identity_cli_two",
        entity_id="ent:person:admiral_eric_olson",
        source_ref="notes/identity_cli_two.txt",
    )

    exit_code = cli_module.main(
        [
            "create-identity-for-entity",
            "--entity-id",
            "ent:person:eric_olson",
            "--actor-id",
            "analyst:identity",
            "--display-label",
            "Eric Olson",
            "--review-db-path",
            str(review_db_path),
            "--output",
            "json",
        ]
    )
    assert exit_code == 0
    identity_bundle = json.loads(_read_stdout(capsys))
    identity_id = str(identity_bundle["identity"]["identity_id"])
    assert identity_bundle["memberships"][0]["entity_id"] == "ent:person:eric_olson"

    exit_code = cli_module.main(
        [
            "attach-identity-alias",
            "--identity-id",
            identity_id,
            "--entity-id",
            "ent:person:admiral_eric_olson",
            "--actor-id",
            "analyst:identity",
            "--review-db-path",
            str(review_db_path),
            "--output",
            "json",
        ]
    )
    assert exit_code == 0
    alias_membership = json.loads(_read_stdout(capsys))
    assert alias_membership["membership_kind"] == "alias"

    exit_code = cli_module.main(
        [
            "attach-external-ref",
            "--identity-id",
            identity_id,
            "--provider",
            "wikidata",
            "--external-id",
            "Q5388397",
            "--reference-label",
            "Eric Olson",
            "--actor-id",
            "analyst:identity",
            "--review-db-path",
            str(review_db_path),
            "--output",
            "json",
        ]
    )
    assert exit_code == 0
    attached_reference = json.loads(_read_stdout(capsys))
    assert attached_reference["reference_status"] == "attached"

    exit_code = cli_module.main(
        [
            "record-unresolved-external-ref",
            "--identity-id",
            identity_id,
            "--provider",
            "wikidata",
            "--unresolved-note",
            "Possible second profile needs review",
            "--actor-id",
            "analyst:identity",
            "--review-db-path",
            str(review_db_path),
            "--output",
            "json",
        ]
    )
    assert exit_code == 0
    unresolved_reference = json.loads(_read_stdout(capsys))
    assert unresolved_reference["reference_status"] == "unresolved"

    exit_code = cli_module.main(
        [
            "list-identities",
            "--review-db-path",
            str(review_db_path),
            "--output",
            "json",
        ]
    )
    assert exit_code == 0
    listed_identities = json.loads(_read_stdout(capsys))
    assert len(listed_identities) == 1
    assert listed_identities[0]["identity"]["identity_id"] == identity_id

    exit_code = cli_module.main(
        [
            "export-identity-report",
            "--review-db-path",
            str(review_db_path),
            "--output",
            "json",
        ]
    )
    assert exit_code == 0
    report = json.loads(_read_stdout(capsys))
    assert report["summary"]["total_identities"] == 1
    assert report["summary"]["total_memberships"] == 2
    assert report["summary"]["total_external_references"] == 2
    assert report["summary"]["external_reference_status_counts"] == {
        "attached": 1,
        "unresolved": 1,
    }
    bundle = report["identity_bundles"][0]
    assert bundle["identity"]["identity_id"] == identity_id
    assert {membership["entity_id"] for membership in bundle["memberships"]} == {
        "ent:person:eric_olson",
        "ent:person:admiral_eric_olson",
    }
    assert bundle["promoted_entities"][0]["first_candidate_id"] == candidate_id_one


def _submit_and_promote(
    review_service: ReviewService,
    *,
    predicate: str,
    entity_id: str,
    source_ref: str,
) -> str:
    """Submit, accept, and promote one candidate through real services."""

    submission = review_service.submit_candidate_assertion(
        payload={
            "predicate": predicate,
            "roles": {
                "subject": [
                    {
                        "entity_id": entity_id,
                        "entity_type": "oc:person",
                    }
                ],
                "descriptor": [
                    {
                        "kind": "value",
                        "value_kind": "string",
                        "value": "identity cli demo",
                    }
                ],
            },
        },
        profile_id="default",
        profile_version="1.0.0",
        submitted_by="analyst:identity-cli-seed",
        source_kind="text_file",
        source_ref=source_ref,
        source_text="Identity CLI source text.",
    )
    accepted = review_service.review_candidate(
        candidate_id=submission.candidate.candidate_id,
        decision="accepted",
        actor_id="analyst:reviewer",
    )
    CanonicalGraphService(db_path=review_service.store.db_path).promote_candidate(
        candidate_id=accepted.candidate_id,
        promoted_by="analyst:graph-promoter",
    )
    return accepted.candidate_id


def _read_stdout(capsys: pytest.CaptureFixture[str]) -> str:
    """Return captured stdout text from a pytest capsys fixture."""

    captured = capsys.readouterr()
    return captured.out

"""Integration tests for the Phase 13 semantic canonicalization CLI surface."""

from __future__ import annotations

import json
from pathlib import Path
import sqlite3

import pytest

from onto_canon6 import cli as cli_module
from onto_canon6.core import CanonicalGraphService
from onto_canon6.pipeline import ReviewService


def _read_stdout(capsys: pytest.CaptureFixture[str]) -> str:
    """Return captured stdout text from a pytest capsys fixture."""

    captured = capsys.readouterr()
    return captured.out


def test_cli_recanonicalizes_promoted_assertion_and_reports_event(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The CLI should repair one legacy promoted assertion and expose the event trail."""

    review_db_path = tmp_path / "review.sqlite3"
    overlay_root = tmp_path / "ontology_overlays"
    review_service = ReviewService(
        db_path=review_db_path,
        overlay_root=overlay_root,
        default_acceptance_policy="record_only",
    )
    submission = review_service.submit_candidate_assertion(
        payload={
            "predicate": "dodaf:operational_node_exchanges_information",
            "roles": {
                "source_node": [
                    {
                        "entity_id": "ent:node:source",
                        "entity_type": "dm2:OperationalNode",
                    }
                ],
                "target_node": [
                    {
                        "entity_id": "ent:node:target",
                        "entity_type": "dm2:OperationalNode",
                    }
                ],
                "information_element": [
                    {
                        "entity_id": "ent:info:message",
                        "entity_type": "dm2:InformationElement",
                    }
                ],
            },
        },
        profile_id="dodaf_minimal_strict",
        profile_version="0.1.0",
        submitted_by="analyst:cli-semantic-seed",
        source_kind="text_file",
        source_ref="notes/dodaf_cli_semantic.txt",
        source_text="Node A exchanges Message M with Node B.",
    )
    candidate = review_service.review_candidate(
        candidate_id=submission.candidate.candidate_id,
        decision="accepted",
        actor_id="analyst:reviewer",
    )
    promoted = CanonicalGraphService(db_path=review_db_path).promote_candidate(
        candidate_id=candidate.candidate_id,
        promoted_by="analyst:graph-promoter",
    )
    with sqlite3.connect(review_db_path) as conn:
        conn.execute(
            """
            UPDATE promoted_graph_assertions
            SET predicate = ?,
                normalized_body_json = ?
            WHERE assertion_id = ?
            """,
            (
                "OperationalNodeExchangesInformation",
                json.dumps(
                    {
                        "predicate": "OperationalNodeExchangesInformation",
                        "roles": {
                            "source": [
                                {
                                    "kind": "entity",
                                    "entity_id": "ent:node:source",
                                    "entity_type": "dm2:OperationalNode",
                                }
                            ],
                            "target": [
                                {
                                    "kind": "entity",
                                    "entity_id": "ent:node:target",
                                    "entity_type": "dm2:OperationalNode",
                                }
                            ],
                            "information": [
                                {
                                    "kind": "entity",
                                    "entity_id": "ent:info:message",
                                    "entity_type": "dm2:InformationElement",
                                }
                            ],
                        },
                    },
                    sort_keys=True,
                ),
                promoted.assertion.assertion_id,
            ),
        )
        conn.execute(
            """
            UPDATE promoted_graph_role_fillers
            SET role_id = CASE role_id
                WHEN 'source_node' THEN 'source'
                WHEN 'target_node' THEN 'target'
                WHEN 'information_element' THEN 'information'
                ELSE role_id
            END
            WHERE assertion_id = ?
            """,
            (promoted.assertion.assertion_id,),
        )

    exit_code = cli_module.main(
        [
            "recanonicalize-promoted-assertion",
            "--assertion-id",
            promoted.assertion.assertion_id,
            "--actor-id",
            "analyst:semantic-repair",
            "--reason",
            "Normalize legacy DoDAF alias ids.",
            "--review-db-path",
            str(review_db_path),
            "--output",
            "json",
        ]
    )
    assert exit_code == 0
    recanonicalize_output = json.loads(_read_stdout(capsys))
    assert recanonicalize_output["status"] == "rewritten"
    assert (
        recanonicalize_output["assertion"]["predicate"]
        == "dodaf:operational_node_exchanges_information"
    )
    assert recanonicalize_output["event"]["before_predicate"] == (
        "OperationalNodeExchangesInformation"
    )

    exit_code = cli_module.main(
        [
            "list-recanonicalization-events",
            "--review-db-path",
            str(review_db_path),
            "--output",
            "json",
        ]
    )
    assert exit_code == 0
    events_output = json.loads(_read_stdout(capsys))
    assert len(events_output) == 1
    assert events_output[0]["assertion_id"] == promoted.assertion.assertion_id

    exit_code = cli_module.main(
        [
            "export-semantic-canonicalization-report",
            "--review-db-path",
            str(review_db_path),
            "--output",
            "json",
        ]
    )
    assert exit_code == 0
    report_output = json.loads(_read_stdout(capsys))
    assert report_output["summary"]["total_assertions"] == 1
    assert report_output["summary"]["total_recanonicalization_events"] == 1
    assert report_output["summary"]["total_rewritten_assertions"] == 1

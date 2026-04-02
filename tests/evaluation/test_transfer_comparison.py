"""Tests for extraction transfer comparison helpers."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from onto_canon6.evaluation.transfer_comparison import compare_transfer_surfaces


def test_compare_transfer_surfaces_reports_only_live_candidates(tmp_path: Path) -> None:
    """A live-only candidate should appear in the `only_live` bucket."""

    observability_db = _make_observability_db(
        tmp_path / "observability.db",
        run_id="run-1",
        item_id="item-1",
        predicted={"candidates": []},
    )
    live_candidates_path = _write_live_candidates(
        tmp_path / "live.json",
        [
            {
                "candidate": {
                    "claim_text": "Live claim",
                    "evidence_spans": [{"text": "Live evidence"}],
                    "normalized_payload": {
                        "predicate": "oc:express_concern",
                        "roles": {
                            "speaker": [{"kind": "entity", "name": "USSOCOM"}],
                            "topic": [{"kind": "value", "raw": "coordination gaps"}],
                        },
                    },
                }
            }
        ],
    )

    comparison = compare_transfer_surfaces(
        observability_db_path=observability_db,
        prompt_eval_run_id="run-1",
        prompt_eval_item_id="item-1",
        live_candidates_path=live_candidates_path,
    )

    assert comparison.prompt_eval_candidates == ()
    assert len(comparison.live_candidates) == 1
    assert len(comparison.only_live) == 1
    assert comparison.only_live[0].predicate == "oc:express_concern"


def test_compare_transfer_surfaces_reports_shared_and_prompt_only(tmp_path: Path) -> None:
    """Shared signatures and prompt-only signatures should both be visible."""

    observability_db = _make_observability_db(
        tmp_path / "observability.db",
        run_id="run-2",
        item_id="item-2",
        predicted={
            "candidates": [
                {
                    "predicate": "oc:limit_capability",
                    "roles": {
                        "subject": [{"kind": "entity", "name": "PSYOP"}],
                        "capability": [{"kind": "value", "raw": "effectiveness"}],
                    },
                    "evidence_spans": [{"text": "Prompt evidence"}],
                    "claim_text": None,
                },
                {
                    "predicate": "oc:hold_command_role",
                    "roles": {"holder": [{"kind": "entity", "name": "USSOCOM commanders"}]},
                    "evidence_spans": [{"text": "Prompt-only evidence"}],
                    "claim_text": None,
                },
            ]
        },
    )
    live_candidates_path = _write_live_candidates(
        tmp_path / "live.json",
        [
            {
                "candidate": {
                    "claim_text": None,
                    "evidence_spans": [{"text": "Prompt evidence"}],
                    "normalized_payload": {
                        "predicate": "oc:limit_capability",
                        "roles": {
                            "subject": [{"kind": "entity", "name": "PSYOP"}],
                            "capability": [{"kind": "value", "raw": "effectiveness"}],
                        },
                    },
                }
            }
        ],
    )

    comparison = compare_transfer_surfaces(
        observability_db_path=observability_db,
        prompt_eval_run_id="run-2",
        prompt_eval_item_id="item-2",
        live_candidates_path=live_candidates_path,
    )

    assert len(comparison.shared) == 1
    assert comparison.shared[0].predicate == "oc:limit_capability"
    assert len(comparison.only_prompt_eval) == 1
    assert comparison.only_prompt_eval[0].predicate == "oc:hold_command_role"


def test_compare_transfer_surfaces_exposes_body_level_matches(tmp_path: Path) -> None:
    """Body-level comparison should ignore claim-text-only wording drift."""

    observability_db = _make_observability_db(
        tmp_path / "observability.db",
        run_id="run-3",
        item_id="item-3",
        predicted={
            "candidates": [
                {
                    "predicate": "oc:hold_command_role",
                    "roles": {
                        "commander": [{"kind": "entity", "name": "Gen. Holland"}],
                        "organization": [{"kind": "entity", "name": "USSOCOM"}],
                    },
                    "evidence_spans": [{"text": "Gen. Holland"}],
                    "claim_text": "Gen. Holland held the role of commander for USSOCOM.",
                }
            ]
        },
    )
    live_candidates_path = _write_live_candidates(
        tmp_path / "live.json",
        [
            {
                "candidate": {
                    "claim_text": "Gen. Holland held the role of commander in USSOCOM.",
                    "evidence_spans": [{"text": "Gen. Holland"}],
                    "normalized_payload": {
                        "predicate": "oc:hold_command_role",
                        "roles": {
                            "commander": [{"kind": "entity", "name": "Gen. Holland"}],
                            "organization": [{"kind": "entity", "name": "USSOCOM"}],
                        },
                    },
                }
            }
        ],
    )

    comparison = compare_transfer_surfaces(
        observability_db_path=observability_db,
        prompt_eval_run_id="run-3",
        prompt_eval_item_id="item-3",
        live_candidates_path=live_candidates_path,
    )

    assert len(comparison.shared) == 0
    assert len(comparison.only_live) == 1
    assert len(comparison.only_prompt_eval) == 1
    assert len(comparison.body_shared) == 1
    assert len(comparison.body_only_live) == 0
    assert len(comparison.body_only_prompt_eval) == 0


def _make_observability_db(
    path: Path, *, run_id: str, item_id: str, predicted: dict[str, object]
) -> Path:
    """Create the minimum experiment_items table needed for comparison tests."""

    connection = sqlite3.connect(path)
    try:
        connection.execute(
            """
            CREATE TABLE experiment_items (
                id INTEGER PRIMARY KEY,
                run_id TEXT NOT NULL,
                item_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                metrics TEXT NOT NULL,
                predicted TEXT,
                gold TEXT,
                latency_s REAL,
                cost REAL,
                n_tool_calls INTEGER,
                error TEXT,
                extra TEXT,
                trace_id TEXT
            )
            """
        )
        connection.execute(
            """
            INSERT INTO experiment_items (
                run_id, item_id, timestamp, metrics, predicted, gold, latency_s, cost,
                n_tool_calls, error, extra, trace_id
            ) VALUES (?, ?, '2026-04-01T00:00:00Z', '{}', ?, NULL, NULL, NULL, NULL, NULL, NULL, 'trace-1')
            """,
            (run_id, item_id, json.dumps(predicted)),
        )
        connection.commit()
    finally:
        connection.close()
    return path


def _write_live_candidates(path: Path, payload: list[dict[str, object]]) -> Path:
    """Write a live reviewed-candidate snapshot payload."""

    path.write_text(json.dumps(payload))
    return path

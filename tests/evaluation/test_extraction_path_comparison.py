"""Tests for extraction-path call-surface comparison helpers."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from onto_canon6.evaluation.extraction_path_comparison import compare_extraction_call_surfaces


def test_compare_extraction_call_surfaces_exposes_temperature_and_timeout_drift(
    tmp_path: Path,
) -> None:
    """Prompt-eval-only temperature kwargs should appear in the structured diff."""

    db_path = _make_llm_calls_db(tmp_path / "observability.db")
    _insert_snapshot(
        db_path,
        timestamp="2026-04-01T00:00:00Z",
        project="live-project",
        task="budget_extraction",
        model="gemini/gemini-2.5-flash",
        trace_id="live-trace",
        prompt_ref="onto_canon6.extraction.live@1",
        call_snapshot=_snapshot(
            public_api="call_llm_structured",
            prompt_ref="onto_canon6.extraction.live@1",
            control={"timeout": 60, "num_retries": 2},
            kwargs={},
            user_message="Case input:\nSource text:\nHello world",
        ),
    )
    _insert_snapshot(
        db_path,
        timestamp="2026-04-01T00:01:00Z",
        project="onto-canon6",
        task="budget_extraction",
        model="gemini/gemini-2.5-flash",
        trace_id="prompt_eval/trace/chunk003",
        prompt_ref="onto_canon6.extraction.parity@3",
        call_snapshot=_snapshot(
            public_api="acall_llm_structured",
            prompt_ref="onto_canon6.extraction.parity@3",
            control={"timeout": 0, "num_retries": 2},
            kwargs={"temperature": 0.0},
            user_message="Case input:\nCase id: chunk003\nSource text:\nHello world",
        ),
    )

    comparison = compare_extraction_call_surfaces(
        observability_db_path=db_path,
        live_project="live-project",
        live_task="budget_extraction",
        prompt_eval_prompt_ref="onto_canon6.extraction.parity@3",
        prompt_eval_trace_id="prompt_eval/trace/chunk003",
    )

    assert comparison.public_api_equal is False
    assert comparison.requested_model_equal is True
    assert comparison.response_model_equal is True
    assert comparison.control_diff["timeout"] == {"live": 60, "prompt_eval": 0}
    assert comparison.kwargs_diff["temperature"] == {"live": None, "prompt_eval": 0.0}
    assert comparison.user_equal is False
    assert any("Case id: chunk003" in line for line in comparison.user_diff)


def _make_llm_calls_db(path: Path) -> Path:
    """Create the minimum llm_calls table needed by the comparison helper."""

    connection = sqlite3.connect(path)
    try:
        connection.execute(
            """
            CREATE TABLE llm_calls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                project TEXT,
                model TEXT NOT NULL,
                messages TEXT,
                response TEXT,
                prompt_tokens INTEGER,
                completion_tokens INTEGER,
                total_tokens INTEGER,
                cost REAL,
                finish_reason TEXT,
                latency_s REAL,
                error TEXT,
                caller TEXT,
                task TEXT,
                trace_id TEXT,
                cost_source TEXT,
                billing_mode TEXT,
                marginal_cost REAL,
                cache_hit INTEGER DEFAULT 0,
                prompt_ref TEXT,
                call_fingerprint TEXT,
                call_snapshot TEXT,
                error_type TEXT,
                execution_path TEXT,
                retry_count INTEGER,
                schema_hash TEXT,
                response_format_type TEXT,
                validation_errors TEXT
            )
            """
        )
        connection.commit()
    finally:
        connection.close()
    return path


def _insert_snapshot(
    path: Path,
    *,
    timestamp: str,
    project: str,
    task: str,
    model: str,
    trace_id: str,
    prompt_ref: str,
    call_snapshot: dict[str, object],
) -> None:
    """Insert one synthetic llm_calls row."""

    connection = sqlite3.connect(path)
    try:
        connection.execute(
            """
            INSERT INTO llm_calls (
                timestamp, project, model, task, trace_id, prompt_ref, call_snapshot
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                timestamp,
                project,
                model,
                task,
                trace_id,
                prompt_ref,
                json.dumps(call_snapshot),
            ),
        )
        connection.commit()
    finally:
        connection.close()


def _snapshot(
    *,
    public_api: str,
    prompt_ref: str,
    control: dict[str, object],
    kwargs: dict[str, object],
    user_message: str,
) -> dict[str, object]:
    """Build one minimal call_snapshot payload."""

    return {
        "snapshot_version": 1,
        "public_api": public_api,
        "call_kind": "structured",
        "request": {
            "requested_model": "gemini/gemini-2.5-flash",
            "messages": [
                {"role": "system", "content": "system prompt"},
                {"role": "user", "content": user_message},
            ],
            "control": control,
            "kwargs": kwargs,
            "prompt_ref": prompt_ref,
            "response_model_fqn": "onto_canon6.pipeline.text_extraction.TextExtractionResponse",
        },
    }

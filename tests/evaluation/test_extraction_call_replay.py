"""Tests for structured extraction call replay helpers."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from onto_canon6.evaluation.extraction_call_replay import replay_structured_call_surface


class _FakeResponse:
    """Small response-model stand-in with a Pydantic-like dump surface."""

    def __init__(self, payload: dict[str, object]) -> None:
        self.payload = payload

    def model_dump(self, *, mode: str) -> dict[str, object]:
        del mode
        return self.payload


def test_replay_structured_call_surface_uses_requested_public_api(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    """Replay should dispatch through the chosen sync or async structured facade."""

    db_path = _make_llm_calls_db(tmp_path / "observability.db")
    _insert_snapshot(
        db_path,
        call_id=11,
        prompt_ref="onto_canon6.extraction.live@1",
        public_api="call_llm_structured",
    )
    calls: dict[str, dict[str, Any]] = {}

    def fake_call(
        model: str,
        messages: list[dict[str, str]],
        *,
        response_model: type[object],
        **kwargs: object,
    ) -> tuple[_FakeResponse, object]:
        calls["sync"] = {
            "model": model,
            "messages": messages,
            "response_model": response_model,
            "kwargs": kwargs,
        }
        return _FakeResponse({"candidates": []}), SimpleNamespace(resolved_model="sync-model")

    async def fake_acall(
        model: str,
        messages: list[dict[str, str]],
        *,
        response_model: type[object],
        **kwargs: object,
    ) -> tuple[_FakeResponse, object]:
        calls["async"] = {
            "model": model,
            "messages": messages,
            "response_model": response_model,
            "kwargs": kwargs,
        }
        return _FakeResponse({"candidates": ["async"]}), SimpleNamespace(resolved_model="async-model")

    import llm_client

    monkeypatch.setattr(llm_client, "call_llm_structured", fake_call)
    monkeypatch.setattr(llm_client, "acall_llm_structured", fake_acall)

    sync_result = replay_structured_call_surface(
        observability_db_path=db_path,
        call_id=11,
        public_api="call_llm_structured",
        trace_id="replay/sync",
        task="budget_extraction",
        max_budget=0.25,
        project="replay-project",
    )
    async_result = replay_structured_call_surface(
        observability_db_path=db_path,
        call_id=11,
        public_api="acall_llm_structured",
        trace_id="replay/async",
        task="budget_extraction",
        max_budget=0.25,
        project="replay-project",
    )

    assert sync_result["replayed_public_api"] == "call_llm_structured"
    assert sync_result["resolved_model"] == "sync-model"
    assert sync_result["parsed"] == {"candidates": []}
    assert calls["sync"]["kwargs"]["temperature"] == 0.0

    assert async_result["replayed_public_api"] == "acall_llm_structured"
    assert async_result["resolved_model"] == "async-model"
    assert async_result["parsed"] == {"candidates": ["async"]}
    assert calls["async"]["kwargs"]["temperature"] == 0.0


def test_replay_structured_call_surface_can_remove_metadata_lines(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    """Replay should support bounded line-level prompt mutations for residual diagnosis."""

    db_path = _make_llm_calls_db(tmp_path / "observability.db")
    _insert_snapshot(
        db_path,
        call_id=12,
        prompt_ref="onto_canon6.extraction.live@1",
        public_api="acall_llm_structured",
    )
    seen_messages: dict[str, Any] = {}

    async def fake_acall(
        model: str,
        messages: list[dict[str, str]],
        *,
        response_model: type[object],
        **kwargs: object,
    ) -> tuple[_FakeResponse, object]:
        del model, response_model, kwargs
        seen_messages["messages"] = messages
        return _FakeResponse({"candidates": []}), SimpleNamespace(resolved_model="async-model")

    import llm_client

    monkeypatch.setattr(llm_client, "acall_llm_structured", fake_acall)

    replay_structured_call_surface(
        observability_db_path=db_path,
        call_id=12,
        public_api="acall_llm_structured",
        trace_id="replay/async",
        task="budget_extraction",
        max_budget=0.25,
        project="replay-project",
        remove_line_prefixes=("Case id:",),
        strip_blank_line_before_prefixes=("Source text:",),
    )

    messages = seen_messages["messages"]
    assert isinstance(messages, list)
    assert len(messages) == 2
    user_message = messages[1]
    assert isinstance(user_message, dict)
    user_content = user_message["content"]
    assert isinstance(user_content, str)
    assert "Case id:" not in user_content
    assert "\n\nSource text:" not in user_content


def test_replay_structured_call_surface_can_replace_matching_lines(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    """Replay should support bounded line replacement for residual diagnosis."""

    db_path = _make_llm_calls_db(tmp_path / "observability.db")
    _insert_snapshot(
        db_path,
        call_id=13,
        prompt_ref="onto_canon6.extraction.live@1",
        public_api="acall_llm_structured",
    )
    seen_messages: dict[str, Any] = {}

    async def fake_acall(
        model: str,
        messages: list[dict[str, str]],
        *,
        response_model: type[object],
        **kwargs: object,
    ) -> tuple[_FakeResponse, object]:
        del model, response_model, kwargs
        seen_messages["messages"] = messages
        return _FakeResponse({"candidates": []}), SimpleNamespace(resolved_model="async-model")

    import llm_client

    monkeypatch.setattr(llm_client, "acall_llm_structured", fake_acall)

    replay_structured_call_surface(
        observability_db_path=db_path,
        call_id=13,
        public_api="acall_llm_structured",
        trace_id="replay/async",
        task="budget_extraction",
        max_budget=0.25,
        project="replay-project",
        replace_line_prefixes=(
            ("Case input:", "Source text only:"),
            ("Source text:", "Body:"),
        ),
    )

    messages = seen_messages["messages"]
    assert isinstance(messages, list)
    user_message = messages[1]
    assert isinstance(user_message, dict)
    user_content = user_message["content"]
    assert isinstance(user_content, str)
    assert "Source text only:" in user_content
    assert "Body:" in user_content
    assert "Case input:" not in user_content
    assert "Source text:" not in user_content


def _make_llm_calls_db(path: Path) -> Path:
    """Create the minimum llm_calls table needed by the replay helper."""

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
    call_id: int,
    prompt_ref: str,
    public_api: str,
) -> None:
    """Insert one synthetic structured-call snapshot row."""

    payload = {
        "snapshot_version": 1,
        "public_api": public_api,
        "call_kind": "structured",
        "request": {
            "requested_model": "gemini/gemini-2.5-flash",
            "messages": [
                {"role": "system", "content": "system prompt"},
                {
                    "role": "user",
                    "content": "\n".join(
                        [
                            "Case input:",
                            "Case id: demo_case",
                            "",
                            "Source text:",
                            "user prompt",
                        ]
                    ),
                },
            ],
            "control": {"timeout": 60, "num_retries": 2},
            "kwargs": {"temperature": 0.0},
            "prompt_ref": prompt_ref,
            "response_model_fqn": "tests.evaluation.test_extraction_call_replay._FakeResponse",
        },
    }
    connection = sqlite3.connect(path)
    try:
        connection.execute(
            """
            INSERT INTO llm_calls (
                id, timestamp, project, model, task, trace_id, prompt_ref, call_snapshot
            ) VALUES (?, '2026-04-02T00:00:00Z', 'source-project', 'gemini/gemini-2.5-flash', 'budget_extraction', 'source-trace', ?, ?)
            """,
            (call_id, prompt_ref, json.dumps(payload)),
        )
        connection.commit()
    finally:
        connection.close()

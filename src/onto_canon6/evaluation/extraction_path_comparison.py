"""Compare prompt-eval and live extraction call surfaces from observability.

This module exists for Plan 0045. Wrapper alignment is already ruled out as
the main rescue lever for chunk `003`, so the next bounded question is about
the extraction call path itself: what non-message request surfaces still differ
between the live extractor and the prompt-eval path under the same prompt/model
pair?
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from difflib import unified_diff
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ExtractionCallSurface:
    """Stable view of one structured extraction call from observability."""

    timestamp: str
    project: str | None
    task: str | None
    model: str
    trace_id: str | None
    prompt_ref: str | None
    public_api: str
    requested_model: str
    response_model_fqn: str | None
    control: dict[str, Any]
    kwargs: dict[str, Any]
    system_message: str
    user_message: str

    @property
    def system_hash(self) -> int:
        """Return a stable Python hash for quick equality diagnostics."""

        return hash(self.system_message)

    @property
    def user_hash(self) -> int:
        """Return a stable Python hash for quick equality diagnostics."""

        return hash(self.user_message)

    def to_jsonable(self) -> dict[str, Any]:
        """Render this call surface in a deterministic JSON-safe shape."""

        return {
            "timestamp": self.timestamp,
            "project": self.project,
            "task": self.task,
            "model": self.model,
            "trace_id": self.trace_id,
            "prompt_ref": self.prompt_ref,
            "public_api": self.public_api,
            "requested_model": self.requested_model,
            "response_model_fqn": self.response_model_fqn,
            "control": self.control,
            "kwargs": self.kwargs,
            "system_length": len(self.system_message),
            "user_length": len(self.user_message),
        }


@dataclass(frozen=True)
class ExtractionPathComparison:
    """Structured comparison between one live and one prompt-eval call."""

    live: ExtractionCallSurface
    prompt_eval: ExtractionCallSurface
    public_api_equal: bool
    prompt_ref_equal: bool
    requested_model_equal: bool
    response_model_equal: bool
    system_equal: bool
    user_equal: bool
    control_diff: dict[str, dict[str, Any]]
    kwargs_diff: dict[str, dict[str, Any]]
    system_diff: tuple[str, ...]
    user_diff: tuple[str, ...]

    def to_jsonable(self) -> dict[str, Any]:
        """Render the comparison in a deterministic JSON-safe shape."""

        return {
            "live": self.live.to_jsonable(),
            "prompt_eval": self.prompt_eval.to_jsonable(),
            "public_api_equal": self.public_api_equal,
            "prompt_ref_equal": self.prompt_ref_equal,
            "requested_model_equal": self.requested_model_equal,
            "response_model_equal": self.response_model_equal,
            "system_equal": self.system_equal,
            "user_equal": self.user_equal,
            "control_diff": self.control_diff,
            "kwargs_diff": self.kwargs_diff,
            "system_diff": list(self.system_diff),
            "user_diff": list(self.user_diff),
        }


def compare_extraction_call_surfaces(
    *,
    observability_db_path: Path,
    live_project: str,
    live_task: str,
    prompt_eval_prompt_ref: str,
    prompt_eval_trace_id: str,
) -> ExtractionPathComparison:
    """Compare one live extraction call against one prompt-eval extraction call."""

    connection = sqlite3.connect(observability_db_path)
    connection.row_factory = sqlite3.Row
    try:
        live = _load_latest_call_surface(
            connection,
            where_clause="project = ? AND task = ?",
            params=(live_project, live_task),
        )
        prompt_eval = _load_latest_call_surface(
            connection,
            where_clause="prompt_ref = ? AND trace_id = ?",
            params=(prompt_eval_prompt_ref, prompt_eval_trace_id),
        )
    finally:
        connection.close()
    return _build_comparison(live=live, prompt_eval=prompt_eval)


def _load_latest_call_surface(
    connection: sqlite3.Connection,
    *,
    where_clause: str,
    params: tuple[str, ...],
) -> ExtractionCallSurface:
    """Load one latest llm_calls row and normalize its call snapshot."""

    row = connection.execute(
        f"""
        SELECT timestamp, project, task, model, trace_id, prompt_ref, call_snapshot
        FROM llm_calls
        WHERE {where_clause}
        ORDER BY timestamp DESC
        LIMIT 1
        """,
        params,
    ).fetchone()
    if row is None:
        raise ValueError(f"No llm_calls row found for selector: {where_clause} {params!r}")
    snapshot = json.loads(_require_string(row["call_snapshot"], "call_snapshot"))
    request = snapshot.get("request")
    if not isinstance(request, dict):
        raise ValueError("call_snapshot.request must be an object")
    messages = request.get("messages")
    if not isinstance(messages, list) or len(messages) < 2:
        raise ValueError("call_snapshot.request.messages must contain at least two messages")
    return ExtractionCallSurface(
        timestamp=_optional_string(row["timestamp"]) or "",
        project=_optional_string(row["project"]),
        task=_optional_string(row["task"]),
        model=_require_string(row["model"], "model"),
        trace_id=_optional_string(row["trace_id"]),
        prompt_ref=_optional_string(row["prompt_ref"]),
        public_api=_require_string(snapshot.get("public_api"), "public_api"),
        requested_model=_require_string(request.get("requested_model"), "requested_model"),
        response_model_fqn=_optional_string(request.get("response_model_fqn")),
        control=_normalize_object(request.get("control")),
        kwargs=_normalize_object(request.get("kwargs")),
        system_message=_message_content(messages, 0),
        user_message=_message_content(messages, 1),
    )


def _build_comparison(
    *, live: ExtractionCallSurface, prompt_eval: ExtractionCallSurface
) -> ExtractionPathComparison:
    """Build a deterministic extraction-path comparison."""

    return ExtractionPathComparison(
        live=live,
        prompt_eval=prompt_eval,
        public_api_equal=live.public_api == prompt_eval.public_api,
        prompt_ref_equal=live.prompt_ref == prompt_eval.prompt_ref,
        requested_model_equal=live.requested_model == prompt_eval.requested_model,
        response_model_equal=live.response_model_fqn == prompt_eval.response_model_fqn,
        system_equal=live.system_message == prompt_eval.system_message,
        user_equal=live.user_message == prompt_eval.user_message,
        control_diff=_diff_objects(live.control, prompt_eval.control),
        kwargs_diff=_diff_objects(live.kwargs, prompt_eval.kwargs),
        system_diff=_diff_strings(
            label_a="live_system",
            value_a=live.system_message,
            label_b="prompt_eval_system",
            value_b=prompt_eval.system_message,
        ),
        user_diff=_diff_strings(
            label_a="live_user",
            value_a=live.user_message,
            label_b="prompt_eval_user",
            value_b=prompt_eval.user_message,
        ),
    )


def _normalize_object(value: Any) -> dict[str, Any]:
    """Normalize one optional JSON object from the snapshot."""

    if isinstance(value, dict):
        return value
    return {}


def _message_content(messages: list[dict[str, Any]], index: int) -> str:
    """Return one message content or fail loudly on shape drift."""

    message = messages[index]
    if not isinstance(message, dict):
        raise ValueError(f"message {index} must be an object")
    content = message.get("content")
    if not isinstance(content, str):
        raise ValueError(f"message {index} is missing string content")
    return content


def _diff_objects(left: dict[str, Any], right: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Return a stable key-wise diff between two JSON-like objects."""

    keys = sorted(set(left) | set(right))
    diff: dict[str, dict[str, Any]] = {}
    for key in keys:
        left_value = left.get(key)
        right_value = right.get(key)
        if left_value != right_value:
            diff[key] = {
                "live": left_value,
                "prompt_eval": right_value,
            }
    return diff


def _diff_strings(*, label_a: str, value_a: str, label_b: str, value_b: str) -> tuple[str, ...]:
    """Return a unified diff over two multiline strings."""

    return tuple(
        unified_diff(
            value_a.splitlines(),
            value_b.splitlines(),
            fromfile=label_a,
            tofile=label_b,
            lineterm="",
        )
    )


def _require_string(value: Any, label: str) -> str:
    """Return one required non-empty string or raise loudly."""

    if not isinstance(value, str) or not value:
        raise ValueError(f"{label} must be a non-empty string")
    return value


def _optional_string(value: Any) -> str | None:
    """Return one optional string or None."""

    return value if isinstance(value, str) and value else None


__all__ = [
    "ExtractionCallSurface",
    "ExtractionPathComparison",
    "compare_extraction_call_surfaces",
]

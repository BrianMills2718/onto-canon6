"""Replay one captured structured extraction call through a chosen public API.

This module exists for Plan 0046. The remaining residual after Plan 0045 is
small enough that the repo needs a direct replay surface:

1. load one captured structured call from observability;
2. preserve its rendered messages, structured schema, and public kwargs; and
3. rerun it through either the sync or async structured-call facade.
"""

from __future__ import annotations

import asyncio
import importlib
import json
import sqlite3
from pathlib import Path
from typing import Any, Literal

StructuredPublicAPI = Literal["call_llm_structured", "acall_llm_structured"]


def replay_structured_call_surface(
    *,
    observability_db_path: Path,
    call_id: int,
    public_api: StructuredPublicAPI,
    trace_id: str,
    task: str,
    max_budget: float,
    project: str | None = None,
) -> dict[str, Any]:
    """Replay one captured structured call through the chosen public API."""

    record = _load_call_record(observability_db_path=observability_db_path, call_id=call_id)
    snapshot = record["snapshot"]
    request = record["request"]
    requested_model = _require_string(request.get("requested_model"), "requested_model")
    response_model = _resolve_response_model(
        _require_string(request.get("response_model_fqn"), "response_model_fqn")
    )
    messages = request.get("messages")
    if not isinstance(messages, list):
        raise ValueError("request.messages must be a list")
    control = _normalize_object(request.get("control"))
    public_kwargs = _normalize_object(request.get("kwargs"))
    call_kwargs: dict[str, Any] = {
        "timeout": control.get("timeout", 60),
        "num_retries": control.get("num_retries", 0),
        "reasoning_effort": control.get("reasoning_effort"),
        "api_base": control.get("api_base"),
        "base_delay": control.get("base_delay", 1.0),
        "max_delay": control.get("max_delay", 30.0),
        "retry_on": control.get("retry_on"),
        "fallback_models": control.get("fallback_models"),
        "task": task,
        "trace_id": trace_id,
        "max_budget": max_budget,
        "prompt_ref": request.get("prompt_ref"),
        **public_kwargs,
    }

    llm_client = importlib.import_module("llm_client")
    selected_project = project if project is not None else record["project"]
    previous_project = None
    if selected_project is not None:
        import os

        previous_project = os.environ.get("LLM_CLIENT_PROJECT")
        os.environ["LLM_CLIENT_PROJECT"] = selected_project
    try:
        if public_api == "call_llm_structured":
            parsed, meta = getattr(llm_client, "call_llm_structured")(
                requested_model,
                messages,
                response_model=response_model,
                **call_kwargs,
            )
        else:
            parsed, meta = asyncio.run(
                getattr(llm_client, "acall_llm_structured")(
                    requested_model,
                    messages,
                    response_model=response_model,
                    **call_kwargs,
                )
            )
    finally:
        if selected_project is not None:
            import os

            if previous_project is None:
                os.environ.pop("LLM_CLIENT_PROJECT", None)
            else:
                os.environ["LLM_CLIENT_PROJECT"] = previous_project

    parsed_json = parsed.model_dump(mode="json") if hasattr(parsed, "model_dump") else parsed
    return {
        "source_call_id": call_id,
        "source_public_api": snapshot.get("public_api"),
        "replayed_public_api": public_api,
        "project": selected_project,
        "task": task,
        "trace_id": trace_id,
        "requested_model": requested_model,
        "prompt_ref": request.get("prompt_ref"),
        "response_model_fqn": request.get("response_model_fqn"),
        "call_kwargs": call_kwargs,
        "parsed": parsed_json,
        "resolved_model": getattr(meta, "resolved_model", requested_model),
    }


def _load_call_record(*, observability_db_path: Path, call_id: int) -> dict[str, Any]:
    """Load one llm_calls row and decode its snapshot."""

    connection = sqlite3.connect(observability_db_path)
    connection.row_factory = sqlite3.Row
    try:
        row = connection.execute(
            """
            SELECT id, project, task, trace_id, call_snapshot
            FROM llm_calls
            WHERE id = ?
            """,
            (call_id,),
        ).fetchone()
    finally:
        connection.close()
    if row is None:
        raise ValueError(f"No llm_calls row found for call_id={call_id}")
    snapshot = json.loads(_require_string(row["call_snapshot"], "call_snapshot"))
    request = snapshot.get("request")
    if not isinstance(request, dict):
        raise ValueError("call_snapshot.request must be an object")
    return {
        "project": row["project"],
        "task": row["task"],
        "trace_id": row["trace_id"],
        "snapshot": snapshot,
        "request": request,
    }


def _resolve_response_model(model_fqn: str) -> type[Any]:
    """Resolve one dotted response-model path from the call snapshot."""

    module_name, _, attr_name = model_fqn.rpartition(".")
    if not module_name or not attr_name:
        raise ValueError(f"Invalid response model path: {model_fqn!r}")
    module = importlib.import_module(module_name)
    model = getattr(module, attr_name, None)
    if not isinstance(model, type):
        raise ValueError(f"Response model path did not resolve to a type: {model_fqn!r}")
    return model


def _normalize_object(value: Any) -> dict[str, Any]:
    """Normalize one optional JSON object from the snapshot."""

    if isinstance(value, dict):
        return value
    return {}


def _require_string(value: Any, label: str) -> str:
    """Return one required non-empty string or raise loudly."""

    if not isinstance(value, str) or not value:
        raise ValueError(f"{label} must be a non-empty string")
    return value


__all__ = [
    "StructuredPublicAPI",
    "replay_structured_call_surface",
]

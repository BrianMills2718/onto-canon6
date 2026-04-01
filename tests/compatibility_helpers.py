"""Helpers for Lane 3 compatibility-fixture assertions.

These helpers keep snapshot/fixture normalization logic in one place so the
owner tests for the promoted graph, governed bundle, Foundation IR export, and
DIGIMON v1 seam do not each reinvent their own placeholder policy.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

FIXTURES_ROOT = Path(__file__).resolve().parent / "fixtures" / "compatibility"

_ID_PLACEHOLDERS = {
    "application_id": "<OVERLAY_APPLICATION_ID>",
    "artifact_id": "<ARTIFACT_ID>",
    "assertion_id": "<ASSERTION_ID>",
    "assessment_id": "<CONFIDENCE_ASSESSMENT_ID>",
    "candidate_id": "<CANDIDATE_ID>",
    "decision_id": "<DECISION_ID>",
    "first_candidate_id": "<CANDIDATE_ID>",
    "proposal_id": "<PROPOSAL_ID>",
    "review_id": "<REVIEW_ID>",
    "source_candidate_id": "<CANDIDATE_ID>",
}
_LIST_ID_PLACEHOLDERS = {
    "candidate_ids": "<CANDIDATE_ID>",
    "proposal_ids": "<PROPOSAL_ID>",
}
_TIMESTAMP_KEYS = {
    "applied_at",
    "created_at",
    "generated_at",
    "promoted_at",
    "submitted_at",
}
_PATH_KEYS = {"content_path"}


def compatibility_fixture_path(*parts: str) -> Path:
    """Return a path under the Lane 3 compatibility-fixture root."""

    return FIXTURES_ROOT.joinpath(*parts)


def load_json_fixture(*parts: str) -> Any:
    """Load one JSON compatibility fixture."""

    path = compatibility_fixture_path(*parts)
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl_fixture(*parts: str) -> list[dict[str, Any]]:
    """Load one JSONL compatibility fixture as a list of dict rows."""

    path = compatibility_fixture_path(*parts)
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            raw = line.strip()
            if not raw:
                continue
            rows.append(json.loads(raw))
    return rows


def normalize_snapshot(value: Any, *, key: str | None = None) -> Any:
    """Normalize volatile ids, timestamps, and temp paths in snapshot data."""

    if isinstance(value, dict):
        return {
            item_key: normalize_snapshot(item_value, key=item_key)
            for item_key, item_value in value.items()
        }

    if isinstance(value, list):
        if key in _LIST_ID_PLACEHOLDERS:
            return [_LIST_ID_PLACEHOLDERS[key] for _ in value]
        return [normalize_snapshot(item) for item in value]

    if isinstance(value, tuple):
        return [normalize_snapshot(item) for item in value]

    if isinstance(value, str):
        if key in _ID_PLACEHOLDERS:
            return _ID_PLACEHOLDERS[key]
        if key in _TIMESTAMP_KEYS:
            return "<TIMESTAMP>"
        if key in _PATH_KEYS:
            return f"<PATH:{Path(value).name}>"
    return value


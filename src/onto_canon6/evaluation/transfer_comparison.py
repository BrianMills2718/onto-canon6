"""Compare live extraction transfer artifacts against prompt-eval payloads.

This module exists to make extraction-transfer certification reproducible.
Plan 0040 needs a narrow, typed way to compare:

1. a live reviewed-candidate snapshot from the `extract-text` path; and
2. a prompt-eval `experiment_items.predicted` payload from the observability DB.

The output is a normalized diff over candidate signatures rather than a second
extraction runtime.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class NormalizedCandidate:
    """Stable comparison shape for one extracted candidate."""

    predicate: str
    roles: tuple[str, ...]
    evidence: tuple[str, ...]
    claim_text: str | None

    @property
    def signature(self) -> tuple[str, tuple[str, ...], tuple[str, ...], str | None]:
        """Return a hashable signature for deterministic comparison."""

        return (self.predicate, self.roles, self.evidence, self.claim_text)


@dataclass(frozen=True)
class TransferComparison:
    """Structured comparison between prompt-eval and live extraction outputs."""

    prompt_eval_run_id: str
    prompt_eval_item_id: str
    prompt_eval_candidates: tuple[NormalizedCandidate, ...]
    live_candidates: tuple[NormalizedCandidate, ...]

    @property
    def only_prompt_eval(self) -> tuple[NormalizedCandidate, ...]:
        """Candidates present only in the prompt-eval payload."""

        live = {candidate.signature for candidate in self.live_candidates}
        return tuple(
            candidate
            for candidate in self.prompt_eval_candidates
            if candidate.signature not in live
        )

    @property
    def only_live(self) -> tuple[NormalizedCandidate, ...]:
        """Candidates present only in the live extraction payload."""

        prompt_eval = {candidate.signature for candidate in self.prompt_eval_candidates}
        return tuple(
            candidate for candidate in self.live_candidates if candidate.signature not in prompt_eval
        )

    @property
    def shared(self) -> tuple[NormalizedCandidate, ...]:
        """Candidates present in both payloads."""

        prompt_eval = {candidate.signature for candidate in self.prompt_eval_candidates}
        return tuple(
            candidate for candidate in self.live_candidates if candidate.signature in prompt_eval
        )

    def to_jsonable(self) -> dict[str, Any]:
        """Render the comparison as deterministic JSON-friendly data."""

        return {
            "prompt_eval_run_id": self.prompt_eval_run_id,
            "prompt_eval_item_id": self.prompt_eval_item_id,
            "prompt_eval_candidates": [_candidate_to_jsonable(c) for c in self.prompt_eval_candidates],
            "live_candidates": [_candidate_to_jsonable(c) for c in self.live_candidates],
            "only_prompt_eval": [_candidate_to_jsonable(c) for c in self.only_prompt_eval],
            "only_live": [_candidate_to_jsonable(c) for c in self.only_live],
            "shared": [_candidate_to_jsonable(c) for c in self.shared],
        }


def compare_transfer_surfaces(
    *,
    observability_db_path: Path,
    prompt_eval_run_id: str,
    prompt_eval_item_id: str,
    live_candidates_path: Path,
) -> TransferComparison:
    """Compare one prompt-eval item against one live reviewed-candidate snapshot."""

    prompt_eval_candidates = load_prompt_eval_candidates(
        observability_db_path=observability_db_path,
        run_id=prompt_eval_run_id,
        item_id=prompt_eval_item_id,
    )
    live_candidates = load_live_candidates(live_candidates_path)
    return TransferComparison(
        prompt_eval_run_id=prompt_eval_run_id,
        prompt_eval_item_id=prompt_eval_item_id,
        prompt_eval_candidates=prompt_eval_candidates,
        live_candidates=live_candidates,
    )


def load_prompt_eval_candidates(
    *, observability_db_path: Path, run_id: str, item_id: str
) -> tuple[NormalizedCandidate, ...]:
    """Load and normalize prompt-eval predicted candidates from observability."""

    connection = sqlite3.connect(observability_db_path)
    try:
        row = connection.execute(
            "SELECT predicted FROM experiment_items WHERE run_id = ? AND item_id = ?",
            (run_id, item_id),
        ).fetchone()
    finally:
        connection.close()
    if row is None:
        raise ValueError(f"No experiment_items row found for run_id={run_id!r} item_id={item_id!r}")
    predicted = json.loads(row[0] or "{}")
    candidates = predicted.get("candidates", [])
    if not isinstance(candidates, list):
        raise ValueError("Prompt-eval predicted payload did not contain a candidate list")
    return tuple(_normalize_prompt_eval_candidate(candidate) for candidate in candidates)


def load_live_candidates(live_candidates_path: Path) -> tuple[NormalizedCandidate, ...]:
    """Load and normalize a live reviewed-candidate snapshot."""

    payload = json.loads(live_candidates_path.read_text())
    if not isinstance(payload, list):
        raise ValueError("Live candidates payload must be a list")
    return tuple(_normalize_live_candidate(item) for item in payload)


def _normalize_prompt_eval_candidate(candidate: dict[str, Any]) -> NormalizedCandidate:
    """Normalize one prompt-eval candidate payload."""

    predicate = _require_string(candidate, "predicate")
    roles = _normalize_roles(candidate.get("roles", {}))
    evidence = _normalize_evidence(candidate.get("evidence_spans", []))
    claim_text = _optional_string(candidate.get("claim_text"))
    return NormalizedCandidate(predicate=predicate, roles=roles, evidence=evidence, claim_text=claim_text)


def _normalize_live_candidate(item: dict[str, Any]) -> NormalizedCandidate:
    """Normalize one live reviewed-candidate snapshot item."""

    candidate = item.get("candidate")
    if not isinstance(candidate, dict):
        raise ValueError("Live candidate snapshot item missing 'candidate' object")
    payload = candidate.get("normalized_payload") or candidate.get("payload")
    if not isinstance(payload, dict):
        raise ValueError("Live candidate snapshot missing normalized payload")
    predicate = _require_string(payload, "predicate")
    roles = _normalize_roles(payload.get("roles", {}))
    evidence = _normalize_evidence(candidate.get("evidence_spans", []))
    claim_text = _optional_string(candidate.get("claim_text"))
    return NormalizedCandidate(predicate=predicate, roles=roles, evidence=evidence, claim_text=claim_text)


def _normalize_roles(roles: Any) -> tuple[str, ...]:
    """Normalize role fillers into a deterministic signature."""

    if not isinstance(roles, dict):
        return ()
    normalized: list[str] = []
    for role_name in sorted(roles):
        fillers = roles[role_name]
        if not isinstance(fillers, list):
            continue
        for filler in fillers:
            if not isinstance(filler, dict):
                continue
            kind = _optional_string(filler.get("kind")) or "unknown"
            label = (
                _optional_string(filler.get("name"))
                or _optional_string(filler.get("normalized"))
                or _optional_string(filler.get("raw"))
                or _optional_string(filler.get("entity_id"))
                or _optional_string(filler.get("value_kind"))
                or "unknown"
            )
            normalized.append(f"{role_name}:{kind}:{label}")
    return tuple(sorted(normalized))


def _normalize_evidence(evidence_spans: Any) -> tuple[str, ...]:
    """Normalize evidence spans to their text content only."""

    if not isinstance(evidence_spans, list):
        return ()
    normalized: list[str] = []
    for span in evidence_spans:
        if not isinstance(span, dict):
            continue
        text = _optional_string(span.get("text"))
        if text:
            normalized.append(text)
    return tuple(sorted(normalized))


def _require_string(payload: dict[str, Any], key: str) -> str:
    """Return one required string field or raise a loud error."""

    value = payload.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"Expected non-empty string field {key!r}")
    return value


def _optional_string(value: Any) -> str | None:
    """Return an optional string field."""

    if isinstance(value, str) and value:
        return value
    return None


def _candidate_to_jsonable(candidate: NormalizedCandidate) -> dict[str, Any]:
    """Render one normalized candidate as JSON-safe data."""

    return {
        "predicate": candidate.predicate,
        "roles": list(candidate.roles),
        "evidence": list(candidate.evidence),
        "claim_text": candidate.claim_text,
    }

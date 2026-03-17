"""File-backed local ontology overlays for successor proving slices.

The successor needs a way to make accepted ontology additions operational
without mutating donor packs. This module provides the smallest workable
mechanism:

1. derive a deterministic local overlay pack reference from a donor pack;
2. persist accepted predicate additions into a repo-local JSONL file;
3. load those additions back into the ontology runtime on demand.

The current implementation supports predicate additions only. Other ontology
item kinds should fail loudly until there is a proven need to support them.
"""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from ..config import get_config
from .contracts import PackRef

_PREDICATE_OVERLAY_FILE = "predicate_additions.jsonl"


class OverlayRuntimeError(RuntimeError):
    """Raised when local overlay state is missing or malformed."""


class OverlayPredicateAdditionRecord(BaseModel):
    """One predicate addition written into a local overlay file."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    proposal_id: str = Field(min_length=1)
    predicate_id: str = Field(min_length=1)
    base_pack: PackRef
    overlay_pack: PackRef
    applied_by: str = Field(min_length=1)
    applied_at: str = Field(min_length=1)


def overlay_pack_ref_for(base_pack: PackRef) -> PackRef:
    """Return the deterministic local overlay-pack reference for one base pack."""

    suffix = get_config().ontology_runtime.overlay_pack_suffix
    return PackRef(
        pack_id=f"{base_pack.pack_id}{suffix}",
        pack_version=base_pack.pack_version,
    )


def overlay_root() -> Path:
    """Return the configured local overlay root directory."""

    return get_config().overlay_root()


def predicate_overlay_file_path(
    overlay_pack: PackRef,
    *,
    overlay_root_path: Path | None = None,
) -> Path:
    """Return the JSONL file path for one overlay pack's predicate additions."""

    root = (overlay_root_path or overlay_root()).resolve()
    return root / overlay_pack.pack_id / overlay_pack.pack_version / _PREDICATE_OVERLAY_FILE


def load_overlay_predicate_additions(
    overlay_pack: PackRef,
    *,
    overlay_root_path: Path | None = None,
) -> tuple[OverlayPredicateAdditionRecord, ...]:
    """Load persisted predicate additions for one overlay pack.

    Missing overlay files are treated as an empty overlay. Malformed JSON or
    non-object JSON lines fail loudly because validation must not silently use a
    partial overlay.
    """

    path = predicate_overlay_file_path(overlay_pack, overlay_root_path=overlay_root_path)
    if not path.exists():
        return ()

    additions: list[OverlayPredicateAdditionRecord] = []
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        try:
            decoded = json.loads(line)
        except json.JSONDecodeError as exc:
            raise OverlayRuntimeError(f"invalid JSON in {path}:{line_number}: {exc}") from exc
        if not isinstance(decoded, dict):
            raise OverlayRuntimeError(f"{path}:{line_number} must decode to an object")
        additions.append(OverlayPredicateAdditionRecord.model_validate(decoded))
    return tuple(additions)


def write_overlay_predicate_addition(
    record: OverlayPredicateAdditionRecord,
    *,
    overlay_root_path: Path | None = None,
) -> Path:
    """Persist one predicate addition into the local overlay file.

    This write path is idempotent by `proposal_id`. Re-applying the same
    proposal with the same predicate returns the existing file path. Re-applying
    the same proposal with a different predicate fails loudly.
    """

    path = predicate_overlay_file_path(record.overlay_pack, overlay_root_path=overlay_root_path)
    existing = load_overlay_predicate_additions(
        record.overlay_pack,
        overlay_root_path=overlay_root_path,
    )
    for addition in existing:
        if addition.proposal_id != record.proposal_id:
            continue
        if addition.predicate_id != record.predicate_id:
            raise OverlayRuntimeError(
                "existing overlay application has a different predicate_id "
                f"for proposal {record.proposal_id}"
            )
        return path

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(record.model_dump_json())
        handle.write("\n")
    return path


__all__ = [
    "OverlayPredicateAdditionRecord",
    "OverlayRuntimeError",
    "load_overlay_predicate_additions",
    "overlay_pack_ref_for",
    "overlay_root",
    "predicate_overlay_file_path",
    "write_overlay_predicate_addition",
]

"""Adapter that exports promoted graph assertions as Foundation Assertion IR.

The Foundation (``~/projects/project-meta/vision/FOUNDATION.md``) defines the
ecosystem's canonical ``Assertion`` interchange record.  This adapter reads the
promoted graph from onto-canon6's canonical graph store and produces the
Foundation format so that downstream consumers (Digimon, research_v3) can
ingest governed assertions without knowing onto-canon6 internals.

Schema mapping:
- ``assertion_id`` → direct copy
- ``predicate`` → direct copy
- ``roles`` → reconstructed from ``normalized_body`` (already has the right shape)
- ``qualifiers`` → populated from epistemic extension if available
- ``confidence`` → from epistemic extension (or None)
- ``provenance_refs`` → ``[source_candidate_id]``
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
import sqlite3
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, JsonValue

from ..core.graph_models import PromotedGraphAssertionRecord
from ..core.graph_store import CanonicalGraphStore

logger = logging.getLogger(__name__)


class FoundationRoleFiller(BaseModel):
    """One role filler in Foundation Assertion IR format."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: str = Field(description="entity, value, or unknown")
    entity_id: str | None = None
    name: str | None = None
    entity_type: str | None = None
    alias_ids: list[str] | None = None
    value_kind: str | None = None
    normalized: JsonValue | None = None
    raw: str | None = None


class FoundationAssertion(BaseModel):
    """One assertion in Foundation Assertion IR format.

    See ``~/projects/project-meta/vision/FOUNDATION.md`` section
    "Assertion IR (Primary Cross-Modal IR)".
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    assertion_id: str
    predicate: str
    roles: dict[str, list[dict[str, Any]]]
    qualifiers: dict[str, Any] = Field(default_factory=dict)
    confidence: float | None = None
    provenance_refs: list[str] = Field(default_factory=list)


def promoted_assertion_to_foundation(
    assertion: PromotedGraphAssertionRecord,
    *,
    confidence: float | None = None,
) -> FoundationAssertion:
    """Convert one onto-canon6 promoted assertion to Foundation Assertion IR.

    The ``normalized_body`` already contains ``predicate`` and ``roles`` in
    the correct shape (``dict[str, list[filler]]``).  This function extracts
    and validates the structure without lossy transformation.
    """

    body = assertion.normalized_body
    raw_roles = body.get("roles", {})

    # Normalize role fillers to Foundation shape.
    roles: dict[str, list[dict[str, Any]]] = {}
    if isinstance(raw_roles, dict):
        for role_name, fillers in raw_roles.items():
            if not isinstance(fillers, list):
                continue
            normalized_fillers: list[dict[str, Any]] = []
            for filler in fillers:
                if not isinstance(filler, dict):
                    continue
                foundation_filler: dict[str, Any] = {}
                kind = filler.get("kind", "unknown")
                foundation_filler["kind"] = kind

                if kind == "entity":
                    if "entity_id" in filler:
                        foundation_filler["entity_id"] = filler["entity_id"]
                    if "name" in filler:
                        foundation_filler["name"] = filler["name"]
                    if "entity_type" in filler:
                        foundation_filler["entity_type"] = filler["entity_type"]
                    if "alias_ids" in filler:
                        foundation_filler["alias_ids"] = filler["alias_ids"]
                elif kind == "value":
                    if "value_kind" in filler:
                        foundation_filler["value_kind"] = filler["value_kind"]
                    if "normalized" in filler:
                        foundation_filler["normalized"] = filler["normalized"]
                    if "raw" in filler:
                        foundation_filler["raw"] = filler["raw"]
                else:
                    # Preserve unknown/raw fillers.
                    if "raw" in filler:
                        foundation_filler["raw"] = filler["raw"]

                normalized_fillers.append(foundation_filler)
            if normalized_fillers:
                roles[role_name] = normalized_fillers

    qualifiers: dict[str, Any] = {}
    if confidence is not None:
        qualifiers["sys:confidence"] = confidence

    return FoundationAssertion(
        assertion_id=assertion.assertion_id,
        predicate=assertion.predicate,
        roles=roles,
        qualifiers=qualifiers,
        confidence=confidence,
        provenance_refs=[assertion.source_candidate_id],
    )


def export_foundation_assertions(
    db_path: Path | str,
    *,
    output_path: Path | str | None = None,
) -> list[FoundationAssertion]:
    """Export all promoted assertions from a review DB as Foundation Assertion IR.

    Returns the list and optionally writes to a JSON file.
    """

    store = CanonicalGraphStore()
    conn = sqlite3.connect(str(db_path))
    try:
        assertions = store.list_promoted_assertions(conn)
    finally:
        conn.close()

    foundation_assertions = [
        promoted_assertion_to_foundation(assertion)
        for assertion in assertions
    ]

    if output_path is not None:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w") as fh:
            json.dump(
                [a.model_dump(exclude_none=True) for a in foundation_assertions],
                fh,
                indent=2,
            )
        logger.info(
            "Exported %d Foundation assertions to %s",
            len(foundation_assertions),
            out,
        )

    return foundation_assertions


# Schema gap documentation for future work:
#
# 1. Entity names: Present in normalized_body roles (from extraction).
#    Foundation expects name on EntityRef. ✓ Covered.
#
# 2. Entity alias_ids: Foundation expects alias_ids on EntityRef.
#    onto-canon6 has these in the identity subsystem (GraphIdentityMembershipRecord).
#    Not yet wired into this export. TODO: join with identity store.
#
# 3. Qualifiers (sys:valid_from, sys:valid_to): onto-canon6 does not yet
#    extract temporal qualifiers. Deferred per ADR (temporal/inference deferred).
#
# 4. Confidence: Available from epistemic extension (ConfidenceAssessmentRecord).
#    Not yet wired. TODO: optional epistemic store join.
#
# 5. Provenance refs: Foundation expects event IDs and artifact IDs.
#    onto-canon6 provides source_candidate_id. To produce full provenance_refs,
#    join with artifact lineage store. TODO: wire artifact store.

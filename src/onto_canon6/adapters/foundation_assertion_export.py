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

try:
    from data_contracts import boundary
except ImportError:
    def boundary(**kwargs):
        def decorator(fn):
            return fn
        return decorator
from pydantic import BaseModel, ConfigDict, Field, JsonValue

from ..core.graph_models import PromotedGraphAssertionRecord
from ..core.graph_store import CanonicalGraphStore
from ..core.identity_store import IdentityStore

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


@boundary(
    name="onto-canon6.promoted_assertion_to_foundation",
    version="0.1.0",
    producer="onto-canon6",
    consumers=["digimon", "research_v3"],
)
def promoted_assertion_to_foundation(
    assertion: PromotedGraphAssertionRecord,
    *,
    confidence: float | None = None,
    alias_lookup: dict[str, list[str]] | None = None,
) -> FoundationAssertion:
    """Convert one onto-canon6 promoted assertion to Foundation Assertion IR.

    The ``normalized_body`` already contains ``predicate`` and ``roles`` in
    the correct shape (``dict[str, list[filler]]``).  This function extracts
    and validates the structure without lossy transformation.

    When ``alias_lookup`` is provided, entity fillers are enriched with
    ``alias_ids`` from the identity subsystem.  The lookup maps each
    ``entity_id`` to a list of other entity_ids that belong to the same
    identity (excluding the entity_id itself).
    """

    body = assertion.normalized_body
    raw_roles = body.get("roles", {})
    _aliases = alias_lookup or {}

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
                    entity_id_raw = filler.get("entity_id")
                    entity_id = entity_id_raw if isinstance(entity_id_raw, str) and entity_id_raw else None
                    if entity_id:
                        foundation_filler["entity_id"] = entity_id
                    if "name" in filler:
                        foundation_filler["name"] = filler["name"]
                    if "entity_type" in filler:
                        foundation_filler["entity_type"] = filler["entity_type"]
                    # Merge alias_ids from payload AND identity subsystem.
                    payload_aliases_raw = filler.get("alias_ids")
                    payload_aliases = (
                        [alias for alias in payload_aliases_raw if isinstance(alias, str)]
                        if isinstance(payload_aliases_raw, list)
                        else []
                    )
                    identity_aliases = _aliases.get(entity_id, []) if entity_id else []
                    merged = sorted(set(payload_aliases + identity_aliases))
                    if merged:
                        foundation_filler["alias_ids"] = merged
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
    # Temporal qualifiers from extraction payload
    valid_from = assertion.normalized_body.get("valid_from")
    valid_to = assertion.normalized_body.get("valid_to")
    if valid_from is not None:
        qualifiers["sys:valid_from"] = valid_from
    if valid_to is not None:
        qualifiers["sys:valid_to"] = valid_to

    return FoundationAssertion(
        assertion_id=assertion.assertion_id,
        predicate=assertion.predicate,
        roles=roles,
        qualifiers=qualifiers,
        confidence=confidence,
        provenance_refs=[assertion.source_candidate_id],
    )


def _build_alias_lookup(db_path: Path) -> dict[str, list[str]]:
    """Build entity_id → alias_ids mapping from the identity subsystem.

    For each entity that belongs to an identity, returns the other entity_ids
    in that same identity (excluding the entity itself).  Entities with no
    identity membership return an empty list (omitted from the dict).
    """

    identity_store = IdentityStore(db_path)
    alias_map: dict[str, list[str]] = {}
    try:
        with identity_store.transaction() as conn:
            identities = identity_store.list_identities(conn)
            for identity in identities:
                memberships = identity_store.list_memberships_for_identity(
                    conn, identity_id=identity.identity_id,
                )
                entity_ids = [m.entity_id for m in memberships]
                if len(entity_ids) < 2:
                    continue
                for eid in entity_ids:
                    alias_map[eid] = sorted(
                        other for other in entity_ids if other != eid
                    )
    except Exception as exc:
        logger.warning("Could not build alias lookup from identity store: %s", exc)
    return alias_map


@boundary(
    name="onto-canon6.export_foundation_assertions",
    version="0.1.0",
    producer="onto-canon6",
    consumers=["digimon", "research_v3"],
    validate_input=False,
    validate_output=False,
)
def export_foundation_assertions(
    db_path: Path | str,
    *,
    output_path: Path | str | None = None,
    include_aliases: bool = True,
) -> list[FoundationAssertion]:
    """Export all promoted assertions from a review DB as Foundation Assertion IR.

    When ``include_aliases`` is True (default), entity fillers are enriched
    with ``alias_ids`` from the identity subsystem so consumers can resolve
    entities across exports without reimplementing dedup.

    Returns the list and optionally writes to a JSON file.
    """

    resolved_path = Path(db_path)
    store = CanonicalGraphStore(resolved_path)
    conn = sqlite3.connect(str(resolved_path))
    conn.row_factory = sqlite3.Row
    try:
        assertions = store.list_promoted_assertions(conn)
    finally:
        conn.close()

    alias_lookup = _build_alias_lookup(resolved_path) if include_aliases else None

    foundation_assertions = [
        promoted_assertion_to_foundation(assertion, alias_lookup=alias_lookup)
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


# Schema gap documentation:
#
# 1. Entity names: ✓ Present in normalized_body roles.
#
# 2. Entity alias_ids: ✓ WIRED. Identity subsystem joined via _build_alias_lookup().
#    Entities with identity memberships get alias_ids from sibling entity_ids.
#
# 3. Qualifiers (sys:valid_from, sys:valid_to): Temporal qualifiers are now
#    extracted when present in source text and exported as sys:valid_from/to.
#    Assertions without temporal info export with empty qualifiers (not failure).
#
# 4. Confidence: Available from epistemic extension (ConfidenceAssessmentRecord).
#    Passed as optional kwarg. TODO: optional epistemic store join in export.
#
# 5. Provenance refs: Foundation expects event IDs and artifact IDs.
#    onto-canon6 provides source_candidate_id. Wrapper adds Foundation envelope.
#    Decision: onto-canon6 does NOT adopt Foundation event log internally.

"""Adapter that exports onto-canon6 promoted graph assertions in Digimon-compatible format.

Digimon (the composable knowledge-graph retrieval system) expects ``EntityRecord``
and ``RelationshipRecord`` dataclasses as its ingestion format.  This adapter reads
the promoted graph from onto-canon6's canonical graph store and produces standalone
JSONL files that Digimon graph builders can load without any onto-canon6 dependency.

The mapping:
- Each ``PromotedGraphEntityRecord`` becomes a ``DigimonEntityRecord`` with the
  human-readable name extracted from the assertion body's role fillers.
- Each ``PromotedGraphAssertionRecord`` with entity role fillers in ARG0 and ARG1
  positions becomes a ``DigimonRelationshipRecord``.
- Assertions with only one entity argument (e.g. only ARG0 or only ARG1) are
  still emitted as relationships with the missing endpoint set to an empty string,
  so no data is silently dropped.
"""

from __future__ import annotations

import dataclasses
import json
import logging
from pathlib import Path
import sqlite3
from typing import Sequence

from ..core.graph_models import (
    PromotedGraphAssertionRecord,
    PromotedGraphEntityRecord,
    PromotedGraphRoleFillerRecord,
)
from ..core.graph_service import CanonicalGraphService
from ..core.graph_store import CanonicalGraphStore
from ..pipeline.service import ReviewService

logger = logging.getLogger(__name__)


@dataclasses.dataclass(frozen=True)
class DigimonEntityRecord:
    """Entity in Digimon's expected format.

    Maps onto-canon6 ``PromotedGraphEntityRecord`` to the flat structure that
    Digimon's ``EntityRecord`` (``Core/Schema/SlotTypes.py``) expects when
    loaded from JSONL.
    """

    entity_name: str
    source_id: str
    entity_type: str = ""
    description: str = ""
    rank: int = 0


@dataclasses.dataclass(frozen=True)
class DigimonRelationshipRecord:
    """Relationship in Digimon's expected format.

    Maps onto-canon6 promoted assertions (with entity role fillers) to the
    flat structure that Digimon's ``RelationshipRecord`` expects when loaded
    from JSONL.
    """

    src_id: str
    tgt_id: str
    relation_name: str = ""
    description: str = ""
    weight: float = 1.0
    keywords: str = ""
    source_id: str = ""


@dataclasses.dataclass(frozen=True)
class DigimonExportBundle:
    """Complete export for Digimon ingestion.

    Contains all promoted entities and relationships in Digimon-compatible
    format, plus provenance metadata pointing back to the onto-canon6 database
    that produced the data.
    """

    entities: list[DigimonEntityRecord]
    relationships: list[DigimonRelationshipRecord]
    source_onto_canon_db: str


def export_for_digimon(
    *,
    graph_service: CanonicalGraphService,
    review_service: ReviewService,
) -> DigimonExportBundle:
    """Export the promoted graph in Digimon-compatible format.

    Reads all promoted assertions and entities from the graph service's
    underlying store and maps them to Digimon's ``EntityRecord`` and
    ``RelationshipRecord`` shapes.

    The ``review_service`` is accepted for API symmetry with the existing
    promoted-graph report surface but is not currently used for the export.
    Future extensions may pull claim text or governance metadata from it.
    """
    store = graph_service._store  # noqa: SLF001 — adapter needs direct store access for bulk reads
    db_path_str = str(graph_service.db_path)

    with store.transaction() as conn:
        assertions = store.list_promoted_assertions(conn)
        all_entities = _list_all_entities(conn)
        entity_name_map = _build_entity_name_map(assertions)
        filler_map = _build_filler_map(conn, store, assertions)
        epistemic_confidence = _load_epistemic_confidence(conn)

    digimon_entities = _convert_entities(all_entities, entity_name_map)
    digimon_relationships = _convert_relationships(
        assertions, filler_map, entity_name_map, epistemic_confidence,
    )

    bundle = DigimonExportBundle(
        entities=digimon_entities,
        relationships=digimon_relationships,
        source_onto_canon_db=db_path_str,
    )
    logger.info(
        "digimon export completed entities=%d relationships=%d db=%s",
        len(bundle.entities),
        len(bundle.relationships),
        db_path_str,
    )
    return bundle


def export_for_digimon_from_db(
    review_db_path: Path,
) -> DigimonExportBundle:
    """Convenience: open services and export.

    Creates a ``CanonicalGraphService`` and ``ReviewService`` from the
    given database path and delegates to ``export_for_digimon``.
    """
    graph_service = CanonicalGraphService(db_path=review_db_path)
    review_service = ReviewService(db_path=review_db_path)
    return export_for_digimon(
        graph_service=graph_service,
        review_service=review_service,
    )


def write_digimon_jsonl(
    bundle: DigimonExportBundle,
    output_dir: Path,
) -> tuple[Path, Path]:
    """Write entities.jsonl and relationships.jsonl files.

    Each line is a JSON object matching the fields of ``DigimonEntityRecord``
    or ``DigimonRelationshipRecord``.  The JSONL format matches what Digimon's
    graph builders expect when loading pre-extracted relations.

    Returns ``(entities_path, relationships_path)``.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    entities_path = output_dir / "entities.jsonl"
    relationships_path = output_dir / "relationships.jsonl"

    with entities_path.open("w", encoding="utf-8") as f:
        for entity in bundle.entities:
            f.write(json.dumps(dataclasses.asdict(entity), ensure_ascii=False, sort_keys=True))
            f.write("\n")

    with relationships_path.open("w", encoding="utf-8") as f:
        for rel in bundle.relationships:
            f.write(json.dumps(dataclasses.asdict(rel), ensure_ascii=False, sort_keys=True))
            f.write("\n")

    logger.info(
        "digimon JSONL written entities_path=%s relationships_path=%s entity_count=%d relationship_count=%d",
        entities_path,
        relationships_path,
        len(bundle.entities),
        len(bundle.relationships),
    )
    return entities_path, relationships_path


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _list_all_entities(conn: sqlite3.Connection) -> list[PromotedGraphEntityRecord]:
    """Query all promoted graph entities in deterministic order.

    The ``CanonicalGraphStore`` only exposes per-assertion entity listing.
    This helper runs a direct SQL query for the full entity set.
    """
    rows: list[sqlite3.Row] = conn.execute(
        """
        SELECT entity_id, entity_type, first_candidate_id, created_at
        FROM promoted_graph_entities
        ORDER BY created_at, entity_id
        """
    ).fetchall()
    return [
        PromotedGraphEntityRecord(
            entity_id=str(row["entity_id"]),
            entity_type=str(row["entity_type"]) if row["entity_type"] is not None else None,
            first_candidate_id=str(row["first_candidate_id"]),
            created_at=str(row["created_at"]),
        )
        for row in rows
    ]


def _build_entity_name_map(
    assertions: Sequence[PromotedGraphAssertionRecord],
) -> dict[str, str]:
    """Build a mapping from entity_id to human-readable name.

    The human-readable name lives in the assertion's ``normalized_body``
    under ``roles -> ARGn -> [{"name": "...", "entity_id": "..."}]``.
    The entity table itself only stores the slugified entity_id.  This
    function extracts the first ``name`` seen for each entity_id across
    all assertions.
    """
    name_map: dict[str, str] = {}
    for assertion in assertions:
        roles = assertion.normalized_body.get("roles")
        if not isinstance(roles, dict):
            continue
        for _role_id, fillers in roles.items():
            if not isinstance(fillers, list):
                continue
            for filler in fillers:
                if not isinstance(filler, dict):
                    continue
                entity_id = filler.get("entity_id")
                name = filler.get("name")
                if isinstance(entity_id, str) and isinstance(name, str) and entity_id not in name_map:
                    name_map[entity_id] = name
    return name_map


def _build_filler_map(
    conn: sqlite3.Connection,
    store: CanonicalGraphStore,
    assertions: Sequence[PromotedGraphAssertionRecord],
) -> dict[str, tuple[PromotedGraphRoleFillerRecord, ...]]:
    """Load role fillers for every assertion, keyed by assertion_id.

    Uses the store's ``list_role_fillers_for_assertion`` to get typed
    filler records with entity_id references.
    """
    result: dict[str, tuple[PromotedGraphRoleFillerRecord, ...]] = {}
    for assertion in assertions:
        result[assertion.assertion_id] = store.list_role_fillers_for_assertion(
            conn,
            assertion_id=assertion.assertion_id,
        )
    return result


def _convert_entities(
    entities: Sequence[PromotedGraphEntityRecord],
    name_map: dict[str, str],
) -> list[DigimonEntityRecord]:
    """Convert onto-canon6 entities to Digimon entity records.

    Uses the ``name_map`` to resolve human-readable names from entity_ids.
    Falls back to the entity_id itself if no name was found in any assertion.
    """
    result: list[DigimonEntityRecord] = []
    for entity in entities:
        human_name = name_map.get(entity.entity_id, entity.entity_id)
        result.append(
            DigimonEntityRecord(
                entity_name=human_name,
                source_id=entity.entity_id,
                entity_type=entity.entity_type or "",
                description="",
                rank=0,
            )
        )
    return result


def _load_epistemic_confidence(conn: sqlite3.Connection) -> dict[str, float]:
    """Load epistemic confidence scores keyed by candidate_id.

    Returns an empty dict if the epistemic tables don't exist yet.
    """
    try:
        rows = conn.execute(
            "SELECT candidate_id, confidence_score "
            "FROM epistemic_confidence_assessments"
        ).fetchall()
        return {str(row["candidate_id"]): float(row["confidence_score"]) for row in rows}
    except Exception:
        return {}


def _convert_relationships(
    assertions: Sequence[PromotedGraphAssertionRecord],
    filler_map: dict[str, tuple[PromotedGraphRoleFillerRecord, ...]],
    name_map: dict[str, str],
    epistemic_confidence: dict[str, float] | None = None,
) -> list[DigimonRelationshipRecord]:
    """Convert promoted assertions to Digimon relationship records.

    Each assertion becomes one relationship.  The source is the first
    entity filler in ARG0, and the target is the first entity filler in
    ARG1.  Assertions that have no entity fillers at all are skipped
    (they are value-only assertions with no relational structure).

    Assertions with only one entity argument are emitted with the missing
    endpoint as an empty string so downstream consumers can detect and
    handle single-argument predicates.
    """
    result: list[DigimonRelationshipRecord] = []
    for assertion in assertions:
        fillers = filler_map.get(assertion.assertion_id, ())
        entity_by_role = _entity_fillers_by_role(fillers)

        # Skip assertions with zero entity fillers
        if not entity_by_role:
            continue

        src_entity_id = entity_by_role.get("ARG0", "")
        tgt_entity_id = entity_by_role.get("ARG1", "")

        # If neither ARG0 nor ARG1 but there are other roles, use whatever is available
        if not src_entity_id and not tgt_entity_id:
            available_roles = sorted(entity_by_role.keys())
            if len(available_roles) >= 1:
                src_entity_id = entity_by_role[available_roles[0]]
            if len(available_roles) >= 2:
                tgt_entity_id = entity_by_role[available_roles[1]]

        src_name = name_map.get(src_entity_id, src_entity_id) if src_entity_id else ""
        tgt_name = name_map.get(tgt_entity_id, tgt_entity_id) if tgt_entity_id else ""

        # Prefer epistemic confidence (from epistemic_confidence_assessments table),
        # fall back to payload confidence, default to 1.0
        epistemic_conf = (
            epistemic_confidence.get(assertion.source_candidate_id)
            if epistemic_confidence else None
        )
        payload_conf = assertion.normalized_body.get("confidence")
        if epistemic_conf is not None:
            weight = float(epistemic_conf)
        elif isinstance(payload_conf, (int, float)):
            weight = float(payload_conf)
        else:
            weight = 1.0

        result.append(
            DigimonRelationshipRecord(
                src_id=src_name,
                tgt_id=tgt_name,
                relation_name=assertion.predicate,
                description=assertion.claim_text or "",
                weight=weight,
                keywords="",
                source_id=assertion.assertion_id,
            )
        )
    return result


def _entity_fillers_by_role(
    fillers: Sequence[PromotedGraphRoleFillerRecord],
) -> dict[str, str]:
    """Extract the first entity filler entity_id for each role.

    Returns a dict mapping role_id (e.g. "ARG0", "ARG1") to entity_id.
    Only entity fillers (not value fillers) are included.
    """
    result: dict[str, str] = {}
    for filler in fillers:
        if filler.filler_kind == "entity" and filler.entity_id and filler.role_id not in result:
            result[filler.role_id] = filler.entity_id
    return result


__all__ = [
    "DigimonEntityRecord",
    "DigimonExportBundle",
    "DigimonRelationshipRecord",
    "export_for_digimon",
    "export_for_digimon_from_db",
    "write_digimon_jsonl",
]

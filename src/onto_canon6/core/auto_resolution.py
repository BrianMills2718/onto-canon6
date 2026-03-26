"""Automated entity resolution over promoted graph entities.

Groups promoted entities by matching display names and creates stable
identities for each group.

Resolution strategies:
- ``exact``: case-insensitive exact name match (default, zero false positives)
- ``fuzzy``: rapidfuzz token_sort_ratio with configurable threshold and
  same-entity-type guard (requires rapidfuzz)

Auto-resolved identities are created with ``created_by="auto:resolution"``
so they can be distinguished from manual identity assignments.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from .graph_models import PromotedGraphAssertionRecord
from .graph_service import CanonicalGraphService
from .identity_service import IdentityConflictError, IdentityService

logger = logging.getLogger(__name__)

ResolutionStrategy = Literal["exact", "fuzzy"]

ACTOR_ID = "auto:resolution"
DEFAULT_FUZZY_THRESHOLD = 85


@dataclass(frozen=True)
class ResolutionResult:
    """Summary of one automated identity resolution run."""

    entities_scanned: int
    groups_found: int
    identities_created: int
    aliases_attached: int
    already_resolved: int
    strategy: str


def auto_resolve_identities(
    *,
    db_path: Path,
    strategy: ResolutionStrategy = "exact",
    fuzzy_threshold: int = DEFAULT_FUZZY_THRESHOLD,
) -> ResolutionResult:
    """Run automated entity resolution over all promoted entities.

    Groups promoted entities by normalized display name and creates
    stable identities for each group. The first entity in each group
    becomes the canonical member; subsequent entities become aliases.

    For ``fuzzy`` strategy, entities with token_sort_ratio >= threshold
    AND the same entity_type are grouped together. The entity_type guard
    prevents false positives (e.g., "USSOCOM" the org vs "USSOCOM Commander"
    the person).

    Entities that already have an identity membership are skipped.
    """
    graph_service = CanonicalGraphService(db_path=db_path)
    identity_service = IdentityService(db_path=db_path)

    store = graph_service._store  # noqa: SLF001
    with store.transaction() as conn:
        assertions = store.list_promoted_assertions(conn)
        all_entities = conn.execute(
            "SELECT entity_id, entity_type FROM promoted_graph_entities "
            "ORDER BY created_at, entity_id"
        ).fetchall()

    entity_ids = [str(row[0]) for row in all_entities]
    entity_types = {str(row[0]): str(row[1]) if row[1] else "" for row in all_entities}
    name_map = _build_entity_name_map(assertions)

    if strategy == "fuzzy":
        groups = _group_by_fuzzy(entity_ids, name_map, entity_types, fuzzy_threshold)
    else:
        groups = _group_by_name(entity_ids, name_map, strategy)

    identities_created = 0
    aliases_attached = 0
    already_resolved = 0

    for _key, group_entity_ids in sorted(groups.items()):
        if len(group_entity_ids) < 2:
            canonical_id = group_entity_ids[0]
            display = name_map.get(canonical_id, canonical_id)
            try:
                bundle = identity_service.create_identity_for_entity(
                    entity_id=canonical_id,
                    created_by=ACTOR_ID,
                    display_label=display,
                )
                if len(bundle.memberships) == 1:
                    identities_created += 1
                else:
                    already_resolved += 1
            except (IdentityConflictError, Exception) as exc:
                logger.debug("skip entity %s: %s", canonical_id, exc)
                already_resolved += 1
            continue

        canonical_id = group_entity_ids[0]
        display = name_map.get(canonical_id, canonical_id)
        try:
            bundle = identity_service.create_identity_for_entity(
                entity_id=canonical_id,
                created_by=ACTOR_ID,
                display_label=display,
            )
            identity_id = bundle.identity.identity_id
            if len(bundle.memberships) == 1:
                identities_created += 1
            else:
                already_resolved += 1
        except Exception as exc:
            logger.warning("failed to create identity for %s: %s", canonical_id, exc)
            already_resolved += 1
            continue

        for alias_entity_id in group_entity_ids[1:]:
            try:
                identity_service.attach_entity_alias(
                    identity_id=identity_id,
                    entity_id=alias_entity_id,
                    attached_by=ACTOR_ID,
                )
                aliases_attached += 1
            except IdentityConflictError:
                already_resolved += 1
            except Exception as exc:
                logger.warning(
                    "failed to attach alias %s to %s: %s",
                    alias_entity_id, identity_id, exc,
                )

    return ResolutionResult(
        entities_scanned=len(entity_ids),
        groups_found=len(groups),
        identities_created=identities_created,
        aliases_attached=aliases_attached,
        already_resolved=already_resolved,
        strategy=strategy,
    )


def _build_entity_name_map(
    assertions: list[PromotedGraphAssertionRecord],
) -> dict[str, str]:
    """Build entity_id → display name map from assertion role fillers."""
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
                if (
                    isinstance(entity_id, str)
                    and isinstance(name, str)
                    and entity_id not in name_map
                ):
                    name_map[entity_id] = name
    return name_map


def _normalize_name(name: str) -> str:
    """Normalize entity name for matching: lowercase, collapse whitespace."""
    return " ".join(name.lower().split())


def _group_by_name(
    entity_ids: list[str],
    name_map: dict[str, str],
    strategy: ResolutionStrategy,
) -> dict[str, list[str]]:
    """Group entity IDs by normalized display name (exact match)."""
    groups: dict[str, list[str]] = defaultdict(list)
    for entity_id in entity_ids:
        display_name = name_map.get(entity_id, entity_id)
        key = _normalize_name(display_name)
        groups[key].append(entity_id)
    return dict(groups)


def _group_by_fuzzy(
    entity_ids: list[str],
    name_map: dict[str, str],
    entity_types: dict[str, str],
    threshold: int,
) -> dict[str, list[str]]:
    """Group entity IDs by fuzzy name similarity with entity_type guard.

    Uses rapidfuzz token_sort_ratio for similarity scoring. Two entities
    are grouped only if:
    1. Their normalized names score >= threshold on token_sort_ratio
    2. They share the same entity_type (false-positive guard)

    Uses union-find for transitive closure of fuzzy matches.
    """
    from rapidfuzz import fuzz

    normalized = {eid: _normalize_name(name_map.get(eid, eid)) for eid in entity_ids}

    # Union-find
    parent: dict[str, str] = {eid: eid for eid in entity_ids}

    def find(x: str) -> str:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: str, b: str) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    # Pairwise comparison (O(n^2) but entity counts are small)
    for i, eid_a in enumerate(entity_ids):
        for eid_b in entity_ids[i + 1:]:
            type_a = entity_types.get(eid_a, "")
            type_b = entity_types.get(eid_b, "")

            # Entity type guard: only merge same-type entities
            if type_a and type_b and type_a != type_b:
                continue

            score = fuzz.token_sort_ratio(normalized[eid_a], normalized[eid_b])
            if score >= threshold:
                union(eid_a, eid_b)
                logger.debug(
                    "fuzzy match score=%d: %s ↔ %s",
                    score, normalized[eid_a], normalized[eid_b],
                )

    # Collect groups
    groups: dict[str, list[str]] = defaultdict(list)
    for eid in entity_ids:
        root = find(eid)
        groups[root].append(eid)

    return dict(groups)


__all__ = [
    "ResolutionResult",
    "ResolutionStrategy",
    "auto_resolve_identities",
]

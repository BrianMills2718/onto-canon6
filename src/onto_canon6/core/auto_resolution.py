"""Automated entity resolution over promoted graph entities.

Groups promoted entities by matching display names and creates stable
identities for each group.

Resolution strategies:
- ``exact``: case-insensitive exact name match (default, zero false positives)
- ``fuzzy``: rapidfuzz token_sort_ratio with configurable threshold and
  same-entity-type guard (requires rapidfuzz)
- ``llm``: LLM-based entity clustering per entity type, optionally with fuzzy
  pre-filtering. Fuzzy-proposed clusters go through LLM validation (no direct
  fuzzy merges). Uses ``llm_client`` with mandatory ``task=``, ``trace_id=``,
  ``max_budget=`` kwargs.

Auto-resolved identities are created with ``created_by="auto:resolution"``
so they can be distinguished from manual identity assignments.
"""

from __future__ import annotations

import asyncio
import json
import logging
import uuid as _uuid
from collections import defaultdict
from dataclasses import dataclass, field
from importlib import import_module
from pathlib import Path
from typing import Any, Literal, Protocol

from .graph_models import PromotedGraphAssertionRecord
from .graph_service import CanonicalGraphService
from .identity_service import IdentityConflictError, IdentityService

logger = logging.getLogger(__name__)

ResolutionStrategy = Literal["exact", "fuzzy", "llm"]


def _oc_type_to_sumo(oc_type: str) -> str:
    """Convert oc:snake_case entity type to SUMO CamelCase.

    ``oc:military_organization`` → ``MilitaryOrganization``
    ``oc_military_organization`` → ``MilitaryOrganization``
    ``militaryorganization`` → ``MilitaryOrganization`` (best effort)
    """
    # Strip oc: or oc_ prefix
    t = oc_type
    if t.startswith("oc:"):
        t = t[3:]
    elif t.startswith("oc_"):
        t = t[3:]

    # Convert snake_case to CamelCase
    parts = t.split("_")
    return "".join(p.capitalize() for p in parts if p)


def _types_compatible(type_a: str, type_b: str, *, sumo_db_path: Path | None = None) -> bool:
    """Check if two entity types are compatible for resolution.

    Compatible means: same type, one is ancestor of the other, or they share
    a common ancestor within depth 3 (top-level category like Organization,
    Person, etc.).

    Falls back to exact match if sumo_plus.db is not available.
    """
    if not type_a or not type_b:
        return True  # Unknown types are compatible with anything

    # Normalize both to SUMO CamelCase
    sumo_a = _oc_type_to_sumo(type_a)
    sumo_b = _oc_type_to_sumo(type_b)

    # Exact match after normalization
    if sumo_a.lower() == sumo_b.lower():
        return True

    # Try ancestor lookup if DB available
    if sumo_db_path is None:
        # Try default location
        default_db = Path("data/sumo_plus.db")
        if default_db.exists():
            sumo_db_path = default_db

    if sumo_db_path is None or not sumo_db_path.exists():
        # No DB — fall back to exact match (already failed above)
        return False

    import sqlite3
    conn = sqlite3.connect(str(sumo_db_path))
    try:
        # Get ancestors of both types (within depth 3)
        ancestors_a = {
            row[0].lower()
            for row in conn.execute(
                "SELECT ancestor_id FROM type_ancestors WHERE type_id = ? AND depth <= 3",
                (sumo_a,),
            ).fetchall()
        }
        ancestors_a.add(sumo_a.lower())

        ancestors_b = {
            row[0].lower()
            for row in conn.execute(
                "SELECT ancestor_id FROM type_ancestors WHERE type_id = ? AND depth <= 3",
                (sumo_b,),
            ).fetchall()
        }
        ancestors_b.add(sumo_b.lower())

        # Compatible if one is ancestor of the other, or they share an ancestor
        return bool(ancestors_a & ancestors_b)
    finally:
        conn.close()

ACTOR_ID = "auto:resolution"
DEFAULT_FUZZY_THRESHOLD = 85

# Title/honorific patterns for name normalization (military, government, academic, civilian)
_TITLE_PATTERNS: list[tuple[str, str]] = [
    # Military ranks — abbreviations and full forms
    ("gen.", "general"),
    ("lt. gen.", "lieutenant general"),
    ("maj. gen.", "major general"),
    ("brig. gen.", "brigadier general"),
    ("col.", "colonel"),
    ("lt. col.", "lieutenant colonel"),
    ("maj.", "major"),
    ("capt.", "captain"),
    ("cpt.", "captain"),
    ("lt.", "lieutenant"),
    ("1lt.", "first lieutenant"),
    ("2lt.", "second lieutenant"),
    ("sgt.", "sergeant"),
    ("sgt. maj.", "sergeant major"),
    ("msgt.", "master sergeant"),
    ("ssgt.", "staff sergeant"),
    ("cpl.", "corporal"),
    ("pvt.", "private"),
    ("adm.", "admiral"),
    ("vadm.", "vice admiral"),
    ("radm.", "rear admiral"),
    ("cmdr.", "commander"),
    ("cdr.", "commander"),
    ("lcdr.", "lieutenant commander"),
    ("ens.", "ensign"),
    # Civilian / academic / government
    ("dr.", "doctor"),
    ("mr.", ""),
    ("mrs.", ""),
    ("ms.", ""),
    ("prof.", "professor"),
    ("sen.", "senator"),
    ("rep.", "representative"),
    ("gov.", "governor"),
    ("amb.", "ambassador"),
    ("sec.", "secretary"),
    ("pres.", "president"),
    ("hon.", "honorable"),
]

# Full-form titles to strip entirely (they add no identity signal)
_STRIP_TITLES: set[str] = {
    "general", "lieutenant general", "major general", "brigadier general",
    "colonel", "lieutenant colonel", "major", "captain", "lieutenant",
    "first lieutenant", "second lieutenant", "sergeant", "sergeant major",
    "master sergeant", "staff sergeant", "corporal", "private",
    "admiral", "vice admiral", "rear admiral", "commander",
    "lieutenant commander", "ensign",
    "doctor", "professor", "senator", "representative", "governor",
    "ambassador", "secretary", "president", "honorable",
    "mister", "miss", "sir", "madam", "dame",
}


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
    require_llm_review: bool | None = None,
) -> ResolutionResult:
    """Run automated entity resolution over all promoted entities.

    Groups promoted entities by normalized display name and creates
    stable identities for each group. The first entity in each group
    becomes the canonical member; subsequent entities become aliases.

    When ``require_llm_review`` is True (default from config), candidate
    groups from exact/fuzzy strategies are validated by an LLM before
    merging. The LLM sees entity names + context and confirms or rejects
    each proposed merge. The ``llm`` strategy always does LLM review
    regardless of this flag.

    Entities that already have an identity membership are skipped.
    """
    # Load config for defaults
    try:
        from ..config import get_config
        config = get_config()
        res_cfg = config.resolution
    except Exception:
        res_cfg = None

    if require_llm_review is None:
        require_llm_review = res_cfg.require_llm_review if res_cfg else False

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
    context_map = _build_context_map(assertions)

    # Step 1: Generate candidate groups
    if strategy == "llm":
        groups = _group_by_llm(
            entity_ids, name_map, entity_types, context_map, assertions,
            model=res_cfg.model_override if res_cfg else None,
            max_budget=res_cfg.max_budget_usd if res_cfg else 0.50,
            prompt_template=res_cfg.cluster_prompt_template if res_cfg else "prompts/resolution/cluster_entities.yaml",
            fuzzy_pre_filter_threshold=res_cfg.fuzzy_pre_filter_threshold if res_cfg else 80,
            batch_token_limit=res_cfg.batch_token_limit if res_cfg else 50000,
            min_entities_for_llm=res_cfg.min_entities_for_llm if res_cfg else 2,
        )
        # LLM strategy already validates — skip require_llm_review
    elif strategy == "fuzzy":
        groups = _group_by_fuzzy(entity_ids, name_map, entity_types, fuzzy_threshold)
    else:
        groups = _group_by_name(entity_ids, name_map, strategy)

    # Step 2: LLM validation of candidate groups (if required and not already LLM)
    if require_llm_review and strategy != "llm":
        has_multi_member = any(len(g) >= 2 for g in groups.values())
        if has_multi_member:
            groups = _validate_groups_with_llm(
                groups, name_map, entity_types, context_map,
                model=res_cfg.model_override if res_cfg else None,
                max_budget=res_cfg.max_budget_usd if res_cfg else 0.50,
                validate_prompt_template=res_cfg.validate_prompt_template if res_cfg else "prompts/resolution/validate_merge.yaml",
            )

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
    """Normalize entity name for matching.

    Steps:
    1. Lowercase and collapse whitespace
    2. Expand known abbreviations (``Gen.`` → ``general``)
    3. Strip titles/honorifics that add no identity signal
    4. Strip trailing punctuation artifacts
    5. Collapse whitespace again after stripping
    """
    result = " ".join(name.lower().split())

    # Expand abbreviations — longest match first to avoid partial replacements
    for abbrev, expansion in sorted(_TITLE_PATTERNS, key=lambda t: -len(t[0])):
        if result.startswith(abbrev + " "):
            result = (expansion + " " + result[len(abbrev) + 1:]).strip()
        elif result.startswith(abbrev):
            result = (expansion + " " + result[len(abbrev):]).strip()

    # Strip full-form titles from the beginning of the name
    words = result.split()
    while words and words[0] in _STRIP_TITLES:
        words.pop(0)

    # Handle two-word titles like "lieutenant general"
    while len(words) >= 2 and f"{words[0]} {words[1]}" in _STRIP_TITLES:
        words.pop(0)
        words.pop(0)

    result = " ".join(words) if words else result

    # Strip trailing punctuation artifacts (periods, commas)
    result = result.strip(" .,;:")

    return " ".join(result.split())


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

            # Entity type guard: only merge compatible-type entities
            # Uses SUMO type hierarchy when available (is-a relationship)
            if type_a and type_b and not _types_compatible(type_a, type_b):
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


# ---------------------------------------------------------------------------
# LLM-based entity clustering and merge validation
# ---------------------------------------------------------------------------

from pydantic import BaseModel, ConfigDict, Field


class EntityCluster(BaseModel):
    """One cluster of entities that refer to the same real-world entity."""

    model_config = ConfigDict(extra="ignore")

    canonical_name: str = Field(description="Best full canonical name for this entity")
    entity_ids: list[str] = Field(description="Entity IDs that refer to this same entity")
    reasoning: str = Field(description="Why these are the same entity, citing evidence")


class ClusteringResult(BaseModel):
    """LLM output: all entity clusters for one entity type."""

    model_config = ConfigDict(extra="ignore")

    clusters: list[EntityCluster]


class MergeValidation(BaseModel):
    """LLM output: whether a proposed merge group should be confirmed."""

    model_config = ConfigDict(extra="ignore")

    confirm: bool = Field(description="True if all entities in the group refer to the same real-world entity")
    reasoning: str = Field(description="Why the merge is confirmed or rejected")


@dataclass(frozen=True)
class _EntityInfo:
    """Entity metadata passed to the clustering prompt."""

    entity_id: str
    name: str
    entity_type: str
    context: str  # from claim_text of assertions involving this entity


@dataclass(frozen=True)
class _FuzzyProposal:
    """A fuzzy-proposed cluster to be validated by the LLM."""

    entities: list[_EntityInfo]


def _build_entity_info_list(
    entity_ids: list[str],
    name_map: dict[str, str],
    entity_types: dict[str, str],
    context_map: dict[str, str],
) -> list[_EntityInfo]:
    """Build entity info list for clustering prompt."""
    return [
        _EntityInfo(
            entity_id=eid,
            name=name_map.get(eid, eid),
            entity_type=entity_types.get(eid, "unknown"),
            context=context_map.get(eid, ""),
        )
        for eid in entity_ids
    ]


def _build_context_map(
    assertions: list[PromotedGraphAssertionRecord],
) -> dict[str, str]:
    """Build entity_id → context snippet map from assertion claim_text."""
    context_map: dict[str, str] = {}
    for assertion in assertions:
        claim_text = assertion.claim_text or ""
        if not claim_text:
            continue
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
                if isinstance(entity_id, str) and entity_id not in context_map:
                    # Use first ~200 chars of claim_text as context
                    context_map[entity_id] = claim_text[:200]
    return context_map


def _fuzzy_pre_filter(
    entities: list[_EntityInfo],
    threshold: int,
) -> tuple[list[_FuzzyProposal], list[_EntityInfo]]:
    """Generate fuzzy candidate clusters for LLM review.

    Returns (proposals, unclustered). Proposals are groups of 2+ entities
    with fuzzy similarity above threshold. Unclustered are singletons.
    """
    from rapidfuzz import fuzz

    entity_ids = [e.entity_id for e in entities]
    name_map = {e.entity_id: e.name for e in entities}
    entity_types = {e.entity_id: e.entity_type for e in entities}

    fuzzy_groups = _group_by_fuzzy(entity_ids, name_map, entity_types, threshold)

    info_map = {e.entity_id: e for e in entities}
    proposals: list[_FuzzyProposal] = []
    unclustered: list[_EntityInfo] = []

    for _root, group_ids in fuzzy_groups.items():
        group_entities = [info_map[eid] for eid in group_ids]
        if len(group_entities) >= 2:
            proposals.append(_FuzzyProposal(entities=group_entities))
        else:
            unclustered.extend(group_entities)

    return proposals, unclustered


def _validate_groups_with_llm(
    groups: dict[str, list[str]],
    name_map: dict[str, str],
    entity_types: dict[str, str],
    context_map: dict[str, str],
    *,
    model: str | None = None,
    max_budget: float = 0.50,
    validate_prompt_template: str = "prompts/resolution/validate_merge.yaml",
) -> dict[str, list[str]]:
    """Validate candidate merge groups using LLM.

    For each group of 2+ entities, asks the LLM whether the merge should be
    confirmed. Confirmed groups are kept; rejected groups are split into
    singletons. Single-entity groups pass through unchanged.

    All LLM calls go through llm_client with task/trace_id/max_budget.
    """
    llm_mod = import_module("llm_client")
    render_prompt = llm_mod.render_prompt
    acall_llm = llm_mod.acall_llm

    if model is None:
        try:
            model = llm_mod.get_model("fast_extraction", use_performance=False)
        except Exception:
            model = "gemini/gemini-2.5-flash"

    schema = MergeValidation.model_json_schema()
    validated_groups: dict[str, list[str]] = {}
    group_counter = 0

    for _key, group_eids in groups.items():
        if len(group_eids) < 2:
            # Singletons pass through without LLM call
            validated_groups[f"singleton_{group_counter}"] = group_eids
            group_counter += 1
            continue

        # Determine entity type for the group (all should be same type)
        etypes = {entity_types.get(eid, "unknown") for eid in group_eids}
        entity_type = etypes.pop() if len(etypes) == 1 else "mixed"

        entities = [
            {"entity_id": eid, "name": name_map.get(eid, eid), "context": context_map.get(eid, "")}
            for eid in group_eids
        ]

        messages = render_prompt(
            validate_prompt_template,
            entity_type=entity_type,
            entities=entities,
        )

        trace_id = f"resolution.validate.{entity_type}.{_uuid.uuid4().hex[:8]}"

        result = asyncio.run(
            acall_llm(
                model,
                messages,
                task="entity_resolution_validation",
                trace_id=trace_id,
                max_budget=max_budget,
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "MergeValidation",
                        "schema": schema,
                    },
                },
            )
        )

        response_text = result.content if hasattr(result, "content") else str(result)
        validation = MergeValidation.model_validate_json(response_text)

        if validation.confirm:
            logger.info(
                "LLM confirmed merge of %d entities (type=%s): %s",
                len(group_eids), entity_type, validation.reasoning[:100],
            )
            validated_groups[f"confirmed_{group_counter}"] = group_eids
        else:
            logger.info(
                "LLM rejected merge of %d entities (type=%s): %s",
                len(group_eids), entity_type, validation.reasoning[:100],
            )
            # Split into singletons
            for eid in group_eids:
                validated_groups[f"rejected_{group_counter}"] = [eid]
                group_counter += 1

        group_counter += 1

    return validated_groups


def _group_by_llm(
    entity_ids: list[str],
    name_map: dict[str, str],
    entity_types: dict[str, str],
    context_map: dict[str, str],
    assertions: list[PromotedGraphAssertionRecord],
    *,
    model: str | None = None,
    max_budget: float = 0.50,
    prompt_template: str = "prompts/resolution/cluster_entities.yaml",
    fuzzy_pre_filter_threshold: int = 80,
    batch_token_limit: int = 50000,
    min_entities_for_llm: int = 2,
) -> dict[str, list[str]]:
    """Group entities using LLM-based clustering with optional fuzzy pre-filter.

    For each entity type:
    1. If type has >=50 entities: run fuzzy pre-filter, send proposals to LLM
    2. If type has <50 entities: send all directly to LLM
    3. LLM validates/rejects fuzzy proposals and identifies additional clusters

    All LLM calls go through llm_client with task/trace_id/max_budget.
    """
    try:
        llm_mod = import_module("llm_client")
        render_prompt = llm_mod.render_prompt
        acall_llm = llm_mod.acall_llm
    except ImportError as exc:
        raise RuntimeError(
            "llm_client is required for LLM resolution strategy; "
            "run `pip install -e ~/projects/llm_client`"
        ) from exc

    if model is None:
        try:
            get_model = llm_mod.get_model
            model = get_model("fast_extraction", use_performance=False)
        except Exception:
            model = "gemini/gemini-2.5-flash"

    # Group entities by type
    type_groups: dict[str, list[str]] = defaultdict(list)
    for eid in entity_ids:
        etype = entity_types.get(eid, "unknown")
        type_groups[etype].append(eid)

    all_groups: dict[str, list[str]] = {}
    group_counter = 0

    for entity_type, type_eids in type_groups.items():
        if len(type_eids) < min_entities_for_llm:
            # Single entity — no clustering needed
            for eid in type_eids:
                all_groups[f"singleton_{group_counter}"] = [eid]
                group_counter += 1
            continue

        entities = _build_entity_info_list(type_eids, name_map, entity_types, context_map)

        # Decide: fuzzy pre-filter or direct LLM
        use_fuzzy_prefilter = len(entities) >= 50
        fuzzy_proposals: list[_FuzzyProposal] | None = None
        unclustered: list[_EntityInfo] | None = None

        if use_fuzzy_prefilter:
            fuzzy_proposals, unclustered = _fuzzy_pre_filter(
                entities, fuzzy_pre_filter_threshold
            )

        # Build prompt context
        prompt_context: dict[str, Any] = {"entity_type": entity_type}

        if fuzzy_proposals is not None and unclustered is not None:
            prompt_context["fuzzy_proposals"] = [
                {
                    "entities": [
                        {"entity_id": e.entity_id, "name": e.name, "context": e.context}
                        for e in p.entities
                    ]
                }
                for p in fuzzy_proposals
            ]
            prompt_context["unclustered_entities"] = [
                {"entity_id": e.entity_id, "name": e.name, "context": e.context}
                for e in unclustered
            ]
        else:
            prompt_context["entities"] = [
                {"entity_id": e.entity_id, "name": e.name, "context": e.context}
                for e in entities
            ]

        # Render prompt — fail loud if template is broken
        messages = render_prompt(prompt_template, **prompt_context)

        # Call LLM
        trace_id = f"resolution.cluster.{entity_type}.{_uuid.uuid4().hex[:8]}"
        schema = ClusteringResult.model_json_schema()

        # Call LLM — fail loud on errors
        result = asyncio.run(
            acall_llm(
                model,
                messages,
                task="entity_resolution",
                trace_id=trace_id,
                max_budget=max_budget,
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "ClusteringResult",
                        "schema": schema,
                    },
                },
            )
        )

        # Parse LLM response — fail loud on parse errors
        response_text = result.content if hasattr(result, "content") else str(result)
        clustering = ClusteringResult.model_validate_json(response_text)

        logger.info(
            "LLM clustering for type %s: %d entities → %d clusters "
            "(entity_count=%d, trace=%s)",
            entity_type, len(type_eids), len(clustering.clusters),
            len(type_eids), trace_id,
        )

        # Convert LLM clusters to groups
        claimed_ids: set[str] = set()
        valid_eids = set(type_eids)

        for cluster in clustering.clusters:
            # Filter to only entity IDs that are actually in this type group
            valid_cluster_ids = [
                eid for eid in cluster.entity_ids
                if eid in valid_eids and eid not in claimed_ids
            ]
            if valid_cluster_ids:
                all_groups[f"llm_{group_counter}"] = valid_cluster_ids
                claimed_ids.update(valid_cluster_ids)
                group_counter += 1

        # Any entities not claimed by LLM clusters get singleton groups
        for eid in type_eids:
            if eid not in claimed_ids:
                all_groups[f"unclaimed_{group_counter}"] = [eid]
                group_counter += 1

    return all_groups


__all__ = [
    "ClusteringResult",
    "EntityCluster",
    "ResolutionResult",
    "ResolutionStrategy",
    "auto_resolve_identities",
]

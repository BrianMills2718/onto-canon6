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
import logging
import re
import uuid as _uuid
from collections import defaultdict
from dataclasses import dataclass
from importlib import import_module
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from .graph_models import PromotedGraphAssertionRecord
from .graph_service import CanonicalGraphService
from .identity_service import IdentityConflictError, IdentityService

logger = logging.getLogger(__name__)

ResolutionStrategy = Literal["exact", "fuzzy", "llm"]

ACTOR_ID = "auto:resolution"
DEFAULT_FUZZY_THRESHOLD = 85
_ORGANIZATION_TYPE_SLUGS = {
    "org",
    "organization",
    "military_organization",
    "military_organization_unit",
    "government_organization",
    "government_agency",
    "intelligence_agency",
    "educational_institution",
    "university",
    "civilian_organization",
    "combatant_command",
    "unit",
}
_PLACE_TYPE_SLUGS = {
    "location",
    "place",
    "city",
    "installation",
    "military_installation",
    "military_base",
    "base",
    "facility",
}
_PERSON_TYPE_SLUGS = {"person", "gp_person"}
_PERSON_LIKE_RANK_TYPE_SLUGS = {"military_rank"}
_INSTALLATION_NAME_PREFIXES = (
    "fort ",
    "ft ",
    "camp ",
    "base ",
    "station ",
)
_GENERIC_TYPE_SLUGS = {"entity", "unknown"}
_ORGANIZATION_NAME_HINTS = {
    "agency",
    "bureau",
    "center",
    "centre",
    "command",
    "commands",
    "committee",
    "department",
    "directorate",
    "division",
    "group",
    "groups",
    "headquarters",
    "office",
    "organization",
    "university",
    "unit",
    "units",
}
_INSTALLATION_EQUIVALENCE_GROUPS = (
    frozenset({"fort bragg", "ft bragg", "fort liberty"}),
)
_INSTALLATION_EQUIVALENCE_LOOKUP = {
    normalized_name: f"installation:{index}"
    for index, names in enumerate(_INSTALLATION_EQUIVALENCE_GROUPS, start=1)
    for normalized_name in names
}
_ALIAS_STOPWORDS = {
    "a",
    "an",
    "and",
    "at",
    "for",
    "from",
    "in",
    "of",
    "on",
    "the",
    "to",
    "with",
}
_COMPOUND_ACRONYM_PARTS = {
    ("special", "operations"): "so",
    ("psychological", "operations"): "po",
}
_WORD_ACRONYM_PARTS = {
    "agency": "a",
    "command": "com",
    "group": "g",
    "headquarters": "hq",
    "university": "u",
}

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


@dataclass(frozen=True)
class _PersonNameInfo:
    """Minimal person-name decomposition for conservative merge checks."""

    surname: str | None
    full_given: str | None
    initial: str | None
    surname_only: bool
    has_title: bool


@dataclass(frozen=True)
class _PersonGroupBridgeInfo:
    """Group-level bridge signals for conservative titled-person collapse."""

    surname: str | None
    full_given_names: frozenset[str]
    initials: frozenset[str]
    titled_full_given_names: frozenset[str]
    titled_initials: frozenset[str]
    has_titled_surname_only: bool


def auto_resolve_identities(
    *,
    db_path: Path,
    strategy: ResolutionStrategy = "exact",
    fuzzy_threshold: int = DEFAULT_FUZZY_THRESHOLD,
    model_override: str | None = None,
) -> ResolutionResult:
    """Run automated entity resolution over all promoted entities.

    Groups promoted entities by normalized display name and creates
    stable identities for each group. The first entity in each group
    becomes the canonical member; subsequent entities become aliases.

    For ``fuzzy`` strategy, entities with token_sort_ratio >= threshold
    AND a compatible resolution family are grouped together. The family guard
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

    if strategy == "llm":
        context_map = _build_context_map(assertions)
        # Load resolution config
        try:
            from ..config import get_config
            config = get_config()
            res_cfg = config.resolution
            groups = _group_by_llm(
                entity_ids, name_map, entity_types, context_map, assertions,
                model=(
                    model_override.strip()
                    if model_override is not None and model_override.strip()
                    else res_cfg.model_override
                ),
                max_budget=res_cfg.max_budget_usd,
                prompt_template=res_cfg.prompt_template,
                fuzzy_pre_filter_threshold=res_cfg.fuzzy_pre_filter_threshold,
                batch_token_limit=res_cfg.batch_token_limit,
                min_entities_for_llm=res_cfg.min_entities_for_llm,
            )
        except Exception:
            # Fall back to config-less defaults
            context_map = _build_context_map(assertions)
            groups = _group_by_llm(
                entity_ids, name_map, entity_types, context_map, assertions,
                model=(
                    model_override.strip()
                    if model_override is not None and model_override.strip()
                    else None
                ),
            )
    elif strategy == "fuzzy":
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
    2. They share a compatible resolution family (false-positive guard)

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
            if type_a and type_b and not _entity_types_compatible(
                type_a,
                type_b,
                left_name=name_map.get(eid_a, eid_a),
                right_name=name_map.get(eid_b, eid_b),
            ):
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
# LLM-based entity clustering (Phase 2)
# ---------------------------------------------------------------------------


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

    # Group entities by compatibility family so subtype-equivalent org and place
    # mentions can still be compared in one LLM call.
    type_groups: dict[str, list[str]] = defaultdict(list)
    for eid in entity_ids:
        etype = entity_types.get(eid, "unknown")
        type_groups[_entity_resolution_family(etype, name_map.get(eid, eid))].append(eid)

    all_groups: dict[str, list[str]] = {}
    group_counter = 0

    for entity_type_family, type_eids in type_groups.items():
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
        prompt_context: dict[str, Any] = {"entity_type_family": entity_type_family}

        if fuzzy_proposals is not None and unclustered is not None:
            prompt_context["fuzzy_proposals"] = [
                {
                    "entities": [
                        {
                            "entity_id": e.entity_id,
                            "name": e.name,
                            "entity_type": e.entity_type,
                            "context": e.context,
                        }
                        for e in p.entities
                    ]
                }
                for p in fuzzy_proposals
            ]
            prompt_context["unclustered_entities"] = [
                {
                    "entity_id": e.entity_id,
                    "name": e.name,
                    "entity_type": e.entity_type,
                    "context": e.context,
                }
                for e in unclustered
            ]
        else:
            prompt_context["entities"] = [
                {
                    "entity_id": e.entity_id,
                    "name": e.name,
                    "entity_type": e.entity_type,
                    "context": e.context,
                }
                for e in entities
            ]

        # Render prompt — fail loud if template is broken
        messages = render_prompt(prompt_template, **prompt_context)

        # Call LLM
        trace_id = (
            f"resolution.cluster.{entity_type_family}.{_uuid.uuid4().hex[:8]}"
        )
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
            "LLM clustering for family %s: %d entities → %d clusters "
            "(entity_count=%d, trace=%s)",
            entity_type_family, len(type_eids), len(clustering.clusters),
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
            if not valid_cluster_ids:
                continue
            for subgroup in _postprocess_llm_cluster(
                valid_cluster_ids,
                name_map=name_map,
                entity_types=entity_types,
            ):
                all_groups[f"llm_{group_counter}"] = subgroup
                claimed_ids.update(subgroup)
                group_counter += 1

        # Any entities not claimed by LLM clusters get singleton groups
        for eid in type_eids:
            if eid not in claimed_ids:
                all_groups[f"unclaimed_{group_counter}"] = [eid]
                group_counter += 1

    return _collapse_equivalent_llm_groups(
        all_groups,
        name_map=name_map,
        entity_types=entity_types,
    )


def _entity_type_slug(entity_type: str) -> str:
    """Return the normalized type slug without CURIE prefix."""

    normalized = entity_type.strip().lower()
    if not normalized:
        return "unknown"
    return normalized.split(":")[-1]


def _resolution_type_family(entity_type: str) -> str:
    """Map fine-grained entity types into conservative resolution families."""

    slug = _entity_type_slug(entity_type)
    if slug in _PERSON_TYPE_SLUGS:
        return "person"
    if slug in _ORGANIZATION_TYPE_SLUGS:
        return "organization"
    if slug in _PLACE_TYPE_SLUGS:
        return "place"
    return slug


def _entity_resolution_family(entity_type: str, name: str | None = None) -> str:
    """Return a conservative name-aware resolution family for one mention."""

    base_family = _resolution_type_family(entity_type)
    if not name or not name.strip():
        return base_family

    normalized_name = _normalize_name(name)
    if not normalized_name:
        return base_family

    slug = _entity_type_slug(entity_type)
    if slug in _PERSON_LIKE_RANK_TYPE_SLUGS and _looks_like_person_mention(normalized_name):
        return "person"
    if normalized_name.startswith(_INSTALLATION_NAME_PREFIXES):
        return "place"
    if slug in _GENERIC_TYPE_SLUGS and _looks_like_generic_person_name(name):
        return "person"
    if slug in _GENERIC_TYPE_SLUGS and _looks_like_organization_name(normalized_name):
        return "organization"
    return base_family


def _looks_like_organization_name(normalized_name: str) -> bool:
    """Return whether a normalized surface form carries strong organization signal."""

    tokens = [token for token in normalized_name.split() if token]
    if not tokens:
        return False
    if any(token in _ORGANIZATION_NAME_HINTS for token in tokens):
        return True
    return len(tokens) >= 2 and bool(_acronym_signatures(normalized_name))


def _has_leading_title(name: str) -> bool:
    """Return whether a raw surface form starts with a title or rank token."""

    normalized = " ".join(name.lower().split()).strip(" .,;:")
    normalized_no_punct = re.sub(r"[.,;:]+", "", normalized)
    if not normalized:
        return False
    for abbrev, _expansion in sorted(_TITLE_PATTERNS, key=lambda item: -len(item[0])):
        cleaned = abbrev.strip(" .,;:")
        if (
            normalized == cleaned
            or normalized.startswith(f"{cleaned} ")
            or normalized_no_punct == cleaned
            or normalized_no_punct.startswith(f"{cleaned} ")
        ):
            return True
    for title in sorted(_STRIP_TITLES, key=len, reverse=True):
        if (
            normalized == title
            or normalized.startswith(f"{title} ")
            or normalized_no_punct == title
            or normalized_no_punct.startswith(f"{title} ")
        ):
            return True
    return False


def _looks_like_generic_person_name(name: str) -> bool:
    """Return whether a generic surface form is strongly person-like."""

    normalized_name = _normalize_name(name)
    tokens = [
        token.strip(".,;:")
        for token in normalized_name.split()
        if token.strip(".,;:")
    ]
    if not tokens:
        return False
    if _has_leading_title(name):
        return all(token.isalpha() for token in tokens) and len(tokens) <= 3
    return len(tokens) == 2 and len(tokens[0]) == 1 and all(
        token.isalpha() for token in tokens
    )


def _installation_equivalence_key(name: str) -> str | None:
    """Return the bounded installation-equivalence key for one surface form."""

    tokens = _alias_signature_tokens(name)
    if not tokens:
        return None
    normalized = " ".join(tokens)
    return _INSTALLATION_EQUIVALENCE_LOOKUP.get(normalized)


def _looks_like_person_mention(normalized_name: str) -> bool:
    """Return whether a normalized name still looks like a person mention."""

    tokens = [token for token in normalized_name.split() if token]
    if not tokens:
        return False
    bare_rank_tokens = {
        "general",
        "lieutenant",
        "major",
        "colonel",
        "captain",
        "commander",
        "admiral",
        "sergeant",
        "corporal",
        "private",
    }
    return any(token not in bare_rank_tokens for token in tokens)


def _entity_types_compatible(
    left_type: str,
    right_type: str,
    *,
    left_name: str | None = None,
    right_name: str | None = None,
) -> bool:
    """Return whether two entity types are compatible for resolution."""

    if left_type == right_type:
        return True
    return _entity_resolution_family(left_type, left_name) == _entity_resolution_family(
        right_type,
        right_name,
    )


def _person_name_info(name: str) -> _PersonNameInfo:
    """Extract a conservative person-name signature for merge checks."""

    has_title = _has_leading_title(name)
    normalized = _normalize_name(name)
    if not normalized:
        return _PersonNameInfo(None, None, None, False, has_title)
    tokens = normalized.split()
    if not tokens:
        return _PersonNameInfo(None, None, None, False, has_title)
    surname = tokens[-1]
    given_tokens = tokens[:-1]
    if not given_tokens:
        return _PersonNameInfo(surname, None, None, True, has_title)
    given = given_tokens[0].strip(".,;:")
    if len(given) == 1:
        return _PersonNameInfo(surname, None, given, False, has_title)
    return _PersonNameInfo(surname, given, given[0], False, has_title)


def _person_group_bridge_info(
    group_ids: list[str],
    *,
    name_map: dict[str, str],
) -> _PersonGroupBridgeInfo | None:
    """Summarize one candidate person group for titled-mention bridge logic."""

    surnames: set[str] = set()
    full_given_names: set[str] = set()
    initials: set[str] = set()
    titled_full_given_names: set[str] = set()
    titled_initials: set[str] = set()
    has_titled_surname_only = False

    for entity_id in group_ids:
        info = _person_name_info(name_map.get(entity_id, entity_id))
        if info.surname is None:
            continue
        surnames.add(info.surname)
        if info.full_given is not None:
            full_given_names.add(info.full_given)
            initials.add(info.full_given[0])
        elif info.initial is not None:
            initials.add(info.initial)
        if not info.has_title:
            continue
        if info.full_given is not None:
            titled_full_given_names.add(info.full_given)
            titled_initials.add(info.full_given[0])
            continue
        if info.initial is not None:
            titled_initials.add(info.initial)
            continue
        if info.surname_only:
            has_titled_surname_only = True

    if len(surnames) != 1:
        return None

    return _PersonGroupBridgeInfo(
        surname=next(iter(surnames)),
        full_given_names=frozenset(sorted(full_given_names)),
        initials=frozenset(sorted(initials)),
        titled_full_given_names=frozenset(sorted(titled_full_given_names)),
        titled_initials=frozenset(sorted(titled_initials)),
        has_titled_surname_only=has_titled_surname_only,
    )


def _postprocess_llm_cluster(
    entity_ids: list[str],
    *,
    name_map: dict[str, str],
    entity_types: dict[str, str],
) -> list[list[str]]:
    """Apply deterministic safety guards to one LLM-proposed cluster."""

    if len(entity_ids) < 2:
        return [entity_ids]

    representative_type = entity_types.get(entity_ids[0], "")
    if _resolution_type_family(representative_type) != "person":
        return [entity_ids]

    infos = {
        eid: _person_name_info(name_map.get(eid, eid))
        for eid in entity_ids
    }
    surname_groups: dict[str, list[str]] = defaultdict(list)
    for eid, info in infos.items():
        surname_groups[info.surname or eid].append(eid)

    output_groups: list[list[str]] = []
    for group_ids in surname_groups.values():
        full_given_names: set[str] = set()
        for eid in group_ids:
            full_given = infos[eid].full_given
            if full_given is not None:
                full_given_names.add(full_given)
        if len(full_given_names) <= 1:
            output_groups.append(group_ids)
            continue

        anchored_groups: dict[str, list[str]] = {
            given_name: []
            for given_name in sorted(full_given_names)
        }
        ambiguous_ids: list[str] = []
        for eid in group_ids:
            info = infos[eid]
            if info.full_given is not None:
                anchored_groups[info.full_given].append(eid)
                continue
            if info.initial is not None:
                matching_full = [
                    given_name
                    for given_name in anchored_groups
                    if given_name.startswith(info.initial)
                ]
                if len(matching_full) == 1:
                    anchored_groups[matching_full[0]].append(eid)
                    continue
            ambiguous_ids.append(eid)

        output_groups.extend(
            [members for members in anchored_groups.values() if members]
        )
        output_groups.extend([[eid] for eid in ambiguous_ids])

    return output_groups


def _alias_signature_tokens(name: str) -> list[str]:
    """Tokenize one surface form for conservative alias-signature generation."""

    normalized = name.strip().lower()
    if not normalized:
        return []
    normalized = normalized.replace("u.s.", "us")
    normalized = re.sub(r"\bu\.s\b", "us", normalized)
    normalized = re.sub(r"'s\b.*", "", normalized)
    normalized = re.sub(r"[^a-z0-9]+", " ", normalized)
    return [
        token
        for token in normalized.split()
        if token and token not in _ALIAS_STOPWORDS
    ]


def _acronym_signatures(name: str) -> set[str]:
    """Return high-confidence acronym signatures for organization-like names."""

    tokens = _alias_signature_tokens(name)
    if not tokens:
        return set()
    if len(tokens) == 1 and len(tokens[0]) >= 2:
        compact = tokens[0]
        signatures = {compact}
        if compact.startswith("us") and len(compact) > 2:
            signatures.add(compact[2:])
        return signatures

    parts: list[str] = []
    index = 0
    while index < len(tokens):
        if index + 1 < len(tokens):
            compound = _COMPOUND_ACRONYM_PARTS.get((tokens[index], tokens[index + 1]))
            if compound is not None:
                parts.append(compound)
                index += 2
                continue
        token = tokens[index]
        if token == "us":
            parts.append("us")
        elif token in _WORD_ACRONYM_PARTS:
            parts.append(_WORD_ACRONYM_PARTS[token])
        elif token[0].isdigit():
            parts.append(token)
        else:
            parts.append(token[0])
        index += 1

    compact = "".join(parts)
    if not compact:
        return set()
    signatures = {compact}
    if compact.startswith("us") and len(compact) > 2:
        signatures.add(compact[2:])
    return signatures


def _group_alias_signatures(
    group_ids: list[str],
    *,
    name_map: dict[str, str],
    entity_types: dict[str, str],
) -> set[str]:
    """Return deterministic merge signatures for one candidate cluster."""

    if not group_ids:
        return set()
    representative_type = entity_types.get(group_ids[0], "")
    family = _entity_resolution_family(
        representative_type,
        name_map.get(group_ids[0], group_ids[0]),
    )
    signatures: set[str] = set()
    for entity_id in group_ids:
        observed_name = name_map.get(entity_id, entity_id)
        if family == "person":
            info = _person_name_info(observed_name)
            if info.full_given is not None and info.surname is not None:
                signatures.add(f"person:{info.full_given}:{info.surname}")
            continue
        normalized = _normalize_name(observed_name)
        if normalized:
            signatures.add(f"norm:{normalized}")
            installation_equivalence = _installation_equivalence_key(observed_name)
            if installation_equivalence is not None:
                signatures.add(installation_equivalence)
        for acronym in _acronym_signatures(observed_name):
            signatures.add(f"acr:{acronym}")
    return signatures


def _collapse_equivalent_llm_groups(
    groups: dict[str, list[str]],
    *,
    name_map: dict[str, str],
    entity_types: dict[str, str],
) -> dict[str, list[str]]:
    """Merge LLM output groups that share high-confidence alias signatures."""

    keys = list(groups.keys())
    if len(keys) < 2:
        return groups

    signatures_by_key = {
        key: _group_alias_signatures(
            groups[key],
            name_map=name_map,
            entity_types=entity_types,
        )
        for key in keys
    }

    parent: dict[str, str] = {key: key for key in keys}

    def find(key: str) -> str:
        while parent[key] != key:
            parent[key] = parent[parent[key]]
            key = parent[key]
        return key

    def union(left: str, right: str) -> None:
        root_left = find(left)
        root_right = find(right)
        if root_left != root_right:
            parent[root_right] = root_left

    for index, left in enumerate(keys):
        left_group = groups[left]
        left_type = entity_types.get(left_group[0], "") if left_group else ""
        left_family = _entity_resolution_family(
            left_type,
            name_map.get(left_group[0], left_group[0]) if left_group else None,
        )
        left_signatures = signatures_by_key[left]
        if not left_signatures:
            continue
        for right in keys[index + 1:]:
            right_group = groups[right]
            right_type = entity_types.get(right_group[0], "") if right_group else ""
            if left_family != _entity_resolution_family(
                right_type,
                name_map.get(right_group[0], right_group[0]) if right_group else None,
            ):
                continue
            if left_signatures & signatures_by_key[right]:
                union(left, right)

    person_bridge_info_by_key: dict[str, _PersonGroupBridgeInfo] = {}
    person_keys_by_surname: dict[str, list[str]] = defaultdict(list)
    for key in keys:
        group = groups[key]
        if not group:
            continue
        representative_name = name_map.get(group[0], group[0])
        if _entity_resolution_family(entity_types.get(group[0], ""), representative_name) != "person":
            continue
        bridge_info = _person_group_bridge_info(group, name_map=name_map)
        if bridge_info is None or bridge_info.surname is None:
            continue
        person_bridge_info_by_key[key] = bridge_info
        person_keys_by_surname[bridge_info.surname].append(key)

    for surname_keys in person_keys_by_surname.values():
        titled_full_keys = [
            key
            for key in surname_keys
            if person_bridge_info_by_key[key].titled_full_given_names
        ]
        initial_only_keys = [
            key
            for key in surname_keys
            if (
                person_bridge_info_by_key[key].titled_initials
                and not person_bridge_info_by_key[key].titled_full_given_names
            )
        ]
        surname_only_keys = [
            key
            for key in surname_keys
            if person_bridge_info_by_key[key].has_titled_surname_only
        ]

        for initial_key in initial_only_keys:
            initials = person_bridge_info_by_key[initial_key].titled_initials
            candidates = [
                full_key
                for full_key in titled_full_keys
                if initials
                & {
                    given_name[0]
                    for given_name in person_bridge_info_by_key[full_key].titled_full_given_names
                }
            ]
            if len(candidates) == 1:
                union(initial_key, candidates[0])

        titled_full_roots = {find(key) for key in titled_full_keys}
        if len(titled_full_roots) != 1:
            continue
        for surname_only_key in surname_only_keys:
            bridge_info = person_bridge_info_by_key[surname_only_key]
            anchor_candidates = titled_full_keys
            if bridge_info.full_given_names:
                anchor_candidates = [
                    full_key
                    for full_key in anchor_candidates
                    if bridge_info.full_given_names
                    & person_bridge_info_by_key[full_key].titled_full_given_names
                ]
            elif bridge_info.initials:
                anchor_candidates = [
                    full_key
                    for full_key in anchor_candidates
                    if bridge_info.initials
                    & person_bridge_info_by_key[full_key].titled_initials
                ]
            if len(anchor_candidates) == 1:
                union(surname_only_key, anchor_candidates[0])

    collapsed: dict[str, list[str]] = defaultdict(list)
    for key in keys:
        collapsed[find(key)].extend(groups[key])
    return dict(collapsed)


__all__ = [
    "ClusteringResult",
    "EntityCluster",
    "ResolutionResult",
    "ResolutionStrategy",
    "_acronym_signatures",
    "_entity_types_compatible",
    "_postprocess_llm_cluster",
    "_resolution_type_family",
    "auto_resolve_identities",
]

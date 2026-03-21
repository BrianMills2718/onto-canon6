"""Progressive disclosure extraction — Passes 1, 2, 3, and orchestrator.

Pass 1 (Slice B): open extraction with SUMO seeding. Extracts entities and
relationships from raw text, assigning coarse SUMO types from the ~50
top-level type list.

Pass 2 (Slice C): predicate mapping with early exit. For each triple from
Pass 1, normalizes the relationship verb to a lemma, looks it up in the
Predicate Canon, and either maps it deterministically (single-sense, ~78%
of cases) or calls an LLM to disambiguate among multiple senses.

Pass 3 (Slice D): entity refinement with narrowed SUMO subtree. For each
mapped assertion, refines entity types by intersecting the coarse type's
descendants with the role constraint from the predicate canon.  Leaf types
bypass the LLM entirely.

Orchestrator (Slice E): ``run_progressive_extraction()`` chains the three
passes sequentially, opening SUMOHierarchy and PredicateCanon internally,
splitting the budget across passes, and aggregating results into a
``ProgressiveExtractionReport``.

All LLM calls go through ``llm_client`` with mandatory ``task=``,
``trace_id=``, and ``max_budget=`` kwargs. Prompt templates are YAML/Jinja2
files loaded via ``llm_client.render_prompt()``. No f-string prompts in Python.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import uuid as _uuid
from dataclasses import dataclass
from importlib import import_module
from pathlib import Path
from typing import Any, Protocol, cast

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from onto_canon6.evaluation.fidelity_experiment import TOP_LEVEL_TYPES

from onto_canon6.evaluation.predicate_canon import PredicateCanon, PredicateMatch
from onto_canon6.evaluation.sumo_hierarchy import SUMOHierarchy

from .progressive_types import (
    EntityRefinement,
    Pass1Entity,
    Pass1Result,
    Pass1Triple,
    Pass2MappedAssertion,
    Pass2Result,
    Pass3Result,
    Pass3TypedAssertion,
    ProgressiveExtractionReport,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# llm_client API boundary (lazy loaded, testable via _load_llm_client_api)
# ---------------------------------------------------------------------------


class _RenderPrompt(Protocol):
    """Callable signature for ``llm_client.render_prompt``."""

    def __call__(
        self, template_path: str, **context: Any
    ) -> list[dict[str, str]]: ...


class _ACallLLM(Protocol):
    """Callable signature for ``llm_client.acall_llm``."""

    async def __call__(
        self, model: str, messages: list[dict[str, Any]], **kwargs: Any
    ) -> Any: ...


@dataclass(frozen=True)
class _LLMClientAPI:
    """Typed view of the llm_client APIs used by this module."""

    render_prompt: _RenderPrompt
    acall_llm: _ACallLLM


def _load_llm_client_api() -> _LLMClientAPI:
    """Lazily import llm_client and return a typed API handle.

    Raises ``ConfigError`` (via import chain) if llm_client is not installed.
    """
    module = import_module("llm_client")
    return _LLMClientAPI(
        render_prompt=cast(_RenderPrompt, getattr(module, "render_prompt")),
        acall_llm=cast(_ACallLLM, getattr(module, "acall_llm")),
    )


# ---------------------------------------------------------------------------
# Internal response model for structured output parsing
# ---------------------------------------------------------------------------

_PASS1_PROMPT_TEMPLATE = "prompts/extraction/pass1_open_extraction.yaml"
_DEFAULT_MODEL = "gemini/gemini-2.5-flash-lite"


class _RawEntity(BaseModel):
    """Permissive entity shape returned by the LLM.

    Allows missing or empty fields so partial extraction results are not
    discarded at the parse boundary.
    """

    model_config = ConfigDict(extra="ignore")

    name: str = ""
    coarse_type: str = ""
    context: str = ""


class _RawTriple(BaseModel):
    """Permissive triple shape returned by the LLM.

    Uses ``extra="ignore"`` so unexpected keys do not crash parsing.
    Missing entities are represented as empty ``_RawEntity`` instances.
    """

    model_config = ConfigDict(extra="ignore")

    entity_a: _RawEntity = Field(default_factory=_RawEntity)
    entity_b: _RawEntity = Field(default_factory=_RawEntity)
    relationship_verb: str = ""
    evidence_span: str = ""
    confidence: float = 0.5


class _RawPass1Response(BaseModel):
    """Top-level shape of the LLM's JSON response for Pass 1.

    Intentionally permissive (``extra="ignore"``) so that unexpected
    top-level keys do not abort parsing.
    """

    model_config = ConfigDict(extra="ignore")

    triples: list[_RawTriple] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _hash_text(text: str) -> str:
    """Return a stable ``sha256:<hex>`` hash of *text*."""
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def _render_type_list() -> str:
    """Format TOP_LEVEL_TYPES as a bulleted list for the prompt template."""
    return "\n".join(f"- {t}" for t in TOP_LEVEL_TYPES)


def _coerce_triple(raw: _RawTriple) -> Pass1Triple | None:
    """Convert a permissive raw triple into a strict Pass1Triple.

    Returns ``None`` when the triple is too incomplete to be useful
    (e.g. missing entity names or relationship verb).
    """
    if not raw.entity_a.name.strip() or not raw.entity_b.name.strip():
        return None
    if not raw.relationship_verb.strip():
        return None

    confidence = max(0.0, min(1.0, raw.confidence))
    try:
        return Pass1Triple(
            entity_a=Pass1Entity(
                name=raw.entity_a.name.strip(),
                coarse_type=raw.entity_a.coarse_type.strip() or "Entity",
                context=raw.entity_a.context.strip(),
            ),
            entity_b=Pass1Entity(
                name=raw.entity_b.name.strip(),
                coarse_type=raw.entity_b.coarse_type.strip() or "Entity",
                context=raw.entity_b.context.strip(),
            ),
            relationship_verb=raw.relationship_verb.strip(),
            evidence_span=raw.evidence_span.strip(),
            confidence=confidence,
        )
    except ValidationError:
        logger.warning("Failed to validate triple: %s", raw, exc_info=True)
        return None


def _deduplicate_entities(triples: list[Pass1Triple]) -> list[Pass1Entity]:
    """Collect a deduplicated entity list from extracted triples.

    Deduplication is by (name, coarse_type). When the same entity name
    appears with different coarse types, both entries are kept since they
    represent genuinely different classifications.
    """
    seen: dict[tuple[str, str], Pass1Entity] = {}
    for triple in triples:
        for entity in (triple.entity_a, triple.entity_b):
            key = (entity.name, entity.coarse_type)
            if key not in seen:
                seen[key] = entity
    return list(seen.values())


def _parse_llm_response(raw_content: str) -> list[Pass1Triple]:
    """Parse the LLM's raw text response into a list of Pass1Triple.

    Attempts structured JSON parsing first.  On failure, logs the error
    and returns an empty list rather than crashing.
    """
    content = raw_content.strip()

    # Strip markdown code fences if present
    if content.startswith("```"):
        lines = content.splitlines()
        # Remove first and last fence lines
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        content = "\n".join(lines)

    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        logger.error("Pass 1 LLM response is not valid JSON: %.200s", content)
        return []

    if not isinstance(data, dict):
        logger.error("Pass 1 LLM response is not a JSON object: %s", type(data).__name__)
        return []

    try:
        raw_response = _RawPass1Response.model_validate(data)
    except ValidationError:
        logger.error("Pass 1 LLM response failed schema validation", exc_info=True)
        return []

    triples: list[Pass1Triple] = []
    for raw_triple in raw_response.triples:
        coerced = _coerce_triple(raw_triple)
        if coerced is not None:
            triples.append(coerced)

    return triples


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def run_pass1(
    text: str,
    *,
    model: str | None = None,
    task: str = "progressive_extraction",
    trace_id: str,
    max_budget: float = 0.10,
    max_triples: int = 50,
    _llm_api: _LLMClientAPI | None = None,
) -> Pass1Result:
    """Run Pass 1: open extraction with top-level SUMO seeding.

    Extracts entities and relationships from *text*, assigning coarse
    SUMO types from the ~50 top-level list.  Returns structured triples
    with evidence spans.

    All LLM calls go through ``llm_client`` with the mandatory kwargs.

    Parameters
    ----------
    text:
        The source text to extract from.
    model:
        LLM model identifier.  Defaults to ``gemini/gemini-2.5-flash-lite``.
    task:
        Task tag for ``llm_client`` observability.
    trace_id:
        Trace ID for ``llm_client`` observability.
    max_budget:
        Maximum spend in USD for this extraction call.
    max_triples:
        Soft limit on the number of triples the LLM should extract.
        Passed to the prompt template as guidance.
    _llm_api:
        Override for the llm_client API handle (testing only).

    Returns
    -------
    Pass1Result with extracted triples, deduplicated entities, and
    provenance metadata.

    Raises
    ------
    Does not raise on LLM or parse failures — returns a Pass1Result
    with empty triples and entities instead, logging the error.
    """
    api = _llm_api or _load_llm_client_api()
    effective_model = model or _DEFAULT_MODEL
    source_hash = _hash_text(text)

    # Render the prompt template
    type_list_str = _render_type_list()
    template_vars: dict[str, Any] = {
        "text": text,
        "type_list": type_list_str,
        "max_triples": max_triples,
    }
    messages = api.render_prompt(
        _PASS1_PROMPT_TEMPLATE,
        **template_vars,
    )

    # Call the LLM
    cost = 0.0
    try:
        result = await api.acall_llm(
            effective_model,
            messages,
            task=task,
            trace_id=trace_id,
            max_budget=max_budget,
            response_format={"type": "json_object"},
        )
        cost = result.cost or 0.0
        raw_content: str = result.content or ""
    except Exception:
        logger.error(
            "Pass 1 LLM call failed for trace_id=%s",
            trace_id,
            exc_info=True,
        )
        return Pass1Result(
            triples=[],
            entities=[],
            source_text_hash=source_hash,
            model=effective_model,
            cost=0.0,
            trace_id=trace_id,
        )

    # Parse and validate
    triples = _parse_llm_response(raw_content)
    entities = _deduplicate_entities(triples)

    logger.info(
        "Pass 1 extracted %d triples, %d unique entities (trace_id=%s, cost=$%.4f)",
        len(triples),
        len(entities),
        trace_id,
        cost,
    )

    return Pass1Result(
        triples=triples,
        entities=entities,
        source_text_hash=source_hash,
        model=effective_model,
        cost=cost,
        trace_id=trace_id,
    )


def run_pass1_sync(
    text: str,
    *,
    model: str | None = None,
    task: str = "progressive_extraction",
    trace_id: str,
    max_budget: float = 0.10,
    max_triples: int = 50,
    _llm_api: _LLMClientAPI | None = None,
) -> Pass1Result:
    """Synchronous wrapper for :func:`run_pass1`.

    Runs the async implementation in a new event loop.  Prefer the async
    version when an event loop is already running.
    """
    return asyncio.run(
        run_pass1(
            text,
            model=model,
            task=task,
            trace_id=trace_id,
            max_budget=max_budget,
            max_triples=max_triples,
            _llm_api=_llm_api,
        )
    )


# ---------------------------------------------------------------------------
# Pass 2: Predicate Mapping
# ---------------------------------------------------------------------------

_PASS2_PROMPT_TEMPLATE = "prompts/extraction/pass2_predicate_disambiguation.yaml"

# Common English verb suffixes for basic lemmatization.  Tried in order;
# the first match that produces a hit in the Predicate Canon wins.
_VERB_SUFFIXES: list[str] = ["ing", "ed", "es", "s"]


def _normalize_lemma(verb: str) -> list[str]:
    """Produce candidate lemma forms for a raw relationship verb.

    Returns a list of candidate strings to try against the Predicate Canon,
    from most specific (raw lowered) to most general (suffix-stripped).
    This is intentionally simple — a basic approach that handles common
    English verb inflections without pulling in a full NLP dependency.

    For "ed" and "ing" suffixes, also tries adding back a trailing 'e'
    since English frequently drops it (e.g. "abated" -> "abat" -> "abate",
    "used" -> "us" -> "use").
    """
    base = verb.lower().strip()
    candidates = [base]
    seen = {base}
    for suffix in _VERB_SUFFIXES:
        if base.endswith(suffix) and len(base) > len(suffix) + 1:
            stripped = base[: -len(suffix)]
            if stripped not in seen:
                candidates.append(stripped)
                seen.add(stripped)
            # For -ed and -ing, also try with trailing 'e' restored
            if suffix in ("ed", "ing"):
                with_e = stripped + "e"
                if with_e not in seen:
                    candidates.append(with_e)
                    seen.add(with_e)
    return candidates


def _render_candidates_for_prompt(
    matches: list[PredicateMatch],
) -> list[dict[str, Any]]:
    """Convert PredicateMatch objects into dicts suitable for the Jinja2 template.

    Each dict contains the predicate metadata and a list of role slot dicts
    so the template can render them without importing Pydantic models.
    """
    result: list[dict[str, Any]] = []
    for m in matches:
        result.append(
            {
                "predicate_id": m.predicate_id,
                "propbank_sense_id": m.propbank_sense_id or "",
                "description": m.description or "",
                "process_type": m.process_type or "",
                "role_slots": [
                    {
                        "arg_position": s.arg_position,
                        "named_label": s.named_label,
                        "type_constraint": s.type_constraint,
                        "required": s.required,
                    }
                    for s in m.role_slots
                ],
            }
        )
    return result


def _build_single_sense_assertion(
    triple: Pass1Triple,
    match: PredicateMatch,
) -> Pass2MappedAssertion:
    """Build a Pass2MappedAssertion for a single-sense deterministic mapping.

    Uses the default heuristic: ARG0 -> entity_a (the agent/performer),
    ARG1 -> entity_b (the patient/theme).  Only maps roles that exist in the
    predicate's role schema.
    """
    role_mapping: dict[str, str] = {}
    arg_positions = {s.arg_position for s in match.role_slots}
    if "ARG0" in arg_positions:
        role_mapping["ARG0"] = triple.entity_a.name
    if "ARG1" in arg_positions:
        role_mapping["ARG1"] = triple.entity_b.name

    return Pass2MappedAssertion(
        triple=triple,
        predicate_id=match.predicate_id,
        propbank_sense_id=match.propbank_sense_id or "",
        process_type=match.process_type or "",
        mapped_roles=role_mapping,
        disambiguation_method="single_sense",
        mapping_confidence=match.mapping_confidence or 0.5,
    )


def _strip_markdown_fences(content: str) -> str:
    """Remove markdown code fences from LLM output if present."""
    stripped = content.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        return "\n".join(lines)
    return stripped


def _parse_disambiguation_response(
    raw_content: str,
    candidates: list[PredicateMatch],
    triple: Pass1Triple,
) -> Pass2MappedAssertion | None:
    """Parse the LLM disambiguation response into a Pass2MappedAssertion.

    Returns ``None`` if the response cannot be parsed or references an
    unknown predicate_id.  Fails loud via logging, does not crash.
    """
    content = _strip_markdown_fences(raw_content)

    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        logger.error("Pass 2 disambiguation response is not valid JSON: %.200s", content)
        return None

    if not isinstance(data, dict):
        logger.error(
            "Pass 2 disambiguation response is not a JSON object: %s",
            type(data).__name__,
        )
        return None

    predicate_id = data.get("predicate_id")
    role_mapping_raw = data.get("role_mapping")

    if not isinstance(predicate_id, str) or not predicate_id:
        logger.error("Pass 2 disambiguation response missing or empty predicate_id")
        return None

    # Verify the chosen predicate is among the candidates
    candidate_map = {m.predicate_id: m for m in candidates}
    chosen = candidate_map.get(predicate_id)
    if chosen is None:
        logger.error(
            "Pass 2 LLM chose predicate_id '%s' which is not among the candidates",
            predicate_id,
        )
        return None

    # Parse role mapping — must be a dict of string->string
    mapped_roles: dict[str, str] = {}
    if isinstance(role_mapping_raw, dict):
        for k, v in role_mapping_raw.items():
            if isinstance(k, str) and isinstance(v, str):
                mapped_roles[k] = v

    return Pass2MappedAssertion(
        triple=triple,
        predicate_id=chosen.predicate_id,
        propbank_sense_id=chosen.propbank_sense_id or "",
        process_type=chosen.process_type or "",
        mapped_roles=mapped_roles,
        disambiguation_method="llm_pick",
        mapping_confidence=chosen.mapping_confidence or 0.5,
    )


def _lookup_lemma(
    verb: str,
    predicate_canon: PredicateCanon,
) -> list[PredicateMatch]:
    """Try normalized lemma candidates against the Predicate Canon.

    Returns the matches from the first candidate that produces a non-empty
    result, or an empty list if no candidate matches.
    """
    for candidate in _normalize_lemma(verb):
        matches = predicate_canon.lookup_by_lemma(candidate)
        if matches:
            return matches
    return []


async def run_pass2(
    pass1_result: Pass1Result,
    *,
    predicate_canon: PredicateCanon,
    model: str | None = None,
    task: str = "progressive_extraction",
    trace_id: str,
    max_budget: float = 0.10,
    _llm_api: _LLMClientAPI | None = None,
) -> Pass2Result:
    """Run Pass 2: predicate mapping with early exit for single-sense lemmas.

    For each triple in *pass1_result*:

    1. Normalize ``relationship_verb`` to candidate lemma forms (lowercased,
       basic suffix stripping).
    2. Look up each candidate in the Predicate Canon until a match is found.
    3. If exactly one sense: map deterministically (no LLM call).
    4. If multiple senses: call LLM with candidate descriptions to disambiguate.
    5. If no match: mark as unresolved.

    The single-sense early exit handles ~78% of cases, keeping costs low.

    Parameters
    ----------
    pass1_result:
        The Pass 1 extraction result to map.
    predicate_canon:
        An already-opened PredicateCanon instance (caller manages lifecycle).
    model:
        LLM model identifier for disambiguation calls.  Defaults to
        ``gemini/gemini-2.5-flash-lite``.
    task:
        Task tag for ``llm_client`` observability.
    trace_id:
        Trace ID for ``llm_client`` observability.
    max_budget:
        Maximum spend in USD for all disambiguation calls in this pass.
    _llm_api:
        Override for the llm_client API handle (testing only).

    Returns
    -------
    Pass2Result with mapped assertions, unresolved triples, and diagnostic
    counts for each disambiguation path.
    """
    api = _llm_api or _load_llm_client_api()
    effective_model = model or _DEFAULT_MODEL

    mapped: list[Pass2MappedAssertion] = []
    unresolved: list[Pass1Triple] = []
    total_cost = 0.0
    single_sense_count = 0
    llm_disambiguated_count = 0
    unresolved_count = 0

    for triple in pass1_result.triples:
        matches = _lookup_lemma(triple.relationship_verb, predicate_canon)

        if not matches:
            # No predicate found — store permissively as unresolved
            logger.info(
                "Pass 2 unresolved: verb '%s' has no predicate match (trace_id=%s)",
                triple.relationship_verb,
                trace_id,
            )
            unresolved.append(triple)
            unresolved_count += 1
            continue

        if len(matches) == 1:
            # Single sense — deterministic mapping, no LLM call
            assertion = _build_single_sense_assertion(triple, matches[0])
            mapped.append(assertion)
            single_sense_count += 1
            continue

        # Multiple senses — LLM disambiguation required
        candidate_dicts = _render_candidates_for_prompt(matches)
        template_vars: dict[str, Any] = {
            "relationship_verb": triple.relationship_verb,
            "entity_a": triple.entity_a.name,
            "entity_b": triple.entity_b.name,
            "evidence_span": triple.evidence_span,
            "candidates": candidate_dicts,
        }
        messages = api.render_prompt(_PASS2_PROMPT_TEMPLATE, **template_vars)

        try:
            result = await api.acall_llm(
                effective_model,
                messages,
                task=task,
                trace_id=trace_id,
                max_budget=max_budget,
                response_format={"type": "json_object"},
            )
            call_cost: float = result.cost or 0.0
            total_cost += call_cost
            raw_content: str = result.content or ""
        except Exception:
            logger.error(
                "Pass 2 LLM disambiguation failed for verb '%s' (trace_id=%s)",
                triple.relationship_verb,
                trace_id,
                exc_info=True,
            )
            unresolved.append(triple)
            unresolved_count += 1
            continue

        disambiguated = _parse_disambiguation_response(raw_content, matches, triple)
        if disambiguated is None:
            logger.warning(
                "Pass 2 disambiguation parse failed for verb '%s', marking unresolved",
                triple.relationship_verb,
            )
            unresolved.append(triple)
            unresolved_count += 1
            continue

        mapped.append(disambiguated)
        llm_disambiguated_count += 1

    logger.info(
        "Pass 2 complete: %d mapped (%d single-sense, %d LLM), %d unresolved "
        "(trace_id=%s, cost=$%.4f)",
        len(mapped),
        single_sense_count,
        llm_disambiguated_count,
        unresolved_count,
        trace_id,
        total_cost,
    )

    return Pass2Result(
        mapped=mapped,
        unresolved=unresolved,
        source_pass1=pass1_result,
        model=effective_model,
        cost=total_cost,
        trace_id=trace_id,
        single_sense_count=single_sense_count,
        llm_disambiguated_count=llm_disambiguated_count,
        unresolved_count=unresolved_count,
    )


def run_pass2_sync(
    pass1_result: Pass1Result,
    *,
    predicate_canon: PredicateCanon,
    model: str | None = None,
    task: str = "progressive_extraction",
    trace_id: str,
    max_budget: float = 0.10,
    _llm_api: _LLMClientAPI | None = None,
) -> Pass2Result:
    """Synchronous wrapper for :func:`run_pass2`.

    Runs the async implementation in a new event loop.  Prefer the async
    version when an event loop is already running.
    """
    return asyncio.run(
        run_pass2(
            pass1_result,
            predicate_canon=predicate_canon,
            model=model,
            task=task,
            trace_id=trace_id,
            max_budget=max_budget,
            _llm_api=_llm_api,
        )
    )


# ---------------------------------------------------------------------------
# Pass 3: Entity Refinement
# ---------------------------------------------------------------------------

_PASS3_PROMPT_TEMPLATE = "prompts/extraction/pass3_entity_refinement.yaml"

# Role constraints that are too broad to be useful for narrowing.  When a
# role's type_constraint is in this set, we treat it as unconstrained and
# show the full coarse-type subtree instead.
_TRIVIAL_CONSTRAINTS: frozenset[str] = frozenset({"Entity"})


def _is_leaf(sumo_hierarchy: SUMOHierarchy, type_name: str) -> bool:
    """Return True if *type_name* has no children in the SUMO hierarchy.

    A type is a leaf when its subtypes list is empty.  Types not found
    in the hierarchy are also treated as leaves (no subtree to explore).
    """
    return len(sumo_hierarchy.subtypes(type_name)) == 0


def _narrow_candidates(
    sumo_hierarchy: SUMOHierarchy,
    coarse_type: str,
    role_constraint: str | None,
) -> tuple[list[str], str]:
    """Compute the narrowed candidate type list for entity refinement.

    Returns a ``(candidates, effective_method)`` tuple where:

    - *candidates* is the list of SUMO type names to show the LLM
      (always includes the coarse_type itself).
    - *effective_method* is ``"subtree_pick"`` when the role constraint
      meaningfully narrows the candidates, or ``"no_constraint"`` when
      the full coarse-type subtree is used.

    The narrowing logic:

    1. Get all descendants of *coarse_type* (including coarse_type itself).
    2. If *role_constraint* is meaningful (non-trivial, exists in hierarchy):
       get all descendants of *role_constraint* and intersect with (1).
    3. If the intersection is non-empty, use it; otherwise fall back to (1).
    """
    coarse_descendants = sumo_hierarchy.subtypes(coarse_type)
    # Always include the coarse type itself as a candidate.
    coarse_set = {coarse_type} | set(coarse_descendants)

    if (
        role_constraint is None
        or role_constraint in _TRIVIAL_CONSTRAINTS
        or not sumo_hierarchy.type_exists(role_constraint)
    ):
        return sorted(coarse_set), "no_constraint"

    # Get the constraint subtree (constraint + its descendants).
    constraint_descendants = sumo_hierarchy.subtypes(role_constraint)
    constraint_set = {role_constraint} | set(constraint_descendants)

    intersection = coarse_set & constraint_set
    if intersection:
        return sorted(intersection), "subtree_pick"

    # No overlap — fall back to coarse subtree.
    return sorted(coarse_set), "no_constraint"


def _parse_refinement_response(
    raw_content: str,
    valid_types: set[str],
    coarse_type: str,
) -> str:
    """Parse the LLM refinement response and extract the refined type.

    Returns the ``refined_type`` from the JSON response if it is a valid
    type from the candidate list.  Falls back to *coarse_type* when the
    response is unparseable or the chosen type is not in the valid set.
    """
    content = _strip_markdown_fences(raw_content)

    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        logger.error("Pass 3 refinement response is not valid JSON: %.200s", content)
        return coarse_type

    if not isinstance(data, dict):
        logger.error(
            "Pass 3 refinement response is not a JSON object: %s",
            type(data).__name__,
        )
        return coarse_type

    refined = data.get("refined_type")
    if not isinstance(refined, str) or not refined.strip():
        logger.error("Pass 3 refinement response missing or empty refined_type")
        return coarse_type

    refined = refined.strip()
    if refined not in valid_types:
        logger.warning(
            "Pass 3 LLM picked type '%s' not in candidate list, falling back to '%s'",
            refined,
            coarse_type,
        )
        return coarse_type

    return refined


async def _refine_entity(
    entity_name: str,
    entity_context: str,
    coarse_type: str,
    role_label: str,
    role_constraint: str | None,
    sumo_hierarchy: SUMOHierarchy,
    api: _LLMClientAPI,
    effective_model: str,
    task: str,
    trace_id: str,
    max_budget: float,
) -> tuple[EntityRefinement, float]:
    """Refine a single entity's type using the narrowed SUMO subtree.

    Returns an ``(EntityRefinement, cost)`` tuple.  The cost is 0.0 for
    early-exit paths (leaf or trivially constrained when the subtree is
    just the coarse type itself).
    """
    # Leaf early exit: coarse type has no children.
    if _is_leaf(sumo_hierarchy, coarse_type):
        return EntityRefinement(
            entity_name=entity_name,
            coarse_type=coarse_type,
            refined_type=coarse_type,
            role_constraint=role_constraint or "",
            refinement_method="leaf_early_exit",
            candidate_count=0,
        ), 0.0

    # Compute narrowed candidate list.
    candidates, method = _narrow_candidates(
        sumo_hierarchy, coarse_type, role_constraint,
    )

    # If the narrowed list is just the coarse type itself, no LLM needed.
    if len(candidates) == 1 and candidates[0] == coarse_type:
        return EntityRefinement(
            entity_name=entity_name,
            coarse_type=coarse_type,
            refined_type=coarse_type,
            role_constraint=role_constraint or "",
            refinement_method=method,
            candidate_count=1,
        ), 0.0

    # Render prompt and call LLM.
    type_list_str = "\n".join(f"- {t}" for t in candidates)
    template_vars: dict[str, Any] = {
        "entity_name": entity_name,
        "entity_context": entity_context,
        "coarse_type": coarse_type,
        "role_label": role_label,
        "role_constraint": role_constraint or "",
        "type_list": type_list_str,
    }
    messages = api.render_prompt(_PASS3_PROMPT_TEMPLATE, **template_vars)

    try:
        result = await api.acall_llm(
            effective_model,
            messages,
            task=task,
            trace_id=trace_id,
            max_budget=max_budget,
            response_format={"type": "json_object"},
        )
        call_cost: float = result.cost or 0.0
        raw_content: str = result.content or ""
    except Exception:
        logger.error(
            "Pass 3 LLM refinement failed for entity '%s' (trace_id=%s)",
            entity_name,
            trace_id,
            exc_info=True,
        )
        return EntityRefinement(
            entity_name=entity_name,
            coarse_type=coarse_type,
            refined_type=coarse_type,
            role_constraint=role_constraint or "",
            refinement_method=method,
            candidate_count=len(candidates),
        ), 0.0

    valid_set = set(candidates)
    refined = _parse_refinement_response(raw_content, valid_set, coarse_type)

    return EntityRefinement(
        entity_name=entity_name,
        coarse_type=coarse_type,
        refined_type=refined,
        role_constraint=role_constraint or "",
        refinement_method=method,
        candidate_count=len(candidates),
    ), call_cost


async def run_pass3(
    pass2_result: Pass2Result,
    *,
    sumo_hierarchy: SUMOHierarchy,
    predicate_canon: PredicateCanon,
    model: str | None = None,
    task: str = "progressive_extraction",
    trace_id: str,
    max_budget: float = 0.10,
    _llm_api: _LLMClientAPI | None = None,
) -> Pass3Result:
    """Run Pass 3: entity refinement with narrowed SUMO subtree.

    For each mapped assertion and each entity role:

    1. Get the role's ``type_constraint`` from the Predicate Canon.
    2. Get descendants of the coarse type (Pass 1) from the SUMO hierarchy.
    3. Intersect with descendants of the role constraint.
    4. If the coarse type is a SUMO leaf (no children), early exit.
    5. Otherwise, show the narrowed type list to the LLM for refinement.

    Entity deduplication: if the same ``(entity_name, coarse_type)`` pair
    appears in multiple roles, it is refined only once and the result is
    reused across all assertions that reference that entity.

    Parameters
    ----------
    pass2_result:
        The Pass 2 mapping result to refine.
    sumo_hierarchy:
        An already-opened SUMOHierarchy instance (caller manages lifecycle).
    predicate_canon:
        An already-opened PredicateCanon instance (caller manages lifecycle).
    model:
        LLM model identifier for refinement calls.  Defaults to
        ``gemini/gemini-2.5-flash-lite``.
    task:
        Task tag for ``llm_client`` observability.
    trace_id:
        Trace ID for ``llm_client`` observability.
    max_budget:
        Maximum spend in USD for all refinement calls in this pass.
    _llm_api:
        Override for the llm_client API handle (testing only).

    Returns
    -------
    Pass3Result with typed assertions, provenance, and diagnostic counts.
    """
    api = _llm_api or _load_llm_client_api()
    effective_model = model or _DEFAULT_MODEL

    total_cost = 0.0
    leaf_early_exit_count = 0
    subtree_pick_count = 0
    no_constraint_count = 0

    # Deduplication cache: (entity_name, coarse_type) -> EntityRefinement
    refinement_cache: dict[tuple[str, str], EntityRefinement] = {}

    typed_assertions: list[Pass3TypedAssertion] = []

    for assertion in pass2_result.mapped:
        role_constraints = predicate_canon.get_role_constraints(
            assertion.predicate_id,
        )
        role_slots = predicate_canon.get_role_slots(assertion.predicate_id)
        # Build a lookup from arg_position to named_label.
        arg_to_label: dict[str, str] = {
            s.arg_position: s.named_label for s in role_slots
        }

        entity_refinements: list[EntityRefinement] = []

        for arg_pos, entity_name in assertion.mapped_roles.items():
            # Find the entity's coarse type from the triple.
            entity_a = assertion.triple.entity_a
            entity_b = assertion.triple.entity_b

            if entity_name == entity_a.name:
                coarse_type = entity_a.coarse_type
                entity_context = entity_a.context
            elif entity_name == entity_b.name:
                coarse_type = entity_b.coarse_type
                entity_context = entity_b.context
            else:
                # Entity name not in the triple — use "Entity" as fallback.
                coarse_type = "Entity"
                entity_context = ""

            cache_key = (entity_name, coarse_type)
            if cache_key in refinement_cache:
                entity_refinements.append(refinement_cache[cache_key])
                continue

            role_constraint = role_constraints.get(arg_pos)
            role_label = arg_to_label.get(arg_pos, arg_pos)

            refinement, cost = await _refine_entity(
                entity_name=entity_name,
                entity_context=entity_context,
                coarse_type=coarse_type,
                role_label=role_label,
                role_constraint=role_constraint,
                sumo_hierarchy=sumo_hierarchy,
                api=api,
                effective_model=effective_model,
                task=task,
                trace_id=trace_id,
                max_budget=max_budget,
            )
            total_cost += cost
            refinement_cache[cache_key] = refinement
            entity_refinements.append(refinement)

            # Track counts.
            if refinement.refinement_method == "leaf_early_exit":
                leaf_early_exit_count += 1
            elif refinement.refinement_method == "subtree_pick":
                subtree_pick_count += 1
            elif refinement.refinement_method == "no_constraint":
                no_constraint_count += 1

        typed_assertions.append(
            Pass3TypedAssertion(
                assertion=assertion,
                entity_refinements=entity_refinements,
            )
        )

    logger.info(
        "Pass 3 complete: %d typed assertions, %d refinements "
        "(%d leaf, %d subtree, %d no_constraint) (trace_id=%s, cost=$%.4f)",
        len(typed_assertions),
        len(refinement_cache),
        leaf_early_exit_count,
        subtree_pick_count,
        no_constraint_count,
        trace_id,
        total_cost,
    )

    return Pass3Result(
        typed_assertions=typed_assertions,
        source_pass2=pass2_result,
        model=effective_model,
        cost=total_cost,
        trace_id=trace_id,
        leaf_early_exit_count=leaf_early_exit_count,
        subtree_pick_count=subtree_pick_count,
        no_constraint_count=no_constraint_count,
    )


def run_pass3_sync(
    pass2_result: Pass2Result,
    *,
    sumo_hierarchy: SUMOHierarchy,
    predicate_canon: PredicateCanon,
    model: str | None = None,
    task: str = "progressive_extraction",
    trace_id: str,
    max_budget: float = 0.10,
    _llm_api: _LLMClientAPI | None = None,
) -> Pass3Result:
    """Synchronous wrapper for :func:`run_pass3`.

    Runs the async implementation in a new event loop.  Prefer the async
    version when an event loop is already running.
    """
    return asyncio.run(
        run_pass3(
            pass2_result,
            sumo_hierarchy=sumo_hierarchy,
            predicate_canon=predicate_canon,
            model=model,
            task=task,
            trace_id=trace_id,
            max_budget=max_budget,
            _llm_api=_llm_api,
        )
    )


# ---------------------------------------------------------------------------
# Pipeline Orchestrator (Slice E)
# ---------------------------------------------------------------------------


class ProgressiveExtractionError(RuntimeError):
    """Raised when the progressive extraction pipeline fails.

    Wraps the underlying exception with context about which pass
    failed and the trace ID for debugging.
    """


async def run_progressive_extraction(
    text: str,
    *,
    sumo_db_path: Path,
    model: str | None = None,
    task: str = "progressive_extraction",
    trace_id: str | None = None,
    max_budget: float = 0.30,
    max_triples: int = 50,
    _llm_api: _LLMClientAPI | None = None,
) -> ProgressiveExtractionReport:
    """Run the full 3-pass progressive extraction pipeline.

    Pass 1: Extract entities and relationships with coarse SUMO types.
    Pass 2: Map relationship verbs to Predicate Canon entries.
    Pass 3: Refine entity types using narrowed SUMO subtrees.

    Opens SUMOHierarchy and PredicateCanon internally (caller does not
    need to manage them).  Generates ``trace_id`` if not provided.

    Budget is split across passes: 40% Pass 1, 30% Pass 2, 30% Pass 3.

    Parameters
    ----------
    text:
        The source text to extract from.
    sumo_db_path:
        Path to the ``sumo_plus.db`` file used by SUMOHierarchy and
        PredicateCanon.
    model:
        LLM model identifier.  Defaults to ``gemini/gemini-2.5-flash-lite``.
    task:
        Task tag for ``llm_client`` observability.
    trace_id:
        Trace ID for ``llm_client`` observability.  Auto-generated if not
        provided.
    max_budget:
        Maximum total spend in USD across all passes.
    max_triples:
        Soft limit on triples for Pass 1.
    _llm_api:
        Override for the llm_client API handle (testing only).

    Returns
    -------
    ProgressiveExtractionReport with all three pass results and summary
    statistics.

    Raises
    ------
    ProgressiveExtractionError:
        If any pass fails with an unrecoverable error.
    """
    effective_trace_id = trace_id or f"prog_{_uuid.uuid4().hex[:12]}"
    effective_model = model or _DEFAULT_MODEL

    # Budget allocation: 40% pass 1, 30% pass 2, 30% pass 3.
    budget_pass1 = max_budget * 0.4
    budget_pass2 = max_budget * 0.3
    budget_pass3 = max_budget * 0.3

    # --- Pass 1 ---
    try:
        pass1_result = await run_pass1(
            text,
            model=effective_model,
            task=task,
            trace_id=effective_trace_id,
            max_budget=budget_pass1,
            max_triples=max_triples,
            _llm_api=_llm_api,
        )
    except Exception as exc:
        raise ProgressiveExtractionError(
            f"Pass 1 failed (trace_id={effective_trace_id}): {exc}"
        ) from exc

    # --- Pass 2 ---
    with PredicateCanon(sumo_db_path) as predicate_canon:
        try:
            pass2_result = await run_pass2(
                pass1_result,
                predicate_canon=predicate_canon,
                model=effective_model,
                task=task,
                trace_id=effective_trace_id,
                max_budget=budget_pass2,
                _llm_api=_llm_api,
            )
        except Exception as exc:
            raise ProgressiveExtractionError(
                f"Pass 2 failed (trace_id={effective_trace_id}): {exc}"
            ) from exc

        # --- Pass 3 ---
        with SUMOHierarchy(sumo_db_path) as sumo_hierarchy:
            try:
                pass3_result = await run_pass3(
                    pass2_result,
                    sumo_hierarchy=sumo_hierarchy,
                    predicate_canon=predicate_canon,
                    model=effective_model,
                    task=task,
                    trace_id=effective_trace_id,
                    max_budget=budget_pass3,
                    _llm_api=_llm_api,
                )
            except Exception as exc:
                raise ProgressiveExtractionError(
                    f"Pass 3 failed (trace_id={effective_trace_id}): {exc}"
                ) from exc

    # --- Aggregate ---
    total_cost = pass1_result.cost + pass2_result.cost + pass3_result.cost

    # Count unique entities refined in Pass 3 (from the dedup cache perspective,
    # each typed assertion has a list of entity refinements).
    refined_entities: set[tuple[str, str]] = set()
    for typed_assertion in pass3_result.typed_assertions:
        for refinement in typed_assertion.entity_refinements:
            refined_entities.add((refinement.entity_name, refinement.coarse_type))

    report = ProgressiveExtractionReport(
        pass1=pass1_result,
        pass2=pass2_result,
        pass3=pass3_result,
        total_cost=total_cost,
        trace_id=effective_trace_id,
        model=effective_model,
        triples_extracted=len(pass1_result.triples),
        predicates_mapped=len(pass2_result.mapped),
        predicates_unresolved=len(pass2_result.unresolved),
        entities_refined=len(refined_entities),
        single_sense_early_exits=pass2_result.single_sense_count,
        leaf_type_early_exits=pass3_result.leaf_early_exit_count,
    )

    logger.info(
        "Progressive extraction complete: %d triples, %d mapped, %d unresolved, "
        "%d entities refined (trace_id=%s, total_cost=$%.4f)",
        report.triples_extracted,
        report.predicates_mapped,
        report.predicates_unresolved,
        report.entities_refined,
        effective_trace_id,
        total_cost,
    )

    return report


def run_progressive_extraction_sync(
    text: str,
    *,
    sumo_db_path: Path,
    model: str | None = None,
    task: str = "progressive_extraction",
    trace_id: str | None = None,
    max_budget: float = 0.30,
    max_triples: int = 50,
    _llm_api: _LLMClientAPI | None = None,
) -> ProgressiveExtractionReport:
    """Synchronous wrapper for :func:`run_progressive_extraction`.

    Runs the async implementation in a new event loop.  Prefer the async
    version when an event loop is already running.
    """
    return asyncio.run(
        run_progressive_extraction(
            text,
            sumo_db_path=sumo_db_path,
            model=model,
            task=task,
            trace_id=trace_id,
            max_budget=max_budget,
            max_triples=max_triples,
            _llm_api=_llm_api,
        )
    )

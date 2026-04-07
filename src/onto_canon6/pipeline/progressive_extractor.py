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
import re
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
    AliasPair,
    AnaphorResolution,
    EntityRefinement,
    MergeDecision,
    Pass1Entity,
    Pass1Event,
    Pass1Participant,
    Pass1Result,
    Pass2MappedAssertion,
    Pass2Result,
    Pass3Result,
    Pass3TypedAssertion,
    Pass4NormalizationResult,
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


class _RawParticipant(BaseModel):
    """Permissive participant shape returned by the LLM.

    Allows missing or empty fields so partial extraction results are not
    discarded at the parse boundary.
    """

    model_config = ConfigDict(extra="ignore")

    proto_role: str = "Unspecified"
    name: str = ""
    coarse_type: str = ""
    context: str = ""


class _RawEvent(BaseModel):
    """Permissive event frame shape returned by the LLM.

    Uses ``extra="ignore"`` so unexpected keys do not crash parsing.
    Missing participants are represented as empty lists.
    """

    model_config = ConfigDict(extra="ignore")

    relationship_verb: str = ""
    participants: list[_RawParticipant] = Field(default_factory=list)
    evidence_span: str = ""
    confidence: float = 0.5
    claim_level: str = "instance"


class _RawPass1Response(BaseModel):
    """Top-level shape of the LLM's JSON response for Pass 1.

    Intentionally permissive (``extra="ignore"``) so that unexpected
    top-level keys do not abort parsing.
    """

    model_config = ConfigDict(extra="ignore")

    events: list[_RawEvent] = Field(default_factory=list)


# -- json_schema response format for Pass 1 ----------------------------------
# Schema field descriptions are a prompting surface: they constrain LLM output
# at decode time.  Design prompt and schema together.

class _SchemaParticipant(BaseModel):
    """Participant schema for json_schema response_format."""

    proto_role: str = Field(
        description=(
            "Semantic role. Must be one of: Agent, Theme, Recipient, "
            "Instrument, Location, Source, Experiencer, Cause, Attribute, Unspecified."
        ),
    )
    name: str = Field(description="Entity name as it appears in the text.")
    coarse_type: str = Field(description="Best SUMO type from the provided type list.")
    context: str = Field(description="One-sentence description of this entity from the text.")


class _SchemaEvent(BaseModel):
    """Event frame schema for json_schema response_format."""

    relationship_verb: str = Field(
        description=(
            "Bare verb infinitive describing the action "
            "(e.g. 'deploy', 'invest', 'compete', 'develop', 'target', 'fund'). "
            "Not past tense, not with prepositions, not a noun phrase. "
            "Will be matched against a predicate database by lemma."
        ),
    )
    participants: list[_SchemaParticipant] = Field(
        description=(
            "All participants in this event with their semantic roles. "
            "Include Agent and Theme at minimum; add Recipient, Instrument, "
            "Location etc. when clearly present in the text."
        ),
    )
    evidence_span: str = Field(description="Short excerpt from the source text supporting this event.")
    confidence: float = Field(description="How clearly the text supports this event, 0.0 to 1.0.")
    claim_level: str = Field(
        description="'instance' for specific events, 'type' for general patterns.",
    )


class _SchemaPass1Response(BaseModel):
    """Top-level response schema for Pass 1 structured output."""

    events: list[_SchemaEvent]


def _pass1_response_format() -> dict[str, Any]:
    """Build the ``json_schema`` response_format for Pass 1.

    Uses Pydantic's ``model_json_schema()`` to generate the JSON Schema,
    then wraps it in the litellm ``response_format`` envelope.
    """
    return {
        "type": "json_schema",
        "json_schema": {
            "name": "pass1_extraction",
            "schema": _SchemaPass1Response.model_json_schema(),
        },
    }


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


def _coerce_event(raw: _RawEvent) -> Pass1Event | None:
    """Convert a permissive raw event into a strict Pass1Event.

    Returns None when the event is too incomplete (no verb or no valid participants).
    Requires at least one participant with a non-empty name.
    """
    if not raw.relationship_verb.strip():
        return None

    participants: list[Pass1Participant] = []
    for rp in raw.participants:
        if not rp.name.strip():
            continue  # skip participants with no name
        try:
            participant = Pass1Participant(
                proto_role=rp.proto_role.strip() if rp.proto_role.strip() else "Unspecified",
                entity=Pass1Entity(
                    name=rp.name.strip(),
                    coarse_type=rp.coarse_type.strip() or "Entity",
                    context=rp.context.strip(),
                ),
            )
            participants.append(participant)
        except ValidationError:
            logger.warning("Failed to coerce participant: %s", rp, exc_info=True)
            continue

    if not participants:
        return None

    confidence = max(0.0, min(1.0, raw.confidence))
    try:
        return Pass1Event(
            relationship_verb=raw.relationship_verb.strip(),
            participants=participants,
            evidence_span=raw.evidence_span.strip(),
            confidence=confidence,
            claim_level=raw.claim_level if raw.claim_level in ("type", "instance") else "instance",
        )
    except ValidationError:
        logger.warning("Failed to validate event: %s", raw, exc_info=True)
        return None


def _deduplicate_entities(events: list[Pass1Event]) -> list[Pass1Entity]:
    """Collect a deduplicated entity list from extracted events.

    Deduplication is by (name, coarse_type). When the same entity name
    appears with different coarse types, both entries are kept since they
    represent genuinely different classifications.
    """
    seen: dict[tuple[str, str], Pass1Entity] = {}
    for event in events:
        for participant in event.participants:
            entity = participant.entity
            key = (entity.name, entity.coarse_type)
            if key not in seen:
                seen[key] = entity
    return list(seen.values())


def _parse_llm_response(raw_content: str) -> list[Pass1Event]:
    """Parse the LLM's raw text response into a list of Pass1Event.

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

    events: list[Pass1Event] = []
    for raw_event in raw_response.events:
        coerced = _coerce_event(raw_event)
        if coerced is not None:
            events.append(coerced)

    return events


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
            response_format=_pass1_response_format(),
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
            events=[],
            entities=[],
            source_text_hash=source_hash,
            model=effective_model,
            cost=0.0,
            trace_id=trace_id,
        )

    # Parse and validate
    events = _parse_llm_response(raw_content)
    entities = _deduplicate_entities(events)

    logger.info(
        "Pass 1 extracted %d events, %d unique entities (trace_id=%s, cost=$%.4f)",
        len(events),
        len(entities),
        trace_id,
        cost,
    )

    return Pass1Result(
        events=events,
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


# Maps proto-roles to the named_label values used in PropBank/SUMO role slots.
_PROTO_ROLE_LABEL_FAMILIES: dict[str, frozenset[str]] = {
    "Agent": frozenset({"Agent", "Operator", "Causer", "Perpetrator", "Actor", "Speaker", "Experiencer", "Gatherer"}),
    "Theme": frozenset({"Theme", "Patient", "Target", "Victim", "Phenomenon", "System", "Item", "Crop", "Total"}),
    "Recipient": frozenset({"Recipient", "Beneficiary", "Destination", "Goal"}),
    "Instrument": frozenset({"Instrument"}),
    "Location": frozenset({"Location", "Place"}),
    "Source": frozenset({"Source", "Origin"}),
    "Experiencer": frozenset({"Experiencer", "Perceiver"}),
    "Cause": frozenset({"Cause", "Reason"}),
    "Attribute": frozenset({"Attribute", "Property", "Manner", "Purpose", "Part"}),
    "Unspecified": frozenset(),
}


def _assign_participant_to_slot(
    proto_role: str,
    role_slots: list[Any],
    already_assigned: set[str],
) -> str | None:
    """Find the best named_label for a participant given their proto_role.

    First tries to match by named_label family, then falls back to the first
    unassigned slot in position order.  Returns the slot's named_label (e.g.
    "Operator", "Theme") — never an ARG position — so mapped_roles stores
    human-readable role names directly.
    """
    family = _PROTO_ROLE_LABEL_FAMILIES.get(proto_role, frozenset())

    # First pass: find slot whose named_label matches the proto_role family
    for slot in role_slots:
        if slot.named_label in already_assigned:
            continue
        if slot.named_label in family or slot.named_label == proto_role:
            return slot.named_label

    # Second pass: take the first unassigned slot
    for slot in role_slots:
        if slot.named_label not in already_assigned:
            return slot.named_label

    return None  # all slots filled


def _build_single_sense_assertion(
    event: Pass1Event,
    match: PredicateMatch,
) -> Pass2MappedAssertion:
    """Build a Pass2MappedAssertion using proto-role affinity for slot assignment.

    Maps participants to predicate named_labels (e.g. "Operator", "Theme") by
    matching proto_role against the predicate's named_label families.  Falls
    back to positional assignment when no family match is found.  mapped_roles
    stores {named_label: entity_name} — never ARG positions.
    """
    role_mapping: dict[str, str] = {}
    assigned: set[str] = set()

    for participant in event.participants:
        role_label = _assign_participant_to_slot(
            participant.proto_role, match.role_slots, assigned
        )
        if role_label is not None:
            role_mapping[role_label] = participant.entity.name
            assigned.add(role_label)

    return Pass2MappedAssertion(
        event=event,
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
    event: Pass1Event,
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

    # Verify the chosen predicate is among the candidates.
    # Accept either predicate_id or propbank_sense_id since the LLM may
    # return either format (both are shown in the disambiguation prompt).
    candidate_by_id = {m.predicate_id: m for m in candidates}
    candidate_by_sense = {m.propbank_sense_id: m for m in candidates}
    chosen = candidate_by_id.get(predicate_id) or candidate_by_sense.get(predicate_id)
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
        event=event,
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
    unresolved: list[Pass1Event] = []
    total_cost = 0.0
    single_sense_count = 0
    llm_disambiguated_count = 0
    unresolved_count = 0

    for event in pass1_result.events:
        matches = _lookup_lemma(event.relationship_verb, predicate_canon)

        if not matches:
            # No predicate found — store permissively as unresolved
            logger.info(
                "Pass 2 unresolved: verb '%s' has no predicate match (trace_id=%s)",
                event.relationship_verb,
                trace_id,
            )
            unresolved.append(event)
            unresolved_count += 1
            continue

        if len(matches) == 1:
            # Single sense — deterministic mapping, no LLM call
            assertion = _build_single_sense_assertion(event, matches[0])
            mapped.append(assertion)
            single_sense_count += 1
            continue

        # Multiple senses — LLM disambiguation required
        candidate_dicts = _render_candidates_for_prompt(matches)
        template_vars: dict[str, Any] = {
            "relationship_verb": event.relationship_verb,
            "participants": [
                {
                    "proto_role": p.proto_role,
                    "entity_name": p.entity.name,
                    "entity_type": p.entity.coarse_type,
                }
                for p in event.participants
            ],
            "evidence_span": event.evidence_span,
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
                event.relationship_verb,
                trace_id,
                exc_info=True,
            )
            unresolved.append(event)
            unresolved_count += 1
            continue

        disambiguated = _parse_disambiguation_response(raw_content, matches, event)
        if disambiguated is None:
            logger.warning(
                "Pass 2 disambiguation parse failed for verb '%s', marking unresolved",
                event.relationship_verb,
            )
            unresolved.append(event)
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
        # mapped_roles stores {named_label: entity_name} — no ARG translation needed.
        role_constraints = predicate_canon.get_role_constraints(
            assertion.predicate_id,
        )

        entity_refinements: list[EntityRefinement] = []

        # Build a lookup from entity name to Pass1Entity using all participants.
        entity_by_name = {
            p.entity.name: p.entity for p in assertion.event.participants
        }

        for role_label, entity_name in assertion.mapped_roles.items():
            # Find the entity's coarse type from the event participants.
            entity = entity_by_name.get(entity_name)
            if entity:
                coarse_type = entity.coarse_type
                entity_context = entity.context
            else:
                # Entity name not among participants — use "Entity" as fallback.
                coarse_type = "Entity"
                entity_context = ""

            cache_key = (entity_name, coarse_type)
            if cache_key in refinement_cache:
                entity_refinements.append(refinement_cache[cache_key])
                continue

            role_constraint = role_constraints.get(role_label)

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
# Pass 4: Entity Normalization
# ---------------------------------------------------------------------------

_PASS4_ANAPHOR_PROMPT = "prompts/extraction/pass4_entity_normalization.yaml"
_PASS4_MERGE_PROMPT = "prompts/extraction/pass4_merge_duplicates.yaml"

# Pronouns that are always anaphors — never real entity names.
_PRONOUNS: frozenset[str] = frozenset(
    {
        "it", "its", "itself",
        "they", "them", "their", "themselves",
        "this", "these", "those",
        "he", "him", "his", "himself",
        "she", "her", "hers", "herself",
        "we", "us", "our", "ourselves",
    }
)

# Generic nouns that, when bare or following an article, mark a descriptive
# phrase rather than a named entity.
_GENERIC_NOUNS: frozenset[str] = frozenset(
    {
        "group", "groups", "actor", "actors", "attacker", "attackers",
        "target", "targets", "device", "devices", "system", "systems",
        "entity", "entities", "organization", "organizations",
        "campaign", "campaigns", "operation", "operations", "activity",
        "activities", "threat", "threats", "initiative", "initiatives",
        "effort", "efforts", "approach", "approaches", "strategy",
        "strategies", "convergence", "dimension", "format", "method",
        "mechanism", "vector", "technique", "infrastructure",
        "assessment", "report", "source", "sources",
        # Additional generics found in quality review
        "step", "steps", "procedure", "procedures", "process", "processes",
        "pattern", "patterns", "behavior", "behaviors", "portfolio",
        "training", "material", "materials", "capability", "capabilities",
        "tactic", "tactics", "tool", "tools", "resource", "resources",
    }
)

# Finite verb forms that indicate a phrase is a sentence fragment, not an entity.
_FINITE_VERB_RE = re.compile(
    r"\b(is|are|was|were|has|have|had|uses|used|provides|allows|includes?|"
    r"conducts?|performs?|operates?|involves?|enables?|relies?|deploys?|"
    r"targets?|employs?)\b",
    re.IGNORECASE,
)

# SUMO type families that represent real-world agents/organizations.
# Near-duplicates are only merged within the same family.
_AGENT_TYPE_FAMILIES: frozenset[str] = frozenset(
    {
        "Agent", "CognitiveAgent", "SentientAgent",
        "Organization", "GovernmentOrganization", "Corporation",
        "MilitaryOrganization", "PoliticalOrganization",
        "EducationalOrganization", "Person", "Human",
    }
)

# SUMO type families that represent processes/events — never merge with agents.
_PROCESS_TYPE_FAMILIES: frozenset[str] = frozenset(
    {
        "Process", "IntentionalProcess", "PhysicalProcess",
        "SocialProcess", "CommunicationAct", "Transfer",
        "Motion", "Proposition", "Attribute", "Relation",
    }
)


def _is_anaphor(name: str) -> tuple[bool, bool, str]:
    """Return (is_anaphor, is_certain, reason) for an entity name.

    ``is_certain`` is True for rules whose pattern is deterministic — the
    entity is definitively not a real named entity and should be dropped
    without LLM confirmation.  ``is_certain`` is False for heuristic rules
    that may have edge cases; those candidates go to the LLM for review.

    Certain rules (bypass LLM):
    1. Bare pronouns ("it", "they", "this", etc.)
    2. Bare generic nouns ("group", "Groups", "activities")
    3. Demonstrative prefix: "This step", "these actors"
    4. Possessive construction: "their X", "its X", "APT42's operators",
       "the group's portfolio"

    LLM-reviewed rules:
    5. Article + generic noun: "the group", "a campaign"
    6. Long descriptive phrases (> 50 chars) with no capitalized proper noun
       after the first word.
    7. Verb-containing phrase (> 30 chars): finite verb indicates sentence fragment.
    """
    stripped = name.strip()
    lower = stripped.lower()

    # 1. Bare pronouns — certain
    if lower in _PRONOUNS:
        return True, True, f"pronoun: '{name}'"

    # 2. Bare generic nouns — certain
    bare = lower.rstrip("s")
    if lower in _GENERIC_NOUNS or bare in _GENERIC_NOUNS:
        return True, True, f"bare generic noun: '{name}'"

    # 3. Demonstrative prefix — certain
    for prefix in ("this ", "these ", "those "):
        if lower.startswith(prefix):
            return True, True, f"demonstrative phrase: '{name}'"

    # 4. Possessive construction — certain
    # 4a. Pronoun possessives: "their X", "its X"
    for prefix in ("their ", "its "):
        if lower.startswith(prefix):
            return True, True, f"possessive anaphor prefix: '{name}'"
    # 4b. "the X's Y" — article + noun + possessive
    if lower.startswith("the ") and "'s" in lower:
        return True, True, f"possessive anaphor: '{name}'"
    # 4c. Proper-noun possessive: "APT42's operators" — X's <lowercase-start word>
    apos_idx = stripped.find("'s ")
    if apos_idx != -1:
        after = stripped[apos_idx + 3:]
        if after and after[0].islower():
            return True, True, f"possessive construction: '{name}'"

    # 5. Article + generic noun — LLM-reviewed (edge cases: "the Organization")
    for article in ("the ", "a ", "an "):
        if lower.startswith(article):
            remainder = lower[len(article):]
            words = remainder.split()
            if not words:
                continue
            first_word = words[0].rstrip("s")
            if first_word in _GENERIC_NOUNS or words[0] in _GENERIC_NOUNS:
                return True, False, f"article + generic noun: '{name}'"
            last_word = words[-1].rstrip("s")
            if last_word in _GENERIC_NOUNS or words[-1] in _GENERIC_NOUNS:
                return True, False, f"article + generic noun phrase: '{name}'"
            if remainder.rstrip() in _GENERIC_NOUNS:
                return True, False, f"article + generic noun: '{name}'"

    # 6. Long descriptive phrase — LLM-reviewed
    if len(stripped) > 50:
        words = stripped.split()
        first_lower = words[0][0].islower() if words else False
        starts_with_article = words[0].lower() in ("a", "an", "the") if words else False
        if first_lower or starts_with_article:
            has_proper_noun = any(
                w[0].isupper() and len(w) > 2 and not w.isupper()
                for w in words[1:]
            )
            if not has_proper_noun:
                return True, False, f"long descriptive phrase ({len(stripped)} chars): '{name[:60]}...'"

    # 7. Verb-containing phrase — LLM-reviewed
    if len(stripped) > 30 and _FINITE_VERB_RE.search(stripped):
        return True, False, f"verb-containing phrase: '{name[:60]}'"

    return False, False, ""


def _are_types_compatible(type_a: str, type_b: str) -> bool:
    """Return True if two SUMO types could belong to the same entity.

    Rejects pairs where one type is in the agent family and the other is
    in the process/attribute family — those are never the same entity.
    """
    a_is_agent = any(type_a.startswith(t) or type_a == t for t in _AGENT_TYPE_FAMILIES)
    b_is_agent = any(type_b.startswith(t) or type_b == t for t in _AGENT_TYPE_FAMILIES)
    a_is_process = any(type_a.startswith(t) or type_a == t for t in _PROCESS_TYPE_FAMILIES)
    b_is_process = any(type_b.startswith(t) or type_b == t for t in _PROCESS_TYPE_FAMILIES)

    # Reject agent-vs-process cross-matches
    if (a_is_agent and b_is_process) or (b_is_agent and a_is_process):
        return False
    return True


def _edit_distance(a: str, b: str) -> int:
    """Compute Levenshtein edit distance between two strings."""
    if a == b:
        return 0
    m, n = len(a), len(b)
    if m == 0:
        return n
    if n == 0:
        return m
    # Use two-row DP to keep memory O(n)
    prev = list(range(n + 1))
    curr = [0] * (n + 1)
    for i in range(1, m + 1):
        curr[0] = i
        for j in range(1, n + 1):
            cost = 0 if a[i - 1] == b[j - 1] else 1
            curr[j] = min(prev[j] + 1, curr[j - 1] + 1, prev[j - 1] + cost)
        prev, curr = curr, prev
    return prev[n]


def _normalize_for_comparison(name: str) -> str:
    """Lowercase and strip a name for near-duplicate comparison."""
    return name.lower().strip().rstrip(".")


def _extract_acronym(name: str) -> str:
    """Return the first-letter acronym of a multi-word name."""
    words = name.split()
    if len(words) < 2:
        return ""
    return "".join(w[0].upper() for w in words if w and w[0].isalpha())


# ---------------------------------------------------------------------------
# Alias extraction from text-declared parenthetical patterns (Plan 0074)
# ---------------------------------------------------------------------------

# Pattern A: "Full Name (ACRONYM)" — long form declared, abbreviation in parens.
_ALIAS_PAREN_DEFINE = re.compile(
    r"\b([A-Z][^\(\)\n]{4,80}?)\s+\(([A-Z][A-Z0-9\-]{1,15})\)",
    re.UNICODE,
)

# Pattern B: "ACRONYM (Full Name)" — abbreviation declared first, expansion in parens.
_ALIAS_PAREN_EXPAND = re.compile(
    r"\b([A-Z][A-Z0-9\-]{1,15})\s+\(([A-Z][^\(\)\n]{4,80}?)\)",
    re.UNICODE,
)


def extract_alias_pairs(
    source_text: str,
    entity_names: set[str],
) -> list[AliasPair]:
    """Extract text-declared alias pairs from parenthetical patterns in source text.

    Detects two patterns:
    - Pattern A "Full Name (ACRONYM)": long form declared, abbreviation in parens.
    - Pattern B "ACRONYM (Full Name)": abbreviation declared first, expansion in parens.

    Only registers a pair when **both** the short form and long form appear as entity
    names in *entity_names*.  The longer form is always canonical.  No LLM verification
    is required — text-declared equivalences are accepted deterministically.

    Article stripping: when the captured long form starts with a leading article
    ("The ", "A ", "An "), the article-stripped form is tried as a fallback.  This
    handles "The Islamic Revolutionary Guard Corps (IRGC)" where the regex matches at
    "The" but the entity name in the corpus is "Islamic Revolutionary Guard Corps".
    """
    if not source_text or not entity_names:
        return []

    found: list[AliasPair] = []
    seen: set[tuple[str, str]] = set()  # (short_form, long_form) dedup key

    _LEADING_ARTICLES = ("The ", "A ", "An ")

    def _try_register(long: str, short: str, raw_span: str) -> bool:
        key = (short, long)
        if key in seen:
            return False
        if short not in entity_names or long not in entity_names:
            return False
        seen.add(key)
        found.append(AliasPair(short_form=short, long_form=long, source_pattern=raw_span))
        return True

    def _register(long_form: str, short_form: str, raw_span: str) -> None:
        short = short_form.strip()
        long = long_form.strip()
        if _try_register(long, short, raw_span):
            return
        # Fallback: strip leading article ("The ", "A ", "An ") and retry.
        # This handles "The Islamic Revolutionary Guard Corps (IRGC)" where the regex
        # anchors on the capital "T" but the entity name omits the leading article.
        for article in _LEADING_ARTICLES:
            if long.startswith(article):
                _try_register(long[len(article):], short, raw_span)
                break

    for m in _ALIAS_PAREN_DEFINE.finditer(source_text):
        _register(long_form=m.group(1), short_form=m.group(2), raw_span=m.group(0))

    for m in _ALIAS_PAREN_EXPAND.finditer(source_text):
        _register(long_form=m.group(2), short_form=m.group(1), raw_span=m.group(0))

    return found


# ---------------------------------------------------------------------------
# Structural fingerprint deduplication (Plan 0074)
# ---------------------------------------------------------------------------


def compute_entity_profiles(
    pass3_result: Pass3Result,
    entity_names: set[str],
) -> dict[str, frozenset[tuple[str, str]]]:
    """Return mapping from entity name → (predicate_id, role_label) profile.

    For each entity, the profile is the frozenset of ``(predicate_id, role_label)``
    pairs from all assertions the entity participates in.  This is the determinative
    predicate fingerprint from the Grale entity deduplication pipeline (Google KDD 2020).

    Parameters
    ----------
    pass3_result:
        The Pass 3 result containing typed assertions with mapped roles.
    entity_names:
        The set of entity names to compute profiles for.
    """
    profiles: dict[str, set[tuple[str, str]]] = {name: set() for name in entity_names}

    for typed_assertion in pass3_result.typed_assertions:
        assertion = typed_assertion.assertion
        predicate_id = assertion.predicate_id
        for role_label, entity_name in assertion.mapped_roles.items():
            if entity_name in profiles:
                profiles[entity_name].add((predicate_id, role_label))

    return {name: frozenset(pairs) for name, pairs in profiles.items()}


def detect_structural_duplicate_pairs(
    entity_infos: list[dict[str, str]],
    profiles: dict[str, frozenset[tuple[str, str]]],
    *,
    jaccard_threshold: float = 0.35,
    min_profile_size: int = 2,
) -> list[tuple[dict[str, str], dict[str, str]]]:
    """Return entity pairs with high Jaccard similarity on their predicate-role profiles.

    Entities with fewer than *min_profile_size* predicate-role pairs are excluded
    (insufficient signal — a single shared pair is noise).  Pairs with incompatible
    SUMO types are rejected by :func:`_are_types_compatible`.

    Parameters
    ----------
    entity_infos:
        List of entity info dicts with keys: ``name``, ``sumo_type``, ``evidence_span``.
    profiles:
        Mapping from entity name → ``frozenset[(predicate_id, role_label)]`` profile.
    jaccard_threshold:
        Minimum Jaccard similarity to flag a pair as a candidate.
    min_profile_size:
        Minimum profile size required to participate in comparison.
    """
    pairs: list[tuple[dict[str, str], dict[str, str]]] = []
    seen: set[tuple[int, int]] = set()

    for i, info_a in enumerate(entity_infos):
        profile_a = profiles.get(info_a["name"], frozenset())
        if len(profile_a) < min_profile_size:
            continue
        for j, info_b in enumerate(entity_infos):
            if j <= i:
                continue
            if (i, j) in seen:
                continue
            profile_b = profiles.get(info_b["name"], frozenset())
            if len(profile_b) < min_profile_size:
                continue
            if not _are_types_compatible(info_a["sumo_type"], info_b["sumo_type"]):
                continue
            intersection = len(profile_a & profile_b)
            if intersection == 0:
                continue
            union = len(profile_a | profile_b)
            jaccard = intersection / union
            if jaccard >= jaccard_threshold:
                pairs.append((info_a, info_b))
                seen.add((i, j))

    return pairs


def _compute_co_participants(
    name_a: str,
    name_b: str,
    assertion_index: dict[str, list[dict[str, Any]]],
    *,
    max_count: int = 5,
) -> list[str]:
    """Return entity names that co-appear with BOTH name_a and name_b across assertions."""
    set_a: set[str] = set()
    for entry in assertion_index.get(name_a, []):
        set_a.update(entry["participants"])
    set_a.discard(name_a)

    set_b: set[str] = set()
    for entry in assertion_index.get(name_b, []):
        set_b.update(entry["participants"])
    set_b.discard(name_b)

    common = (set_a & set_b) - {name_a, name_b}
    return sorted(common)[:max_count]


def detect_near_duplicate_pairs(
    entity_infos: list[dict[str, str]],
) -> list[tuple[dict[str, str], dict[str, str]]]:
    """Detect candidate near-duplicate pairs among entity infos.

    Each entity info dict has keys: ``name``, ``sumo_type``, ``evidence_span``.

    Pair detection criteria (Tier 1 — no embeddings):
    1. Substring: one normalized name is a substring of another.
    2. Acronym match: acronym of one name equals the other (normalized).
    3. Edit distance ≤ 2 on normalized forms.

    Pairs where SUMO types are incompatible (agent vs process) are rejected
    before being returned.

    Returns a list of (entity_a_info, entity_b_info) pairs.
    """
    pairs: list[tuple[dict[str, str], dict[str, str]]] = []
    seen: set[tuple[int, int]] = set()

    for i, info_a in enumerate(entity_infos):
        norm_a = _normalize_for_comparison(info_a["name"])
        acronym_a = _extract_acronym(info_a["name"])

        for j, info_b in enumerate(entity_infos):
            if j <= i:
                continue
            if (i, j) in seen:
                continue

            norm_b = _normalize_for_comparison(info_b["name"])
            acronym_b = _extract_acronym(info_b["name"])

            # Check type compatibility first
            if not _are_types_compatible(info_a["sumo_type"], info_b["sumo_type"]):
                continue

            is_candidate = False
            # 1. Substring test — only when shorter string is substantial AND
            # at least 60% the length of the longer string.  This prevents
            # short tokens like "APT42" or "Israel" from matching long compound
            # phrases that merely *contain* them ("APT35 and APT42",
            # "Israel and the United States").
            if norm_a and norm_b and (norm_a in norm_b or norm_b in norm_a):
                shorter = norm_a if len(norm_a) <= len(norm_b) else norm_b
                longer = norm_b if len(norm_a) <= len(norm_b) else norm_a
                if len(shorter) >= 3 and len(shorter) / len(longer) >= 0.50:
                    is_candidate = True
            # 2. Acronym match
            elif acronym_a and (acronym_a == norm_b.upper() or acronym_a == info_b["name"]):
                is_candidate = True
            elif acronym_b and (acronym_b == norm_a.upper() or acronym_b == info_a["name"]):
                is_candidate = True
            # 3. Edit distance ≤ 1 — catches plural/singular and single-char
            # variants but rejects different-entity short-string collisions
            # (APT42 vs APT35, FBI vs FTP, Iran vs IRGC all have distance 2).
            elif len(norm_a) <= 30 and len(norm_b) <= 30 and _edit_distance(norm_a, norm_b) <= 1:
                is_candidate = True

            if is_candidate:
                pairs.append((info_a, info_b))
                seen.add((i, j))

    return pairs


def _collect_entity_infos(
    pass3_result: Pass3Result,
) -> list[dict[str, str]]:
    """Collect unique entity name/type/evidence tuples from Pass 3 results.

    Returns a list of dicts with keys: ``name``, ``sumo_type``, ``evidence_span``.
    Deduplication is by name (first occurrence wins).
    """
    seen: set[str] = set()
    infos: list[dict[str, str]] = []
    for typed_assertion in pass3_result.typed_assertions:
        event = typed_assertion.assertion.event
        evidence = event.evidence_span
        for participant in event.participants:
            name = participant.entity.name
            if name in seen:
                continue
            seen.add(name)
            # Use refined type from entity_refinements if available
            refined_type = participant.entity.coarse_type
            for ref in typed_assertion.entity_refinements:
                if ref.entity_name == name:
                    refined_type = ref.refined_type
                    break
            infos.append(
                {
                    "name": name,
                    "sumo_type": refined_type,
                    "evidence_span": evidence[:200],
                }
            )
    return infos


def _parse_anaphor_response(
    raw_content: str,
    flagged_names: list[str],
    canonical_names: list[str],
    model: str,
    total_cost: float,
) -> tuple[list[AnaphorResolution], dict[str, str | None]]:
    """Parse the LLM anaphor resolution response.

    Returns ``(resolutions, partial_map)`` where ``partial_map`` maps each
    flagged name to its canonical resolution (or None to drop).

    Falls back gracefully: names not present in the response keep their
    original value (treated as uncertain).
    """
    content = _strip_markdown_fences(raw_content)
    partial_map: dict[str, str | None] = {}
    resolutions: list[AnaphorResolution] = []

    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        logger.error("Pass 4 anaphor response is not valid JSON: %.200s", content)
        return resolutions, partial_map

    if not isinstance(data, dict):
        logger.error("Pass 4 anaphor response is not a JSON object")
        return resolutions, partial_map

    canonical_set = set(canonical_names)

    for name in flagged_names:
        value = data.get(name)
        if value is None:
            # LLM did not include this name — leave uncertain
            continue

        if not isinstance(value, str):
            logger.warning("Pass 4 anaphor response: value for '%s' is not a string", name)
            continue

        value = value.strip()
        if value == "DROP":
            resolutions.append(
                AnaphorResolution(
                    original_name=name,
                    resolved_to=None,
                    confidence=0.8,
                    evidence="Flagged as descriptive phrase or unresolvable anaphor.",
                )
            )
            partial_map[name] = None
        elif value in canonical_set:
            resolutions.append(
                AnaphorResolution(
                    original_name=name,
                    resolved_to=value,
                    confidence=0.8,
                    evidence=f"Resolved anaphor '{name}' to canonical entity '{value}'.",
                )
            )
            partial_map[name] = value
        else:
            logger.warning(
                "Pass 4 anaphor resolution: '%s' resolved to '%s' which is not in canonical list",
                name,
                value,
            )
            # Accept it anyway — LLM may have picked a close variant
            resolutions.append(
                AnaphorResolution(
                    original_name=name,
                    resolved_to=value,
                    confidence=0.5,
                    evidence=f"Resolved to '{value}' (not in canonical list — check manually).",
                )
            )
            partial_map[name] = value

    return resolutions, partial_map


def _parse_merge_response(
    raw_content: str,
    candidate_groups: list[list[dict[str, str]]],
) -> list[MergeDecision]:
    """Parse the LLM merge response and return MergeDecision objects.

    Only returns decisions with verdict == "same" and confidence >= 0.80.
    """
    content = _strip_markdown_fences(raw_content)
    decisions: list[MergeDecision] = []

    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        logger.error("Pass 4 merge response is not valid JSON: %.200s", content)
        return decisions

    if not isinstance(data, list):
        logger.error("Pass 4 merge response is not a JSON array")
        return decisions

    for i, item in enumerate(data):
        if i >= len(candidate_groups):
            break
        if not isinstance(item, dict):
            continue
        verdict = item.get("verdict", "")
        confidence = float(item.get("confidence", 0.0))
        canonical = item.get("canonical", "")
        evidence = item.get("evidence", "")

        if verdict == "same" and confidence >= 0.80 and isinstance(canonical, str) and canonical:
            group = candidate_groups[i]
            aliases = [e["name"] for e in group if e["name"] != canonical]
            if aliases:
                decisions.append(
                    MergeDecision(
                        canonical_name=canonical,
                        aliases=aliases,
                        confidence=confidence,
                        evidence=evidence if isinstance(evidence, str) else "",
                    )
                )

    return decisions


def _build_normalization_map(
    anaphor_resolutions: list[AnaphorResolution],
    merge_decisions: list[MergeDecision],
    flagged_names: set[str],
) -> dict[str, str | None]:
    """Build the consolidated normalization map from resolutions and merges.

    Priority: anaphor resolutions take precedence over merge decisions.
    The map covers:
    - Resolved anaphors: name → canonical (or None to drop)
    - Merge aliases: alias → canonical_name
    - Flagged names not resolved: not included (kept as-is)
    """
    norm_map: dict[str, str | None] = {}

    # Apply merge decisions first (lower priority)
    for decision in merge_decisions:
        for alias in decision.aliases:
            norm_map[alias] = decision.canonical_name

    # Apply anaphor resolutions (higher priority — overwrite merges)
    for resolution in anaphor_resolutions:
        norm_map[resolution.original_name] = resolution.resolved_to

    return norm_map


def _apply_normalization_to_event(
    event: Pass1Event,
    norm_map: dict[str, str | None],
) -> Pass1Event | None:
    """Apply the normalization map to a single Pass1Event.

    Rewrites participant entity names using the map.  Participants whose
    name maps to None are removed.  Returns None if the event has no
    participants left after normalization.
    """
    new_participants: list[Pass1Participant] = []
    for participant in event.participants:
        original_name = participant.entity.name
        if original_name not in norm_map:
            # Not in map — keep unchanged
            new_participants.append(participant)
            continue

        target = norm_map[original_name]
        if target is None:
            # Drop this participant
            continue

        if target == original_name:
            # No change needed
            new_participants.append(participant)
            continue

        # Rewrite entity name
        new_entity = Pass1Entity(
            name=target,
            coarse_type=participant.entity.coarse_type,
            context=participant.entity.context,
        )
        new_participant = Pass1Participant(
            proto_role=participant.proto_role,
            entity=new_entity,
            resolution_status="resolved",
            resolved_from=original_name,
        )
        new_participants.append(new_participant)

    if not new_participants:
        return None  # drop empty event

    return Pass1Event(
        relationship_verb=event.relationship_verb,
        participants=new_participants,
        evidence_span=event.evidence_span,
        confidence=event.confidence,
        claim_level=event.claim_level,
    )


def _apply_normalization_to_pass3(
    pass3_result: Pass3Result,
    norm_map: dict[str, str | None],
) -> Pass3Result:
    """Rewrite all events in a Pass3Result using the normalization map.

    Updates Pass3TypedAssertion.assertion.event for every typed assertion.
    Assertions whose events become empty (all participants dropped) are
    removed from the result.
    """
    if not norm_map:
        return pass3_result

    new_typed_assertions: list[Pass3TypedAssertion] = []

    for typed_assertion in pass3_result.typed_assertions:
        assertion = typed_assertion.assertion
        old_event = assertion.event

        new_event = _apply_normalization_to_event(old_event, norm_map)
        if new_event is None:
            logger.info(
                "Pass 4: dropping assertion (predicate=%s) — all participants removed",
                assertion.predicate_id,
            )
            continue

        # Rebuild the assertion with the normalized event.
        # Entries where norm_map maps to None (dropped) are excluded from
        # mapped_roles entirely — the `or entity_name` fallback would
        # re-insert dropped names, so we filter explicitly.
        new_assertion = Pass2MappedAssertion(
            event=new_event,
            predicate_id=assertion.predicate_id,
            propbank_sense_id=assertion.propbank_sense_id,
            process_type=assertion.process_type,
            mapped_roles={
                role: cast(str, resolved)
                for role, entity_name in assertion.mapped_roles.items()
                if (resolved := norm_map.get(entity_name, entity_name)) is not None
            },
            disambiguation_method=assertion.disambiguation_method,
            mapping_confidence=assertion.mapping_confidence,
        )
        new_typed_assertions.append(
            Pass3TypedAssertion(
                assertion=new_assertion,
                entity_refinements=typed_assertion.entity_refinements,
            )
        )

    # Rebuild Pass3Result with updated typed_assertions
    return Pass3Result(
        typed_assertions=new_typed_assertions,
        source_pass2=pass3_result.source_pass2,
        model=pass3_result.model,
        cost=pass3_result.cost,
        trace_id=pass3_result.trace_id,
        leaf_early_exit_count=pass3_result.leaf_early_exit_count,
        subtree_pick_count=pass3_result.subtree_pick_count,
        no_constraint_count=pass3_result.no_constraint_count,
    )


def _normalize_pass2_unresolved(
    pass2_result: Pass2Result,
    norm_map: dict[str, str | None],
) -> Pass2Result:
    """Apply normalization (plus anaphor detection) to Pass 2 unresolved events.

    Entities in unresolved events are not seen by Pass 4's main normalization
    loop (which only processes Pass 3 typed assertions).  This function:
    1. Collects entity names from unresolved events that are not already in the
       norm_map.
    2. Runs ``_is_anaphor`` on each and adds certain anaphors (resolved_to=None)
       to an extended copy of the norm_map.
    3. Applies the extended map to filter participants from each unresolved
       event; events with zero participants remaining are dropped.
    4. Returns a new Pass2Result with the filtered unresolved list.
    """
    # Step 1: find names in unresolved events not already covered by norm_map
    extended_map = dict(norm_map)
    seen: set[str] = set()
    for event in pass2_result.unresolved:
        for participant in event.participants:
            name = participant.entity.name
            if name in seen or name in extended_map:
                continue
            seen.add(name)
            is_anaphor, is_certain, _reason = _is_anaphor(name)
            if is_anaphor and is_certain:
                extended_map[name] = None
                logger.info(
                    "Pass 4 (unresolved): deterministic drop '%s' (%s)",
                    name,
                    _reason,
                )

    if not extended_map:
        return pass2_result

    # Step 2: apply map to unresolved events
    normalized_unresolved: list[Pass1Event] = []
    for event in pass2_result.unresolved:
        new_event = _apply_normalization_to_event(event, extended_map)
        if new_event is not None:
            normalized_unresolved.append(new_event)

    if len(normalized_unresolved) == len(pass2_result.unresolved):
        return pass2_result  # nothing changed

    dropped = len(pass2_result.unresolved) - len(normalized_unresolved)
    logger.info(
        "Pass 4 (unresolved): dropped %d/%d unresolved events after normalization",
        dropped,
        len(pass2_result.unresolved),
    )

    return Pass2Result(
        mapped=pass2_result.mapped,
        unresolved=normalized_unresolved,
        source_pass1=pass2_result.source_pass1,
        model=pass2_result.model,
        cost=pass2_result.cost,
        trace_id=pass2_result.trace_id,
        single_sense_count=pass2_result.single_sense_count,
        llm_disambiguated_count=pass2_result.llm_disambiguated_count,
        unresolved_count=len(normalized_unresolved),
    )


async def run_pass4_normalization(
    pass3_result: Pass3Result,
    *,
    source_text: str = "",
    model: str | None = None,
    task: str = "progressive_extraction",
    trace_id: str,
    max_budget: float = 0.045,
    _llm_api: _LLMClientAPI | None = None,
) -> tuple[Pass4NormalizationResult, Pass3Result]:
    """Run Pass 4: entity normalization (anaphor resolution + near-duplicate merging).

    Detects and resolves four categories of problematic entity names:
    1. Anaphors and pronouns ("the group", "it", "they") → resolve to named entity or drop.
    2. Descriptive noun phrases (not real entities) → drop.
    3. Text-declared alias pairs ("Islamic Revolutionary Guard Corps (IRGC)") →
       deterministic merge without LLM, zero cost.
    4. Near-duplicates by string heuristics or structural fingerprint → LLM merge verifier.

    The LLM merge verifier uses a profile-aware prompt that includes per-entity top-3
    assertions, alias hints, co-participant overlap, and detection method label.

    Parameters
    ----------
    pass3_result:
        The Pass 3 typed assertion result to normalize.
    source_text:
        Optional raw source text used for alias extraction.  When non-empty, parenthetical
        alias patterns ("Full Name (ACRONYM)") are detected deterministically.
    model:
        LLM model identifier.  Defaults to ``gemini/gemini-2.5-flash-lite``.
    task:
        Task tag for ``llm_client`` observability.
    trace_id:
        Trace ID for ``llm_client`` observability.
    max_budget:
        Maximum spend in USD for all Pass 4 LLM calls.
    _llm_api:
        Override for the llm_client API handle (testing only).

    Returns
    -------
    Tuple of (Pass4NormalizationResult, normalized_Pass3Result).
    """
    api = _llm_api or _load_llm_client_api()
    effective_model = model or _DEFAULT_MODEL
    total_cost = 0.0

    # Collect entity infos from Pass 3
    entity_infos = _collect_entity_infos(pass3_result)
    entity_names_set = {info["name"] for info in entity_infos}

    # Step 0: Extract text-declared alias pairs (deterministic, no LLM cost)
    alias_pairs: list[AliasPair] = []
    alias_non_canonicals: set[str] = set()
    if source_text:
        alias_pairs = extract_alias_pairs(source_text, entity_names_set)
        for ap in alias_pairs:
            alias_non_canonicals.add(ap.short_form)
        if alias_pairs:
            logger.info(
                "Pass 4: %d text-declared alias pairs detected (trace_id=%s)",
                len(alias_pairs),
                trace_id,
            )

    # Step 1: Detect anaphors / descriptive phrases.
    # Certain anaphors (pronouns, bare generics, possessives, demonstratives)
    # are dropped immediately without an LLM call.  Uncertain anaphors
    # (article+generic, long phrases, verb phrases) go to the LLM for review.
    flagged: list[dict[str, str]] = []
    canonical_names: list[str] = []
    anaphor_resolutions: list[AnaphorResolution] = []
    merge_decisions: list[MergeDecision] = []
    for info in entity_infos:
        is_anaphoric, is_certain, reason = _is_anaphor(info["name"])
        if is_anaphoric and is_certain:
            # Deterministic drop — no LLM needed
            anaphor_resolutions.append(
                AnaphorResolution(
                    original_name=info["name"],
                    resolved_to=None,
                    confidence=1.0,
                    evidence=f"Deterministic rule: {reason}",
                )
            )
        elif is_anaphoric:
            flagged.append({
                "name": info["name"],
                "flag_reason": reason,
                "evidence_span": info["evidence_span"],
            })
        else:
            canonical_names.append(info["name"])

    # Step 2: String heuristic near-dup detection.
    # Exclude alias non-canonicals (short forms) — they're already resolved.
    canonical_infos = [
        info for info in entity_infos
        if info["name"] in canonical_names and info["name"] not in alias_non_canonicals
    ]
    string_dup_pairs = detect_near_duplicate_pairs(canonical_infos)

    # Step 2b: Structural fingerprint deduplication (predicate-role Jaccard ≥ 0.35).
    profiles = compute_entity_profiles(pass3_result, {info["name"] for info in canonical_infos})
    structural_pairs = detect_structural_duplicate_pairs(canonical_infos, profiles)

    # Union string + structural pairs, dedup by entity-name frozenset, annotate detection_method.
    seen_pair_keys: set[frozenset[str]] = set()
    annotated_pairs: list[tuple[dict[str, str], dict[str, str], str]] = []
    for pair_a, pair_b in string_dup_pairs:
        key: frozenset[str] = frozenset({pair_a["name"], pair_b["name"]})
        if key not in seen_pair_keys:
            seen_pair_keys.add(key)
            annotated_pairs.append((pair_a, pair_b, "string_heuristic"))
    for pair_a, pair_b in structural_pairs:
        key = frozenset({pair_a["name"], pair_b["name"]})
        if key not in seen_pair_keys:
            seen_pair_keys.add(key)
            annotated_pairs.append((pair_a, pair_b, "structural_fingerprint"))

    logger.info(
        "Pass 4: %d flagged anaphors, %d string pairs, %d structural pairs, "
        "%d total dup pairs (trace_id=%s)",
        len(flagged),
        len(string_dup_pairs),
        len(structural_pairs),
        len(annotated_pairs),
        trace_id,
    )

    # Build assertion index for profile-aware merge prompt (top-3 per entity).
    assertion_index: dict[str, list[dict[str, Any]]] = {}
    for ta in pass3_result.typed_assertions:
        a = ta.assertion
        for entity_name in a.mapped_roles.values():
            if entity_name not in assertion_index:
                assertion_index[entity_name] = []
            if len(assertion_index[entity_name]) < 3:
                assertion_index[entity_name].append({
                    "predicate_id": a.predicate_id,
                    "participants": list(a.mapped_roles.values()),
                    "evidence_span": a.event.evidence_span[:100],
                })

    # Build alias hints map: entity_name -> list of "short ↔ long" strings.
    alias_hints_map: dict[str, list[str]] = {}
    for ap in alias_pairs:
        for name in (ap.short_form, ap.long_form):
            if name not in alias_hints_map:
                alias_hints_map[name] = []
            alias_hints_map[name].append(f"{ap.short_form} ↔ {ap.long_form}")

    flagged_names_set: set[str] = {item["name"] for item in flagged}

    # Step 3: LLM anaphor resolution (single batched call)
    if flagged and total_cost < max_budget:
        evidence_spans = [item["evidence_span"] for item in flagged if item["evidence_span"]]
        source_excerpt = " ... ".join(evidence_spans[:5])[:500]

        template_vars: dict[str, Any] = {
            "source_text_excerpt": source_excerpt or "(no excerpt available)",
            "canonical_names": canonical_names,
            "flagged_items": flagged,
        }
        messages = api.render_prompt(_PASS4_ANAPHOR_PROMPT, **template_vars)

        try:
            result = await api.acall_llm(
                effective_model,
                messages,
                task=task,
                trace_id=trace_id,
                max_budget=max_budget - total_cost,
            )
            call_cost: float = result.cost or 0.0
            total_cost += call_cost
            raw_content: str = result.content or ""

            resolutions, _ = _parse_anaphor_response(
                raw_content,
                [item["name"] for item in flagged],
                canonical_names,
                effective_model,
                total_cost,
            )
            anaphor_resolutions.extend(resolutions)

        except Exception:
            logger.error(
                "Pass 4 anaphor resolution LLM call failed (trace_id=%s)",
                trace_id,
                exc_info=True,
            )

    # Step 4: LLM near-duplicate merging (batch in groups of up to 10 pairs).
    _MERGE_BATCH_SIZE = 10
    pair_batches: list[list[tuple[list[dict[str, str]], str]]] = []
    batch: list[tuple[list[dict[str, str]], str]] = []
    for pair_a, pair_b, detection_method in annotated_pairs:
        if total_cost >= max_budget:
            logger.info(
                "Pass 4: budget exhausted before merge step (cost=$%.4f, budget=$%.4f)",
                total_cost,
                max_budget,
            )
            break
        batch.append(([pair_a, pair_b], detection_method))
        if len(batch) >= _MERGE_BATCH_SIZE:
            pair_batches.append(batch)
            batch = []
    if batch:
        pair_batches.append(batch)

    for batch_items in pair_batches:
        if total_cost >= max_budget:
            break
        # batch_items: list[tuple[list[dict], str]]  (group_entities, detection_method)
        batch_groups = [group for group, _ in batch_items]  # for _parse_merge_response compat
        template_vars_merge: dict[str, Any] = {
            "candidate_groups": [
                {
                    "detection_method": dm,
                    "co_participants": _compute_co_participants(
                        group[0]["name"], group[1]["name"], assertion_index
                    ),
                    "entities": [
                        {
                            "name": e["name"],
                            "sumo_type": e["sumo_type"],
                            "evidence_span": e["evidence_span"][:150],
                            "assertions": assertion_index.get(e["name"], [])[:3],
                            "alias_hints": alias_hints_map.get(e["name"], []),
                        }
                        for e in group
                    ],
                }
                for group, dm in batch_items
            ],
        }
        messages_merge = api.render_prompt(_PASS4_MERGE_PROMPT, **template_vars_merge)

        try:
            merge_result = await api.acall_llm(
                effective_model,
                messages_merge,
                task=task,
                trace_id=trace_id,
                max_budget=max_budget - total_cost,
            )
            merge_cost: float = merge_result.cost or 0.0
            total_cost += merge_cost
            merge_content: str = merge_result.content or ""

            batch_decisions = _parse_merge_response(merge_content, batch_groups)
            merge_decisions.extend(batch_decisions)

        except Exception:
            logger.error(
                "Pass 4 merge LLM call failed (trace_id=%s)",
                trace_id,
                exc_info=True,
            )

    # Step 5: Build consolidated normalization map.
    norm_map = _build_normalization_map(anaphor_resolutions, merge_decisions, flagged_names_set)
    # Apply alias pairs at lowest priority (don't overwrite anaphor/merge decisions).
    for ap in alias_pairs:
        if ap.short_form not in norm_map:
            norm_map[ap.short_form] = ap.long_form

    logger.info(
        "Pass 4 complete: %d anaphor resolutions, %d merge decisions, %d alias pairs, "
        "%d normalization entries (trace_id=%s, cost=$%.4f)",
        len(anaphor_resolutions),
        len(merge_decisions),
        len(alias_pairs),
        len(norm_map),
        trace_id,
        total_cost,
    )

    pass4_result = Pass4NormalizationResult(
        anaphor_resolutions=anaphor_resolutions,
        merge_decisions=merge_decisions,
        alias_pairs=alias_pairs,
        normalization_map=norm_map,
        cost_usd=total_cost,
        model=effective_model,
    )

    # Step 6: Apply normalization map to Pass 3 result.
    normalized_pass3 = _apply_normalization_to_pass3(pass3_result, norm_map)

    return pass4_result, normalized_pass3


# ---------------------------------------------------------------------------
# Pipeline Orchestrator (Slice E)
# ---------------------------------------------------------------------------


class ProgressiveExtractionError(RuntimeError):
    """Raised when the progressive extraction pipeline fails.

    Wraps the underlying exception with context about which pass
    failed and the trace ID for debugging.
    """


_CHUNK_TARGET_CHARS = 3000
"""Target chunk size in characters for Pass 1 text splitting."""

_CHUNK_OVERLAP_CHARS = 200
"""Overlap between adjacent chunks to avoid losing context at boundaries."""


def _chunk_text(
    text: str,
    *,
    target_chars: int = _CHUNK_TARGET_CHARS,
    overlap_chars: int = _CHUNK_OVERLAP_CHARS,
) -> list[str]:
    """Split *text* into chunks on paragraph boundaries.

    Splits on double-newlines first, then single newlines if a paragraph
    exceeds *target_chars*.  Adjacent chunks share *overlap_chars* of
    trailing/leading text so entity references near boundaries aren't lost.

    Returns at least one chunk (the full text) when it is short enough.
    """
    if len(text) <= target_chars:
        return [text]

    paragraphs = text.split("\n\n")
    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    for para in paragraphs:
        para_len = len(para) + 2  # account for the \n\n we stripped
        if current and current_len + para_len > target_chars:
            chunk_text = "\n\n".join(current)
            chunks.append(chunk_text)
            # Overlap: keep last paragraph(s) up to overlap_chars
            overlap: list[str] = []
            overlap_len = 0
            for p in reversed(current):
                if overlap_len + len(p) > overlap_chars:
                    break
                overlap.insert(0, p)
                overlap_len += len(p)
            current = overlap + [para]
            current_len = overlap_len + para_len
        else:
            current.append(para)
            current_len += para_len

    if current:
        chunks.append("\n\n".join(current))

    return chunks if chunks else [text]


def _merge_pass1_results(results: list[Pass1Result]) -> Pass1Result:
    """Merge Pass 1 results from multiple text chunks.

    Concatenates events, deduplicates entities by ``(name, coarse_type)``,
    combines hashes and costs.
    """
    all_events: list[Pass1Event] = []
    seen_entities: dict[tuple[str, str], Pass1Entity] = {}
    total_cost = 0.0
    hashes: list[str] = []
    model = results[0].model if results else "unknown"
    trace_id = results[0].trace_id if results else "unknown"

    for result in results:
        all_events.extend(result.events)
        for entity in result.entities:
            key = (entity.name, entity.coarse_type)
            if key not in seen_entities:
                seen_entities[key] = entity
        total_cost += result.cost
        hashes.append(result.source_text_hash)

    combined_hash = hashlib.sha256("|".join(hashes).encode()).hexdigest()[:16]

    return Pass1Result(
        events=all_events,
        entities=list(seen_entities.values()),
        source_text_hash=combined_hash,
        model=model,
        cost=total_cost,
        trace_id=trace_id,
    )


async def run_progressive_extraction(
    text: str,
    *,
    sumo_db_path: Path,
    model: str | None = None,
    task: str = "progressive_extraction",
    trace_id: str | None = None,
    max_budget: float = 0.30,
    max_triples: int = 50,
    chunk_target_chars: int = _CHUNK_TARGET_CHARS,
    _llm_api: _LLMClientAPI | None = None,
) -> ProgressiveExtractionReport:
    """Run the full 3-pass progressive extraction pipeline.

    Pass 1: Extract entities and relationships with coarse SUMO types.
            Long texts are split into ~3000-char chunks on paragraph
            boundaries and processed independently, then merged.
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

    # Budget allocation: 34% pass 1, 25.5% pass 2, 25.5% pass 3, 15% pass 4.
    budget_pass1 = max_budget * 0.34
    budget_pass2 = max_budget * 0.255
    budget_pass3 = max_budget * 0.255
    budget_pass4 = max_budget * 0.15

    # --- Pass 1 (chunked) ---
    chunks = _chunk_text(text, target_chars=chunk_target_chars)
    logger.info(
        "Pass 1: splitting text (%d chars) into %d chunks (target=%d)",
        len(text), len(chunks), chunk_target_chars,
    )

    chunk_results: list[Pass1Result] = []
    per_chunk_budget = budget_pass1 / max(len(chunks), 1)
    multi_chunk = len(chunks) > 1
    for i, chunk in enumerate(chunks):
        chunk_trace = (
            f"{effective_trace_id}_chunk{i}" if multi_chunk
            else effective_trace_id
        )
        try:
            chunk_result = await run_pass1(
                chunk,
                model=effective_model,
                task=task,
                trace_id=chunk_trace,
                max_budget=per_chunk_budget,
                max_triples=max_triples,
                _llm_api=_llm_api,
            )
            chunk_results.append(chunk_result)
        except Exception as exc:
            logger.warning(
                "Pass 1 chunk %d/%d failed (trace_id=%s): %s",
                i + 1, len(chunks), effective_trace_id, exc,
            )
            # Continue with remaining chunks — permissive extraction.

    if not chunk_results:
        raise ProgressiveExtractionError(
            f"Pass 1 failed on all {len(chunks)} chunks "
            f"(trace_id={effective_trace_id})"
        )

    if multi_chunk:
        pass1_result = _merge_pass1_results(chunk_results)
        # Restore base trace_id on the merged result.
        pass1_result = Pass1Result(
            events=pass1_result.events,
            entities=pass1_result.entities,
            source_text_hash=pass1_result.source_text_hash,
            model=pass1_result.model,
            cost=pass1_result.cost,
            trace_id=effective_trace_id,
        )
    else:
        pass1_result = chunk_results[0]

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

    # --- Pass 4: Entity Normalization ---
    # Use a separate trace_id suffix so llm_client's per-trace budget counter
    # starts at $0 for Pass 4.  Passes 1-3 already spent their budgets on the
    # main trace; re-using the same trace_id would immediately trigger the
    # budget guard even though Pass 4 has its own allocation.
    pass4_trace_id = effective_trace_id + "_pass4"
    pass4_result: Pass4NormalizationResult | None = None
    try:
        pass4_result, pass3_result = await run_pass4_normalization(
            pass3_result,
            source_text=text,
            model=effective_model,
            task=task,
            trace_id=pass4_trace_id,
            max_budget=budget_pass4,
            _llm_api=_llm_api,
        )
    except Exception:
        logger.error(
            "Pass 4 normalization failed (trace_id=%s) — continuing without normalization",
            effective_trace_id,
            exc_info=True,
        )

    # Also normalize pass2 unresolved events — entities there bypass Pass 4's
    # entity collection (which only reads pass3 typed assertions).
    if pass4_result is not None:
        pass2_result = _normalize_pass2_unresolved(
            pass2_result, pass4_result.normalization_map
        )

    # --- Aggregate ---
    pass4_cost = pass4_result.cost_usd if pass4_result is not None else 0.0
    total_cost = pass1_result.cost + pass2_result.cost + pass3_result.cost + pass4_cost

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
        pass4=pass4_result,
        total_cost=total_cost,
        trace_id=effective_trace_id,
        model=effective_model,
        triples_extracted=len(pass1_result.events),
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
    chunk_target_chars: int = _CHUNK_TARGET_CHARS,
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
            chunk_target_chars=chunk_target_chars,
            _llm_api=_llm_api,
        )
    )

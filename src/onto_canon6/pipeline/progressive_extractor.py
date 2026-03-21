"""Progressive disclosure extraction — Pass 1: open extraction with SUMO seeding.

Extracts entities and relationships from raw text, assigning coarse SUMO
types from the ~50 top-level type list.  All LLM calls go through
``llm_client`` with mandatory ``task=``, ``trace_id=``, and ``max_budget=``
kwargs.

The prompt template is a YAML/Jinja2 file loaded via
``llm_client.render_prompt()``.  No f-string prompts in Python.

This module implements Plan 0018, Slice B.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
from dataclasses import dataclass
from importlib import import_module
from typing import Any, Callable, Protocol, cast

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from onto_canon6.evaluation.fidelity_experiment import TOP_LEVEL_TYPES

from .progressive_types import Pass1Entity, Pass1Result, Pass1Triple

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

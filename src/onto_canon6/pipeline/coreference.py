"""Post-extraction coreference resolution for entity and propositional mentions.

This module resolves two classes of coreference that the extraction pipeline
produces as separate entries:

1. **Entity coreference**: Different surface forms referring to the same
   real-world entity (e.g., "a Kurdish militia" and "the militia") are merged
   under a single canonical name.

2. **Propositional coreference**: Anaphoric references to propositions
   (e.g., "these claims" in "Turkey disputed these claims") are resolved to
   the actual propositional content from the source text.

Both resolvers use LLM calls via ``llm_client`` with mandatory ``task=``,
``trace_id=``, and ``max_budget=`` kwargs. Prompt templates are YAML/Jinja2
files loaded via ``llm_client.render_prompt()``.

This module is opt-in — callers must explicitly invoke ``resolve_coreferences``
or the individual resolvers. The pipeline does not run coreference by default.
"""

from __future__ import annotations

import json
import logging
import re
import uuid as _uuid
from dataclasses import dataclass
from importlib import import_module
from typing import Any, Protocol, cast

from pydantic import BaseModel, ConfigDict, Field

from .text_extraction import ExtractedCandidate, ExtractedFiller

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Prompt template paths (relative to repo root, loaded by render_prompt)
# ---------------------------------------------------------------------------

_ENTITY_COREF_PROMPT = "prompts/coreference/entity_coref.yaml"
_PROPOSITIONAL_COREF_PROMPT = "prompts/coreference/propositional_coref.yaml"

# Default model — same as progressive extractor
_DEFAULT_MODEL = "gemini/gemini-2.5-flash-lite"

# Minimum entity count to justify an LLM coreference call
_MIN_ENTITIES_FOR_COREF = 3

# Patterns that indicate a vague propositional reference
_VAGUE_REFERENCE_PATTERNS = re.compile(
    r"^(these|those|this|that|the|such)\s+"
    r"(claims?|allegations?|assertions?|statements?|assessment|"
    r"findings?|accusations?|reports?|arguments?|demands?|proposals?|"
    r"positions?|views?)$",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# llm_client API boundary (lazy loaded, testable via dependency injection)
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
    """Lazily import llm_client and return a typed API handle."""
    module = import_module("llm_client")
    return _LLMClientAPI(
        render_prompt=cast(_RenderPrompt, getattr(module, "render_prompt")),
        acall_llm=cast(_ACallLLM, getattr(module, "acall_llm")),
    )


# ---------------------------------------------------------------------------
# Response schemas for structured output
# ---------------------------------------------------------------------------


class CorefGroup(BaseModel):
    """One group of coreferent entity mentions."""

    model_config = ConfigDict(extra="ignore")

    canonical_name: str = Field(
        description=(
            "The most specific or informative name for this entity. "
            "Prefer full names over abbreviations, specific descriptors "
            "over generic ones."
        ),
    )
    surface_forms: list[str] = Field(
        description="All surface forms that refer to this entity, including the canonical name.",
    )


class EntityCorefResponse(BaseModel):
    """LLM response for entity coreference resolution."""

    model_config = ConfigDict(extra="ignore")

    groups: list[CorefGroup] = Field(
        default_factory=list,
        description="Groups of coreferent entity mentions.",
    )


class ResolvedReference(BaseModel):
    """One resolved propositional reference."""

    model_config = ConfigDict(extra="ignore")

    index: int = Field(description="1-based index of the vague reference from the input list.")
    resolved_text: str = Field(
        description="The specific proposition being referenced, or the original text if unresolvable.",
    )


class PropCorefResponse(BaseModel):
    """LLM response for propositional coreference resolution."""

    model_config = ConfigDict(extra="ignore")

    resolutions: list[ResolvedReference] = Field(
        default_factory=list,
        description="Resolved propositional references.",
    )


# ---------------------------------------------------------------------------
# json_schema response formats
# ---------------------------------------------------------------------------


def _entity_coref_response_format() -> dict[str, Any]:
    """Build the ``json_schema`` response_format for entity coreference."""
    return {
        "type": "json_schema",
        "json_schema": {
            "name": "entity_coreference",
            "schema": EntityCorefResponse.model_json_schema(),
        },
    }


def _prop_coref_response_format() -> dict[str, Any]:
    """Build the ``json_schema`` response_format for propositional coreference."""
    return {
        "type": "json_schema",
        "json_schema": {
            "name": "propositional_coreference",
            "schema": PropCorefResponse.model_json_schema(),
        },
    }


# ---------------------------------------------------------------------------
# Entity name collection helpers
# ---------------------------------------------------------------------------


def _collect_entity_names(candidates: list[ExtractedCandidate]) -> list[str]:
    """Extract all unique entity filler names from candidates, preserving order."""
    seen: set[str] = set()
    names: list[str] = []
    for candidate in candidates:
        for fillers in candidate.roles.values():
            for filler in fillers:
                if filler.kind == "entity" and filler.name:
                    normalized = filler.name.strip()
                    if normalized and normalized not in seen:
                        seen.add(normalized)
                        names.append(normalized)
    return names


def _build_entity_merge_map(groups: list[CorefGroup]) -> dict[str, str]:
    """Build a mapping from each surface form to its canonical name.

    Only includes entries where the surface form differs from the canonical.
    """
    merge_map: dict[str, str] = {}
    for group in groups:
        canonical = group.canonical_name.strip()
        if not canonical:
            continue
        for form in group.surface_forms:
            normalized_form = form.strip()
            if normalized_form and normalized_form != canonical:
                merge_map[normalized_form] = canonical
    return merge_map


def _apply_entity_merge(
    candidates: list[ExtractedCandidate],
    merge_map: dict[str, str],
) -> list[ExtractedCandidate]:
    """Return new candidates with entity names replaced per merge_map.

    ExtractedCandidate is frozen, so we reconstruct via model_copy.
    """
    if not merge_map:
        return candidates

    updated: list[ExtractedCandidate] = []
    merges_applied = 0
    for candidate in candidates:
        new_roles: dict[str, list[ExtractedFiller]] = {}
        changed = False
        for role_name, fillers in candidate.roles.items():
            new_fillers: list[ExtractedFiller] = []
            for filler in fillers:
                if (
                    filler.kind == "entity"
                    and filler.name
                    and filler.name.strip() in merge_map
                ):
                    canonical = merge_map[filler.name.strip()]
                    new_filler = filler.model_copy(update={"name": canonical})
                    new_fillers.append(new_filler)
                    changed = True
                    merges_applied += 1
                else:
                    new_fillers.append(filler)
            new_roles[role_name] = new_fillers
        if changed:
            updated.append(candidate.model_copy(update={"roles": new_roles}))
        else:
            updated.append(candidate)

    if merges_applied:
        logger.info(
            "entity coreference: applied %d name merges across %d candidates",
            merges_applied,
            len(candidates),
        )
    return updated


# ---------------------------------------------------------------------------
# Propositional reference detection helpers
# ---------------------------------------------------------------------------


@dataclass
class _VagueReference:
    """A detected vague propositional reference with its location."""

    candidate_idx: int
    role_name: str
    filler_idx: int
    vague_text: str
    predicate: str
    context: str


def _is_vague_reference(filler: ExtractedFiller) -> bool:
    """Check if a filler looks like a vague propositional reference."""
    # Check raw field for unknown fillers
    text = filler.raw or filler.name or ""
    text = text.strip()
    if not text:
        return True  # Empty content is vague
    return bool(_VAGUE_REFERENCE_PATTERNS.match(text))


def _find_vague_references(
    candidates: list[ExtractedCandidate],
) -> list[_VagueReference]:
    """Find all fillers that look like vague propositional references."""
    refs: list[_VagueReference] = []
    for c_idx, candidate in enumerate(candidates):
        for role_name, fillers in candidate.roles.items():
            for f_idx, filler in enumerate(fillers):
                # Only check non-entity fillers (propositions are typically
                # kind=unknown or kind=value)
                if filler.kind == "entity":
                    continue
                if _is_vague_reference(filler):
                    vague_text = (filler.raw or filler.name or "").strip()
                    context = ""
                    if candidate.evidence_spans:
                        context = candidate.evidence_spans[0].text
                    refs.append(
                        _VagueReference(
                            candidate_idx=c_idx,
                            role_name=role_name,
                            filler_idx=f_idx,
                            vague_text=vague_text,
                            predicate=candidate.predicate,
                            context=context,
                        )
                    )
    return refs


def _apply_propositional_resolutions(
    candidates: list[ExtractedCandidate],
    vague_refs: list[_VagueReference],
    resolutions: list[ResolvedReference],
) -> list[ExtractedCandidate]:
    """Apply resolved propositional text back into candidates.

    Returns new candidate list with vague references replaced by resolved text.
    """
    # Build resolution lookup: 1-based index -> resolved text
    resolution_map: dict[int, str] = {}
    for res in resolutions:
        resolved = res.resolved_text.strip()
        if resolved:
            resolution_map[res.index] = resolved

    if not resolution_map:
        return candidates

    # Build a per-candidate update plan: (candidate_idx, role_name, filler_idx) -> new text
    updates: dict[tuple[int, str, int], str] = {}
    for ref_idx, vague_ref in enumerate(vague_refs):
        one_based = ref_idx + 1
        if one_based in resolution_map:
            new_text = resolution_map[one_based]
            # Only update if the resolution is different from the vague text
            if new_text != vague_ref.vague_text:
                key = (vague_ref.candidate_idx, vague_ref.role_name, vague_ref.filler_idx)
                updates[key] = new_text

    if not updates:
        return candidates

    # Apply updates by reconstructing affected candidates
    result: list[ExtractedCandidate] = list(candidates)
    resolutions_applied = 0
    # Group updates by candidate index
    candidate_updates: dict[int, list[tuple[str, int, str]]] = {}
    for (c_idx, role_name, f_idx), new_text in updates.items():
        candidate_updates.setdefault(c_idx, []).append((role_name, f_idx, new_text))

    for c_idx, role_updates in candidate_updates.items():
        candidate = result[c_idx]
        new_roles: dict[str, list[ExtractedFiller]] = {
            k: list(v) for k, v in candidate.roles.items()
        }
        for role_name, f_idx, new_text in role_updates:
            if role_name in new_roles and f_idx < len(new_roles[role_name]):
                old_filler = new_roles[role_name][f_idx]
                update_fields: dict[str, Any] = {}
                if old_filler.raw is not None:
                    update_fields["raw"] = new_text
                if old_filler.name is not None:
                    update_fields["name"] = new_text
                # If both are None, set raw (the general-purpose field)
                if not update_fields:
                    update_fields["raw"] = new_text
                new_roles[role_name][f_idx] = old_filler.model_copy(update=update_fields)
                resolutions_applied += 1
        result[c_idx] = candidate.model_copy(update={"roles": new_roles})

    if resolutions_applied:
        logger.info(
            "propositional coreference: resolved %d vague references across %d candidates",
            resolutions_applied,
            len(candidates),
        )
    return result


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def resolve_entity_coreferences(
    candidates: list[ExtractedCandidate],
    *,
    source_text: str = "",
    model: str | None = None,
    task: str = "coreference_resolution",
    trace_id: str | None = None,
    max_budget: float = 0.10,
    _llm_api: _LLMClientAPI | None = None,
) -> list[ExtractedCandidate]:
    """Merge coreferent entity mentions across candidates.

    Uses an LLM pass to identify which entities refer to the same real-world
    entity, then merges their mentions under a single canonical name.

    Parameters
    ----------
    candidates:
        Extracted candidates from the pipeline.
    source_text:
        Original source text for disambiguation context.
    model:
        LLM model override. Falls back to module default.
    task:
        Observability task tag for llm_client.
    trace_id:
        Trace ID for observability. Auto-generated if absent.
    max_budget:
        Maximum spend in USD for this LLM call.
    _llm_api:
        Override for the llm_client API handle (testing only).

    Returns
    -------
    Updated list of ExtractedCandidate with coreferent entity names merged.
    """
    entity_names = _collect_entity_names(candidates)
    if len(entity_names) < _MIN_ENTITIES_FOR_COREF:
        logger.debug(
            "entity coreference skipped: only %d unique entities (min=%d)",
            len(entity_names),
            _MIN_ENTITIES_FOR_COREF,
        )
        return candidates

    api = _llm_api or _load_llm_client_api()
    effective_model = model or _DEFAULT_MODEL
    effective_trace_id = trace_id or f"coref-entity-{_uuid.uuid4().hex[:12]}"

    messages = api.render_prompt(
        _ENTITY_COREF_PROMPT,
        entity_names=entity_names,
        source_text=source_text,
    )

    try:
        result = await api.acall_llm(
            effective_model,
            messages,
            task=task,
            trace_id=effective_trace_id,
            max_budget=max_budget,
            response_format=_entity_coref_response_format(),
        )
        raw_content: str = result.content or ""
    except Exception:
        logger.error(
            "entity coreference LLM call failed (trace_id=%s)",
            effective_trace_id,
            exc_info=True,
        )
        return candidates

    # Parse response
    try:
        parsed = json.loads(raw_content)
        response = EntityCorefResponse.model_validate(parsed)
    except (json.JSONDecodeError, Exception):
        logger.error(
            "entity coreference response parse failed (trace_id=%s)",
            effective_trace_id,
            exc_info=True,
        )
        return candidates

    merge_map = _build_entity_merge_map(response.groups)
    if not merge_map:
        logger.debug("entity coreference: no merges needed")
        return candidates

    logger.info(
        "entity coreference: found %d merge mappings from %d groups (trace_id=%s)",
        len(merge_map),
        len(response.groups),
        effective_trace_id,
    )
    return _apply_entity_merge(candidates, merge_map)


async def resolve_propositional_coreferences(
    candidates: list[ExtractedCandidate],
    source_text: str,
    *,
    model: str | None = None,
    task: str = "coreference_resolution",
    trace_id: str | None = None,
    max_budget: float = 0.10,
    _llm_api: _LLMClientAPI | None = None,
) -> list[ExtractedCandidate]:
    """Resolve anaphoric references to propositions.

    When an entity stance references 'these claims' or 'this assessment',
    identify the actual proposition being referenced and fill in the content.

    Parameters
    ----------
    candidates:
        Extracted candidates from the pipeline.
    source_text:
        Original source text — required for propositional resolution.
    model:
        LLM model override. Falls back to module default.
    task:
        Observability task tag for llm_client.
    trace_id:
        Trace ID for observability. Auto-generated if absent.
    max_budget:
        Maximum spend in USD for this LLM call.
    _llm_api:
        Override for the llm_client API handle (testing only).

    Returns
    -------
    Updated list of ExtractedCandidate with vague references resolved.
    """
    vague_refs = _find_vague_references(candidates)
    if not vague_refs:
        logger.debug("propositional coreference: no vague references found")
        return candidates

    api = _llm_api or _load_llm_client_api()
    effective_model = model or _DEFAULT_MODEL
    effective_trace_id = trace_id or f"coref-prop-{_uuid.uuid4().hex[:12]}"

    # Build the vague reference list for the prompt
    vague_items = [
        {
            "predicate": ref.predicate,
            "vague_text": ref.vague_text,
            "context": ref.context,
        }
        for ref in vague_refs
    ]

    messages = api.render_prompt(
        _PROPOSITIONAL_COREF_PROMPT,
        source_text=source_text,
        vague_references=vague_items,
    )

    try:
        result = await api.acall_llm(
            effective_model,
            messages,
            task=task,
            trace_id=effective_trace_id,
            max_budget=max_budget,
            response_format=_prop_coref_response_format(),
        )
        raw_content: str = result.content or ""
    except Exception:
        logger.error(
            "propositional coreference LLM call failed (trace_id=%s)",
            effective_trace_id,
            exc_info=True,
        )
        return candidates

    # Parse response
    try:
        parsed = json.loads(raw_content)
        response = PropCorefResponse.model_validate(parsed)
    except (json.JSONDecodeError, Exception):
        logger.error(
            "propositional coreference response parse failed (trace_id=%s)",
            effective_trace_id,
            exc_info=True,
        )
        return candidates

    if not response.resolutions:
        logger.debug("propositional coreference: LLM returned no resolutions")
        return candidates

    logger.info(
        "propositional coreference: %d resolutions from LLM (trace_id=%s)",
        len(response.resolutions),
        effective_trace_id,
    )
    return _apply_propositional_resolutions(candidates, vague_refs, response.resolutions)


async def resolve_coreferences(
    candidates: list[ExtractedCandidate],
    source_text: str,
    *,
    model: str | None = None,
    task: str = "coreference_resolution",
    trace_id: str | None = None,
    max_budget: float = 0.20,
    _llm_api: _LLMClientAPI | None = None,
) -> list[ExtractedCandidate]:
    """Run both entity and propositional coreference resolution.

    This is the primary entry point for post-extraction coreference. It runs
    entity coreference first (to canonicalize names), then propositional
    coreference (to resolve anaphoric references).

    Parameters
    ----------
    candidates:
        Extracted candidates from the pipeline.
    source_text:
        Original source text — required for both resolution types.
    model:
        LLM model override.
    task:
        Observability task tag.
    trace_id:
        Trace ID. Auto-generated if absent.
    max_budget:
        Maximum total spend in USD, split across both calls.
    _llm_api:
        Override for the llm_client API handle (testing only).

    Returns
    -------
    Updated candidates with entity merges and propositional resolutions applied.
    """
    effective_trace_id = trace_id or f"coref-{_uuid.uuid4().hex[:12]}"
    half_budget = max_budget / 2.0

    shared_kwargs: dict[str, Any] = {
        "model": model,
        "task": task,
        "_llm_api": _llm_api,
    }

    candidates = await resolve_entity_coreferences(
        candidates,
        source_text=source_text,
        trace_id=f"{effective_trace_id}-entity",
        max_budget=half_budget,
        **shared_kwargs,
    )
    candidates = await resolve_propositional_coreferences(
        candidates,
        source_text,
        trace_id=f"{effective_trace_id}-prop",
        max_budget=half_budget,
        **shared_kwargs,
    )
    return candidates

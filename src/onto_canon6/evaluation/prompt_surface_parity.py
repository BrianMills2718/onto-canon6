"""Render and compare live vs prompt-eval extraction prompt surfaces.

This module exists for Plan 0041. The residual extraction blocker is no longer
"which prompt asset?" but "what exact prompt/context contract each path hands
to the model on the same full chunk?" The helper below renders both surfaces
through the real repo code paths and emits a compact diff without creating a
second extraction runtime.
"""

from __future__ import annotations

from dataclasses import dataclass
from difflib import unified_diff
from pathlib import Path
from typing import Any

from ..config import PromptEvalVariantConfig, get_config
from ..ontology_runtime import load_effective_profile
from ..pipeline import (
    ProfileRef,
    SourceArtifactRef,
    render_entity_type_catalog,
    render_predicate_catalog,
)
from .models import BenchmarkCase
from .prompt_eval_service import _format_case_input, _load_llm_client_api, _variant_render_context


@dataclass(frozen=True)
class PromptSurfaceComparison:
    """Compact comparison between the live and prompt-eval message surfaces."""

    live_messages: tuple[dict[str, str], ...]
    prompt_eval_template_messages: tuple[dict[str, str], ...]
    prompt_eval_effective_messages: tuple[dict[str, str], ...]
    prompt_eval_input_content: str
    live_prompt_template: str
    prompt_eval_prompt_template: str
    live_prompt_ref: str
    prompt_eval_prompt_ref: str
    system_equal: bool
    user_equal: bool
    system_diff: tuple[str, ...]
    user_diff: tuple[str, ...]

    def to_jsonable(self) -> dict[str, Any]:
        """Render the comparison in a deterministic JSON-safe shape."""

        return {
            "live_prompt_template": self.live_prompt_template,
            "prompt_eval_prompt_template": self.prompt_eval_prompt_template,
            "live_prompt_ref": self.live_prompt_ref,
            "prompt_eval_prompt_ref": self.prompt_eval_prompt_ref,
            "live_messages": list(self.live_messages),
            "prompt_eval_template_messages": list(self.prompt_eval_template_messages),
            "prompt_eval_effective_messages": list(self.prompt_eval_effective_messages),
            "prompt_eval_input_content": self.prompt_eval_input_content,
            "system_equal": self.system_equal,
            "user_equal": self.user_equal,
            "system_diff": list(self.system_diff),
            "user_diff": list(self.user_diff),
        }


def compare_prompt_surfaces(
    *,
    source_text: str,
    profile_id: str,
    profile_version: str,
    source_kind: str,
    source_ref: str,
    source_label: str | None,
    case_id: str,
    live_prompt_template: Path | None = None,
    live_prompt_ref: str | None = None,
    prompt_eval_prompt_template: Path | None = None,
    prompt_eval_prompt_ref: str | None = None,
    include_case_id_in_prompt_eval_input: bool | None = None,
    max_candidates_per_case: int = 10,
    max_evidence_spans_per_candidate: int = 1,
    extraction_goal: str | None = None,
) -> PromptSurfaceComparison:
    """Render both extraction surfaces and return a deterministic diff."""
    case = BenchmarkCase(
        case_id=case_id,
        profile=ProfileRef(profile_id=profile_id, profile_version=profile_version),
        source_artifact=SourceArtifactRef(
            source_kind=source_kind,
            source_ref=source_ref,
            source_label=source_label,
            content_text=source_text,
        ),
    )
    return compare_prompt_surfaces_for_case(
        case=case,
        live_prompt_template=live_prompt_template,
        live_prompt_ref=live_prompt_ref,
        prompt_eval_prompt_template=prompt_eval_prompt_template,
        prompt_eval_prompt_ref=prompt_eval_prompt_ref,
        include_case_id_in_prompt_eval_input=include_case_id_in_prompt_eval_input,
        max_candidates_per_case=max_candidates_per_case,
        max_evidence_spans_per_candidate=max_evidence_spans_per_candidate,
        extraction_goal=extraction_goal,
    )


def compare_prompt_surfaces_for_case(
    *,
    case: BenchmarkCase,
    live_prompt_template: Path | None = None,
    live_prompt_ref: str | None = None,
    prompt_eval_prompt_template: Path | None = None,
    prompt_eval_prompt_ref: str | None = None,
    include_case_id_in_prompt_eval_input: bool | None = None,
    max_candidates_per_case: int = 10,
    max_evidence_spans_per_candidate: int = 1,
    extraction_goal: str | None = None,
) -> PromptSurfaceComparison:
    """Render both extraction surfaces from one benchmark case."""

    config = get_config()
    llm_client_api = _load_llm_client_api()
    effective_goal = extraction_goal or config.extraction.default_extraction_goal
    include_case_id = (
        config.evaluation.prompt_experiment.include_case_id_in_input
        if include_case_id_in_prompt_eval_input is None
        else include_case_id_in_prompt_eval_input
    )
    if not effective_goal:
        raise ValueError("extraction_goal is required")

    profile_id = case.profile.profile_id
    profile_version = case.profile.profile_version
    source_text = case.source_artifact.content_text
    source_kind = case.source_artifact.source_kind
    source_ref = case.source_artifact.source_ref
    source_label = case.source_artifact.source_label
    profile = load_effective_profile(
        profile_id,
        profile_version,
        overlay_root=config.overlay_root(),
    )
    live_template = live_prompt_template or config.resolve_repo_path(
        "prompts/extraction/text_to_candidate_assertions_compact_v4.yaml"
    )
    prompt_eval_template = prompt_eval_prompt_template or config.resolve_repo_path(
        "prompts/extraction/prompt_eval_text_to_candidate_assertions_compact_operational_parity_v2.yaml"
    )
    live_ref = live_prompt_ref or "onto_canon6.extraction.text_to_candidate_assertions_compact_v4@1"
    prompt_eval_ref = (
        prompt_eval_prompt_ref
        or "onto_canon6.extraction.prompt_eval_text_to_candidate_assertions_compact_operational_parity@2"
    )

    live_messages = tuple(
        llm_client_api.render_prompt(
            live_template,
            profile_id=profile_id,
            profile_version=profile_version,
            predicate_catalog=render_predicate_catalog(
                profile,
                source_text=source_text,
                max_predicates=config.extraction.max_predicates_in_prompt,
            ),
            entity_type_catalog=render_entity_type_catalog(profile),
            max_candidates_per_case=max_candidates_per_case,
            max_evidence_spans_per_candidate=max_evidence_spans_per_candidate,
            extraction_goal=effective_goal,
            source_kind=source_kind,
            source_ref=source_ref,
            source_label=source_label,
            source_text=source_text,
        )
    )
    prompt_eval_input_content = _format_case_input(case, include_case_id=include_case_id)
    prompt_eval_template_messages = tuple(
        llm_client_api.render_prompt(
            prompt_eval_template,
            **_variant_render_context(
                shared_context={
                    "profile_id": profile_id,
                    "profile_version": profile_version,
                    "predicate_catalog": render_predicate_catalog(profile),
                    "entity_type_catalog": render_entity_type_catalog(profile),
                    "extraction_goal": effective_goal,
                    "source_text": "",
                    "source_kind": "",
                    "source_ref": "",
                    "source_label": "",
                },
                default_max_candidates_per_case=max_candidates_per_case,
                default_max_evidence_spans_per_candidate=max_evidence_spans_per_candidate,
                variant=_require_prompt_eval_variant("compact_operational_parity"),
            ),
            input=prompt_eval_input_content,
        )
    )
    prompt_eval_effective_messages = tuple(
        _substitute_input(prompt_eval_template_messages, prompt_eval_input_content)
    )

    live_system = _message_content(live_messages, 0)
    parity_system = _message_content(prompt_eval_effective_messages, 0)
    live_user = _message_content(live_messages, 1)
    parity_user = _message_content(prompt_eval_effective_messages, 1)

    return PromptSurfaceComparison(
        live_messages=live_messages,
        prompt_eval_template_messages=prompt_eval_template_messages,
        prompt_eval_effective_messages=prompt_eval_effective_messages,
        prompt_eval_input_content=prompt_eval_input_content,
        live_prompt_template=str(live_template),
        prompt_eval_prompt_template=str(prompt_eval_template),
        live_prompt_ref=live_ref,
        prompt_eval_prompt_ref=prompt_eval_ref,
        system_equal=live_system == parity_system,
        user_equal=live_user == parity_user,
        system_diff=_diff_strings(
            label_a="live_system",
            value_a=live_system,
            label_b="prompt_eval_system",
            value_b=parity_system,
        ),
        user_diff=_diff_strings(
            label_a="live_user",
            value_a=live_user,
            label_b="prompt_eval_user",
            value_b=parity_user,
        ),
    )


def _message_content(messages: tuple[dict[str, str], ...], index: int) -> str:
    """Return one message content or fail loudly if the shape drifted."""

    if len(messages) <= index:
        raise ValueError(f"expected message index {index}, found {len(messages)} messages")
    message = messages[index]
    content = message.get("content")
    if not isinstance(content, str):
        raise ValueError(f"message {index} is missing string content")
    return content


def _diff_strings(*, label_a: str, value_a: str, label_b: str, value_b: str) -> tuple[str, ...]:
    """Return a unified diff over two multiline prompt strings."""

    return tuple(
        unified_diff(
            value_a.splitlines(),
            value_b.splitlines(),
            fromfile=label_a,
            tofile=label_b,
            lineterm="",
        )
    )


def _require_prompt_eval_variant(name: str) -> PromptEvalVariantConfig:
    """Return one configured prompt-eval variant by name or fail loudly."""

    for variant in get_config().evaluation.prompt_experiment.variants:
        if variant.name == name:
            return variant
    raise ValueError(f"prompt-eval variant not found: {name}")


def _substitute_input(
    messages: tuple[dict[str, str], ...], content: str
) -> tuple[dict[str, str], ...]:
    """Match prompt_eval's runtime {input} substitution semantics exactly."""

    return tuple({**msg, "content": msg["content"].replace("{input}", content)} for msg in messages)


__all__ = [
    "PromptSurfaceComparison",
    "compare_prompt_surfaces",
    "compare_prompt_surfaces_for_case",
]

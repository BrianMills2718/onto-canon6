"""llm_client-backed raw-text extraction into candidate assertion imports.

This module is the first real Phase 4 producer integration in `onto-canon6`.
It deliberately stays narrow:

- input remains raw text plus source-artifact metadata;
- the extractor returns typed candidate-import records, not accepted facts;
- `llm_client` owns prompt rendering, model selection, structured output, and
  observability tags;
- the existing review pipeline remains the only place that persists candidate
  assertions and governance state.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from importlib import import_module
import json
import logging
from pathlib import Path
import re
from typing import Any, Mapping, Protocol, cast

from pydantic import BaseModel, ConfigDict, Field, JsonValue, model_validator

from ..config import ConfigError, get_config
from ..ontology_runtime import load_effective_profile
from ..ontology_runtime.loaders import LoadedProfile
from .models import (
    CandidateAssertionImport,
    CandidateSubmissionResult,
    EvidenceSpan,
    ProfileRef,
    SourceArtifactRef,
)
from .service import ReviewService

logger = logging.getLogger(__name__)


class ExtractionError(RuntimeError):
    """Raised when the text-extraction boundary fails."""


class ExtractedFiller(BaseModel):
    """Structured filler emitted by the extractor response model.

    Flat model with strong ``Field(description=...)`` on every field.  Field
    descriptions are the primary mechanism for correct structured output —
    they constrain LLM behavior at decode time.  Discriminated unions
    (``oneOf`` + ``discriminator``) are architecturally correct but current
    models cannot navigate them (produce empty roles).  This flat model
    achieves the same outcome via descriptions + post-parse validation.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: str = Field(
        min_length=1,
        description=(
            "Filler kind. MUST be one of: 'entity' (for named entities from source text), "
            "'value' (for concrete literals like strings, times, money), or 'unknown' (for raw untyped text)."
        ),
    )
    entity_type: str | None = Field(
        default=None,
        description="Entity type from the active entity-type catalog (e.g. oc:person, oc:military_organization).",
    )
    name: str | None = Field(
        default=None,
        description="Exact surface form from the source text.",
    )
    entity_id: str | None = Field(
        default=None,
        description="Optional store-scoped entity ID. The system derives this if absent.",
    )
    alias_ids: list[str] = Field(
        default_factory=list,
        description="Optional alternate IDs for this entity from other sources.",
    )
    value_kind: str | None = Field(
        default=None,
        description="Semantic type of the value (e.g. string, time, money, quantity).",
    )
    normalized: JsonValue | None = Field(
        default=None,
        description="Structured normalized form of the value. Required for value fillers unless raw is provided.",
    )
    raw: str | None = Field(
        default=None,
        description="Raw source text form. Required for value fillers unless normalized is provided. Required for unknown fillers.",
    )

    @model_validator(mode="after")
    def _validate_shape(self) -> "ExtractedFiller":
        """Require the minimal fields implied by the declared filler kind."""

        normalized_kind = self.kind.strip()
        if normalized_kind == "entity":
            if self.entity_id is not None and self.entity_id.strip():
                return self
            if self.name is None or not self.name.strip():
                raise ValueError("entity fillers require entity_id or name")
            return self
        if normalized_kind == "value":
            if self.value_kind is None or not self.value_kind.strip():
                raise ValueError("value fillers require value_kind")
            if self.normalized is None and (self.raw is None or not self.raw.strip()):
                raise ValueError("value fillers require normalized or raw")
            return self
        if normalized_kind == "unknown":
            if self.raw is None or not self.raw.strip():
                raise ValueError("unknown fillers require raw")
            return self
        raise ValueError(f"unsupported filler kind: {self.kind!r}")


# Keep concrete type aliases for backward compatibility with tests that import them.
ExtractedEntityFiller = ExtractedFiller
ExtractedValueFiller = ExtractedFiller
ExtractedUnknownFiller = ExtractedFiller


class ExtractedEvidenceSpan(BaseModel):
    """Extractor-facing evidence span before deterministic offset resolution.

    The live extraction run showed that models are much better at quoting exact
    source text than at computing reliable character offsets. The producer
    boundary therefore treats exact span text as primary and resolves offsets
    deterministically against the source text before handing the candidate to
    the review pipeline.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    text: str = Field(
        min_length=1,
        description="Exact source substring copied character-for-character from the input text.",
    )
    start_char: int | None = Field(default=None, ge=0)
    end_char: int | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def _validate_optional_offsets(self) -> "ExtractedEvidenceSpan":
        """Require both offsets together when either offset is present."""

        has_start = self.start_char is not None
        has_end = self.end_char is not None
        if has_start != has_end:
            raise ValueError("evidence span offsets must provide both start_char and end_char")
        if self.start_char is not None and self.end_char is not None:
            if self.end_char <= self.start_char:
                raise ValueError("end_char must be greater than start_char")
        return self


class ExtractedCandidate(BaseModel):
    """One candidate assertion emitted by the structured extraction model."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    predicate: str = Field(
        min_length=1,
        description="Predicate identifier only, without serialized role payloads or extra prose.",
    )
    roles: dict[str, list[ExtractedFiller]] = Field(
        description=(
            "Role mapping. MUST include at least one role with at least one filler. "
            "Each role name maps to an array of filler objects."
        ),
    )
    evidence_spans: list[ExtractedEvidenceSpan] = Field(
        min_length=1,
        description="One or more exact evidence spans that directly support the candidate assertion.",
    )
    claim_text: str | None = Field(
        default=None,
        description="Optional short natural-language gloss to help reviewers inspect the candidate.",
    )

    @model_validator(mode="before")
    @classmethod
    def _normalize_serialized_assertion_envelope(cls, data: object) -> object:
        """Unwrap provider responses that serialize the assertion into `predicate`.

        Some live structured-output responses place a JSON-encoded object in the
        `predicate` field and omit the sibling `roles` field entirely, or pack
        the roles into a `predicate_id | roles={...}` string. The persisted
        pipeline contract still wants `predicate` and `roles` split apart, so
        this boundary unwraps the serialized envelope explicitly and logs that
        provider drift was observed.
        """

        if not isinstance(data, Mapping):
            return data
        predicate_obj = data.get("predicate")
        if not isinstance(predicate_obj, str):
            return data
        unwrapped = _unwrap_predicate_envelope(predicate_obj)
        if unwrapped is None:
            return data
        predicate_id, roles_obj = unwrapped
        normalized = dict(data)
        normalized["predicate"] = predicate_id
        if "roles" not in normalized or not normalized["roles"]:
            normalized["roles"] = _normalize_role_fillers_object(roles_obj)
        logger.warning(
            "normalized serialized assertion envelope from predicate field predicate=%s",
            predicate_id,
        )
        return normalized

    @model_validator(mode="before")
    @classmethod
    def _normalize_singleton_role_fillers(cls, data: object) -> object:
        """Wrap singleton role fillers into one-element arrays.

        Live structured-output providers sometimes collapse one-filler role
        arrays into a single object even when the schema implies arrays. The
        extractor runtime still requires every role to normalize into a tuple of
        fillers, so this boundary normalizes the known singleton shape instead
        of forcing downstream layers to care about provider-specific variance.
        """

        if not isinstance(data, Mapping):
            return data
        roles_obj = data.get("roles")
        if not isinstance(roles_obj, Mapping):
            return data
        normalized = dict(data)
        normalized["roles"] = _normalize_role_fillers_object(roles_obj)
        return normalized

    @model_validator(mode="after")
    def _validate_roles(self) -> "ExtractedCandidate":
        """Reject empty role maps and blank role names."""

        if not self.roles:
            raise ValueError("candidate roles must not be empty")
        for role_name, fillers in self.roles.items():
            if not role_name.strip():
                raise ValueError("candidate role names must not be blank")
            if not fillers:
                raise ValueError(f"candidate role {role_name!r} must not be empty")
        return self


class TextExtractionResponse(BaseModel):
    """Structured extractor response for one raw-text source."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    candidates: list[ExtractedCandidate] = Field(
        description="Single required candidate array for the extractor response. Use an empty array when no candidates are supported.",
    )


class TextExtractionRun(BaseModel):
    """One extraction run plus the resolved model context used to produce it.

    Phase 4 originally only needed the extracted candidate imports. Phase 5
    needs the surrounding execution context as well so benchmark reports can
    say which task and model produced a given extraction run.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    selection_task: str = Field(min_length=1)
    prompt_template: str = Field(min_length=1)
    prompt_ref: str | None = None
    selected_model: str = Field(min_length=1)
    resolved_model: str = Field(min_length=1)
    trace_id: str = Field(min_length=1)
    candidate_imports: tuple[CandidateAssertionImport, ...] = ()


class _GetModel(Protocol):
    """Resolve one model ID from a configured task name."""

    def __call__(self, task: str, *, use_performance: bool = True) -> str: ...


class _RenderPrompt(Protocol):
    """Render one YAML/Jinja prompt asset into chat messages."""

    def __call__(self, template_path: str | Path, **context: Any) -> list[dict[str, str]]: ...


class _CallStructured(Protocol):
    """Call llm_client structured output with a Pydantic response model."""

    def __call__(
        self,
        model: str,
        messages: list[dict[str, str]],
        response_model: type[TextExtractionResponse],
        **kwargs: Any,
    ) -> tuple[TextExtractionResponse, object]: ...


@dataclass(frozen=True)
class _LLMClientAPI:
    """Small typed view of the llm_client APIs used by this module."""

    get_model: _GetModel
    render_prompt: _RenderPrompt
    call_llm_structured: _CallStructured


class TextExtractionService:
    """Extract reviewable candidate assertions from raw text via llm_client.

    The service owns only the producer boundary. It does not bypass the review
    pipeline or persist assertions directly. Callers can either:

    - get typed `CandidateAssertionImport` objects for inspection; or
    - submit the extracted imports into the existing `ReviewService`.
    """

    def __init__(
        self,
        *,
        review_service: ReviewService | None = None,
        selection_task: str | None = None,
        prompt_template: Path | None = None,
        prompt_ref: str | None = None,
        max_candidates_per_call: int | None = None,
        max_evidence_spans_per_candidate: int | None = None,
    ) -> None:
        """Create the extractor with config-backed defaults and bounded overrides.

        Task overrides let bounded experiments change model selection without
        touching repo config. Prompt overrides are stricter: callers must
        provide both the template path and the prompt reference together so the
        live extraction path can stay observable and fail loud about which
        prompt actually ran.
        """

        config = get_config()
        self._review_service = review_service or ReviewService()
        self._selection_task = (
            selection_task.strip()
            if selection_task is not None and selection_task.strip()
            else config.extraction.selection_task
        )
        self._selection_use_performance = config.extraction.selection_use_performance
        self._model_override = config.extraction.model_override
        if (prompt_template is None) != (prompt_ref is None):
            raise ConfigError(
                "prompt_template and prompt_ref overrides must be provided together"
            )
        if prompt_template is None:
            self._prompt_template = config.extraction_prompt_template()
            self._prompt_ref = config.extraction.prompt_ref
        else:
            resolved_prompt_template = prompt_template.resolve()
            if not resolved_prompt_template.exists():
                raise FileNotFoundError(
                    f"prompt_template override does not exist: {resolved_prompt_template}"
                )
            normalized_prompt_ref = prompt_ref.strip() if prompt_ref is not None else ""
            if not normalized_prompt_ref:
                raise ConfigError("prompt_ref override must be a non-empty string")
            self._prompt_template = resolved_prompt_template
            self._prompt_ref = normalized_prompt_ref
        if max_candidates_per_call is not None and max_candidates_per_call < 1:
            raise ValueError("max_candidates_per_call must be at least 1 when provided")
        if (
            max_evidence_spans_per_candidate is not None
            and max_evidence_spans_per_candidate < 1
        ):
            raise ValueError(
                "max_evidence_spans_per_candidate must be at least 1 when provided"
            )
        experiment_config = config.evaluation.prompt_experiment
        self._max_candidates_per_call = (
            max_candidates_per_call
            if max_candidates_per_call is not None
            else experiment_config.max_candidates_per_case
        )
        self._max_evidence_spans_per_candidate = (
            max_evidence_spans_per_candidate
            if max_evidence_spans_per_candidate is not None
            else experiment_config.max_evidence_spans_per_candidate
        )
        self._timeout_seconds = config.extraction.timeout_seconds
        self._num_retries = config.extraction.num_retries
        self._max_budget_usd = config.extraction.max_budget_usd
        self._default_extraction_goal = config.extraction.default_extraction_goal

    @property
    def review_service(self) -> ReviewService:
        """Expose the review service used for `extract_and_submit`."""

        return self._review_service

    @property
    def prompt_template(self) -> Path:
        """Return the configured or overridden extraction prompt template path."""

        return self._prompt_template

    @property
    def selection_task(self) -> str:
        """Return the configured llm_client model-selection task."""

        return self._selection_task

    @property
    def prompt_ref(self) -> str:
        """Return the configured or overridden prompt reference."""

        return self._prompt_ref

    def extract_candidate_imports(
        self,
        *,
        source_text: str,
        profile_id: str,
        profile_version: str,
        submitted_by: str,
        source_ref: str,
        source_kind: str = "raw_text",
        source_label: str | None = None,
        source_metadata: dict[str, JsonValue] | None = None,
        extraction_goal: str | None = None,
    ) -> tuple[CandidateAssertionImport, ...]:
        """Extract typed candidate-import records from one raw-text source."""

        return self.extract_candidate_run(
            source_text=source_text,
            profile_id=profile_id,
            profile_version=profile_version,
            submitted_by=submitted_by,
            source_ref=source_ref,
            source_kind=source_kind,
            source_label=source_label,
            source_metadata=source_metadata,
            extraction_goal=extraction_goal,
        ).candidate_imports

    def extract_candidate_run(
        self,
        *,
        source_text: str,
        profile_id: str,
        profile_version: str,
        submitted_by: str,
        source_ref: str,
        source_kind: str = "raw_text",
        source_label: str | None = None,
        source_metadata: dict[str, JsonValue] | None = None,
        extraction_goal: str | None = None,
    ) -> TextExtractionRun:
        """Extract candidate imports and return the resolved run context."""

        normalized_text = source_text.strip()
        if not normalized_text:
            raise ValueError("source_text must be a non-empty string")
        normalized_profile = ProfileRef(
            profile_id=profile_id.strip(),
            profile_version=profile_version.strip(),
        )
        source_artifact = SourceArtifactRef(
            source_kind=source_kind.strip(),
            source_ref=source_ref.strip(),
            source_label=source_label.strip() if source_label is not None else None,
            source_metadata=source_metadata or {},
            content_text=normalized_text,
        )
        llm_client_api = _load_llm_client_api()
        profile = load_effective_profile(
            normalized_profile.profile_id,
            normalized_profile.profile_version,
            overlay_root=self._review_service.overlay_root,
        )
        if self._model_override:
            selected_model = self._model_override
        else:
            selected_model = llm_client_api.get_model(
                self._selection_task,
                use_performance=self._selection_use_performance,
            )
        effective_goal = extraction_goal or self._default_extraction_goal
        if not effective_goal:
            raise ValueError(
                "extraction_goal is required — set it per-call or via config.extraction.default_extraction_goal"
            )
        messages = llm_client_api.render_prompt(
            self._prompt_template,
            profile_id=normalized_profile.profile_id,
            profile_version=normalized_profile.profile_version,
            predicate_catalog=render_predicate_catalog(profile),
            entity_type_catalog=render_entity_type_catalog(profile),
            max_candidates_per_case=self._max_candidates_per_call,
            max_evidence_spans_per_candidate=self._max_evidence_spans_per_candidate,
            extraction_goal=effective_goal,
            source_kind=source_artifact.source_kind,
            source_ref=source_artifact.source_ref,
            source_label=source_artifact.source_label,
            source_text=normalized_text,
        )
        trace_id = _trace_id_for_source(source_ref=source_artifact.source_ref, text=normalized_text)
        try:
            response, meta = llm_client_api.call_llm_structured(
                selected_model,
                messages,
                response_model=TextExtractionResponse,
                timeout=self._timeout_seconds,
                num_retries=self._num_retries,
                task=self._selection_task,
                trace_id=trace_id,
                max_budget=self._max_budget_usd,
                prompt_ref=self._prompt_ref,
            )
        except Exception as exc:
            raise ExtractionError(f"llm_client text extraction failed: {exc}") from exc

        candidate_imports = tuple(
            candidate_import_from_extracted(
                candidate=candidate,
                profile=normalized_profile,
                submitted_by=submitted_by,
                source_artifact=source_artifact,
            )
            for candidate in response.candidates
        )
        resolved_model = str(getattr(meta, "resolved_model", selected_model))
        logger.info(
            "text extraction produced candidate_count=%d profile=%s/%s source_ref=%s model=%s resolved_model=%s",
            len(candidate_imports),
            normalized_profile.profile_id,
            normalized_profile.profile_version,
            source_artifact.source_ref,
            selected_model,
            resolved_model,
        )
        return TextExtractionRun(
            selection_task=self._selection_task,
            prompt_template=str(self._prompt_template),
            prompt_ref=self._prompt_ref,
            selected_model=selected_model,
            resolved_model=resolved_model,
            trace_id=trace_id,
            candidate_imports=candidate_imports,
        )

    def extract_and_submit(
        self,
        *,
        source_text: str,
        profile_id: str,
        profile_version: str,
        submitted_by: str,
        source_ref: str,
        source_kind: str = "raw_text",
        source_label: str | None = None,
        source_metadata: dict[str, JsonValue] | None = None,
        extraction_goal: str | None = None,
    ) -> tuple[CandidateSubmissionResult, ...]:
        """Extract candidate imports and submit them through the review pipeline."""

        extraction_run = self.extract_candidate_run(
            source_text=source_text,
            profile_id=profile_id,
            profile_version=profile_version,
            submitted_by=submitted_by,
            source_ref=source_ref,
            source_kind=source_kind,
            source_label=source_label,
            source_metadata=source_metadata,
            extraction_goal=extraction_goal,
        )
        return tuple(
            self._review_service.submit_candidate_import(candidate_import=candidate_import)
            for candidate_import in extraction_run.candidate_imports
        )


def candidate_import_from_extracted(
    *,
    candidate: ExtractedCandidate,
    profile: ProfileRef,
    submitted_by: str,
    source_artifact: SourceArtifactRef,
) -> CandidateAssertionImport:
    """Convert one extracted candidate into the pipeline import contract."""

    payload: dict[str, JsonValue] = {
        "predicate": candidate.predicate,
        "roles": {
            role_name: [
                _pipeline_filler_from_extracted(
                    filler=filler,
                    source_ref=source_artifact.source_ref,
                )
                for filler in fillers
            ]
            for role_name, fillers in candidate.roles.items()
        },
    }
    claim_text = candidate.claim_text.strip() if candidate.claim_text is not None else None
    return CandidateAssertionImport(
        profile=profile,
        payload=payload,
        submitted_by=submitted_by,
        source_artifact=source_artifact,
        evidence_spans=_resolve_evidence_spans(
            source_text=source_artifact.content_text or "",
            evidence_spans=tuple(candidate.evidence_spans),
        ),
        claim_text=claim_text if claim_text else None,
    )


def _pipeline_filler_from_extracted(
    *,
    filler: ExtractedEntityFiller | ExtractedValueFiller | ExtractedUnknownFiller,
    source_ref: str,
) -> dict[str, JsonValue]:
    """Normalize one extracted filler into the persisted pipeline payload.

    Entity fillers allow ``name`` without ``entity_id`` at the extraction
    boundary.  The runtime derives a source-scoped local entity identifier so
    raw-text extraction does not need to solve cross-document identity before
    review, promotion, or the later identity phase.
    """

    filler_payload = cast(
        dict[str, JsonValue],
        filler.model_dump(exclude_none=True, mode="json"),
    )
    if filler.kind == "value" and "normalized" not in filler_payload:
        raw_value = filler.raw.strip() if filler.raw else ""
        if not raw_value:
            raise ValueError("value filler is missing normalized and raw")
        filler_payload["normalized"] = raw_value
        return filler_payload
    if filler.kind != "entity":
        return filler_payload
    # Entity — derive entity_id if not provided.
    entity_id = filler.entity_id.strip() if filler.entity_id else ""
    if entity_id:
        filler_payload["entity_id"] = entity_id
        return filler_payload
    filler_payload["entity_id"] = _derive_local_entity_id(
        source_ref=source_ref,
        name=filler.name or "",
        entity_type=filler.entity_type or None,
    )
    return filler_payload


def _derive_local_entity_id(
    *,
    source_ref: str,
    name: str,
    entity_type: str | None,
) -> str:
    """Derive a deterministic source-scoped local entity id from one mention.

    The ID is intentionally scoped by `source_ref` so separate documents do not
    silently merge similarly named mentions before the later stable-identity
    phase has a chance to review them.
    """

    normalized_name = name.strip()
    if not normalized_name:
        raise ValueError("cannot derive local entity id from blank entity name")
    source_digest = hashlib.sha256(source_ref.encode("utf-8")).hexdigest()[:8]
    type_slug = _slug_token(entity_type or "entity")
    name_slug = _slug_token(normalized_name)
    return f"ent:auto:{source_digest}:{type_slug}:{name_slug}"


def _slug_token(value: str) -> str:
    """Collapse free text into a stable ASCII token for local ids."""

    slug = re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_")
    if not slug:
        raise ValueError(f"cannot derive slug token from value: {value!r}")
    return slug


def _resolve_evidence_spans(
    *,
    source_text: str,
    evidence_spans: tuple[ExtractedEvidenceSpan, ...],
) -> tuple[EvidenceSpan, ...]:
    """Resolve extractor evidence text into verified pipeline evidence spans.

    Exact quoted text is primary at the producer boundary. When valid offsets
    are present and match the quoted text, they are reused. Otherwise the
    runtime finds a unique exact match in the source text and emits the verified
    offsets explicitly. Ambiguous or missing matches still fail loudly.
    """

    resolved: list[EvidenceSpan] = []
    for index, span in enumerate(evidence_spans):
        if span.start_char is not None and span.end_char is not None:
            candidate_text = source_text[span.start_char : span.end_char]
            if candidate_text == span.text:
                resolved.append(
                    EvidenceSpan(
                        start_char=span.start_char,
                        end_char=span.end_char,
                        text=span.text,
                    )
                )
                continue
            logger.warning(
                "extractor evidence offsets did not match quoted text span_index=%d start=%s end=%s",
                index,
                span.start_char,
                span.end_char,
            )
        matches = _find_unique_span_matches(source_text=source_text, span_text=span.text)
        if len(matches) != 1:
            raise ValueError(
                f"evidence span {index} text did not resolve to a unique exact match in source"
            )
        start_char, end_char = matches[0]
        resolved.append(
            EvidenceSpan(
                start_char=start_char,
                end_char=end_char,
                text=span.text,
            )
        )
    return tuple(resolved)


def _find_unique_span_matches(*, source_text: str, span_text: str) -> list[tuple[int, int]]:
    """Return all exact occurrences of one quoted span within the source text."""

    matches: list[tuple[int, int]] = []
    start = 0
    while True:
        found = source_text.find(span_text, start)
        if found < 0:
            return matches
        matches.append((found, found + len(span_text)))
        start = found + 1


def _trace_id_for_source(*, source_ref: str, text: str) -> str:
    """Build a deterministic trace identifier for one extraction call."""

    digest = hashlib.sha256(f"{source_ref}\n{text}".encode("utf-8")).hexdigest()[:16]
    return f"{get_config().project.package_name}.extract.{digest}"


def render_predicate_catalog(profile: LoadedProfile) -> str:
    """Render the active predicate catalog with role constraints.

    The first real extraction run showed that role names alone are not enough
    guidance for the model. This catalog now carries the role-level contract as
    well so the extractor can choose entity types and value kinds that the
    runtime will actually accept.
    """

    rules = sorted(profile.predicate_rules.items())
    if not rules:
        return "none provided"
    lines = []
    for predicate_id, rule in rules:
        if not rule.allowed_roles:
            lines.append(f"- {predicate_id} (roles: no declared roles)")
            continue
        role_parts: list[str] = []
        for role_name in rule.allowed_roles:
            details: list[str] = []
            cardinality = rule.role_cardinality.get(role_name)
            if cardinality is not None:
                required = role_name in rule.required_roles or cardinality.min_count > 0
                details.append("required" if required else "optional")
                if cardinality.max_count is None:
                    details.append(f"min={cardinality.min_count}")
                else:
                    details.append(f"count={cardinality.min_count}..{cardinality.max_count}")
            elif role_name in rule.required_roles:
                details.append("required")
            expected_entity_type = rule.role_filler_types.get(role_name)
            expected_value_kind = rule.role_value_kinds.get(role_name)
            if expected_entity_type is not None:
                details.append(f"entity_type={expected_entity_type}")
            if expected_value_kind is not None:
                details.append(f"value_kind={expected_value_kind}")
            detail_text = ", ".join(details) if details else "declared"
            role_parts.append(f"{role_name} [{detail_text}]")
        lines.append(f"- {predicate_id} (roles: {'; '.join(role_parts)})")
    return "\n".join(lines)


def render_entity_type_catalog(profile: LoadedProfile) -> str:
    """Render the active entity-type catalog from pack and profile information."""

    type_names: set[str] = set(profile.type_hierarchy_overrides.keys())
    if profile.pack is not None:
        type_names.update(profile.pack.type_parents.keys())
    if not type_names:
        return "none provided"
    return "\n".join(f"- {type_name}" for type_name in sorted(type_names))


def _normalize_role_fillers_object(roles_obj: Mapping[object, object]) -> dict[str, object]:
    """Normalize mapping-valued singleton role fillers into one-item arrays."""

    normalized_roles: dict[str, object] = {}
    for role_name, fillers in roles_obj.items():
        if isinstance(fillers, Mapping):
            normalized_roles[str(role_name)] = [dict(fillers)]
        else:
            normalized_roles[str(role_name)] = fillers
    return normalized_roles


def _unwrap_predicate_envelope(predicate_value: str) -> tuple[str, Mapping[object, object]] | None:
    """Parse known provider drift variants that serialize roles into `predicate`."""

    stripped = predicate_value.strip()
    if stripped.startswith("{"):
        try:
            envelope = json.loads(stripped)
        except json.JSONDecodeError as exc:
            raise ValueError("serialized predicate envelope is not valid JSON") from exc
        if not isinstance(envelope, Mapping):
            raise ValueError("serialized predicate envelope must decode to an object")
        predicate_id = envelope.get("predicate_id")
        roles_obj = envelope.get("roles")
        if not isinstance(predicate_id, str) or not predicate_id.strip():
            raise ValueError("serialized predicate envelope must include predicate_id")
        if not isinstance(roles_obj, Mapping):
            raise ValueError("serialized predicate envelope must include roles")
        return predicate_id, roles_obj

    role_marker = "| roles="
    if role_marker not in stripped:
        return None
    predicate_id, roles_blob = stripped.split(role_marker, 1)
    normalized_predicate_id = predicate_id.strip()
    if not normalized_predicate_id:
        raise ValueError("serialized predicate envelope must include predicate_id")
    try:
        roles_obj = json.loads(roles_blob.strip())
    except json.JSONDecodeError as exc:
        raise ValueError("serialized predicate role payload is not valid JSON") from exc
    if not isinstance(roles_obj, Mapping):
        raise ValueError("serialized predicate role payload must decode to an object")
    return normalized_predicate_id, roles_obj


def _load_llm_client_api() -> _LLMClientAPI:
    """Import the required llm_client APIs lazily and fail loudly if missing."""

    try:
        module = import_module("llm_client")
    except ImportError as exc:
        raise ConfigError(
            "text extraction requires llm_client to be installed; "
            "run `pip install -e ~/projects/llm_client` in this repo's .venv"
        ) from exc
    return _LLMClientAPI(
        get_model=cast(_GetModel, getattr(module, "get_model")),
        render_prompt=cast(_RenderPrompt, getattr(module, "render_prompt")),
        call_llm_structured=cast(_CallStructured, getattr(module, "call_llm_structured")),
    )


__all__ = [
    "candidate_import_from_extracted",
    "ExtractedCandidate",
    "ExtractedEntityFiller",
    "ExtractedEvidenceSpan",
    "ExtractedFiller",
    "ExtractedUnknownFiller",
    "ExtractedValueFiller",
    "ExtractionError",
    "render_entity_type_catalog",
    "render_predicate_catalog",
    "TextExtractionRun",
    "TextExtractionResponse",
    "TextExtractionService",
]

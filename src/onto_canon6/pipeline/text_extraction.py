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

    The shape mirrors the current candidate payload contract closely enough to
    keep downstream validation deterministic while still leaving normalized
    value payloads open where the ontology runtime is intentionally open.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: str = Field(min_length=1)
    entity_id: str | None = None
    entity_type: str | None = None
    name: str | None = None
    alias_ids: list[str] = Field(default_factory=list)
    value_kind: str | None = None
    normalized: JsonValue | None = None
    raw: str | None = None

    @model_validator(mode="after")
    def _validate_shape(self) -> "ExtractedFiller":
        """Require the minimal fields implied by the declared filler kind."""

        normalized_kind = self.kind.strip()
        if normalized_kind == "entity":
            if self.entity_id is None or not self.entity_id.strip():
                raise ValueError("entity fillers require entity_id")
            return self
        if normalized_kind == "value":
            if self.value_kind is None or not self.value_kind.strip():
                raise ValueError("value fillers require value_kind")
            if self.normalized is None:
                raise ValueError("value fillers require normalized")
            return self
        if normalized_kind == "unknown":
            if self.raw is None or not self.raw.strip():
                raise ValueError("unknown fillers require raw")
            return self
        raise ValueError(f"unsupported filler kind: {self.kind!r}")


class ExtractedCandidate(BaseModel):
    """One candidate assertion emitted by the structured extraction model."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    predicate: str = Field(min_length=1)
    roles: dict[str, list[ExtractedFiller]] = Field(default_factory=dict)
    evidence_spans: list[EvidenceSpan] = Field(min_length=1)
    claim_text: str | None = None

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

    candidates: list[ExtractedCandidate] = Field(default_factory=list)


class TextExtractionRun(BaseModel):
    """One extraction run plus the resolved model context used to produce it.

    Phase 4 originally only needed the extracted candidate imports. Phase 5
    needs the surrounding execution context as well so benchmark reports can
    say which task and model produced a given extraction run.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    selection_task: str = Field(min_length=1)
    prompt_template: str = Field(min_length=1)
    selected_model: str = Field(min_length=1)
    resolved_model: str = Field(min_length=1)
    trace_id: str = Field(min_length=1)
    candidate_imports: tuple[CandidateAssertionImport, ...] = ()


class _GetModel(Protocol):
    """Resolve one model ID from a configured task name."""

    def __call__(self, task: str) -> str: ...


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
    ) -> None:
        """Create the extractor with config-backed prompt and model defaults."""

        config = get_config()
        self._review_service = review_service or ReviewService()
        self._selection_task = config.extraction.selection_task
        self._prompt_template = config.extraction_prompt_template()
        self._timeout_seconds = config.extraction.timeout_seconds
        self._num_retries = config.extraction.num_retries
        self._max_budget_usd = config.extraction.max_budget_usd
        self._max_output_tokens = config.extraction.max_output_tokens

    @property
    def review_service(self) -> ReviewService:
        """Expose the review service used for `extract_and_submit`."""

        return self._review_service

    @property
    def prompt_template(self) -> Path:
        """Return the configured extraction prompt template path."""

        return self._prompt_template

    @property
    def selection_task(self) -> str:
        """Return the configured llm_client model-selection task."""

        return self._selection_task

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
        selected_model = llm_client_api.get_model(self._selection_task)
        messages = llm_client_api.render_prompt(
            self._prompt_template,
            profile_id=normalized_profile.profile_id,
            profile_version=normalized_profile.profile_version,
            predicate_catalog=_render_predicate_catalog(profile),
            entity_type_catalog=_render_entity_type_catalog(profile),
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
                max_tokens=self._max_output_tokens,
            )
        except Exception as exc:
            raise ExtractionError(f"llm_client text extraction failed: {exc}") from exc

        candidate_imports = tuple(
            _candidate_import_from_extracted(
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
        )
        return tuple(
            self._review_service.submit_candidate_import(candidate_import=candidate_import)
            for candidate_import in extraction_run.candidate_imports
        )


def _candidate_import_from_extracted(
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
                cast(
                    dict[str, JsonValue],
                    filler.model_dump(exclude_none=True, mode="json"),
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
        evidence_spans=tuple(candidate.evidence_spans),
        claim_text=claim_text if claim_text else None,
    )


def _trace_id_for_source(*, source_ref: str, text: str) -> str:
    """Build a deterministic trace identifier for one extraction call."""

    digest = hashlib.sha256(f"{source_ref}\n{text}".encode("utf-8")).hexdigest()[:16]
    return f"{get_config().project.package_name}.extract.{digest}"


def _render_predicate_catalog(profile: LoadedProfile) -> str:
    """Render a small predicate catalog string from the active profile."""

    rules = sorted(profile.predicate_rules.items())
    if not rules:
        return "none provided"
    lines = []
    for predicate_id, rule in rules:
        role_text = ", ".join(rule.allowed_roles) if rule.allowed_roles else "no declared roles"
        lines.append(f"- {predicate_id} (roles: {role_text})")
    return "\n".join(lines)


def _render_entity_type_catalog(profile: LoadedProfile) -> str:
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
    "ExtractedCandidate",
    "ExtractedFiller",
    "ExtractionError",
    "TextExtractionRun",
    "TextExtractionResponse",
    "TextExtractionService",
]

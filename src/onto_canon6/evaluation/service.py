"""Live extraction evaluation for the Phase 5 benchmark slice.

This module runs the current text extractor over a small benchmark fixture and
reports three lanes separately:

1. reasonableness/support judged from the source text;
2. structural validation status from the local ontology runtime;
3. exact preferred-form fidelity against hand-authored reference payloads.

The service deliberately does not persist review state. Its job is to evaluate
the extraction path, not to mutate the operational workflow.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
from importlib import import_module
import json
from pathlib import Path
from typing import Any, Mapping, Protocol, cast
import uuid

from pydantic import BaseModel, ConfigDict, Field

from ..config import ConfigError, get_config
from ..ontology_runtime import (
    canonical_assertion_body,
    load_effective_profile,
    validate_assertion_payload,
)
from ..pipeline import (
    CandidateAssertionImport,
    CandidateValidationStatus,
    ProfileRef,
    TextExtractionRun,
    TextExtractionService,
)
from .models import (
    AggregateReasonablenessSummary,
    AggregateValidationSummary,
    BenchmarkAggregateSummary,
    BenchmarkCase,
    BenchmarkCaseEvaluation,
    BenchmarkEvaluationReport,
    BenchmarkFixture,
    BenchmarkReferenceCandidate,
    CandidateEvaluationRecord,
    CandidateReasonablenessReview,
    CanonicalizationSummary,
    LLMRunRecord,
    ReasonablenessLabel,
    ReasonablenessReview,
)


class EvaluationError(RuntimeError):
    """Raised when the live extraction evaluation cannot complete honestly."""


class _JudgeCandidateReview(BaseModel):
    """Structured judge verdict for one extracted candidate."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    candidate_index: int = Field(ge=0)
    support_label: ReasonablenessLabel
    reasoning: str = Field(min_length=1)


class _JudgeResponse(BaseModel):
    """Structured reasonableness review returned by the judge model."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    candidate_reviews: tuple[_JudgeCandidateReview, ...] = ()
    important_missing_facts: tuple[str, ...] = ()
    overall_notes: str | None = None


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
        response_model: type[_JudgeResponse],
        **kwargs: Any,
    ) -> tuple[_JudgeResponse, object]: ...


class _StartRun(Protocol):
    """Start one shared observability experiment run and return its run ID."""

    def __call__(self, **kwargs: Any) -> str: ...


class _FinishRun(Protocol):
    """Finish one shared observability experiment run."""

    def __call__(self, *, run_id: str, **kwargs: Any) -> dict[str, Any]: ...


class _LogItem(Protocol):
    """Log one item row into a shared observability experiment run."""

    def __call__(self, *, run_id: str, item_id: str, metrics: dict[str, Any], **kwargs: Any) -> None: ...


class _LogAggregate(Protocol):
    """Log one family-level shared experiment aggregate."""

    def __call__(self, **kwargs: Any) -> str: ...


class _ExtractionRunner(Protocol):
    """Narrow extraction seam needed by the evaluation slice."""

    @property
    def selection_task(self) -> str: ...

    @property
    def prompt_template(self) -> Path: ...

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
        source_metadata: dict[str, Any] | None = None,
    ) -> TextExtractionRun: ...


@dataclass(frozen=True)
class _JudgeLLMClientAPI:
    """Small typed view of the llm_client APIs used by the judge."""

    get_model: _GetModel
    render_prompt: _RenderPrompt
    call_llm_structured: _CallStructured


@dataclass(frozen=True)
class _ObservabilityAPI:
    """Small typed view of the shared experiment-observability functions."""

    start_run: _StartRun
    finish_run: _FinishRun
    log_item: _LogItem
    log_experiment_aggregate: _LogAggregate


def load_benchmark_fixture(fixture_path: Path | str) -> BenchmarkFixture:
    """Load one benchmark fixture file into typed evaluation models."""

    path = Path(fixture_path)
    if not path.exists():
        raise FileNotFoundError(f"benchmark fixture not found: {path}")
    return BenchmarkFixture.model_validate_json(path.read_text(encoding="utf-8"))


class LiveExtractionEvaluationService:
    """Run the text extractor over a benchmark fixture and score the results."""

    def __init__(
        self,
        *,
        extractor: _ExtractionRunner | None = None,
    ) -> None:
        """Create the evaluator with config-backed defaults."""

        config = get_config()
        self._extractor = extractor or TextExtractionService()
        self._benchmark_fixture = config.evaluation_benchmark_fixture()
        self._observability_dataset = config.evaluation.observability_dataset
        self._observability_phase = config.evaluation.observability_phase
        self._judge_selection_task = config.evaluation.judge_selection_task
        self._judge_prompt_template = config.evaluation_judge_prompt_template()
        self._judge_prompt_ref = config.evaluation.judge_prompt_ref
        self._judge_timeout_seconds = config.evaluation.judge_timeout_seconds
        self._judge_num_retries = config.evaluation.judge_num_retries
        self._judge_max_budget_usd = config.evaluation.judge_max_budget_usd
        self._judge_max_output_tokens = config.evaluation.judge_max_output_tokens

    @property
    def benchmark_fixture(self) -> Path:
        """Return the configured benchmark fixture path."""

        return self._benchmark_fixture

    def run_live_benchmark(
        self,
        *,
        fixture_path: Path | str | None = None,
        case_limit: int | None = None,
        submitted_by: str = "agent:onto_canon6_benchmark",
    ) -> BenchmarkEvaluationReport:
        """Run the benchmark live against the configured extraction path."""

        resolved_fixture_path = Path(fixture_path or self._benchmark_fixture)
        fixture = load_benchmark_fixture(resolved_fixture_path)
        cases = fixture.cases if case_limit is None else fixture.cases[:case_limit]
        experiment_execution_id = uuid.uuid4().hex[:12]
        observability_api = _load_observability_api()
        case_reports = tuple(
            self.evaluate_case_live(
                case=case,
                submitted_by=submitted_by,
                experiment_execution_id=experiment_execution_id,
                fixture_id=fixture.fixture_id,
                fixture_path=resolved_fixture_path,
                observability_api=observability_api,
            )
            for case in cases
        )
        report = BenchmarkEvaluationReport(
            fixture_id=fixture.fixture_id,
            fixture_path=str(resolved_fixture_path),
            experiment_execution_id=experiment_execution_id,
            cases=case_reports,
            summary=_build_aggregate_summary(case_reports),
        )
        _log_fixture_observability_aggregate(
            observability_api=observability_api,
            report=report,
        )
        return report

    def evaluate_case_live(
        self,
        *,
        case: BenchmarkCase,
        submitted_by: str,
        experiment_execution_id: str | None = None,
        fixture_id: str | None = None,
        fixture_path: Path | None = None,
        observability_api: _ObservabilityAPI | None = None,
    ) -> BenchmarkCaseEvaluation:
        """Run extraction and split evaluation for one benchmark case."""

        source_text = case.source_artifact.content_text
        if source_text is None or not source_text.strip():
            raise EvaluationError(f"benchmark case {case.case_id} is missing source text")
        extraction_run = self._extractor.extract_candidate_run(
            source_text=source_text,
            profile_id=case.profile.profile_id,
            profile_version=case.profile.profile_version,
            submitted_by=submitted_by,
            source_ref=case.source_artifact.source_ref,
            source_kind=case.source_artifact.source_kind,
            source_label=case.source_artifact.source_label,
            source_metadata=dict(case.source_artifact.source_metadata),
        )
        validation_statuses = _validate_candidate_imports(
            candidate_imports=extraction_run.candidate_imports,
            profile=case.profile,
            overlay_root=self._extractor.review_service.overlay_root
            if isinstance(self._extractor, TextExtractionService)
            else None,
        )
        support_review, judge_run = self._judge_reasonableness(
            case=case,
            candidate_imports=extraction_run.candidate_imports,
        )
        exact_match_flags, canonicalization = _score_exact_canonicalization(
            expected_candidates=case.expected_candidates,
            observed_candidates=extraction_run.candidate_imports,
        )
        candidate_evaluations = tuple(
            CandidateEvaluationRecord(
                candidate_index=index,
                candidate_import=candidate_import,
                validation_status=validation_statuses[index],
                support_label=support_review.candidate_reviews[index].support_label,
                support_reasoning=support_review.candidate_reviews[index].reasoning,
                exact_preferred_match=exact_match_flags[index],
            )
            for index, candidate_import in enumerate(extraction_run.candidate_imports)
        )
        case_evaluation = BenchmarkCaseEvaluation(
            case_id=case.case_id,
            profile=case.profile,
            source_artifact=case.source_artifact,
            extraction_run=LLMRunRecord(
                selection_task=extraction_run.selection_task,
                prompt_template=extraction_run.prompt_template,
                prompt_ref=extraction_run.prompt_ref,
                selected_model=extraction_run.selected_model,
                resolved_model=extraction_run.resolved_model,
                trace_id=extraction_run.trace_id,
                max_budget_usd=get_config().extraction.max_budget_usd,
            ),
            judge_run=judge_run,
            candidate_evaluations=candidate_evaluations,
            canonicalization=canonicalization,
            important_missing_facts=support_review.important_missing_facts,
            overall_notes=support_review.overall_notes,
        )
        observability_run_id = _log_case_observability_run(
            observability_api=observability_api,
            case=case,
            case_evaluation=case_evaluation,
            experiment_execution_id=experiment_execution_id,
            fixture_id=fixture_id,
            fixture_path=fixture_path,
        )
        return case_evaluation.model_copy(update={"observability_run_id": observability_run_id})

    def _judge_reasonableness(
        self,
        *,
        case: BenchmarkCase,
        candidate_imports: tuple[CandidateAssertionImport, ...],
    ) -> tuple[ReasonablenessReview, LLMRunRecord]:
        """Judge extracted candidates for support/reasonableness only."""

        llm_client_api = _load_judge_llm_client_api()
        selected_model = llm_client_api.get_model(self._judge_selection_task)
        trace_id = _judge_trace_id(case_id=case.case_id, source_ref=case.source_artifact.source_ref)
        messages = llm_client_api.render_prompt(
            self._judge_prompt_template,
            case_id=case.case_id,
            source_ref=case.source_artifact.source_ref,
            source_text=case.source_artifact.content_text,
            candidate_assertions_json=json.dumps(
                [
                    {
                        "candidate_index": index,
                        "payload": candidate_import.payload,
                        "claim_text": candidate_import.claim_text,
                        "evidence_spans": [
                            span.model_dump(mode="json")
                            for span in candidate_import.evidence_spans
                        ],
                    }
                    for index, candidate_import in enumerate(candidate_imports)
                ],
                indent=2,
                sort_keys=True,
            ),
        )
        try:
            parsed, meta = llm_client_api.call_llm_structured(
                selected_model,
                messages,
                response_model=_JudgeResponse,
                timeout=self._judge_timeout_seconds,
                num_retries=self._judge_num_retries,
                task=self._judge_selection_task,
                trace_id=trace_id,
                max_budget=self._judge_max_budget_usd,
                max_tokens=self._judge_max_output_tokens,
                prompt_ref=self._judge_prompt_ref,
            )
        except Exception as exc:
            raise EvaluationError(f"reasonableness judge failed: {exc}") from exc
        review = _coerce_reasonableness_review(
            parsed=parsed,
            candidate_count=len(candidate_imports),
        )
        judge_run = LLMRunRecord(
            selection_task=self._judge_selection_task,
            prompt_template=str(self._judge_prompt_template),
            prompt_ref=self._judge_prompt_ref,
            selected_model=selected_model,
            resolved_model=str(getattr(meta, "resolved_model", selected_model)),
            trace_id=trace_id,
            max_budget_usd=self._judge_max_budget_usd,
        )
        return review, judge_run


def _coerce_reasonableness_review(
    *,
    parsed: _JudgeResponse,
    candidate_count: int,
) -> ReasonablenessReview:
    """Require one review row for each candidate and preserve the declared order."""

    if candidate_count == 0:
        if parsed.candidate_reviews:
            raise EvaluationError("judge returned candidate reviews for an empty extraction result")
        return ReasonablenessReview(
            candidate_reviews=(),
            important_missing_facts=parsed.important_missing_facts,
            overall_notes=parsed.overall_notes,
        )

    by_index = {review.candidate_index: review for review in parsed.candidate_reviews}
    expected_indexes = set(range(candidate_count))
    if set(by_index) != expected_indexes:
        raise EvaluationError(
            "judge must return exactly one candidate review for each extracted candidate"
        )
    ordered_reviews = tuple(
        CandidateReasonablenessReview(
            candidate_index=index,
            support_label=by_index[index].support_label,
            reasoning=by_index[index].reasoning,
        )
        for index in range(candidate_count)
    )
    return ReasonablenessReview(
        candidate_reviews=ordered_reviews,
        important_missing_facts=parsed.important_missing_facts,
        overall_notes=parsed.overall_notes,
    )


def _validate_candidate_imports(
    *,
    candidate_imports: tuple[CandidateAssertionImport, ...],
    profile: ProfileRef,
    overlay_root: Path | None,
) -> tuple[CandidateValidationStatus, ...]:
    """Reduce local validator outcomes to structural status labels."""

    loaded_profile = load_effective_profile(
        profile.profile_id,
        profile.profile_version,
        overlay_root=overlay_root,
    )
    statuses: list[CandidateValidationStatus] = []
    for candidate_import in candidate_imports:
        outcome = validate_assertion_payload(candidate_import.payload, profile=loaded_profile)
        if outcome.has_hard_errors:
            statuses.append("invalid")
        elif outcome.has_soft_violations:
            statuses.append("needs_review")
        else:
            statuses.append("valid")
    return tuple(statuses)


def _score_exact_canonicalization(
    *,
    expected_candidates: tuple[BenchmarkReferenceCandidate, ...],
    observed_candidates: tuple[CandidateAssertionImport, ...],
) -> tuple[tuple[bool, ...], CanonicalizationSummary]:
    """Score exact preferred-form agreement against the benchmark fixture."""

    expected_signatures = Counter(
        _candidate_signature(reference.payload) for reference in expected_candidates
    )
    observed_signatures = Counter(
        _candidate_signature(candidate_import.payload) for candidate_import in observed_candidates
    )
    matched_counter = expected_signatures & observed_signatures
    matched = sum(matched_counter.values())
    expected_count = sum(expected_signatures.values())
    observed_count = sum(observed_signatures.values())
    precision = matched / observed_count if observed_count else 0.0
    recall = matched / expected_count if expected_count else 0.0
    f1 = 0.0
    if precision and recall:
        f1 = 2 * precision * recall / (precision + recall)

    remaining = Counter(expected_signatures)
    match_flags: list[bool] = []
    for candidate_import in observed_candidates:
        signature = _candidate_signature(candidate_import.payload)
        if remaining[signature] > 0:
            remaining[signature] -= 1
            match_flags.append(True)
        else:
            match_flags.append(False)

    return (
        tuple(match_flags),
        CanonicalizationSummary(
            expected=expected_count,
            observed=observed_count,
            matched=matched,
            precision=round(precision, 4),
            recall=round(recall, 4),
            f1=round(f1, 4),
            missing_signatures=tuple((expected_signatures - observed_signatures).elements()),
            unexpected_signatures=tuple((observed_signatures - expected_signatures).elements()),
        ),
    )


def _candidate_signature(payload: Mapping[str, Any]) -> str:
    """Canonicalize one payload into a stable exact-match signature."""

    body = canonical_assertion_body(payload)
    predicate = str(body.get("predicate", "")).strip()
    roles_obj = body.get("roles", {})
    if not isinstance(roles_obj, Mapping):
        raise EvaluationError("candidate payload roles must be a mapping for exact scoring")
    normalized_roles: dict[str, list[Any]] = {}
    for role_name, fillers in roles_obj.items():
        if not isinstance(fillers, list):
            raise EvaluationError("candidate role fillers must be lists for exact scoring")
        normalized_roles[str(role_name)] = sorted(
            (_normalize_json(filler) for filler in fillers),
            key=_stable_json,
        )
    canonical = {
        "predicate": predicate,
        "roles": {role_name: normalized_roles[role_name] for role_name in sorted(normalized_roles)},
    }
    return _stable_json(canonical)


def _normalize_json(value: Any) -> Any:
    """Normalize arbitrary JSON-like data into a stable comparable shape."""

    if isinstance(value, Mapping):
        return {str(key): _normalize_json(item) for key, item in sorted(value.items())}
    if isinstance(value, list):
        return sorted((_normalize_json(item) for item in value), key=_stable_json)
    return value


def _stable_json(value: Any) -> str:
    """Serialize normalized JSON deterministically for matching and reports."""

    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _build_aggregate_summary(
    case_reports: tuple[BenchmarkCaseEvaluation, ...],
) -> BenchmarkAggregateSummary:
    """Aggregate reasonableness, validation, and exact fidelity across cases."""

    support_counts: Counter[str] = Counter()
    validation_counts: Counter[str] = Counter()
    canonical_counter: Counter[str] = Counter()

    for case_report in case_reports:
        for candidate in case_report.candidate_evaluations:
            support_counts[candidate.support_label] += 1
            validation_counts[candidate.validation_status] += 1
        canonical_counter.update(
            {
                "expected": case_report.canonicalization.expected,
                "observed": case_report.canonicalization.observed,
                "matched": case_report.canonicalization.matched,
            }
        )

    total_candidates = sum(support_counts.values())
    supported_count = int(support_counts["supported"])
    partially_supported_count = int(support_counts["partially_supported"])
    unsupported_count = int(support_counts["unsupported"])
    supported_rate = supported_count / total_candidates if total_candidates else 0.0
    acceptable_rate = (
        (supported_count + partially_supported_count) / total_candidates if total_candidates else 0.0
    )
    expected = int(canonical_counter["expected"])
    observed = int(canonical_counter["observed"])
    matched = int(canonical_counter["matched"])
    precision = matched / observed if observed else 0.0
    recall = matched / expected if expected else 0.0
    f1 = 0.0
    if precision and recall:
        f1 = 2 * precision * recall / (precision + recall)

    return BenchmarkAggregateSummary(
        case_count=len(case_reports),
        reasonableness=AggregateReasonablenessSummary(
            total_candidates=total_candidates,
            supported_count=supported_count,
            partially_supported_count=partially_supported_count,
            unsupported_count=unsupported_count,
            supported_rate=round(supported_rate, 4),
            acceptable_rate=round(acceptable_rate, 4),
        ),
        validation=AggregateValidationSummary(
            valid_count=int(validation_counts["valid"]),
            needs_review_count=int(validation_counts["needs_review"]),
            invalid_count=int(validation_counts["invalid"]),
        ),
        canonicalization=CanonicalizationSummary(
            expected=expected,
            observed=observed,
            matched=matched,
            precision=round(precision, 4),
            recall=round(recall, 4),
            f1=round(f1, 4),
            missing_signatures=(),
            unexpected_signatures=(),
        ),
    )


def _log_case_observability_run(
    *,
    observability_api: _ObservabilityAPI | None,
    case: BenchmarkCase,
    case_evaluation: BenchmarkCaseEvaluation,
    experiment_execution_id: str | None,
    fixture_id: str | None,
    fixture_path: Path | None,
) -> str | None:
    """Persist one benchmark-case experiment run when observability is enabled."""

    if observability_api is None or experiment_execution_id is None or fixture_id is None:
        return None
    config = get_config()
    run_id = observability_api.start_run(
        dataset=config.evaluation.observability_dataset,
        model=case_evaluation.extraction_run.resolved_model,
        task="benchmark.live_extraction",
        config={
            "profile_id": case.profile.profile_id,
            "profile_version": case.profile.profile_version,
            "extraction_selection_task": case_evaluation.extraction_run.selection_task,
            "judge_selection_task": case_evaluation.judge_run.selection_task,
            "extraction_prompt_ref": case_evaluation.extraction_run.prompt_ref,
            "judge_prompt_ref": case_evaluation.judge_run.prompt_ref,
        },
        condition_id=case.case_id,
        replicate=0,
        scenario_id=fixture_id,
        phase=config.evaluation.observability_phase,
        metrics_schema=[
            "supported",
            "partially_supported",
            "unsupported",
            "acceptable",
            "valid",
            "needs_review",
            "invalid",
            "exact_preferred_match",
        ],
        provenance={
            "source_package": config.project.package_name,
            "benchmark_execution_id": experiment_execution_id,
            "fixture_id": fixture_id,
            "fixture_path": str(fixture_path) if fixture_path is not None else None,
            "source_ref": case.source_artifact.source_ref,
            "source_kind": case.source_artifact.source_kind,
            "judge_model": case_evaluation.judge_run.resolved_model,
            "judge_trace_id": case_evaluation.judge_run.trace_id,
            "important_missing_facts": list(case_evaluation.important_missing_facts),
        },
        allow_missing_agent_spec=True,
        missing_agent_spec_reason=(
            "live extraction benchmark runs evaluate one service boundary rather than "
            "an agent-spec-governed agent workload"
        ),
        project=config.project.name,
    )
    for candidate_evaluation in case_evaluation.candidate_evaluations:
        observability_api.log_item(
            run_id=run_id,
            item_id=f"candidate_{candidate_evaluation.candidate_index}",
            metrics=_candidate_metrics(candidate_evaluation),
            predicted=json.dumps(
                {
                    "payload": candidate_evaluation.candidate_import.payload,
                    "claim_text": candidate_evaluation.candidate_import.claim_text,
                    "evidence_spans": [
                        span.model_dump(mode="json")
                        for span in candidate_evaluation.candidate_import.evidence_spans
                    ],
                },
                sort_keys=True,
            ),
            gold=None,
            extra={
                "support_label": candidate_evaluation.support_label,
                "support_reasoning": candidate_evaluation.support_reasoning,
                "validation_status": candidate_evaluation.validation_status,
                "exact_preferred_match": candidate_evaluation.exact_preferred_match,
                "profile_id": case.profile.profile_id,
                "profile_version": case.profile.profile_version,
                "judge_trace_id": case_evaluation.judge_run.trace_id,
            },
            trace_id=case_evaluation.extraction_run.trace_id,
        )
    observability_api.finish_run(run_id=run_id)
    return run_id


def _candidate_metrics(candidate_evaluation: CandidateEvaluationRecord) -> dict[str, float]:
    """Convert one benchmark candidate evaluation into numeric experiment metrics."""

    support_label = candidate_evaluation.support_label
    validation_status = candidate_evaluation.validation_status
    return {
        "supported": 1.0 if support_label == "supported" else 0.0,
        "partially_supported": 1.0 if support_label == "partially_supported" else 0.0,
        "unsupported": 1.0 if support_label == "unsupported" else 0.0,
        "acceptable": 1.0 if support_label in {"supported", "partially_supported"} else 0.0,
        "valid": 1.0 if validation_status == "valid" else 0.0,
        "needs_review": 1.0 if validation_status == "needs_review" else 0.0,
        "invalid": 1.0 if validation_status == "invalid" else 0.0,
        "exact_preferred_match": 1.0 if candidate_evaluation.exact_preferred_match else 0.0,
    }


def _log_fixture_observability_aggregate(
    *,
    observability_api: _ObservabilityAPI | None,
    report: BenchmarkEvaluationReport,
) -> str | None:
    """Persist one family-level aggregate over a full benchmark invocation."""

    if observability_api is None or report.experiment_execution_id is None:
        return None
    config = get_config()
    source_run_ids = tuple(
        case.observability_run_id
        for case in report.cases
        if case.observability_run_id is not None
    )
    return observability_api.log_experiment_aggregate(
        dataset=config.evaluation.observability_dataset,
        family_id=report.experiment_execution_id,
        aggregate_type="onto_canon6.live_extraction_benchmark.summary",
        scenario_id=report.fixture_id,
        phase=config.evaluation.observability_phase,
        metrics={
            "case_count": report.summary.case_count,
            "supported_rate": report.summary.reasonableness.supported_rate,
            "acceptable_rate": report.summary.reasonableness.acceptable_rate,
            "valid_count": report.summary.validation.valid_count,
            "needs_review_count": report.summary.validation.needs_review_count,
            "invalid_count": report.summary.validation.invalid_count,
            "exact_precision": report.summary.canonicalization.precision,
            "exact_recall": report.summary.canonicalization.recall,
            "exact_f1": report.summary.canonicalization.f1,
        },
        provenance={
            "source_package": config.project.package_name,
            "fixture_id": report.fixture_id,
            "fixture_path": report.fixture_path,
        },
        source_run_ids=list(source_run_ids),
        project=config.project.name,
    )


def _judge_trace_id(*, case_id: str, source_ref: str) -> str:
    """Build a deterministic trace identifier for the reasonableness judge."""

    digest = hashlib.sha256(f"{case_id}\n{source_ref}".encode("utf-8")).hexdigest()[:16]
    return f"{get_config().project.package_name}.eval.reasonableness.{digest}"


def _load_judge_llm_client_api() -> _JudgeLLMClientAPI:
    """Import the required llm_client APIs lazily and fail loudly if missing."""

    try:
        module = import_module("llm_client")
    except ImportError as exc:
        raise ConfigError(
            "live evaluation requires llm_client to be installed; "
            "run `pip install -e ~/projects/llm_client` in this repo's .venv"
        ) from exc
    return _JudgeLLMClientAPI(
        get_model=cast(_GetModel, getattr(module, "get_model")),
        render_prompt=cast(_RenderPrompt, getattr(module, "render_prompt")),
        call_llm_structured=cast(_CallStructured, getattr(module, "call_llm_structured")),
    )


def _load_observability_api() -> _ObservabilityAPI:
    """Import the shared experiment-observability APIs lazily and fail loudly."""

    try:
        module = import_module("llm_client.observability")
    except ImportError as exc:
        raise ConfigError(
            "live evaluation observability requires llm_client to be installed; "
            "run `pip install -e ~/projects/llm_client` in this repo's .venv"
        ) from exc
    return _ObservabilityAPI(
        start_run=cast(_StartRun, getattr(module, "start_run")),
        finish_run=cast(_FinishRun, getattr(module, "finish_run")),
        log_item=cast(_LogItem, getattr(module, "log_item")),
        log_experiment_aggregate=cast(_LogAggregate, getattr(module, "log_experiment_aggregate")),
    )

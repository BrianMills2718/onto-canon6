"""prompt_eval-backed extraction prompt experiments.

This module adds the smallest useful experiment layer on top of the existing
Phase 5 benchmark slice:

1. it reuses the current benchmark fixture as the experiment corpus;
2. it compares explicit prompt variants over the same extraction task;
3. it scores trials deterministically against the local runtime contracts; and
4. it reloads the result family from shared observability before reporting.

The goal is not to replace the live benchmark. The goal is to stop doing
prompt iteration through ad hoc local loops when `prompt_eval` already exists
for that purpose.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from importlib import import_module
from pathlib import Path
from typing import Any, Awaitable, Callable, Protocol, cast

from ..config import ConfigError, PromptEvalVariantConfig, get_config
from ..ontology_runtime import load_effective_profile
from ..pipeline import (
    ProfileRef,
    TextExtractionResponse,
    candidate_import_from_extracted,
    render_entity_type_catalog,
    render_predicate_catalog,
)
from .models import (
    BenchmarkCase,
    ExtractionPromptExperimentReport,
    PromptEvalComparisonMethod,
    PromptEvalFailureCategory,
    PromptVariantComparisonRecord,
    PromptVariantSummaryRecord,
)
from .service import (
    _score_exact_canonicalization,
    _validate_candidate_imports,
    load_benchmark_fixture,
)


class ExtractionPromptExperimentError(RuntimeError):
    """Raised when the prompt-eval extraction experiment cannot run honestly."""


class _GetModel(Protocol):
    """Resolve one model ID from a configured task name."""

    def __call__(self, task: str) -> str: ...


class _RenderPrompt(Protocol):
    """Render one YAML/Jinja prompt template into chat messages."""

    def __call__(self, template_path: str | Path, **context: Any) -> list[dict[str, str]]: ...


class _PromptEvalRun(Protocol):
    """Run one prompt-eval experiment asynchronously."""

    def __call__(
        self,
        experiment: Any,
        evaluator: Callable[[Any, Any | None], Any],
        *,
        observability: Any,
    ) -> Awaitable[Any]: ...


class _PromptEvalLoad(Protocol):
    """Reload one prompt-eval execution family from shared observability."""

    def __call__(
        self,
        execution_id: str,
        *,
        project: str | None = None,
        dataset: str | None = None,
        limit: int = 1000,
    ) -> Any: ...


class _PromptEvalCompare(Protocol):
    """Compare two prompt variants from one prompt-eval result."""

    def __call__(
        self,
        result: Any,
        variant_a: str,
        variant_b: str,
        *,
        confidence: float = 0.95,
        method: str = "bootstrap",
        dimension: str | None = None,
    ) -> Any: ...


@dataclass(frozen=True)
class _LLMClientAPI:
    """Small typed view of the llm_client APIs used by prompt experiments."""

    get_model: _GetModel
    render_prompt: _RenderPrompt


@dataclass(frozen=True)
class _PromptEvalAPI:
    """Small typed view of the prompt_eval APIs used by this module."""

    Experiment: type[Any]
    ExperimentInput: type[Any]
    PromptVariant: type[Any]
    EvalScore: type[Any]
    PromptEvalObservabilityConfig: type[Any]
    run_experiment: _PromptEvalRun
    load_result_from_observability: _PromptEvalLoad
    compare_variants: _PromptEvalCompare


class ExtractionPromptExperimentService:
    """Run deterministic prompt_eval experiments over the extraction benchmark.

    The service is intentionally bounded:

    - it only supports fixtures where every case shares the same profile;
    - it uses deterministic scoring over exact-fidelity and validation lanes;
    - it keeps prompt assets local to `onto-canon6` and records prompt refs as
      explicit observability metadata;
    - it does not mutate candidate review state or the operational stores.
    """

    def __init__(self) -> None:
        """Load the config-backed defaults for extraction prompt experiments."""

        config = get_config()
        experiment = config.evaluation.prompt_experiment
        self._benchmark_fixture = config.evaluation_benchmark_fixture()
        self._experiment_name = experiment.experiment_name
        self._observability_dataset = experiment.observability_dataset
        self._observability_phase = experiment.observability_phase
        self._selection_task = experiment.selection_task
        self._n_runs = experiment.n_runs
        self._temperature = experiment.temperature
        self._timeout_seconds = experiment.timeout_seconds
        self._num_retries = experiment.num_retries
        self._max_budget_usd = experiment.max_budget_usd
        self._max_output_tokens = experiment.max_output_tokens
        self._baseline_variant_name = experiment.baseline_variant_name
        self._comparison_method = experiment.comparison_method
        self._comparison_confidence = experiment.comparison_confidence
        self._variant_configs = experiment.variants
        self._overlay_root = config.overlay_root()

    def run_prompt_experiment(
        self,
        *,
        fixture_path: Path | str | None = None,
        case_limit: int | None = None,
        n_runs: int | None = None,
        comparison_method: PromptEvalComparisonMethod | None = None,
    ) -> ExtractionPromptExperimentReport:
        """Run the extraction prompt experiment from synchronous code.

        This helper exists for the CLI and normal scripts. Notebook callers
        with an active event loop should use `await run_prompt_experiment_async`
        directly so the service does not try to nest a new event loop.
        """

        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(
                self.run_prompt_experiment_async(
                    fixture_path=fixture_path,
                    case_limit=case_limit,
                    n_runs=n_runs,
                    comparison_method=comparison_method,
                )
            )
        raise ExtractionPromptExperimentError(
            "run_prompt_experiment() cannot run inside an active event loop; "
            "use `await run_prompt_experiment_async(...)` instead"
        )

    async def run_prompt_experiment_async(
        self,
        *,
        fixture_path: Path | str | None = None,
        case_limit: int | None = None,
        n_runs: int | None = None,
        comparison_method: PromptEvalComparisonMethod | None = None,
    ) -> ExtractionPromptExperimentReport:
        """Run the configured extraction prompt experiment asynchronously."""

        resolved_fixture_path = Path(fixture_path or self._benchmark_fixture)
        fixture = load_benchmark_fixture(resolved_fixture_path)
        cases = fixture.cases if case_limit is None else fixture.cases[:case_limit]
        if not cases:
            raise ExtractionPromptExperimentError("prompt_eval requires at least one benchmark case")
        effective_n_runs = n_runs or self._n_runs
        effective_comparison_method = comparison_method or self._comparison_method
        _validate_experiment_shape(
            case_count=len(cases),
            n_runs=effective_n_runs,
            comparison_method=effective_comparison_method,
        )
        profile = _require_single_profile(cases)

        llm_client_api = _load_llm_client_api()
        prompt_eval_api = _load_prompt_eval_api()
        selected_model = llm_client_api.get_model(self._selection_task)
        loaded_profile = load_effective_profile(
            profile.profile_id,
            profile.profile_version,
            overlay_root=self._overlay_root,
        )
        render_context = {
            "profile_id": profile.profile_id,
            "profile_version": profile.profile_version,
            "predicate_catalog": render_predicate_catalog(loaded_profile),
            "entity_type_catalog": render_entity_type_catalog(loaded_profile),
        }
        variants = [
            prompt_eval_api.PromptVariant(
                name=variant.name,
                messages=llm_client_api.render_prompt(
                    get_config().evaluation_prompt_experiment_variant_template(
                        variant.prompt_template
                    ),
                    **render_context,
                ),
                prompt_ref=variant.prompt_ref,
                model=selected_model,
                temperature=self._temperature,
                kwargs={
                    "task": self._selection_task,
                    "max_budget": self._max_budget_usd,
                    "timeout": self._timeout_seconds,
                    "num_retries": self._num_retries,
                    "max_tokens": self._max_output_tokens,
                    "prompt_ref": variant.prompt_ref,
                },
            )
            for variant in self._variant_configs
        ]
        experiment = prompt_eval_api.Experiment(
            name=self._experiment_name,
            variants=variants,
            inputs=[
                prompt_eval_api.ExperimentInput(
                    id=case.case_id,
                    content=_format_case_input(case),
                    expected=case,
                )
                for case in cases
            ],
            n_runs=effective_n_runs,
            response_model=TextExtractionResponse,
        )
        observability = prompt_eval_api.PromptEvalObservabilityConfig(
            project=get_config().project.name,
            dataset=self._observability_dataset,
            scenario_id=fixture.fixture_id,
            phase=self._observability_phase,
            provenance={
                "source_package": get_config().project.package_name,
                "selection_task": self._selection_task,
                "fixture_id": fixture.fixture_id,
                "fixture_path": str(resolved_fixture_path),
            },
        )
        def evaluate_trial(output: Any, expected: Any | None) -> Any:
            """Score one prompt_eval trial through the deterministic local lanes."""

            return _score_prompt_eval_trial(
                output=output,
                expected=expected,
                eval_score_cls=prompt_eval_api.EvalScore,
                overlay_root=self._overlay_root,
            )

        result = await prompt_eval_api.run_experiment(
            experiment,
            evaluator=evaluate_trial,
            observability=observability,
        )
        execution_id = getattr(result, "execution_id", None)
        if not isinstance(execution_id, str) or not execution_id.strip():
            raise ExtractionPromptExperimentError(
                "prompt_eval did not return an execution_id for the experiment run"
            )
        loaded_result = prompt_eval_api.load_result_from_observability(
            execution_id,
            project=get_config().project.name,
            dataset=self._observability_dataset,
            limit=_observability_load_limit(
                case_count=len(cases),
                variant_count=len(self._variant_configs),
                n_runs=int(experiment.n_runs),
            ),
        )
        _validate_loaded_result_comparison_shape(
            result=loaded_result,
            comparison_method=effective_comparison_method,
            baseline_variant_name=self._baseline_variant_name,
            variant_names=tuple(variant.name for variant in self._variant_configs),
        )
        comparisons = tuple(
            prompt_eval_api.compare_variants(
                loaded_result,
                variant.name,
                self._baseline_variant_name,
                confidence=self._comparison_confidence,
                method=effective_comparison_method,
            )
            for variant in self._variant_configs
            if variant.name != self._baseline_variant_name
        )
        return _build_prompt_experiment_report(
            result=loaded_result,
            comparisons=comparisons,
            fixture_id=fixture.fixture_id,
            fixture_path=resolved_fixture_path,
            case_count=len(cases),
            n_runs=int(experiment.n_runs),
            observability_dataset=self._observability_dataset,
            observability_phase=self._observability_phase,
            baseline_variant_name=self._baseline_variant_name,
            variant_configs=self._variant_configs,
        )


def _score_prompt_eval_trial(
    *,
    output: Any,
    expected: Any,
    eval_score_cls: type[Any],
    overlay_root: Path,
) -> Any:
    """Score one extracted output deterministically against a benchmark case."""

    zero_dimensions = {
        "exact_f1": 0.0,
        "structural_usable_rate": 0.0,
        "count_alignment": 0.0,
    }
    try:
        if not isinstance(expected, BenchmarkCase):
            raise ExtractionPromptExperimentError(
                "prompt_eval expected payload must be one BenchmarkCase"
            )
        if not isinstance(output, TextExtractionResponse):
            raise ExtractionPromptExperimentError(
                "prompt_eval extraction output must be a TextExtractionResponse"
            )
        candidate_imports = tuple(
            candidate_import_from_extracted(
                candidate=candidate,
                profile=expected.profile,
                submitted_by="agent:onto_canon6_prompt_eval",
                source_artifact=expected.source_artifact,
            )
            for candidate in output.candidates
        )
        validation_statuses = _validate_candidate_imports(
            candidate_imports=candidate_imports,
            profile=expected.profile,
            overlay_root=overlay_root,
        )
        _, canonicalization = _score_exact_canonicalization(
            expected_candidates=expected.expected_candidates,
            observed_candidates=candidate_imports,
        )
        observed_count = len(candidate_imports)
        expected_count = len(expected.expected_candidates)
        usable_count = sum(status != "invalid" for status in validation_statuses)
        usable_rate = usable_count / observed_count if observed_count else 0.0
        count_alignment = 1.0 - (
            abs(observed_count - expected_count) / max(observed_count, expected_count, 1)
        )
        overall_score = round(
            canonicalization.f1 * 0.65 + usable_rate * 0.25 + count_alignment * 0.10,
            4,
        )
        return eval_score_cls(
            score=overall_score,
            dimension_scores={
                "exact_f1": canonicalization.f1,
                "structural_usable_rate": round(usable_rate, 4),
                "count_alignment": round(count_alignment, 4),
            },
            reasoning=(
                "Deterministic extraction score from exact canonical fidelity, "
                f"structural usability, and candidate-count alignment. "
                f"observed={observed_count} expected={expected_count} "
                f"usable={usable_count}"
            ),
        )
    except Exception as exc:
        return eval_score_cls(
            score=0.0,
            dimension_scores=zero_dimensions,
            reasoning=f"deterministic prompt_eval scoring failed: {exc}",
        )


def _require_single_profile(cases: tuple[BenchmarkCase, ...]) -> ProfileRef:
    """Fail loudly unless every benchmark case shares one profile reference."""

    profile_refs = {(case.profile.profile_id, case.profile.profile_version) for case in cases}
    if len(profile_refs) != 1:
        raise ExtractionPromptExperimentError(
            "prompt_eval extraction experiments require a single shared profile across all cases"
        )
    profile_id, profile_version = next(iter(profile_refs))
    return ProfileRef(profile_id=profile_id, profile_version=profile_version)


def _format_case_input(case: BenchmarkCase) -> str:
    """Format one benchmark case into the single `{input}` slot prompt_eval supports."""

    source_label = case.source_artifact.source_label or "none"
    source_text = case.source_artifact.content_text
    if source_text is None or not source_text.strip():
        raise ExtractionPromptExperimentError(
            f"benchmark case {case.case_id} is missing source text for prompt_eval"
        )
    return (
        f"Case id: {case.case_id}\n"
        f"Source kind: {case.source_artifact.source_kind}\n"
        f"Source ref: {case.source_artifact.source_ref}\n"
        f"Source label: {source_label}\n\n"
        "Source text:\n"
        f"{source_text}"
    )


def _observability_load_limit(*, case_count: int, variant_count: int, n_runs: int) -> int:
    """Compute a safe observability scan limit for one prompt_eval run family."""

    return max(100, case_count * variant_count * n_runs * 4)


def _validate_experiment_shape(
    *,
    case_count: int,
    n_runs: int,
    comparison_method: str,
) -> None:
    """Fail loudly on experiment shapes that cannot support the chosen comparison."""

    if comparison_method == "welch" and case_count * n_runs < 2:
        raise ExtractionPromptExperimentError(
            "welch comparison requires at least two scored trials per variant; "
            "increase case_count or n_runs, or switch the comparison method"
        )


def _validate_loaded_result_comparison_shape(
    *,
    result: Any,
    comparison_method: str,
    baseline_variant_name: str,
    variant_names: tuple[str, ...],
) -> None:
    """Fail loudly if live trial errors make the chosen comparison impossible.

    The pre-run shape check can only reason about planned trial counts. Live
    prompt experiments can still lose trials to provider or schema errors, and
    Welch requires at least two scored trials in each compared variant. This
    helper turns the downstream stats failure into an experiment-specific error
    with the observed successful-trial counts.
    """

    if comparison_method != "welch":
        return
    summary_obj = getattr(result, "summary", None)
    if not isinstance(summary_obj, dict):
        raise ExtractionPromptExperimentError("prompt_eval result summary must be a mapping")
    success_counts: dict[str, int] = {}
    for variant_name in variant_names:
        variant_summary = summary_obj.get(variant_name)
        if variant_summary is None:
            raise ExtractionPromptExperimentError(
                f"prompt_eval result is missing summary for variant {variant_name!r}"
            )
        n_trials = int(getattr(variant_summary, "n_trials"))
        n_errors = int(getattr(variant_summary, "n_errors"))
        success_counts[variant_name] = max(0, n_trials - n_errors)
    baseline_successes = success_counts[baseline_variant_name]
    insufficient = {
        variant_name: success_count
        for variant_name, success_count in success_counts.items()
        if success_count < 2 or baseline_successes < 2
    }
    if insufficient:
        rendered = ", ".join(
            f"{variant_name}={success_count}" for variant_name, success_count in sorted(insufficient.items())
        )
        raise ExtractionPromptExperimentError(
            "welch comparison became impossible after live trial errors; "
            f"successful_scored_trials=({rendered}). rerun with more cases or runs, "
            "or switch the comparison method"
        )


def _build_prompt_experiment_report(
    *,
    result: Any,
    comparisons: tuple[Any, ...],
    fixture_id: str,
    fixture_path: Path,
    case_count: int,
    n_runs: int,
    observability_dataset: str,
    observability_phase: str,
    baseline_variant_name: str,
    variant_configs: tuple[PromptEvalVariantConfig, ...],
) -> ExtractionPromptExperimentReport:
    """Convert prompt_eval result objects into the repo-local typed report."""

    execution_id = getattr(result, "execution_id", None)
    experiment_name = getattr(result, "experiment_name", None)
    if not isinstance(execution_id, str) or not execution_id.strip():
        raise ExtractionPromptExperimentError("prompt_eval report is missing execution_id")
    if not isinstance(experiment_name, str) or not experiment_name.strip():
        raise ExtractionPromptExperimentError("prompt_eval report is missing experiment_name")

    summary_obj = getattr(result, "summary", None)
    if not isinstance(summary_obj, dict):
        raise ExtractionPromptExperimentError("prompt_eval report summary must be a mapping")
    variant_by_name = {variant.name: variant for variant in variant_configs}
    variant_summaries = []
    trial_obj = getattr(result, "trials", None)
    if not isinstance(trial_obj, list):
        raise ExtractionPromptExperimentError("prompt_eval report trials must be a list")
    failures_by_variant = _summarize_trial_failures_by_variant(
        trials=tuple(trial_obj),
        variant_names=tuple(variant_by_name.keys()),
    )
    for variant_name, variant_summary in summary_obj.items():
        if not isinstance(variant_name, str) or variant_name not in variant_by_name:
            raise ExtractionPromptExperimentError(
                f"prompt_eval returned an unknown variant summary: {variant_name!r}"
            )
        variant_config = variant_by_name[variant_name]
        dimension_means = getattr(variant_summary, "dimension_means", None)
        variant_summaries.append(
            PromptVariantSummaryRecord(
                variant_name=variant_name,
                prompt_template=variant_config.prompt_template,
                prompt_ref=variant_config.prompt_ref,
                n_trials=int(getattr(variant_summary, "n_trials")),
                successful_trials=max(
                    0,
                    int(getattr(variant_summary, "n_trials"))
                    - int(getattr(variant_summary, "n_errors")),
                ),
                n_errors=int(getattr(variant_summary, "n_errors")),
                mean_score=getattr(variant_summary, "mean_score", None),
                std_score=getattr(variant_summary, "std_score", None),
                dimension_means=dict(dimension_means or {}),
                failure_counts=failures_by_variant[variant_name],
                mean_cost=float(getattr(variant_summary, "mean_cost")),
                mean_latency_ms=float(getattr(variant_summary, "mean_latency_ms")),
                total_tokens=int(getattr(variant_summary, "total_tokens")),
            )
        )
    comparison_records = tuple(
        PromptVariantComparisonRecord(
            variant_a=str(getattr(comparison, "variant_a")),
            variant_b=str(getattr(comparison, "variant_b")),
            mean_a=float(getattr(comparison, "mean_a")),
            mean_b=float(getattr(comparison, "mean_b")),
            difference=float(getattr(comparison, "difference")),
            ci_lower=float(getattr(comparison, "ci_lower")),
            ci_upper=float(getattr(comparison, "ci_upper")),
            significant=bool(getattr(comparison, "significant")),
            method=cast(
                PromptEvalComparisonMethod,
                str(getattr(comparison, "method")),
            ),
            detail=str(getattr(comparison, "detail")),
        )
        for comparison in comparisons
    )
    return ExtractionPromptExperimentReport(
        experiment_name=experiment_name,
        fixture_id=fixture_id,
        fixture_path=str(fixture_path),
        execution_id=execution_id,
        observability_dataset=observability_dataset,
        observability_phase=observability_phase,
        case_count=case_count,
        n_runs=n_runs,
        baseline_variant_name=baseline_variant_name,
        variant_summaries=tuple(sorted(variant_summaries, key=lambda item: item.variant_name)),
        comparisons=comparison_records,
    )


def _summarize_trial_failures_by_variant(
    *,
    trials: tuple[Any, ...],
    variant_names: tuple[str, ...],
) -> dict[str, dict[PromptEvalFailureCategory, int]]:
    """Aggregate classified trial failures by variant name."""

    counts_by_variant: dict[str, dict[PromptEvalFailureCategory, int]] = {
        variant_name: {} for variant_name in variant_names
    }
    for trial in trials:
        variant_name = getattr(trial, "variant_name", None)
        if not isinstance(variant_name, str) or variant_name not in counts_by_variant:
            raise ExtractionPromptExperimentError(
                f"prompt_eval returned a trial with unknown variant {variant_name!r}"
            )
        category = _classify_prompt_eval_trial_failure(trial)
        if category is None:
            continue
        variant_counts = counts_by_variant[variant_name]
        variant_counts[category] = variant_counts.get(category, 0) + 1
    return counts_by_variant


def _classify_prompt_eval_trial_failure(trial: Any) -> PromptEvalFailureCategory | None:
    """Classify one prompt_eval trial failure into a stable repo-local bucket."""

    error_obj = getattr(trial, "error", None)
    reasoning_obj = getattr(trial, "reasoning", None)
    error_text = error_obj.strip().lower() if isinstance(error_obj, str) else ""
    reasoning_text = reasoning_obj.strip().lower() if isinstance(reasoning_obj, str) else ""
    if not error_text and not reasoning_text:
        return None
    combined = f"{error_text}\n{reasoning_text}".strip()
    if "key limit exceeded" in combined or "rate limit" in combined or "429" in combined:
        return "provider_rate_limited"
    if "max_tokens length limit" in combined or "finish_reason='length'" in combined:
        return "length_truncated"
    if "multiple tool calls" in combined:
        return "multiple_tool_calls"
    if "entity fillers require entity_id or name" in combined:
        return "unnamed_entity_filler"
    if "candidate roles must not be empty" in combined:
        return "empty_roles"
    if "evidence span" in combined and "did not resolve" in combined:
        return "bad_evidence_span"
    if "validation error for textextractionresponse" in combined or "pydantic.dev" in combined:
        return "schema_validation_error"
    if error_text:
        return "other_failure"
    return None


def _load_llm_client_api() -> _LLMClientAPI:
    """Import the required llm_client APIs lazily and fail loudly if missing."""

    try:
        module = import_module("llm_client")
    except ImportError as exc:
        raise ConfigError(
            "prompt_eval extraction experiments require llm_client to be installed; "
            "run `pip install -e ~/projects/llm_client` in this repo's .venv"
        ) from exc
    return _LLMClientAPI(
        get_model=cast(_GetModel, getattr(module, "get_model")),
        render_prompt=cast(_RenderPrompt, getattr(module, "render_prompt")),
    )


def _load_prompt_eval_api() -> _PromptEvalAPI:
    """Import the required prompt_eval APIs lazily and fail loudly if missing."""

    try:
        module = import_module("prompt_eval")
    except ImportError as exc:
        raise ConfigError(
            "prompt_eval extraction experiments require prompt_eval to be installed; "
            "run `pip install -e ~/projects/prompt_eval` in this repo's .venv"
        ) from exc
    return _PromptEvalAPI(
        Experiment=cast(type[Any], getattr(module, "Experiment")),
        ExperimentInput=cast(type[Any], getattr(module, "ExperimentInput")),
        PromptVariant=cast(type[Any], getattr(module, "PromptVariant")),
        EvalScore=cast(type[Any], getattr(module, "EvalScore")),
        PromptEvalObservabilityConfig=cast(
            type[Any],
            getattr(module, "PromptEvalObservabilityConfig"),
        ),
        run_experiment=cast(_PromptEvalRun, getattr(module, "run_experiment")),
        load_result_from_observability=cast(
            _PromptEvalLoad,
            getattr(module, "load_result_from_observability"),
        ),
        compare_variants=cast(_PromptEvalCompare, getattr(module, "compare_variants")),
    )

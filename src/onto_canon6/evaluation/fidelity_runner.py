"""Runner that connects prepared fidelity experiments to prompt_eval and scores results.

Bridges the gap between ``fidelity_experiment.PreparedExperiment`` (which only
prepares inputs without calling LLMs) and ``prompt_eval.run_experiment()``
(which actually executes LLM calls and collects trials). After execution, each
trial is scored with the ancestor evaluator from ``ancestor_evaluator.py`` and
aggregate metrics are computed.

Implements Plan 0017, Component 5 (fidelity experiment execution layer).
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from importlib import import_module
from pathlib import Path
from typing import Any, Awaitable, Callable, Mapping, Protocol, cast

from pydantic import BaseModel, ConfigDict, Field

from onto_canon6.evaluation.ancestor_evaluator import (
    AncestorEvalScore,
    AncestorEvaluatorCallable,
    make_ancestor_evaluator,
)
from onto_canon6.evaluation.fidelity_experiment import (
    ExperimentItem,
    FidelityLevel,
    PreparedExperiment,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Result data models
# ---------------------------------------------------------------------------


class FidelityItemResult(BaseModel):
    """Scored result for one fidelity experiment trial.

    Combines the prompt_eval trial output with ancestor evaluator scoring.
    Each item corresponds to one (entity, fidelity_level) pair that was sent
    to the LLM.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    entity_name: str = Field(min_length=1)
    fidelity_level: FidelityLevel
    reference_type: str = Field(min_length=1)
    pick: str = Field(
        description="The SUMO type the LLM chose (raw output, stripped)."
    )
    ancestor_eval_score: float = Field(
        ge=0.0,
        description=(
            "Overall ancestor-aware score from the evaluator. "
            "Can exceed 1.0 when the LLM picks a more-specific descendant "
            "of the reference type."
        ),
    )
    exact_match: bool
    ancestor_match: bool
    specificity: float = Field(ge=0.0)
    pick_exists: bool = Field(
        description="Whether the LLM's pick is a known SUMO type.",
    )
    cost: float = Field(default=0.0, ge=0.0)
    error: str | None = Field(
        default=None,
        description="Error message if the trial failed.",
    )


class FidelityExperimentReport(BaseModel):
    """Aggregated report for a single-model fidelity experiment run.

    Contains per-item results and aggregate metrics across fidelity levels.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    model: str = Field(min_length=1)
    experiment_name: str = Field(min_length=1)
    execution_id: str = Field(
        min_length=1,
        description="prompt_eval execution family identifier.",
    )
    entity_count: int = Field(ge=0)
    fidelity_levels: tuple[FidelityLevel, ...]
    items: tuple[FidelityItemResult, ...]
    # Aggregate metrics
    ancestor_match_rate: float = Field(
        ge=0.0, le=1.0,
        description="Fraction of items where pick is ancestor-or-equal of reference.",
    )
    exact_match_rate: float = Field(
        ge=0.0, le=1.0,
        description="Fraction of items where pick == reference.",
    )
    mean_specificity: float = Field(
        ge=0.0,
        description="Mean specificity across all successfully scored items.",
    )
    wrong_branch_rate: float = Field(
        ge=0.0, le=1.0,
        description="Fraction of items where pick is neither ancestor nor descendant.",
    )
    mean_score: float = Field(
        ge=0.0, le=1.0,
        description="Mean overall ancestor-aware score.",
    )
    total_cost: float = Field(
        ge=0.0,
        description="Total LLM cost for the experiment run.",
    )
    error_count: int = Field(
        ge=0,
        description="Number of items that failed (LLM error, not wrong answer).",
    )


class FidelityComparisonReport(BaseModel):
    """Comparison report across multiple models for the same prepared experiment.

    Contains one ``FidelityExperimentReport`` per model and a summary table
    comparing their aggregate metrics.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    models: tuple[str, ...] = Field(min_length=1)
    entity_count: int = Field(ge=0)
    fidelity_levels: tuple[FidelityLevel, ...]
    reports: tuple[FidelityExperimentReport, ...]
    comparison_table: tuple[dict[str, Any], ...] = Field(
        description=(
            "One row per model with keys: model, ancestor_match_rate, "
            "exact_match_rate, mean_specificity, wrong_branch_rate, "
            "mean_score, total_cost, error_count."
        ),
    )


# ---------------------------------------------------------------------------
# Protocol types for lazy imports
# ---------------------------------------------------------------------------


class _GetModel(Protocol):
    """Resolve one model ID from a configured task name."""

    def __call__(self, task: str, *, use_performance: bool = True) -> str: ...


class _RenderPrompt(Protocol):
    """Render one YAML/Jinja prompt template into chat messages."""

    def __call__(
        self, template_path: str | Path | None = None, **context: Any
    ) -> list[dict[str, str]]: ...


class _PromptEvalRun(Protocol):
    """Run one prompt-eval experiment asynchronously."""

    def __call__(
        self,
        experiment: Any,
        evaluator: Callable[[Any, Any | None], Any] | None = None,
        corpus_evaluator: Any | None = None,
        observability: Any = True,
    ) -> Awaitable[Any]: ...


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_DEFAULT_EXPERIMENT_NAME = "onto_canon6_fidelity_type_assignment"
_DEFAULT_FIDELITY_TASK = "fidelity_experiment"
_DEFAULT_MAX_BUDGET_USD = 0.25


def _load_llm_client_api() -> tuple[_GetModel, _RenderPrompt]:
    """Lazily import the llm_client APIs we need."""
    try:
        module = import_module("llm_client")
    except ImportError as exc:
        raise RuntimeError(
            "fidelity_runner requires llm_client; "
            "run `pip install -e ~/projects/llm_client` in this repo's .venv"
        ) from exc
    return (
        cast(_GetModel, getattr(module, "get_model")),
        cast(_RenderPrompt, getattr(module, "render_prompt")),
    )


def _load_prompt_eval_api() -> Mapping[str, Any]:
    """Lazily import prompt_eval types and runner."""
    try:
        module = import_module("prompt_eval")
    except ImportError as exc:
        raise RuntimeError(
            "fidelity_runner requires prompt_eval; "
            "run `pip install -e ~/projects/prompt_eval` in this repo's .venv"
        ) from exc
    return {
        "Experiment": getattr(module, "Experiment"),
        "ExperimentInput": getattr(module, "ExperimentInput"),
        "PromptVariant": getattr(module, "PromptVariant"),
        "EvalScore": getattr(module, "EvalScore"),
        "PromptEvalObservabilityConfig": getattr(module, "PromptEvalObservabilityConfig"),
        "run_experiment": getattr(module, "run_experiment"),
    }


def _resolve_model(
    model: str | None,
    task: str,
) -> str:
    """Resolve the model, falling back to llm_client task-based selection."""
    if model is not None:
        return model
    get_model, _ = _load_llm_client_api()
    return get_model(task, use_performance=False)


def _build_prompt_eval_experiment(
    prepared: PreparedExperiment,
    *,
    model: str,
    rendered_messages: list[list[dict[str, str]]],
    task: str,
    max_budget: float,
    experiment_name: str,
    pe_api: Mapping[str, Any],
) -> Any:
    """Construct a prompt_eval Experiment from a PreparedExperiment.

    Each ExperimentItem becomes an ExperimentInput. The rendered prompt content
    is placed into the {input} slot that prompt_eval substitutes. The expected
    value is the reference type for evaluator scoring.
    """
    inputs = []
    for i, item in enumerate(prepared.items):
        # The ExperimentInput.content is substituted into the {input} placeholder
        # in the variant messages. We pass the full rendered user message content
        # as the input content.
        user_content = ""
        for msg in rendered_messages[i]:
            if msg["role"] == "user":
                user_content = msg["content"]
                break
        inputs.append(
            pe_api["ExperimentInput"](
                id=f"{item.entity_name}__{item.fidelity_level.value}",
                content=user_content,
                expected=item.reference_type,
            )
        )

    # The system message is the same for all items (from the template).
    # Extract it from the first rendered message set.
    system_content = ""
    if rendered_messages:
        for msg in rendered_messages[0]:
            if msg["role"] == "system":
                system_content = msg["content"]
                break

    variant = pe_api["PromptVariant"](
        name=model,
        messages=[
            {"role": "system", "content": system_content},
            {"role": "user", "content": "{input}"},
        ],
        model=model,
        temperature=0.0,
        kwargs={
            "task": task,
            "max_budget": max_budget,
        },
    )

    return pe_api["Experiment"](
        name=experiment_name,
        variants=[variant],
        inputs=inputs,
        n_runs=1,
    )


def _render_all_prompts(
    prepared: PreparedExperiment,
    render_prompt: _RenderPrompt,
) -> list[list[dict[str, str]]]:
    """Render the prompt template for every item in the prepared experiment.

    Returns a list parallel to ``prepared.items`` where each element is the
    rendered chat messages for that item.
    """
    from onto_canon6.config import repo_root

    template_path = repo_root() / prepared.prompt_template
    rendered: list[list[dict[str, str]]] = []
    for item in prepared.items:
        messages = render_prompt(str(template_path), **item.prompt_variables)
        rendered.append(messages)
    return rendered


def _make_fidelity_evaluator(
    ancestor_eval: AncestorEvaluatorCallable,
    eval_score_cls: type[Any],
) -> Callable[[Any, Any | None], Any]:
    """Build the prompt_eval evaluator function that wraps the ancestor evaluator.

    The evaluator receives the raw LLM output (a string) and the expected
    reference type, scores it with the ancestor evaluator, and returns an
    EvalScore with dimension scores.

    Parameters
    ----------
    ancestor_eval:
        The ancestor evaluator callable from ``make_ancestor_evaluator()``.
    eval_score_cls:
        The ``EvalScore`` class from prompt_eval, passed in to avoid
        a redundant import inside the closure.
    """

    def evaluate(output: Any, expected: Any = None) -> Any:
        """Score one LLM type pick against the reference using ancestor evaluation."""
        if expected is None:
            return eval_score_cls(score=0.0, reasoning="No expected value provided")

        pick = str(output).strip()
        result: AncestorEvalScore = ancestor_eval(pick, str(expected))

        return eval_score_cls(
            score=result.score,
            dimension_scores={
                "exact_match": result.exact,
                "ancestor_match": result.ancestor_match,
                "specificity": result.specificity,
            },
            reasoning=(
                f"pick={result.pick!r} ref={result.reference!r} "
                f"exact={result.exact} ancestor={result.ancestor_match} "
                f"specificity={result.specificity:.3f} "
                f"pick_exists={result.pick_exists} ref_exists={result.reference_exists}"
            ),
        )

    return evaluate


def _build_item_results(
    prepared: PreparedExperiment,
    eval_result: Any,
    ancestor_eval: AncestorEvaluatorCallable,
) -> tuple[FidelityItemResult, ...]:
    """Convert prompt_eval trials into FidelityItemResult models.

    Re-scores each trial with the ancestor evaluator to capture the full
    AncestorEvalScore fields (pick_exists, etc.) that prompt_eval's evaluator
    protocol cannot convey through dimension scores alone.
    """
    trials = getattr(eval_result, "trials", [])
    # Build a lookup from input_id to ExperimentItem.
    item_by_id: dict[str, ExperimentItem] = {}
    for item in prepared.items:
        input_id = f"{item.entity_name}__{item.fidelity_level.value}"
        item_by_id[input_id] = item

    results: list[FidelityItemResult] = []
    for trial in trials:
        input_id = str(getattr(trial, "input_id", ""))
        maybe_item = item_by_id.get(input_id)
        if maybe_item is None:
            logger.warning("Trial input_id %r not found in prepared items", input_id)
            continue
        item = maybe_item

        error = getattr(trial, "error", None)
        output = getattr(trial, "output", None)
        cost = float(getattr(trial, "cost", 0.0))

        if error is not None or output is None:
            results.append(
                FidelityItemResult(
                    entity_name=item.entity_name,
                    fidelity_level=item.fidelity_level,
                    reference_type=item.reference_type,
                    pick="",
                    ancestor_eval_score=0.0,
                    exact_match=False,
                    ancestor_match=False,
                    specificity=0.0,
                    pick_exists=False,
                    cost=cost,
                    error=str(error) if error else "No output",
                )
            )
            continue

        pick = str(output).strip()
        score: AncestorEvalScore = ancestor_eval(pick, item.reference_type)
        results.append(
            FidelityItemResult(
                entity_name=item.entity_name,
                fidelity_level=item.fidelity_level,
                reference_type=item.reference_type,
                pick=pick,
                ancestor_eval_score=score.score,
                exact_match=score.exact > 0.5,
                ancestor_match=score.ancestor_match > 0.5,
                specificity=score.specificity,
                pick_exists=score.pick_exists,
                cost=cost,
            )
        )

    return tuple(results)


def _compute_aggregate_metrics(
    items: tuple[FidelityItemResult, ...],
) -> dict[str, float | int]:
    """Compute aggregate metrics from scored item results.

    Returns a dict with: ancestor_match_rate, exact_match_rate,
    mean_specificity, wrong_branch_rate, mean_score, total_cost, error_count.
    """
    if not items:
        return {
            "ancestor_match_rate": 0.0,
            "exact_match_rate": 0.0,
            "mean_specificity": 0.0,
            "wrong_branch_rate": 0.0,
            "mean_score": 0.0,
            "total_cost": 0.0,
            "error_count": 0,
        }

    error_count = sum(1 for it in items if it.error is not None)
    scored_items = [it for it in items if it.error is None]
    scored_count = len(scored_items)

    if scored_count == 0:
        return {
            "ancestor_match_rate": 0.0,
            "exact_match_rate": 0.0,
            "mean_specificity": 0.0,
            "wrong_branch_rate": 1.0,
            "mean_score": 0.0,
            "total_cost": sum(it.cost for it in items),
            "error_count": error_count,
        }

    ancestor_matches = sum(1 for it in scored_items if it.ancestor_match)
    exact_matches = sum(1 for it in scored_items if it.exact_match)
    wrong_branch = scored_count - ancestor_matches
    mean_specificity = sum(it.specificity for it in scored_items) / scored_count
    mean_score = sum(it.ancestor_eval_score for it in scored_items) / scored_count
    total_cost = sum(it.cost for it in items)

    return {
        "ancestor_match_rate": ancestor_matches / scored_count,
        "exact_match_rate": exact_matches / scored_count,
        "mean_specificity": mean_specificity,
        "wrong_branch_rate": wrong_branch / scored_count,
        "mean_score": mean_score,
        "total_cost": total_cost,
        "error_count": error_count,
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def run_fidelity_experiment_async(
    prepared: PreparedExperiment,
    *,
    model: str | None = None,
    sumo_db_path: Path,
    task: str = _DEFAULT_FIDELITY_TASK,
    max_budget: float = _DEFAULT_MAX_BUDGET_USD,
    trace_id: str | None = None,
    experiment_name: str = _DEFAULT_EXPERIMENT_NAME,
    observability: bool = True,
) -> FidelityExperimentReport:
    """Run a fidelity experiment through prompt_eval and score with ancestor evaluator.

    Parameters
    ----------
    prepared:
        The prepared experiment from ``prepare_experiment()`` or
        ``prepare_experiment_from_config()``.
    model:
        Explicit model to use. If None, resolved via
        ``llm_client.get_model(task)``.
    sumo_db_path:
        Path to the ``sumo_plus.db`` file for ancestor evaluation.
    task:
        llm_client task name for cost tracking and model selection.
    max_budget:
        Maximum budget in USD per experiment run.
    trace_id:
        Base trace ID. If None, a UUID is generated.
    experiment_name:
        Name for the prompt_eval experiment.
    observability:
        Whether to emit shared llm_client observability records.

    Returns
    -------
    FidelityExperimentReport with per-item results and aggregate metrics.
    """
    resolved_model = _resolve_model(model, task)
    resolved_trace_id = trace_id or f"fidelity_exp_{uuid.uuid4().hex[:12]}"

    _, render_prompt = _load_llm_client_api()
    pe_api = _load_prompt_eval_api()

    # Render all prompts from the template.
    rendered_messages = _render_all_prompts(prepared, render_prompt)

    # Build the prompt_eval experiment.
    experiment = _build_prompt_eval_experiment(
        prepared,
        model=resolved_model,
        rendered_messages=rendered_messages,
        task=task,
        max_budget=max_budget,
        experiment_name=experiment_name,
        pe_api=pe_api,
    )

    # Build ancestor evaluator for scoring.
    ancestor_eval = make_ancestor_evaluator(sumo_db_path)

    # Build the prompt_eval evaluator wrapper.
    evaluator = _make_fidelity_evaluator(ancestor_eval, pe_api["EvalScore"])

    # Configure observability.
    obs_config: Any = False
    if observability:
        obs_config = pe_api["PromptEvalObservabilityConfig"](
            project="onto_canon6",
            dataset=experiment_name,
            scenario_id=f"fidelity_{resolved_trace_id}",
            phase="evaluation",
            provenance={
                "source_package": "onto_canon6",
                "task": task,
                "trace_id": resolved_trace_id,
                "model": resolved_model,
                "entity_count": prepared.entity_count,
                "fidelity_levels": [lv.value for lv in prepared.fidelity_levels],
            },
        )

    # Execute through prompt_eval.
    eval_result = await pe_api["run_experiment"](
        experiment,
        evaluator=evaluator,
        observability=obs_config,
    )

    execution_id = getattr(eval_result, "execution_id", None)
    if not isinstance(execution_id, str) or not execution_id.strip():
        execution_id = resolved_trace_id

    # Re-score each trial with the full ancestor evaluator for richer fields.
    item_results = _build_item_results(prepared, eval_result, ancestor_eval)

    # Aggregate metrics.
    metrics = _compute_aggregate_metrics(item_results)

    return FidelityExperimentReport(
        model=resolved_model,
        experiment_name=experiment_name,
        execution_id=execution_id,
        entity_count=prepared.entity_count,
        fidelity_levels=prepared.fidelity_levels,
        items=item_results,
        ancestor_match_rate=float(metrics["ancestor_match_rate"]),
        exact_match_rate=float(metrics["exact_match_rate"]),
        mean_specificity=float(metrics["mean_specificity"]),
        wrong_branch_rate=float(metrics["wrong_branch_rate"]),
        mean_score=float(metrics["mean_score"]),
        total_cost=float(metrics["total_cost"]),
        error_count=int(metrics["error_count"]),
    )


def run_fidelity_experiment(
    prepared: PreparedExperiment,
    *,
    model: str | None = None,
    sumo_db_path: Path,
    task: str = _DEFAULT_FIDELITY_TASK,
    max_budget: float = _DEFAULT_MAX_BUDGET_USD,
    trace_id: str | None = None,
    experiment_name: str = _DEFAULT_EXPERIMENT_NAME,
    observability: bool = True,
) -> FidelityExperimentReport:
    """Synchronous wrapper for ``run_fidelity_experiment_async``.

    Uses ``asyncio.run()`` when no event loop is active. Raises if called
    inside an active event loop (use the async variant directly).
    """
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(
            run_fidelity_experiment_async(
                prepared,
                model=model,
                sumo_db_path=sumo_db_path,
                task=task,
                max_budget=max_budget,
                trace_id=trace_id,
                experiment_name=experiment_name,
                observability=observability,
            )
        )
    raise RuntimeError(
        "run_fidelity_experiment() cannot run inside an active event loop; "
        "use `await run_fidelity_experiment_async(...)` instead"
    )


async def run_fidelity_comparison_async(
    prepared: PreparedExperiment,
    *,
    models: list[str],
    sumo_db_path: Path,
    task: str = _DEFAULT_FIDELITY_TASK,
    max_budget: float = _DEFAULT_MAX_BUDGET_USD,
    experiment_name: str = _DEFAULT_EXPERIMENT_NAME,
    observability: bool = True,
) -> FidelityComparisonReport:
    """Run the same fidelity experiment across multiple models and compare.

    Parameters
    ----------
    prepared:
        The prepared experiment.
    models:
        List of model identifiers to compare.
    sumo_db_path:
        Path to the ``sumo_plus.db`` file.
    task:
        llm_client task name for cost tracking.
    max_budget:
        Maximum budget in USD per model run.
    experiment_name:
        Base experiment name (model name is appended).
    observability:
        Whether to emit observability records.

    Returns
    -------
    FidelityComparisonReport with per-model reports and comparison table.
    """
    if not models:
        raise ValueError("models must not be empty for comparison")

    reports: list[FidelityExperimentReport] = []
    for model_id in models:
        trace_id = f"fidelity_cmp_{uuid.uuid4().hex[:12]}"
        report = await run_fidelity_experiment_async(
            prepared,
            model=model_id,
            sumo_db_path=sumo_db_path,
            task=task,
            max_budget=max_budget,
            trace_id=trace_id,
            experiment_name=f"{experiment_name}__{model_id}",
            observability=observability,
        )
        reports.append(report)

    comparison_table: list[dict[str, Any]] = []
    for report in reports:
        comparison_table.append({
            "model": report.model,
            "ancestor_match_rate": report.ancestor_match_rate,
            "exact_match_rate": report.exact_match_rate,
            "mean_specificity": report.mean_specificity,
            "wrong_branch_rate": report.wrong_branch_rate,
            "mean_score": report.mean_score,
            "total_cost": report.total_cost,
            "error_count": report.error_count,
        })

    return FidelityComparisonReport(
        models=tuple(models),
        entity_count=prepared.entity_count,
        fidelity_levels=prepared.fidelity_levels,
        reports=tuple(reports),
        comparison_table=tuple(comparison_table),
    )


def run_fidelity_comparison(
    prepared: PreparedExperiment,
    *,
    models: list[str],
    sumo_db_path: Path,
    task: str = _DEFAULT_FIDELITY_TASK,
    max_budget: float = _DEFAULT_MAX_BUDGET_USD,
    experiment_name: str = _DEFAULT_EXPERIMENT_NAME,
    observability: bool = True,
) -> FidelityComparisonReport:
    """Synchronous wrapper for ``run_fidelity_comparison_async``.

    Uses ``asyncio.run()`` when no event loop is active. Raises if called
    inside an active event loop (use the async variant directly).
    """
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(
            run_fidelity_comparison_async(
                prepared,
                models=models,
                sumo_db_path=sumo_db_path,
                task=task,
                max_budget=max_budget,
                experiment_name=experiment_name,
                observability=observability,
            )
        )
    raise RuntimeError(
        "run_fidelity_comparison() cannot run inside an active event loop; "
        "use `await run_fidelity_comparison_async(...)` instead"
    )

"""Tests for the fidelity experiment runner.

Verifies experiment construction, ancestor evaluator scoring integration,
and metric aggregation without making real LLM calls.

All prompt_eval and llm_client interactions are mocked.
"""

# mock-ok: prompt_eval runner makes LLM calls; llm_client model selection requires config

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))


from onto_canon6.evaluation.fidelity_experiment import (
    ExperimentItem,
    FidelityLevel,
    PreparedExperiment,
)
from onto_canon6.evaluation.fidelity_runner import (
    FidelityComparisonReport,
    FidelityExperimentReport,
    FidelityItemResult,
    _build_item_results,
    _compute_aggregate_metrics,
    _build_prompt_eval_experiment,
)


# ---------------------------------------------------------------------------
# Helpers and fixtures
# ---------------------------------------------------------------------------


@dataclass
class FakeEvalScore:
    """Stand-in for prompt_eval.EvalScore in tests."""

    score: float = 0.0
    dimension_scores: dict[str, float] = field(default_factory=dict)
    reasoning: str = ""


@dataclass
class FakeTrial:
    """Stand-in for prompt_eval.Trial in tests."""

    variant_name: str = "test_model"
    input_id: str = ""
    replicate: int = 0
    output: Any = None
    score: float | None = None
    dimension_scores: dict[str, float] | None = None
    reasoning: str | None = None
    cost: float = 0.001
    latency_ms: float = 50.0
    tokens_used: int = 100
    error: str | None = None
    trace_id: str | None = None


@dataclass
class FakeEvalResult:
    """Stand-in for prompt_eval.EvalResult in tests."""

    experiment_name: str = "test_fidelity"
    execution_id: str = "exec_test_123"
    variants: list[str] = field(default_factory=lambda: ["test_model"])
    trials: list[FakeTrial] = field(default_factory=list)
    summary: dict[str, Any] = field(default_factory=dict)


@dataclass
class FakeAncestorEvalScore:
    """Stand-in for AncestorEvalScore in tests."""

    score: float
    exact: float
    ancestor_match: float
    specificity: float
    pick: str
    reference: str
    pick_exists: bool = True
    reference_exists: bool = True


def _make_prepared_experiment(
    items: list[tuple[str, FidelityLevel, str]] | None = None,
) -> PreparedExperiment:
    """Build a minimal PreparedExperiment for testing.

    Each tuple in items is (entity_name, fidelity_level, reference_type).
    """
    if items is None:
        items = [
            ("CIA", FidelityLevel.TOP_LEVEL, "GovernmentOrganization"),
            ("V-BAT", FidelityLevel.TOP_LEVEL, "MilitaryAircraft"),
            ("Brian", FidelityLevel.TOP_LEVEL, "Human"),
        ]

    experiment_items = []
    for entity_name, level, ref_type in items:
        experiment_items.append(
            ExperimentItem(
                entity_name=entity_name,
                entity_context=f"Context for {entity_name}",
                reference_type=ref_type,
                fidelity_level=level,
                type_list=("Organization", "Human", "GovernmentOrganization", "MilitaryAircraft"),
                prompt_variables={
                    "entity_name": entity_name,
                    "entity_context": f"Context for {entity_name}",
                    "type_list": "- Organization\n- Human\n- GovernmentOrganization\n- MilitaryAircraft",
                },
            )
        )

    return PreparedExperiment(
        entity_count=len(set(name for name, _, _ in items)),
        fidelity_levels=tuple(dict.fromkeys(level for _, level, _ in items)),
        items=tuple(experiment_items),
        prompt_template="prompts/evaluation/fidelity_type_assignment.yaml",
    )


def _make_ancestor_eval(
    score_map: dict[tuple[str, str], FakeAncestorEvalScore] | None = None,
) -> Any:
    """Build a fake ancestor evaluator that returns pre-configured scores."""
    default_map = score_map or {}

    def _eval(pick: str, reference: str | None = None) -> FakeAncestorEvalScore:
        if reference is None:
            return FakeAncestorEvalScore(
                score=0.0, exact=0.0, ancestor_match=0.0,
                specificity=0.0, pick=pick, reference="",
                pick_exists=False, reference_exists=False,
            )
        key = (pick, reference)
        if key in default_map:
            return default_map[key]
        # Default: wrong branch.
        return FakeAncestorEvalScore(
            score=0.0, exact=0.0, ancestor_match=0.0,
            specificity=0.0, pick=pick, reference=reference,
            pick_exists=True, reference_exists=True,
        )

    return _eval


# ---------------------------------------------------------------------------
# _compute_aggregate_metrics tests
# ---------------------------------------------------------------------------


class TestComputeAggregateMetrics:
    """Verify metric aggregation logic."""

    def test_empty_items(self) -> None:
        """Empty item list produces zeroed metrics."""
        metrics = _compute_aggregate_metrics(())
        assert metrics["ancestor_match_rate"] == 0.0
        assert metrics["exact_match_rate"] == 0.0
        assert metrics["mean_specificity"] == 0.0
        assert metrics["wrong_branch_rate"] == 0.0
        assert metrics["error_count"] == 0

    def test_all_exact_matches(self) -> None:
        """All exact matches produce perfect scores."""
        items = tuple(
            FidelityItemResult(
                entity_name=f"entity_{i}",
                fidelity_level=FidelityLevel.TOP_LEVEL,
                reference_type="Human",
                pick="Human",
                ancestor_eval_score=1.0,
                exact_match=True,
                ancestor_match=True,
                specificity=1.0,
                pick_exists=True,
                cost=0.001,
            )
            for i in range(5)
        )
        metrics = _compute_aggregate_metrics(items)
        assert metrics["ancestor_match_rate"] == 1.0
        assert metrics["exact_match_rate"] == 1.0
        assert metrics["mean_specificity"] == 1.0
        assert metrics["wrong_branch_rate"] == 0.0
        assert metrics["mean_score"] == 1.0
        assert metrics["error_count"] == 0

    def test_mixed_results(self) -> None:
        """Mix of exact, ancestor, and wrong-branch produces correct rates."""
        items = (
            # Exact match.
            FidelityItemResult(
                entity_name="CIA",
                fidelity_level=FidelityLevel.TOP_LEVEL,
                reference_type="GovernmentOrganization",
                pick="GovernmentOrganization",
                ancestor_eval_score=1.0,
                exact_match=True,
                ancestor_match=True,
                specificity=1.0,
                pick_exists=True,
                cost=0.001,
            ),
            # Ancestor match (coarser pick).
            FidelityItemResult(
                entity_name="V-BAT",
                fidelity_level=FidelityLevel.TOP_LEVEL,
                reference_type="MilitaryAircraft",
                pick="Aircraft",
                ancestor_eval_score=0.6,
                exact_match=False,
                ancestor_match=True,
                specificity=0.75,
                pick_exists=True,
                cost=0.001,
            ),
            # Wrong branch.
            FidelityItemResult(
                entity_name="Brian",
                fidelity_level=FidelityLevel.TOP_LEVEL,
                reference_type="Human",
                pick="Organization",
                ancestor_eval_score=0.0,
                exact_match=False,
                ancestor_match=False,
                specificity=0.0,
                pick_exists=True,
                cost=0.001,
            ),
        )
        metrics = _compute_aggregate_metrics(items)
        assert metrics["ancestor_match_rate"] == pytest.approx(2.0 / 3.0)
        assert metrics["exact_match_rate"] == pytest.approx(1.0 / 3.0)
        assert metrics["wrong_branch_rate"] == pytest.approx(1.0 / 3.0)
        assert metrics["mean_specificity"] == pytest.approx((1.0 + 0.75 + 0.0) / 3.0)
        assert metrics["error_count"] == 0

    def test_error_items_excluded_from_rates(self) -> None:
        """Items with errors are counted separately, not in scored rates."""
        items = (
            FidelityItemResult(
                entity_name="CIA",
                fidelity_level=FidelityLevel.TOP_LEVEL,
                reference_type="GovernmentOrganization",
                pick="GovernmentOrganization",
                ancestor_eval_score=1.0,
                exact_match=True,
                ancestor_match=True,
                specificity=1.0,
                pick_exists=True,
                cost=0.001,
            ),
            FidelityItemResult(
                entity_name="V-BAT",
                fidelity_level=FidelityLevel.TOP_LEVEL,
                reference_type="MilitaryAircraft",
                pick="",
                ancestor_eval_score=0.0,
                exact_match=False,
                ancestor_match=False,
                specificity=0.0,
                pick_exists=False,
                cost=0.0,
                error="LLM timeout",
            ),
        )
        metrics = _compute_aggregate_metrics(items)
        # Only 1 scored item (the one without error).
        assert metrics["ancestor_match_rate"] == 1.0
        assert metrics["exact_match_rate"] == 1.0
        assert metrics["error_count"] == 1

    def test_all_errors(self) -> None:
        """All errored items produce zeroed rates with full error count."""
        items = (
            FidelityItemResult(
                entity_name="CIA",
                fidelity_level=FidelityLevel.TOP_LEVEL,
                reference_type="GovernmentOrganization",
                pick="",
                ancestor_eval_score=0.0,
                exact_match=False,
                ancestor_match=False,
                specificity=0.0,
                pick_exists=False,
                cost=0.0,
                error="timeout",
            ),
        )
        metrics = _compute_aggregate_metrics(items)
        assert metrics["ancestor_match_rate"] == 0.0
        assert metrics["wrong_branch_rate"] == 1.0
        assert metrics["error_count"] == 1


# ---------------------------------------------------------------------------
# _build_item_results tests
# ---------------------------------------------------------------------------


class TestBuildItemResults:
    """Verify trial-to-FidelityItemResult conversion."""

    def test_successful_trial_scored(self) -> None:
        """A successful trial is scored via the ancestor evaluator."""
        prepared = _make_prepared_experiment([
            ("CIA", FidelityLevel.TOP_LEVEL, "GovernmentOrganization"),
        ])
        score_map = {
            ("GovernmentOrganization", "GovernmentOrganization"): FakeAncestorEvalScore(
                score=1.0, exact=1.0, ancestor_match=1.0,
                specificity=1.0, pick="GovernmentOrganization",
                reference="GovernmentOrganization",
            ),
        }
        eval_result = FakeEvalResult(
            trials=[
                FakeTrial(
                    input_id="CIA__top_level",
                    output="GovernmentOrganization",
                    cost=0.002,
                ),
            ],
        )
        results = _build_item_results(prepared, eval_result, _make_ancestor_eval(score_map))
        assert len(results) == 1
        assert results[0].entity_name == "CIA"
        assert results[0].pick == "GovernmentOrganization"
        assert results[0].exact_match is True
        assert results[0].ancestor_match is True
        assert results[0].ancestor_eval_score == 1.0
        assert results[0].error is None

    def test_failed_trial_records_error(self) -> None:
        """A trial with an error produces an error item result."""
        prepared = _make_prepared_experiment([
            ("CIA", FidelityLevel.TOP_LEVEL, "GovernmentOrganization"),
        ])
        eval_result = FakeEvalResult(
            trials=[
                FakeTrial(
                    input_id="CIA__top_level",
                    output=None,
                    error="Connection timed out",
                    cost=0.0,
                ),
            ],
        )
        results = _build_item_results(prepared, eval_result, _make_ancestor_eval())
        assert len(results) == 1
        assert results[0].error is not None
        assert "timed out" in results[0].error
        assert results[0].pick == ""

    def test_wrong_branch_scored_zero(self) -> None:
        """A pick in the wrong SUMO branch gets zero ancestor match."""
        prepared = _make_prepared_experiment([
            ("Brian", FidelityLevel.TOP_LEVEL, "Human"),
        ])
        # Organization is not an ancestor of Human.
        eval_result = FakeEvalResult(
            trials=[
                FakeTrial(
                    input_id="Brian__top_level",
                    output="Organization",
                    cost=0.001,
                ),
            ],
        )
        results = _build_item_results(prepared, eval_result, _make_ancestor_eval())
        assert len(results) == 1
        assert results[0].ancestor_match is False
        assert results[0].exact_match is False
        assert results[0].ancestor_eval_score == 0.0

    def test_strips_whitespace_from_pick(self) -> None:
        """LLM output is stripped before scoring."""
        prepared = _make_prepared_experiment([
            ("CIA", FidelityLevel.TOP_LEVEL, "GovernmentOrganization"),
        ])
        score_map = {
            ("GovernmentOrganization", "GovernmentOrganization"): FakeAncestorEvalScore(
                score=1.0, exact=1.0, ancestor_match=1.0,
                specificity=1.0, pick="GovernmentOrganization",
                reference="GovernmentOrganization",
            ),
        }
        eval_result = FakeEvalResult(
            trials=[
                FakeTrial(
                    input_id="CIA__top_level",
                    output="  GovernmentOrganization  \n",
                    cost=0.001,
                ),
            ],
        )
        results = _build_item_results(prepared, eval_result, _make_ancestor_eval(score_map))
        assert results[0].pick == "GovernmentOrganization"


# ---------------------------------------------------------------------------
# _build_prompt_eval_experiment tests
# ---------------------------------------------------------------------------


class TestBuildPromptEvalExperiment:
    """Verify construction of prompt_eval Experiment from PreparedExperiment."""

    def test_correct_input_count(self) -> None:
        """Experiment should have one input per prepared item."""
        prepared = _make_prepared_experiment()

        # Minimal fake prompt_eval types.
        pe_api = {
            "Experiment": MagicMock(),
            "ExperimentInput": MagicMock(side_effect=lambda **kwargs: kwargs),
            "PromptVariant": MagicMock(side_effect=lambda **kwargs: kwargs),
        }
        rendered = [
            [
                {"role": "system", "content": "System prompt"},
                {"role": "user", "content": f"User prompt for {item.entity_name}"},
            ]
            for item in prepared.items
        ]

        _build_prompt_eval_experiment(
            prepared,
            model="test/model",
            rendered_messages=rendered,
            task="fidelity_experiment",
            max_budget=0.25,
            experiment_name="test_exp",
            pe_api=pe_api,
        )

        # ExperimentInput was called once per item.
        assert pe_api["ExperimentInput"].call_count == len(prepared.items)

        # Verify expected values are the reference types.
        for call_args, item in zip(
            pe_api["ExperimentInput"].call_args_list, prepared.items
        ):
            assert call_args.kwargs["expected"] == item.reference_type

    def test_input_ids_encode_entity_and_level(self) -> None:
        """Input IDs should encode entity name and fidelity level."""
        prepared = _make_prepared_experiment([
            ("CIA", FidelityLevel.TOP_LEVEL, "GovernmentOrganization"),
            ("CIA", FidelityLevel.MID_LEVEL, "GovernmentOrganization"),
        ])
        pe_api = {
            "Experiment": MagicMock(),
            "ExperimentInput": MagicMock(side_effect=lambda **kwargs: kwargs),
            "PromptVariant": MagicMock(side_effect=lambda **kwargs: kwargs),
        }
        rendered = [
            [{"role": "system", "content": "sys"}, {"role": "user", "content": "usr"}]
            for _ in prepared.items
        ]
        _build_prompt_eval_experiment(
            prepared,
            model="test/model",
            rendered_messages=rendered,
            task="fidelity_experiment",
            max_budget=0.25,
            experiment_name="test_exp",
            pe_api=pe_api,
        )
        ids = [call.kwargs["id"] for call in pe_api["ExperimentInput"].call_args_list]
        assert "CIA__top_level" in ids
        assert "CIA__mid_level" in ids

    def test_variant_uses_correct_model_and_task(self) -> None:
        """The PromptVariant should use the specified model and task."""
        prepared = _make_prepared_experiment([
            ("CIA", FidelityLevel.TOP_LEVEL, "GovernmentOrganization"),
        ])
        pe_api = {
            "Experiment": MagicMock(),
            "ExperimentInput": MagicMock(side_effect=lambda **kwargs: kwargs),
            "PromptVariant": MagicMock(side_effect=lambda **kwargs: kwargs),
        }
        rendered = [
            [{"role": "system", "content": "sys"}, {"role": "user", "content": "usr"}]
        ]
        _build_prompt_eval_experiment(
            prepared,
            model="gemini/gemini-2.5-flash-lite",
            rendered_messages=rendered,
            task="fidelity_experiment",
            max_budget=0.25,
            experiment_name="test_exp",
            pe_api=pe_api,
        )
        variant_kwargs = pe_api["PromptVariant"].call_args.kwargs
        assert variant_kwargs["model"] == "gemini/gemini-2.5-flash-lite"
        assert variant_kwargs["kwargs"]["task"] == "fidelity_experiment"
        assert variant_kwargs["kwargs"]["max_budget"] == 0.25
        assert variant_kwargs["temperature"] == 0.0


# ---------------------------------------------------------------------------
# Full run_fidelity_experiment integration test (mocked)
# ---------------------------------------------------------------------------


class TestRunFidelityExperiment:
    """End-to-end test of run_fidelity_experiment with mocked dependencies."""

    def test_full_run_produces_report(self) -> None:
        """A mocked run produces a valid FidelityExperimentReport."""
        prepared = _make_prepared_experiment([
            ("CIA", FidelityLevel.TOP_LEVEL, "GovernmentOrganization"),
            ("Brian", FidelityLevel.TOP_LEVEL, "Human"),
        ])

        # Build fake eval result with trials.
        fake_trials = [
            FakeTrial(
                input_id="CIA__top_level",
                output="GovernmentOrganization",
                cost=0.001,
            ),
            FakeTrial(
                input_id="Brian__top_level",
                output="CognitiveAgent",
                cost=0.001,
            ),
        ]
        fake_result = FakeEvalResult(trials=fake_trials, execution_id="exec_abc123")

        async def fake_run_experiment(experiment: Any, **kwargs: Any) -> Any:
            return fake_result

        # Build a fake ancestor evaluator.
        score_map = {
            ("GovernmentOrganization", "GovernmentOrganization"): FakeAncestorEvalScore(
                score=1.0, exact=1.0, ancestor_match=1.0,
                specificity=1.0, pick="GovernmentOrganization",
                reference="GovernmentOrganization",
            ),
            ("CognitiveAgent", "Human"): FakeAncestorEvalScore(
                score=0.64, exact=0.0, ancestor_match=1.0,
                specificity=0.8, pick="CognitiveAgent",
                reference="Human",
            ),
        }
        fake_ancestor = _make_ancestor_eval(score_map)

        # Mock all external dependencies.
        fake_pe_api = {
            "Experiment": MagicMock(side_effect=lambda **kwargs: MagicMock(**kwargs)),
            "ExperimentInput": MagicMock(side_effect=lambda **kwargs: MagicMock(**kwargs)),
            "PromptVariant": MagicMock(side_effect=lambda **kwargs: MagicMock(**kwargs)),
            "EvalScore": FakeEvalScore,
            "PromptEvalObservabilityConfig": MagicMock(side_effect=lambda **kwargs: MagicMock(**kwargs)),
            "run_experiment": fake_run_experiment,
        }

        def fake_render_prompt(template_path: Any, **context: Any) -> list[dict[str, str]]:
            return [
                {"role": "system", "content": "System prompt for SUMO typing"},
                {"role": "user", "content": f"Entity: {context.get('entity_name', '')}"},
            ]

        with (
            patch(
                "onto_canon6.evaluation.fidelity_runner._load_prompt_eval_api",
                return_value=fake_pe_api,
            ),
            patch(
                "onto_canon6.evaluation.fidelity_runner._load_llm_client_api",
                return_value=(MagicMock(return_value="test/model"), fake_render_prompt),
            ),
            patch(
                "onto_canon6.evaluation.fidelity_runner.make_ancestor_evaluator",
                return_value=fake_ancestor,
            ),
        ):
            import asyncio

            report = asyncio.run(
                __import__(
                    "onto_canon6.evaluation.fidelity_runner", fromlist=["run_fidelity_experiment_async"]
                ).run_fidelity_experiment_async(
                    prepared,
                    model="test/model",
                    sumo_db_path=Path("/fake/sumo.db"),
                    task="fidelity_experiment",
                    max_budget=0.25,
                    observability=False,
                )
            )

        assert isinstance(report, FidelityExperimentReport)
        assert report.model == "test/model"
        assert report.entity_count == 2
        assert len(report.items) == 2
        assert report.ancestor_match_rate == 1.0  # Both are ancestor matches.
        assert report.exact_match_rate == 0.5  # Only CIA is exact.
        assert report.error_count == 0
        assert report.total_cost == pytest.approx(0.002)

    def test_run_with_errored_trial(self) -> None:
        """A run with one errored trial records it correctly in the report."""
        prepared = _make_prepared_experiment([
            ("CIA", FidelityLevel.TOP_LEVEL, "GovernmentOrganization"),
        ])

        fake_trials = [
            FakeTrial(
                input_id="CIA__top_level",
                output=None,
                error="Rate limited",
                cost=0.0,
            ),
        ]
        fake_result = FakeEvalResult(trials=fake_trials, execution_id="exec_err456")

        async def fake_run_experiment(experiment: Any, **kwargs: Any) -> Any:
            return fake_result

        fake_pe_api = {
            "Experiment": MagicMock(side_effect=lambda **kwargs: MagicMock(**kwargs)),
            "ExperimentInput": MagicMock(side_effect=lambda **kwargs: MagicMock(**kwargs)),
            "PromptVariant": MagicMock(side_effect=lambda **kwargs: MagicMock(**kwargs)),
            "EvalScore": FakeEvalScore,
            "PromptEvalObservabilityConfig": MagicMock(side_effect=lambda **kwargs: MagicMock(**kwargs)),
            "run_experiment": fake_run_experiment,
        }

        def fake_render_prompt(template_path: Any, **context: Any) -> list[dict[str, str]]:
            return [
                {"role": "system", "content": "sys"},
                {"role": "user", "content": "usr"},
            ]

        fake_ancestor = _make_ancestor_eval()

        with (
            patch(
                "onto_canon6.evaluation.fidelity_runner._load_prompt_eval_api",
                return_value=fake_pe_api,
            ),
            patch(
                "onto_canon6.evaluation.fidelity_runner._load_llm_client_api",
                return_value=(MagicMock(return_value="test/model"), fake_render_prompt),
            ),
            patch(
                "onto_canon6.evaluation.fidelity_runner.make_ancestor_evaluator",
                return_value=fake_ancestor,
            ),
        ):
            import asyncio
            from onto_canon6.evaluation.fidelity_runner import run_fidelity_experiment_async

            report = asyncio.run(
                run_fidelity_experiment_async(
                    prepared,
                    model="test/model",
                    sumo_db_path=Path("/fake/sumo.db"),
                    observability=False,
                )
            )

        assert report.error_count == 1
        assert report.items[0].error is not None
        assert "Rate limited" in report.items[0].error


# ---------------------------------------------------------------------------
# FidelityComparisonReport construction test
# ---------------------------------------------------------------------------


class TestFidelityComparisonReport:
    """Verify FidelityComparisonReport model construction."""

    def test_comparison_report_structure(self) -> None:
        """A comparison report has the correct structure."""
        report_a = FidelityExperimentReport(
            model="model_a",
            experiment_name="test",
            execution_id="exec_a",
            entity_count=2,
            fidelity_levels=(FidelityLevel.TOP_LEVEL,),
            items=(),
            ancestor_match_rate=0.8,
            exact_match_rate=0.5,
            mean_specificity=0.7,
            wrong_branch_rate=0.2,
            mean_score=0.75,
            total_cost=0.01,
            error_count=0,
        )
        report_b = FidelityExperimentReport(
            model="model_b",
            experiment_name="test",
            execution_id="exec_b",
            entity_count=2,
            fidelity_levels=(FidelityLevel.TOP_LEVEL,),
            items=(),
            ancestor_match_rate=1.0,
            exact_match_rate=0.8,
            mean_specificity=0.9,
            wrong_branch_rate=0.0,
            mean_score=0.95,
            total_cost=0.02,
            error_count=0,
        )
        comparison = FidelityComparisonReport(
            models=("model_a", "model_b"),
            entity_count=2,
            fidelity_levels=(FidelityLevel.TOP_LEVEL,),
            reports=(report_a, report_b),
            comparison_table=(
                {
                    "model": "model_a",
                    "ancestor_match_rate": 0.8,
                    "exact_match_rate": 0.5,
                    "mean_specificity": 0.7,
                    "wrong_branch_rate": 0.2,
                    "mean_score": 0.75,
                    "total_cost": 0.01,
                    "error_count": 0,
                },
                {
                    "model": "model_b",
                    "ancestor_match_rate": 1.0,
                    "exact_match_rate": 0.8,
                    "mean_specificity": 0.9,
                    "wrong_branch_rate": 0.0,
                    "mean_score": 0.95,
                    "total_cost": 0.02,
                    "error_count": 0,
                },
            ),
        )
        assert len(comparison.reports) == 2
        assert len(comparison.comparison_table) == 2
        assert comparison.comparison_table[1]["model"] == "model_b"
        assert comparison.comparison_table[1]["exact_match_rate"] == 0.8


# ---------------------------------------------------------------------------
# Data model validation tests
# ---------------------------------------------------------------------------


class TestFidelityItemResult:
    """Verify FidelityItemResult model constraints."""

    def test_valid_item(self) -> None:
        """A valid item result passes validation."""
        item = FidelityItemResult(
            entity_name="CIA",
            fidelity_level=FidelityLevel.TOP_LEVEL,
            reference_type="GovernmentOrganization",
            pick="GovernmentOrganization",
            ancestor_eval_score=1.0,
            exact_match=True,
            ancestor_match=True,
            specificity=1.0,
            pick_exists=True,
        )
        assert item.entity_name == "CIA"

    def test_accepts_score_above_one_for_more_specific_picks(self) -> None:
        """Ancestor eval score can exceed 1.0 for more-specific descendants."""
        result = FidelityItemResult(
            entity_name="Brian",
            fidelity_level=FidelityLevel.MID_LEVEL,
            reference_type="Human",
            pick="HumanAdult",
            ancestor_eval_score=1.33,
            exact_match=False,
            ancestor_match=True,
            specificity=2.0,
            pick_exists=True,
        )
        assert result.ancestor_eval_score == 1.33

    def test_allows_empty_pick_for_errors(self) -> None:
        """Pick can be empty string when there's an error."""
        item = FidelityItemResult(
            entity_name="CIA",
            fidelity_level=FidelityLevel.TOP_LEVEL,
            reference_type="GovernmentOrganization",
            pick="",
            ancestor_eval_score=0.0,
            exact_match=False,
            ancestor_match=False,
            specificity=0.0,
            pick_exists=False,
            error="timeout",
        )
        assert item.error == "timeout"

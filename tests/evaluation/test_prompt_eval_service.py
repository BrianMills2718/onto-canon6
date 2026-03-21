"""Tests for the prompt_eval-backed extraction prompt experiment slice."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
import sys
from typing import Callable, cast

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))

from onto_canon6.evaluation import ExtractionPromptExperimentError, ExtractionPromptExperimentService  # noqa: E402
from onto_canon6.evaluation import prompt_eval_service as prompt_eval_service_module  # noqa: E402
from onto_canon6.evaluation.models import BenchmarkCase, BenchmarkReferenceCandidate  # noqa: E402
from onto_canon6.config import PromptEvalVariantConfig  # noqa: E402
from onto_canon6.pipeline import (  # noqa: E402
    ExtractedCandidate,
    ExtractedEvidenceSpan,
    ExtractedFiller,
    ProfileRef,
    SourceArtifactRef,
    TextExtractionResponse,
)


def _render_prompt(template_path: str | Path, **context: object) -> list[dict[str, str]]:
    """Load llm_client.render_prompt lazily for deterministic local tests."""

    module = __import__("llm_client", fromlist=["render_prompt"])
    render = cast(Callable[..., list[dict[str, str]]], getattr(module, "render_prompt"))
    return render(template_path, **context)


def _fixture_path() -> Path:
    """Return the shared local benchmark fixture path."""

    return PROJECT_ROOT / "tests" / "fixtures" / "psyop_eval_slice.json"


class _FakeEvalScore:
    """Small stand-in for prompt_eval.EvalScore."""

    def __init__(self, *, score: float, dimension_scores: dict[str, float], reasoning: str) -> None:
        self.score = score
        self.dimension_scores = dimension_scores
        self.reasoning = reasoning


class _FakePromptVariant:
    """Small prompt variant record for service-level wiring tests."""

    def __init__(
        self,
        *,
        name: str,
        messages: list[dict[str, str]],
        prompt_ref: str,
        model: str,
        temperature: float,
        kwargs: dict[str, object],
    ) -> None:
        self.name = name
        self.messages = messages
        self.prompt_ref = prompt_ref
        self.model = model
        self.temperature = temperature
        self.kwargs = kwargs


class _FakeExperimentInput:
    """Small prompt_eval input record for service-level wiring tests."""

    def __init__(self, *, id: str, content: str, expected: object) -> None:
        self.id = id
        self.content = content
        self.expected = expected


class _FakeExperiment:
    """Small prompt_eval experiment record for service-level wiring tests."""

    def __init__(
        self,
        *,
        name: str,
        variants: list[_FakePromptVariant],
        inputs: list[_FakeExperimentInput],
        n_runs: int,
        response_model: type[TextExtractionResponse],
    ) -> None:
        self.name = name
        self.variants = variants
        self.inputs = inputs
        self.n_runs = n_runs
        self.response_model = response_model


class _FakePromptEvalObservabilityConfig:
    """Small prompt_eval observability config stand-in."""

    def __init__(self, **kwargs: object) -> None:
        self.kwargs = kwargs


def test_score_prompt_eval_trial_rewards_exact_usable_output() -> None:
    """The deterministic scorer should give a perfect score to an exact usable match."""

    case = BenchmarkCase(
        case_id="case-1",
        profile=ProfileRef(profile_id="default", profile_version="1.0.0"),
        source_artifact=SourceArtifactRef(
            source_kind="raw_text",
            source_ref="text://case-1",
            source_label="Case 1",
            source_metadata={},
            content_text="Mission planning uses the radar system.",
        ),
        expected_candidates=(
            BenchmarkReferenceCandidate(
                payload={
                    "predicate": "oc:uses_system_demo",
                    "roles": {
                        "subject": [
                            {
                                "kind": "entity",
                                "entity_type": "oc:activity",
                                "name": "Mission planning",
                                "entity_id": "ent:activity:mission_planning",
                                "alias_ids": [],
                            }
                        ],
                        "object": [
                            {
                                "kind": "entity",
                                "entity_type": "oc:system",
                                "name": "radar system",
                                "entity_id": "ent:system:radar_system",
                                "alias_ids": [],
                            }
                        ],
                    },
                }
            ),
        ),
    )
    output = TextExtractionResponse(
        candidates=[
            ExtractedCandidate(
                predicate="oc:uses_system_demo",
                roles={
                    "subject": [
                        ExtractedFiller(
                            kind="entity",
                            entity_type="oc:activity",
                            name="Mission planning",
                            entity_id="ent:activity:mission_planning",
                        )
                    ],
                    "object": [
                        ExtractedFiller(
                            kind="entity",
                            entity_type="oc:system",
                            name="radar system",
                            entity_id="ent:system:radar_system",
                        )
                    ],
                },
                evidence_spans=[
                    ExtractedEvidenceSpan(text="Mission planning"),
                    ExtractedEvidenceSpan(text="radar system"),
                ],
            )
        ]
    )

    score = prompt_eval_service_module._score_prompt_eval_trial(
        output=output,
        expected=case,
        eval_score_cls=_FakeEvalScore,
        overlay_root=PROJECT_ROOT / "var" / "ontology_overlays",
    )

    assert score.score == 1.0
    assert score.dimension_scores["exact_f1"] == 1.0
    assert score.dimension_scores["structural_usable_rate"] == 1.0
    assert score.dimension_scores["count_alignment"] == 1.0


def test_score_prompt_eval_trial_ignores_reviewer_ids_and_value_normalization_shapes() -> None:
    """Prompt-eval exact scoring should focus on extraction-boundary semantics."""

    case = BenchmarkCase(
        case_id="case-psyop-label",
        profile=ProfileRef(profile_id="psyop_seed", profile_version="0.1.0"),
        source_artifact=SourceArtifactRef(
            source_kind="raw_text",
            source_ref="text://case-psyop-label",
            source_label="PSYOP label case",
            source_metadata={},
            content_text="Psychological Operations continued to use the label PSYOP.",
        ),
        expected_candidates=(
            BenchmarkReferenceCandidate(
                payload={
                    "predicate": "oc:uses_designation_label",
                    "roles": {
                        "subject": [
                            {
                                "entity_id": "ent:operation:psychological_operations",
                                "name": "Psychological Operations",
                                "entity_type": "oc:psychological_operation",
                            }
                        ],
                        "label": [
                            {
                                "kind": "value",
                                "value_kind": "string",
                                "raw": "PSYOP",
                                "normalized": {
                                    "value": "PSYOP",
                                },
                            }
                        ],
                    },
                }
            ),
        ),
    )
    output = TextExtractionResponse(
        candidates=[
            ExtractedCandidate(
                predicate="oc:uses_designation_label",
                roles={
                    "subject": [
                        ExtractedFiller(
                            kind="entity",
                            entity_type="oc:psychological_operation",
                            name="Psychological Operations",
                        )
                    ],
                    "label": [
                        ExtractedFiller(
                            kind="value",
                            value_kind="string",
                            raw="PSYOP",
                        )
                    ],
                },
                evidence_spans=[
                    ExtractedEvidenceSpan(text="PSYOP"),
                ],
            )
        ]
    )

    score = prompt_eval_service_module._score_prompt_eval_trial(
        output=output,
        expected=case,
        eval_score_cls=_FakeEvalScore,
        overlay_root=PROJECT_ROOT / "var" / "ontology_overlays",
    )

    assert score.score == 1.0
    assert score.dimension_scores["exact_f1"] == 1.0
    assert score.dimension_scores["structural_usable_rate"] == 1.0
    assert score.dimension_scores["count_alignment"] == 1.0


def test_run_prompt_experiment_builds_report_and_variant_comparison(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The service should build a typed report over one prompt_eval execution family."""

    captured: dict[str, object] = {}

    async def fake_run_experiment(
        experiment: _FakeExperiment,
        evaluator: Callable[[object, object | None], object],
        *,
        observability: _FakePromptEvalObservabilityConfig,
    ) -> object:
        captured["experiment"] = experiment
        captured["observability"] = observability
        first_input = experiment.inputs[0]
        sample_output = TextExtractionResponse(candidates=[])
        captured["trial_score"] = evaluator(sample_output, first_input.expected)
        summary = {
            "baseline": SimpleNamespace(
                n_trials=len(experiment.inputs) * experiment.n_runs,
                n_errors=0,
                mean_score=0.31,
                std_score=0.04,
                dimension_means={
                    "exact_f1": 0.25,
                    "structural_usable_rate": 0.75,
                    "count_alignment": 0.60,
                },
                mean_cost=0.01,
                mean_latency_ms=1200.0,
                total_tokens=900,
            ),
            "hardened": SimpleNamespace(
                n_trials=len(experiment.inputs) * experiment.n_runs,
                n_errors=0,
                mean_score=0.43,
                std_score=0.05,
                dimension_means={
                    "exact_f1": 0.39,
                    "structural_usable_rate": 0.80,
                    "count_alignment": 0.68,
                },
                mean_cost=0.011,
                mean_latency_ms=1180.0,
                total_tokens=940,
            ),
            "compact": SimpleNamespace(
                n_trials=len(experiment.inputs) * experiment.n_runs,
                n_errors=1,
                mean_score=0.28,
                std_score=0.03,
                dimension_means={
                    "exact_f1": 0.20,
                    "structural_usable_rate": 0.90,
                    "count_alignment": 0.62,
                },
                mean_cost=0.009,
                mean_latency_ms=1000.0,
                total_tokens=700,
            ),
            "single_response_hardened": SimpleNamespace(
                n_trials=len(experiment.inputs) * experiment.n_runs,
                n_errors=0,
                mean_score=0.45,
                std_score=0.04,
                dimension_means={
                    "exact_f1": 0.41,
                    "structural_usable_rate": 0.84,
                    "count_alignment": 0.69,
                },
                mean_cost=0.012,
                mean_latency_ms=1210.0,
                total_tokens=960,
            ),
        }
        return SimpleNamespace(
            experiment_name=experiment.name,
            execution_id="exec123",
            variants=["baseline", "compact", "hardened", "single_response_hardened"],
            trials=[],
            summary=summary,
        )

    def fake_load_result_from_observability(
        execution_id: str,
        *,
        project: str | None = None,
        dataset: str | None = None,
        limit: int = 1000,
    ) -> object:
        captured["loaded_execution_id"] = execution_id
        captured["loaded_project"] = project
        captured["loaded_dataset"] = dataset
        captured["loaded_limit"] = limit
        return SimpleNamespace(
            experiment_name="onto_canon6_extraction_prompt_eval",
            execution_id=execution_id,
            variants=["baseline", "compact", "hardened", "single_response_hardened"],
            trials=[],
            summary={
                "baseline": SimpleNamespace(
                    n_trials=4,
                    n_errors=0,
                    mean_score=0.31,
                    std_score=0.04,
                    dimension_means={
                        "exact_f1": 0.25,
                        "structural_usable_rate": 0.75,
                        "count_alignment": 0.60,
                    },
                    mean_cost=0.01,
                    mean_latency_ms=1200.0,
                    total_tokens=900,
                ),
                "hardened": SimpleNamespace(
                    n_trials=4,
                    n_errors=0,
                    mean_score=0.43,
                    std_score=0.05,
                    dimension_means={
                        "exact_f1": 0.39,
                        "structural_usable_rate": 0.80,
                        "count_alignment": 0.68,
                    },
                    mean_cost=0.011,
                    mean_latency_ms=1180.0,
                    total_tokens=940,
                ),
                "compact": SimpleNamespace(
                    n_trials=4,
                    n_errors=1,
                    mean_score=0.28,
                    std_score=0.03,
                    dimension_means={
                        "exact_f1": 0.20,
                        "structural_usable_rate": 0.90,
                        "count_alignment": 0.62,
                    },
                    mean_cost=0.009,
                    mean_latency_ms=1000.0,
                    total_tokens=700,
                ),
                "single_response_hardened": SimpleNamespace(
                    n_trials=4,
                    n_errors=0,
                    mean_score=0.45,
                    std_score=0.04,
                    dimension_means={
                        "exact_f1": 0.41,
                        "structural_usable_rate": 0.84,
                        "count_alignment": 0.69,
                    },
                    mean_cost=0.012,
                    mean_latency_ms=1210.0,
                    total_tokens=960,
                ),
            },
        )

    def fake_compare_variants(
        result: object,
        variant_a: str,
        variant_b: str,
        *,
        confidence: float = 0.95,
        method: str = "bootstrap",
        dimension: str | None = None,
    ) -> object:
        del result, confidence, dimension
        return SimpleNamespace(
            variant_a=variant_a,
            variant_b=variant_b,
            mean_a=0.43,
            mean_b=0.31,
            difference=0.12,
            ci_lower=0.01,
            ci_upper=0.23,
            significant=True,
            method=method,
            detail="welch comparison",
        )

    monkeypatch.setattr(
        prompt_eval_service_module,
        "_load_llm_client_api",
        lambda: prompt_eval_service_module._LLMClientAPI(
            get_model=lambda task, use_performance=True: f"model-for-{task}",
            render_prompt=_render_prompt,
        ),
    )
    monkeypatch.setattr(
        prompt_eval_service_module,
        "_load_prompt_eval_api",
        lambda: prompt_eval_service_module._PromptEvalAPI(
            Experiment=_FakeExperiment,
            ExperimentInput=_FakeExperimentInput,
            PromptVariant=_FakePromptVariant,
            EvalScore=_FakeEvalScore,
            PromptEvalObservabilityConfig=_FakePromptEvalObservabilityConfig,
            run_experiment=fake_run_experiment,
            load_result_from_observability=fake_load_result_from_observability,
            compare_variants=fake_compare_variants,
        ),
    )

    report = ExtractionPromptExperimentService().run_prompt_experiment()

    assert report.execution_id == "exec123"
    assert report.baseline_variant_name == "baseline"
    assert report.selection_task == "fast_extraction"
    assert report.selected_model == "model-for-fast_extraction"
    assert [item.variant_name for item in report.variant_summaries] == [
        "baseline",
        "compact",
        "hardened",
        "single_response_hardened",
    ]
    assert report.comparisons[0].variant_a == "hardened"
    assert report.comparisons[0].variant_b == "baseline"
    assert report.variant_summaries[0].successful_trials == 4
    assert report.variant_summaries[0].failure_counts == {}
    experiment = captured["experiment"]
    assert isinstance(experiment, _FakeExperiment)
    assert experiment.n_runs == 2
    assert experiment.response_model is TextExtractionResponse
    assert [variant.name for variant in experiment.variants] == [
        "baseline",
        "hardened",
        "compact",
        "single_response_hardened",
    ]
    assert experiment.variants[0].kwargs["task"] == "fast_extraction"
    assert experiment.variants[0].kwargs["max_budget"] == 0.25
    assert experiment.variants[1].kwargs["task"] == "fast_extraction"
    assert experiment.variants[1].kwargs["max_budget"] == 0.25
    assert experiment.variants[2].kwargs["task"] == "fast_extraction"
    assert experiment.variants[2].kwargs["max_budget"] == 0.25
    assert experiment.variants[3].kwargs["task"] == "fast_extraction"
    assert experiment.variants[3].kwargs["max_budget"] == 0.25
    baseline_messages = experiment.variants[0].messages
    hardened_messages = experiment.variants[1].messages
    compact_messages = experiment.variants[2].messages
    single_response_messages = experiment.variants[3].messages
    assert "Case input:\n{input}" in baseline_messages[-1]["content"]
    assert "Return at most 2 candidates." in baseline_messages[0]["content"]
    assert "Use at most 1 evidence spans per" in baseline_messages[0]["content"]
    assert "Use exact source surface forms for entity names and values." in baseline_messages[0]["content"]
    assert "Build candidates role-first." in baseline_messages[0]["content"]
    assert "Every filler object must include `kind`" in baseline_messages[0]["content"]
    assert "abbreviation expansions" in hardened_messages[0]["content"]
    assert "parenthetical name expansions" in hardened_messages[0]["content"]
    assert "Every filler object must include `kind`" in hardened_messages[0]["content"]
    assert "Prefer the smallest sufficient candidate set" in compact_messages[0]["content"]
    assert "Return at most 1 candidates." in compact_messages[0]["content"]
    assert "Use at most 1 evidence spans per" in compact_messages[0]["content"]
    assert "Empty candidates are allowed." in compact_messages[0]["content"]
    assert "Build candidates role-first." in compact_messages[0]["content"]
    assert "parenthetical name expansions" in compact_messages[0]["content"]
    assert "return no opinion candidate" in compact_messages[0]["content"]
    assert "Every filler object must include `kind`" in compact_messages[0]["content"]
    assert "Return exactly one structured response object" in single_response_messages[0]["content"]
    assert "Return at most 1 candidates." in single_response_messages[0]["content"]
    assert "Use at most 1 evidence spans per" in single_response_messages[0]["content"]
    assert "Never emit `roles: {}`." in single_response_messages[0]["content"]
    assert "Use exact source surface forms for entity names and values." in single_response_messages[0]["content"]
    assert "parenthetical name expansions" in single_response_messages[0]["content"]
    assert "return no opinion candidate" in single_response_messages[0]["content"]
    assert "Every filler object must include `kind`" in single_response_messages[0]["content"]
    observability = captured["observability"]
    assert isinstance(observability, _FakePromptEvalObservabilityConfig)
    assert observability.kwargs["dataset"] == "onto_canon6_extraction_prompt_eval"
    assert observability.kwargs["project"] == "onto-canon6"
    provenance = observability.kwargs["provenance"]
    assert isinstance(provenance, dict)
    assert provenance["selection_task"] == "fast_extraction"
    assert captured["loaded_execution_id"] == "exec123"
    assert captured["loaded_dataset"] == "onto_canon6_extraction_prompt_eval"
    trial_score = captured["trial_score"]
    assert isinstance(trial_score, _FakeEvalScore)


def test_run_prompt_experiment_fails_loud_on_mixed_profile_fixture(tmp_path: Path) -> None:
    """Mixed-profile fixtures should fail before any prompt_eval work starts."""

    fixture = json.loads(_fixture_path().read_text(encoding="utf-8"))
    fixture["cases"][1]["profile"]["profile_id"] = "default"
    mixed_fixture_path = tmp_path / "mixed_fixture.json"
    mixed_fixture_path.write_text(json.dumps(fixture), encoding="utf-8")

    service = ExtractionPromptExperimentService()

    with pytest.raises(
        ExtractionPromptExperimentError,
        match="single shared profile",
    ):
        service.run_prompt_experiment(fixture_path=mixed_fixture_path)


def test_run_prompt_experiment_fails_loud_on_undersized_welch_shape() -> None:
    """Welch comparison should fail before any live prompt work if the shape is too small."""

    service = ExtractionPromptExperimentService()

    with pytest.raises(
        ExtractionPromptExperimentError,
        match="welch comparison requires at least two scored trials per variant",
    ):
        service.run_prompt_experiment(case_limit=1, n_runs=1)


def test_run_prompt_experiment_fails_loud_on_undersized_bootstrap_shape() -> None:
    """Bootstrap comparison should fail before any live prompt work if the shape is too small."""

    service = ExtractionPromptExperimentService()

    with pytest.raises(
        ExtractionPromptExperimentError,
        match="bootstrap comparison requires at least two scored trials per variant",
    ):
        service.run_prompt_experiment(case_limit=1, n_runs=1, comparison_method="bootstrap")


def test_run_prompt_experiment_allows_bootstrap_override_with_minimal_valid_shape(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A call-site bootstrap override should work once the comparison shape is valid."""

    prepared_result = SimpleNamespace(
        experiment_name="onto_canon6_extraction_prompt_eval",
        execution_id="exec123",
        variants=["baseline", "compact", "hardened", "single_response_hardened"],
        trials=[],
        summary={
            "baseline": SimpleNamespace(
                n_trials=2,
                n_errors=0,
                mean_score=0.35,
                std_score=0.02,
                dimension_means={},
                mean_cost=0.01,
                mean_latency_ms=1200.0,
                total_tokens=900,
            ),
            "hardened": SimpleNamespace(
                n_trials=2,
                n_errors=0,
                mean_score=0.43,
                std_score=0.05,
                dimension_means={"exact_f1": 0.39},
                mean_cost=0.011,
                mean_latency_ms=1180.0,
                total_tokens=940,
            ),
            "compact": SimpleNamespace(
                n_trials=2,
                n_errors=0,
                mean_score=0.28,
                std_score=0.03,
                dimension_means={"exact_f1": 0.20},
                mean_cost=0.009,
                mean_latency_ms=1000.0,
                total_tokens=700,
            ),
            "single_response_hardened": SimpleNamespace(
                n_trials=2,
                n_errors=0,
                mean_score=0.45,
                std_score=0.04,
                dimension_means={"exact_f1": 0.41},
                mean_cost=0.012,
                mean_latency_ms=1210.0,
                total_tokens=960,
            ),
        },
    )
    comparison_methods: list[str] = []

    async def fake_run_experiment(
        experiment: _FakeExperiment,
        evaluator: Callable[[object, object | None], object],
        *,
        observability: _FakePromptEvalObservabilityConfig,
    ) -> object:
        del experiment, evaluator, observability
        return prepared_result

    def fake_load_result_from_observability(
        execution_id: str,
        *,
        project: str | None = None,
        dataset: str | None = None,
        limit: int = 1000,
    ) -> object:
        del execution_id, project, dataset, limit
        return prepared_result

    def fake_compare_variants(
        result: object,
        variant_a: str,
        variant_b: str,
        *,
        confidence: float = 0.95,
        method: str = "bootstrap",
        dimension: str | None = None,
    ) -> object:
        del result, confidence, dimension
        comparison_methods.append(method)
        return SimpleNamespace(
            variant_a=variant_a,
            variant_b=variant_b,
            mean_a=0.5,
            mean_b=0.4,
            difference=0.1,
            ci_lower=-0.1,
            ci_upper=0.3,
            significant=False,
            method=method,
            detail="bootstrap comparison",
        )

    monkeypatch.setattr(
        prompt_eval_service_module,
        "_load_llm_client_api",
        lambda: prompt_eval_service_module._LLMClientAPI(
            get_model=lambda task, use_performance=True: f"model-for-{task}",
            render_prompt=_render_prompt,
        ),
    )
    monkeypatch.setattr(
        prompt_eval_service_module,
        "_load_prompt_eval_api",
        lambda: prompt_eval_service_module._PromptEvalAPI(
            Experiment=_FakeExperiment,
            ExperimentInput=_FakeExperimentInput,
            PromptVariant=_FakePromptVariant,
            EvalScore=_FakeEvalScore,
            PromptEvalObservabilityConfig=_FakePromptEvalObservabilityConfig,
            run_experiment=fake_run_experiment,
            load_result_from_observability=fake_load_result_from_observability,
            compare_variants=fake_compare_variants,
        ),
    )

    report = ExtractionPromptExperimentService().run_prompt_experiment(
        case_limit=1,
        n_runs=2,
        comparison_method="bootstrap",
    )

    assert report.comparisons
    assert all(comparison.method == "bootstrap" for comparison in report.comparisons)
    assert comparison_methods == ["bootstrap", "bootstrap", "bootstrap"]


def test_run_prompt_experiment_allows_selection_task_override(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A call-site selection-task override should flow into model choice and provenance."""

    captured: dict[str, object] = {}
    prepared_result = SimpleNamespace(
        experiment_name="onto_canon6_extraction_prompt_eval",
        execution_id="exec123",
        variants=["baseline", "compact", "hardened", "single_response_hardened"],
        trials=[],
        summary={
            "baseline": SimpleNamespace(
                n_trials=2,
                n_errors=0,
                mean_score=0.31,
                std_score=0.04,
                dimension_means={},
                mean_cost=0.01,
                mean_latency_ms=1200.0,
                total_tokens=900,
            ),
            "hardened": SimpleNamespace(
                n_trials=2,
                n_errors=0,
                mean_score=0.43,
                std_score=0.05,
                dimension_means={},
                mean_cost=0.011,
                mean_latency_ms=1180.0,
                total_tokens=940,
            ),
            "compact": SimpleNamespace(
                n_trials=2,
                n_errors=0,
                mean_score=0.28,
                std_score=0.03,
                dimension_means={},
                mean_cost=0.009,
                mean_latency_ms=1000.0,
                total_tokens=700,
            ),
            "single_response_hardened": SimpleNamespace(
                n_trials=2,
                n_errors=0,
                mean_score=0.45,
                std_score=0.04,
                dimension_means={},
                mean_cost=0.012,
                mean_latency_ms=1210.0,
                total_tokens=960,
            ),
        },
    )

    async def fake_run_experiment(
        experiment: _FakeExperiment,
        evaluator: Callable[[object, object | None], object],
        *,
        observability: _FakePromptEvalObservabilityConfig,
    ) -> object:
        del evaluator
        captured["experiment"] = experiment
        captured["observability"] = observability
        return prepared_result

    def fake_load_result_from_observability(
        execution_id: str,
        *,
        project: str | None = None,
        dataset: str | None = None,
        limit: int = 1000,
    ) -> object:
        del execution_id, project, dataset, limit
        return prepared_result

    def fake_compare_variants(
        result: object,
        variant_a: str,
        variant_b: str,
        *,
        confidence: float = 0.95,
        method: str = "bootstrap",
        dimension: str | None = None,
    ) -> object:
        del result, confidence, dimension
        return SimpleNamespace(
            variant_a=variant_a,
            variant_b=variant_b,
            mean_a=0.5,
            mean_b=0.4,
            difference=0.1,
            ci_lower=-0.1,
            ci_upper=0.3,
            significant=False,
            method=method,
            detail="bootstrap comparison",
        )

    monkeypatch.setattr(
        prompt_eval_service_module,
        "_load_llm_client_api",
        lambda: prompt_eval_service_module._LLMClientAPI(
            get_model=lambda task, use_performance=True: f"model-for-{task}",
            render_prompt=_render_prompt,
        ),
    )
    monkeypatch.setattr(
        prompt_eval_service_module,
        "_load_prompt_eval_api",
        lambda: prompt_eval_service_module._PromptEvalAPI(
            Experiment=_FakeExperiment,
            ExperimentInput=_FakeExperimentInput,
            PromptVariant=_FakePromptVariant,
            EvalScore=_FakeEvalScore,
            PromptEvalObservabilityConfig=_FakePromptEvalObservabilityConfig,
            run_experiment=fake_run_experiment,
            load_result_from_observability=fake_load_result_from_observability,
            compare_variants=fake_compare_variants,
        ),
    )

    report = ExtractionPromptExperimentService().run_prompt_experiment(
        case_limit=1,
        n_runs=2,
        comparison_method="bootstrap",
        selection_task="extraction",
    )

    assert report.selection_task == "extraction"
    assert report.selected_model == "model-for-extraction"
    experiment = captured["experiment"]
    assert isinstance(experiment, _FakeExperiment)
    assert all(variant.kwargs["task"] == "extraction" for variant in experiment.variants)
    observability = captured["observability"]
    assert isinstance(observability, _FakePromptEvalObservabilityConfig)
    provenance = observability.kwargs["provenance"]
    assert isinstance(provenance, dict)
    assert provenance["selection_task"] == "extraction"


def test_run_prompt_experiment_allows_routing_policy_override(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A call-site routing-policy override should flow into prompt_eval call kwargs."""

    captured: dict[str, object] = {}
    fake_config = object()
    prepared_result = SimpleNamespace(
        experiment_name="onto_canon6_extraction_prompt_eval",
        execution_id="exec123",
        variants=["baseline", "compact", "hardened", "single_response_hardened"],
        trials=[],
        summary={
            "baseline": SimpleNamespace(
                n_trials=2,
                n_errors=0,
                mean_score=0.31,
                std_score=0.04,
                dimension_means={},
                mean_cost=0.01,
                mean_latency_ms=1200.0,
                total_tokens=900,
            ),
            "hardened": SimpleNamespace(
                n_trials=2,
                n_errors=0,
                mean_score=0.43,
                std_score=0.05,
                dimension_means={},
                mean_cost=0.011,
                mean_latency_ms=1180.0,
                total_tokens=940,
            ),
            "compact": SimpleNamespace(
                n_trials=2,
                n_errors=0,
                mean_score=0.28,
                std_score=0.03,
                dimension_means={},
                mean_cost=0.009,
                mean_latency_ms=1000.0,
                total_tokens=700,
            ),
            "single_response_hardened": SimpleNamespace(
                n_trials=2,
                n_errors=0,
                mean_score=0.45,
                std_score=0.04,
                dimension_means={},
                mean_cost=0.012,
                mean_latency_ms=1210.0,
                total_tokens=960,
            ),
        },
    )

    async def fake_run_experiment(
        experiment: _FakeExperiment,
        evaluator: Callable[[object, object | None], object],
        *,
        observability: _FakePromptEvalObservabilityConfig,
    ) -> object:
        del evaluator
        captured["experiment"] = experiment
        captured["observability"] = observability
        return prepared_result

    def fake_load_result_from_observability(
        execution_id: str,
        *,
        project: str | None = None,
        dataset: str | None = None,
        limit: int = 1000,
    ) -> object:
        del execution_id, project, dataset, limit
        return prepared_result

    def fake_compare_variants(
        result: object,
        variant_a: str,
        variant_b: str,
        *,
        confidence: float = 0.95,
        method: str = "bootstrap",
        dimension: str | None = None,
    ) -> object:
        del result, confidence, dimension
        return SimpleNamespace(
            variant_a=variant_a,
            variant_b=variant_b,
            mean_a=0.5,
            mean_b=0.4,
            difference=0.1,
            ci_lower=-0.1,
            ci_upper=0.3,
            significant=False,
            method=method,
            detail="bootstrap comparison",
        )

    monkeypatch.setattr(
        prompt_eval_service_module,
        "_load_llm_client_api",
        lambda: prompt_eval_service_module._LLMClientAPI(
            get_model=lambda task, use_performance=True: f"model-for-{task}",
            render_prompt=_render_prompt,
        ),
    )
    monkeypatch.setattr(
        prompt_eval_service_module,
        "_build_llm_client_config_for_routing_policy",
        lambda routing_policy: fake_config if routing_policy == "direct" else None,
    )
    monkeypatch.setattr(
        prompt_eval_service_module,
        "_load_prompt_eval_api",
        lambda: prompt_eval_service_module._PromptEvalAPI(
            Experiment=_FakeExperiment,
            ExperimentInput=_FakeExperimentInput,
            PromptVariant=_FakePromptVariant,
            EvalScore=_FakeEvalScore,
            PromptEvalObservabilityConfig=_FakePromptEvalObservabilityConfig,
            run_experiment=fake_run_experiment,
            load_result_from_observability=fake_load_result_from_observability,
            compare_variants=fake_compare_variants,
        ),
    )

    report = ExtractionPromptExperimentService().run_prompt_experiment(
        case_limit=1,
        n_runs=2,
        comparison_method="bootstrap",
        routing_policy="direct",
    )

    assert report.selection_task == "fast_extraction"
    experiment = captured["experiment"]
    assert isinstance(experiment, _FakeExperiment)
    assert all(variant.kwargs["config"] is fake_config for variant in experiment.variants)
    observability = captured["observability"]
    assert isinstance(observability, _FakePromptEvalObservabilityConfig)
    provenance = observability.kwargs["provenance"]
    assert isinstance(provenance, dict)
    assert provenance["routing_policy_override"] == "direct"


def test_run_prompt_experiment_fails_loud_when_live_errors_break_welch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Live trial errors should become an experiment-specific Welch failure."""

    async def fake_run_experiment(
        experiment: _FakeExperiment,
        evaluator: Callable[[object, object | None], object],
        *,
        observability: _FakePromptEvalObservabilityConfig,
    ) -> object:
        del evaluator, observability
        return SimpleNamespace(
            experiment_name=experiment.name,
            execution_id="exec123",
            variants=["baseline", "compact", "hardened", "single_response_hardened"],
            trials=[],
            summary={},
        )

    def fake_load_result_from_observability(
        execution_id: str,
        *,
        project: str | None = None,
        dataset: str | None = None,
        limit: int = 1000,
    ) -> object:
        del execution_id, project, dataset, limit
        return SimpleNamespace(
            experiment_name="onto_canon6_extraction_prompt_eval",
            execution_id="exec123",
            variants=["baseline", "compact", "hardened", "single_response_hardened"],
            trials=[],
            summary={
                "baseline": SimpleNamespace(
                    n_trials=2,
                    n_errors=1,
                    mean_score=0.31,
                    std_score=0.04,
                    dimension_means={},
                    mean_cost=0.01,
                    mean_latency_ms=1200.0,
                    total_tokens=900,
                ),
                "hardened": SimpleNamespace(
                    n_trials=2,
                    n_errors=0,
                    mean_score=0.43,
                    std_score=0.05,
                    dimension_means={},
                    mean_cost=0.011,
                    mean_latency_ms=1180.0,
                    total_tokens=940,
                ),
                "compact": SimpleNamespace(
                    n_trials=2,
                    n_errors=0,
                    mean_score=0.28,
                    std_score=0.03,
                    dimension_means={},
                    mean_cost=0.009,
                    mean_latency_ms=1000.0,
                    total_tokens=700,
                ),
                "single_response_hardened": SimpleNamespace(
                    n_trials=2,
                    n_errors=0,
                    mean_score=0.45,
                    std_score=0.04,
                    dimension_means={},
                    mean_cost=0.012,
                    mean_latency_ms=1210.0,
                    total_tokens=960,
                ),
            },
        )

    monkeypatch.setattr(
        prompt_eval_service_module,
        "_load_llm_client_api",
        lambda: prompt_eval_service_module._LLMClientAPI(
            get_model=lambda task, use_performance=True: f"model-for-{task}",
            render_prompt=_render_prompt,
        ),
    )
    monkeypatch.setattr(
        prompt_eval_service_module,
        "_load_prompt_eval_api",
        lambda: prompt_eval_service_module._PromptEvalAPI(
            Experiment=_FakeExperiment,
            ExperimentInput=_FakeExperimentInput,
            PromptVariant=_FakePromptVariant,
            EvalScore=_FakeEvalScore,
            PromptEvalObservabilityConfig=_FakePromptEvalObservabilityConfig,
            run_experiment=fake_run_experiment,
            load_result_from_observability=fake_load_result_from_observability,
            compare_variants=lambda *args, **kwargs: None,
        ),
    )

    with pytest.raises(
        ExtractionPromptExperimentError,
        match="welch comparison became impossible after live trial errors",
    ):
        ExtractionPromptExperimentService().run_prompt_experiment(case_limit=2, n_runs=1)


def test_run_prompt_experiment_fails_loud_when_live_errors_break_bootstrap(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Live trial errors should become an experiment-specific bootstrap failure."""

    async def fake_run_experiment(
        experiment: _FakeExperiment,
        evaluator: Callable[[object, object | None], object],
        *,
        observability: _FakePromptEvalObservabilityConfig,
    ) -> object:
        del evaluator, observability
        return SimpleNamespace(
            experiment_name=experiment.name,
            execution_id="exec123",
            variants=["baseline", "compact", "hardened", "single_response_hardened"],
            trials=[],
            summary={},
        )

    def fake_load_result_from_observability(
        execution_id: str,
        *,
        project: str | None = None,
        dataset: str | None = None,
        limit: int = 1000,
    ) -> object:
        del execution_id, project, dataset, limit
        return SimpleNamespace(
            experiment_name="onto_canon6_extraction_prompt_eval",
            execution_id="exec123",
            variants=["baseline", "compact", "hardened", "single_response_hardened"],
            trials=[],
            summary={
                "baseline": SimpleNamespace(
                    n_trials=2,
                    n_errors=1,
                    mean_score=0.31,
                    std_score=0.04,
                    dimension_means={},
                    mean_cost=0.01,
                    mean_latency_ms=1200.0,
                    total_tokens=900,
                ),
                "hardened": SimpleNamespace(
                    n_trials=2,
                    n_errors=0,
                    mean_score=0.43,
                    std_score=0.05,
                    dimension_means={},
                    mean_cost=0.011,
                    mean_latency_ms=1180.0,
                    total_tokens=940,
                ),
                "compact": SimpleNamespace(
                    n_trials=2,
                    n_errors=0,
                    mean_score=0.28,
                    std_score=0.03,
                    dimension_means={},
                    mean_cost=0.009,
                    mean_latency_ms=1000.0,
                    total_tokens=700,
                ),
                "single_response_hardened": SimpleNamespace(
                    n_trials=2,
                    n_errors=0,
                    mean_score=0.45,
                    std_score=0.04,
                    dimension_means={},
                    mean_cost=0.012,
                    mean_latency_ms=1210.0,
                    total_tokens=960,
                ),
            },
        )

    monkeypatch.setattr(
        prompt_eval_service_module,
        "_load_llm_client_api",
        lambda: prompt_eval_service_module._LLMClientAPI(
            get_model=lambda task, use_performance=True: f"model-for-{task}",
            render_prompt=_render_prompt,
        ),
    )
    monkeypatch.setattr(
        prompt_eval_service_module,
        "_load_prompt_eval_api",
        lambda: prompt_eval_service_module._PromptEvalAPI(
            Experiment=_FakeExperiment,
            ExperimentInput=_FakeExperimentInput,
            PromptVariant=_FakePromptVariant,
            EvalScore=_FakeEvalScore,
            PromptEvalObservabilityConfig=_FakePromptEvalObservabilityConfig,
            run_experiment=fake_run_experiment,
            load_result_from_observability=fake_load_result_from_observability,
            compare_variants=lambda *args, **kwargs: None,
        ),
    )

    with pytest.raises(
        ExtractionPromptExperimentError,
        match="bootstrap comparison became impossible after live trial errors",
    ):
        ExtractionPromptExperimentService().run_prompt_experiment(
            case_limit=1,
            n_runs=2,
            comparison_method="bootstrap",
        )


def test_classify_prompt_eval_trial_failure_categories() -> None:
    """Known live trial failures should map to stable taxonomy labels."""

    classify = prompt_eval_service_module._classify_prompt_eval_trial_failure

    assert (
        classify(SimpleNamespace(error="The output is incomplete due to a max_tokens length limit."))
        == "length_truncated"
    )
    assert (
        classify(SimpleNamespace(error="Instructor does not support multiple tool calls"))
        == "multiple_tool_calls"
    )
    assert (
        classify(SimpleNamespace(error='APIError: {"message":"Key limit exceeded (total limit)"}'))
        == "provider_rate_limited"
    )
    assert (
        classify(
            SimpleNamespace(
                error='APIError: {"message":"This request requires more credits, or fewer max_tokens.","code":402}'
            )
        )
        == "insufficient_credits"
    )
    assert (
        classify(
            SimpleNamespace(
                error='OpenAIException - {"error":{"message":"Invalid schema for response_format","code":"invalid_json_schema"}}'
            )
        )
        == "provider_schema_rejected"
    )
    assert (
        classify(
            SimpleNamespace(
                error="LLMCapabilityError: acall_llm_structured: provider rejected structured-output call arguments for model openrouter/x-ai/grok-4.1-fast"
            )
        )
        == "provider_invalid_arguments"
    )
    assert (
        classify(
            SimpleNamespace(
                error="litellm.Timeout: Connection timed out. Timeout passed=60.0, time taken=62.095 seconds"
            )
        )
        == "provider_timeout"
    )
    assert (
        classify(
            SimpleNamespace(
                error=(
                    "LLMCapabilityError: call_llm_structured: provider rejected structured "
                    "JSON-schema output for GPT-5-family model gpt-5-mini"
                )
            )
        )
        == "provider_schema_rejected"
    )
    assert (
        classify(SimpleNamespace(reasoning="deterministic prompt_eval scoring failed: entity fillers require entity_id or name"))
        == "unnamed_entity_filler"
    )
    assert (
        classify(SimpleNamespace(error="candidate roles must not be empty"))
        == "empty_roles"
    )
    assert (
        classify(SimpleNamespace(reasoning="deterministic prompt_eval scoring failed: evidence span 0 text did not resolve to a unique exact match in source"))
        == "bad_evidence_span"
    )


def test_summarize_trial_failures_by_variant() -> None:
    """The report builder should aggregate classified failures per variant."""

    summarize = prompt_eval_service_module._summarize_trial_failures_by_variant
    failures = summarize(
        trials=(
            SimpleNamespace(variant_name="baseline", error="The output is incomplete due to a max_tokens length limit.", reasoning=None),
            SimpleNamespace(variant_name="baseline", error='APIError: {"message":"Key limit exceeded (total limit)"}', reasoning=None),
            SimpleNamespace(variant_name="baseline", error="litellm.Timeout: Connection timed out. Timeout passed=60.0, time taken=62.095 seconds", reasoning=None),
            SimpleNamespace(variant_name="baseline", error='APIError: {"message":"This request requires more credits, or fewer max_tokens.","code":402}', reasoning=None),
            SimpleNamespace(variant_name="baseline", error='OpenAIException - {"error":{"message":"Invalid schema for response_format","code":"invalid_json_schema"}}', reasoning=None),
            SimpleNamespace(variant_name="baseline", error="LLMCapabilityError: acall_llm_structured: provider rejected structured-output call arguments for model openrouter/x-ai/grok-4.1-fast", reasoning=None),
            SimpleNamespace(variant_name="hardened", error=None, reasoning="deterministic prompt_eval scoring failed: entity fillers require entity_id or name"),
        ),
        variant_names=("baseline", "hardened"),
    )

    assert failures == {
        "baseline": {
            "length_truncated": 1,
            "provider_rate_limited": 1,
            "provider_timeout": 1,
            "insufficient_credits": 1,
            "provider_schema_rejected": 1,
            "provider_invalid_arguments": 1,
        },
        "hardened": {
            "unnamed_entity_filler": 1,
        },
    }


def test_validate_loaded_result_has_scored_trials_for_comparison_raises_clear_error() -> None:
    """Zero-success variants should fail before compare_variants with failure context."""

    validate = prompt_eval_service_module._validate_loaded_result_has_scored_trials_for_comparison
    result = SimpleNamespace(
        summary={
            "baseline": SimpleNamespace(n_trials=1, n_errors=1),
            "hardened": SimpleNamespace(n_trials=1, n_errors=1),
        },
        trials=[
            SimpleNamespace(
                variant_name="baseline",
                error=(
                    "LLMCapabilityError: call_llm_structured: provider rejected structured "
                    "JSON-schema output for GPT-5-family model gpt-5-mini"
                ),
                reasoning=None,
            ),
            SimpleNamespace(
                variant_name="hardened",
                error='APIError: {"message":"This request requires more credits, or fewer max_tokens.","code":402}',
                reasoning=None,
            ),
        ],
    )

    with pytest.raises(
        ExtractionPromptExperimentError,
        match="zero successful scored trials",
    ) as exc_info:
        validate(
            result=result,
            baseline_variant_name="baseline",
            variant_names=("baseline", "hardened"),
        )

    message = str(exc_info.value)
    assert "provider_schema_rejected=1" in message
    assert "insufficient_credits=1" in message


def test_variant_render_context_applies_per_variant_budget_overrides() -> None:
    """Variant prompt budgets should override the shared experiment defaults only locally."""

    variant = PromptEvalVariantConfig(
        name="compact",
        prompt_template="prompts/extraction/prompt_eval_text_to_candidate_assertions_compact.yaml",
        prompt_ref="onto_canon6.extraction.prompt_eval_text_to_candidate_assertions_compact@1",
        max_candidates_per_case=1,
        max_evidence_spans_per_candidate=1,
    )

    context = prompt_eval_service_module._variant_render_context(
        shared_context={
            "profile_id": "psyop_seed",
            "profile_version": "0.1.0",
            "predicate_catalog": "- oc:example",
            "entity_type_catalog": "- oc:entity",
        },
        default_max_candidates_per_case=4,
        default_max_evidence_spans_per_candidate=2,
        variant=variant,
    )

    assert context["profile_id"] == "psyop_seed"
    assert context["max_candidates_per_case"] == 1
    assert context["max_evidence_spans_per_candidate"] == 1

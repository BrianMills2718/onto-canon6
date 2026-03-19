"""Integration tests for the prompt-eval CLI entrypoint."""

from __future__ import annotations

import json

import pytest

from onto_canon6 import cli as cli_module
from onto_canon6.evaluation import (
    ExtractionPromptExperimentReport,
    PromptVariantComparisonRecord,
    PromptVariantSummaryRecord,
)


class _FakeExtractionPromptExperimentService:
    """Deterministic stand-in for the prompt_eval extraction experiment service."""

    def run_prompt_experiment(
        self,
        *,
        fixture_path: object | None = None,
        case_limit: int | None = None,
        n_runs: int | None = None,
    ) -> ExtractionPromptExperimentReport:
        """Return one stable report without invoking live prompt_eval work."""

        del fixture_path, case_limit, n_runs
        return ExtractionPromptExperimentReport(
            experiment_name="onto_canon6_extraction_prompt_eval",
            fixture_id="psyop_eval_slice_v1",
            fixture_path="tests/fixtures/psyop_eval_slice.json",
            execution_id="exec123",
            observability_dataset="onto_canon6_extraction_prompt_eval",
            observability_phase="evaluation",
            case_count=2,
            n_runs=2,
            baseline_variant_name="baseline",
            variant_summaries=(
                PromptVariantSummaryRecord(
                    variant_name="baseline",
                    prompt_template="prompts/extraction/prompt_eval_text_to_candidate_assertions_baseline.yaml",
                    prompt_ref="onto_canon6.extraction.prompt_eval_text_to_candidate_assertions_baseline@1",
                    n_trials=4,
                    n_errors=0,
                    mean_score=0.31,
                    std_score=0.04,
                    dimension_means={"exact_f1": 0.25},
                    mean_cost=0.01,
                    mean_latency_ms=1000.0,
                    total_tokens=900,
                ),
                PromptVariantSummaryRecord(
                    variant_name="hardened",
                    prompt_template="prompts/extraction/prompt_eval_text_to_candidate_assertions_hardened.yaml",
                    prompt_ref="onto_canon6.extraction.prompt_eval_text_to_candidate_assertions_hardened@1",
                    n_trials=4,
                    n_errors=0,
                    mean_score=0.43,
                    std_score=0.05,
                    dimension_means={"exact_f1": 0.39},
                    mean_cost=0.011,
                    mean_latency_ms=980.0,
                    total_tokens=940,
                ),
            ),
            comparisons=(
                PromptVariantComparisonRecord(
                    variant_a="hardened",
                    variant_b="baseline",
                    mean_a=0.43,
                    mean_b=0.31,
                    difference=0.12,
                    ci_lower=0.01,
                    ci_upper=0.23,
                    significant=True,
                    method="welch",
                    detail="welch comparison",
                ),
            ),
        )


def test_cli_runs_extraction_prompt_experiment_and_emits_json(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The CLI should expose the prompt-eval extraction experiment surface."""

    # mock-ok: the CLI wiring is the target here; prompt_eval execution itself
    # is covered at the service boundary.
    monkeypatch.setattr(
        cli_module,
        "ExtractionPromptExperimentService",
        _FakeExtractionPromptExperimentService,
    )

    exit_code = cli_module.main(
        [
            "run-extraction-prompt-experiment",
            "--output",
            "json",
        ]
    )

    assert exit_code == 0
    output = json.loads(capsys.readouterr().out)
    assert output["execution_id"] == "exec123"
    assert output["baseline_variant_name"] == "baseline"
    assert output["variant_summaries"][1]["variant_name"] == "hardened"

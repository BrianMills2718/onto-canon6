"""Tests for the Phase 5 live extraction-evaluation slice."""

from __future__ import annotations

from importlib import import_module
from pathlib import Path
from types import SimpleNamespace
import sys
from typing import Callable, cast

import pytest
from pydantic import JsonValue

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))

from onto_canon6.evaluation import EvaluationError, LiveExtractionEvaluationService, load_benchmark_fixture  # noqa: E402
from onto_canon6.evaluation import service as evaluation_service_module  # noqa: E402
from onto_canon6.pipeline import (  # noqa: E402
    CandidateAssertionImport,
    EvidenceSpan,
    ProfileRef,
    SourceArtifactRef,
    TextExtractionRun,
)


def _render_prompt(template_path: str | Path, **context: object) -> list[dict[str, str]]:
    """Load llm_client.render_prompt lazily for deterministic local tests."""

    module = import_module("llm_client")
    render = cast(Callable[..., list[dict[str, str]]], getattr(module, "render_prompt"))
    return render(template_path, **context)


def _fixture_path() -> Path:
    """Return the local benchmark fixture path used by the evaluation tests."""

    return PROJECT_ROOT / "tests" / "fixtures" / "psyop_eval_slice.json"


def _candidate_import(
    *,
    profile: ProfileRef,
    source_artifact: SourceArtifactRef,
    payload: dict[str, JsonValue],
    claim_text: str,
    spans: tuple[EvidenceSpan, ...],
) -> CandidateAssertionImport:
    """Build one typed candidate import for fake extractor results."""

    return CandidateAssertionImport(
        profile=profile,
        payload=dict(payload),
        submitted_by="agent:test-eval",
        source_artifact=source_artifact,
        evidence_spans=spans,
        claim_text=claim_text,
    )


class _FakeExtractor:
    """Return deterministic candidate imports for benchmark evaluation tests."""

    def __init__(self, *, fixture_case_index: int = 0) -> None:
        self.selection_task = "extraction"
        self.prompt_template = PROJECT_ROOT / "prompts" / "extraction" / "text_to_candidate_assertions.yaml"
        self._fixture_case_index = fixture_case_index

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
        source_metadata: dict[str, object] | None = None,
    ) -> TextExtractionRun:
        """Return one exact and one noncanonical-but-valid candidate."""

        del submitted_by
        fixture = load_benchmark_fixture(_fixture_path())
        case = fixture.cases[self._fixture_case_index]
        assert source_text == case.source_artifact.content_text
        assert profile_id == case.profile.profile_id
        assert profile_version == case.profile.profile_version
        assert source_ref == case.source_artifact.source_ref
        assert source_kind == case.source_artifact.source_kind
        assert source_label == case.source_artifact.source_label
        assert source_metadata == dict(case.source_artifact.source_metadata)

        profile = case.profile
        source_artifact = case.source_artifact
        exact_payload = case.expected_candidates[0].payload
        noncanonical_payload = cast(
            dict[str, JsonValue],
            {
            "predicate": "oc:hold_command_role",
            "roles": {
                "commander": [
                    {
                        "entity_id": "ent:person:admiral_eric_olson",
                        "name": "Admiral Eric Olson",
                        "entity_type": "oc:person",
                    }
                ],
                "organization": [
                    {
                        "entity_id": "ent:org:united_states_special_operations_command",
                        "name": "United States Special Operations Command",
                        "entity_type": "oc:military_organization",
                    }
                ],
                "role_title": [
                    {
                        "kind": "value",
                        "value_kind": "string",
                        "raw": "commander",
                        "normalized": {
                            "value": "commander",
                        },
                    }
                ],
            },
            },
        )
        candidate_imports = (
            _candidate_import(
                profile=profile,
                source_artifact=source_artifact,
                payload=exact_payload,
                claim_text="Eric Olson replaced the designation in 2011.",
                spans=(
                    EvidenceSpan(start_char=3, end_char=7, text="2011"),
                    EvidenceSpan(start_char=30, end_char=48, text="Admiral Eric Olson"),
                ),
            ),
            _candidate_import(
                profile=profile,
                source_artifact=source_artifact,
                payload=noncanonical_payload,
                claim_text="Eric Olson was commander of USSOCOM.",
                spans=(
                    EvidenceSpan(start_char=30, end_char=48, text="Admiral Eric Olson"),
                    EvidenceSpan(
                        start_char=67,
                        end_char=106,
                        text="United States Special Operations Command",
                    ),
                ),
            ),
        )
        return TextExtractionRun(
            selection_task=self.selection_task,
            prompt_template=str(self.prompt_template),
            prompt_ref="onto_canon6.extraction.text_to_candidate_assertions@1",
            selected_model="fake-extraction-model",
            resolved_model="fake-extraction-model",
            trace_id="onto_canon6.extract.fake",
            candidate_imports=candidate_imports,
        )


def test_load_benchmark_fixture_reads_local_cases() -> None:
    """The local Phase 5 fixture should load into typed benchmark models."""

    fixture = load_benchmark_fixture(_fixture_path())

    assert fixture.fixture_id == "psyop_eval_slice_v4"
    assert len(fixture.cases) == 10
    assert fixture.cases[0].profile.profile_id == "psyop_seed"
    assert fixture.cases[0].source_artifact.content_text is not None
    assert len(fixture.cases[0].expected_candidates) == 4


def test_load_benchmark_fixture_covers_targeted_semantic_failure_modes() -> None:
    """The benchmark fixture should explicitly cover the planned semantic failure modes."""

    fixture = load_benchmark_fixture(_fixture_path())
    cases_by_id = {case.case_id: case for case in fixture.cases}

    alias_case = cases_by_id["psyop_003_alias_expansion_parenthetical_only"]
    subordinate_case = cases_by_id["psyop_004_subordinate_unit_belongs_to_organization"]
    unattributed_case = cases_by_id["psyop_005_unattributed_opinion_strict_omit"]
    context_only_case = cases_by_id["psyop_006_context_only_membership_strict_omit"]
    named_concern_case = cases_by_id["psyop_007_named_institutional_concern"]
    jpotf_case = cases_by_id["psyop_008_jpotf_establishment_not_org_form"]
    narrator_case = cases_by_id["psyop_009_report_narration_without_named_speaker_strict_omit"]
    loose_capability_case = cases_by_id["psyop_010_limit_capability_without_named_subject_strict_omit"]

    assert alias_case.expected_candidates == ()
    assert len(subordinate_case.expected_candidates) == 1
    assert subordinate_case.expected_candidates[0].payload["predicate"] == "oc:belongs_to_organization"
    assert unattributed_case.expected_candidates == ()
    assert context_only_case.expected_candidates == ()
    assert len(named_concern_case.expected_candidates) == 1
    assert named_concern_case.expected_candidates[0].payload["predicate"] == "oc:express_concern"
    assert jpotf_case.expected_candidates == ()
    assert narrator_case.expected_candidates == ()
    assert loose_capability_case.expected_candidates == ()


def test_run_live_benchmark_separates_reasonableness_and_exact_fidelity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Support labels and exact preferred-form matches should remain separate."""

    extractor = _FakeExtractor()
    service = LiveExtractionEvaluationService(extractor=extractor)

    def fake_get_model(task: str) -> str:
        assert task == "judging"
        return "fake-judge-model"

    # mock-ok: isolates the llm_client network boundary while exercising the
    # real prompt asset and local evaluation contracts.
    def fake_call_llm_structured(
        model: str,
        messages: list[dict[str, str]],
        response_model: type[evaluation_service_module._JudgeResponse],
        **kwargs: object,
    ) -> tuple[evaluation_service_module._JudgeResponse, object]:
        assert model == "fake-judge-model"
        assert kwargs["task"] == "judging"
        assert kwargs["prompt_ref"] == "onto_canon6.evaluation.judge_candidate_reasonableness@1"
        assert "Candidate assertions JSON" in messages[-1]["content"]
        parsed = response_model(
            candidate_reviews=(
                evaluation_service_module._JudgeCandidateReview(
                    candidate_index=0,
                    support_label="supported",
                    reasoning="The designation change is directly stated in the source text.",
                ),
                evaluation_service_module._JudgeCandidateReview(
                    candidate_index=1,
                    support_label="supported",
                    reasoning="The command role is directly stated even though the IDs differ from the preferred reference.",
                ),
            ),
            important_missing_facts=("The source also names PSYOP and MISO as designation labels.",),
            overall_notes="The extraction is mostly reasonable but incomplete relative to the reference set.",
        )
        return parsed, SimpleNamespace(resolved_model="fake-judge-model")

    monkeypatch.setattr(
        evaluation_service_module,
        "_load_judge_llm_client_api",
        lambda: evaluation_service_module._JudgeLLMClientAPI(
            get_model=fake_get_model,
            render_prompt=_render_prompt,
            call_llm_structured=fake_call_llm_structured,
        ),
    )

    report = service.run_live_benchmark(fixture_path=_fixture_path(), case_limit=1)

    assert report.summary.case_count == 1
    assert report.summary.reasonableness.total_candidates == 2
    assert report.summary.reasonableness.supported_count == 2
    assert report.summary.reasonableness.acceptable_rate == 1.0
    assert report.summary.validation.valid_count == 2
    assert report.summary.canonicalization.expected == 4
    assert report.summary.canonicalization.observed == 2
    assert report.summary.canonicalization.matched == 1
    assert report.summary.canonicalization.precision == 0.5
    assert report.summary.canonicalization.recall == 0.25
    assert report.cases[0].candidate_evaluations[0].exact_preferred_match is True
    assert report.cases[0].candidate_evaluations[1].exact_preferred_match is False
    assert report.cases[0].extraction_run.prompt_ref == "onto_canon6.extraction.text_to_candidate_assertions@1"
    assert report.cases[0].judge_run.prompt_ref == "onto_canon6.evaluation.judge_candidate_reasonableness@1"
    assert report.cases[0].important_missing_facts == (
        "The source also names PSYOP and MISO as designation labels.",
    )


def test_run_live_benchmark_fails_loud_when_judge_omits_candidate_review(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Judge output must cover every extracted candidate exactly once."""

    extractor = _FakeExtractor()
    service = LiveExtractionEvaluationService(extractor=extractor)

    def fake_get_model(task: str) -> str:
        assert task == "judging"
        return "fake-judge-model"

    # mock-ok: isolates the llm_client network boundary so the failure test can
    # focus on local evaluation contract enforcement.
    def fake_call_llm_structured(
        model: str,
        messages: list[dict[str, str]],
        response_model: type[evaluation_service_module._JudgeResponse],
        **kwargs: object,
    ) -> tuple[evaluation_service_module._JudgeResponse, object]:
        del model, messages, kwargs
        parsed = response_model(
            candidate_reviews=(
                evaluation_service_module._JudgeCandidateReview(
                    candidate_index=0,
                    support_label="supported",
                    reasoning="Only one candidate was reviewed.",
                ),
            ),
        )
        return parsed, SimpleNamespace(resolved_model="fake-judge-model")

    monkeypatch.setattr(
        evaluation_service_module,
        "_load_judge_llm_client_api",
        lambda: evaluation_service_module._JudgeLLMClientAPI(
            get_model=fake_get_model,
            render_prompt=_render_prompt,
            call_llm_structured=fake_call_llm_structured,
        ),
    )

    with pytest.raises(
        EvaluationError,
        match="judge must return exactly one candidate review for each extracted candidate",
    ):
        service.run_live_benchmark(fixture_path=_fixture_path(), case_limit=1)


def test_run_live_benchmark_emits_shared_experiment_records(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The benchmark should log case runs and one family aggregate."""

    extractor = _FakeExtractor()
    service = LiveExtractionEvaluationService(extractor=extractor)
    run_calls: dict[str, object] = {}
    item_calls: list[dict[str, object]] = []
    aggregate_calls: list[dict[str, object]] = []

    def fake_get_model(task: str) -> str:
        assert task == "judging"
        return "fake-judge-model"

    # mock-ok: isolates both the llm_client network boundary and the shared
    # observability backend while preserving the local benchmark logic.
    def fake_call_llm_structured(
        model: str,
        messages: list[dict[str, str]],
        response_model: type[evaluation_service_module._JudgeResponse],
        **kwargs: object,
    ) -> tuple[evaluation_service_module._JudgeResponse, object]:
        del model, messages
        assert kwargs["prompt_ref"] == "onto_canon6.evaluation.judge_candidate_reasonableness@1"
        parsed = response_model(
            candidate_reviews=(
                evaluation_service_module._JudgeCandidateReview(
                    candidate_index=0,
                    support_label="supported",
                    reasoning="supported",
                ),
                evaluation_service_module._JudgeCandidateReview(
                    candidate_index=1,
                    support_label="partially_supported",
                    reasoning="partial",
                ),
            ),
        )
        return parsed, SimpleNamespace(resolved_model="fake-judge-model")

    def fake_start_run(**kwargs: object) -> str:
        run_calls.update(kwargs)
        return "run-case-1"

    def fake_finish_run(*, run_id: str, **kwargs: object) -> dict[str, object]:
        assert run_id == "run-case-1"
        return {"run_id": run_id, **kwargs}

    def fake_log_item(**kwargs: object) -> None:
        item_calls.append(dict(kwargs))

    def fake_log_experiment_aggregate(**kwargs: object) -> str:
        aggregate_calls.append(dict(kwargs))
        return "agg-1"

    monkeypatch.setattr(
        evaluation_service_module,
        "_load_judge_llm_client_api",
        lambda: evaluation_service_module._JudgeLLMClientAPI(
            get_model=fake_get_model,
            render_prompt=_render_prompt,
            call_llm_structured=fake_call_llm_structured,
        ),
    )
    monkeypatch.setattr(
        evaluation_service_module,
        "_load_observability_api",
        lambda: evaluation_service_module._ObservabilityAPI(
            start_run=fake_start_run,
            finish_run=fake_finish_run,
            log_item=fake_log_item,
            log_experiment_aggregate=fake_log_experiment_aggregate,
        ),
    )

    report = service.run_live_benchmark(fixture_path=_fixture_path(), case_limit=1)

    assert report.experiment_execution_id is not None
    assert report.cases[0].observability_run_id == "run-case-1"
    assert run_calls["dataset"] == "onto_canon6_live_extraction_benchmark"
    assert run_calls["task"] == "benchmark.live_extraction"
    assert run_calls["condition_id"] == report.cases[0].case_id
    assert run_calls["scenario_id"] == report.fixture_id
    assert len(item_calls) == 2
    assert item_calls[0]["trace_id"] == "onto_canon6.extract.fake"
    assert item_calls[0]["metrics"] == {
        "supported": 1.0,
        "partially_supported": 0.0,
        "unsupported": 0.0,
        "acceptable": 1.0,
        "valid": 1.0,
        "needs_review": 0.0,
        "invalid": 0.0,
        "exact_preferred_match": 1.0,
    }
    assert len(aggregate_calls) == 1
    assert aggregate_calls[0]["family_id"] == report.experiment_execution_id
    aggregate_metrics = aggregate_calls[0]["metrics"]
    assert isinstance(aggregate_metrics, dict)
    assert aggregate_metrics["exact_f1"] == report.summary.canonicalization.f1

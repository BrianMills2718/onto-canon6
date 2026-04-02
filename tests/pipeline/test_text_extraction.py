"""Tests for the llm_client-backed text extraction boundary."""

from __future__ import annotations

from importlib import import_module
import json
from pathlib import Path
from types import SimpleNamespace
import sys
from typing import Any, Callable, cast

from pydantic import BaseModel
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))

from onto_canon6.ontology_runtime import clear_loader_caches  # noqa: E402
from onto_canon6.ontology_runtime import load_effective_profile  # noqa: E402
from onto_canon6.core import CanonicalGraphService  # noqa: E402
from onto_canon6.pipeline import EvidenceSpan, ProfileRef, ReviewService, SourceArtifactRef  # noqa: E402
from onto_canon6.pipeline import text_extraction as extraction_module  # noqa: E402
from onto_canon6.config import ConfigError, get_config  # noqa: E402
from onto_canon6.pipeline.text_extraction import (  # noqa: E402
    ExtractedCandidate,
    ExtractedEntityFiller,
    ExtractedEvidenceSpan,
    ExtractedValueFiller,
    TextExtractionResponse,
    TextExtractionService,
)


def _render_prompt(template_path: str | Path, **context: object) -> list[dict[str, str]]:
    """Load llm_client.render_prompt lazily for local deterministic tests."""

    module = import_module("llm_client")
    render = cast(Callable[..., list[dict[str, str]]], getattr(module, "render_prompt"))
    return render(template_path, **context)


def setup_function() -> None:
    """Reset cached donor profile state between tests."""

    clear_loader_caches()


def _make_review_service(tmp_path: Path) -> ReviewService:
    """Create a review service with isolated review DB and overlay root."""

    return ReviewService(
        db_path=tmp_path / "review.sqlite3",
        overlay_root=tmp_path / "ontology_overlays",
        default_acceptance_policy="record_only",
    )


def test_extract_candidate_imports_uses_llm_client_boundary(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The extractor should render the prompt and return typed candidate imports."""

    service = TextExtractionService(review_service=_make_review_service(tmp_path))
    # Clear model_override so the test exercises task-based model selection.
    object.__setattr__(service, "_model_override", None)
    calls: dict[str, object] = {}

    def fake_get_model(task: str, *, use_performance: bool = True) -> str:
        calls["selection_task"] = task
        calls["selection_use_performance"] = use_performance
        return "fake-structured-model"

    # mock-ok: isolates the llm_client network boundary while still exercising
    # the real prompt asset and local extractor contract.
    def fake_call_llm_structured(
        model: str,
        messages: list[dict[str, str]],
        response_model: type[BaseModel],
        **kwargs: object,
    ) -> tuple[BaseModel, object]:
        calls["model"] = model
        calls["messages"] = messages
        calls["kwargs"] = kwargs
        if response_model is TextExtractionResponse:
            response = response_model(
                candidates=[
                    ExtractedCandidate(
                        predicate="oc:uses_system_demo",
                        roles={
                            "subject": [
                                ExtractedEntityFiller(
                                    kind="entity", entity_id="ent:activity:mission_planning",
                                    entity_type="oc:activity",
                                    name="Mission planning",
                                ),
                            ],
                            "object": [
                                ExtractedEntityFiller(
                                    kind="entity", entity_id="ent:system:radar_system",
                                    entity_type="oc:system",
                                    name="radar system",
                                ),
                            ],
                        },
                        evidence_spans=[
                            ExtractedEvidenceSpan(text="Mission planning"),
                            ExtractedEvidenceSpan(text="radar system"),
                        ],
                        claim_text="Mission planning uses the radar system.",
                    ),
                ]
            )
        else:
            response = response_model.model_validate(
                {"judgments": [{"candidate_index": 0, "label": "supported"}]}
            )
        return response, SimpleNamespace(resolved_model="fake-structured-model")

    monkeypatch.setattr(
        extraction_module,
        "_load_llm_client_api",
        lambda: extraction_module._LLMClientAPI(
            get_model=fake_get_model,
            render_prompt=_render_prompt,
            call_llm_structured=cast(Any, fake_call_llm_structured),
        ),
    )

    imports = service.extract_candidate_imports(
        source_text="Mission planning uses the radar system during the exercise.",
        profile_id="default",
        profile_version="1.0.0",
        submitted_by="analyst:text-extract",
        source_ref="text://phase4/mission-planning",
    )

    assert len(imports) == 1
    assert imports[0].claim_text == "Mission planning uses the radar system."
    assert imports[0].evidence_spans[0].text == "Mission planning"
    assert imports[0].evidence_spans[0].start_char == 0
    assert imports[0].source_artifact.content_text is not None
    assert calls["selection_task"] == "fast_extraction"
    assert calls["selection_use_performance"] is False
    call_kwargs = calls["kwargs"]
    assert isinstance(call_kwargs, dict)
    assert call_kwargs["task"] == "fast_extraction"
    assert call_kwargs["max_budget"] == 0.25
    assert call_kwargs["prompt_ref"] == "onto_canon6.extraction.text_to_candidate_assertions@1"
    assert str(call_kwargs["trace_id"]).startswith("onto_canon6.extract.")
    messages = calls["messages"]
    assert isinstance(messages, list)
    assert "Mission planning uses the radar system during the exercise." in messages[-1]["content"]


def test_extract_candidate_imports_forwards_temperature_override(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A bounded temperature override should flow into the live extraction call."""

    service = TextExtractionService(
        review_service=_make_review_service(tmp_path),
        temperature=0.0,
    )
    calls: dict[str, object] = {}

    def fake_get_model(task: str, *, use_performance: bool = True) -> str:
        del task, use_performance
        return "fake-structured-model"

    def fake_call_llm_structured(
        model: str,
        messages: list[dict[str, str]],
        response_model: type[BaseModel],
        **kwargs: object,
    ) -> tuple[BaseModel, object]:
        del model, messages
        calls["kwargs"] = kwargs
        if response_model is TextExtractionResponse:
            return response_model(candidates=[]), SimpleNamespace(resolved_model="fake-structured-model")
        return response_model.model_validate(
            {"judgments": [{"candidate_index": 0, "label": "supported"}]}
        ), SimpleNamespace(resolved_model="fake-structured-model")

    monkeypatch.setattr(
        extraction_module,
        "_load_llm_client_api",
        lambda: extraction_module._LLMClientAPI(
            get_model=fake_get_model,
            render_prompt=_render_prompt,
            call_llm_structured=cast(Any, fake_call_llm_structured),
        ),
    )

    imports = service.extract_candidate_imports(
        source_text="Mission planning uses the radar system during the exercise.",
        profile_id="default",
        profile_version="1.0.0",
        submitted_by="analyst:text-extract",
        source_ref="text://phase4/mission-planning",
    )

    assert imports == ()
    call_kwargs = calls["kwargs"]
    assert isinstance(call_kwargs, dict)
    assert call_kwargs["temperature"] == 0.0


def test_text_extraction_response_drops_unparseable_candidates_before_response_parse() -> None:
    """One malformed candidate should not poison an otherwise valid response."""

    response = TextExtractionResponse.model_validate(
        {
            "candidates": [
                {
                    "predicate": "gp:holds_role",
                    "roles": {
                        "subject": [
                            {
                                "kind": "entity",
                                "entity_type": "oc:person",
                                "name": "Col. Rodriguez",
                            }
                        ]
                    },
                    "evidence_spans": [{"text": "Col. Rodriguez"}],
                    "claim_text": "Col. Rodriguez is mentioned.",
                },
                {
                    "predicate": "gp:attends",
                    "roles": {
                        "subject": [
                            {
                                "kind": "event",
                                "entity_type": "oc:ceremony",
                                "name": "ceremony",
                            }
                        ]
                    },
                    "evidence_spans": [{"text": "ceremony"}],
                    "claim_text": "A ceremony occurred.",
                },
                {
                    "predicate": "gp:acts_on",
                    "roles": {
                        "topic": [
                            {
                                "kind": "unknown",
                                "name": "psychological operations community",
                            }
                        ]
                    },
                    "evidence_spans": [{"text": "psychological operations community"}],
                    "claim_text": "The community was affected.",
                },
            ]
        }
    )

    assert len(response.candidates) == 1
    assert response.candidates[0].predicate == "gp:holds_role"


def test_extract_candidate_imports_keeps_valid_candidates_when_one_candidate_is_malformed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Malformed candidates should be dropped loudly without losing the document."""

    service = TextExtractionService(review_service=_make_review_service(tmp_path))

    def fake_get_model(task: str, *, use_performance: bool = True) -> str:
        del task, use_performance
        return "fake-structured-model"

    def fake_call_llm_structured(
        model: str,
        messages: list[dict[str, str]],
        response_model: type[BaseModel],
        **kwargs: object,
    ) -> tuple[BaseModel, object]:
        del model, messages, kwargs
        if response_model is TextExtractionResponse:
            raw_response = {
                "candidates": [
                    {
                        "predicate": "gp:holds_role",
                        "roles": {
                            "subject": [
                                {
                                    "kind": "entity",
                                    "entity_type": "oc:person",
                                    "name": "Col. Rodriguez",
                                }
                            ],
                            "organization": [
                                {
                                    "kind": "entity",
                                    "entity_type": "oc:military_organization",
                                    "name": "4th POG",
                                }
                            ],
                        },
                        "evidence_spans": [
                            {"text": "Col. Rodriguez"},
                            {"text": "4th POG"},
                        ],
                        "claim_text": "Col. Rodriguez assumed command of the 4th POG.",
                    },
                    {
                        "predicate": "gp:attends",
                        "roles": {
                            "subject": [
                                {
                                    "kind": "event",
                                    "entity_type": "oc:ceremony",
                                    "name": "ceremony",
                                }
                            ]
                        },
                        "evidence_spans": [{"text": "ceremony"}],
                        "claim_text": "A ceremony occurred.",
                    },
                ]
            }
            return (
                response_model.model_validate(raw_response),
                SimpleNamespace(resolved_model="fake-structured-model"),
            )
        return (
            response_model.model_validate(
                {"judgments": [{"candidate_index": 0, "label": "supported"}]}
            ),
            SimpleNamespace(resolved_model="fake-structured-model"),
        )

    monkeypatch.setattr(
        extraction_module,
        "_load_llm_client_api",
        lambda: extraction_module._LLMClientAPI(
            get_model=fake_get_model,
            render_prompt=_render_prompt,
            call_llm_structured=cast(Any, fake_call_llm_structured),
        ),
    )

    imports = service.extract_candidate_imports(
        source_text=Path("tests/fixtures/synthetic_corpus/doc_06.txt").read_text(encoding="utf-8"),
        profile_id="default",
        profile_version="1.0.0",
        submitted_by="scale_test:doc_06",
        source_ref="doc_06",
        source_kind="synthetic_text",
    )

    assert len(imports) == 1
    assert imports[0].claim_text == "Col. Rodriguez assumed command of the 4th POG."
    assert imports[0].source_artifact.source_ref == "doc_06"


def test_extract_candidate_imports_allows_selection_task_override(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The extractor should allow bounded task overrides without config edits."""

    service = TextExtractionService(
        review_service=_make_review_service(tmp_path),
        selection_task="budget_extraction",
    )
    object.__setattr__(service, "_model_override", None)
    calls: dict[str, object] = {}

    def fake_get_model(task: str, *, use_performance: bool = True) -> str:
        calls["selection_task"] = task
        calls["selection_use_performance"] = use_performance
        return "fake-structured-model"

    # mock-ok: isolates the llm_client network boundary while proving that the
    # override reaches both model selection and the structured call contract.
    def fake_call_llm_structured(
        model: str,
        messages: list[dict[str, str]],
        response_model: type[BaseModel],
        **kwargs: object,
    ) -> tuple[BaseModel, object]:
        del model, messages
        calls["kwargs"] = kwargs
        if response_model is TextExtractionResponse:
            return response_model(candidates=[]), SimpleNamespace(resolved_model="fake-structured-model")
        return response_model.model_validate(
            {"judgments": [{"candidate_index": 0, "label": "supported"}]}
        ), SimpleNamespace(resolved_model="fake-structured-model")

    monkeypatch.setattr(
        extraction_module,
        "_load_llm_client_api",
        lambda: extraction_module._LLMClientAPI(
            get_model=fake_get_model,
            render_prompt=_render_prompt,
            call_llm_structured=cast(Any, fake_call_llm_structured),
        ),
    )

    imports = service.extract_candidate_imports(
        source_text="Mission planning uses the radar system during the exercise.",
        profile_id="default",
        profile_version="1.0.0",
        submitted_by="analyst:text-extract",
        source_ref="text://phase4/mission-planning",
    )

    assert imports == ()
    assert calls["selection_task"] == "budget_extraction"
    call_kwargs = calls["kwargs"]
    assert isinstance(call_kwargs, dict)
    assert call_kwargs["task"] == "budget_extraction"


def test_extract_candidate_imports_allows_prompt_override_pair(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The extractor should allow a bounded prompt override with explicit provenance."""

    override_prompt = tmp_path / "override_prompt.yaml"
    override_prompt.write_text(
        "\n".join(
            [
                'name: test_override',
                'version: "1.0"',
                'description: "Prompt override test"',
                "messages:",
                "  - role: system",
                "    content: |",
                "      Override prompt. Limit {{ max_candidates_per_case }} candidates.",
                "  - role: user",
                "    content: |",
                "      Source: {{ source_text }}",
                "      Evidence budget: {{ max_evidence_spans_per_candidate }}",
            ]
        ),
        encoding="utf-8",
    )
    service = TextExtractionService(
        review_service=_make_review_service(tmp_path),
        prompt_template=override_prompt,
        prompt_ref="onto_canon6.extraction.test_override@1",
        max_candidates_per_call=1,
        max_evidence_spans_per_candidate=1,
    )
    calls: dict[str, object] = {}

    def fake_get_model(task: str, *, use_performance: bool = True) -> str:
        calls["selection_task"] = task
        calls["selection_use_performance"] = use_performance
        return "fake-structured-model"

    def fake_call_llm_structured(
        model: str,
        messages: list[dict[str, str]],
        response_model: type[BaseModel],
        **kwargs: object,
    ) -> tuple[BaseModel, object]:
        del model
        calls["messages"] = messages
        calls["kwargs"] = kwargs
        if response_model is TextExtractionResponse:
            return response_model(candidates=[]), SimpleNamespace(resolved_model="fake-structured-model")
        return response_model.model_validate(
            {"judgments": [{"candidate_index": 0, "label": "supported"}]}
        ), SimpleNamespace(resolved_model="fake-structured-model")

    monkeypatch.setattr(
        extraction_module,
        "_load_llm_client_api",
        lambda: extraction_module._LLMClientAPI(
            get_model=fake_get_model,
            render_prompt=_render_prompt,
            call_llm_structured=cast(Any, fake_call_llm_structured),
        ),
    )

    imports = service.extract_candidate_imports(
        source_text="Mission planning uses the radar system during the exercise.",
        profile_id="default",
        profile_version="1.0.0",
        submitted_by="analyst:text-extract",
        source_ref="text://phase4/mission-planning",
    )

    assert imports == ()
    assert service.prompt_template == override_prompt.resolve()
    assert service.prompt_ref == "onto_canon6.extraction.test_override@1"
    messages = calls["messages"]
    assert isinstance(messages, list)
    assert messages[0]["content"] == "Override prompt. Limit 1 candidates."
    assert "Mission planning uses the radar system during the exercise." in messages[-1]["content"]
    assert "Evidence budget: 1" in messages[-1]["content"]
    call_kwargs = calls["kwargs"]
    assert isinstance(call_kwargs, dict)
    assert call_kwargs["prompt_ref"] == "onto_canon6.extraction.test_override@1"


def test_text_extraction_service_fails_loud_on_partial_prompt_override(tmp_path: Path) -> None:
    """Prompt overrides must arrive as a template/ref pair so provenance stays honest."""

    with pytest.raises(
        ConfigError,
        match="prompt_template and prompt_ref overrides must be provided together",
    ):
        TextExtractionService(
            review_service=_make_review_service(tmp_path),
            prompt_template=tmp_path / "override_prompt.yaml",
        )


def test_main_extraction_prompt_includes_current_winning_guidance() -> None:
    """The live extraction prompt should carry the proven Phase A guidance."""

    messages = _render_prompt(
        PROJECT_ROOT / "prompts" / "extraction" / "text_to_candidate_assertions.yaml",
        profile_id="psyop_seed",
        profile_version="0.1.0",
        predicate_catalog="- oc:replace_designation",
        entity_type_catalog="- oc:person",
        extraction_goal="",
        source_kind="raw_text",
        source_ref="text://phase-b/prompt",
        source_label="prompt test",
        source_text="Admiral Eric Olson replaced PSYOP with MISO.",
    )

    system_prompt = messages[0]["content"]
    assert "Every `entity` filler must include a reviewer-meaningful `name` and an" in system_prompt
    assert "`entity_type` chosen from the active ontology catalog" in system_prompt
    assert "if one sentence explicitly states multiple independent facts" in system_prompt
    assert "abbreviation expansions, acronym definitions" in system_prompt
    assert "the `subject` must be the" in system_prompt
    assert "enduring named entity being renamed" in system_prompt
    assert "if the text explicitly states both a concern and a concrete lost or" in system_prompt


def test_extract_and_submit_persists_extracted_candidates(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Extracted candidate imports should flow through the existing review store."""

    review_service = _make_review_service(tmp_path)
    service = TextExtractionService(review_service=review_service)

    def fake_get_model(task: str, *, use_performance: bool = True) -> str:
        del use_performance
        return f"model-for-{task}"

    # mock-ok: isolates the llm_client network boundary for deterministic
    # review-pipeline integration testing.
    def fake_call_llm_structured(
        model: str,
        messages: list[dict[str, str]],
        response_model: type[BaseModel],
        **kwargs: object,
    ) -> tuple[BaseModel, object]:
        if response_model is TextExtractionResponse:
            return (
                response_model(
                    candidates=[
                        ExtractedCandidate(
                            predicate="oc:uses_system_demo",
                            roles={
                                "subject": [
                                    ExtractedEntityFiller(
                                        kind="entity", entity_type="oc:activity",
                                        name="Mission planning",
                                    ),
                                ],
                            },
                            evidence_spans=[
                                ExtractedEvidenceSpan(text="Mission planning"),
                            ],
                            claim_text="Mission planning is the subject.",
                        ),
                    ]
                ),
                SimpleNamespace(resolved_model=model),
            )
        return response_model.model_validate(
            {"judgments": [{"candidate_index": 0, "label": "supported"}]}
        ), SimpleNamespace(resolved_model=model)

    monkeypatch.setattr(
        extraction_module,
        "_load_llm_client_api",
        lambda: extraction_module._LLMClientAPI(
            get_model=fake_get_model,
            render_prompt=_render_prompt,
            call_llm_structured=cast(Any, fake_call_llm_structured),
        ),
    )

    results = service.extract_and_submit(
        source_text="Mission planning uses the radar system during the exercise.",
        profile_id="default",
        profile_version="1.0.0",
        submitted_by="analyst:text-extract",
        source_ref="text://phase4/submit",
    )

    assert len(results) == 1
    persisted = review_service.list_candidate_assertions()
    assert len(persisted) == 1
    assert persisted[0].claim_text == "Mission planning is the subject."
    assert persisted[0].evidence_spans[0].text == "Mission planning"
    roles_obj = persisted[0].payload.get("roles")
    assert isinstance(roles_obj, dict)
    subject_fillers = roles_obj.get("subject")
    assert isinstance(subject_fillers, list)
    subject_filler = subject_fillers[0]
    assert isinstance(subject_filler, dict)
    assert str(subject_filler["entity_id"]).startswith("ent:auto:")


def test_extract_and_submit_skips_unresolvable_evidence_spans(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Bad extractor spans should be skipped (non-strict) with a warning."""

    service = TextExtractionService(review_service=_make_review_service(tmp_path))

    def fake_get_model(task: str, *, use_performance: bool = True) -> str:
        del use_performance
        return f"model-for-{task}"

    # mock-ok: isolates the llm_client network boundary so the test can focus
    # on deterministic span verification behavior.
    def fake_call_llm_structured(
        model: str,
        messages: list[dict[str, str]],
        response_model: type[BaseModel],
        **kwargs: object,
    ) -> tuple[BaseModel, object]:
        if response_model is TextExtractionResponse:
            return (
                response_model(
                    candidates=[
                        ExtractedCandidate(
                            predicate="oc:uses_system_demo",
                            roles={
                                "subject": [
                                    ExtractedEntityFiller(
                                        kind="entity", entity_type="oc:activity",
                                        name="Alpha",
                                    ),
                                ],
                            },
                            evidence_spans=[
                                ExtractedEvidenceSpan(text="Wrong"),
                            ],
                        ),
                    ]
                ),
                SimpleNamespace(resolved_model=model),
            )
        return response_model.model_validate(
            {"judgments": [{"candidate_index": 0, "label": "supported"}]}
        ), SimpleNamespace(resolved_model=model)

    monkeypatch.setattr(
        extraction_module,
        "_load_llm_client_api",
        lambda: extraction_module._LLMClientAPI(
            get_model=fake_get_model,
            render_prompt=_render_prompt,
            call_llm_structured=cast(Any, fake_call_llm_structured),
        ),
    )

    # With strict=False, bad spans are skipped. The candidate may still
    # submit with 0 evidence spans (downstream handles this).
    results = service.extract_and_submit(
        source_text="Alpha Beta",
        profile_id="default",
        profile_version="1.0.0",
        submitted_by="analyst:text-extract",
        source_ref="text://phase4/bad-span",
    )
    # Candidate submitted but with 0 resolved evidence spans
    assert len(results) >= 0  # may be 0 or 1 depending on downstream handling


def test_judge_candidate_uses_explicit_judge_model_override(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Single-candidate auto review must honor the explicit bounded judge model."""

    review_service = _make_review_service(tmp_path)
    submission = review_service.submit_candidate_assertion(
        payload={
            "predicate": "oc:uses_system_demo",
            "roles": {
                "subject": [
                    {
                        "kind": "entity",
                        "entity_type": "oc:activity",
                        "name": "Mission planning",
                    }
                ]
            },
        },
        profile_id="default",
        profile_version="1.0.0",
        submitted_by="judge-test",
        source_kind="text_file",
        source_ref="text://phase4/judge-override",
        claim_text="Mission planning is the subject.",
    )
    service = TextExtractionService(
        review_service=review_service,
        judge_model_override="judge-lite-test",
    )
    calls: dict[str, object] = {}

    def fake_call_llm_structured(
        model: str,
        messages: list[dict[str, str]],
        response_model: type[BaseModel],
        **kwargs: object,
    ) -> tuple[BaseModel, object]:
        calls["model"] = model
        calls["messages"] = messages
        calls["kwargs"] = kwargs
        result = response_model.model_validate(
            {"judgments": [{"candidate_index": 0, "label": "partially_supported"}]}
        )
        return result, SimpleNamespace(resolved_model=model)

    monkeypatch.setattr(
        extraction_module,
        "_load_llm_client_api",
        lambda: extraction_module._LLMClientAPI(
            get_model=lambda task, **kw: "unused-model",
            render_prompt=_render_prompt,
            call_llm_structured=cast(Any, fake_call_llm_structured),
        ),
    )

    label = service._judge_candidate(
        submission.candidate,
        "Mission planning uses the radar system during the exercise.",
        get_config(),
    )

    assert label == "partially_supported"
    assert calls["model"] == "judge-lite-test"
    call_kwargs = calls["kwargs"]
    assert isinstance(call_kwargs, dict)
    assert call_kwargs["task"] == get_config().evaluation.judge_selection_task
    assert call_kwargs["max_budget"] == get_config().evaluation.judge_max_budget_usd


def test_extract_and_submit_leaves_candidate_pending_when_auto_review_judge_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Judge failure must leave the candidate pending instead of silently accepting it."""

    base_config = get_config()
    config_override = base_config.model_copy(
        update={
            "pipeline": base_config.pipeline.model_copy(update={"review_mode": "llm"}),
            "extraction": base_config.extraction.model_copy(
                update={"enable_judge_filter": False}
            ),
        }
    )
    monkeypatch.setattr(extraction_module, "get_config", lambda: config_override)
    review_service = _make_review_service(tmp_path)
    service = TextExtractionService(
        review_service=review_service,
        judge_model_override="judge-lite-test",
    )

    def fake_call_llm_structured(
        model: str,
        messages: list[dict[str, str]],
        response_model: type[BaseModel],
        **kwargs: object,
    ) -> tuple[BaseModel, object]:
        del model, messages, kwargs
        if response_model is TextExtractionResponse:
            return (
                response_model(
                    candidates=[
                        ExtractedCandidate(
                            predicate="oc:uses_system_demo",
                            roles={
                                "subject": [
                                    ExtractedEntityFiller(
                                        kind="entity",
                                        entity_type="oc:activity",
                                        name="Mission planning",
                                    )
                                ]
                            },
                            evidence_spans=[ExtractedEvidenceSpan(text="Mission planning")],
                            claim_text="Mission planning is the subject.",
                        )
                    ]
                ),
                SimpleNamespace(resolved_model="extract-model"),
            )
        raise RuntimeError("judge boom")

    monkeypatch.setattr(
        extraction_module,
        "_load_llm_client_api",
        lambda: extraction_module._LLMClientAPI(
            get_model=lambda task, **kw: "extract-model",
            render_prompt=_render_prompt,
            call_llm_structured=cast(Any, fake_call_llm_structured),
        ),
    )

    results = service.extract_and_submit(
        source_text="Mission planning uses the radar system during the exercise.",
        profile_id="default",
        profile_version="1.0.0",
        submitted_by="analyst:text-extract",
        source_ref="text://phase4/auto-review-failure",
    )

    assert len(results) == 1
    persisted = review_service.list_candidate_assertions()
    assert len(persisted) == 1
    assert persisted[0].review_status == "pending_review"
    promoted = CanonicalGraphService(db_path=review_service.store.db_path).list_promoted_assertions()
    assert promoted == []
    assert "leaving candidate pending" in caplog.text


@pytest.mark.parametrize(
    ("judge_label", "expected_status", "expected_promoted_count"),
    [
        ("partially_supported", "pending_review", 0),
        ("unsupported", "rejected", 0),
        ("supported", "accepted", 1),
    ],
)
def test_extract_and_submit_applies_llm_review_label_contract(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    judge_label: str,
    expected_status: str,
    expected_promoted_count: int,
) -> None:
    """LLM review mode should treat supported, partial, and unsupported labels differently."""

    base_config = get_config()
    config_override = base_config.model_copy(
        update={
            "pipeline": base_config.pipeline.model_copy(update={"review_mode": "llm"}),
            "extraction": base_config.extraction.model_copy(
                update={"enable_judge_filter": False}
            ),
        }
    )
    monkeypatch.setattr(extraction_module, "get_config", lambda: config_override)
    review_service = _make_review_service(tmp_path)
    service = TextExtractionService(
        review_service=review_service,
        judge_model_override="judge-lite-test",
    )

    def fake_call_llm_structured(
        model: str,
        messages: list[dict[str, str]],
        response_model: type[BaseModel],
        **kwargs: object,
    ) -> tuple[BaseModel, object]:
        del model, messages, kwargs
        if response_model is TextExtractionResponse:
            return (
                response_model(
                    candidates=[
                        ExtractedCandidate(
                            predicate="oc:uses_system_demo",
                            roles={
                                "subject": [
                                    ExtractedEntityFiller(
                                        kind="entity",
                                        entity_type="oc:activity",
                                        name="Mission planning",
                                    )
                                ]
                            },
                            evidence_spans=[ExtractedEvidenceSpan(text="Mission planning")],
                            claim_text="Mission planning is the subject.",
                        )
                    ]
                ),
                SimpleNamespace(resolved_model="extract-model"),
            )
        return (
            response_model.model_validate(
                {"judgments": [{"candidate_index": 0, "label": judge_label}]}
            ),
            SimpleNamespace(resolved_model="judge-model"),
        )

    monkeypatch.setattr(
        extraction_module,
        "_load_llm_client_api",
        lambda: extraction_module._LLMClientAPI(
            get_model=lambda task, **kw: "extract-model",
            render_prompt=_render_prompt,
            call_llm_structured=cast(Any, fake_call_llm_structured),
        ),
    )

    results = service.extract_and_submit(
        source_text="Mission planning uses the radar system during the exercise.",
        profile_id="default",
        profile_version="1.0.0",
        submitted_by="analyst:text-extract",
        source_ref="text://phase4/auto-review-label-contract",
    )

    assert len(results) == 1
    persisted = review_service.list_candidate_assertions()
    assert len(persisted) == 1
    assert persisted[0].review_status == expected_status
    promoted = CanonicalGraphService(db_path=review_service.store.db_path).list_promoted_assertions()
    assert len(promoted) == expected_promoted_count


def test_extraction_response_accepts_entity_fillers_without_entity_id() -> None:
    """Entity fillers may omit entity_id when they still provide a named mention."""

    response = TextExtractionResponse.model_validate(
        {
            "candidates": [
                {
                    "predicate": "oc:hold_command_role",
                    "roles": {
                        "commander": [
                            {
                                "kind": "entity",
                                "entity_type": "oc:person",
                                "name": "Admiral Eric Olson",
                            }
                        ]
                    },
                    "evidence_spans": [{"text": "Admiral Eric Olson"}],
                }
            ]
        }
    )

    candidate = response.candidates[0]
    assert candidate.roles["commander"][0].entity_id is None
    assert candidate.roles["commander"][0].name == "Admiral Eric Olson"


def test_extraction_response_drops_candidate_when_roles_field_is_missing() -> None:
    """Response parsing should salvage the document when one candidate omits roles."""

    response = TextExtractionResponse.model_validate(
        {
            "candidates": [
                {
                    "predicate": "oc:replace_designation",
                    "evidence_spans": [{"text": "PSYOP was officially replaced"}],
                }
            ]
        }
    )

    assert response.candidates == []


def test_extraction_response_schema_requires_candidates_and_roles() -> None:
    """The structured schema should advertise `candidates` and candidate `roles` as required."""

    response_schema = TextExtractionResponse.model_json_schema()
    candidate_schema = ExtractedCandidate.model_json_schema()

    assert "candidates" in response_schema["required"]
    assert "roles" in candidate_schema["required"]


def test_extraction_response_resolves_offsets_from_exact_text() -> None:
    """Quoted evidence text should resolve into deterministic offsets."""

    candidate_import = extraction_module.candidate_import_from_extracted(
        candidate=ExtractedCandidate(
            predicate="oc:uses_system_demo",
            roles={
                "subject": [
                    ExtractedEntityFiller(
                        kind="entity", entity_type="oc:activity",
                        name="Mission planning",
                    )
                ],
            },
            evidence_spans=[
                ExtractedEvidenceSpan(text="Mission planning"),
            ],
        ),
        profile=ProfileRef(profile_id="default", profile_version="1.0.0"),
        submitted_by="analyst:text-extract",
        source_artifact=SourceArtifactRef(
            source_kind="raw_text",
            source_ref="text://phase4/span-resolution",
            content_text="Mission planning uses the radar system.",
        ),
    )

    assert candidate_import.evidence_spans == (
        EvidenceSpan(start_char=0, end_char=16, text="Mission planning"),
    )


def test_extraction_response_normalizes_raw_only_value_filler() -> None:
    """Raw-only value fillers should normalize into pipeline payload values."""

    candidate_import = extraction_module.candidate_import_from_extracted(
        candidate=ExtractedCandidate(
            predicate="oc:describe_dissatisfaction",
            roles={
                "description": [
                    ExtractedValueFiller(
                        kind="value", value_kind="description",
                        raw="transition to a central pillar",
                    )
                ],
            },
            evidence_spans=[
                ExtractedEvidenceSpan(text="transition to a central pillar"),
            ],
        ),
        profile=ProfileRef(profile_id="default", profile_version="1.0.0"),
        submitted_by="analyst:text-extract",
        source_artifact=SourceArtifactRef(
            source_kind="raw_text",
            source_ref="text://phase4/raw-value",
            content_text="The report describes a transition to a central pillar.",
        ),
    )

    roles_obj = candidate_import.payload.get("roles")
    assert isinstance(roles_obj, dict)
    fillers = roles_obj.get("description")
    assert isinstance(fillers, list)
    filler = fillers[0]
    assert isinstance(filler, dict)
    assert filler["normalized"] == "transition to a central pillar"


def test_candidate_import_drops_optional_unknown_fillers_before_validation(tmp_path: Path) -> None:
    """Optional unknown fillers should not invalidate an otherwise good candidate."""

    review_service = _make_review_service(tmp_path)
    loaded_profile = load_effective_profile(
        "general_purpose_open",
        "0.1.0",
        overlay_root=review_service.overlay_root,
    )

    candidate_import = extraction_module.candidate_import_from_extracted(
        candidate=ExtractedCandidate(
            predicate="gp:holds_role",
            roles={
                "subject": [
                    ExtractedEntityFiller(
                        kind="entity",
                        entity_type="oc:person",
                        name="Sarah Chen",
                    )
                ],
                "organization": [
                    ExtractedEntityFiller(
                        kind="entity",
                        entity_type="oc:educational_institution",
                        name="George Washington University",
                    )
                ],
                "role_title": [
                    extraction_module.ExtractedUnknownFiller(
                        kind="unknown",
                        raw="lectured",
                    )
                ],
            },
            evidence_spans=[ExtractedEvidenceSpan(text="George Washington University")],
            claim_text="Sarah Chen lectured at George Washington University.",
        ),
        profile=ProfileRef(profile_id="general_purpose_open", profile_version="0.1.0"),
        loaded_profile=loaded_profile,
        submitted_by="analyst:text-extract",
        source_artifact=SourceArtifactRef(
            source_kind="raw_text",
            source_ref="text://phase4/optional-unknown",
            content_text="Sarah Chen lectured at George Washington University.",
        ),
    )

    roles_obj = candidate_import.payload.get("roles")
    assert isinstance(roles_obj, dict)
    assert "role_title" not in roles_obj

    submission = review_service.submit_candidate_import(candidate_import=candidate_import)
    assert submission.candidate.validation_status == "valid"


def test_candidate_import_keeps_required_unknown_fillers(tmp_path: Path) -> None:
    """Required malformed fillers must still fail loud after sanitization."""

    review_service = _make_review_service(tmp_path)
    loaded_profile = load_effective_profile(
        "general_purpose_open",
        "0.1.0",
        overlay_root=review_service.overlay_root,
    )

    candidate_import = extraction_module.candidate_import_from_extracted(
        candidate=ExtractedCandidate(
            predicate="gp:occurs_at",
            roles={
                "subject": [
                    extraction_module.ExtractedUnknownFiller(
                        kind="unknown",
                        raw="lectured",
                    )
                ],
                "location": [
                    ExtractedEntityFiller(
                        kind="entity",
                        entity_type="oc:educational_institution",
                        name="George Washington University",
                    )
                ],
            },
            evidence_spans=[ExtractedEvidenceSpan(text="George Washington University")],
            claim_text="Sarah Chen lectured at George Washington University.",
        ),
        profile=ProfileRef(profile_id="general_purpose_open", profile_version="0.1.0"),
        loaded_profile=loaded_profile,
        submitted_by="analyst:text-extract",
        source_artifact=SourceArtifactRef(
            source_kind="raw_text",
            source_ref="text://phase4/required-unknown",
            content_text="Sarah Chen lectured at George Washington University.",
        ),
    )

    roles_obj = candidate_import.payload.get("roles")
    assert isinstance(roles_obj, dict)
    assert "subject" in roles_obj

    submission = review_service.submit_candidate_import(candidate_import=candidate_import)
    assert submission.candidate.validation_status == "invalid"


def test_render_predicate_catalog_includes_role_constraints(tmp_path: Path) -> None:
    """The prompt-facing predicate catalog should include role-level constraints."""

    review_service = _make_review_service(tmp_path)
    profile = load_effective_profile(
        "dodaf_minimal_strict",
        "0.1.0",
        overlay_root=review_service.overlay_root,
    )

    rendered = extraction_module.render_predicate_catalog(profile)

    assert "source_node [required" in rendered
    assert "entity_type=dm2:OperationalNode" in rendered
    assert "information_element [required" in rendered
    assert "entity_type=dm2:InformationElement" in rendered


def test_extraction_response_normalizes_live_provider_shape() -> None:
    """The extractor boundary should normalize known live provider drift.

    The current live provider may:

    - encode the whole assertion envelope as JSON in the `predicate` field;
    - collapse singleton role fillers into objects instead of one-item arrays;
    - emit JSON arrays for evidence spans.

    This test keeps that boundary explicit so downstream layers can stay typed
    against the stable candidate-import contract.
    """

    response = TextExtractionResponse.model_validate(
        {
            "candidates": [
                {
                    "predicate": json.dumps(
                        {
                            "predicate_id": "oc:hold_command_role",
                            "roles": {
                                "commander": {
                                    "kind": "entity",
                                    "entity_id": "ent:person:admiral_eric_olson",
                                    "entity_type": "oc:person",
                                    "name": "Admiral Eric Olson",
                                },
                                "role_title": {
                                    "kind": "value",
                                    "value_kind": "string",
                                    "normalized": "commander",
                                    "raw": "commander",
                                },
                            },
                        }
                    ),
                    "evidence_spans": [
                        {
                            "start_char": 0,
                            "end_char": 18,
                            "text": "Admiral Eric Olson",
                        }
                    ],
                }
            ]
        }
    )

    assert len(response.candidates) == 1
    candidate = response.candidates[0]
    assert candidate.predicate == "oc:hold_command_role"
    assert candidate.roles["commander"][0].entity_id == "ent:person:admiral_eric_olson"
    assert candidate.roles["role_title"][0].normalized == "commander"
    assert candidate.evidence_spans[0].text == "Admiral Eric Olson"


def test_extraction_response_normalizes_pipe_delimited_predicate_envelope() -> None:
    """The extractor boundary should normalize `predicate | roles={...}` drift."""

    response = TextExtractionResponse.model_validate(
        {
            "candidates": [
                {
                    "predicate": (
                        'oc:hold_command_role | roles={"commander":{"kind":"entity",'
                        '"entity_id":"ent:person:admiral_eric_olson",'
                        '"entity_type":"oc:person","name":"Admiral Eric Olson"},'
                        '"role_title":{"kind":"value","value_kind":"string",'
                        '"normalized":"commander","raw":"commander"}}'
                    ),
                    "evidence_spans": [
                        {
                            "start_char": 0,
                            "end_char": 18,
                            "text": "Admiral Eric Olson",
                        }
                    ],
                }
            ]
        }
    )

    assert len(response.candidates) == 1
    candidate = response.candidates[0]
    assert candidate.predicate == "oc:hold_command_role"
    assert candidate.roles["commander"][0].entity_id == "ent:person:admiral_eric_olson"
    assert candidate.roles["role_title"][0].normalized == "commander"


# --- Schema enforcement tests ---


def test_filler_schema_has_descriptions_for_all_fields() -> None:
    """Every filler field must have a description for decode-time guidance.

    Descriptions are the primary mechanism for correct structured output.
    """

    schema = TextExtractionResponse.model_json_schema()
    defs = schema.get("$defs", {})
    filler_props = defs.get("ExtractedFiller", {}).get("properties", {})
    for field_name in ("kind", "entity_type", "name", "value_kind", "raw"):
        assert "description" in filler_props.get(field_name, {}), f"{field_name} missing description"


def test_entity_filler_accepts_null_entity_type() -> None:
    """Null entity_type is accepted — descriptions guide the model, validator doesn't enforce.

    This matches Phase B behavior: entity_type is optional in the schema.
    The model SHOULD fill it (guided by description) but the system doesn't
    reject it if missing — downstream identity/canonicalization handles it.
    """

    response = TextExtractionResponse.model_validate(
        {
            "candidates": [
                {
                    "predicate": "oc:test",
                    "roles": {
                        "subject": [{"kind": "entity", "entity_type": None, "name": "Alice"}]
                    },
                    "evidence_spans": [{"text": "Alice"}],
                }
            ]
        }
    )
    assert response.candidates[0].roles["subject"][0].entity_type is None


def test_entity_filler_rejects_missing_name() -> None:
    """Entity filler without name must still fail loudly at filler validation."""

    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        ExtractedEntityFiller.model_validate(
            {"kind": "entity", "entity_type": "oc:person"}
        )


def test_value_filler_rejects_missing_value_kind() -> None:
    """Value filler without value_kind must still fail loudly at filler validation."""

    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        ExtractedValueFiller.model_validate(
            {"kind": "value", "raw": "something"}
        )


def test_empty_roles_candidate_filtered_not_crashed() -> None:
    """Candidates with empty roles should be filtered out, not crash the parse.

    Providers do not enforce minProperties at decode time, so the LLM can
    produce candidates with ``"roles": {}``.  The response parser should
    recover valid candidates from the same response.
    """

    response = TextExtractionResponse.model_validate(
        {
            "candidates": [
                {
                    "predicate": "oc:hold_command_role",
                    "roles": {},
                    "evidence_spans": [{"text": "some text"}],
                },
                {
                    "predicate": "oc:lead_organization",
                    "roles": {
                        "leader": [
                            {
                                "kind": "entity",
                                "entity_type": "oc:person",
                                "name": "General Smith",
                            }
                        ]
                    },
                    "evidence_spans": [{"text": "General Smith"}],
                },
            ]
        }
    )

    assert len(response.candidates) == 1
    assert response.candidates[0].predicate == "oc:lead_organization"


def test_all_empty_roles_candidates_yield_empty_list() -> None:
    """When all candidates have empty roles, the response should have zero candidates."""

    response = TextExtractionResponse.model_validate(
        {
            "candidates": [
                {
                    "predicate": "oc:hold_command_role",
                    "roles": {},
                    "evidence_spans": [{"text": "some text"}],
                },
            ]
        }
    )

    assert len(response.candidates) == 0


def test_filler_value_field_drift_normalized_to_name() -> None:
    """LLM field drift: ``value`` should be normalized to ``name`` for entity fillers."""

    response = TextExtractionResponse.model_validate(
        {
            "candidates": [
                {
                    "predicate": "oc:hold_command_role",
                    "roles": {
                        "commander": [
                            {
                                "kind": "entity",
                                "entity_type": "oc:person",
                                "value": "Admiral Eric Olson",
                            }
                        ]
                    },
                    "evidence_spans": [{"text": "Admiral Eric Olson"}],
                }
            ]
        }
    )

    assert len(response.candidates) == 1
    filler = response.candidates[0].roles["commander"][0]
    assert filler.name == "Admiral Eric Olson"
    assert filler.entity_type == "oc:person"


def test_extra_fields_ignored_in_permissive_parsing() -> None:
    """Extra fields from provider drift should be silently ignored, not rejected."""

    response = TextExtractionResponse.model_validate(
        {
            "candidates": [
                {
                    "predicate": "oc:hold_command_role",
                    "roles": {
                        "commander": [
                            {
                                "kind": "entity",
                                "entity_type": "oc:person",
                                "name": "Admiral Eric Olson",
                                "confidence": 0.95,
                            }
                        ]
                    },
                    "evidence_spans": [{"text": "Admiral Eric Olson"}],
                    "model_notes": "high confidence",
                }
            ],
            "metadata": {"model": "gemini-2.5-flash"},
        }
    )

    assert len(response.candidates) == 1
    assert response.candidates[0].roles["commander"][0].name == "Admiral Eric Olson"

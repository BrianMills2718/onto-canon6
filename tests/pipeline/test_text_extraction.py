"""Tests for the llm_client-backed text extraction boundary."""

from __future__ import annotations

from importlib import import_module
import json
from pathlib import Path
from types import SimpleNamespace
import sys
from typing import Callable, cast

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))

from onto_canon6.ontology_runtime import clear_loader_caches  # noqa: E402
from onto_canon6.pipeline import EvidenceSpan, ReviewService  # noqa: E402
from onto_canon6.pipeline import text_extraction as extraction_module  # noqa: E402
from onto_canon6.pipeline.text_extraction import (  # noqa: E402
    ExtractedCandidate,
    ExtractedFiller,
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
    calls: dict[str, object] = {}

    def fake_get_model(task: str) -> str:
        calls["selection_task"] = task
        return "fake-structured-model"

    # mock-ok: isolates the llm_client network boundary while still exercising
    # the real prompt asset and local extractor contract.
    def fake_call_llm_structured(
        model: str,
        messages: list[dict[str, str]],
        response_model: type[TextExtractionResponse],
        **kwargs: object,
    ) -> tuple[TextExtractionResponse, object]:
        calls["model"] = model
        calls["messages"] = messages
        calls["kwargs"] = kwargs
        response = response_model(
            candidates=[
                ExtractedCandidate(
                    predicate="oc:uses_system_demo",
                    roles={
                        "subject": [
                            ExtractedFiller(
                                kind="entity",
                                entity_id="ent:activity:mission_planning",
                                entity_type="oc:activity",
                                name="Mission planning",
                            ),
                        ],
                        "object": [
                            ExtractedFiller(
                                kind="entity",
                                entity_id="ent:system:radar_system",
                                entity_type="oc:system",
                                name="radar system",
                            ),
                        ],
                    },
                    evidence_spans=[
                        EvidenceSpan(start_char=0, end_char=16, text="Mission planning"),
                        EvidenceSpan(start_char=26, end_char=38, text="radar system"),
                    ],
                    claim_text="Mission planning uses the radar system.",
                ),
            ]
        )
        return response, SimpleNamespace(resolved_model="fake-structured-model")

    monkeypatch.setattr(
        extraction_module,
        "_load_llm_client_api",
        lambda: extraction_module._LLMClientAPI(
            get_model=fake_get_model,
            render_prompt=_render_prompt,
            call_llm_structured=fake_call_llm_structured,
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
    assert imports[0].source_artifact.content_text is not None
    assert calls["selection_task"] == "extraction"
    call_kwargs = calls["kwargs"]
    assert isinstance(call_kwargs, dict)
    assert call_kwargs["task"] == "extraction"
    assert call_kwargs["max_budget"] == 0.25
    assert str(call_kwargs["trace_id"]).startswith("onto_canon6.extract.")
    messages = calls["messages"]
    assert isinstance(messages, list)
    assert "Mission planning uses the radar system during the exercise." in messages[-1]["content"]


def test_extract_and_submit_persists_extracted_candidates(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Extracted candidate imports should flow through the existing review store."""

    review_service = _make_review_service(tmp_path)
    service = TextExtractionService(review_service=review_service)

    def fake_get_model(task: str) -> str:
        return f"model-for-{task}"

    # mock-ok: isolates the llm_client network boundary for deterministic
    # review-pipeline integration testing.
    def fake_call_llm_structured(
        model: str,
        messages: list[dict[str, str]],
        response_model: type[TextExtractionResponse],
        **kwargs: object,
    ) -> tuple[TextExtractionResponse, object]:
        return (
            response_model(
                candidates=[
                    ExtractedCandidate(
                        predicate="oc:uses_system_demo",
                        roles={
                            "subject": [
                                ExtractedFiller(
                                    kind="entity",
                                    entity_id="ent:activity:mission_planning",
                                ),
                            ],
                        },
                        evidence_spans=[
                            EvidenceSpan(start_char=0, end_char=16, text="Mission planning"),
                        ],
                        claim_text="Mission planning is the subject.",
                    ),
                ]
            ),
            SimpleNamespace(resolved_model=model),
        )

    monkeypatch.setattr(
        extraction_module,
        "_load_llm_client_api",
        lambda: extraction_module._LLMClientAPI(
            get_model=fake_get_model,
            render_prompt=_render_prompt,
            call_llm_structured=fake_call_llm_structured,
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


def test_extract_and_submit_fails_loud_on_bad_evidence_span(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Bad extractor spans should fail loudly when routed into persistence."""

    service = TextExtractionService(review_service=_make_review_service(tmp_path))

    def fake_get_model(task: str) -> str:
        return f"model-for-{task}"

    # mock-ok: isolates the llm_client network boundary so the test can focus
    # on deterministic span verification behavior.
    def fake_call_llm_structured(
        model: str,
        messages: list[dict[str, str]],
        response_model: type[TextExtractionResponse],
        **kwargs: object,
    ) -> tuple[TextExtractionResponse, object]:
        return (
            response_model(
                candidates=[
                    ExtractedCandidate(
                        predicate="oc:uses_system_demo",
                        roles={
                            "subject": [
                                ExtractedFiller(
                                    kind="entity",
                                    entity_id="ent:activity:mission_planning",
                                ),
                            ],
                        },
                        evidence_spans=[
                            EvidenceSpan(start_char=0, end_char=5, text="Wrong"),
                        ],
                    ),
                ]
            ),
            SimpleNamespace(resolved_model=model),
        )

    monkeypatch.setattr(
        extraction_module,
        "_load_llm_client_api",
        lambda: extraction_module._LLMClientAPI(
            get_model=fake_get_model,
            render_prompt=_render_prompt,
            call_llm_structured=fake_call_llm_structured,
        ),
    )

    with pytest.raises(ValueError, match="evidence span 0 text does not match source text"):
        service.extract_and_submit(
            source_text="Alpha Beta",
            profile_id="default",
            profile_version="1.0.0",
            submitted_by="analyst:text-extract",
            source_ref="text://phase4/bad-span",
        )


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
                        '"entity_id":"ent:person:admiral_eric_olson"},'
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

"""Tests for Pass 1 progressive extraction (Plan 0018, Slice B).

All LLM calls are mocked (mock-ok: LLM calls must be mocked for
deterministic testing).  The tests exercise prompt rendering, JSON
parsing, entity deduplication, cost tracking, error handling, and
the permissive type policy.
"""

from __future__ import annotations

import json
from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock

import pytest

from onto_canon6.evaluation.fidelity_experiment import TOP_LEVEL_TYPES
from onto_canon6.pipeline.progressive_extractor import (
    _LLMClientAPI,
    _deduplicate_entities,
    _hash_text,
    _parse_llm_response,
    _render_type_list,
    run_pass1,
)
from onto_canon6.pipeline.progressive_types import Pass1Entity, Pass1Result, Pass1Triple


# ---------------------------------------------------------------------------
# Fixtures and helpers
# ---------------------------------------------------------------------------

SAMPLE_TEXT = (
    "Shield AI developed the Hivemind autonomous pilot software. "
    "The V-BAT drone, manufactured by Kratos Defense, was deployed by USSOCOM "
    "in a test exercise. Shield AI partnered with Kratos Defense to integrate "
    "Hivemind into the V-BAT platform."
)


def _make_valid_llm_json() -> str:
    """Return a well-formed Pass 1 JSON response."""
    return json.dumps(
        {
            "triples": [
                {
                    "entity_a": {
                        "name": "Shield AI",
                        "coarse_type": "Corporation",
                        "context": "Defense technology company",
                    },
                    "entity_b": {
                        "name": "Hivemind",
                        "coarse_type": "Abstract",
                        "context": "Autonomous pilot software",
                    },
                    "relationship_verb": "developed",
                    "evidence_span": "Shield AI developed the Hivemind autonomous pilot software",
                    "confidence": 0.9,
                },
                {
                    "entity_a": {
                        "name": "USSOCOM",
                        "coarse_type": "MilitaryOrganization",
                        "context": "United States Special Operations Command",
                    },
                    "entity_b": {
                        "name": "V-BAT",
                        "coarse_type": "MilitaryAircraft",
                        "context": "Autonomous VTOL drone",
                    },
                    "relationship_verb": "deployed",
                    "evidence_span": "V-BAT drone was deployed by USSOCOM",
                    "confidence": 0.85,
                },
            ]
        }
    )


def _make_llm_result(content: str, cost: float = 0.001) -> SimpleNamespace:
    """Create a fake LLMCallResult-like object."""
    return SimpleNamespace(content=content, cost=cost)


def _make_fake_api(
    llm_content: str,
    llm_cost: float = 0.001,
    *,
    acall_side_effect: Exception | None = None,
) -> _LLMClientAPI:
    """Build an _LLMClientAPI with mocked render_prompt and acall_llm.

    mock-ok: LLM network boundary must be mocked for deterministic testing.
    """
    fake_result = _make_llm_result(llm_content, cost=llm_cost)

    if acall_side_effect is not None:
        mock_acall = AsyncMock(side_effect=acall_side_effect)
    else:
        mock_acall = AsyncMock(return_value=fake_result)

    def fake_render(template_path: str, **context: Any) -> list[dict[str, str]]:
        return [
            {"role": "system", "content": "system prompt"},
            {"role": "user", "content": f"text: {context.get('text', '')[:50]}"},
        ]

    return _LLMClientAPI(
        render_prompt=fake_render,
        acall_llm=mock_acall,
    )


# ---------------------------------------------------------------------------
# 1. Prompt rendering
# ---------------------------------------------------------------------------


def test_prompt_renders_with_text_and_type_list() -> None:
    """The prompt template should render with text, type_list, and max_triples."""
    import llm_client

    type_list_str = _render_type_list()
    messages = llm_client.render_prompt(
        "prompts/extraction/pass1_open_extraction.yaml",
        text="Some test text about entities.",
        type_list=type_list_str,
        max_triples=10,
    )

    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"
    # The user message should contain the type list and text
    assert "Entity" in messages[1]["content"]
    assert "Corporation" in messages[1]["content"]
    assert "Some test text about entities." in messages[1]["content"]
    assert "10" in messages[1]["content"]


# ---------------------------------------------------------------------------
# 2. Successful extraction
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_successful_extraction() -> None:
    """A valid LLM JSON response should produce a Pass1Result with triples."""
    api = _make_fake_api(_make_valid_llm_json(), llm_cost=0.002)

    result = await run_pass1(
        SAMPLE_TEXT,
        trace_id="test/pass1/success",
        _llm_api=api,
    )

    assert isinstance(result, Pass1Result)
    assert len(result.triples) == 2
    assert result.triples[0].entity_a.name == "Shield AI"
    assert result.triples[0].entity_a.coarse_type == "Corporation"
    assert result.triples[0].relationship_verb == "developed"
    assert result.triples[1].entity_b.name == "V-BAT"
    assert result.cost == 0.002
    assert result.trace_id == "test/pass1/success"


# ---------------------------------------------------------------------------
# 3. Partial extraction (incomplete triple)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_partial_extraction_skips_incomplete_triples() -> None:
    """Triples missing entity_b should be dropped, not crash."""
    partial_json = json.dumps(
        {
            "triples": [
                {
                    "entity_a": {"name": "Shield AI", "coarse_type": "Corporation"},
                    "entity_b": {"name": "", "coarse_type": ""},
                    "relationship_verb": "does something",
                    "confidence": 0.5,
                },
                {
                    "entity_a": {"name": "USSOCOM", "coarse_type": "MilitaryOrganization"},
                    "entity_b": {"name": "V-BAT", "coarse_type": "MilitaryAircraft"},
                    "relationship_verb": "deployed",
                    "confidence": 0.8,
                },
            ]
        }
    )
    api = _make_fake_api(partial_json)

    result = await run_pass1(SAMPLE_TEXT, trace_id="test/pass1/partial", _llm_api=api)

    # Only the complete triple survives
    assert len(result.triples) == 1
    assert result.triples[0].entity_a.name == "USSOCOM"


# ---------------------------------------------------------------------------
# 4. Empty extraction
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_empty_extraction() -> None:
    """LLM returning no triples should produce a Pass1Result with empty lists."""
    api = _make_fake_api(json.dumps({"triples": []}))

    result = await run_pass1(SAMPLE_TEXT, trace_id="test/pass1/empty", _llm_api=api)

    assert result.triples == []
    assert result.entities == []
    assert result.source_text_hash.startswith("sha256:")


# ---------------------------------------------------------------------------
# 5. Parse failure
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_parse_failure_returns_empty_result() -> None:
    """Garbage LLM output should produce an empty Pass1Result, not crash."""
    api = _make_fake_api("This is not JSON at all!!!")

    result = await run_pass1(SAMPLE_TEXT, trace_id="test/pass1/garbage", _llm_api=api)

    assert result.triples == []
    assert result.entities == []
    # Cost should still be captured
    assert result.cost == 0.001


# ---------------------------------------------------------------------------
# 6. Entity deduplication
# ---------------------------------------------------------------------------


def test_entity_deduplication() -> None:
    """Same entity appearing in multiple triples should be deduplicated."""
    shield_ai = Pass1Entity(name="Shield AI", coarse_type="Corporation", context="")
    hivemind = Pass1Entity(name="Hivemind", coarse_type="Abstract", context="")
    vbat = Pass1Entity(name="V-BAT", coarse_type="MilitaryAircraft", context="")

    triples = [
        Pass1Triple(
            entity_a=shield_ai,
            entity_b=hivemind,
            relationship_verb="developed",
        ),
        Pass1Triple(
            entity_a=shield_ai,
            entity_b=vbat,
            relationship_verb="integrated",
        ),
    ]

    entities = _deduplicate_entities(triples)
    entity_names = [e.name for e in entities]
    assert len(entities) == 3
    assert entity_names.count("Shield AI") == 1


def test_dedup_preserves_different_types_for_same_name() -> None:
    """Same entity name with different coarse types should both be kept."""
    entity_org = Pass1Entity(name="Apple", coarse_type="Corporation", context="tech company")
    entity_obj = Pass1Entity(name="Apple", coarse_type="Object", context="a fruit")
    other = Pass1Entity(name="Orange", coarse_type="Object", context="")

    triples = [
        Pass1Triple(entity_a=entity_org, entity_b=other, relationship_verb="sells"),
        Pass1Triple(entity_a=entity_obj, entity_b=other, relationship_verb="resembles"),
    ]

    entities = _deduplicate_entities(triples)
    apple_entities = [e for e in entities if e.name == "Apple"]
    assert len(apple_entities) == 2


# ---------------------------------------------------------------------------
# 7. Cost tracking
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_cost_tracking() -> None:
    """Cost from the LLM result should be captured in the Pass1Result."""
    api = _make_fake_api(json.dumps({"triples": []}), llm_cost=0.0042)

    result = await run_pass1(SAMPLE_TEXT, trace_id="test/pass1/cost", _llm_api=api)

    assert result.cost == pytest.approx(0.0042)


# ---------------------------------------------------------------------------
# 8. Source text hashing
# ---------------------------------------------------------------------------


def test_source_text_hash_is_deterministic() -> None:
    """The same input text should always produce the same hash."""
    hash1 = _hash_text("Hello, world!")
    hash2 = _hash_text("Hello, world!")
    hash3 = _hash_text("Different text")

    assert hash1 == hash2
    assert hash1 != hash3
    assert hash1.startswith("sha256:")


# ---------------------------------------------------------------------------
# 9. Type validation (permissive)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_non_top_level_types_accepted() -> None:
    """Coarse types not in TOP_LEVEL_TYPES should still be accepted (permissive)."""
    custom_type_json = json.dumps(
        {
            "triples": [
                {
                    "entity_a": {
                        "name": "Some Entity",
                        "coarse_type": "ComputerProgram",
                        "context": "a software program",
                    },
                    "entity_b": {
                        "name": "Another Entity",
                        "coarse_type": "HumanAdult",
                        "context": "a person",
                    },
                    "relationship_verb": "was created by",
                    "confidence": 0.7,
                }
            ]
        }
    )
    # Verify these types are NOT in the top-level list
    assert "ComputerProgram" not in TOP_LEVEL_TYPES
    assert "HumanAdult" not in TOP_LEVEL_TYPES

    api = _make_fake_api(custom_type_json)

    result = await run_pass1(SAMPLE_TEXT, trace_id="test/pass1/permissive", _llm_api=api)

    assert len(result.triples) == 1
    assert result.triples[0].entity_a.coarse_type == "ComputerProgram"
    assert result.triples[0].entity_b.coarse_type == "HumanAdult"


# ---------------------------------------------------------------------------
# 10. LLM call failure
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_llm_call_failure_returns_empty_result() -> None:
    """An LLM call exception should produce an empty result, not crash."""
    api = _make_fake_api("", acall_side_effect=RuntimeError("network error"))

    result = await run_pass1(SAMPLE_TEXT, trace_id="test/pass1/failure", _llm_api=api)

    assert result.triples == []
    assert result.entities == []
    assert result.cost == 0.0


# ---------------------------------------------------------------------------
# 11. Markdown code fence stripping
# ---------------------------------------------------------------------------


def test_parse_strips_markdown_fences() -> None:
    """JSON wrapped in markdown code fences should parse correctly."""
    fenced = '```json\n{"triples": []}\n```'
    triples = _parse_llm_response(fenced)
    assert triples == []  # Valid empty result, not a parse error


# ---------------------------------------------------------------------------
# 12. Model parameter forwarding
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_custom_model_is_forwarded() -> None:
    """A custom model parameter should be forwarded to the LLM call."""
    api = _make_fake_api(json.dumps({"triples": []}))

    result = await run_pass1(
        SAMPLE_TEXT,
        model="custom/my-model",
        trace_id="test/pass1/model",
        _llm_api=api,
    )

    assert result.model == "custom/my-model"
    # Verify the custom model was passed to acall_llm
    api.acall_llm.assert_called_once()  # type: ignore[union-attr]
    assert api.acall_llm.call_args[0][0] == "custom/my-model"  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# 13. Default model
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_default_model_used_when_none() -> None:
    """When no model is specified, the default should be used."""
    api = _make_fake_api(json.dumps({"triples": []}))

    result = await run_pass1(
        SAMPLE_TEXT,
        trace_id="test/pass1/default_model",
        _llm_api=api,
    )

    assert result.model == "gemini/gemini-2.5-flash-lite"

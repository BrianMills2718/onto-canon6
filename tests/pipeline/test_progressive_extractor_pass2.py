"""Tests for Pass 2 progressive extraction — predicate mapping (Plan 0018, Slice C).

LLM calls are mocked (mock-ok: LLM calls must be mocked for deterministic
testing).  PredicateCanon lookups use the real sumo_plus.db for deterministic
lemma lookup tests.  Tests are skipped if the database is unavailable.
"""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock

import pytest

from onto_canon6.evaluation.predicate_canon import PredicateCanon, PredicateMatch
from onto_canon6.pipeline.progressive_extractor import (
    _LLMClientAPI,
    _build_single_sense_assertion,
    _lookup_lemma,
    _normalize_lemma,
    _parse_disambiguation_response,
    _render_candidates_for_prompt,
    run_pass2,
)
from onto_canon6.pipeline.progressive_types import (
    Pass1Entity,
    Pass1Result,
    Pass1Triple,
    Pass2MappedAssertion,
    Pass2Result,
)

SUMO_DB = Path(__file__).resolve().parents[2] / ".." / "onto-canon" / "data" / "sumo_plus.db"
SKIP_REASON = "sumo_plus.db not available"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def canon() -> PredicateCanon:
    """Provide a PredicateCanon instance, skipping if DB is absent."""
    if not SUMO_DB.exists():
        pytest.skip(SKIP_REASON)
    return PredicateCanon(SUMO_DB)


def _entity(name: str, coarse_type: str = "Entity") -> Pass1Entity:
    """Build a Pass1Entity with sensible defaults."""
    return Pass1Entity(name=name, coarse_type=coarse_type)


def _triple(
    verb: str,
    entity_a_name: str = "CIA",
    entity_b_name: str = "agents",
    evidence: str = "",
) -> Pass1Triple:
    """Build a Pass1Triple with sensible defaults."""
    return Pass1Triple(
        entity_a=_entity(entity_a_name, "Organization"),
        entity_b=_entity(entity_b_name, "Human"),
        relationship_verb=verb,
        evidence_span=evidence,
        confidence=0.8,
    )


def _pass1_result(triples: list[Pass1Triple]) -> Pass1Result:
    """Build a Pass1Result wrapping the given triples."""
    return Pass1Result(
        triples=triples,
        entities=[],
        source_text_hash="sha256:test",
        model="gemini/gemini-2.5-flash-lite",
        cost=0.001,
        trace_id="test/pass1",
    )


def _make_llm_result(content: str, cost: float = 0.001) -> SimpleNamespace:
    """Create a fake LLMCallResult-like object."""
    return SimpleNamespace(content=content, cost=cost)


def _make_fake_api(
    llm_content: str = "",
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
        """Fake render_prompt that returns minimal messages."""
        return [
            {"role": "system", "content": "system prompt"},
            {"role": "user", "content": f"verb: {context.get('relationship_verb', '')}"},
        ]

    return _LLMClientAPI(
        render_prompt=fake_render,
        acall_llm=mock_acall,
    )


# ---------------------------------------------------------------------------
# 1. Single-sense early exit
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_single_sense_early_exit(canon: PredicateCanon) -> None:
    """A single-sense lemma ('abate') should map deterministically with no LLM call."""
    api = _make_fake_api()
    p1 = _pass1_result([_triple("abate", "the storm", "its strength")])

    result = await run_pass2(
        p1,
        predicate_canon=canon,
        trace_id="test/pass2/single_sense",
        _llm_api=api,
    )

    assert isinstance(result, Pass2Result)
    assert len(result.mapped) == 1
    assert result.mapped[0].predicate_id == "abate_decrease_strength"
    assert result.mapped[0].propbank_sense_id == "abate-01"
    assert result.mapped[0].process_type == "Decreasing"
    assert result.mapped[0].disambiguation_method == "single_sense"
    assert result.single_sense_count == 1
    assert result.llm_disambiguated_count == 0
    # No LLM call should have been made
    api.acall_llm.assert_not_called()  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# 2. Multi-sense disambiguation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_multi_sense_disambiguation(canon: PredicateCanon) -> None:
    """A multi-sense lemma ('abandon') should call the LLM and pick one sense."""
    llm_response = json.dumps(
        {
            "predicate_id": "abandon_leave_behind",
            "role_mapping": {"ARG0": "CIA", "ARG1": "agents"},
        }
    )
    api = _make_fake_api(llm_response, llm_cost=0.002)
    p1 = _pass1_result(
        [_triple("abandon", "CIA", "agents", evidence="The CIA abandoned its agents")]
    )

    result = await run_pass2(
        p1,
        predicate_canon=canon,
        trace_id="test/pass2/multi_sense",
        _llm_api=api,
    )

    assert len(result.mapped) == 1
    assert result.mapped[0].predicate_id == "abandon_leave_behind"
    assert result.mapped[0].disambiguation_method == "llm_pick"
    assert result.llm_disambiguated_count == 1
    assert result.single_sense_count == 0
    api.acall_llm.assert_called_once()  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# 3. Unresolved lemma
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_unresolved_lemma(canon: PredicateCanon) -> None:
    """A verb with no predicate match should go to the unresolved list."""
    api = _make_fake_api()
    p1 = _pass1_result([_triple("zzz_nonexistent")])

    result = await run_pass2(
        p1,
        predicate_canon=canon,
        trace_id="test/pass2/unresolved",
        _llm_api=api,
    )

    assert len(result.mapped) == 0
    assert len(result.unresolved) == 1
    assert result.unresolved[0].relationship_verb == "zzz_nonexistent"
    assert result.unresolved_count == 1
    api.acall_llm.assert_not_called()  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# 4. Mixed batch
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_mixed_batch(canon: PredicateCanon) -> None:
    """A batch with single-sense, multi-sense, and unresolved triples."""
    llm_response = json.dumps(
        {
            "predicate_id": "abandon_leave_behind",
            "role_mapping": {"ARG0": "CIA", "ARG1": "agents"},
        }
    )
    api = _make_fake_api(llm_response, llm_cost=0.002)
    p1 = _pass1_result(
        [
            _triple("abate", "the storm", "its strength"),  # single-sense
            _triple("abandon", "CIA", "agents"),  # multi-sense
            _triple("zzz_nonexistent"),  # unresolved
        ]
    )

    result = await run_pass2(
        p1,
        predicate_canon=canon,
        trace_id="test/pass2/mixed",
        _llm_api=api,
    )

    assert result.single_sense_count == 1
    assert result.llm_disambiguated_count == 1
    assert result.unresolved_count == 1
    assert len(result.mapped) == 2
    assert len(result.unresolved) == 1


# ---------------------------------------------------------------------------
# 5. Role mapping from LLM
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_role_mapping_from_llm(canon: PredicateCanon) -> None:
    """LLM-returned role mapping should appear correctly in the assertion."""
    llm_response = json.dumps(
        {
            "predicate_id": "abandon_leave_behind",
            "role_mapping": {"ARG0": "CIA", "ARG1": "agents", "ARG2": "safe house"},
        }
    )
    api = _make_fake_api(llm_response)
    p1 = _pass1_result(
        [_triple("abandon", "CIA", "agents", evidence="CIA abandoned its agents")]
    )

    result = await run_pass2(
        p1,
        predicate_canon=canon,
        trace_id="test/pass2/role_mapping",
        _llm_api=api,
    )

    assert len(result.mapped) == 1
    roles = result.mapped[0].mapped_roles
    assert roles["ARG0"] == "CIA"
    assert roles["ARG1"] == "agents"
    assert roles["ARG2"] == "safe house"


# ---------------------------------------------------------------------------
# 6. LLM parse failure on disambiguation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_llm_parse_failure_goes_to_unresolved(canon: PredicateCanon) -> None:
    """Garbage LLM output during disambiguation should send the triple to unresolved."""
    api = _make_fake_api("This is not JSON at all!!!", llm_cost=0.001)
    p1 = _pass1_result(
        [_triple("abandon", "CIA", "agents")]
    )

    result = await run_pass2(
        p1,
        predicate_canon=canon,
        trace_id="test/pass2/parse_failure",
        _llm_api=api,
    )

    assert len(result.mapped) == 0
    assert len(result.unresolved) == 1
    assert result.unresolved_count == 1
    assert result.llm_disambiguated_count == 0


# ---------------------------------------------------------------------------
# 7. Cost tracking
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_cost_tracking(canon: PredicateCanon) -> None:
    """Only LLM-disambiguated triples should incur cost; single-sense are free."""
    llm_response = json.dumps(
        {
            "predicate_id": "abandon_leave_behind",
            "role_mapping": {"ARG0": "CIA", "ARG1": "agents"},
        }
    )
    api = _make_fake_api(llm_response, llm_cost=0.003)
    p1 = _pass1_result(
        [
            _triple("abate", "the storm", "its strength"),  # free
            _triple("abandon", "CIA", "agents"),  # costs 0.003
        ]
    )

    result = await run_pass2(
        p1,
        predicate_canon=canon,
        trace_id="test/pass2/cost",
        _llm_api=api,
    )

    assert result.cost == pytest.approx(0.003)
    assert result.single_sense_count == 1
    assert result.llm_disambiguated_count == 1


# ---------------------------------------------------------------------------
# 8. Provenance
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_provenance_references_input(canon: PredicateCanon) -> None:
    """source_pass1 should reference the exact input Pass1Result."""
    api = _make_fake_api()
    p1 = _pass1_result([_triple("abate")])

    result = await run_pass2(
        p1,
        predicate_canon=canon,
        trace_id="test/pass2/provenance",
        _llm_api=api,
    )

    assert result.source_pass1 is p1
    assert result.trace_id == "test/pass2/provenance"
    assert result.model == "gemini/gemini-2.5-flash-lite"


# ---------------------------------------------------------------------------
# 9. Empty pass1
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_empty_pass1(canon: PredicateCanon) -> None:
    """An empty Pass1Result should produce an empty Pass2Result."""
    api = _make_fake_api()
    p1 = _pass1_result([])

    result = await run_pass2(
        p1,
        predicate_canon=canon,
        trace_id="test/pass2/empty",
        _llm_api=api,
    )

    assert result.mapped == []
    assert result.unresolved == []
    assert result.single_sense_count == 0
    assert result.llm_disambiguated_count == 0
    assert result.unresolved_count == 0
    assert result.cost == 0.0


# ---------------------------------------------------------------------------
# 10. Prompt rendering
# ---------------------------------------------------------------------------


def test_prompt_renders_with_candidates() -> None:
    """The disambiguation template should render with candidate predicates."""
    import llm_client

    # Build minimal candidate data matching template expectations
    candidates = [
        {
            "predicate_id": "abandon_leave_behind",
            "propbank_sense_id": "abandon-01",
            "description": "leave behind",
            "process_type": "Leaving",
            "role_slots": [
                {
                    "arg_position": "ARG0",
                    "named_label": "Agent",
                    "type_constraint": "AutonomousAgent",
                    "required": False,
                },
                {
                    "arg_position": "ARG1",
                    "named_label": "Theme",
                    "type_constraint": "Entity",
                    "required": False,
                },
            ],
        },
    ]

    messages = llm_client.render_prompt(
        "prompts/extraction/pass2_predicate_disambiguation.yaml",
        relationship_verb="abandon",
        entity_a="CIA",
        entity_b="agents",
        evidence_span="The CIA abandoned its agents",
        candidates=candidates,
    )

    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"
    # Template should contain our variables
    user_content = messages[1]["content"]
    assert "abandon" in user_content
    assert "CIA" in user_content
    assert "agents" in user_content
    assert "abandon_leave_behind" in user_content
    assert "AutonomousAgent" in user_content


# ---------------------------------------------------------------------------
# Unit tests for helpers
# ---------------------------------------------------------------------------


def test_normalize_lemma_basic() -> None:
    """Basic lemma normalization should produce expected candidates."""
    assert _normalize_lemma("developed")[0] == "developed"
    assert "develop" in _normalize_lemma("developed")
    assert _normalize_lemma("ABATE")[0] == "abate"
    assert _normalize_lemma("  abandon  ")[0] == "abandon"


def test_normalize_lemma_short_words() -> None:
    """Very short words should not be over-stripped."""
    # "is" should not strip "s" to just "i" (too short)
    candidates = _normalize_lemma("is")
    assert "i" not in candidates


def test_lookup_lemma_with_suffix(canon: PredicateCanon) -> None:
    """Lookup should try suffix-stripped forms and find 'abate' from 'abated'."""
    matches = _lookup_lemma("abated", canon)
    assert len(matches) == 1
    assert matches[0].predicate_id == "abate_decrease_strength"


def test_render_candidates_for_prompt(canon: PredicateCanon) -> None:
    """Candidate rendering should produce template-friendly dicts."""
    matches = canon.lookup_by_lemma("abandon")
    rendered = _render_candidates_for_prompt(matches)
    assert len(rendered) == 3
    assert rendered[0]["predicate_id"] == "abandon_leave_behind"
    assert isinstance(rendered[0]["role_slots"], list)
    assert len(rendered[0]["role_slots"]) > 0


def test_build_single_sense_assertion(canon: PredicateCanon) -> None:
    """Single-sense builder should map ARG0->entity_a, ARG1->entity_b."""
    matches = canon.lookup_by_lemma("abate")
    assert len(matches) == 1
    triple = _triple("abate", "the storm", "its strength")
    assertion = _build_single_sense_assertion(triple, matches[0])
    assert assertion.predicate_id == "abate_decrease_strength"
    assert assertion.mapped_roles.get("ARG0") == "the storm"
    assert assertion.mapped_roles.get("ARG1") == "its strength"
    assert assertion.disambiguation_method == "single_sense"


def test_parse_disambiguation_response_valid(canon: PredicateCanon) -> None:
    """Valid disambiguation JSON should parse into a Pass2MappedAssertion."""
    matches = canon.lookup_by_lemma("abandon")
    triple = _triple("abandon", "CIA", "agents")
    raw = json.dumps(
        {
            "predicate_id": "abandon_leave_behind",
            "role_mapping": {"ARG0": "CIA", "ARG1": "agents"},
        }
    )
    result = _parse_disambiguation_response(raw, matches, triple)
    assert result is not None
    assert result.predicate_id == "abandon_leave_behind"
    assert result.mapped_roles == {"ARG0": "CIA", "ARG1": "agents"}


def test_parse_disambiguation_response_garbage(canon: PredicateCanon) -> None:
    """Garbage input should return None, not crash."""
    matches = canon.lookup_by_lemma("abandon")
    triple = _triple("abandon")
    assert _parse_disambiguation_response("not json", matches, triple) is None


def test_parse_disambiguation_response_unknown_predicate(canon: PredicateCanon) -> None:
    """A predicate_id not in the candidates should return None."""
    matches = canon.lookup_by_lemma("abandon")
    triple = _triple("abandon")
    raw = json.dumps(
        {
            "predicate_id": "totally_unknown_predicate",
            "role_mapping": {"ARG0": "CIA"},
        }
    )
    assert _parse_disambiguation_response(raw, matches, triple) is None

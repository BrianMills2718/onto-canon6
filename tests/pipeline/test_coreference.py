"""Tests for post-extraction coreference resolution.

All LLM calls are mocked (mock-ok: LLM network boundary must be mocked
for deterministic testing).  Tests exercise entity name merging,
propositional reference detection and resolution, the combined resolver,
edge cases (few entities, no vague refs, LLM failures), and the
json_schema response format builders.
"""

from __future__ import annotations

import json
from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock

import pytest

from onto_canon6.pipeline.coreference import (
    CorefGroup,
    EntityCorefResponse,
    PropCorefResponse,
    ResolvedReference,
    _LLMClientAPI,
    _MIN_ENTITIES_FOR_COREF,
    _apply_entity_merge,
    _build_entity_merge_map,
    _collect_entity_names,
    _entity_coref_response_format,
    _find_vague_references,
    _is_vague_reference,
    _prop_coref_response_format,
    resolve_coreferences,
    resolve_entity_coreferences,
    resolve_propositional_coreferences,
)
from onto_canon6.pipeline.text_extraction import (
    ExtractedCandidate,
    ExtractedEvidenceSpan,
    ExtractedFiller,
)


# ---------------------------------------------------------------------------
# Fixtures and helpers
# ---------------------------------------------------------------------------

SOURCE_TEXT = (
    "A Kurdish militia launched an offensive against ISIS positions near Raqqa. "
    "The militia, supported by US airstrikes, captured several villages. "
    "Turkey disputed these claims, saying the operation violated its sovereignty. "
    "The Kurdish fighters advanced despite Turkish objections."
)


def _make_entity_filler(name: str, entity_type: str = "oc:organization") -> ExtractedFiller:
    """Create an entity filler with the given name."""
    return ExtractedFiller(kind="entity", name=name, entity_type=entity_type)


def _make_unknown_filler(raw: str) -> ExtractedFiller:
    """Create an unknown filler with the given raw text."""
    return ExtractedFiller(kind="unknown", raw=raw)


def _make_evidence(text: str) -> ExtractedEvidenceSpan:
    """Create an evidence span."""
    return ExtractedEvidenceSpan(text=text)


def _make_candidate(
    predicate: str,
    roles: dict[str, list[ExtractedFiller]],
    evidence_text: str = "some evidence",
) -> ExtractedCandidate:
    """Create a candidate assertion."""
    return ExtractedCandidate(
        predicate=predicate,
        roles=roles,
        evidence_spans=[_make_evidence(evidence_text)],
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

    return _LLMClientAPI(
        render_prompt=lambda template_path, **ctx: [
            {"role": "system", "content": "test"},
            {"role": "user", "content": "test"},
        ],
        acall_llm=mock_acall,
    )


# ---------------------------------------------------------------------------
# Entity name collection
# ---------------------------------------------------------------------------


class TestCollectEntityNames:
    """Tests for _collect_entity_names."""

    def test_collects_unique_names(self) -> None:
        candidates = [
            _make_candidate(
                "attack",
                {
                    "ARG0": [_make_entity_filler("Kurdish militia")],
                    "ARG1": [_make_entity_filler("ISIS positions")],
                },
            ),
            _make_candidate(
                "capture",
                {
                    "ARG0": [_make_entity_filler("the militia")],
                    "ARG1": [_make_entity_filler("several villages")],
                },
            ),
        ]
        names = _collect_entity_names(candidates)
        assert names == ["Kurdish militia", "ISIS positions", "the militia", "several villages"]

    def test_deduplicates_names(self) -> None:
        candidates = [
            _make_candidate(
                "attack",
                {"ARG0": [_make_entity_filler("Shield AI")]},
            ),
            _make_candidate(
                "develop",
                {"ARG0": [_make_entity_filler("Shield AI")]},
            ),
        ]
        names = _collect_entity_names(candidates)
        assert names == ["Shield AI"]

    def test_skips_non_entity_fillers(self) -> None:
        candidates = [
            _make_candidate(
                "claim",
                {
                    "ARG0": [_make_entity_filler("Turkey")],
                    "ARG1": [_make_unknown_filler("these claims")],
                },
            ),
        ]
        names = _collect_entity_names(candidates)
        assert names == ["Turkey"]

    def test_empty_candidates(self) -> None:
        assert _collect_entity_names([]) == []


# ---------------------------------------------------------------------------
# Entity merge map
# ---------------------------------------------------------------------------


class TestBuildEntityMergeMap:
    """Tests for _build_entity_merge_map."""

    def test_builds_merge_map(self) -> None:
        groups = [
            CorefGroup(
                canonical_name="Kurdish militia",
                surface_forms=["Kurdish militia", "the militia", "Kurdish fighters"],
            ),
            CorefGroup(
                canonical_name="ISIS",
                surface_forms=["ISIS", "ISIS positions"],
            ),
        ]
        merge_map = _build_entity_merge_map(groups)
        assert merge_map == {
            "the militia": "Kurdish militia",
            "Kurdish fighters": "Kurdish militia",
            "ISIS positions": "ISIS",
        }

    def test_singleton_group_no_merges(self) -> None:
        groups = [
            CorefGroup(canonical_name="Turkey", surface_forms=["Turkey"]),
        ]
        assert _build_entity_merge_map(groups) == {}

    def test_empty_groups(self) -> None:
        assert _build_entity_merge_map([]) == {}


# ---------------------------------------------------------------------------
# Apply entity merge
# ---------------------------------------------------------------------------


class TestApplyEntityMerge:
    """Tests for _apply_entity_merge."""

    def test_merges_names(self) -> None:
        candidates = [
            _make_candidate(
                "attack",
                {"ARG0": [_make_entity_filler("the militia")]},
            ),
        ]
        merge_map = {"the militia": "Kurdish militia"}
        result = _apply_entity_merge(candidates, merge_map)
        assert len(result) == 1
        filler = result[0].roles["ARG0"][0]
        assert filler.name == "Kurdish militia"

    def test_no_merges_returns_same(self) -> None:
        candidates = [
            _make_candidate(
                "attack",
                {"ARG0": [_make_entity_filler("Turkey")]},
            ),
        ]
        result = _apply_entity_merge(candidates, {})
        assert result is candidates

    def test_preserves_non_matching(self) -> None:
        candidates = [
            _make_candidate(
                "attack",
                {"ARG0": [_make_entity_filler("Turkey")]},
            ),
        ]
        merge_map = {"the militia": "Kurdish militia"}
        result = _apply_entity_merge(candidates, merge_map)
        assert result[0].roles["ARG0"][0].name == "Turkey"


# ---------------------------------------------------------------------------
# Vague reference detection
# ---------------------------------------------------------------------------


class TestVagueReferenceDetection:
    """Tests for _is_vague_reference and _find_vague_references."""

    def test_detects_these_claims(self) -> None:
        filler = _make_unknown_filler("these claims")
        assert _is_vague_reference(filler) is True

    def test_detects_this_assessment(self) -> None:
        filler = _make_unknown_filler("this assessment")
        assert _is_vague_reference(filler) is True

    def test_detects_the_allegations(self) -> None:
        filler = _make_unknown_filler("the allegations")
        assert _is_vague_reference(filler) is True

    def test_rejects_specific_content(self) -> None:
        filler = _make_unknown_filler("the militia captured three villages near Raqqa")
        assert _is_vague_reference(filler) is False

    def test_detects_empty_name_as_vague(self) -> None:
        """A filler with no usable text content is treated as vague.

        ExtractedFiller validation prevents truly blank 'unknown' fillers,
        so we test via a value filler where name and raw are both None.
        """
        filler = ExtractedFiller(kind="value", value_kind="string", raw="n/a", name=None)
        # Monkey-patch raw to empty to simulate edge case at the _is_vague_reference level
        # Since the filler is frozen, construct directly with model_construct
        edge_filler = ExtractedFiller.model_construct(kind="unknown", raw="", name=None)
        assert _is_vague_reference(edge_filler) is True

    def test_finds_vague_in_candidates(self) -> None:
        candidates = [
            _make_candidate(
                "dispute",
                {
                    "ARG0": [_make_entity_filler("Turkey")],
                    "ARG1": [_make_unknown_filler("these claims")],
                },
                evidence_text="Turkey disputed these claims",
            ),
        ]
        refs = _find_vague_references(candidates)
        assert len(refs) == 1
        assert refs[0].vague_text == "these claims"
        assert refs[0].predicate == "dispute"

    def test_skips_entity_fillers(self) -> None:
        """Entity fillers are never treated as vague propositional references."""
        candidates = [
            _make_candidate(
                "attack",
                {"ARG0": [_make_entity_filler("the militia")]},
            ),
        ]
        refs = _find_vague_references(candidates)
        assert refs == []


# ---------------------------------------------------------------------------
# Response format schemas
# ---------------------------------------------------------------------------


class TestResponseFormats:
    """Verify json_schema response format structure."""

    def test_entity_coref_format(self) -> None:
        fmt = _entity_coref_response_format()
        assert fmt["type"] == "json_schema"
        assert "schema" in fmt["json_schema"]
        schema = fmt["json_schema"]["schema"]
        assert "properties" in schema
        assert "groups" in schema["properties"]

    def test_prop_coref_format(self) -> None:
        fmt = _prop_coref_response_format()
        assert fmt["type"] == "json_schema"
        assert "schema" in fmt["json_schema"]
        schema = fmt["json_schema"]["schema"]
        assert "properties" in schema
        assert "resolutions" in schema["properties"]


# ---------------------------------------------------------------------------
# Entity coreference resolver (async, mocked LLM)
# ---------------------------------------------------------------------------


class TestResolveEntityCoreferences:
    """Tests for resolve_entity_coreferences."""

    @pytest.mark.asyncio
    async def test_merges_coreferent_entities(self) -> None:
        candidates = [
            _make_candidate(
                "attack",
                {
                    "ARG0": [_make_entity_filler("Kurdish militia")],
                    "ARG1": [_make_entity_filler("ISIS positions")],
                },
            ),
            _make_candidate(
                "capture",
                {
                    "ARG0": [_make_entity_filler("the militia")],
                    "ARG1": [_make_entity_filler("several villages")],
                },
            ),
            _make_candidate(
                "advance",
                {
                    "ARG0": [_make_entity_filler("Kurdish fighters")],
                },
            ),
        ]

        llm_response = json.dumps({
            "groups": [
                {
                    "canonical_name": "Kurdish militia",
                    "surface_forms": ["Kurdish militia", "the militia", "Kurdish fighters"],
                },
                {
                    "canonical_name": "ISIS positions",
                    "surface_forms": ["ISIS positions"],
                },
                {
                    "canonical_name": "several villages",
                    "surface_forms": ["several villages"],
                },
            ]
        })
        api = _make_fake_api(llm_response)

        result = await resolve_entity_coreferences(
            candidates,
            source_text=SOURCE_TEXT,
            task="test",
            trace_id="test-entity-coref",
            _llm_api=api,
        )

        assert len(result) == 3
        # "the militia" -> "Kurdish militia"
        assert result[1].roles["ARG0"][0].name == "Kurdish militia"
        # "Kurdish fighters" -> "Kurdish militia"
        assert result[2].roles["ARG0"][0].name == "Kurdish militia"
        # Unchanged entities stay the same
        assert result[0].roles["ARG0"][0].name == "Kurdish militia"
        assert result[0].roles["ARG1"][0].name == "ISIS positions"

    @pytest.mark.asyncio
    async def test_skips_when_too_few_entities(self) -> None:
        """Should not call LLM when fewer than _MIN_ENTITIES_FOR_COREF entities."""
        candidates = [
            _make_candidate(
                "attack",
                {"ARG0": [_make_entity_filler("Turkey")]},
            ),
        ]
        api = _make_fake_api("")
        result = await resolve_entity_coreferences(
            candidates,
            task="test",
            trace_id="test-skip",
            _llm_api=api,
        )
        assert result is candidates
        api.acall_llm.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_returns_original_on_llm_failure(self) -> None:
        candidates = [
            _make_candidate(
                "attack",
                {
                    "ARG0": [_make_entity_filler("A")],
                    "ARG1": [_make_entity_filler("B")],
                    "ARG2": [_make_entity_filler("C")],
                },
            ),
        ]
        api = _make_fake_api("", acall_side_effect=RuntimeError("LLM down"))
        result = await resolve_entity_coreferences(
            candidates,
            task="test",
            trace_id="test-fail",
            _llm_api=api,
        )
        assert result is candidates

    @pytest.mark.asyncio
    async def test_returns_original_on_parse_failure(self) -> None:
        candidates = [
            _make_candidate(
                "attack",
                {
                    "ARG0": [_make_entity_filler("A")],
                    "ARG1": [_make_entity_filler("B")],
                    "ARG2": [_make_entity_filler("C")],
                },
            ),
        ]
        api = _make_fake_api("not valid json at all")
        result = await resolve_entity_coreferences(
            candidates,
            task="test",
            trace_id="test-parse-fail",
            _llm_api=api,
        )
        assert result is candidates

    @pytest.mark.asyncio
    async def test_no_merges_needed(self) -> None:
        """When all entities are distinct, no merges should happen."""
        candidates = [
            _make_candidate(
                "trade",
                {
                    "ARG0": [_make_entity_filler("USA")],
                    "ARG1": [_make_entity_filler("China")],
                    "ARG2": [_make_entity_filler("EU")],
                },
            ),
        ]
        llm_response = json.dumps({
            "groups": [
                {"canonical_name": "USA", "surface_forms": ["USA"]},
                {"canonical_name": "China", "surface_forms": ["China"]},
                {"canonical_name": "EU", "surface_forms": ["EU"]},
            ]
        })
        api = _make_fake_api(llm_response)
        result = await resolve_entity_coreferences(
            candidates,
            task="test",
            trace_id="test-no-merge",
            _llm_api=api,
        )
        # No merges, but structure is preserved
        assert result[0].roles["ARG0"][0].name == "USA"


# ---------------------------------------------------------------------------
# Propositional coreference resolver (async, mocked LLM)
# ---------------------------------------------------------------------------


class TestResolvePropositionalCoreferences:
    """Tests for resolve_propositional_coreferences."""

    @pytest.mark.asyncio
    async def test_resolves_vague_reference(self) -> None:
        candidates = [
            _make_candidate(
                "dispute",
                {
                    "ARG0": [_make_entity_filler("Turkey")],
                    "ARG1": [_make_unknown_filler("these claims")],
                },
                evidence_text="Turkey disputed these claims",
            ),
        ]

        llm_response = json.dumps({
            "resolutions": [
                {
                    "index": 1,
                    "resolved_text": (
                        "the Kurdish militia captured several villages "
                        "near Raqqa with US airstrike support"
                    ),
                },
            ]
        })
        api = _make_fake_api(llm_response)

        result = await resolve_propositional_coreferences(
            candidates,
            SOURCE_TEXT,
            task="test",
            trace_id="test-prop-coref",
            _llm_api=api,
        )

        assert len(result) == 1
        resolved_filler = result[0].roles["ARG1"][0]
        assert "Kurdish militia captured" in resolved_filler.raw

    @pytest.mark.asyncio
    async def test_skips_when_no_vague_refs(self) -> None:
        candidates = [
            _make_candidate(
                "attack",
                {
                    "ARG0": [_make_entity_filler("Turkey")],
                    "ARG1": [_make_entity_filler("Kurdish militia")],
                },
            ),
        ]
        api = _make_fake_api("")
        result = await resolve_propositional_coreferences(
            candidates,
            SOURCE_TEXT,
            task="test",
            trace_id="test-skip",
            _llm_api=api,
        )
        assert result is candidates
        api.acall_llm.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_returns_original_on_llm_failure(self) -> None:
        candidates = [
            _make_candidate(
                "dispute",
                {
                    "ARG0": [_make_entity_filler("Turkey")],
                    "ARG1": [_make_unknown_filler("these claims")],
                },
            ),
        ]
        api = _make_fake_api("", acall_side_effect=RuntimeError("LLM down"))
        result = await resolve_propositional_coreferences(
            candidates,
            SOURCE_TEXT,
            task="test",
            trace_id="test-fail",
            _llm_api=api,
        )
        assert result is candidates


# ---------------------------------------------------------------------------
# Combined resolver
# ---------------------------------------------------------------------------


class TestResolveCoreferences:
    """Tests for the combined resolve_coreferences entry point."""

    @pytest.mark.asyncio
    async def test_runs_both_resolvers(self) -> None:
        """Verify entity coref runs first, then propositional coref."""
        candidates = [
            _make_candidate(
                "attack",
                {
                    "ARG0": [_make_entity_filler("Kurdish militia")],
                    "ARG1": [_make_entity_filler("ISIS positions")],
                },
            ),
            _make_candidate(
                "capture",
                {
                    "ARG0": [_make_entity_filler("the militia")],
                    "ARG1": [_make_entity_filler("villages")],
                },
            ),
            _make_candidate(
                "dispute",
                {
                    "ARG0": [_make_entity_filler("Turkey")],
                    "ARG1": [_make_unknown_filler("these claims")],
                },
            ),
        ]

        # First call: entity coref; second call: propositional coref
        entity_response = json.dumps({
            "groups": [
                {
                    "canonical_name": "Kurdish militia",
                    "surface_forms": ["Kurdish militia", "the militia"],
                },
                {"canonical_name": "ISIS positions", "surface_forms": ["ISIS positions"]},
                {"canonical_name": "villages", "surface_forms": ["villages"]},
                {"canonical_name": "Turkey", "surface_forms": ["Turkey"]},
            ]
        })
        prop_response = json.dumps({
            "resolutions": [
                {
                    "index": 1,
                    "resolved_text": "the Kurdish militia captured villages near Raqqa",
                },
            ]
        })

        call_count = 0

        async def _mock_acall(model: str, messages: Any, **kwargs: Any) -> SimpleNamespace:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return _make_llm_result(entity_response)
            return _make_llm_result(prop_response)

        api = _LLMClientAPI(
            render_prompt=lambda template_path, **ctx: [
                {"role": "system", "content": "test"},
                {"role": "user", "content": "test"},
            ],
            acall_llm=_mock_acall,  # type: ignore[arg-type]
        )

        result = await resolve_coreferences(
            candidates,
            SOURCE_TEXT,
            task="test",
            trace_id="test-combined",
            _llm_api=api,
        )

        assert call_count == 2
        # Entity merge applied
        assert result[1].roles["ARG0"][0].name == "Kurdish militia"
        # Propositional resolution applied
        assert "Kurdish militia captured" in result[2].roles["ARG1"][0].raw

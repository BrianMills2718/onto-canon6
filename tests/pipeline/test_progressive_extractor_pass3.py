"""Tests for Pass 3 progressive extraction -- entity refinement (Plan 0018, Slice D).

LLM calls are mocked (mock-ok: LLM calls must be mocked for deterministic
testing). SUMOHierarchy and PredicateCanon use the real repo-local
``sumo_plus.db`` for deterministic subtree and role-constraint tests. Tests
are skipped if the database is unavailable.
"""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock

import pytest

from onto_canon6.evaluation.predicate_canon import PredicateCanon
from onto_canon6.evaluation.sumo_hierarchy import SUMOHierarchy
from onto_canon6.pipeline.progressive_extractor import (
    _LLMClientAPI,
    _is_leaf,
    _narrow_candidates,
    _parse_refinement_response,
    run_pass3,
)
from onto_canon6.pipeline.progressive_types import (
    EntityRefinement,
    Pass1Entity,
    Pass1Result,
    Pass1Triple,
    Pass2MappedAssertion,
    Pass2Result,
    Pass3Result,
    Pass3TypedAssertion,
)

SUMO_DB = Path(__file__).resolve().parents[2] / "data" / "sumo_plus.db"
SKIP_REASON = "sumo_plus.db not available"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def hierarchy() -> SUMOHierarchy:
    """Provide a SUMOHierarchy instance, skipping if DB is absent."""
    if not SUMO_DB.exists():
        pytest.skip(SKIP_REASON)
    return SUMOHierarchy(SUMO_DB)


@pytest.fixture()
def canon() -> PredicateCanon:
    """Provide a PredicateCanon instance, skipping if DB is absent."""
    if not SUMO_DB.exists():
        pytest.skip(SKIP_REASON)
    return PredicateCanon(SUMO_DB)


def _entity(name: str, coarse_type: str = "Entity", context: str = "") -> Pass1Entity:
    """Build a Pass1Entity with sensible defaults."""
    return Pass1Entity(name=name, coarse_type=coarse_type, context=context)


def _triple(
    verb: str,
    entity_a_name: str = "CIA",
    entity_a_type: str = "Organization",
    entity_b_name: str = "agents",
    entity_b_type: str = "Human",
    evidence: str = "",
) -> Pass1Triple:
    """Build a Pass1Triple with configurable entity types."""
    return Pass1Triple(
        entity_a=_entity(entity_a_name, entity_a_type),
        entity_b=_entity(entity_b_name, entity_b_type),
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


def _mapped_assertion(
    triple: Pass1Triple,
    predicate_id: str = "abandon_leave_behind",
    propbank_sense_id: str = "abandon-01",
    process_type: str = "Leaving",
    mapped_roles: dict[str, str] | None = None,
    disambiguation_method: str = "single_sense",
) -> Pass2MappedAssertion:
    """Build a Pass2MappedAssertion with sensible defaults."""
    if mapped_roles is None:
        mapped_roles = {
            "ARG0": triple.entity_a.name,
            "ARG1": triple.entity_b.name,
        }
    return Pass2MappedAssertion(
        triple=triple,
        predicate_id=predicate_id,
        propbank_sense_id=propbank_sense_id,
        process_type=process_type,
        mapped_roles=mapped_roles,
        disambiguation_method=disambiguation_method,
        mapping_confidence=0.9,
    )


def _pass2_result(
    mapped: list[Pass2MappedAssertion],
    triples: list[Pass1Triple] | None = None,
) -> Pass2Result:
    """Build a Pass2Result wrapping the given mapped assertions."""
    if triples is None:
        triples = [m.triple for m in mapped]
    p1 = _pass1_result(triples)
    return Pass2Result(
        mapped=mapped,
        unresolved=[],
        source_pass1=p1,
        model="gemini/gemini-2.5-flash-lite",
        cost=0.001,
        trace_id="test/pass2",
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
            {"role": "user", "content": f"entity: {context.get('entity_name', '')}"},
        ]

    return _LLMClientAPI(
        render_prompt=fake_render,
        acall_llm=mock_acall,
    )


# ---------------------------------------------------------------------------
# 1. Leaf early exit
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_leaf_early_exit(
    hierarchy: SUMOHierarchy, canon: PredicateCanon,
) -> None:
    """Entity with a leaf coarse_type should skip LLM, refined_type = coarse_type.

    We find a real leaf type in the SUMO hierarchy by picking a type that
    has no subtypes.  MilitaryOrganization or a similar deep type is used.
    """
    # Find a real leaf: pick a type known to be deep and check.
    # "InfantryUnit" is likely a leaf; fall back to a known check.
    leaf_type = _find_leaf_type(hierarchy)
    assert leaf_type is not None, "Could not find a leaf type in SUMO hierarchy"

    triple = _triple("abandon", "Delta Force", leaf_type, "the compound", "Object")
    assertion = _mapped_assertion(triple)
    p2 = _pass2_result([assertion])

    api = _make_fake_api()
    result = await run_pass3(
        p2,
        sumo_hierarchy=hierarchy,
        predicate_canon=canon,
        trace_id="test/pass3/leaf",
        _llm_api=api,
    )

    assert isinstance(result, Pass3Result)
    assert len(result.typed_assertions) == 1

    # Find the refinement for the leaf entity.
    refinements = result.typed_assertions[0].entity_refinements
    leaf_refs = [r for r in refinements if r.coarse_type == leaf_type]
    assert len(leaf_refs) >= 1
    ref = leaf_refs[0]
    assert ref.refined_type == leaf_type
    assert ref.refinement_method == "leaf_early_exit"
    assert ref.candidate_count == 0
    assert result.leaf_early_exit_count >= 1


def _find_leaf_type(hierarchy: SUMOHierarchy) -> str | None:
    """Find a real leaf type by checking known deep types."""
    # Try a few candidates likely to be leaves.
    for candidate in ["AbortedFlight", "AbortedLaunch", "Abdomen"]:
        if hierarchy.type_exists(candidate) and _is_leaf(hierarchy, candidate):
            return candidate
    # Fallback: find any leaf among Organization subtypes.
    for sub in hierarchy.subtypes("Organization"):
        if _is_leaf(hierarchy, sub):
            return sub
    return None


# ---------------------------------------------------------------------------
# 2. Subtree narrowing
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_subtree_narrowing(
    hierarchy: SUMOHierarchy, canon: PredicateCanon,
) -> None:
    """Entity with coarse 'Organization' and role constraint 'MilitaryOrganization' should narrow."""
    # Use a triple where entity_a has type Organization.
    triple = _triple(
        "abandon",
        entity_a_name="NATO",
        entity_a_type="Organization",
        entity_b_name="the base",
        entity_b_type="Object",
    )
    # Map ARG0 to NATO (constraint is AutonomousAgent on abandon_leave_behind).
    # For a tighter test, look up a predicate that constrains to MilitaryOrganization.
    # Since abandon_leave_behind constrains ARG0 to AutonomousAgent, the
    # narrowing will intersect Organization descendants with AutonomousAgent
    # descendants.
    assertion = _mapped_assertion(triple)
    p2 = _pass2_result([assertion])

    llm_response = json.dumps({"refined_type": "MilitaryOrganization"})
    api = _make_fake_api(llm_response, llm_cost=0.002)

    result = await run_pass3(
        p2,
        sumo_hierarchy=hierarchy,
        predicate_canon=canon,
        trace_id="test/pass3/subtree",
        _llm_api=api,
    )

    assert len(result.typed_assertions) == 1
    refinements = result.typed_assertions[0].entity_refinements
    org_refs = [r for r in refinements if r.entity_name == "NATO"]
    assert len(org_refs) == 1
    ref = org_refs[0]
    assert ref.coarse_type == "Organization"
    # The refinement may be subtree_pick or no_constraint depending on
    # whether AutonomousAgent intersects with Organization descendants.
    assert ref.refinement_method in ("subtree_pick", "no_constraint")
    assert ref.candidate_count > 1


# ---------------------------------------------------------------------------
# 3. No constraint
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_no_constraint_path(
    hierarchy: SUMOHierarchy, canon: PredicateCanon,
) -> None:
    """Role with type_constraint 'Entity' should use full coarse-type subtree."""
    # abandon_leave_behind has ARG1 constrained to 'Entity' (trivial).
    triple = _triple(
        "abandon",
        entity_a_name="CIA",
        entity_a_type="Organization",
        entity_b_name="the plan",
        entity_b_type="Process",
        evidence="The CIA abandoned the plan.",
    )
    assertion = _mapped_assertion(triple)
    p2 = _pass2_result([assertion])

    # The LLM should be called for ARG1 (entity_b = "the plan", type Process,
    # constraint Entity -> no_constraint path).
    llm_response = json.dumps({"refined_type": "Process"})
    api = _make_fake_api(llm_response, llm_cost=0.001)

    result = await run_pass3(
        p2,
        sumo_hierarchy=hierarchy,
        predicate_canon=canon,
        trace_id="test/pass3/no_constraint",
        _llm_api=api,
    )

    refinements = result.typed_assertions[0].entity_refinements
    plan_refs = [r for r in refinements if r.entity_name == "the plan"]
    assert len(plan_refs) == 1
    ref = plan_refs[0]
    assert ref.role_constraint == "Entity"
    assert ref.refinement_method == "no_constraint"


# ---------------------------------------------------------------------------
# 4. LLM picks refined type
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_llm_picks_valid_refined_type(
    hierarchy: SUMOHierarchy, canon: PredicateCanon,
) -> None:
    """Mock LLM returns a valid type from the narrowed list -> EntityRefinement created."""
    triple = _triple(
        "abandon",
        entity_a_name="special forces",
        entity_a_type="Organization",
        entity_b_name="the hostages",
        entity_b_type="Human",
    )
    assertion = _mapped_assertion(triple)
    p2 = _pass2_result([assertion])

    # Human descendants should include HumanAdult, Man, Woman etc.
    # Find a real descendant of Human.
    human_subtypes = hierarchy.subtypes("Human")
    if human_subtypes:
        target_type = human_subtypes[0]
    else:
        target_type = "Human"

    llm_response = json.dumps({"refined_type": target_type})
    api = _make_fake_api(llm_response, llm_cost=0.002)

    result = await run_pass3(
        p2,
        sumo_hierarchy=hierarchy,
        predicate_canon=canon,
        trace_id="test/pass3/llm_pick",
        _llm_api=api,
    )

    refinements = result.typed_assertions[0].entity_refinements
    hostage_refs = [r for r in refinements if r.entity_name == "the hostages"]
    assert len(hostage_refs) == 1
    ref = hostage_refs[0]
    assert ref.refined_type == target_type
    assert ref.candidate_count > 0


# ---------------------------------------------------------------------------
# 5. LLM picks invalid type -> fallback to coarse_type
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_llm_picks_invalid_type_falls_back(
    hierarchy: SUMOHierarchy, canon: PredicateCanon,
) -> None:
    """LLM returns a type not in the candidate list -> falls back to coarse_type."""
    triple = _triple(
        "abandon",
        entity_a_name="Army",
        entity_a_type="Organization",
        entity_b_name="the mission",
        entity_b_type="Process",
    )
    assertion = _mapped_assertion(triple)
    p2 = _pass2_result([assertion])

    # Return a type that will definitely not be in the Process subtree.
    llm_response = json.dumps({"refined_type": "ZZZTotallyFakeType"})
    api = _make_fake_api(llm_response, llm_cost=0.001)

    result = await run_pass3(
        p2,
        sumo_hierarchy=hierarchy,
        predicate_canon=canon,
        trace_id="test/pass3/invalid",
        _llm_api=api,
    )

    refinements = result.typed_assertions[0].entity_refinements
    mission_refs = [r for r in refinements if r.entity_name == "the mission"]
    assert len(mission_refs) == 1
    ref = mission_refs[0]
    # Should fall back to coarse_type since the LLM picked an invalid type.
    assert ref.refined_type == "Process"


# ---------------------------------------------------------------------------
# 6. Entity deduplication
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_entity_deduplication(
    hierarchy: SUMOHierarchy, canon: PredicateCanon,
) -> None:
    """Same entity in two assertions -> only one LLM refinement call."""
    triple1 = _triple(
        "abandon",
        entity_a_name="CIA",
        entity_a_type="Organization",
        entity_b_name="the plan",
        entity_b_type="Process",
    )
    triple2 = _triple(
        "abandon",
        entity_a_name="CIA",
        entity_a_type="Organization",
        entity_b_name="the project",
        entity_b_type="Process",
    )
    assertion1 = _mapped_assertion(triple1)
    assertion2 = _mapped_assertion(triple2)
    p2 = _pass2_result([assertion1, assertion2])

    call_count = 0
    original_return = _make_llm_result(
        json.dumps({"refined_type": "Organization"}), cost=0.001,
    )

    async def counting_acall(*args: Any, **kwargs: Any) -> SimpleNamespace:
        nonlocal call_count
        call_count += 1
        return original_return

    api = _LLMClientAPI(
        render_prompt=lambda template_path, **ctx: [
            {"role": "system", "content": "s"},
            {"role": "user", "content": "u"},
        ],
        acall_llm=counting_acall,  # type: ignore[arg-type]
    )

    result = await run_pass3(
        p2,
        sumo_hierarchy=hierarchy,
        predicate_canon=canon,
        trace_id="test/pass3/dedup",
        _llm_api=api,
    )

    # Both assertions reference "CIA" with coarse_type "Organization".
    # It should be refined only once.
    assert len(result.typed_assertions) == 2
    cia_refs_1 = [
        r for r in result.typed_assertions[0].entity_refinements
        if r.entity_name == "CIA"
    ]
    cia_refs_2 = [
        r for r in result.typed_assertions[1].entity_refinements
        if r.entity_name == "CIA"
    ]
    assert len(cia_refs_1) == 1
    assert len(cia_refs_2) == 1
    # Same refinement result.
    assert cia_refs_1[0].refined_type == cia_refs_2[0].refined_type

    # Count how many LLM calls were made for "CIA" with "Organization".
    # There are 4 unique (entity, coarse_type) pairs across both assertions:
    # (CIA, Organization), (the plan, Process), (the project, Process).
    # But "CIA" should be deduplicated, so at most 3 unique refinements.
    # However, leaf types may skip LLM calls. The key assertion is that
    # the total call count is less than 4 (the non-deduplicated count).
    # At minimum, CIA is called once not twice.
    assert call_count < 4, (
        f"Expected deduplication to reduce LLM calls, got {call_count}"
    )


# ---------------------------------------------------------------------------
# 7. Multiple assertions
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_multiple_assertions(
    hierarchy: SUMOHierarchy, canon: PredicateCanon,
) -> None:
    """Pass2Result with multiple assertions -> all processed."""
    triple1 = _triple(
        "abandon",
        entity_a_name="CIA",
        entity_a_type="Organization",
        entity_b_name="agents",
        entity_b_type="Human",
    )
    triple2 = _triple(
        "abandon",
        entity_a_name="NATO",
        entity_a_type="Organization",
        entity_b_name="the base",
        entity_b_type="StationaryArtifact",
    )
    assertion1 = _mapped_assertion(triple1)
    assertion2 = _mapped_assertion(triple2)
    p2 = _pass2_result([assertion1, assertion2])

    llm_response = json.dumps({"refined_type": "Organization"})
    api = _make_fake_api(llm_response, llm_cost=0.001)

    result = await run_pass3(
        p2,
        sumo_hierarchy=hierarchy,
        predicate_canon=canon,
        trace_id="test/pass3/multiple",
        _llm_api=api,
    )

    assert len(result.typed_assertions) == 2
    # Each assertion should have refinements for its entities.
    for ta in result.typed_assertions:
        assert len(ta.entity_refinements) > 0


# ---------------------------------------------------------------------------
# 8. Empty pass2
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_empty_pass2(
    hierarchy: SUMOHierarchy, canon: PredicateCanon,
) -> None:
    """No mapped assertions -> empty Pass3Result."""
    p2 = _pass2_result([])

    api = _make_fake_api()
    result = await run_pass3(
        p2,
        sumo_hierarchy=hierarchy,
        predicate_canon=canon,
        trace_id="test/pass3/empty",
        _llm_api=api,
    )

    assert isinstance(result, Pass3Result)
    assert result.typed_assertions == []
    assert result.leaf_early_exit_count == 0
    assert result.subtree_pick_count == 0
    assert result.no_constraint_count == 0
    assert result.cost == 0.0
    api.acall_llm.assert_not_called()  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# 9. Cost tracking
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_cost_tracking(
    hierarchy: SUMOHierarchy, canon: PredicateCanon,
) -> None:
    """Only subtree_pick and no_constraint entities that call LLM incur cost; leaf exits are free."""
    # Use a leaf entity type and a non-leaf entity type.
    leaf_type = _find_leaf_type(hierarchy)
    assert leaf_type is not None

    triple = _triple(
        "abandon",
        entity_a_name="Delta Force",
        entity_a_type=leaf_type,  # leaf -> no cost
        entity_b_name="the hostages",
        entity_b_type="Human",  # non-leaf -> LLM call
    )
    assertion = _mapped_assertion(triple)
    p2 = _pass2_result([assertion])

    llm_response = json.dumps({"refined_type": "Human"})
    api = _make_fake_api(llm_response, llm_cost=0.005)

    result = await run_pass3(
        p2,
        sumo_hierarchy=hierarchy,
        predicate_canon=canon,
        trace_id="test/pass3/cost",
        _llm_api=api,
    )

    # The leaf entity should be free. The non-leaf entity costs 0.005.
    # Total cost should be the sum of LLM calls only.
    assert result.cost > 0.0
    assert result.leaf_early_exit_count >= 1


# ---------------------------------------------------------------------------
# 10. Provenance
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_provenance_references_input(
    hierarchy: SUMOHierarchy, canon: PredicateCanon,
) -> None:
    """source_pass2 should reference the exact input Pass2Result."""
    triple = _triple("abandon")
    assertion = _mapped_assertion(triple)
    p2 = _pass2_result([assertion])

    llm_response = json.dumps({"refined_type": "Organization"})
    api = _make_fake_api(llm_response)

    result = await run_pass3(
        p2,
        sumo_hierarchy=hierarchy,
        predicate_canon=canon,
        trace_id="test/pass3/provenance",
        _llm_api=api,
    )

    assert result.source_pass2 is p2
    assert result.trace_id == "test/pass3/provenance"
    assert result.model == "gemini/gemini-2.5-flash-lite"


# ---------------------------------------------------------------------------
# Unit tests for helpers
# ---------------------------------------------------------------------------


def test_is_leaf_known_leaf(hierarchy: SUMOHierarchy) -> None:
    """A known leaf type should return True."""
    leaf = _find_leaf_type(hierarchy)
    assert leaf is not None
    assert _is_leaf(hierarchy, leaf) is True


def test_is_leaf_known_branch(hierarchy: SUMOHierarchy) -> None:
    """A known branch type (Organization) should return False."""
    assert _is_leaf(hierarchy, "Organization") is False


def test_is_leaf_nonexistent(hierarchy: SUMOHierarchy) -> None:
    """A nonexistent type is treated as a leaf (no subtree to explore)."""
    assert _is_leaf(hierarchy, "ZZZTotallyFakeType") is True


def test_narrow_candidates_with_constraint(hierarchy: SUMOHierarchy) -> None:
    """Narrowing Organization by AutonomousAgent should produce a non-empty intersection."""
    candidates, method = _narrow_candidates(
        hierarchy, "Organization", "AutonomousAgent",
    )
    assert len(candidates) > 0
    assert method == "subtree_pick"


def test_narrow_candidates_trivial_constraint(hierarchy: SUMOHierarchy) -> None:
    """Constraint 'Entity' should use the full coarse-type subtree."""
    candidates, method = _narrow_candidates(hierarchy, "Organization", "Entity")
    assert method == "no_constraint"
    assert len(candidates) > 1


def test_narrow_candidates_none_constraint(hierarchy: SUMOHierarchy) -> None:
    """None constraint should use the full coarse-type subtree."""
    candidates, method = _narrow_candidates(hierarchy, "Organization", None)
    assert method == "no_constraint"
    assert len(candidates) > 1


def test_parse_refinement_response_valid() -> None:
    """Valid JSON with a type in the candidate set should return that type."""
    valid_types = {"Human", "HumanAdult", "Man", "Woman"}
    raw = json.dumps({"refined_type": "HumanAdult"})
    assert _parse_refinement_response(raw, valid_types, "Human") == "HumanAdult"


def test_parse_refinement_response_invalid_type() -> None:
    """A type not in the candidate set should fall back to coarse_type."""
    valid_types = {"Human", "HumanAdult"}
    raw = json.dumps({"refined_type": "MilitaryOrganization"})
    assert _parse_refinement_response(raw, valid_types, "Human") == "Human"


def test_parse_refinement_response_garbage() -> None:
    """Garbage input should fall back to coarse_type."""
    assert _parse_refinement_response("not json", {"Human"}, "Human") == "Human"


def test_parse_refinement_response_markdown_fences() -> None:
    """JSON wrapped in markdown fences should still parse."""
    valid_types = {"Human", "HumanAdult"}
    raw = '```json\n{"refined_type": "HumanAdult"}\n```'
    assert _parse_refinement_response(raw, valid_types, "Human") == "HumanAdult"


def test_parse_refinement_response_missing_field() -> None:
    """JSON missing 'refined_type' should fall back to coarse_type."""
    raw = json.dumps({"wrong_field": "HumanAdult"})
    assert _parse_refinement_response(raw, {"HumanAdult"}, "Human") == "Human"

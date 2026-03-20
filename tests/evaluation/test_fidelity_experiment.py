"""Tests for the fidelity experiment infrastructure.

These tests require v1's ``sumo_plus.db`` to be present at the configured
path. They are skipped if the database is unavailable.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))

from onto_canon6.evaluation.fidelity_experiment import (
    TOP_LEVEL_TYPES,
    EntityFixture,
    ExperimentItem,
    ExperimentResult,
    FidelityLevel,
    PreparedExperiment,
    build_prompt_variables,
    default_entity_fixtures,
    generate_type_list,
    prepare_experiment,
    prepare_experiment_from_config,
)
from onto_canon6.evaluation.sumo_hierarchy import SUMOHierarchy

SUMO_DB = Path(__file__).resolve().parents[3] / "onto-canon" / "data" / "sumo_plus.db"
SKIP_REASON = "sumo_plus.db not available"


@pytest.fixture()
def hierarchy() -> SUMOHierarchy:
    """Provide a SUMOHierarchy instance, skipping if DB is absent."""
    if not SUMO_DB.exists():
        pytest.skip(SKIP_REASON)
    return SUMOHierarchy(SUMO_DB)


# ---------------------------------------------------------------------------
# Entity fixture tests
# ---------------------------------------------------------------------------


def test_default_entity_fixtures_not_empty() -> None:
    """Default entity fixtures should contain a non-trivial entity set."""
    fixtures = default_entity_fixtures()
    assert len(fixtures) >= 5
    names = [e.entity_name for e in fixtures]
    # Required entities from the plan.
    assert "CIA" in names
    assert "Kratos Defense" in names
    assert "V-BAT" in names
    assert "USSOCOM" in names
    assert "Brian" in names


def test_entity_fixture_validation() -> None:
    """EntityFixture validates required fields."""
    entity = EntityFixture(
        entity_name="Test",
        reference_type="Human",
        constraint_type="CognitiveAgent",
    )
    assert entity.entity_name == "Test"
    assert entity.entity_context == ""


def test_entity_fixture_rejects_empty_name() -> None:
    """EntityFixture rejects empty entity_name."""
    with pytest.raises(Exception):
        EntityFixture(
            entity_name="",
            reference_type="Human",
            constraint_type="CognitiveAgent",
        )


# ---------------------------------------------------------------------------
# Type list generation tests
# ---------------------------------------------------------------------------


def test_top_level_type_list_is_stable() -> None:
    """The static TOP_LEVEL_TYPES constant should contain ~50 types."""
    assert len(TOP_LEVEL_TYPES) >= 40
    assert len(TOP_LEVEL_TYPES) <= 60
    # Key types from the plan must be present.
    assert "Entity" in TOP_LEVEL_TYPES
    assert "Organization" in TOP_LEVEL_TYPES
    assert "Human" in TOP_LEVEL_TYPES
    assert "Aircraft" in TOP_LEVEL_TYPES
    assert "Weapon" in TOP_LEVEL_TYPES
    assert "CognitiveAgent" in TOP_LEVEL_TYPES


def test_generate_type_list_top_level(hierarchy: SUMOHierarchy) -> None:
    """Top-level type list uses the stable constant, filtered by DB existence."""
    result = generate_type_list(hierarchy, FidelityLevel.TOP_LEVEL, "Organization")
    # Should be a subset of TOP_LEVEL_TYPES (only existing types kept).
    assert len(result) > 30  # Most should exist.
    assert all(hierarchy.type_exists(t) for t in result)
    # Should be sorted.
    assert list(result) == sorted(result)
    # Constraint type is ignored for top-level.
    result2 = generate_type_list(hierarchy, FidelityLevel.TOP_LEVEL, "Aircraft")
    assert result == result2


def test_generate_type_list_mid_level(hierarchy: SUMOHierarchy) -> None:
    """Mid-level type list includes subtypes within max_depth of the constraint."""
    result = generate_type_list(hierarchy, FidelityLevel.MID_LEVEL, "Organization")
    assert len(result) >= 10
    assert "Organization" in result  # Constraint type itself included.
    assert "GovernmentOrganization" in result
    # Should be sorted.
    assert list(result) == sorted(result)


def test_generate_type_list_full_subtree(hierarchy: SUMOHierarchy) -> None:
    """Full-subtree type list includes all descendants of the constraint type."""
    mid = generate_type_list(hierarchy, FidelityLevel.MID_LEVEL, "Organization")
    full = generate_type_list(hierarchy, FidelityLevel.FULL_SUBTREE, "Organization")
    # Full subtree should be at least as large as mid-level.
    assert len(full) >= len(mid)
    # All mid-level types should appear in the full subtree.
    assert set(mid).issubset(set(full))


def test_generate_type_list_mid_level_military(hierarchy: SUMOHierarchy) -> None:
    """Mid-level for MilitaryOrganization should contain military subtypes."""
    result = generate_type_list(hierarchy, FidelityLevel.MID_LEVEL, "MilitaryOrganization")
    assert "MilitaryOrganization" in result
    assert "MilitaryUnit" in result
    assert len(result) >= 10


def test_generate_type_list_nonexistent_constraint(hierarchy: SUMOHierarchy) -> None:
    """Non-existent constraint type raises ValueError for non-top-level."""
    with pytest.raises(ValueError, match="not found"):
        generate_type_list(hierarchy, FidelityLevel.MID_LEVEL, "FakeType999")

    # But top-level ignores the constraint type entirely.
    result = generate_type_list(hierarchy, FidelityLevel.TOP_LEVEL, "FakeType999")
    assert len(result) > 0


# ---------------------------------------------------------------------------
# Prompt construction tests
# ---------------------------------------------------------------------------


def test_build_prompt_variables() -> None:
    """Prompt variables should contain entity name, context, and formatted type list."""
    entity = EntityFixture(
        entity_name="CIA",
        entity_context="US intelligence agency",
        reference_type="GovernmentOrganization",
        constraint_type="Organization",
    )
    type_list = ("GovernmentOrganization", "MilitaryOrganization", "Organization")
    result = build_prompt_variables(entity, type_list)
    assert result["entity_name"] == "CIA"
    assert result["entity_context"] == "US intelligence agency"
    assert "- GovernmentOrganization" in result["type_list"]
    assert "- MilitaryOrganization" in result["type_list"]
    assert "- Organization" in result["type_list"]


def test_build_prompt_variables_empty_context() -> None:
    """Prompt variables with no context should have empty string."""
    entity = EntityFixture(
        entity_name="Test",
        reference_type="Human",
        constraint_type="CognitiveAgent",
    )
    result = build_prompt_variables(entity, ("Human", "CognitiveAgent"))
    assert result["entity_context"] == ""


# ---------------------------------------------------------------------------
# Data model validation tests
# ---------------------------------------------------------------------------


def test_experiment_result_validates() -> None:
    """ExperimentResult should validate and store all required fields."""
    result = ExperimentResult(
        entity_name="CIA",
        fidelity_level=FidelityLevel.TOP_LEVEL,
        pick="GovernmentOrganization",
        reference_type="GovernmentOrganization",
        ancestor_eval_score=1.0,
        exact_match=True,
        ancestor_match=True,
        specificity=1.0,
    )
    assert result.entity_name == "CIA"
    assert result.fidelity_level == FidelityLevel.TOP_LEVEL
    assert result.exact_match is True


def test_experiment_result_rejects_invalid_score() -> None:
    """ExperimentResult rejects scores outside [0, 1]."""
    with pytest.raises(Exception):
        ExperimentResult(
            entity_name="CIA",
            fidelity_level=FidelityLevel.TOP_LEVEL,
            pick="Organization",
            reference_type="GovernmentOrganization",
            ancestor_eval_score=1.5,
            exact_match=False,
            ancestor_match=True,
            specificity=0.5,
        )


def test_experiment_item_serializes_to_json() -> None:
    """ExperimentItem should be JSON-serializable via Pydantic."""
    item = ExperimentItem(
        entity_name="Brian",
        reference_type="Human",
        fidelity_level=FidelityLevel.MID_LEVEL,
        type_list=("Human", "CognitiveAgent"),
        prompt_variables={"entity_name": "Brian", "entity_context": "", "type_list": "- Human\n- CognitiveAgent"},
    )
    data = json.loads(item.model_dump_json())
    assert data["entity_name"] == "Brian"
    assert data["fidelity_level"] == "mid_level"
    assert len(data["type_list"]) == 2


# ---------------------------------------------------------------------------
# Full experiment preparation tests
# ---------------------------------------------------------------------------


def test_prepare_experiment_all_levels(hierarchy: SUMOHierarchy) -> None:
    """Prepare experiment with all three fidelity levels produces correct item count."""
    entities = default_entity_fixtures()
    levels = [FidelityLevel.TOP_LEVEL, FidelityLevel.MID_LEVEL, FidelityLevel.FULL_SUBTREE]
    result = prepare_experiment(hierarchy, entities, levels)
    assert result.entity_count == len(entities)
    assert len(result.fidelity_levels) == 3
    assert len(result.items) == len(entities) * 3


def test_prepare_experiment_single_level(hierarchy: SUMOHierarchy) -> None:
    """Prepare experiment with a single level works correctly."""
    entities = [
        EntityFixture(
            entity_name="CIA",
            entity_context="US intelligence agency",
            reference_type="GovernmentOrganization",
            constraint_type="Organization",
        ),
    ]
    result = prepare_experiment(hierarchy, entities, [FidelityLevel.TOP_LEVEL])
    assert result.entity_count == 1
    assert len(result.items) == 1
    item = result.items[0]
    assert item.entity_name == "CIA"
    assert item.fidelity_level == FidelityLevel.TOP_LEVEL
    assert len(item.type_list) > 30  # Top-level has ~50 types.
    assert "entity_name" in item.prompt_variables


def test_prepare_experiment_empty_entities_raises(hierarchy: SUMOHierarchy) -> None:
    """Empty entities should raise ValueError."""
    with pytest.raises(ValueError, match="entities must not be empty"):
        prepare_experiment(hierarchy, [], [FidelityLevel.TOP_LEVEL])


def test_prepare_experiment_empty_levels_raises(hierarchy: SUMOHierarchy) -> None:
    """Empty levels should raise ValueError."""
    entities = list(default_entity_fixtures())
    with pytest.raises(ValueError, match="levels must not be empty"):
        prepare_experiment(hierarchy, entities, [])


def test_prepare_experiment_type_list_varies_by_level(hierarchy: SUMOHierarchy) -> None:
    """Type lists should differ between fidelity levels for the same entity."""
    entities = [
        EntityFixture(
            entity_name="USSOCOM",
            entity_context="United States Special Operations Command",
            reference_type="MilitaryUnit",
            constraint_type="MilitaryOrganization",
        ),
    ]
    levels = [FidelityLevel.TOP_LEVEL, FidelityLevel.MID_LEVEL, FidelityLevel.FULL_SUBTREE]
    result = prepare_experiment(hierarchy, entities, levels)
    type_lists = [set(item.type_list) for item in result.items]
    # Each level should have a different type set.
    assert type_lists[0] != type_lists[1]
    # Full subtree should be superset of mid-level.
    assert type_lists[1].issubset(type_lists[2])


def test_prepare_experiment_serializes_to_json(hierarchy: SUMOHierarchy) -> None:
    """PreparedExperiment should be fully JSON-serializable."""
    entities = list(default_entity_fixtures())[:2]
    result = prepare_experiment(hierarchy, entities, [FidelityLevel.TOP_LEVEL])
    data = json.loads(result.model_dump_json())
    assert data["entity_count"] == 2
    assert len(data["items"]) == 2
    assert data["prompt_template"] == "prompts/evaluation/fidelity_type_assignment.yaml"


def test_prepare_experiment_from_config_defaults() -> None:
    """Convenience wrapper with defaults should produce a valid experiment."""
    if not SUMO_DB.exists():
        pytest.skip(SKIP_REASON)
    result = prepare_experiment_from_config(SUMO_DB)
    assert result.entity_count >= 5
    assert len(result.fidelity_levels) == 3
    assert len(result.items) == result.entity_count * 3


def test_prepare_experiment_from_config_single_level() -> None:
    """Convenience wrapper with a single level works."""
    if not SUMO_DB.exists():
        pytest.skip(SKIP_REASON)
    result = prepare_experiment_from_config(
        SUMO_DB,
        levels=[FidelityLevel.MID_LEVEL],
    )
    assert len(result.fidelity_levels) == 1
    assert all(item.fidelity_level == FidelityLevel.MID_LEVEL for item in result.items)


def test_reference_types_exist_in_hierarchy(hierarchy: SUMOHierarchy) -> None:
    """All reference types in the default fixtures should exist in the SUMO DB."""
    for entity in default_entity_fixtures():
        assert hierarchy.type_exists(entity.reference_type), (
            f"Reference type {entity.reference_type!r} for {entity.entity_name!r} not in SUMO DB"
        )


def test_constraint_types_exist_in_hierarchy(hierarchy: SUMOHierarchy) -> None:
    """All constraint types in the default fixtures should exist in the SUMO DB."""
    for entity in default_entity_fixtures():
        assert hierarchy.type_exists(entity.constraint_type), (
            f"Constraint type {entity.constraint_type!r} for {entity.entity_name!r} not in SUMO DB"
        )


def test_reference_type_is_under_constraint(hierarchy: SUMOHierarchy) -> None:
    """Reference types should be descendants of their constraint types."""
    for entity in default_entity_fixtures():
        assert hierarchy.is_descendant_or_equal(entity.reference_type, entity.constraint_type), (
            f"{entity.reference_type!r} is not under {entity.constraint_type!r} "
            f"for entity {entity.entity_name!r}"
        )

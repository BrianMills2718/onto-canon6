"""Tests for the SUMO hierarchy read-only interface.

These tests require the repo-local ``sumo_plus.db`` to be present at the
configured path. They are skipped if the database is unavailable.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))

from onto_canon6.evaluation.sumo_hierarchy import SUMOHierarchy, SUMOHierarchyError

SUMO_DB = PROJECT_ROOT / "data" / "sumo_plus.db"
SKIP_REASON = "sumo_plus.db not available"


@pytest.fixture()
def hierarchy() -> SUMOHierarchy:
    """Provide a SUMOHierarchy instance, skipping if DB is absent."""
    if not SUMO_DB.exists():
        pytest.skip(SKIP_REASON)
    return SUMOHierarchy(SUMO_DB)


def test_missing_db_raises() -> None:
    """SUMOHierarchy raises on a nonexistent database path."""
    with pytest.raises(SUMOHierarchyError, match="not found"):
        SUMOHierarchy(Path("/nonexistent/sumo_plus.db"))


def test_type_exists(hierarchy: SUMOHierarchy) -> None:
    """Known SUMO types should be found."""
    assert hierarchy.type_exists("Entity")
    assert hierarchy.type_exists("CognitiveAgent")
    assert hierarchy.type_exists("MilitaryOrganization")
    assert not hierarchy.type_exists("NonexistentTypeFoo")


def test_is_ancestor_or_equal_exact(hierarchy: SUMOHierarchy) -> None:
    """A type is an ancestor-or-equal of itself."""
    assert hierarchy.is_ancestor_or_equal("Entity", "Entity")
    assert hierarchy.is_ancestor_or_equal("CognitiveAgent", "CognitiveAgent")


def test_is_ancestor_or_equal_true(hierarchy: SUMOHierarchy) -> None:
    """Known ancestor relationships should hold."""
    # Organization is an ancestor of MilitaryOrganization.
    assert hierarchy.is_ancestor_or_equal("Organization", "MilitaryOrganization")
    # Entity is an ancestor of everything.
    assert hierarchy.is_ancestor_or_equal("Entity", "MilitaryOrganization")


def test_is_ancestor_or_equal_false(hierarchy: SUMOHierarchy) -> None:
    """Non-ancestor relationships should return False."""
    # MilitaryOrganization is NOT an ancestor of Organization.
    assert not hierarchy.is_ancestor_or_equal("MilitaryOrganization", "Organization")
    # Unrelated types.
    assert not hierarchy.is_ancestor_or_equal("Human", "MilitaryOrganization")


def test_is_descendant_or_equal(hierarchy: SUMOHierarchy) -> None:
    """Descendant check is the inverse of ancestor check."""
    assert hierarchy.is_descendant_or_equal("MilitaryOrganization", "Organization")
    assert not hierarchy.is_descendant_or_equal("Organization", "MilitaryOrganization")


def test_depth_root_types(hierarchy: SUMOHierarchy) -> None:
    """Root types should have depth 0 or very low depth."""
    entity_depth = hierarchy.depth("Entity")
    assert entity_depth >= 0


def test_depth_deep_types(hierarchy: SUMOHierarchy) -> None:
    """Deeply nested types should have higher depth than root types."""
    entity_depth = hierarchy.depth("Entity")
    human_depth = hierarchy.depth("Human")
    # Entity is a root (depth 0), Human is deeply nested (depth ~10).
    assert human_depth > entity_depth


def test_depth_nonexistent(hierarchy: SUMOHierarchy) -> None:
    """Nonexistent types return depth -1."""
    assert hierarchy.depth("NonexistentTypeFoo") == -1


def test_ancestors(hierarchy: SUMOHierarchy) -> None:
    """Ancestors list should contain known ancestors."""
    ancestors = hierarchy.ancestors("MilitaryOrganization")
    assert len(ancestors) > 0
    # Organization should be in the ancestors list.
    assert "Organization" in ancestors


def test_subtypes(hierarchy: SUMOHierarchy) -> None:
    """Subtypes should include known descendants."""
    subtypes = hierarchy.subtypes("Organization")
    assert len(subtypes) > 0
    assert "MilitaryOrganization" in subtypes


def test_subtypes_max_depth(hierarchy: SUMOHierarchy) -> None:
    """max_depth limits how deep we go."""
    all_subtypes = hierarchy.subtypes("Organization")
    shallow = hierarchy.subtypes("Organization", max_depth=1)
    assert len(shallow) <= len(all_subtypes)
    assert len(shallow) > 0


def test_type_count(hierarchy: SUMOHierarchy) -> None:
    """Type count should match the known range for the canonical local DB."""
    count = hierarchy.type_count()
    # v1 docs say ~7,894 types.
    assert count > 7000
    assert count < 10000

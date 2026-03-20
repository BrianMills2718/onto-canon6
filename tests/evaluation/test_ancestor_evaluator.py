"""Tests for the ancestor-aware evaluator.

These tests require v1's ``sumo_plus.db`` to be present at the configured
path. They are skipped if the database is unavailable.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))

from onto_canon6.evaluation.ancestor_evaluator import AncestorEvalScore, make_ancestor_evaluator

SUMO_DB = Path(__file__).resolve().parents[3] / "onto-canon" / "data" / "sumo_plus.db"
SKIP_REASON = "sumo_plus.db not available"


@pytest.fixture()
def evaluator():  # noqa: ANN201
    """Build an ancestor evaluator, skipping if DB is absent."""
    if not SUMO_DB.exists():
        pytest.skip(SKIP_REASON)
    return make_ancestor_evaluator(SUMO_DB)


def test_exact_match(evaluator) -> None:  # noqa: ANN001
    """Exact match should score 1.0 on all dimensions."""
    result = evaluator("MilitaryOrganization", "MilitaryOrganization")
    assert isinstance(result, AncestorEvalScore)
    assert result.score == 1.0
    assert result.exact == 1.0
    assert result.ancestor_match == 1.0
    assert result.specificity == 1.0


def test_ancestor_match(evaluator) -> None:  # noqa: ANN001
    """Ancestor match should score > 0 but < 1.0, with specificity < 1.0."""
    # Entity (depth 0) is an ancestor of Human (depth ~10).
    result = evaluator("Entity", "Human")
    assert result.score > 0.0
    assert result.score < 1.0
    assert result.exact == 0.0
    assert result.ancestor_match == 1.0
    assert result.specificity >= 0.0
    assert result.specificity < 1.0


def test_coarser_ancestor_scores_lower(evaluator) -> None:  # noqa: ANN001
    """A more distant ancestor should score lower than a closer one."""
    # CognitiveAgent (depth 5) is closer to Human (depth 10) than Entity (depth 0).
    close = evaluator("CognitiveAgent", "Human")
    far = evaluator("Entity", "Human")
    assert close.score > far.score
    assert close.specificity > far.specificity


def test_descendant_match(evaluator) -> None:  # noqa: ANN001
    """More-specific pick (descendant) should score well."""
    # MilitaryOrganization is more specific than Organization.
    result = evaluator("MilitaryOrganization", "Organization")
    assert result.score > 0.0
    assert result.ancestor_match == 1.0  # Still in the right branch.


def test_wrong_branch(evaluator) -> None:  # noqa: ANN001
    """Unrelated types should score 0.0."""
    result = evaluator("Human", "MilitaryOrganization")
    assert result.score == 0.0
    assert result.exact == 0.0
    assert result.ancestor_match == 0.0
    assert result.specificity == 0.0


def test_nonexistent_pick(evaluator) -> None:  # noqa: ANN001
    """A pick that doesn't exist in SUMO should score 0.0."""
    result = evaluator("FakeTypeFoo", "MilitaryOrganization")
    assert result.score == 0.0
    assert not result.pick_exists
    assert result.reference_exists


def test_nonexistent_reference(evaluator) -> None:  # noqa: ANN001
    """A reference that doesn't exist in SUMO should score 0.0."""
    result = evaluator("MilitaryOrganization", "FakeTypeFoo")
    assert result.score == 0.0
    assert result.pick_exists
    assert not result.reference_exists


def test_no_expected(evaluator) -> None:  # noqa: ANN001
    """Calling with None expected returns score 0.0."""
    result = evaluator("MilitaryOrganization", None)
    assert result.score == 0.0
    assert result.reference == ""


def test_entity_root_is_coarse(evaluator) -> None:  # noqa: ANN001
    """Entity as a pick for a deep type should score low specificity."""
    result = evaluator("Entity", "Human")
    assert result.ancestor_match == 1.0
    assert result.specificity < 0.1  # Entity (depth 0) vs Human (depth 10).


def test_custom_base_score() -> None:
    """Custom ancestor_base_score should affect scoring."""
    if not SUMO_DB.exists():
        pytest.skip(SKIP_REASON)
    eval_low = make_ancestor_evaluator(SUMO_DB, ancestor_base_score=0.5)
    eval_high = make_ancestor_evaluator(SUMO_DB, ancestor_base_score=0.9)
    low_result = eval_low("Organization", "MilitaryOrganization")
    high_result = eval_high("Organization", "MilitaryOrganization")
    assert high_result.score > low_result.score

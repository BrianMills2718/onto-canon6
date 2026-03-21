"""Tests for the Predicate Canon read-only interface.

These tests require v1's ``sumo_plus.db`` to be present at the configured
path.  They are skipped if the database is unavailable.  All assertions are
deterministic against the real database contents.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))

from onto_canon6.evaluation.predicate_canon import (
    PredicateCanon,
    PredicateCanonError,
    PredicateInfo,
    PredicateMatch,
    RoleSlotInfo,
)

SUMO_DB = Path(__file__).resolve().parents[3] / "onto-canon" / "data" / "sumo_plus.db"
SKIP_REASON = "sumo_plus.db not available"


@pytest.fixture()
def canon() -> PredicateCanon:
    """Provide a PredicateCanon instance, skipping if DB is absent."""
    if not SUMO_DB.exists():
        pytest.skip(SKIP_REASON)
    return PredicateCanon(SUMO_DB)


def test_lookup_by_lemma_abandon(canon: PredicateCanon) -> None:
    """'abandon' should return 3 candidate predicate senses."""
    matches = canon.lookup_by_lemma("abandon")
    assert len(matches) == 3
    ids = [m.predicate_id for m in matches]
    assert "abandon_leave_behind" in ids
    assert "abandon_exchange" in ids
    assert "abandon_surrender_give" in ids
    # Each match should have role slots populated.
    for m in matches:
        assert isinstance(m, PredicateMatch)
        assert len(m.role_slots) > 0


def test_is_single_sense_abate(canon: PredicateCanon) -> None:
    """'abate' maps to exactly one predicate sense."""
    assert canon.is_single_sense("abate") is True


def test_is_single_sense_abandon(canon: PredicateCanon) -> None:
    """'abandon' has 3 senses and is NOT single-sense."""
    assert canon.is_single_sense("abandon") is False


def test_get_role_constraints_abandon_leave_behind(canon: PredicateCanon) -> None:
    """Role constraints for abandon_leave_behind match expected types."""
    constraints = canon.get_role_constraints("abandon_leave_behind")
    assert constraints == {
        "ARG0": "AutonomousAgent",
        "ARG1": "Entity",
        "ARG2": "Object",
    }


def test_get_role_slots_abandon_leave_behind(canon: PredicateCanon) -> None:
    """abandon_leave_behind should have 3 role slots."""
    slots = canon.get_role_slots("abandon_leave_behind")
    assert len(slots) == 3
    for slot in slots:
        assert isinstance(slot, RoleSlotInfo)
    positions = {s.arg_position for s in slots}
    assert positions == {"ARG0", "ARG1", "ARG2"}


def test_get_predicate_exists(canon: PredicateCanon) -> None:
    """get_predicate returns correct PredicateInfo for a known predicate."""
    pred = canon.get_predicate("abandon_leave_behind")
    assert pred is not None
    assert isinstance(pred, PredicateInfo)
    assert pred.predicate_id == "abandon_leave_behind"
    assert pred.propbank_sense_id == "abandon-01"
    assert pred.process_type == "Leaving"
    assert pred.lemma == "abandon"
    assert pred.sense_num == 1
    assert pred.description == "leave behind"
    assert pred.frame_id == "Quitting_a_place"
    assert pred.mapping_confidence == 0.9
    assert pred.is_static is False


def test_get_predicate_nonexistent(canon: PredicateCanon) -> None:
    """get_predicate returns None for an unknown predicate."""
    assert canon.get_predicate("nonexistent_predicate") is None


def test_lookup_by_lemma_nonexistent(canon: PredicateCanon) -> None:
    """lookup_by_lemma returns empty list for an unknown lemma."""
    assert canon.lookup_by_lemma("zzz_nonexistent") == []


def test_lemma_sense_count_abandon(canon: PredicateCanon) -> None:
    """'abandon' has exactly 3 senses."""
    assert canon.lemma_sense_count("abandon") == 3


def test_list_lemmas_for_process_type_leaving(canon: PredicateCanon) -> None:
    """Process type 'Leaving' should include 'abandon'."""
    lemmas = canon.list_lemmas_for_process_type("Leaving")
    assert "abandon" in lemmas
    # Should also include other known Leaving verbs.
    assert len(lemmas) > 1


def test_context_manager_protocol() -> None:
    """PredicateCanon works as a context manager."""
    if not SUMO_DB.exists():
        pytest.skip(SKIP_REASON)
    with PredicateCanon(SUMO_DB) as pc:
        # Should be usable inside the context.
        assert pc.lemma_sense_count("abandon") == 3
    # After exiting, the connection is closed.  Attempting a query should
    # raise (ProgrammingError: Cannot operate on a closed database).


def test_db_not_found_raises() -> None:
    """PredicateCanon raises PredicateCanonError on a nonexistent path."""
    with pytest.raises(PredicateCanonError, match="not found"):
        PredicateCanon(Path("/nonexistent/sumo_plus.db"))


def test_single_sense_rate_sanity(canon: PredicateCanon) -> None:
    """Approximately 78% of lemmas should be single-sense.

    This is a sanity check against the known ~78.1% single-sense rate
    documented in Plan 0018.
    """
    cursor = canon._conn.execute(  # noqa: SLF001
        "SELECT lemma, COUNT(*) AS cnt FROM predicates GROUP BY lemma"
    )
    rows = cursor.fetchall()
    total = len(rows)
    single = sum(1 for r in rows if r["cnt"] == 1)
    rate = single / total
    # Allow +/- 5% tolerance around the expected 78%.
    assert 0.73 < rate < 0.83, f"Single-sense rate {rate:.3f} outside expected range"

"""Tests for the ProbLog fact-store adapter."""

from __future__ import annotations

from pathlib import Path

import pytest

from onto_canon6.extensions.problog_adapter import (
    DerivedFact,
    RuleEvaluationResult,
    _sanitize_atom,
    evaluate_rules,
    load_facts_from_db,
)
from onto_canon6.core import CanonicalGraphService
from onto_canon6.pipeline import ReviewService


def _seed_review_service(tmp_path: Path) -> ReviewService:
    """Create one isolated review service."""
    review_db_path = tmp_path / "review.sqlite3"
    overlay_root = tmp_path / "ontology_overlays"
    return ReviewService(
        db_path=review_db_path,
        overlay_root=overlay_root,
        default_acceptance_policy="record_only",
        permissive_review=True,
    )


def _submit_accept_promote(
    review_service: ReviewService,
    *,
    predicate: str,
    roles: dict,
    source_ref: str = "test_source",
) -> str:
    """Submit, accept, and promote one candidate."""
    submission = review_service.submit_candidate_assertion(
        payload={"predicate": predicate, "roles": roles},
        profile_id="default",
        profile_version="1.0.0",
        submitted_by="test",
        source_kind="text_file",
        source_ref=source_ref,
    )
    candidate_id = submission.candidate.candidate_id
    review_service.review_candidate(
        candidate_id=candidate_id,
        decision="accepted",
        actor_id="test",
    )
    CanonicalGraphService(db_path=review_service.store.db_path).promote_candidate(
        candidate_id=candidate_id,
        promoted_by="test",
    )
    return candidate_id


class TestSanitizeAtom:
    """Test Prolog atom sanitization."""

    def test_lowercase(self) -> None:
        assert _sanitize_atom("USSOCOM") == "ussocom"

    def test_remove_special_chars(self) -> None:
        assert _sanitize_atom("Gen. Holland") == "gen_holland"

    def test_leading_digit(self) -> None:
        assert _sanitize_atom("4th Group") == "e_4th_group"

    def test_empty(self) -> None:
        assert _sanitize_atom("") == "unknown"

    def test_apostrophe(self) -> None:
        assert _sanitize_atom("O'Brien") == "obrien"


class TestLoadFactsFromDb:
    """Test fact loading from onto-canon6 DB."""

    def test_empty_db(self, tmp_path: Path) -> None:
        """Empty DB produces no facts."""
        review_svc = _seed_review_service(tmp_path)
        facts = load_facts_from_db(review_svc.store.db_path)
        assert facts == []

    def test_promoted_assertion_becomes_fact(self, tmp_path: Path) -> None:
        """Promoted assertion with entity fillers becomes a ProbLog fact."""
        review_svc = _seed_review_service(tmp_path)
        _submit_accept_promote(
            review_svc,
            predicate="test:commands",
            roles={
                "commander": [{"kind": "entity", "entity_type": "oc:person", "name": "Alice", "entity_id": "ent_alice"}],
                "organization": [{"kind": "entity", "entity_type": "oc:org", "name": "Acme", "entity_id": "ent_acme"}],
            },
        )
        facts = load_facts_from_db(review_svc.store.db_path)
        assert len(facts) == 1
        assert "alice" in facts[0]
        assert "acme" in facts[0]

    def test_predicate_mapping(self, tmp_path: Path) -> None:
        """Custom predicate mapping renames functors."""
        review_svc = _seed_review_service(tmp_path)
        _submit_accept_promote(
            review_svc,
            predicate="oc:hold_command_role",
            roles={
                "commander": [{"kind": "entity", "entity_type": "oc:person", "name": "Bob", "entity_id": "ent_bob"}],
                "org": [{"kind": "entity", "entity_type": "oc:org", "name": "Corp", "entity_id": "ent_corp"}],
            },
        )
        facts = load_facts_from_db(
            review_svc.store.db_path,
            predicate_mapping={"oc:hold_command_role": "commands"},
        )
        assert len(facts) == 1
        assert facts[0].startswith("1.0::commands(")


class TestEvaluateRules:
    """Test ProbLog rule evaluation."""

    def test_empty_db_returns_error(self, tmp_path: Path) -> None:
        """Empty DB produces error, not crash."""
        review_svc = _seed_review_service(tmp_path)
        result = evaluate_rules(
            db_path=review_svc.store.db_path,
            rules="query(foo(X)).",
        )
        assert result.input_facts == 0
        assert "No facts" in result.errors[0]

    def test_simple_rule_evaluation(self, tmp_path: Path) -> None:
        """Simple rule over 1 fact produces derived facts."""
        review_svc = _seed_review_service(tmp_path)
        _submit_accept_promote(
            review_svc,
            predicate="test:commands",
            roles={
                "commander": [{"kind": "entity", "entity_type": "oc:person", "name": "Alice", "entity_id": "ent_alice"}],
                "organization": [{"kind": "entity", "entity_type": "oc:org", "name": "Acme", "entity_id": "ent_acme"}],
            },
        )
        result = evaluate_rules(
            db_path=review_svc.store.db_path,
            rules="""
            authority(X, O) :- test_commands(X, O).
            query(authority(X, O)).
            """,
        )
        assert result.input_facts == 1
        assert result.rules_applied >= 1
        assert len(result.derived_facts) >= 1
        assert any("alice" in f.term and "acme" in f.term for f in result.derived_facts)

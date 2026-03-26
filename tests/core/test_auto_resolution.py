"""Tests for automated entity resolution."""

from __future__ import annotations

from pathlib import Path

import pytest

from onto_canon6.core.auto_resolution import (
    ResolutionResult,
    auto_resolve_identities,
    _normalize_name,
    _group_by_name,
)
from onto_canon6.core import CanonicalGraphService, IdentityService
from onto_canon6.pipeline import ReviewService


def _seed_review_service(tmp_path: Path) -> ReviewService:
    """Create one isolated review service."""
    review_db_path = tmp_path / "review.sqlite3"
    overlay_root = tmp_path / "ontology_overlays"
    return ReviewService(
        db_path=review_db_path,
        overlay_root=overlay_root,
        default_acceptance_policy="record_only",
    )


def _submit_accept_promote(
    review_service: ReviewService,
    *,
    predicate: str,
    entity_name: str,
    entity_type: str,
    entity_id: str,
    source_ref: str = "test_source",
) -> str:
    """Submit, accept, and promote one candidate."""
    submission = review_service.submit_candidate_assertion(
        payload={
            "predicate": predicate,
            "roles": {
                "ARG0": [
                    {
                        "kind": "entity",
                        "entity_id": entity_id,
                        "entity_type": entity_type,
                        "name": entity_name,
                    }
                ],
            },
        },
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


class TestNormalizeName:
    """Test name normalization for matching."""

    def test_lowercase(self) -> None:
        assert _normalize_name("USSOCOM") == "ussocom"

    def test_collapse_whitespace(self) -> None:
        assert _normalize_name("4th  PSYOP   Group") == "4th psyop group"

    def test_strip(self) -> None:
        assert _normalize_name("  Gen. Holland  ") == "gen. holland"

    def test_empty(self) -> None:
        assert _normalize_name("") == ""


class TestGroupByName:
    """Test entity grouping logic."""

    def test_exact_match_groups(self) -> None:
        entity_ids = ["ent_1", "ent_2", "ent_3"]
        name_map = {"ent_1": "USSOCOM", "ent_2": "ussocom", "ent_3": "Other"}
        groups = _group_by_name(entity_ids, name_map, "exact")
        assert len(groups) == 2
        assert len(groups["ussocom"]) == 2
        assert len(groups["other"]) == 1

    def test_no_name_uses_entity_id(self) -> None:
        entity_ids = ["ent_1"]
        name_map = {}
        groups = _group_by_name(entity_ids, name_map, "exact")
        assert "ent_1" in groups


class TestAutoResolveIdentities:
    """Test the full auto-resolve workflow."""

    def test_empty_graph(self, tmp_path: Path) -> None:
        """Auto-resolve on empty graph produces zero results."""
        review_svc = _seed_review_service(tmp_path)
        result = auto_resolve_identities(db_path=review_svc.store.db_path)
        assert result.entities_scanned == 0
        assert result.groups_found == 0
        assert result.identities_created == 0

    def test_single_entity(self, tmp_path: Path) -> None:
        """Single entity gets its own identity."""
        review_svc = _seed_review_service(tmp_path)
        _submit_accept_promote(
            review_svc,
            predicate="test:pred",
            entity_name="Gen. Holland",
            entity_type="oc:person",
            entity_id="ent_1",
        )
        result = auto_resolve_identities(db_path=review_svc.store.db_path)
        assert result.entities_scanned == 1
        assert result.groups_found == 1
        assert result.identities_created == 1
        assert result.aliases_attached == 0

    def test_two_entities_same_name_merge(self, tmp_path: Path) -> None:
        """Two entities with the same display name get merged."""
        review_svc = _seed_review_service(tmp_path)
        _submit_accept_promote(
            review_svc,
            predicate="test:pred1",
            entity_name="USSOCOM",
            entity_type="oc:org",
            entity_id="ent_chunk1_ussocom",
            source_ref="chunk1",
        )
        _submit_accept_promote(
            review_svc,
            predicate="test:pred2",
            entity_name="USSOCOM",
            entity_type="oc:org",
            entity_id="ent_chunk2_ussocom",
            source_ref="chunk2",
        )
        result = auto_resolve_identities(db_path=review_svc.store.db_path)
        assert result.entities_scanned == 2
        assert result.groups_found == 1
        assert result.identities_created == 1
        assert result.aliases_attached == 1

        # Verify identity has 2 memberships
        identity_svc = IdentityService(db_path=review_svc.store.db_path)
        identities = identity_svc.list_identities()
        assert len(identities) == 1
        assert len(identities[0].memberships) == 2

    def test_different_names_no_merge(self, tmp_path: Path) -> None:
        """Entities with different names stay separate."""
        review_svc = _seed_review_service(tmp_path)
        _submit_accept_promote(
            review_svc,
            predicate="test:pred",
            entity_name="Gen. Holland",
            entity_type="oc:person",
            entity_id="ent_1",
        )
        _submit_accept_promote(
            review_svc,
            predicate="test:pred",
            entity_name="Adm. Olson",
            entity_type="oc:person",
            entity_id="ent_2",
        )
        result = auto_resolve_identities(db_path=review_svc.store.db_path)
        assert result.entities_scanned == 2
        assert result.groups_found == 2
        assert result.identities_created == 2
        assert result.aliases_attached == 0

    def test_case_insensitive_merge(self, tmp_path: Path) -> None:
        """Case-insensitive matching merges USSOCOM and ussocom."""
        review_svc = _seed_review_service(tmp_path)
        _submit_accept_promote(
            review_svc,
            predicate="test:pred1",
            entity_name="USSOCOM",
            entity_type="oc:org",
            entity_id="ent_upper",
        )
        _submit_accept_promote(
            review_svc,
            predicate="test:pred2",
            entity_name="ussocom",
            entity_type="oc:org",
            entity_id="ent_lower",
        )
        result = auto_resolve_identities(db_path=review_svc.store.db_path)
        assert result.groups_found == 1

    def test_idempotent(self, tmp_path: Path) -> None:
        """Running auto-resolve twice doesn't duplicate identities."""
        review_svc = _seed_review_service(tmp_path)
        _submit_accept_promote(
            review_svc,
            predicate="test:pred",
            entity_name="Gen. Holland",
            entity_type="oc:person",
            entity_id="ent_1",
        )
        result1 = auto_resolve_identities(db_path=review_svc.store.db_path)
        result2 = auto_resolve_identities(db_path=review_svc.store.db_path)
        assert result1.identities_created == 1
        # Second run: identity already exists, so create returns existing
        # Code path hits the "already has membership" branch
        assert result2.identities_created + result2.already_resolved == 1

    def test_strategy_in_result(self, tmp_path: Path) -> None:
        """Result records which strategy was used."""
        review_svc = _seed_review_service(tmp_path)
        result = auto_resolve_identities(db_path=review_svc.store.db_path, strategy="exact")
        assert result.strategy == "exact"

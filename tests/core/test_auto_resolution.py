"""Tests for automated entity resolution."""

from __future__ import annotations

from pathlib import Path

import pytest

from unittest.mock import MagicMock, patch

from onto_canon6.core.auto_resolution import (
    ClusteringResult,
    EntityCluster,
    _acronym_signatures,
    _build_entity_info_list,
    _entity_types_compatible,
    _fuzzy_pre_filter,
    _group_by_fuzzy,
    _group_by_name,
    _normalize_name,
    _postprocess_llm_cluster,
    _resolution_type_family,
    auto_resolve_identities,
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

    def test_strip_whitespace(self) -> None:
        assert _normalize_name("  Holland  ") == "holland"

    def test_empty(self) -> None:
        assert _normalize_name("") == ""

    def test_title_abbreviation_stripped(self) -> None:
        """Gen. Smith normalizes to just 'smith'."""
        assert _normalize_name("Gen. Smith") == "smith"

    def test_full_title_stripped(self) -> None:
        """General Smith normalizes to just 'smith'."""
        assert _normalize_name("General Smith") == "smith"

    def test_title_variations_converge(self) -> None:
        """Gen. John Smith and General John Smith normalize to same key."""
        assert _normalize_name("Gen. John Smith") == _normalize_name("General John Smith")

    def test_multi_word_title_stripped(self) -> None:
        """Lieutenant General normalizes away."""
        assert _normalize_name("Lt. Gen. James Holland") == "james holland"

    def test_civilian_title_stripped(self) -> None:
        """Dr. and Mr. are stripped."""
        assert _normalize_name("Dr. Jane Doe") == "jane doe"
        assert _normalize_name("Mr. John Smith") == "john smith"

    def test_no_title_unchanged(self) -> None:
        """Names without titles pass through normally."""
        assert _normalize_name("John Smith") == "john smith"

    def test_org_names_unaffected(self) -> None:
        """Org names that happen to contain title-like substrings are fine."""
        assert _normalize_name("USSOCOM") == "ussocom"
        assert _normalize_name("4th PSYOP Group") == "4th psyop group"

    def test_trailing_punctuation_stripped(self) -> None:
        """Trailing periods and commas are cleaned."""
        assert _normalize_name("Smith,") == "smith"
        assert _normalize_name("Smith.") == "smith"


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
        name_map: dict[str, str] = {}
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


class TestFuzzyResolution:
    """Test fuzzy name matching with rapidfuzz."""

    def test_fuzzy_groups_similar_names(self) -> None:
        """Fuzzy matching groups 'Gen. Holland' and 'General Holland'."""
        entity_ids = ["ent_1", "ent_2"]
        name_map = {"ent_1": "Gen. Holland", "ent_2": "General Holland"}
        entity_types = {"ent_1": "oc:person", "ent_2": "oc:person"}
        groups = _group_by_fuzzy(entity_ids, name_map, entity_types, threshold=75)
        # token_sort_ratio("gen. holland", "general holland") ≈ 81 → should merge
        assert len(groups) == 1

    def test_fuzzy_rejects_different_types(self) -> None:
        """Fuzzy matching respects entity_type guard."""
        entity_ids = ["ent_1", "ent_2"]
        name_map = {"ent_1": "USSOCOM", "ent_2": "USSOCOM Commander"}
        entity_types = {"ent_1": "oc:org", "ent_2": "oc:person"}
        groups = _group_by_fuzzy(entity_ids, name_map, entity_types, threshold=70)
        # Different types → should NOT merge despite similar names
        assert len(groups) == 2

    def test_fuzzy_threshold_controls_strictness(self) -> None:
        """Higher threshold means fewer merges."""
        entity_ids = ["ent_1", "ent_2"]
        name_map = {"ent_1": "4th PSYOP Group", "ent_2": "4th POG"}
        entity_types = {"ent_1": "oc:unit", "ent_2": "oc:unit"}
        # Low threshold — merge
        groups_low = _group_by_fuzzy(entity_ids, name_map, entity_types, threshold=40)
        # High threshold — don't merge
        groups_high = _group_by_fuzzy(entity_ids, name_map, entity_types, threshold=95)
        assert len(groups_low) <= len(groups_high)

    def test_fuzzy_full_workflow(self, tmp_path: Path) -> None:
        """Fuzzy strategy works end-to-end."""
        review_svc = _seed_review_service(tmp_path)
        _submit_accept_promote(
            review_svc,
            predicate="test:pred1",
            entity_name="Gen. Holland",
            entity_type="oc:person",
            entity_id="ent_holland_1",
            source_ref="chunk1",
        )
        _submit_accept_promote(
            review_svc,
            predicate="test:pred2",
            entity_name="General Holland",
            entity_type="oc:person",
            entity_id="ent_holland_2",
            source_ref="chunk2",
        )
        result = auto_resolve_identities(
            db_path=review_svc.store.db_path,
            strategy="fuzzy",
            fuzzy_threshold=75,
        )
        assert result.strategy == "fuzzy"
        assert result.groups_found == 1  # Should merge
        assert result.entities_scanned == 2

    def test_exact_merges_title_variations(self, tmp_path: Path) -> None:
        """Exact match NOW merges Gen. Holland / General Holland via normalization."""
        review_svc = _seed_review_service(tmp_path)
        _submit_accept_promote(
            review_svc,
            predicate="test:pred1",
            entity_name="Gen. Holland",
            entity_type="oc:person",
            entity_id="ent_gen",
        )
        _submit_accept_promote(
            review_svc,
            predicate="test:pred2",
            entity_name="General Holland",
            entity_type="oc:person",
            entity_id="ent_general",
        )
        result = auto_resolve_identities(
            db_path=review_svc.store.db_path,
            strategy="exact",
        )
        # Title normalization makes both "holland" → exact merge
        assert result.groups_found == 1


class TestClusteringModels:
    """Test Pydantic models for LLM clustering output."""

    def test_clustering_result_parses(self) -> None:
        """ClusteringResult parses valid JSON."""
        raw = '{"clusters": [{"canonical_name": "John Smith", "entity_ids": ["e1", "e2"], "reasoning": "same person"}]}'
        result = ClusteringResult.model_validate_json(raw)
        assert len(result.clusters) == 1
        assert result.clusters[0].canonical_name == "John Smith"
        assert result.clusters[0].entity_ids == ["e1", "e2"]

    def test_clustering_result_ignores_extra(self) -> None:
        """ClusteringResult ignores extra fields from LLM."""
        raw = '{"clusters": [{"canonical_name": "X", "entity_ids": ["e1"], "reasoning": "ok", "extra": true}], "extra_top": 1}'
        result = ClusteringResult.model_validate_json(raw)
        assert len(result.clusters) == 1

    def test_empty_clusters(self) -> None:
        """Empty clusters list is valid."""
        raw = '{"clusters": []}'
        result = ClusteringResult.model_validate_json(raw)
        assert len(result.clusters) == 0


class TestBuildEntityInfo:
    """Test entity info construction for prompts."""

    def test_build_entity_info_list(self) -> None:
        entities = _build_entity_info_list(
            ["e1", "e2"],
            {"e1": "Gen. Smith", "e2": "John Doe"},
            {"e1": "oc:person", "e2": "oc:person"},
            {"e1": "commanded 3rd division", "e2": ""},
        )
        assert len(entities) == 2
        assert entities[0].entity_id == "e1"
        assert entities[0].name == "Gen. Smith"
        assert entities[0].context == "commanded 3rd division"
        assert entities[1].context == ""


class TestFuzzyPreFilter:
    """Test fuzzy pre-filtering for LLM clustering."""

    def test_pre_filter_groups_similar(self) -> None:
        """Fuzzy pre-filter groups similar names."""
        from onto_canon6.core.auto_resolution import _EntityInfo
        entities = [
            _EntityInfo("e1", "Gen. Holland", "oc:person", ""),
            _EntityInfo("e2", "General Holland", "oc:person", ""),
            _EntityInfo("e3", "Adm. Olson", "oc:person", ""),
        ]
        proposals, unclustered = _fuzzy_pre_filter(entities, threshold=75)
        assert len(proposals) == 1  # Holland pair
        assert len(proposals[0].entities) == 2
        assert len(unclustered) == 1  # Olson singleton
        assert unclustered[0].entity_id == "e3"


class TestGroupByLLM:
    """Test LLM clustering with mocked LLM calls."""

    def test_resolution_type_family_maps_subtypes_together(self) -> None:
        """Related organization and place subtypes share a resolution family."""
        assert _resolution_type_family("oc:military_organization") == "organization"
        assert _resolution_type_family("oc:organization") == "organization"
        assert _resolution_type_family("oc:military_installation") == "place"
        assert _resolution_type_family("oc:location") == "place"

    def test_entity_type_compatibility_uses_resolution_family(self) -> None:
        """Compatibility is broader than exact string equality for safe subtype pairs."""
        assert _entity_types_compatible(
            "oc:military_organization",
            "oc:organization",
        )
        assert _entity_types_compatible(
            "oc:military_installation",
            "oc:location",
        )
        assert not _entity_types_compatible("oc:person", "oc:organization")

    def test_postprocess_llm_cluster_splits_conflicting_full_given_names(self) -> None:
        """Conflicting full first names with the same surname do not remain merged."""
        groups = _postprocess_llm_cluster(
            ["e1", "e2", "e3", "e4"],
            name_map={
                "e1": "General John Smith",
                "e2": "James Smith",
                "e3": "Gen. J. Smith",
                "e4": "General Smith",
            },
            entity_types={
                "e1": "oc:person",
                "e2": "oc:person",
                "e3": "oc:person",
                "e4": "oc:person",
            },
        )
        normalized_groups = {frozenset(group) for group in groups}
        assert frozenset({"e1"}) in normalized_groups
        assert frozenset({"e2"}) in normalized_groups
        assert frozenset({"e3"}) in normalized_groups
        assert frozenset({"e4"}) in normalized_groups

    def test_postprocess_llm_cluster_keeps_unique_initial_with_full_name(self) -> None:
        """Initial-only variants stay attached when they match exactly one full name."""
        groups = _postprocess_llm_cluster(
            ["e1", "e2"],
            name_map={
                "e1": "General John Smith",
                "e2": "Gen. J. Smith",
            },
            entity_types={
                "e1": "oc:person",
                "e2": "oc:person",
            },
        )
        assert groups == [["e1", "e2"]]

    def test_postprocess_llm_cluster_leaves_non_people_unchanged(self) -> None:
        """Only person clusters get the extra deterministic split guard."""
        groups = _postprocess_llm_cluster(
            ["e1", "e2"],
            name_map={
                "e1": "USSOCOM",
                "e2": "U.S. Special Operations Command",
            },
            entity_types={
                "e1": "oc:military_organization",
                "e2": "oc:organization",
            },
        )
        assert groups == [["e1", "e2"]]

    def test_acronym_signatures_cover_org_shortforms(self) -> None:
        """Organization-like names expose deterministic acronym signatures."""

        assert "gwu" in _acronym_signatures("George Washington University")
        assert "cia" in _acronym_signatures("Central Intelligence Agency")
        assert "ussocom" in _acronym_signatures("U.S. Special Operations Command")
        assert "socom" in _acronym_signatures("USSOCOM")

    def test_llm_can_cluster_compatible_org_subtypes_together(self) -> None:
        """Subtype-equivalent orgs are not split before the LLM sees them."""
        mock_response = MagicMock()
        mock_response.content = ClusteringResult(
            clusters=[
                EntityCluster(
                    canonical_name="U.S. Special Operations Command",
                    entity_ids=["e1", "e2"],
                    reasoning="Same organization under short and expanded names",
                ),
            ]
        ).model_dump_json()

        async def mock_acall_llm(*args: object, **kwargs: object) -> object:
            return mock_response

        with patch.dict(
            "sys.modules",
            {
                "llm_client": MagicMock(
                    render_prompt=lambda tpl, **ctx: [{"role": "user", "content": "test"}],
                    acall_llm=mock_acall_llm,
                    get_model=lambda task, **kw: "mock-model",
                ),
            },
        ):
            from onto_canon6.core import auto_resolution as ar_mod

            groups = ar_mod._group_by_llm(
                entity_ids=["e1", "e2"],
                name_map={
                    "e1": "USSOCOM",
                    "e2": "U.S. Special Operations Command",
                },
                entity_types={
                    "e1": "oc:military_organization",
                    "e2": "oc:organization",
                },
                context_map={"e1": "", "e2": ""},
                assertions=[],
            )

        assert list(groups.values()) == [["e1", "e2"]]

    def test_llm_clustering_with_mock(self) -> None:
        """LLM clustering produces correct groups from mocked response."""
        mock_response = MagicMock()
        mock_response.content = ClusteringResult(
            clusters=[
                EntityCluster(
                    canonical_name="General John Smith",
                    entity_ids=["e1", "e2"],
                    reasoning="Same person — title variation",
                ),
                EntityCluster(
                    canonical_name="Admiral Olson",
                    entity_ids=["e3"],
                    reasoning="Singleton",
                ),
            ]
        ).model_dump_json()

        async def mock_acall_llm(*args: object, **kwargs: object) -> object:
            return mock_response

        with patch.dict(
            "sys.modules",
            {
                "llm_client": MagicMock(
                    render_prompt=lambda tpl, **ctx: [{"role": "user", "content": "test"}],
                    acall_llm=mock_acall_llm,
                    get_model=lambda task, **kw: "mock-model",
                ),
            },
        ):
            from onto_canon6.core import auto_resolution as ar_mod
            # Force re-import of llm_client in the function
            groups = ar_mod._group_by_llm(
                entity_ids=["e1", "e2", "e3"],
                name_map={"e1": "Gen. Smith", "e2": "General John Smith", "e3": "Adm. Olson"},
                entity_types={"e1": "oc:person", "e2": "oc:person", "e3": "oc:person"},
                context_map={"e1": "", "e2": "", "e3": ""},
                assertions=[],
            )

        # Should have 2 groups: one with 2 entities, one with 1
        multi_groups = [g for g in groups.values() if len(g) >= 2]
        single_groups = [g for g in groups.values() if len(g) == 1]
        assert len(multi_groups) == 1
        assert set(multi_groups[0]) == {"e1", "e2"}
        assert len(single_groups) == 1

    def test_llm_collapses_same_full_person_name_across_clusters(self) -> None:
        """Equivalent full person names should collapse after the LLM split them."""

        mock_response = MagicMock()
        mock_response.content = ClusteringResult(
            clusters=[
                EntityCluster(
                    canonical_name="General John Smith",
                    entity_ids=["e1"],
                    reasoning="full title form",
                ),
                EntityCluster(
                    canonical_name="John Smith",
                    entity_ids=["e2"],
                    reasoning="plain form",
                ),
            ]
        ).model_dump_json()

        async def mock_acall_llm(*args: object, **kwargs: object) -> object:
            return mock_response

        with patch.dict(
            "sys.modules",
            {
                "llm_client": MagicMock(
                    render_prompt=lambda tpl, **ctx: [{"role": "user", "content": "test"}],
                    acall_llm=mock_acall_llm,
                    get_model=lambda task, **kw: "mock-model",
                ),
            },
        ):
            from onto_canon6.core import auto_resolution as ar_mod

            groups = ar_mod._group_by_llm(
                entity_ids=["e1", "e2"],
                name_map={
                    "e1": "General John Smith",
                    "e2": "John Smith",
                },
                entity_types={
                    "e1": "oc:person",
                    "e2": "oc:person",
                },
                context_map={"e1": "", "e2": ""},
                assertions=[],
            )

        assert list(groups.values()) == [["e1", "e2"]]

    def test_llm_collapses_acronym_and_long_form_org_clusters(self) -> None:
        """Equivalent acronym and long-form org clusters should collapse after LLM."""

        mock_response = MagicMock()
        mock_response.content = ClusteringResult(
            clusters=[
                EntityCluster(
                    canonical_name="USSOCOM",
                    entity_ids=["e1"],
                    reasoning="short form mention",
                ),
                EntityCluster(
                    canonical_name="U.S. Special Operations Command",
                    entity_ids=["e2"],
                    reasoning="long form mention",
                ),
            ]
        ).model_dump_json()

        async def mock_acall_llm(*args: object, **kwargs: object) -> object:
            return mock_response

        with patch.dict(
            "sys.modules",
            {
                "llm_client": MagicMock(
                    render_prompt=lambda tpl, **ctx: [{"role": "user", "content": "test"}],
                    acall_llm=mock_acall_llm,
                    get_model=lambda task, **kw: "mock-model",
                ),
            },
        ):
            from onto_canon6.core import auto_resolution as ar_mod

            groups = ar_mod._group_by_llm(
                entity_ids=["e1", "e2"],
                name_map={
                    "e1": "USSOCOM",
                    "e2": "U.S. Special Operations Command",
                },
                entity_types={
                    "e1": "oc:military_organization",
                    "e2": "oc:military_organization",
                },
                context_map={"e1": "", "e2": ""},
                assertions=[],
            )

        assert list(groups.values()) == [["e1", "e2"]]

    def test_llm_collapses_generic_acronym_and_long_form_org_clusters(self) -> None:
        """Generic acronym organization surfaces should still share one LLM family."""

        mock_response = MagicMock()
        mock_response.content = ClusteringResult(
            clusters=[
                EntityCluster(
                    canonical_name="NSA",
                    entity_ids=["e1"],
                    reasoning="short form mention",
                ),
                EntityCluster(
                    canonical_name="National Security Agency",
                    entity_ids=["e2"],
                    reasoning="long form mention",
                ),
            ]
        ).model_dump_json()

        async def mock_acall_llm(*args: object, **kwargs: object) -> object:
            return mock_response

        with patch.dict(
            "sys.modules",
            {
                "llm_client": MagicMock(
                    render_prompt=lambda tpl, **ctx: [{"role": "user", "content": "test"}],
                    acall_llm=mock_acall_llm,
                    get_model=lambda task, **kw: "mock-model",
                ),
            },
        ):
            from onto_canon6.core import auto_resolution as ar_mod

            groups = ar_mod._group_by_llm(
                entity_ids=["e1", "e2"],
                name_map={
                    "e1": "NSA",
                    "e2": "National Security Agency",
                },
                entity_types={
                    "e1": "",
                    "e2": "oc:government_agency",
                },
                context_map={"e1": "", "e2": ""},
                assertions=[],
            )

        assert list(groups.values()) == [["e1", "e2"]]

    def test_entity_types_compatible_person_like_rank_mentions(self) -> None:
        """Rank-typed titled names can still compare with person mentions."""

        from onto_canon6.core.auto_resolution import _entity_types_compatible

        assert _entity_types_compatible(
            "oc:military_rank",
            "oc:person",
            left_name="Gen. Smith",
            right_name="General John Smith",
        )

    def test_entity_types_compatible_installation_like_names(self) -> None:
        """Installation-like names can compare across place/org drift."""

        from onto_canon6.core.auto_resolution import _entity_types_compatible

        assert _entity_types_compatible(
            "oc:location",
            "oc:military_organization",
            left_name="Ft. Bragg",
            right_name="Fort Liberty",
        )

    def test_entity_types_compatible_city_and_location(self) -> None:
        """City mentions should compare with location ground truth conservatively."""

        from onto_canon6.core.auto_resolution import _entity_types_compatible

        assert _entity_types_compatible(
            "oc:city",
            "oc:location",
            left_name="Washington",
            right_name="Washington D.C.",
        )

    def test_entity_types_compatible_university_like_names(self) -> None:
        """University mentions can compare with educational-institution ground truth."""

        from onto_canon6.core.auto_resolution import _entity_types_compatible

        assert _entity_types_compatible(
            "oc:university",
            "oc:educational_institution",
            left_name="George Washington University",
            right_name="George Washington University",
        )

    def test_entity_types_compatible_government_agency_family(self) -> None:
        """Government-agency mentions should compare with government organizations."""

        from onto_canon6.core.auto_resolution import _entity_types_compatible

        assert _entity_types_compatible(
            "oc:government_agency",
            "oc:government_organization",
            left_name="CIA",
            right_name="Central Intelligence Agency",
        )

    def test_entity_types_compatible_generic_org_like_names(self) -> None:
        """Generic / missing types can join the organization family when the name is strong."""

        from onto_canon6.core.auto_resolution import _entity_types_compatible

        assert _entity_types_compatible(
            "",
            "oc:military_organization",
            left_name="U.S. Special Operations Command",
            right_name="USSOCOM",
        )

    def test_entity_types_compatible_generic_acronym_org_like_names(self) -> None:
        """Single-token uppercase acronyms can still route into the organization family."""

        from onto_canon6.core.auto_resolution import _entity_types_compatible

        assert _entity_types_compatible(
            "",
            "oc:government_agency",
            left_name="NSA",
            right_name="National Security Agency",
        )
        assert _entity_types_compatible(
            "",
            "oc:university",
            left_name="GWU",
            right_name="George Washington University",
        )

    def test_entity_types_compatible_does_not_treat_short_place_abbrev_as_org(self) -> None:
        """Short place abbreviations must not be rerouted into the organization family."""

        from onto_canon6.core.auto_resolution import _entity_types_compatible

        assert not _entity_types_compatible(
            "",
            "oc:location",
            left_name="D.C.",
            right_name="Washington D.C.",
        )

    def test_entity_types_compatible_generic_titled_person_names(self) -> None:
        """Generic titled person mentions should compare with person entities."""

        from onto_canon6.core.auto_resolution import _entity_types_compatible

        assert _entity_types_compatible(
            "",
            "oc:person",
            left_name="Gen. J. Smith",
            right_name="General John Smith",
        )

    def test_collapse_equivalent_llm_groups_merges_installation_renames(self) -> None:
        """Known installation redesignations should collapse across separate LLM groups."""

        from onto_canon6.core import auto_resolution as ar_mod

        groups = ar_mod._collapse_equivalent_llm_groups(
            {
                "g1": ["e1"],
                "g2": ["e2"],
            },
            name_map={
                "e1": "Ft. Bragg",
                "e2": "Fort Liberty",
            },
            entity_types={
                "e1": "oc:military_base",
                "e2": "oc:military_organization",
            },
        )

        assert {frozenset(group) for group in groups.values()} == {
            frozenset({"e1", "e2"}),
        }

    def test_collapse_equivalent_llm_groups_merges_titled_person_bridges(self) -> None:
        """Titled Smith variants should collapse when only one titled anchor exists."""

        from onto_canon6.core import auto_resolution as ar_mod

        groups = ar_mod._collapse_equivalent_llm_groups(
            {
                "g1": ["e1", "e2"],
                "g2": ["e3"],
                "g3": ["e4"],
                "g4": ["e5"],
            },
            name_map={
                "e1": "General John Smith",
                "e2": "John Smith",
                "e3": "Gen. Smith",
                "e4": "Gen. J. Smith",
                "e5": "James Smith",
            },
            entity_types={
                "e1": "oc:person",
                "e2": "oc:person",
                "e3": "oc:person",
                "e4": "",
                "e5": "oc:person",
            },
        )

        assert {frozenset(group) for group in groups.values()} == {
            frozenset({"e1", "e2", "e3", "e4"}),
            frozenset({"e5"}),
        }

    def test_collapse_equivalent_llm_groups_merges_initial_bridge_into_unique_full_anchor(self) -> None:
        """A titled initial-only group can join one unique full-name anchor even when the anchor is untitled."""

        from onto_canon6.core import auto_resolution as ar_mod

        groups = ar_mod._collapse_equivalent_llm_groups(
            {
                "g1": ["e1"],
                "g2": ["e2", "e3"],
            },
            name_map={
                "e1": "John Smith",
                "e2": "Gen. J. Smith",
                "e3": "J. Smith",
            },
            entity_types={
                "e1": "oc:person",
                "e2": "oc:person",
                "e3": "oc:person",
            },
        )

        assert {frozenset(group) for group in groups.values()} == {
            frozenset({"e1", "e2", "e3"}),
        }

    def test_collapse_equivalent_llm_groups_keeps_conflicting_titled_anchors_separate(self) -> None:
        """Surname-only titled mentions must stay explicit when two titled anchors compete."""

        from onto_canon6.core import auto_resolution as ar_mod

        groups = ar_mod._collapse_equivalent_llm_groups(
            {
                "g1": ["e1"],
                "g2": ["e2"],
                "g3": ["e3"],
            },
            name_map={
                "e1": "General John Smith",
                "e2": "Colonel James Smith",
                "e3": "Gen. Smith",
            },
            entity_types={
                "e1": "oc:person",
                "e2": "oc:person",
                "e3": "oc:person",
            },
        )

        assert {frozenset(group) for group in groups.values()} == {
            frozenset({"e1"}),
            frozenset({"e2"}),
            frozenset({"e3"}),
        }

    def test_collapse_equivalent_llm_groups_does_not_merge_person_groups_on_bare_surname(self) -> None:
        """Bare titled surnames must not glue incompatible full-name person groups together."""

        from onto_canon6.core import auto_resolution as ar_mod

        groups = ar_mod._collapse_equivalent_llm_groups(
            {
                "g1": ["e1", "e2"],
                "g2": ["e3", "e4"],
            },
            name_map={
                "e1": "General John Smith",
                "e2": "Gen. J. Smith",
                "e3": "James Smith",
                "e4": "General Smith",
            },
            entity_types={
                "e1": "oc:person",
                "e2": "oc:person",
                "e3": "oc:person",
                "e4": "oc:person",
            },
        )

        assert {frozenset(group) for group in groups.values()} == {
            frozenset({"e1", "e2"}),
            frozenset({"e3", "e4"}),
        }

    def test_collapse_equivalent_llm_groups_merges_unique_titled_surname_into_single_full_anchor(self) -> None:
        """A titled surname-only group can join one compatible full-name family when no conflict exists."""

        from onto_canon6.core import auto_resolution as ar_mod

        groups = ar_mod._collapse_equivalent_llm_groups(
            {
                "g1": ["e1", "e2"],
                "g2": ["e3"],
            },
            name_map={
                "e1": "James Rodriguez",
                "e2": "Colonel Rodriguez",
                "e3": "Col. Rodriguez",
            },
            entity_types={
                "e1": "oc:person",
                "e2": "oc:person",
                "e3": "oc:person",
            },
        )

        assert {frozenset(group) for group in groups.values()} == {
            frozenset({"e1", "e2", "e3"}),
        }

    def test_collapse_equivalent_llm_groups_merges_district_place_alias_family(self) -> None:
        """District-style place aliases should collapse with their single-token place surface."""

        from onto_canon6.core import auto_resolution as ar_mod

        groups = ar_mod._collapse_equivalent_llm_groups(
            {
                "g1": ["e1", "e2"],
                "g2": ["e3"],
            },
            name_map={
                "e1": "Washington D.C.",
                "e2": "D.C.",
                "e3": "Washington",
            },
            entity_types={
                "e1": "oc:location",
                "e2": "oc:location",
                "e3": "oc:location",
            },
        )

        assert {frozenset(group) for group in groups.values()} == {
            frozenset({"e1", "e2", "e3"}),
        }

    def test_collapse_equivalent_llm_groups_merges_unknown_single_token_place_into_district_family(self) -> None:
        """A generic single-token place mention can attach to one unique district-place anchor."""

        from onto_canon6.core import auto_resolution as ar_mod

        groups = ar_mod._collapse_equivalent_llm_groups(
            {
                "g1": ["e1", "e2"],
                "g2": ["e3"],
            },
            name_map={
                "e1": "Washington D.C.",
                "e2": "D.C.",
                "e3": "Washington",
            },
            entity_types={
                "e1": "oc:location",
                "e2": "oc:location",
                "e3": "",
            },
        )

        assert {frozenset(group) for group in groups.values()} == {
            frozenset({"e1", "e2", "e3"}),
        }

    def test_collapse_equivalent_llm_groups_keeps_district_place_separate_from_institution(self) -> None:
        """District-style place bridging must not cross the place/institution family boundary."""

        from onto_canon6.core import auto_resolution as ar_mod

        groups = ar_mod._collapse_equivalent_llm_groups(
            {
                "g1": ["e1", "e2"],
                "g2": ["e3"],
            },
            name_map={
                "e1": "Washington D.C.",
                "e2": "D.C.",
                "e3": "George Washington University",
            },
            entity_types={
                "e1": "oc:location",
                "e2": "oc:location",
                "e3": "oc:university",
            },
        )

        assert {frozenset(group) for group in groups.values()} == {
            frozenset({"e1", "e2"}),
            frozenset({"e3"}),
        }

    def test_collapse_equivalent_llm_groups_merges_unique_descriptor_alias_family(self) -> None:
        """One bounded descriptor-only organization group can join one unique source-backed anchor."""

        from onto_canon6.core import auto_resolution as ar_mod

        groups = ar_mod._collapse_equivalent_llm_groups(
            {
                "g1": ["e1"],
                "g2": ["e2"],
            },
            name_map={
                "e1": "the Agency",
                "e2": "CIA",
            },
            entity_types={
                "e1": "oc:organization",
                "e2": "oc:government_agency",
            },
            context_map={
                "e2": "Eric Olson met with officials from the CIA at the agency's headquarters in Washington.",
            },
        )

        assert {frozenset(group) for group in groups.values()} == {
            frozenset({"e1", "e2"}),
        }

    def test_collapse_equivalent_llm_groups_keeps_ambiguous_descriptor_alias_unmerged(self) -> None:
        """Descriptor-only organization groups must stay explicit when two anchors advertise the same head."""

        from onto_canon6.core import auto_resolution as ar_mod

        groups = ar_mod._collapse_equivalent_llm_groups(
            {
                "g1": ["e1"],
                "g2": ["e2"],
                "g3": ["e3"],
            },
            name_map={
                "e1": "the Agency",
                "e2": "CIA",
                "e3": "NSA",
            },
            entity_types={
                "e1": "oc:organization",
                "e2": "oc:government_agency",
                "e3": "oc:government_agency",
            },
            context_map={
                "e2": "Officials from the CIA arrived at the agency's headquarters.",
                "e3": "Analysts from the NSA said the agency's budget increased.",
            },
        )

        assert {frozenset(group) for group in groups.values()} == {
            frozenset({"e1"}),
            frozenset({"e2"}),
            frozenset({"e3"}),
        }

    def test_llm_clustering_postprocesses_conflicting_person_names(self) -> None:
        """Conflicting same-surname people keep one John cluster and one James cluster."""
        mock_response = MagicMock()
        mock_response.content = ClusteringResult(
            clusters=[
                EntityCluster(
                    canonical_name="Smith",
                    entity_ids=["e1", "e2", "e3"],
                    reasoning="All appear to be Smith references",
                ),
            ]
        ).model_dump_json()

        async def mock_acall_llm(*args: object, **kwargs: object) -> object:
            return mock_response

        with patch.dict(
            "sys.modules",
            {
                "llm_client": MagicMock(
                    render_prompt=lambda tpl, **ctx: [{"role": "user", "content": "test"}],
                    acall_llm=mock_acall_llm,
                    get_model=lambda task, **kw: "mock-model",
                ),
            },
        ):
            from onto_canon6.core import auto_resolution as ar_mod

            groups = ar_mod._group_by_llm(
                entity_ids=["e1", "e2", "e3"],
                name_map={
                    "e1": "General John Smith",
                    "e2": "James Smith",
                    "e3": "Gen. J. Smith",
                },
                entity_types={
                    "e1": "oc:person",
                    "e2": "oc:person",
                    "e3": "oc:person",
                },
                context_map={"e1": "", "e2": "", "e3": ""},
                assertions=[],
            )

        assert {frozenset(group) for group in groups.values()} == {
            frozenset({"e1", "e3"}),
            frozenset({"e2"}),
        }

    def test_llm_fails_loud_on_import_error(self) -> None:
        """Raises RuntimeError when llm_client unavailable (fail loud, no silent fallback)."""
        with patch.dict("sys.modules", {"llm_client": None}):
            from onto_canon6.core import auto_resolution as ar_mod
            with pytest.raises(RuntimeError, match="llm_client is required"):
                ar_mod._group_by_llm(
                    entity_ids=["e1", "e2"],
                    name_map={"e1": "USSOCOM", "e2": "USSOCOM"},
                    entity_types={"e1": "oc:org", "e2": "oc:org"},
                    context_map={},
                    assertions=[],
                )

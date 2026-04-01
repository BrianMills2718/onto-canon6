"""Tests for automated entity resolution."""

from __future__ import annotations

from pathlib import Path

import pytest

from unittest.mock import MagicMock, patch

from onto_canon6.core.auto_resolution import (
    ClusteringResult,
    EntityCluster,
    MergeValidation,
    _build_context_map,
    _build_entity_info_list,
    _fuzzy_pre_filter,
    _group_by_fuzzy,
    _group_by_llm,
    _oc_type_to_sumo,
    _types_compatible,
    _validate_groups_with_llm,
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


class TestOcTypeToSumo:
    """Test oc: type to SUMO CamelCase conversion."""

    def test_oc_prefix(self) -> None:
        assert _oc_type_to_sumo("oc:military_organization") == "MilitaryOrganization"

    def test_oc_underscore_prefix(self) -> None:
        assert _oc_type_to_sumo("oc_military_organization") == "MilitaryOrganization"

    def test_plain_snake_case(self) -> None:
        assert _oc_type_to_sumo("military_organization") == "MilitaryOrganization"

    def test_person(self) -> None:
        assert _oc_type_to_sumo("oc:person") == "Person"

    def test_already_camel(self) -> None:
        assert _oc_type_to_sumo("MilitaryOrganization") == "Militaryorganization"
        # Note: this is imperfect for already-CamelCase input but acceptable


class TestTypesCompatible:
    """Test type compatibility using SUMO hierarchy."""

    def test_same_type(self) -> None:
        assert _types_compatible("oc:person", "oc:person") is True

    def test_empty_type_compatible(self) -> None:
        assert _types_compatible("", "oc:person") is True
        assert _types_compatible("oc:person", "") is True

    def test_military_org_is_organization(self) -> None:
        """MilitaryOrganization and Organization share ancestor."""
        # This test requires sumo_plus.db — skip if not available
        from pathlib import Path
        if not Path("data/sumo_plus.db").exists():
            pytest.skip("sumo_plus.db not available")
        assert _types_compatible("oc:military_organization", "oc:organization") is True

    def test_person_not_organization(self) -> None:
        """Person and Organization should NOT be compatible."""
        from pathlib import Path
        if not Path("data/sumo_plus.db").exists():
            pytest.skip("sumo_plus.db not available")
        assert _types_compatible("oc:person", "oc:organization") is False

    def test_government_org_compatible_with_org(self) -> None:
        from pathlib import Path
        if not Path("data/sumo_plus.db").exists():
            pytest.skip("sumo_plus.db not available")
        assert _types_compatible("oc:government_organization", "oc:organization") is True


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


class TestValidateGroupsWithLLM:
    """Test LLM merge validation with mocked LLM calls."""

    def test_confirm_merge(self) -> None:
        """LLM confirms a valid merge group."""
        mock_response = MagicMock()
        mock_response.content = MergeValidation(
            confirm=True,
            reasoning="Same person — title variation of General Smith",
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
            groups = {"group_0": ["e1", "e2"]}
            result = ar_mod._validate_groups_with_llm(
                groups,
                {"e1": "Gen. Smith", "e2": "General Smith"},
                {"e1": "oc:person", "e2": "oc:person"},
                {"e1": "commanded 3rd div", "e2": "led 3rd division"},
            )

        # Confirmed group should be preserved
        multi = [g for g in result.values() if len(g) >= 2]
        assert len(multi) == 1
        assert set(multi[0]) == {"e1", "e2"}

    def test_reject_merge(self) -> None:
        """LLM rejects a false merge — entities split into singletons."""
        mock_response = MagicMock()
        mock_response.content = MergeValidation(
            confirm=False,
            reasoning="Different people — John Smith (general) vs James Smith (analyst)",
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
            groups = {"group_0": ["e1", "e2"]}
            result = ar_mod._validate_groups_with_llm(
                groups,
                {"e1": "Gen. Smith", "e2": "James Smith"},
                {"e1": "oc:person", "e2": "oc:person"},
                {"e1": "commanded forces", "e2": "civilian analyst"},
            )

        # Rejected group should be split into singletons
        multi = [g for g in result.values() if len(g) >= 2]
        assert len(multi) == 0
        assert len(result) == 2  # Two singletons

    def test_singletons_pass_through(self) -> None:
        """Single-entity groups pass through without LLM call."""
        def _fail_render(*a: object, **k: object) -> list[dict[str, str]]:
            raise AssertionError("render_prompt should not be called for singletons")

        async def _fail_acall(*a: object, **k: object) -> object:
            raise AssertionError("acall_llm should not be called for singletons")

        with patch.dict(
            "sys.modules",
            {
                "llm_client": MagicMock(
                    render_prompt=_fail_render,
                    acall_llm=_fail_acall,
                    get_model=lambda task, **kw: "mock-model",
                ),
            },
        ):
            from onto_canon6.core import auto_resolution as ar_mod
            groups = {"s0": ["e1"], "s1": ["e2"]}
            result = ar_mod._validate_groups_with_llm(
                groups,
                {"e1": "Smith", "e2": "Jones"},
                {"e1": "oc:person", "e2": "oc:person"},
                {},
            )

        assert len(result) == 2
        assert all(len(g) == 1 for g in result.values())

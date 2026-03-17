"""Tests for donor profile and ontology-pack loading."""

from __future__ import annotations

from pathlib import Path
import sys

from onto_canon6.ontology_runtime import decide_unknown_item

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))

from onto_canon6.ontology_runtime import (  # noqa: E402
    LoadedProfile,
    OverlayPredicateAdditionRecord,
    clear_loader_caches,
    donor_ontology_packs_root,
    donor_profiles_root,
    load_effective_profile,
    load_ontology_pack,
    load_overlay_predicate_additions,
    load_profile,
    overlay_pack_ref_for,
    write_overlay_predicate_addition,
)


def setup_function() -> None:
    """Reset loader caches so tests observe local file changes deterministically."""

    clear_loader_caches()


def test_loader_uses_repo_relative_donor_roots() -> None:
    """Donor roots should resolve through onto-canon6 config, not absolute code paths."""

    assert donor_profiles_root().name == "profiles"
    assert donor_profiles_root().parent.name == "onto-canon5"
    assert donor_ontology_packs_root().name == "ontology_packs"
    assert donor_ontology_packs_root().parent.name == "onto-canon5"


def test_load_default_profile() -> None:
    """Default donor profile should load as open mode with no pack reference."""

    profile = load_profile("default", "1.0.0")

    assert isinstance(profile, LoadedProfile)
    assert profile.ontology_policy.mode == "open"
    assert profile.ontology_policy.proposal_policy == "reject"
    assert profile.pack_ref is None
    assert profile.pack is None
    assert profile.allowed_predicates is None
    assert profile.type_adapter == "null"
    assert profile.type_check_policy == "skip"


def test_load_dodaf_profile() -> None:
    """DoDAF donor profile should load explicit predicate rules from profile YAML."""

    profile = load_profile("dodaf", "0.1.0")

    assert profile.ontology_policy.mode == "closed"
    assert profile.ontology_policy.proposal_policy == "reject"
    assert profile.pack_ref is None
    assert profile.allowed_predicates is not None
    assert len(profile.allowed_predicates) == 9
    assert len(profile.predicate_rules) == 9
    support_rule = profile.predicate_rules["dodaf:service_supports_activity"]
    assert support_rule.allowed_roles == ("activity", "service")
    assert support_rule.required_roles == ("activity", "service")
    assert support_rule.role_filler_types["service"] == "dm2:Service"
    assert profile.severity_by_code["oc:profile_unknown_predicate"] == "hard"


def test_load_psyop_seed_profile_inherits_pack_rules() -> None:
    """PSYOP donor profile should load its referenced pack and inherit pack vocabulary."""

    profile = load_profile("psyop_seed", "0.1.0")

    assert profile.ontology_policy.mode == "mixed"
    assert profile.ontology_policy.proposal_policy == "allow"
    assert profile.pack_ref is not None
    assert profile.pack_ref.pack_id == "onto_canon_psyop_seed"
    assert profile.pack is not None
    assert profile.allowed_predicates is not None
    assert len(profile.allowed_predicates) == 14
    assert len(profile.predicate_rules) == 14
    assert profile.severity_by_code["oc:profile_unknown_predicate"] == "soft"
    assert "oc:replace_designation" in profile.allowed_predicates
    assert profile.pack.type_parents["oc:community"] == ("oc:organization",)
    assert profile.ontology_policy.overlay_target is not None
    assert profile.ontology_policy.overlay_target.pack_id.endswith("__overlay")


def test_load_pack_directly() -> None:
    """Direct pack loading should expose pack predicate ids and rule derivation."""

    pack = load_ontology_pack("onto_canon_psyop_seed", "0.1.0")

    assert pack.pack_ref.pack_id == "onto_canon_psyop_seed"
    assert len(pack.predicate_ids) == 14
    assert len(pack.predicate_rules) == 14
    assert pack.path.name == "0.1.0"


def test_loaded_profiles_drive_unknown_item_decisions() -> None:
    """Loaded donor profile policy should map cleanly onto unknown-item handling."""

    default_profile = load_profile("default", "1.0.0")
    dodaf_profile = load_profile("dodaf", "0.1.0")
    psyop_profile = load_profile("psyop_seed", "0.1.0")

    assert decide_unknown_item(
        policy=default_profile.ontology_policy,
        kind="predicate",
        value="oc:unknown_predicate_demo",
    ).action == "allow"
    assert decide_unknown_item(
        policy=dodaf_profile.ontology_policy,
        kind="predicate",
        value="oc:unknown_predicate_demo",
    ).action == "reject"
    psyop_decision = decide_unknown_item(
        policy=psyop_profile.ontology_policy,
        kind="predicate",
        value="oc:unknown_predicate_demo",
    )
    assert psyop_decision.action == "propose"
    assert psyop_decision.target_pack == psyop_profile.ontology_policy.overlay_target


def test_load_effective_profile_merges_local_overlay_predicates(tmp_path: Path) -> None:
    """Effective profile loading should merge locally applied overlay predicates."""

    base_profile = load_profile("psyop_seed", "0.1.0")
    assert base_profile.pack_ref is not None
    assert base_profile.ontology_policy.overlay_target is not None

    write_overlay_predicate_addition(
        OverlayPredicateAdditionRecord(
            proposal_id="prop_test_overlay",
            predicate_id="oc:overlay_added_predicate",
            base_pack=base_profile.pack_ref,
            overlay_pack=base_profile.ontology_policy.overlay_target,
            applied_by="tester",
            applied_at="2026-03-17T00:00:00Z",
        ),
        overlay_root_path=tmp_path,
    )

    effective_profile = load_effective_profile(
        "psyop_seed",
        "0.1.0",
        overlay_root=tmp_path,
    )
    assert effective_profile.allowed_predicates is not None
    assert "oc:overlay_added_predicate" in effective_profile.allowed_predicates
    assert effective_profile.active_overlay_predicates == frozenset({"oc:overlay_added_predicate"})

    additions = load_overlay_predicate_additions(
        overlay_pack_ref_for(base_profile.pack_ref),
        overlay_root_path=tmp_path,
    )
    assert len(additions) == 1

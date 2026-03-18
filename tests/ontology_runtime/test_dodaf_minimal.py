"""Tests for the local DoDAF minimal second-pack slice."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from onto_canon6.ontology_runtime import (
    load_effective_profile,
    load_ontology_pack,
    load_profile,
    validate_assertion_payload,
)
from onto_canon6.pipeline import OverlayApplicationService, ReviewService


def test_local_dodaf_minimal_pack_and_profiles_load() -> None:
    """The local DoDAF pack should load before donor roots, with strict/mixed profiles over it."""

    pack = load_ontology_pack("dodaf_minimal", "0.1.0")
    strict = load_profile("dodaf_minimal_strict", "0.1.0")
    mixed = load_profile("dodaf_minimal_mixed", "0.1.0")

    assert pack.pack_ref.pack_id == "dodaf_minimal"
    assert pack.path == Path("ontology_packs/dodaf_minimal/0.1.0").resolve()
    assert strict.pack_ref == pack.pack_ref
    assert mixed.pack_ref == pack.pack_ref
    assert strict.ontology_policy.mode == "closed"
    assert mixed.ontology_policy.mode == "mixed"
    assert mixed.ontology_policy.overlay_target is not None
    assert mixed.ontology_policy.overlay_target.pack_id == "dodaf_minimal__overlay"
    assert pack.predicate_aliases["operationalnodeexchangesinformation"] == (
        "dodaf:operational_node_exchanges_information"
    )
    assert pack.role_aliases["source"] == "source_node"
    assert pack.role_aliases["target"] == "target_node"
    assert pack.role_aliases["information"] == "information_element"


def test_dodaf_minimal_strict_accepts_known_assertion() -> None:
    """The strict DoDAF profile should accept a valid assertion using the local pack rules."""

    strict = load_profile("dodaf_minimal_strict", "0.1.0")
    outcome = validate_assertion_payload(
        {
            "predicate": "dodaf:operational_node_exchanges_information",
            "roles": {
                "source_node": [
                    {
                        "kind": "entity",
                        "entity_id": "ent:node:source",
                        "entity_type": "dm2:OperationalNode",
                    }
                ],
                "target_node": [
                    {
                        "kind": "entity",
                        "entity_id": "ent:node:target",
                        "entity_type": "dm2:OperationalNode",
                    }
                ],
                "information_element": [
                    {
                        "kind": "entity",
                        "entity_id": "ent:info:message",
                        "entity_type": "dm2:InformationElement",
                    }
                ],
            },
        },
        profile=strict,
    )

    assert outcome.hard_errors == ()
    assert outcome.soft_violations == ()
    assert outcome.proposal_requests == ()


def test_dodaf_minimal_profiles_diverge_by_ontology_mode() -> None:
    """Strict and mixed DoDAF profiles should share vocabulary but differ on unknown predicates."""

    payload = {
        "predicate": "dodaf:operational_node_supports_activity",
        "roles": {
            "source": [{"kind": "value", "value_kind": "string", "value": "Node A"}],
            "target": [{"kind": "value", "value_kind": "string", "value": "Activity B"}],
        },
    }

    strict = load_profile("dodaf_minimal_strict", "0.1.0")
    mixed = load_profile("dodaf_minimal_mixed", "0.1.0")
    strict_outcome = validate_assertion_payload(payload, profile=strict)
    mixed_outcome = validate_assertion_payload(payload, profile=mixed)

    assert [finding.code for finding in strict_outcome.hard_errors] == [
        "oc:profile_unknown_predicate"
    ]
    assert strict_outcome.proposal_requests == ()
    assert [finding.code for finding in mixed_outcome.soft_violations] == [
        "oc:profile_unknown_predicate"
    ]
    assert len(mixed_outcome.proposal_requests) == 1
    assert mixed_outcome.proposal_requests[0].target_pack is not None
    assert mixed_outcome.proposal_requests[0].target_pack.pack_id == "dodaf_minimal__overlay"


def test_dodaf_minimal_overlay_application_updates_effective_profile() -> None:
    """Applying an accepted mixed-mode proposal should change the effective profile view."""

    with TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        review_service = ReviewService(
            db_path=tmp_path / "review.sqlite3",
            overlay_root=tmp_path / "overlays",
        )
        overlay_service = OverlayApplicationService(
            db_path=tmp_path / "review.sqlite3",
            overlay_root=tmp_path / "overlays",
        )

        submission = review_service.submit_candidate_assertion(
            payload={
                "predicate": "dodaf:operational_node_supports_activity",
                "roles": {
                    "source": [{"kind": "value", "value_kind": "string", "value": "Node A"}],
                    "target": [{"kind": "value", "value_kind": "string", "value": "Activity B"}],
                },
            },
            profile_id="dodaf_minimal_mixed",
            profile_version="0.1.0",
            submitted_by="analyst:test",
            source_kind="text_file",
            source_ref="sample.txt",
        )

        proposal_id = submission.proposals[0].proposal_id
        review_service.review_proposal(
            proposal_id=proposal_id,
            decision="accepted",
            actor_id="analyst:reviewer",
            acceptance_policy="apply_to_overlay",
        )
        overlay_service.apply_proposal_to_overlay(
            proposal_id=proposal_id,
            applied_by="analyst:reviewer",
        )

        effective_profile = load_effective_profile(
            "dodaf_minimal_mixed",
            "0.1.0",
            overlay_root=tmp_path / "overlays",
        )

        assert "dodaf:operational_node_supports_activity" in (
            effective_profile.allowed_predicates or frozenset()
        )
        assert "dodaf:operational_node_supports_activity" in effective_profile.active_overlay_predicates

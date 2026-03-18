"""Tests for the local WhyGame minimal Phase 14 pack and profile."""

from __future__ import annotations

from pathlib import Path

from onto_canon6.ontology_runtime import load_ontology_pack, load_profile, validate_assertion_payload


def test_local_whygame_minimal_pack_and_profile_load() -> None:
    """The local WhyGame pack should load with its strict profile and aliases."""

    pack = load_ontology_pack("whygame_minimal", "0.1.0")
    profile = load_profile("whygame_minimal_strict", "0.1.0")

    assert pack.pack_ref.pack_id == "whygame_minimal"
    assert pack.path == Path("ontology_packs/whygame_minimal/0.1.0").resolve()
    assert profile.pack_ref == pack.pack_ref
    assert profile.ontology_policy.mode == "closed"
    assert pack.role_aliases["from"] == "source_concept"
    assert pack.role_aliases["to"] == "target_concept"
    assert pack.role_aliases["relationship"] == "relationship_label"


def test_whygame_minimal_strict_accepts_known_assertion() -> None:
    """The strict WhyGame profile should accept the adapter's fixed assertion shape."""

    profile = load_profile("whygame_minimal_strict", "0.1.0")
    outcome = validate_assertion_payload(
        {
            "predicate": "whygame:relationship",
            "roles": {
                "source_concept": [
                    {
                        "kind": "entity",
                        "entity_id": "ent:whygame:ai_integration",
                        "entity_type": "whygame:Concept",
                    }
                ],
                "target_concept": [
                    {
                        "kind": "entity",
                        "entity_id": "ent:whygame:military_modernization",
                        "entity_type": "whygame:Concept",
                    }
                ],
                "relationship_label": [
                    {
                        "kind": "value",
                        "value_kind": "string",
                        "value": "supports",
                    }
                ],
            },
        },
        profile=profile,
    )

    assert outcome.hard_errors == ()
    assert outcome.soft_violations == ()
    assert outcome.proposal_requests == ()

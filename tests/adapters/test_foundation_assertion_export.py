"""Tests for the Foundation Assertion IR export adapter."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))

from onto_canon6.adapters.foundation_assertion_export import (
    FoundationAssertion,
    promoted_assertion_to_foundation,
)
from onto_canon6.core.graph_models import PromotedGraphAssertionRecord
from onto_canon6.pipeline import ProfileRef


def _make_assertion(
    *,
    assertion_id: str = "asn_001",
    predicate: str = "oc:belongs_to_organization",
    roles: dict | None = None,
) -> PromotedGraphAssertionRecord:
    """Build a test promoted assertion with realistic normalized_body."""

    if roles is None:
        roles = {
            "subordinate": [
                {
                    "kind": "entity",
                    "entity_id": "ent:auto:test:org:alpha_unit",
                    "entity_type": "sumo:Organization",
                    "name": "Alpha unit",
                }
            ],
            "parent": [
                {
                    "kind": "entity",
                    "entity_id": "ent:auto:test:org:bravo_command",
                    "entity_type": "sumo:Organization",
                    "name": "Bravo command",
                }
            ],
        }
    return PromotedGraphAssertionRecord(
        assertion_id=assertion_id,
        source_candidate_id="cand_abc123",
        profile=ProfileRef(profile_id="psyop_seed", profile_version="0.1.0"),
        predicate=predicate,
        normalized_body={"predicate": predicate, "roles": roles},
        claim_text="Alpha unit reports to Bravo command",
        promoted_by="analyst@test",
        promoted_at="2026-03-23T00:00:00Z",
    )


def test_entity_filler_preserves_name_and_type() -> None:
    """Foundation IR must include entity name and type from normalized_body."""

    assertion = _make_assertion()
    result = promoted_assertion_to_foundation(assertion)

    assert result.assertion_id == "asn_001"
    assert result.predicate == "oc:belongs_to_organization"
    assert "subordinate" in result.roles
    assert "parent" in result.roles

    sub_filler = result.roles["subordinate"][0]
    assert sub_filler["kind"] == "entity"
    assert sub_filler["name"] == "Alpha unit"
    assert sub_filler["entity_type"] == "sumo:Organization"
    assert sub_filler["entity_id"] == "ent:auto:test:org:alpha_unit"


def test_value_filler_preserves_kind_and_normalized() -> None:
    """Foundation IR must preserve value filler structure."""

    roles = {
        "amount": [
            {
                "kind": "value",
                "value_kind": "money",
                "normalized": {"amount_decimal": "5000000", "currency": "GBP"},
                "raw": "£5 million",
            }
        ],
        "agent": [
            {
                "kind": "entity",
                "entity_id": "ent:org:test",
                "name": "Test Org",
                "entity_type": "sumo:Organization",
            }
        ],
    }
    assertion = _make_assertion(
        predicate="oc:fund_ongoing_support",
        roles=roles,
    )
    result = promoted_assertion_to_foundation(assertion)

    amount_filler = result.roles["amount"][0]
    assert amount_filler["kind"] == "value"
    assert amount_filler["value_kind"] == "money"
    assert amount_filler["normalized"]["amount_decimal"] == "5000000"
    assert amount_filler["raw"] == "£5 million"


def test_provenance_refs_includes_source_candidate() -> None:
    """Foundation IR provenance_refs should include source_candidate_id."""

    assertion = _make_assertion()
    result = promoted_assertion_to_foundation(assertion)

    assert "cand_abc123" in result.provenance_refs


def test_confidence_wired_when_provided() -> None:
    """Confidence from epistemic extension should appear in qualifiers."""

    assertion = _make_assertion()
    result = promoted_assertion_to_foundation(assertion, confidence=0.85)

    assert result.confidence == 0.85
    assert result.qualifiers["sys:confidence"] == 0.85


def test_confidence_absent_when_not_provided() -> None:
    """No confidence should produce empty qualifiers."""

    assertion = _make_assertion()
    result = promoted_assertion_to_foundation(assertion)

    assert result.confidence is None
    assert "sys:confidence" not in result.qualifiers


def test_roundtrip_to_json() -> None:
    """Foundation assertion must serialize cleanly to JSON."""

    assertion = _make_assertion()
    result = promoted_assertion_to_foundation(assertion, confidence=0.9)

    dumped = result.model_dump(exclude_none=True)
    assert isinstance(dumped, dict)
    assert dumped["assertion_id"] == "asn_001"
    assert isinstance(dumped["roles"], dict)
    assert len(dumped["provenance_refs"]) == 1

    # Verify it can be reconstructed.
    roundtripped = FoundationAssertion(**dumped)
    assert roundtripped.assertion_id == result.assertion_id
    assert roundtripped.predicate == result.predicate


def test_alias_lookup_enriches_entity_fillers() -> None:
    """Entity fillers should get alias_ids from the identity subsystem lookup."""

    assertion = _make_assertion()
    alias_lookup = {
        "ent:auto:test:org:alpha_unit": ["ent:auto:other:org:alpha_unit_v2"],
    }
    result = promoted_assertion_to_foundation(assertion, alias_lookup=alias_lookup)

    sub_filler = result.roles["subordinate"][0]
    assert "alias_ids" in sub_filler
    assert "ent:auto:other:org:alpha_unit_v2" in sub_filler["alias_ids"]

    # Parent entity has no aliases — alias_ids should be absent.
    parent_filler = result.roles["parent"][0]
    assert "alias_ids" not in parent_filler


def test_alias_lookup_none_is_backward_compatible() -> None:
    """When alias_lookup is None, no alias_ids are added."""

    assertion = _make_assertion()
    result = promoted_assertion_to_foundation(assertion, alias_lookup=None)

    sub_filler = result.roles["subordinate"][0]
    assert "alias_ids" not in sub_filler

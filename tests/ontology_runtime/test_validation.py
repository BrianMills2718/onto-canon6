"""Tests for the first local assertion-validation slice."""

from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))

from onto_canon6.ontology_runtime import clear_loader_caches, load_profile, validate_assertion_payload  # noqa: E402


def setup_function() -> None:
    """Reset loader caches so validation tests see local donor changes."""

    clear_loader_caches()


def test_default_profile_allows_unknown_predicate_without_findings() -> None:
    """Open mode should accept unknown predicates without emitting ontology findings."""

    profile = load_profile("default", "1.0.0")

    outcome = validate_assertion_payload(
        {
            "predicate": "oc:unknown_predicate_demo",
            "roles": {
                "subject": [
                    {
                        "entity_id": "ent:subject:1",
                        "entity_type": "oc:person",
                    }
                ]
            },
        },
        profile=profile,
    )

    assert not outcome.hard_errors
    assert not outcome.soft_violations
    assert not outcome.proposal_requests


def test_dodaf_profile_accepts_valid_assertion() -> None:
    """Closed DoDAF profile should accept a rule-conforming assertion."""

    profile = load_profile("dodaf", "0.1.0")

    outcome = validate_assertion_payload(
        {
            "predicate": "dodaf:activity_performs_resource",
            "roles": {
                "performer": [
                    {
                        "entity_id": "ent:performer:1",
                        "entity_type": "dm2:Performer",
                    }
                ],
                "activity": [
                    {
                        "entity_id": "ent:activity:1",
                        "entity_type": "dm2:OperationalActivity",
                    }
                ],
                "resource": [
                    {
                        "entity_id": "ent:resource:1",
                        "entity_type": "dm2:Resource",
                    }
                ],
            },
        },
        profile=profile,
    )

    assert not outcome.hard_errors
    assert not outcome.soft_violations
    assert outcome.type_checks_total == 3


def test_dodaf_profile_accepts_override_subtype() -> None:
    """Hierarchical DoDAF checks should honor donor type-hierarchy overrides."""

    profile = load_profile("dodaf", "0.1.0")

    outcome = validate_assertion_payload(
        {
            "predicate": "dodaf:service_supports_activity",
            "roles": {
                "service": [
                    {
                        "entity_id": "ent:service:1",
                        "entity_type": "dm2:CoalitionService",
                    }
                ],
                "activity": [
                    {
                        "entity_id": "ent:activity:1",
                        "entity_type": "dm2:OperationalActivity",
                    }
                ],
            },
        },
        profile=profile,
    )

    assert not outcome.hard_errors
    assert not outcome.soft_violations
    assert outcome.type_checks_total == 2


def test_dodaf_profile_rejects_unknown_predicate() -> None:
    """Closed mode should reject unknown predicates as hard validation errors."""

    profile = load_profile("dodaf", "0.1.0")

    outcome = validate_assertion_payload(
        {
            "predicate": "oc:unknown_predicate_demo",
            "roles": {
                "subject": [
                    {
                        "entity_id": "ent:subject:1",
                        "entity_type": "oc:person",
                    }
                ]
            },
        },
        profile=profile,
    )

    assert [finding.code for finding in outcome.hard_errors] == ["oc:profile_unknown_predicate"]
    assert not outcome.soft_violations
    assert not outcome.proposal_requests


def test_psyop_profile_generates_soft_unknown_predicate_proposal() -> None:
    """Mixed mode should soft-flag unknown predicates and emit a proposal request."""

    profile = load_profile("psyop_seed", "0.1.0")

    outcome = validate_assertion_payload(
        {
            "predicate": "oc:unknown_predicate_demo",
            "roles": {
                "subject": [
                    {
                        "entity_id": "ent:subject:1",
                        "entity_type": "oc:person",
                    }
                ]
            },
        },
        profile=profile,
    )

    assert not outcome.hard_errors
    assert [finding.code for finding in outcome.soft_violations] == ["oc:profile_unknown_predicate"]
    assert len(outcome.proposal_requests) == 1
    proposal = outcome.proposal_requests[0]
    assert proposal.kind == "predicate"
    assert proposal.value == "oc:unknown_predicate_demo"
    assert proposal.target_pack is not None
    assert proposal.target_pack.pack_id.endswith("__overlay")


def test_psyop_profile_reports_required_role_and_cardinality_violations() -> None:
    """Known rules should still enforce required roles and role cardinality."""

    profile = load_profile("psyop_seed", "0.1.0")

    outcome = validate_assertion_payload(
        {
            "predicate": "oc:belongs_to_organization",
            "roles": {
                "member": [
                    {
                        "entity_id": "ent:unit:1",
                        "entity_type": "oc:military_unit",
                    },
                    {
                        "entity_id": "ent:unit:2",
                        "entity_type": "oc:military_unit",
                    },
                ]
            },
        },
        profile=profile,
    )

    assert [finding.code for finding in outcome.hard_errors] == ["oc:profile_missing_required_role"]
    assert [finding.code for finding in outcome.soft_violations] == [
        "oc:profile_role_cardinality_violation",
        "oc:profile_role_cardinality_violation",
    ]


def test_psyop_profile_rejects_incompatible_entity_type() -> None:
    """Ontology-pack hierarchical checks should reject incompatible role filler types."""

    profile = load_profile("psyop_seed", "0.1.0")

    outcome = validate_assertion_payload(
        {
            "predicate": "oc:belongs_to_organization",
            "roles": {
                "member": [
                    {
                        "entity_id": "ent:person:1",
                        "entity_type": "oc:person",
                    }
                ],
                "organization": [
                    {
                        "entity_id": "ent:org:1",
                        "entity_type": "oc:military_organization",
                    }
                ],
            },
        },
        profile=profile,
    )

    # role_type_violation is soft (reviewer decides, not auto-reject)
    assert not outcome.hard_errors
    assert [finding.code for finding in outcome.soft_violations] == ["oc:profile_role_type_violation"]


def test_psyop_profile_rejects_wrong_value_kind() -> None:
    """Value-typed roles should enforce the donor-declared value kind exactly."""

    profile = load_profile("psyop_seed", "0.1.0")

    outcome = validate_assertion_payload(
        {
            "predicate": "oc:hold_command_role",
            "roles": {
                "commander": [
                    {
                        "entity_id": "ent:person:olson",
                        "entity_type": "oc:person",
                    }
                ],
                "organization": [
                    {
                        "entity_id": "ent:org:ussocom",
                        "entity_type": "oc:military_organization",
                    }
                ],
                "role_title": [
                    {
                        "kind": "value",
                        "value_kind": "time",
                    }
                ],
            },
        },
        profile=profile,
    )

    assert [finding.code for finding in outcome.hard_errors] == [
        "oc:profile_role_value_kind_violation"
    ]
    assert not outcome.soft_violations

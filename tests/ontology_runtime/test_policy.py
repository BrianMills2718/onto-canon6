"""Tests for first-slice ontology-runtime policy semantics."""

from __future__ import annotations

from pathlib import Path
import sys

import pytest
from pydantic import ValidationError

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))

from onto_canon6.ontology_runtime import (  # noqa: E402
    OntologyPolicy,
    PackRef,
    UnknownItemPolicy,
    build_proposal_request,
    decide_unknown_item,
)


def test_open_mode_allows_unknown_predicates_by_default() -> None:
    """Open mode should allow undeclared items without proposal routing."""

    decision = decide_unknown_item(
        policy=OntologyPolicy(mode="open"),
        kind="predicate",
        value="oc:unknown_predicate_demo",
    )

    assert decision.action == "allow"
    assert decision.target_pack is None


def test_closed_mode_rejects_unknown_predicates_by_default() -> None:
    """Closed mode should reject undeclared items deterministically."""

    decision = decide_unknown_item(
        policy=OntologyPolicy(mode="closed"),
        kind="predicate",
        value="oc:unknown_predicate_demo",
    )

    assert decision.action == "reject"
    assert decision.target_pack is None


def test_mixed_mode_proposes_unknown_predicates_by_default() -> None:
    """Mixed mode should route unknown items into proposal flow."""

    decision = decide_unknown_item(
        policy=OntologyPolicy(mode="mixed", proposal_policy="allow"),
        kind="predicate",
        value="oc:unknown_predicate_demo",
    )

    assert decision.action == "propose"
    assert decision.target_pack is None


def test_explicit_override_can_propose_to_overlay_from_closed_mode() -> None:
    """Explicit per-kind policy should override the mode default when configured."""

    policy = OntologyPolicy(
        mode="closed",
        proposal_policy="allow",
        overlay_target=PackRef(pack_id="project_local_overlay", pack_version="0.1.0"),
        unknown_items=UnknownItemPolicy(predicate="propose"),
    )

    decision = decide_unknown_item(
        policy=policy,
        kind="predicate",
        value="oc:unknown_predicate_demo",
    )

    assert decision.action == "propose"
    assert decision.target_pack == PackRef(
        pack_id="project_local_overlay",
        pack_version="0.1.0",
    )


def test_build_proposal_request_requires_propose_action() -> None:
    """Proposal request construction should fail loudly on non-proposal actions."""

    decision = decide_unknown_item(
        policy=OntologyPolicy(mode="open"),
        kind="predicate",
        value="oc:unknown_predicate_demo",
    )

    with pytest.raises(ValueError, match="cannot build proposal request"):
        build_proposal_request(decision)


def test_mixed_mode_requires_allowing_proposals() -> None:
    """Mixed mode should reject contradictory reject-only proposal policy."""

    with pytest.raises(ValidationError, match="mixed mode requires proposal_policy='allow'"):
        OntologyPolicy(mode="mixed", proposal_policy="reject")


def test_explicit_propose_requires_proposal_policy_allow() -> None:
    """Propose actions should fail validation when proposal routing is disabled."""

    with pytest.raises(
        ValidationError,
        match="unknown item actions cannot propose when proposal_policy='reject'",
    ):
        OntologyPolicy(
            mode="closed",
            proposal_policy="reject",
            unknown_items=UnknownItemPolicy(predicate="propose"),
        )

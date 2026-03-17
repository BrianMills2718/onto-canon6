"""Deterministic unknown-item policy resolution for ontology runtime.

The successor should make ontology policy behavior inspectable before the rest
of the system is rebuilt. This module resolves the current policy for an unknown
ontology item without assuming persistence, extraction, or workflow machinery.
"""

from __future__ import annotations

from .contracts import (
    OntologyPolicy,
    ProposalRequest,
    UnknownItemAction,
    UnknownItemDecision,
    UnknownItemKind,
)


def decide_unknown_item(
    *,
    policy: OntologyPolicy,
    kind: UnknownItemKind,
    value: str,
) -> UnknownItemDecision:
    """Resolve how one unknown ontology item should be handled.

    Explicit per-kind overrides win. Otherwise the action comes from ontology
    mode:

    - `open` -> allow
    - `closed` -> reject
    - `mixed` -> propose
    """

    normalized_value = value.strip()
    if not normalized_value:
        raise ValueError("value must be non-empty")

    action = policy.unknown_items.action_for(kind)
    reason_prefix = "explicit unknown-item policy"
    if action is None:
        action = _default_action_for_mode(policy.mode)
        reason_prefix = f"default ontology mode '{policy.mode}'"

    target_pack = policy.overlay_target if action == "propose" else None
    return UnknownItemDecision(
        kind=kind,
        value=normalized_value,
        action=action,
        reason=f"{reason_prefix} resolved action '{action}' for {kind}",
        target_pack=target_pack,
    )


def build_proposal_request(decision: UnknownItemDecision) -> ProposalRequest:
    """Build a proposal request from a resolved unknown-item decision.

    This fails loudly when called for non-proposal actions so higher layers do
    not silently treat `allow` or `reject` as persisted governance outcomes.
    """

    if decision.action != "propose":
        raise ValueError(f"cannot build proposal request for action '{decision.action}'")
    return ProposalRequest(
        kind=decision.kind,
        value=decision.value,
        reason=decision.reason,
        target_pack=decision.target_pack,
    )


def _default_action_for_mode(mode: str) -> UnknownItemAction:
    if mode == "open":
        return "allow"
    if mode == "closed":
        return "reject"
    if mode == "mixed":
        return "propose"
    raise ValueError(f"unsupported ontology mode: {mode}")


__all__ = ["build_proposal_request", "decide_unknown_item"]

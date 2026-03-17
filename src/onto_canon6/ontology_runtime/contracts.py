"""Typed contracts for the first ontology-runtime slice.

These models define the minimum architectural surface needed to reason about
ontology usage before the rest of the successor is built out:

- which pack or overlay is being targeted;
- which ontology mode is active;
- how unknown items should be handled;
- which sink receives proposal-worthy additions.
"""

from __future__ import annotations

from typing import Literal, Protocol

from pydantic import BaseModel, ConfigDict, Field, model_validator

OntologyMode = Literal["open", "closed", "mixed"]
ProposalPolicy = Literal["reject", "allow"]
UnknownItemKind = Literal["predicate", "role", "entity_type", "value_kind"]
UnknownItemAction = Literal["allow", "reject", "propose"]


class PackRef(BaseModel):
    """Reference one versioned ontology pack or overlay target."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    pack_id: str = Field(min_length=1)
    pack_version: str = Field(min_length=1)


class UnknownItemPolicy(BaseModel):
    """Declare how unknown ontology items are handled by kind.

    The policy is intentionally small. It allows the successor to override the
    default mode-based behavior without introducing a large configuration
    framework before the first slice is proven.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    default_action: UnknownItemAction | None = None
    predicate: UnknownItemAction | None = None
    role: UnknownItemAction | None = None
    entity_type: UnknownItemAction | None = None
    value_kind: UnknownItemAction | None = None

    def action_for(self, kind: UnknownItemKind) -> UnknownItemAction | None:
        """Return the explicit action for one kind or the policy default."""

        if kind == "predicate":
            explicit = self.predicate
        elif kind == "role":
            explicit = self.role
        elif kind == "entity_type":
            explicit = self.entity_type
        else:
            explicit = self.value_kind
        if explicit is not None:
            return explicit
        return self.default_action

    def declares_proposals(self) -> bool:
        """Return `True` when any configured branch proposes unknown items."""

        return "propose" in {
            action
            for action in (
                self.default_action,
                self.predicate,
                self.role,
                self.entity_type,
                self.value_kind,
            )
            if action is not None
        }


class OntologyPolicy(BaseModel):
    """Describe how the runtime uses ontology content and grows beyond it."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    mode: OntologyMode
    proposal_policy: ProposalPolicy = "reject"
    unknown_items: UnknownItemPolicy = Field(default_factory=UnknownItemPolicy)
    overlay_target: PackRef | None = None

    @model_validator(mode="after")
    def validate_consistency(self) -> "OntologyPolicy":
        """Reject contradictory mixed-mode and proposal-sink configurations."""

        if self.mode == "mixed" and self.proposal_policy != "allow":
            raise ValueError("mixed mode requires proposal_policy='allow'")
        if self.unknown_items.declares_proposals() and self.proposal_policy != "allow":
            raise ValueError("unknown item actions cannot propose when proposal_policy='reject'")
        if self.overlay_target is not None and self.proposal_policy != "allow":
            raise ValueError("overlay_target requires proposal_policy='allow'")
        return self


class UnknownItemDecision(BaseModel):
    """Resolved action for one unknown ontology item."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: UnknownItemKind
    value: str = Field(min_length=1)
    action: UnknownItemAction
    reason: str = Field(min_length=1)
    target_pack: PackRef | None = None


class ProposalRequest(BaseModel):
    """Proposal-ready representation of one unknown ontology item."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: UnknownItemKind
    value: str = Field(min_length=1)
    reason: str = Field(min_length=1)
    target_pack: PackRef | None = None


class ProposalSink(Protocol):
    """Minimal protocol for recording proposal-worthy unknown ontology items."""

    def record(self, request: ProposalRequest) -> str:
        """Persist one proposal request and return its stable identifier."""


__all__ = [
    "OntologyMode",
    "OntologyPolicy",
    "PackRef",
    "ProposalPolicy",
    "ProposalRequest",
    "ProposalSink",
    "UnknownItemAction",
    "UnknownItemDecision",
    "UnknownItemKind",
    "UnknownItemPolicy",
]

"""Typed models for the first stable-identity slice.

Phase 12 starts with identities over promoted graph entities only. The models
here make three concerns explicit:

1. the stable local identity record;
2. explicit membership of promoted entity ids within that identity;
3. explicit external-reference state, including unresolved work.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from .graph_models import PromotedGraphEntityRecord

IdentityKind = Literal["entity"]
IdentityMembershipKind = Literal["canonical", "alias"]
ExternalReferenceStatus = Literal["attached", "unresolved"]


class GraphIdentityRecord(BaseModel):
    """One stable local identity record over promoted entities."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    identity_id: str = Field(min_length=1)
    identity_kind: IdentityKind
    display_label: str | None = None
    created_by: str = Field(min_length=1)
    created_at: str = Field(min_length=1)


class GraphIdentityMembershipRecord(BaseModel):
    """One explicit membership of a promoted entity within an identity."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    identity_id: str = Field(min_length=1)
    entity_id: str = Field(min_length=1)
    membership_kind: IdentityMembershipKind
    attached_by: str = Field(min_length=1)
    attached_at: str = Field(min_length=1)


class GraphExternalReferenceRecord(BaseModel):
    """One explicit external-reference attachment or unresolved record."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    reference_id: str = Field(min_length=1)
    identity_id: str = Field(min_length=1)
    provider: str = Field(min_length=1)
    reference_status: ExternalReferenceStatus
    external_id: str | None = None
    reference_label: str | None = None
    unresolved_note: str | None = None
    attached_by: str = Field(min_length=1)
    attached_at: str = Field(min_length=1)


class IdentityBundleRecord(BaseModel):
    """Bundle one identity with its memberships, promoted entities, and refs."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    identity: GraphIdentityRecord
    memberships: tuple[GraphIdentityMembershipRecord, ...] = ()
    promoted_entities: tuple[PromotedGraphEntityRecord, ...] = ()
    external_references: tuple[GraphExternalReferenceRecord, ...] = ()


__all__ = [
    "ExternalReferenceStatus",
    "GraphExternalReferenceRecord",
    "GraphIdentityMembershipRecord",
    "GraphIdentityRecord",
    "IdentityBundleRecord",
    "IdentityKind",
    "IdentityMembershipKind",
]

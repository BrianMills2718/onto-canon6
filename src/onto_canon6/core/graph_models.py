"""Typed models for the first canonical-graph recovery slice.

This module defines the smallest durable graph target for Phase 11:

1. promoted graph assertions created from accepted candidates;
2. promoted graph entities materialized only from explicit entity fillers;
3. typed role-filler rows that preserve the promoted assertion structure
   without flattening everything into a single JSON blob.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, JsonValue

from ..pipeline import ProfileRef

PromotedGraphFillerKind = Literal["entity", "value"]


class PromotedGraphEntityRecord(BaseModel):
    """One materialized graph-entity row for an explicit promoted entity id."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    entity_id: str = Field(min_length=1)
    entity_type: str | None = None
    first_candidate_id: str = Field(min_length=1)
    created_at: str = Field(min_length=1)


class PromotedGraphRoleFillerRecord(BaseModel):
    """One typed role filler attached to a promoted assertion.

    The first graph slice only distinguishes:

    1. entity fillers, which point at promoted graph entities;
    2. value fillers, which preserve the promoted literal/value payload.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    assertion_id: str = Field(min_length=1)
    role_id: str = Field(min_length=1)
    filler_index: int = Field(ge=0)
    filler_kind: PromotedGraphFillerKind
    entity_id: str | None = None
    entity_type: str | None = None
    value_kind: str | None = None
    value: JsonValue | None = None


class PromotedGraphAssertionRecord(BaseModel):
    """One durable promoted assertion derived from an accepted candidate."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    assertion_id: str = Field(min_length=1)
    source_candidate_id: str = Field(min_length=1)
    profile: ProfileRef
    predicate: str = Field(min_length=1)
    normalized_body: dict[str, JsonValue]
    claim_text: str | None = None
    promoted_by: str = Field(min_length=1)
    promoted_at: str = Field(min_length=1)


class CanonicalGraphPromotionResult(BaseModel):
    """Return one promoted assertion plus its role fillers and materialized entities."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    assertion: PromotedGraphAssertionRecord
    role_fillers: tuple[PromotedGraphRoleFillerRecord, ...] = ()
    entities: tuple[PromotedGraphEntityRecord, ...] = ()


__all__ = [
    "CanonicalGraphPromotionResult",
    "PromotedGraphAssertionRecord",
    "PromotedGraphEntityRecord",
    "PromotedGraphFillerKind",
    "PromotedGraphRoleFillerRecord",
]

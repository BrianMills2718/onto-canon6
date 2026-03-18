"""Typed models for the Phase 13 semantic canonicalization slice.

This module keeps semantic repair explicit and bounded. It models:

1. persisted recanonicalization events over promoted assertions;
2. typed results returned by the semantic repair service.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, JsonValue

from ..ontology_runtime import ValidationOutcome
from .graph_models import PromotedGraphAssertionRecord, PromotedGraphRoleFillerRecord

SemanticCanonicalizationStatus = Literal["already_canonical", "rewritten"]


class PromotedGraphRecanonicalizationEventRecord(BaseModel):
    """One persisted semantic repair event over a promoted assertion.

    The event stores before and after semantic snapshots so later operators can
    audit exactly what changed and why. This keeps repair explicit rather than
    silently mutating graph state.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    event_id: str = Field(min_length=1)
    assertion_id: str = Field(min_length=1)
    actor_id: str = Field(min_length=1)
    reason: str | None = None
    before_predicate: str = Field(min_length=1)
    before_body: dict[str, JsonValue]
    after_predicate: str = Field(min_length=1)
    after_body: dict[str, JsonValue]
    created_at: str = Field(min_length=1)


class SemanticCanonicalizationResult(BaseModel):
    """Return the current promoted assertion state after semantic repair.

    The result reports both the rewritten graph view and the validation outcome
    that justified persisting it. No-op canonicalization remains explicit so
    operators can distinguish "already canonical" from "rewritten".
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    status: SemanticCanonicalizationStatus
    assertion: PromotedGraphAssertionRecord
    role_fillers: tuple[PromotedGraphRoleFillerRecord, ...] = ()
    validation_outcome: ValidationOutcome
    event: PromotedGraphRecanonicalizationEventRecord | None = None


__all__ = [
    "PromotedGraphRecanonicalizationEventRecord",
    "SemanticCanonicalizationResult",
    "SemanticCanonicalizationStatus",
]

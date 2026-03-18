"""Typed WhyGame adapter contracts for the Phase 14 recovery slice.

The successor only recovers the smallest useful WhyGame path:

1. RELATIONSHIP facts become candidate assertions;
2. the adapter remains explicit and typed at the pipeline boundary;
3. provenance stays visible through the existing candidate and artifact
   surfaces rather than through a second runtime.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, JsonValue

from ..artifacts import ArtifactRecord, CandidateArtifactLinkRecord
from ..pipeline import CandidateSubmissionResult, ProfileRef

WhyGameFactType = Literal["RELATIONSHIP"]


class WhyGameRelationshipRoles(BaseModel):
    """Capture the role triple emitted by WhyGame relationship facts."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    from_: str = Field(alias="from", min_length=1)
    to: str = Field(min_length=1)
    relationship: str = Field(min_length=1)


class WhyGameRelationshipFact(BaseModel):
    """Represent the minimal WhyGame relationship-fact shape accepted today.

    The adapter fails loudly on non-relationship fact types so the recovered
    slice stays explicit about what it does and does not import.
    """

    model_config = ConfigDict(extra="forbid", frozen=True, populate_by_name=True)

    id: str = Field(min_length=1)
    fact_type: WhyGameFactType
    roles: WhyGameRelationshipRoles
    context: dict[str, JsonValue] = Field(default_factory=dict)
    confidence: float = Field(ge=0.0, le=1.0, default=1.0)
    metadata: dict[str, JsonValue] = Field(default_factory=dict)
    created_at: str | None = None


class WhyGameImportRequest(BaseModel):
    """Define one explicit WhyGame-to-candidate import request.

    This request intentionally keeps the adapter narrow:

    1. one explicit profile controls validation;
    2. facts remain relationship-only;
    3. optional artifact registration remains visible and configurable.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    profile: ProfileRef
    submitted_by: str = Field(min_length=1)
    source_ref: str = Field(min_length=1)
    source_label: str | None = None
    source_metadata: dict[str, JsonValue] = Field(default_factory=dict)
    facts: tuple[WhyGameRelationshipFact, ...] = Field(min_length=1)
    register_artifact: bool = True
    artifact_uri: str | None = None
    artifact_label: str | None = None


class WhyGameImportResult(BaseModel):
    """Return the persisted results of one WhyGame import request."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    profile: ProfileRef
    artifact: ArtifactRecord | None = None
    submissions: tuple[CandidateSubmissionResult, ...] = ()
    artifact_links: tuple[CandidateArtifactLinkRecord, ...] = ()


__all__ = [
    "WhyGameFactType",
    "WhyGameImportRequest",
    "WhyGameImportResult",
    "WhyGameRelationshipFact",
    "WhyGameRelationshipRoles",
]

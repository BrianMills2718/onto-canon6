"""Typed models for the Phase 8 artifact-lineage slice.

The first slice is intentionally narrow:

1. artifacts are explicit first-class records;
2. candidate assertions are the first link target;
3. lineage between artifacts stays separate from review/runtime policy;
4. accepted-assertion lineage is derived later by traversal rather than copied
   into a second storage path.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, JsonValue

from ..pipeline import CandidateAssertionRecord

ArtifactKind = Literal["source", "derived_dataset", "analysis_result"]
ArtifactLineageRelationship = Literal["derived_from"]
CandidateArtifactSupportKind = Literal[
    "quoted_from",
    "supported_by_dataset",
    "supported_by_analysis",
]


class ArtifactRecord(BaseModel):
    """Persisted artifact metadata for provenance and lineage traversal.

    The current slice stores only the minimum needed to explain where evidence
    came from: kind, URI or path-like locator, optional label, open metadata,
    and an optional exact fingerprint for future deduplication.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    artifact_id: str = Field(min_length=1)
    artifact_kind: ArtifactKind
    uri: str = Field(min_length=1)
    label: str | None = None
    metadata: dict[str, JsonValue] = Field(default_factory=dict)
    fingerprint: str | None = None
    created_at: str = Field(min_length=1)


class ArtifactLineageEdge(BaseModel):
    """Record one explicit artifact-to-artifact lineage relationship."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    parent_artifact_id: str = Field(min_length=1)
    child_artifact_id: str = Field(min_length=1)
    relationship_type: ArtifactLineageRelationship


class CandidateArtifactLinkRecord(BaseModel):
    """Record one explicit support link from a candidate to an artifact."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    candidate_id: str = Field(min_length=1)
    artifact_id: str = Field(min_length=1)
    support_kind: CandidateArtifactSupportKind
    reference_detail: str | None = None
    created_at: str = Field(min_length=1)


class CandidateLineageReport(BaseModel):
    """Bundle one candidate with its direct artifact links and artifact lineage.

    This report shape is intentionally small and inspectable. It answers:

    1. which artifacts directly support the candidate;
    2. which ancestor artifacts explain how those supporting artifacts were
       produced;
    3. which candidate record remains the review-governed subject of those
       links.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    candidate: CandidateAssertionRecord
    direct_artifact_links: tuple[CandidateArtifactLinkRecord, ...] = ()
    artifacts: tuple[ArtifactRecord, ...] = ()
    lineage_edges: tuple[ArtifactLineageEdge, ...] = ()

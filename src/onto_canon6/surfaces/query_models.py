"""Typed contracts for the first read-only promoted-knowledge query surface.

The first query slice is intentionally narrow. These models describe exactly
the five supported read operations over promoted state:

1. entity search;
2. entity detail;
3. promoted assertion search;
4. promoted assertion detail; and
5. evidence/provenance lookup.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ..artifacts import ArtifactLineageEdge, ArtifactRecord, CandidateArtifactLinkRecord
from ..core import CanonicalGraphPromotionResult, IdentityBundleRecord, PromotedGraphEntityRecord
from ..extensions.epistemic import PromotedAssertionEpistemicReport, PromotedAssertionEpistemicStatus
from ..pipeline import CandidateAssertionRecord, EvidenceSpan, SourceArtifactRef

EntityMatchReason = Literal["canonical_exact", "alias_exact", "prefix", "substring"]


class EntitySearchRequest(BaseModel):
    """Search for promoted entities by canonical or alias name."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    query: str = Field(min_length=1)
    entity_type: str | None = None
    limit: int = Field(default=20, ge=1, le=200)


class EntitySearchResult(BaseModel):
    """One matched entity result from the read-only search surface."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    identity_id: str | None = None
    entity_id: str = Field(min_length=1)
    display_label: str = Field(min_length=1)
    entity_type: str | None = None
    match_reason: EntityMatchReason


class GetEntityRequest(BaseModel):
    """Fetch one entity detail by entity or identity id."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    entity_id: str | None = None
    identity_id: str | None = None

    @model_validator(mode="after")
    def _require_exactly_one_identifier(self) -> "GetEntityRequest":
        """Require exactly one lookup identifier."""

        if bool(self.entity_id) == bool(self.identity_id):
            raise ValueError("provide exactly one of entity_id or identity_id")
        return self


class AssertionSearchRequest(BaseModel):
    """Search promoted assertions by predicate, entity, or claim text."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    predicate: str | None = None
    entity_id: str | None = None
    text_query: str | None = None
    limit: int = Field(default=20, ge=1, le=200)

    @model_validator(mode="after")
    def _require_at_least_one_filter(self) -> "AssertionSearchRequest":
        """Require at least one search filter."""

        if not any((self.predicate, self.entity_id, self.text_query)):
            raise ValueError(
                "at least one of predicate, entity_id, or text_query must be provided"
            )
        return self


class AssertionSearchResult(BaseModel):
    """One summary result from promoted-assertion search."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    assertion_id: str = Field(min_length=1)
    predicate: str = Field(min_length=1)
    claim_text: str | None = None
    entity_ids: tuple[str, ...] = ()
    confidence_score: float | None = None
    epistemic_status: PromotedAssertionEpistemicStatus | None = None


class GetPromotedAssertionRequest(BaseModel):
    """Fetch one promoted assertion detail by identifier."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    assertion_id: str = Field(min_length=1)


class GetEvidenceRequest(BaseModel):
    """Fetch one evidence/provenance bundle by promoted assertion identifier."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    assertion_id: str = Field(min_length=1)


class EvidenceBundle(BaseModel):
    """Evidence and provenance attached to one promoted assertion."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    assertion_id: str = Field(min_length=1)
    candidate: CandidateAssertionRecord
    source_artifact: SourceArtifactRef
    claim_text: str | None = None
    source_text: str | None = None
    evidence_spans: tuple[EvidenceSpan, ...] = ()
    artifact_links: tuple[CandidateArtifactLinkRecord, ...] = ()
    artifacts: tuple[ArtifactRecord, ...] = ()
    lineage_edges: tuple[ArtifactLineageEdge, ...] = ()


class EntityDetail(BaseModel):
    """Detailed promoted-entity view with identity and linked assertion context."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    entity: PromotedGraphEntityRecord
    display_label: str = Field(min_length=1)
    names: tuple[str, ...] = ()
    identity_bundle: IdentityBundleRecord | None = None
    linked_assertions: tuple[AssertionSearchResult, ...] = ()


class PromotedAssertionDetail(BaseModel):
    """Detailed promoted-assertion view for query and browse workflows."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    promotion: CanonicalGraphPromotionResult
    source_candidate: CandidateAssertionRecord
    epistemic_report: PromotedAssertionEpistemicReport
    evidence: EvidenceBundle


__all__ = [
    "AssertionSearchRequest",
    "AssertionSearchResult",
    "EntityDetail",
    "EntityMatchReason",
    "EntitySearchRequest",
    "EntitySearchResult",
    "EvidenceBundle",
    "GetEntityRequest",
    "GetEvidenceRequest",
    "GetPromotedAssertionRequest",
    "PromotedAssertionDetail",
]

"""Typed contracts for the read-only promoted-knowledge query surface.

The first query slice is intentionally narrow. These models describe browse,
search, and detail operations over promoted state without exposing raw storage
rows as the public contract.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ..artifacts import ArtifactLineageEdge, ArtifactRecord, CandidateArtifactLinkRecord
from ..core import (
    CanonicalGraphPromotionResult,
    ExternalReferenceStatus,
    IdentityBundleRecord,
    PromotedGraphEntityRecord,
)
from ..extensions.epistemic import PromotedAssertionEpistemicReport, PromotedAssertionEpistemicStatus
from ..pipeline import CandidateAssertionRecord, EvidenceSpan, SourceArtifactRef

EntityMatchReason = Literal[
    "canonical_exact",
    "alias_exact",
    "external_id_exact",
    "reference_label_exact",
    "prefix",
    "external_prefix",
    "substring",
    "external_substring",
]


class EntityBrowseRequest(BaseModel):
    """Browse promoted entities in deterministic order."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    entity_type: str | None = None
    has_identity: bool | None = None
    provider: str | None = None
    reference_status: ExternalReferenceStatus | None = None
    limit: int = Field(default=50, ge=1, le=200)


class EntityBrowseResult(BaseModel):
    """One summary result from deterministic entity browsing."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    identity_id: str | None = None
    entity_id: str = Field(min_length=1)
    display_label: str = Field(min_length=1)
    entity_type: str | None = None
    linked_assertion_count: int = Field(ge=0)
    has_identity: bool
    attached_external_reference_count: int = Field(ge=0)
    unresolved_external_reference_count: int = Field(ge=0)
    external_reference_providers: tuple[str, ...] = ()


class EntitySearchRequest(BaseModel):
    """Search for promoted entities by canonical, alias, or external-reference text."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    query: str = Field(min_length=1)
    entity_type: str | None = None
    provider: str | None = None
    reference_status: ExternalReferenceStatus | None = None
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


class AssertionBrowseRequest(BaseModel):
    """Browse promoted assertions with optional deterministic filters."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    predicate: str | None = None
    entity_id: str | None = None
    source_ref: str | None = None
    source_kind: str | None = None
    limit: int = Field(default=50, ge=1, le=200)


class AssertionSearchRequest(BaseModel):
    """Search promoted assertions by predicate, entity, claim text, or source."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    predicate: str | None = None
    entity_id: str | None = None
    text_query: str | None = None
    source_ref: str | None = None
    source_kind: str | None = None
    limit: int = Field(default=20, ge=1, le=200)

    @model_validator(mode="after")
    def _require_at_least_one_filter(self) -> "AssertionSearchRequest":
        """Require at least one search filter."""

        if not any((self.predicate, self.entity_id, self.text_query, self.source_ref, self.source_kind)):
            raise ValueError(
                "at least one of predicate, entity_id, text_query, source_ref, or source_kind must be provided"
            )
        return self


class AssertionSearchResult(BaseModel):
    """One summary result from promoted-assertion browse or search."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    assertion_id: str = Field(min_length=1)
    source_candidate_id: str = Field(min_length=1)
    predicate: str = Field(min_length=1)
    claim_text: str | None = None
    entity_ids: tuple[str, ...] = ()
    source_ref: str = Field(min_length=1)
    source_kind: str = Field(min_length=1)
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
    "AssertionBrowseRequest",
    "AssertionSearchRequest",
    "AssertionSearchResult",
    "EntityBrowseRequest",
    "EntityBrowseResult",
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

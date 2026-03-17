"""Typed models for the review-oriented pipeline slice.

These models separate three concerns that were intentionally collapsed during
Phase 1 to keep the first proving slice small:

1. validation outcome, which records what ontology validation concluded;
2. candidate review state, which records what a reviewer decided to do next;
3. provenance, which records where a candidate came from and who submitted it.

The current slice still keeps the workflow narrow:

- candidate assertions are persisted as immutable payload snapshots;
- text-grounded imports can attach source text, claim glosses, and evidence
  spans without changing the core review flow;
- validation findings remain immutable;
- candidate and proposal reviews are each single-decision records;
- report surfaces consume these typed records instead of ad hoc dicts.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, JsonValue, model_validator

from ..ontology_runtime import PackRef, UnknownItemKind, ValidationFinding, ValidationOutcome

CandidateValidationStatus = Literal["valid", "invalid", "needs_review"]
CandidateReviewStatus = Literal["pending_review", "accepted", "rejected"]
CandidateReviewDecision = Literal["accepted", "rejected"]
ProposalStatus = Literal["pending", "accepted", "rejected"]
ProposalReviewDecision = Literal["accepted", "rejected"]
ProposalAcceptancePolicy = Literal["record_only", "apply_to_overlay"]
ProposalApplicationStatus = Literal[
    "not_requested",
    "recorded",
    "pending_overlay_apply",
    "applied_to_overlay",
]


class ProfileRef(BaseModel):
    """Identify the validation profile used for a candidate or proposal."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    profile_id: str = Field(min_length=1)
    profile_version: str = Field(min_length=1)


class SourceArtifactRef(BaseModel):
    """Identify one source artifact and optionally keep its local text.

    The current slice still stores source text inline with the candidate review
    workflow because it is the simplest way to keep span verification and
    notebook inspection explicit. Later slices may deduplicate larger artifacts
    behind a separate store if the current representation becomes too heavy.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    source_kind: str = Field(min_length=1)
    source_ref: str = Field(min_length=1)
    source_label: str | None = None
    source_metadata: dict[str, JsonValue] = Field(default_factory=dict)
    content_text: str | None = None


class EvidenceSpan(BaseModel):
    """Record one exact supporting span within a source artifact.

    The current phase uses character offsets plus exact text so the importer
    can verify that an extractor's proposed support actually exists in the
    underlying source text. Multiple span rows allow one candidate assertion to
    be grounded in non-adjacent portions of the source.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    start_char: int = Field(ge=0)
    end_char: int = Field(gt=0)
    text: str = Field(min_length=1)

    @model_validator(mode="after")
    def _validate_offsets(self) -> "EvidenceSpan":
        """Require strictly increasing offsets for one span."""

        if self.end_char <= self.start_char:
            raise ValueError("end_char must be greater than start_char")
        return self


class CandidateProvenance(BaseModel):
    """Record where a candidate came from and who submitted it.

    The provenance surface intentionally stays open enough to support notebook,
    batch-import, and future text-grounded producer ingestion without
    pretending the project already knows every future provenance shape.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    submitted_by: str = Field(min_length=1)
    source_artifact: SourceArtifactRef

    @property
    def source_kind(self) -> str:
        """Expose the source kind without forcing callers to unwrap the artifact."""

        return self.source_artifact.source_kind

    @property
    def source_ref(self) -> str:
        """Expose the source reference without forcing callers to unwrap the artifact."""

        return self.source_artifact.source_ref

    @property
    def source_label(self) -> str | None:
        """Expose the source label without forcing callers to unwrap the artifact."""

        return self.source_artifact.source_label

    @property
    def source_metadata(self) -> dict[str, JsonValue]:
        """Expose the source metadata without forcing callers to unwrap the artifact."""

        return self.source_artifact.source_metadata

    @property
    def content_text(self) -> str | None:
        """Expose the optional source text without forcing callers to unwrap the artifact."""

        return self.source_artifact.content_text


class CandidateAssertionImport(BaseModel):
    """Typed import contract for one candidate assertion submission.

    This contract is the first Phase 4 boundary. It keeps the existing review
    path intact while making text-grounded imports explicit:

    - the candidate payload is still ontology-shaped machine-readable data;
    - the source artifact remains primary;
    - evidence spans and optional claim text travel with the candidate.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    profile: ProfileRef
    payload: dict[str, JsonValue]
    submitted_by: str = Field(min_length=1)
    source_artifact: SourceArtifactRef
    evidence_spans: tuple[EvidenceSpan, ...] = ()
    claim_text: str | None = None


class PersistedValidationSnapshot(BaseModel):
    """Persistable subset of one validation result.

    Proposal requests are intentionally excluded because proposal persistence is
    tracked explicitly through proposal records and candidate-proposal links.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    hard_errors: tuple[ValidationFinding, ...] = ()
    soft_violations: tuple[ValidationFinding, ...] = ()
    type_checks_total: int = Field(default=0, ge=0)
    type_checks_unknown: int = Field(default=0, ge=0)

    @classmethod
    def from_outcome(cls, outcome: ValidationOutcome) -> "PersistedValidationSnapshot":
        """Build a persistable snapshot from a live validation outcome."""

        return cls(
            hard_errors=outcome.hard_errors,
            soft_violations=outcome.soft_violations,
            type_checks_total=outcome.type_checks_total,
            type_checks_unknown=outcome.type_checks_unknown,
        )

    @property
    def has_hard_errors(self) -> bool:
        """Return `True` when any hard errors were recorded."""

        return bool(self.hard_errors)

    @property
    def has_soft_violations(self) -> bool:
        """Return `True` when any soft violations were recorded."""

        return bool(self.soft_violations)


class CandidateReviewRecord(BaseModel):
    """Immutable review decision recorded against one candidate assertion."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    review_id: str = Field(min_length=1)
    candidate_id: str = Field(min_length=1)
    decision: CandidateReviewDecision
    actor_id: str = Field(min_length=1)
    note_text: str | None = None
    created_at: str = Field(min_length=1)


class ProposalReviewRecord(BaseModel):
    """Immutable review decision recorded against one proposal."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    decision_id: str = Field(min_length=1)
    proposal_id: str = Field(min_length=1)
    decision: ProposalReviewDecision
    actor_id: str = Field(min_length=1)
    note_text: str | None = None
    acceptance_policy: ProposalAcceptancePolicy
    application_status: ProposalApplicationStatus
    created_at: str = Field(min_length=1)


class OverlayApplicationRecord(BaseModel):
    """Immutable audit record for one explicit overlay application step."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    application_id: str = Field(min_length=1)
    proposal_id: str = Field(min_length=1)
    profile: ProfileRef
    overlay_pack: PackRef
    proposal_kind: UnknownItemKind
    applied_value: str = Field(min_length=1)
    content_path: str = Field(min_length=1)
    applied_by: str = Field(min_length=1)
    created_at: str = Field(min_length=1)


class ProposalRecord(BaseModel):
    """Persisted ontology proposal plus any review state."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    proposal_id: str = Field(min_length=1)
    proposal_key: str = Field(min_length=1)
    proposal_kind: UnknownItemKind
    proposed_value: str = Field(min_length=1)
    profile: ProfileRef
    target_pack: PackRef | None = None
    reason: str = Field(min_length=1)
    status: ProposalStatus
    application_status: ProposalApplicationStatus
    details: dict[str, JsonValue] = Field(default_factory=dict)
    candidate_ids: tuple[str, ...] = ()
    created_at: str = Field(min_length=1)
    review: ProposalReviewRecord | None = None
    overlay_application: OverlayApplicationRecord | None = None


class CandidateAssertionRecord(BaseModel):
    """Persisted candidate assertion plus validation, review state, and provenance."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    candidate_id: str = Field(min_length=1)
    profile: ProfileRef
    validation_status: CandidateValidationStatus
    review_status: CandidateReviewStatus
    payload_hash: str = Field(min_length=1)
    payload: dict[str, JsonValue]
    normalized_payload: dict[str, JsonValue]
    validation: PersistedValidationSnapshot
    proposal_ids: tuple[str, ...] = ()
    provenance: CandidateProvenance
    claim_text: str | None = None
    evidence_spans: tuple[EvidenceSpan, ...] = ()
    submitted_at: str = Field(min_length=1)
    review: CandidateReviewRecord | None = None


class CandidateSubmissionResult(BaseModel):
    """Return value for one candidate submission through the review slice."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    candidate: CandidateAssertionRecord
    proposals: tuple[ProposalRecord, ...] = ()


__all__ = [
    "CandidateAssertionRecord",
    "CandidateAssertionImport",
    "CandidateProvenance",
    "CandidateReviewDecision",
    "CandidateReviewRecord",
    "CandidateReviewStatus",
    "CandidateSubmissionResult",
    "CandidateValidationStatus",
    "EvidenceSpan",
    "OverlayApplicationRecord",
    "PersistedValidationSnapshot",
    "ProfileRef",
    "ProposalAcceptancePolicy",
    "ProposalApplicationStatus",
    "ProposalRecord",
    "ProposalReviewDecision",
    "ProposalReviewRecord",
    "ProposalStatus",
    "SourceArtifactRef",
]

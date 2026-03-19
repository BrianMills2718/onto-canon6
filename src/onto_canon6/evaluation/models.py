"""Typed models for the Phase 5 live extraction-evaluation slice.

These models keep the Phase 5 benchmark honest by separating three questions:

1. is the extracted candidate assertion supported by the source text?
2. is the extracted candidate structurally usable by the local validator?
3. did the extractor reproduce the preferred canonical payload exactly?

The benchmark can aggregate all three, but it should not collapse them back
into one headline number.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, JsonValue

from ..pipeline import CandidateAssertionImport, CandidateValidationStatus, ProfileRef, SourceArtifactRef

ReasonablenessLabel = Literal["supported", "partially_supported", "unsupported"]


class BenchmarkReferenceCandidate(BaseModel):
    """One preferred reference candidate payload from the benchmark fixture."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    candidate_id: str | None = None
    payload: dict[str, JsonValue]


class BenchmarkCase(BaseModel):
    """One benchmark case with source text and preferred reference candidates."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    case_id: str = Field(min_length=1)
    profile: ProfileRef
    source_artifact: SourceArtifactRef
    expected_candidates: tuple[BenchmarkReferenceCandidate, ...] = ()


class BenchmarkFixture(BaseModel):
    """Top-level benchmark fixture container."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    fixture_id: str = Field(min_length=1)
    cases: tuple[BenchmarkCase, ...] = ()


class CandidateReasonablenessReview(BaseModel):
    """Judge verdict for one extracted candidate assertion."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    candidate_index: int = Field(ge=0)
    support_label: ReasonablenessLabel
    reasoning: str = Field(min_length=1)


class ReasonablenessReview(BaseModel):
    """Structured case-level reasonableness review for extracted candidates."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    candidate_reviews: tuple[CandidateReasonablenessReview, ...] = ()
    important_missing_facts: tuple[str, ...] = ()
    overall_notes: str | None = None


class CanonicalizationSummary(BaseModel):
    """Secondary exact-match summary against preferred canonical payloads."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    expected: int = Field(ge=0)
    observed: int = Field(ge=0)
    matched: int = Field(ge=0)
    precision: float = Field(ge=0.0, le=1.0)
    recall: float = Field(ge=0.0, le=1.0)
    f1: float = Field(ge=0.0, le=1.0)
    missing_signatures: tuple[str, ...] = ()
    unexpected_signatures: tuple[str, ...] = ()


class LLMRunRecord(BaseModel):
    """Execution context for one LLM-backed leg of the evaluation pipeline."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    selection_task: str = Field(min_length=1)
    prompt_template: str = Field(min_length=1)
    prompt_ref: str | None = None
    selected_model: str = Field(min_length=1)
    resolved_model: str = Field(min_length=1)
    trace_id: str = Field(min_length=1)
    max_budget_usd: float = Field(ge=0.0)


class CandidateEvaluationRecord(BaseModel):
    """One extracted candidate plus its evaluation across the split metrics."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    candidate_index: int = Field(ge=0)
    candidate_import: CandidateAssertionImport
    validation_status: CandidateValidationStatus
    support_label: ReasonablenessLabel
    support_reasoning: str = Field(min_length=1)
    exact_preferred_match: bool


class BenchmarkCaseEvaluation(BaseModel):
    """Evaluation output for one benchmark case."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    case_id: str = Field(min_length=1)
    profile: ProfileRef
    source_artifact: SourceArtifactRef
    observability_run_id: str | None = None
    extraction_run: LLMRunRecord
    judge_run: LLMRunRecord
    candidate_evaluations: tuple[CandidateEvaluationRecord, ...] = ()
    canonicalization: CanonicalizationSummary
    important_missing_facts: tuple[str, ...] = ()
    overall_notes: str | None = None


class AggregateReasonablenessSummary(BaseModel):
    """Aggregate support/reasonableness summary across all extracted candidates."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    total_candidates: int = Field(ge=0)
    supported_count: int = Field(ge=0)
    partially_supported_count: int = Field(ge=0)
    unsupported_count: int = Field(ge=0)
    supported_rate: float = Field(ge=0.0, le=1.0)
    acceptable_rate: float = Field(ge=0.0, le=1.0)


class AggregateValidationSummary(BaseModel):
    """Aggregate structural-validation summary across extracted candidates."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    valid_count: int = Field(ge=0)
    needs_review_count: int = Field(ge=0)
    invalid_count: int = Field(ge=0)


class BenchmarkAggregateSummary(BaseModel):
    """Top-level aggregate summary for the live extraction benchmark."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    case_count: int = Field(ge=0)
    reasonableness: AggregateReasonablenessSummary
    validation: AggregateValidationSummary
    canonicalization: CanonicalizationSummary


class BenchmarkEvaluationReport(BaseModel):
    """Typed report for a full live extraction-evaluation run."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    generated_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    fixture_id: str = Field(min_length=1)
    fixture_path: str = Field(min_length=1)
    experiment_execution_id: str | None = None
    cases: tuple[BenchmarkCaseEvaluation, ...] = ()
    summary: BenchmarkAggregateSummary

"""Typed models for the first epistemic extension slice.

This extension deliberately avoids broad truth-maintenance behavior. The first
operators are:

1. confidence assessments for accepted candidate assertions;
2. explicit supersession from one accepted candidate assertion to another.

The extension keeps its own records and derives current epistemic status from
those records instead of mutating the base review pipeline schema.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from ...pipeline import CandidateAssertionRecord

ConfidenceSourceKind = Literal["user", "model"]
EpistemicCandidateStatus = Literal["active", "superseded"]


class ConfidenceAssessmentRecord(BaseModel):
    """Persist one confidence assessment against an accepted candidate.

    The first slice allows one current confidence assessment per candidate. A
    later phase can add richer assessment history if real workflows require it.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    assessment_id: str = Field(min_length=1)
    candidate_id: str = Field(min_length=1)
    confidence_score: float = Field(ge=0.0, le=1.0)
    source_kind: ConfidenceSourceKind
    actor_id: str = Field(min_length=1)
    rationale: str | None = None
    created_at: str = Field(min_length=1)


class SupersessionRecord(BaseModel):
    """Persist one explicit supersession from an older accepted candidate to a newer one."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    supersession_id: str = Field(min_length=1)
    prior_candidate_id: str = Field(min_length=1)
    replacement_candidate_id: str = Field(min_length=1)
    actor_id: str = Field(min_length=1)
    rationale: str | None = None
    created_at: str = Field(min_length=1)


class EpistemicCandidateReport(BaseModel):
    """Bundle one accepted candidate with its extension-local epistemic state."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    candidate: CandidateAssertionRecord
    epistemic_status: EpistemicCandidateStatus
    confidence: ConfidenceAssessmentRecord | None = None
    superseded_by: SupersessionRecord | None = None
    supersedes: tuple[SupersessionRecord, ...] = ()

"""Typed models for the epistemic extension slices.

This extension deliberately avoids broad truth-maintenance behavior. The
currently proved operators are:

1. confidence assessments for accepted candidate assertions;
2. explicit supersession from one accepted candidate assertion to another;
3. explicit `active` / `weakened` / `retracted` dispositions over promoted
   graph assertions;
4. derived corroboration and tension reporting over promoted graph state.

The extension keeps its own records and derives current epistemic status from
those records instead of mutating the base review pipeline schema.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from ...core import PromotedGraphAssertionRecord
from ...pipeline import CandidateAssertionRecord

ConfidenceSourceKind = Literal["user", "model"]
EpistemicCandidateStatus = Literal["active", "superseded"]
AssertionDispositionTargetStatus = Literal["active", "weakened", "retracted"]
PromotedAssertionEpistemicStatus = Literal["active", "weakened", "superseded", "retracted"]
EpistemicTensionKind = Literal["role_filler_conflict"]


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


class AssertionDispositionRecord(BaseModel):
    """Persist one explicit promoted-assertion disposition event.

    The current successor slice keeps manual assertion status deliberately
    narrow:

    1. only promoted assertions can receive manual dispositions;
    2. `superseded` remains derived from candidate-level supersession instead
       of manually authored here;
    3. each event records both the prior and target status for auditability.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    disposition_id: str = Field(min_length=1)
    assertion_id: str = Field(min_length=1)
    prior_status: PromotedAssertionEpistemicStatus
    target_status: AssertionDispositionTargetStatus
    actor_id: str = Field(min_length=1)
    rationale: str | None = None
    created_at: str = Field(min_length=1)


class AssertionCorroborationGroup(BaseModel):
    """Represent one derived corroboration group over promoted assertions."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    group_id: str = Field(min_length=1)
    predicate: str = Field(min_length=1)
    normalized_body_fingerprint: str = Field(min_length=1)
    assertion_ids: tuple[str, ...] = ()


class AssertionTensionRecord(BaseModel):
    """Represent one deterministic tension pair over promoted assertions."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    tension_id: str = Field(min_length=1)
    assertion_a_id: str = Field(min_length=1)
    assertion_b_id: str = Field(min_length=1)
    predicate: str = Field(min_length=1)
    tension_kind: EpistemicTensionKind
    anchor_roles: tuple[str, ...] = ()
    differing_roles: tuple[str, ...] = ()
    description: str = Field(min_length=1)


class PromotedAssertionEpistemicReport(BaseModel):
    """Bundle one promoted assertion with extension-local epistemic state.

    The promoted assertion itself remains immutable. Current status is derived
    from manual assertion dispositions, candidate-backed supersession,
    candidate-backed confidence, and deterministic corroboration / tension
    signals.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    assertion: PromotedGraphAssertionRecord
    epistemic_status: PromotedAssertionEpistemicStatus
    confidence: ConfidenceAssessmentRecord | None = None
    current_disposition: AssertionDispositionRecord | None = None
    disposition_history: tuple[AssertionDispositionRecord, ...] = ()
    superseded_by: SupersessionRecord | None = None
    superseded_by_assertion_id: str | None = None
    corroborating_assertion_ids: tuple[str, ...] = ()
    tensions: tuple[AssertionTensionRecord, ...] = ()


class PromotedAssertionEpistemicReportSummary(BaseModel):
    """Summarize one promoted-assertion epistemic collection report."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    total_assertions: int = Field(ge=0)
    total_active: int = Field(ge=0)
    total_weakened: int = Field(ge=0)
    total_superseded: int = Field(ge=0)
    total_retracted: int = Field(ge=0)
    total_assertions_with_confidence: int = Field(ge=0)
    total_corroboration_groups: int = Field(ge=0)
    total_tension_pairs: int = Field(ge=0)


class PromotedAssertionEpistemicCollectionReport(BaseModel):
    """Bundle promoted assertions plus derived corroboration and tension state."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    assertion_reports: tuple[PromotedAssertionEpistemicReport, ...] = ()
    corroboration_groups: tuple[AssertionCorroborationGroup, ...] = ()
    tensions: tuple[AssertionTensionRecord, ...] = ()
    summary: PromotedAssertionEpistemicReportSummary

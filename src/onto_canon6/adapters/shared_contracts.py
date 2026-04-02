"""Adapters between onto-canon6 internal models and epistemic-contracts shared models.

These converters operate at boundary points (export/import). Internal onto-canon6
code continues to use its own models. Only adapters that cross project boundaries
use the shared contracts.
"""

from __future__ import annotations

from typing import Any

from epistemic_contracts import (
    ClaimRecord,
    ConfidenceScore,
    EntityReference,
    EvidenceSpan as SharedEvidenceSpan,
    SourceRecord as SharedSourceRecord,
)

from ..core.graph_models import PromotedGraphAssertionRecord
from ..extensions.epistemic.models import ConfidenceAssessmentRecord
from ..pipeline.models import (
    CandidateAssertionRecord,
    EvidenceSpan,
    SourceArtifactRef,
)


def confidence_to_shared(record: ConfidenceAssessmentRecord) -> ConfidenceScore:
    """Convert onto-canon6 ConfidenceAssessmentRecord to shared ConfidenceScore."""
    return ConfidenceScore(
        score=record.confidence_score,
        source=record.source_kind,  # type: ignore[arg-type]  # ConfidenceSourceKind ⊂ ConfidenceSource
        actor_id=record.actor_id,
        rationale=record.rationale,
    )


def confidence_from_float(
    score: float,
    source: str = "extraction",
    actor_id: str | None = None,
) -> ConfidenceScore:
    """Create a shared ConfidenceScore from a bare float (research_v3 style)."""
    return ConfidenceScore(
        score=score,
        source=source,  # type: ignore[arg-type]
        actor_id=actor_id,
    )


def evidence_span_to_shared(span: EvidenceSpan) -> SharedEvidenceSpan:
    """Convert onto-canon6 EvidenceSpan to shared EvidenceSpan."""
    return SharedEvidenceSpan(
        text=span.text,
        start_char=span.start_char,
        end_char=span.end_char,
    )


def source_to_shared(ref: SourceArtifactRef) -> SharedSourceRecord:
    """Convert onto-canon6 SourceArtifactRef to shared SourceRecord."""
    return SharedSourceRecord(
        id=ref.source_ref,
        source_kind=ref.source_kind,
        source_ref=ref.source_ref,
        source_label=ref.source_label,
        source_metadata=ref.source_metadata,
    )


def entity_ref_from_promoted(
    entity_id: str,
    name: str,
    entity_type: str,
    *,
    ftm_id: str | None = None,
    wikidata_id: str | None = None,
    aliases: list[str] | None = None,
) -> EntityReference:
    """Create a shared EntityReference from onto-canon6 promoted entity data."""
    external_ids: dict[str, str] = {"onto_canon6": entity_id}
    if ftm_id:
        external_ids["ftm"] = ftm_id
    if wikidata_id:
        external_ids["wikidata"] = wikidata_id

    return EntityReference(
        entity_id=entity_id,
        name=name,
        entity_type=entity_type,
        external_ids=external_ids,
        aliases=aliases or [],
    )


def candidate_to_shared_claim(
    candidate: CandidateAssertionRecord,
    confidence: ConfidenceAssessmentRecord | None = None,
) -> ClaimRecord:
    """Convert onto-canon6 CandidateAssertionRecord to shared ClaimRecord."""
    shared_confidence = confidence_to_shared(confidence) if confidence else None

    return ClaimRecord(
        id=candidate.candidate_id,
        statement=candidate.claim_text or "",
        claim_type="assertion",
        status=_map_review_status(candidate.review_status),
        confidence=shared_confidence,
        evidence_spans=[
            evidence_span_to_shared(span)
            for span in (candidate.evidence_spans or ())
        ],
        predicate=candidate.payload.get("predicate") if candidate.payload else None,
        roles=candidate.payload.get("roles") if candidate.payload else None,
        source_system="onto-canon6",
    )


def _map_review_status(status: str) -> str:
    """Map onto-canon6 review status to shared ClaimStatus."""
    mapping = {
        "pending_review": "unverified",
        "accepted": "active",
        "rejected": "retracted",
    }
    return mapping.get(status, status)


__all__ = [
    "candidate_to_shared_claim",
    "confidence_from_float",
    "confidence_to_shared",
    "entity_ref_from_promoted",
    "evidence_span_to_shared",
    "source_to_shared",
]

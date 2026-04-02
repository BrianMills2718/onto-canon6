"""Import grounded-research adjudicated claims into onto-canon6.

Consumes shared epistemic-contracts ClaimRecords produced by grounded-research's
shared_export.py. Creates onto-canon6 candidates with preserved confidence,
evidence quality, and adjudication status.

This adapter uses the shared contracts — no custom mapping between project-
specific models. Any system that produces ClaimRecords can feed onto-canon6.
"""

from __future__ import annotations

import logging
from pathlib import Path

from epistemic_contracts import ClaimRecord, ConfidenceScore

from ..pipeline.models import (
    CandidateAssertionImport,
    EvidenceSpan,
    ProfileRef,
    SourceArtifactRef,
)

logger = logging.getLogger(__name__)


def import_shared_claims(
    claims: list[ClaimRecord],
    *,
    profile_id: str = "general_purpose_open",
    profile_version: str = "0.1.0",
) -> list[CandidateAssertionImport]:
    """Convert shared ClaimRecords to onto-canon6 CandidateAssertionImports.

    Preserves:
    - Confidence from adjudication (if present)
    - Evidence spans (if present)
    - Source references
    - Adjudication status (mapped to validation metadata)
    - Entity references (if present)
    """
    imports: list[CandidateAssertionImport] = []

    for claim in claims:
        # Build payload from claim data
        payload: dict = {}
        if claim.predicate:
            payload["predicate"] = claim.predicate
        else:
            payload["predicate"] = f"shared:{claim.claim_type}"

        if claim.roles:
            payload["roles"] = claim.roles

        # Build confidence metadata
        if claim.confidence:
            payload["confidence"] = claim.confidence.score
            payload["confidence_source"] = claim.confidence.source

        # Preserve adjudication metadata
        if claim.evidence_label:
            payload["evidence_label"] = claim.evidence_label
        if claim.is_provisional is not None:
            payload["is_provisional"] = claim.is_provisional
        if claim.corroboration_status:
            payload["corroboration_status"] = claim.corroboration_status

        # Build source artifact ref
        source_ref = claim.source_ids[0] if claim.source_ids else claim.id
        source_artifact = SourceArtifactRef(
            source_kind=f"{claim.source_system}_claim",
            source_ref=source_ref,
            source_label=f"{claim.source_system} claim {claim.id}",
            source_metadata={
                "claim_id": claim.id,
                "source_system": claim.source_system,
                "status": claim.status,
                "tags": claim.tags,
            },
            content_text=claim.statement,
        )

        # Evidence spans
        evidence_spans = tuple(
            EvidenceSpan(
                text=span.text,
                start_char=span.start_char if span.start_char is not None else 0,
                end_char=span.end_char if span.end_char is not None else len(span.text),
            )
            for span in claim.evidence_spans
        )

        # If no evidence spans, use the claim statement as evidence
        if not evidence_spans and claim.statement:
            evidence_spans = (
                EvidenceSpan(
                    text=claim.statement,
                    start_char=0,
                    end_char=len(claim.statement),
                ),
            )

        # Set content_text for evidence span verification — the review
        # pipeline requires source_artifact.content_text to verify spans
        content_text = claim.statement if evidence_spans else None

        candidate_import = CandidateAssertionImport(
            profile=ProfileRef(
                profile_id=profile_id,
                profile_version=profile_version,
            ),
            payload=payload,
            submitted_by=f"adapter:{claim.source_system}",
            source_artifact=source_artifact,
            evidence_spans=evidence_spans,
            claim_text=claim.statement,
        )

        imports.append(candidate_import)

    logger.info(
        "Converted %d shared claims to onto-canon6 candidate imports (source=%s)",
        len(imports),
        claims[0].source_system if claims else "unknown",
    )

    return imports


__all__ = ["import_shared_claims"]

"""Import research_v3 KnowledgeGraph YAML into onto-canon6 candidate assertions.

Converts research_v3 claims (with FtM entities, corroboration status, sources)
into onto-canon6 CandidateAssertionImport objects suitable for the review pipeline.

Entity type mapping: FtM schema names → SUMO-compatible types via a static map.
Corroboration status → epistemic confidence score.
Source URLs and retrieval timestamps → onto-canon6 provenance.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, cast

try:
    from data_contracts import boundary
except ImportError:
    def boundary(**kwargs):
        def decorator(fn):
            return fn
        return decorator
import yaml

from ..pipeline import (
    CandidateAssertionImport,
    ProfileRef,
    SourceArtifactRef,
)

logger = logging.getLogger(__name__)

# FtM schema → onto-canon6 entity type mapping
# FtM has ~70 schemas; we map the common ones
FTM_TO_OC_TYPE: dict[str, str] = {
    "Person": "oc:person",
    "Organization": "oc:organization",
    "Company": "oc:company",
    "PublicBody": "oc:government_organization",
    "LegalEntity": "oc:legal_entity",
    "Document": "oc:document",
    "Address": "oc:location",
    "Email": "oc:contact",
    "Phone": "oc:contact",
    "Vessel": "oc:vehicle",
    "Vehicle": "oc:vehicle",
    "BankAccount": "oc:financial_account",
    "Payment": "oc:financial_transaction",
    "Event": "oc:event",
    "Thing": "oc:entity",
}

# Corroboration status → confidence score
CORROBORATION_CONFIDENCE: dict[str, float] = {
    "corroborated": 0.90,
    "partially_corroborated": 0.70,
    "unverified": 0.50,
    "contradicted": 0.20,
}

# Confidence label → score
CONFIDENCE_LABEL_SCORE: dict[str, float] = {
    "very_high": 0.95,
    "high": 0.85,
    "medium": 0.65,
    "low": 0.40,
    "very_low": 0.20,
}


def load_research_v3_graph(graph_path: Path) -> dict[str, Any]:
    """Load a research_v3 graph.yaml file."""
    with graph_path.open("r", encoding="utf-8") as f:
        loaded = yaml.safe_load(f)
    if loaded is None:
        return {}
    if not isinstance(loaded, dict):
        raise ValueError(f"research_v3 graph must be a mapping: {graph_path}")
    return cast(dict[str, Any], loaded)


def map_ftm_entity_type(ftm_schema: str) -> str:
    """Map FtM schema name to onto-canon6 entity type."""
    return FTM_TO_OC_TYPE.get(ftm_schema, f"oc:{ftm_schema.lower()}")


def map_corroboration_to_confidence(
    corroboration_status: str,
    confidence_label: str | None = None,
    confidence_score: float | None = None,
) -> float:
    """Derive confidence from research_v3 corroboration and confidence fields."""
    if confidence_score is not None:
        return confidence_score
    if confidence_label:
        label_score = CONFIDENCE_LABEL_SCORE.get(confidence_label, 0.50)
        corr_score = CORROBORATION_CONFIDENCE.get(corroboration_status, 0.50)
        return (label_score + corr_score) / 2
    return CORROBORATION_CONFIDENCE.get(corroboration_status, 0.50)


@boundary(
    name="onto-canon6.import_research_v3_graph",
    version="0.1.0",
    producer="research_v3",
    consumers=["onto-canon6"],
    validate_input=False,
    validate_output=False,
)
def import_research_v3_graph(
    *,
    graph_path: Path,
    profile_id: str = "progressive_permissive",
    profile_version: str = "0.1.0",
    submitted_by: str = "adapter:research_v3",
) -> list[CandidateAssertionImport]:
    """Convert research_v3 graph.yaml claims into onto-canon6 candidate imports.

    Each claim becomes one candidate assertion with:
    - predicate: inferred from claim_type
    - roles: entities from entity_refs
    - provenance: source URL and retrieval timestamp
    - confidence: derived from corroboration_status
    """
    graph_data = load_research_v3_graph(graph_path)
    claims = graph_data.get("claims", [])
    entities = graph_data.get("entities", {})

    imports: list[CandidateAssertionImport] = []

    for claim in claims:
        claim_id = claim.get("id", "unknown")
        statement = claim.get("statement", "")
        if not statement:
            continue

        entity_refs = claim.get("entity_refs", [])
        claim_type = claim.get("claim_type", "fact_claim")
        source = claim.get("source", {})
        corr_status = claim.get("corroboration_status", "unverified")
        conf_label = claim.get("confidence")
        conf_score = claim.get("confidence_score")

        # Map claim_type → predicate
        predicate = _map_claim_type_to_predicate(claim_type)

        # Build role fillers from entity refs
        roles: dict[str, list[dict[str, Any]]] = {}
        for i, entity_ref in enumerate(entity_refs):
            entity_data = entities.get(entity_ref, {})
            ftm_schema = entity_data.get("schema", "Thing")
            entity_name = _extract_entity_name(entity_data)

            role_name = f"ARG{i}" if i < 2 else f"participant_{i}"
            roles[role_name] = [{
                "kind": "entity",
                "entity_type": map_ftm_entity_type(ftm_schema),
                "name": entity_name,
            }]

        # Add confidence as a value filler
        confidence = map_corroboration_to_confidence(corr_status, conf_label, conf_score)

        # Build payload
        payload: dict[str, Any] = {
            "predicate": predicate,
            "roles": roles,
            "confidence": confidence,
            "research_v3_claim_id": claim_id,
            "research_v3_corroboration": corr_status,
        }

        # Source provenance
        source_url = source.get("url", "")
        source_type = source.get("source_type", "unknown")
        retrieved_at = source.get("retrieved_at", "")

        source_artifact = SourceArtifactRef(
            source_kind=f"research_v3:{source_type}",
            source_ref=source_url or str(graph_path),
            source_label=f"research_v3 claim {claim_id}",
            content_text=statement,
            source_metadata={
                "source_type": source_type,
                "retrieved_at": retrieved_at,
                "claim_id": claim_id,
            },
        )

        imports.append(CandidateAssertionImport(
            profile=ProfileRef(
                profile_id=profile_id,
                profile_version=profile_version,
            ),
            payload=payload,
            submitted_by=submitted_by,
            source_artifact=source_artifact,
            evidence_spans=(),
            claim_text=statement,
        ))

    logger.info(
        "research_v3 import: %d claims → %d candidate imports from %s",
        len(claims), len(imports), graph_path,
    )
    return imports


def _map_claim_type_to_predicate(claim_type: str) -> str:
    """Map research_v3 claim types to generic predicates."""
    mapping = {
        "fact_claim": "rv3:asserts_fact",
        "relationship_claim": "rv3:asserts_relationship",
        "financial_claim": "rv3:asserts_financial",
        "temporal_claim": "rv3:asserts_temporal",
    }
    return mapping.get(claim_type, "rv3:asserts_fact")


def _extract_entity_name(entity_data: dict[str, Any]) -> str:
    """Extract display name from FtM entity dict."""
    properties = entity_data.get("properties", {})
    # FtM stores names as arrays
    if isinstance(properties, dict):
        names = properties.get("name", [])
        if isinstance(names, list) and names and isinstance(names[0], str):
            return names[0]
    # Fallback to id
    entity_id = entity_data.get("id")
    if isinstance(entity_id, str) and entity_id:
        return entity_id
    return "unknown"


__all__ = [
    "import_and_submit_memo",
    "import_research_v3_memo",
    "load_research_v3_memo",
    "FTM_TO_OC_TYPE",
    "import_research_v3_graph",
    "load_research_v3_graph",
    "map_corroboration_to_confidence",
    "map_ftm_entity_type",
]


# ── memo.yaml import ────────────────────────────────────────────────────────


def load_research_v3_memo(memo_path: Path) -> dict[str, Any]:
    """Load a research_v3 loop memo.yaml file."""
    with memo_path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


@boundary(
    name="onto-canon6.import_research_v3_memo",
    version="0.1.0",
    producer="research_v3",
    consumers=["onto-canon6"],
    validate_input=False,
    validate_output=False,
)
def import_research_v3_memo(
    memo_path: Path,
    *,
    limit: int | None = None,
    profile_id: str = "research_v3_integration",
    profile_version: str = "0.1.0",
    submitted_by: str = "adapter:research_v3_memo",
) -> list[CandidateAssertionImport]:
    """Import findings from a research_v3 loop memo.yaml.

    Converts each Finding (claim, source_urls, confidence, corroborated, tags)
    into a CandidateAssertionImport with full provenance mapping.

    Unlike import_research_v3_graph() which expects FtM entities and structured
    claims, this handles the simplified loop output format where each finding
    is a self-contained claim with confidence and source URLs.
    """
    memo_data = load_research_v3_memo(memo_path)
    findings = memo_data.get("key_findings", [])
    question = memo_data.get("question", "")

    if limit is not None:
        findings = findings[:limit]

    imports: list[CandidateAssertionImport] = []

    for i, finding in enumerate(findings):
        claim = finding.get("claim", "")
        if not claim:
            continue

        confidence = finding.get("confidence", 0.5)
        corroborated = finding.get("corroborated", False)
        tags = finding.get("tags", [])
        source_urls = finding.get("source_urls", [])

        # Truncate claim for label
        claim_preview = claim[:60] + "..." if len(claim) > 60 else claim

        source_artifact = SourceArtifactRef(
            source_kind="research_v3_memo",
            source_ref=f"{memo_path.name}:finding_{i}",
            source_label=f"Finding {i}: {claim_preview}",
            content_text=claim,
            source_metadata={
                "confidence": confidence,
                "corroboration_status": "corroborated" if corroborated else "unverified",
                "tags": tags,
                "source_urls": source_urls,
                "investigation_question": question,
            },
        )

        # Minimal assertion payload — the extraction pipeline fills the real
        # ontology-grounded structure later.  We include enough for the
        # candidate to pass validation as a self-contained record.
        payload: dict[str, Any] = {
            "predicate": "rv3:asserts",
            "roles": {
                "content": [{
                    "kind": "value",
                    "entity_type": "string",
                    "value": claim,
                }],
            },
            "confidence": confidence,
            "research_v3_corroboration": (
                "corroborated" if corroborated else "unverified"
            ),
        }

        imports.append(CandidateAssertionImport(
            profile=ProfileRef(
                profile_id=profile_id,
                profile_version=profile_version,
            ),
            payload=payload,
            submitted_by=submitted_by,
            source_artifact=source_artifact,
            evidence_spans=(),
            claim_text=claim,
        ))

    logger.info(
        "research_v3 memo import: %d findings → %d candidate imports from %s",
        len(memo_data.get("key_findings", [])),
        len(imports),
        memo_path,
    )
    return imports


def import_and_submit_memo(
    memo_path: Path,
    review_service: Any,
    **kwargs: Any,
) -> list[dict[str, Any]]:
    """Import memo findings and submit to the review pipeline.

    Returns a list of dicts with candidate_id, claim_text, and
    validation_status for each submitted candidate.
    """
    imports = import_research_v3_memo(memo_path, **kwargs)
    results: list[dict[str, Any]] = []
    for candidate_import in imports:
        result = review_service.submit_candidate_import(
            candidate_import=candidate_import,
        )
        results.append({
            "candidate_id": result.candidate.candidate_id,
            "claim_text": result.candidate.claim_text,
            "validation_status": result.candidate.validation_status,
        })
    logger.info(
        "research_v3 memo submit: %d candidates submitted from %s",
        len(results),
        memo_path,
    )
    return results

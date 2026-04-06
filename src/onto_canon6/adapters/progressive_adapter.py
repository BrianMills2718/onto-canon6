"""Adapter converting progressive extraction pipeline output into candidate assertion submissions.

The progressive extraction pipeline (Plan 0018) produces a
``ProgressiveExtractionReport`` containing Pass 1 triples, Pass 2 mapped
assertions, and Pass 3 typed assertions.  This adapter converts those into
``CandidateAssertionImport`` objects that feed directly into the review and
promotion workflow via ``ReviewService.submit_candidate_import()``.

Each ``Pass3TypedAssertion`` becomes one candidate import with a structured
payload containing subject, predicate, object, types, and provenance about
which pipeline pass produced the final form.

Unresolved triples from Pass 2 (those with no predicate match) are also
submitted as candidates with ``predicate: "unresolved"`` and
``pass_provenance: "pass1"`` so they remain visible in the review surface
rather than being silently dropped.

The default validation profile is ``progressive_permissive`` which uses
``mode=open`` so SUMO types produced by the LLM that are not in a closed
ontology pack are accepted rather than rejected.
"""

from __future__ import annotations

import logging
from typing import Sequence, cast

from pydantic import JsonValue

from ..config import get_config
from ..pipeline.models import (
    CandidateAssertionImport,
    CandidateSubmissionResult,
    EvidenceSpan,
    ProfileRef,
    SourceArtifactRef,
)
from ..pipeline.progressive_types import (
    EntityRefinement,
    Pass1Event,
    Pass2MappedAssertion,
    Pass3TypedAssertion,
    ProgressiveExtractionReport,
)
from ..pipeline.service import ReviewService

logger = logging.getLogger(__name__)


def convert_to_candidate_imports(
    report: ProgressiveExtractionReport,
    *,
    source_text: str,
    source_ref: str,
    source_label: str | None = None,
    profile_id: str = "progressive_permissive",
    profile_version: str = "0.1.0",
    submitted_by: str = "progressive_extractor",
) -> list[CandidateAssertionImport]:
    """Convert a ProgressiveExtractionReport into candidate imports.

    Each ``Pass3TypedAssertion`` becomes one ``CandidateAssertionImport`` with:

    - *payload*: ontology-shaped dict with subject, predicate, object, types
    - *evidence_spans*: from the Pass1Triple evidence_span (char offsets found
      in source_text)
    - *source_artifact*: reference to the source text
    - *claim_text*: human-readable gloss of the assertion

    Unresolved triples from Pass 2 (those with no predicate match) are also
    included with ``predicate="unresolved"`` and ``pass_provenance="pass1"``.
    """
    config = get_config()
    adapter_config = config.adapters.progressive
    effective_profile_id = profile_id or adapter_config.default_profile_id
    effective_profile_version = profile_version or adapter_config.default_profile_version
    effective_submitted_by = submitted_by or adapter_config.submitted_by

    profile = ProfileRef(
        profile_id=effective_profile_id,
        profile_version=effective_profile_version,
    )
    source_artifact = SourceArtifactRef(
        source_kind=adapter_config.source_kind,
        source_ref=source_ref,
        source_label=source_label,
        content_text=source_text,
    )

    imports: list[CandidateAssertionImport] = []

    for typed_assertion in report.pass3.typed_assertions:
        candidate_import = _typed_assertion_to_import(
            typed_assertion=typed_assertion,
            profile=profile,
            source_artifact=source_artifact,
            submitted_by=effective_submitted_by,
            source_text=source_text,
        )
        imports.append(candidate_import)

    for unresolved_event in report.pass2.unresolved:
        candidate_import = _unresolved_event_to_import(
            event=unresolved_event,
            profile=profile,
            source_artifact=source_artifact,
            submitted_by=effective_submitted_by,
            source_text=source_text,
        )
        imports.append(candidate_import)

    logger.info(
        "progressive adapter converted report: typed=%d unresolved=%d total=%d trace_id=%s",
        len(report.pass3.typed_assertions),
        len(report.pass2.unresolved),
        len(imports),
        report.trace_id,
    )
    return imports


def submit_progressive_report(
    report: ProgressiveExtractionReport,
    *,
    review_service: ReviewService,
    source_text: str,
    source_ref: str,
    source_label: str | None = None,
    profile_id: str = "progressive_permissive",
    profile_version: str = "0.1.0",
) -> list[CandidateSubmissionResult]:
    """Convert and submit all assertions from a progressive extraction report.

    Converts the report into ``CandidateAssertionImport`` objects and submits
    each one through the provided ``ReviewService``.  Returns the submission
    results in the same order as the candidate imports (typed assertions first,
    then unresolved triples).
    """
    imports = convert_to_candidate_imports(
        report,
        source_text=source_text,
        source_ref=source_ref,
        source_label=source_label,
        profile_id=profile_id,
        profile_version=profile_version,
    )
    results: list[CandidateSubmissionResult] = []
    for candidate_import in imports:
        result = review_service.submit_candidate_import(candidate_import=candidate_import)
        results.append(result)

    logger.info(
        "progressive adapter submitted %d candidates via review service trace_id=%s",
        len(results),
        report.trace_id,
    )
    return results


def _typed_assertion_to_import(
    *,
    typed_assertion: Pass3TypedAssertion,
    profile: ProfileRef,
    source_artifact: SourceArtifactRef,
    submitted_by: str,
    source_text: str,
) -> CandidateAssertionImport:
    """Convert one Pass3TypedAssertion into a CandidateAssertionImport.

    Builds the payload dict from the mapped assertion and entity refinements,
    locates the evidence span in the source text, and generates a human-readable
    claim gloss.
    """
    mapped = typed_assertion.assertion
    event = mapped.event
    refinements = typed_assertion.entity_refinements

    # Build a type lookup from entity name to resolved type for all participants.
    entity_type_by_name: dict[str, str] = {
        p.entity.name: _resolve_entity_type(
            entity_name=p.entity.name,
            coarse_type=p.entity.coarse_type,
            refinements=refinements,
        )
        for p in event.participants
    }

    payload = _build_typed_payload(
        mapped=mapped,
        entity_type_by_name=entity_type_by_name,
    )
    evidence_spans = _find_evidence_spans(
        evidence_text=event.evidence_span,
        source_text=source_text,
    )
    claim_text = _build_claim_text_from_mapped(mapped)

    return CandidateAssertionImport(
        profile=profile,
        payload=payload,
        submitted_by=submitted_by,
        source_artifact=source_artifact,
        evidence_spans=evidence_spans,
        claim_text=claim_text,
    )


def _unresolved_event_to_import(
    *,
    event: Pass1Event,
    profile: ProfileRef,
    source_artifact: SourceArtifactRef,
    submitted_by: str,
    source_text: str,
) -> CandidateAssertionImport:
    """Convert one unresolved Pass1Event into a CandidateAssertionImport.

    These events had no predicate match in Pass 2.  They are still submitted as
    candidates with ``predicate="unresolved"`` so they remain visible for review
    rather than being silently dropped.
    """
    payload = _build_unresolved_payload(event)
    evidence_spans = _find_evidence_spans(
        evidence_text=event.evidence_span,
        source_text=source_text,
    )
    claim_text = _build_claim_text_from_event(event)

    return CandidateAssertionImport(
        profile=profile,
        payload=payload,
        submitted_by=submitted_by,
        source_artifact=source_artifact,
        evidence_spans=evidence_spans,
        claim_text=claim_text,
    )


def _entity_filler(
    name: str,
    entity_type: str,
) -> dict[str, JsonValue]:
    """Build one entity role filler in the canonical graph format."""
    slug = name.lower().replace(" ", "_").replace("'", "")
    return {
        "kind": "entity",
        "entity_id": f"ent:progressive:{slug}",
        "entity_type": entity_type,
        "name": name,
    }


def _build_typed_payload(
    *,
    mapped: Pass2MappedAssertion,
    entity_type_by_name: dict[str, str],
) -> dict[str, JsonValue]:
    """Build the role-based payload dict for a typed assertion.

    The payload uses the canonical graph's ``predicate`` + ``roles`` format
    so candidates can be promoted without a separate normalization step.
    The ``roles`` dict maps semantic role names (e.g. "Operator", "Theme")
    to entity fillers — never ARG positions.  Additional provenance fields
    travel alongside.
    """
    event = mapped.event
    # Build roles from the mapped role assignments using the entity type lookup.
    roles: dict[str, list[dict[str, JsonValue]]] = {}
    for role_label, entity_name in mapped.mapped_roles.items():
        etype = entity_type_by_name.get(entity_name, "Entity")
        roles[role_label] = [_entity_filler(entity_name, etype)]

    # Ensure at least source_entity and target_entity roles exist
    if not roles and event.participants:
        first = event.participants[0]
        first_type = entity_type_by_name.get(first.entity.name, first.entity.coarse_type)
        roles["source_entity"] = [_entity_filler(first.entity.name, first_type)]
        if len(event.participants) > 1:
            second = event.participants[1]
            second_type = entity_type_by_name.get(second.entity.name, second.entity.coarse_type)
            roles["target_entity"] = [_entity_filler(second.entity.name, second_type)]

    result: dict[str, JsonValue] = {
        "predicate": mapped.predicate_id,
        "predicate_sense": mapped.propbank_sense_id,
        "process_type": mapped.process_type,
        "confidence": event.confidence,
        "disambiguation_method": mapped.disambiguation_method,
        "pass_provenance": "pass3",
    }
    # Cast roles to satisfy JsonValue typing — the structure is correct but
    # too deeply nested for the recursive type alias.
    result["roles"] = cast(JsonValue, roles)
    return result


def _build_unresolved_payload(event: Pass1Event) -> dict[str, JsonValue]:
    """Build the role-based payload dict for an unresolved event.

    Uses ``predicate="unresolved"`` and ``pass_provenance="pass1"`` to make
    the lack of predicate mapping explicit in the candidate record.  Still
    includes ``roles`` so the candidate is promotable if later resolved.
    Roles are keyed by proto_role (lowercased).
    """
    roles: dict[str, list[dict[str, JsonValue]]] = {}
    for p in event.participants:
        role_key = p.proto_role.lower()
        roles.setdefault(role_key, []).append(
            _entity_filler(p.entity.name, p.entity.coarse_type)
        )
    roles["relationship_verb"] = [{
        "kind": "value",
        "value": event.relationship_verb,
        "value_kind": "string",
    }]

    # Provide legacy source_entity/target_entity keys for consumers that rely on them.
    if event.participants and "source_entity" not in roles:
        first = event.participants[0]
        roles["source_entity"] = [_entity_filler(first.entity.name, first.entity.coarse_type)]
    if len(event.participants) > 1 and "target_entity" not in roles:
        second = event.participants[1]
        roles["target_entity"] = [_entity_filler(second.entity.name, second.entity.coarse_type)]

    return {
        "predicate": "unresolved",
        "roles": cast(JsonValue, roles),
        "predicate_sense": "",
        "process_type": "",
        "confidence": event.confidence,
        "disambiguation_method": "unresolved",
        "pass_provenance": "pass1",
    }


def _resolve_entity_type(
    *,
    entity_name: str,
    coarse_type: str,
    refinements: Sequence[EntityRefinement],
) -> str:
    """Return the most refined type available for a named entity.

    Searches the refinement list for a matching entity name.  If found, returns
    the refined type; otherwise falls back to the coarse type from Pass 1.
    """
    for refinement in refinements:
        if refinement.entity_name == entity_name:
            return refinement.refined_type
    return coarse_type


def _find_evidence_spans(
    *,
    evidence_text: str,
    source_text: str,
) -> tuple[EvidenceSpan, ...]:
    """Locate the evidence text within the source and return char-offset spans.

    If the evidence text is empty or not found in the source text, returns an
    empty tuple rather than crashing.  This is intentional: the evidence span
    from the LLM may be an approximate paraphrase rather than a verbatim excerpt.
    """
    if not evidence_text:
        return ()
    start = source_text.find(evidence_text)
    if start < 0:
        return ()
    return (
        EvidenceSpan(
            start_char=start,
            end_char=start + len(evidence_text),
            text=evidence_text,
        ),
    )


def _build_claim_text_from_mapped(mapped: Pass2MappedAssertion) -> str:
    """Generate a human-readable claim gloss from a mapped assertion.

    Format: ``<agent> [<predicate_sense>] <theme>``
    Falls back to first two participant names when agent/theme not labeled.
    """
    event = mapped.event
    agent = next((p for p in event.participants if p.proto_role == "Agent"), None)
    theme = next((p for p in event.participants if p.proto_role == "Theme"), None)
    if agent and theme:
        return f"{agent.entity.name} [{mapped.propbank_sense_id}] {theme.entity.name}"
    names = [p.entity.name for p in event.participants[:2]]
    return f"{' '.join(names)} [{mapped.propbank_sense_id}]"


def _build_claim_text_from_event(event: Pass1Event) -> str:
    """Generate a human-readable claim gloss from an unresolved event.

    Format: ``<agent> <relationship_verb> <theme>``
    Falls back to first two participant names when agent/theme not labeled.
    """
    agent = next((p for p in event.participants if p.proto_role == "Agent"), None)
    theme = next((p for p in event.participants if p.proto_role == "Theme"), None)
    if agent and theme:
        return f"{agent.entity.name} {event.relationship_verb} {theme.entity.name}"
    names = [p.entity.name for p in event.participants[:2]]
    return f"{' '.join(names)} [{event.relationship_verb}]"


__all__ = [
    "convert_to_candidate_imports",
    "submit_progressive_report",
]

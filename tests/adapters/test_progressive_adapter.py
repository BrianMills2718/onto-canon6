"""Tests for the progressive extraction adapter.

Verifies that progressive extraction pipeline output is correctly converted
into candidate assertion submissions and flows through the review service.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from onto_canon6.adapters.progressive_adapter import (
    convert_to_candidate_imports,
    submit_progressive_report,
)
from onto_canon6.pipeline import ReviewService
from onto_canon6.pipeline.progressive_types import (
    EntityRefinement,
    Pass1Entity,
    Pass1Event,
    Pass1Participant,
    Pass1Result,
    Pass2MappedAssertion,
    Pass2Result,
    Pass3Result,
    Pass3TypedAssertion,
    ProgressiveExtractionReport,
)


_SOURCE_TEXT = (
    "Shield AI develops autonomous drones for military operations. "
    "The company raised $200M in Series E funding from investors."
)


def _make_entity(name: str, coarse_type: str, context: str = "") -> Pass1Entity:
    """Build a minimal Pass1Entity for testing."""
    return Pass1Entity(name=name, coarse_type=coarse_type, context=context)


def _make_event(
    entity_a: Pass1Entity,
    entity_b: Pass1Entity,
    verb: str,
    evidence: str = "",
    confidence: float = 0.8,
) -> Pass1Event:
    """Build a minimal Pass1Event for testing (Agent + Theme participants)."""
    return Pass1Event(
        relationship_verb=verb,
        participants=[
            Pass1Participant(proto_role="Agent", entity=entity_a),
            Pass1Participant(proto_role="Theme", entity=entity_b),
        ],
        evidence_span=evidence,
        confidence=confidence,
    )


def _make_mapped_assertion(
    event: Pass1Event,
    predicate_id: str = "develop_create",
    propbank_sense: str = "develop-02",
    process_type: str = "Making",
    method: str = "single_sense",
) -> Pass2MappedAssertion:
    """Build a minimal Pass2MappedAssertion for testing."""
    return Pass2MappedAssertion(
        event=event,
        predicate_id=predicate_id,
        propbank_sense_id=propbank_sense,
        process_type=process_type,
        mapped_roles={
            "ARG0": event.participants[0].entity.name,
            "ARG1": event.participants[1].entity.name if len(event.participants) > 1 else "",
        },
        disambiguation_method=method,
        mapping_confidence=0.9,
    )


def _make_refinement(
    entity_name: str, coarse: str, refined: str, method: str = "subtree_pick"
) -> EntityRefinement:
    """Build a minimal EntityRefinement for testing."""
    return EntityRefinement(
        entity_name=entity_name,
        coarse_type=coarse,
        refined_type=refined,
        role_constraint="Entity",
        refinement_method=method,
        candidate_count=5,
    )


def _make_report(
    typed_assertions: list[Pass3TypedAssertion] | None = None,
    unresolved_events: list[Pass1Event] | None = None,
) -> ProgressiveExtractionReport:
    """Build a minimal ProgressiveExtractionReport for testing.

    Creates the full pass1/pass2/pass3 chain from the provided typed assertions
    and unresolved events.
    """
    entity_a = _make_entity("Shield AI", "Corporation")
    entity_b = _make_entity("autonomous drones", "Device")
    entity_c = _make_entity("investors", "Human")

    event1 = _make_event(
        entity_a, entity_b, "develops",
        evidence="Shield AI develops autonomous drones",
        confidence=0.9,
    )
    event2 = _make_event(
        entity_a, entity_c, "raise",
        evidence="The company raised $200M in Series E funding from investors",
        confidence=0.7,
    )

    mapped1 = _make_mapped_assertion(event1)
    refinement_a = _make_refinement("Shield AI", "Corporation", "MilitaryOrganization")
    refinement_b = _make_refinement("autonomous drones", "Device", "UnmannedAerialVehicle")

    default_typed = [
        Pass3TypedAssertion(
            assertion=mapped1,
            entity_refinements=[refinement_a, refinement_b],
        ),
    ]
    default_unresolved = [event2]

    effective_typed = typed_assertions if typed_assertions is not None else default_typed
    effective_unresolved = unresolved_events if unresolved_events is not None else default_unresolved

    all_events = [ta.assertion.event for ta in effective_typed] + list(effective_unresolved)
    all_entities_dict: dict[str, Pass1Entity] = {}
    for ev in all_events:
        for p in ev.participants:
            all_entities_dict[p.entity.name] = p.entity
    all_entities = list(all_entities_dict.values())

    pass1 = Pass1Result(
        events=all_events,
        entities=all_entities,
        source_text_hash="sha256:abc123",
        model="test-model",
        cost=0.01,
        trace_id="test-trace-001",
    )
    pass2 = Pass2Result(
        mapped=[ta.assertion for ta in effective_typed],
        unresolved=effective_unresolved,
        source_pass1=pass1,
        model="test-model",
        cost=0.01,
        trace_id="test-trace-001",
        single_sense_count=len(effective_typed),
        llm_disambiguated_count=0,
        unresolved_count=len(effective_unresolved),
    )
    pass3 = Pass3Result(
        typed_assertions=effective_typed,
        source_pass2=pass2,
        model="test-model",
        cost=0.01,
        trace_id="test-trace-001",
        leaf_early_exit_count=0,
        subtree_pick_count=len(effective_typed),
        no_constraint_count=0,
    )
    return ProgressiveExtractionReport(
        pass1=pass1,
        pass2=pass2,
        pass3=pass3,
        total_cost=0.03,
        trace_id="test-trace-001",
        model="test-model",
        triples_extracted=len(all_events),
        predicates_mapped=len(effective_typed),
        predicates_unresolved=len(effective_unresolved),
        entities_refined=sum(len(ta.entity_refinements) for ta in effective_typed),
        single_sense_early_exits=len(effective_typed),
        leaf_type_early_exits=0,
    )


def test_typed_assertion_converts_to_candidate_import() -> None:
    """A typed assertion should produce a CandidateAssertionImport with the correct payload shape."""
    report = _make_report()
    imports = convert_to_candidate_imports(
        report, source_text=_SOURCE_TEXT, source_ref="test://shield-ai",
    )

    typed_import = imports[0]
    payload = typed_import.payload
    assert payload["predicate"] == "develop_create"
    assert payload["predicate_sense"] == "develop-02"
    assert payload["process_type"] == "Making"
    assert payload["confidence"] == 0.9
    assert payload["disambiguation_method"] == "single_sense"
    assert payload["pass_provenance"] == "pass3"
    # Role-based entity structure
    roles = payload["roles"]
    assert isinstance(roles, dict)
    assert len(roles) > 0
    # At least one role should contain Shield AI or autonomous drones
    all_names = [
        filler["name"]
        for fillers in roles.values()
        if isinstance(fillers, list)
        for filler in fillers
        if isinstance(filler, dict) and "name" in filler
    ]
    assert "Shield AI" in all_names or "autonomous drones" in all_names


def test_unresolved_event_converts_to_candidate_import() -> None:
    """An unresolved event should produce a CandidateAssertionImport with predicate='unresolved'."""
    report = _make_report()
    imports = convert_to_candidate_imports(
        report, source_text=_SOURCE_TEXT, source_ref="test://shield-ai",
    )

    unresolved_import = imports[1]
    payload = unresolved_import.payload
    assert payload["predicate"] == "unresolved"
    assert payload["pass_provenance"] == "pass1"
    assert payload["disambiguation_method"] == "unresolved"
    # Role-based entity structure for unresolved events uses proto_role keys + legacy aliases
    roles = payload["roles"]
    assert "source_entity" in roles
    assert "target_entity" in roles
    src = roles["source_entity"][0]
    tgt = roles["target_entity"][0]
    assert src["name"] == "Shield AI"
    assert src["entity_type"] == "Corporation"
    assert tgt["name"] == "investors"
    assert tgt["entity_type"] == "Human"


def test_evidence_span_found_in_source_text() -> None:
    """When the evidence text is found in the source, char offsets should be correct."""
    report = _make_report()
    imports = convert_to_candidate_imports(
        report, source_text=_SOURCE_TEXT, source_ref="test://shield-ai",
    )

    typed_import = imports[0]
    assert len(typed_import.evidence_spans) == 1
    span = typed_import.evidence_spans[0]
    assert span.text == "Shield AI develops autonomous drones"
    assert _SOURCE_TEXT[span.start_char:span.end_char] == span.text


def test_evidence_span_not_found_gives_empty() -> None:
    """When the evidence text is not in the source, evidence_spans should be empty, not crash."""
    entity_a = _make_entity("FooOrg", "Organization")
    entity_b = _make_entity("BarThing", "Artifact")
    event = _make_event(
        entity_a, entity_b, "use",
        evidence="This text does not appear in the source at all",
        confidence=0.5,
    )
    mapped = _make_mapped_assertion(event)
    refinement_a = _make_refinement("FooOrg", "Organization", "GovernmentOrganization")
    refinement_b = _make_refinement("BarThing", "Artifact", "Weapon")
    typed = Pass3TypedAssertion(assertion=mapped, entity_refinements=[refinement_a, refinement_b])
    report = _make_report(typed_assertions=[typed], unresolved_events=[])

    imports = convert_to_candidate_imports(
        report, source_text=_SOURCE_TEXT, source_ref="test://shield-ai",
    )

    assert len(imports) == 1
    assert imports[0].evidence_spans == ()


def test_submit_through_review_service(tmp_path: Path) -> None:
    """Submitting through ReviewService should return CandidateSubmissionResults."""
    review_service = ReviewService(
        db_path=tmp_path / "review.sqlite3",
        overlay_root=tmp_path / "overlays",
    )
    report = _make_report()
    results = submit_progressive_report(
        report,
        review_service=review_service,
        source_text=_SOURCE_TEXT,
        source_ref="test://shield-ai",
        source_label="Shield AI findings",
    )

    assert len(results) == 2
    first = results[0]
    assert first.candidate.review_status == "pending_review"
    assert first.candidate.provenance.source_kind == "progressive_extraction"
    assert first.candidate.provenance.source_ref == "test://shield-ai"
    assert first.candidate.provenance.source_label == "Shield AI findings"


def test_full_report_conversion_count() -> None:
    """Full report should produce one import per typed assertion plus one per unresolved triple."""
    report = _make_report()
    imports = convert_to_candidate_imports(
        report, source_text=_SOURCE_TEXT, source_ref="test://shield-ai",
    )
    expected = len(report.pass3.typed_assertions) + len(report.pass2.unresolved)
    assert len(imports) == expected


def test_claim_text_for_typed_assertion() -> None:
    """Typed assertion claim text should use the format: subject [propbank_sense] object."""
    report = _make_report()
    imports = convert_to_candidate_imports(
        report, source_text=_SOURCE_TEXT, source_ref="test://shield-ai",
    )
    typed_import = imports[0]
    assert typed_import.claim_text == "Shield AI [develop-02] autonomous drones"


def test_claim_text_for_unresolved_event() -> None:
    """Unresolved event claim text should use Agent + relationship_verb + Theme."""
    report = _make_report()
    imports = convert_to_candidate_imports(
        report, source_text=_SOURCE_TEXT, source_ref="test://shield-ai",
    )
    unresolved_import = imports[1]
    assert unresolved_import.claim_text == "Shield AI raise investors"


def test_source_artifact_fields() -> None:
    """Source artifact should carry the correct source_kind, source_ref, source_label, and content_text."""
    report = _make_report()
    imports = convert_to_candidate_imports(
        report,
        source_text=_SOURCE_TEXT,
        source_ref="test://shield-ai",
        source_label="Shield AI findings",
    )

    for candidate_import in imports:
        artifact = candidate_import.source_artifact
        assert artifact.source_kind == "progressive_extraction"
        assert artifact.source_ref == "test://shield-ai"
        assert artifact.source_label == "Shield AI findings"
        assert artifact.content_text == _SOURCE_TEXT

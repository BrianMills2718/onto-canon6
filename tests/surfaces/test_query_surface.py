"""Tests for the first read-only promoted-knowledge query surface."""

from __future__ import annotations

from pathlib import Path

import pytest

from onto_canon6.artifacts import ArtifactLineageService
from onto_canon6.core import CanonicalGraphService, IdentityService
from onto_canon6.pipeline import ReviewService
from onto_canon6.surfaces import (
    AssertionBrowseRequest,
    AssertionSearchRequest,
    EntityBrowseRequest,
    EntitySearchRequest,
    GetEntityRequest,
    GetEvidenceRequest,
    GetPromotedAssertionRequest,
    QuerySurfaceNotFoundError,
    QuerySurfaceService,
)


def _seed_review_service(tmp_path: Path) -> ReviewService:
    """Create one isolated review service for query-surface tests."""

    review_db_path = tmp_path / "review.sqlite3"
    overlay_root = tmp_path / "ontology_overlays"
    return ReviewService(
        db_path=review_db_path,
        overlay_root=overlay_root,
        default_acceptance_policy="record_only",
    )


def _submit_accept_and_promote(
    review_service: ReviewService,
    *,
    predicate: str,
    person_entity_id: str,
    person_name: str,
    source_ref: str,
    claim_text: str,
) -> str:
    """Seed one accepted and promoted assertion with explicit entity names."""

    source_text = f"{person_name} served as commander of USSOCOM."
    submission = review_service.submit_candidate_assertion(
        payload={
            "predicate": predicate,
            "roles": {
                "commander": [
                    {
                        "entity_id": person_entity_id,
                        "entity_type": "oc:person",
                        "name": person_name,
                    }
                ],
                "organization": [
                    {
                        "entity_id": "ent:org:ussocom",
                        "entity_type": "oc:organization",
                        "name": "USSOCOM",
                    }
                ],
            },
        },
        profile_id="default",
        profile_version="1.0.0",
        submitted_by="analyst:query-seed",
        source_kind="text_file",
        source_ref=source_ref,
        source_text=source_text,
        claim_text=claim_text,
        evidence_spans=(
            {
                "start_char": 0,
                "end_char": len(person_name),
                "text": person_name,
            },
        ),
    )
    accepted = review_service.review_candidate(
        candidate_id=submission.candidate.candidate_id,
        decision="accepted",
        actor_id="analyst:reviewer",
    )
    promotion = CanonicalGraphService(db_path=review_service.store.db_path).promote_candidate(
        candidate_id=accepted.candidate_id,
        promoted_by="analyst:graph-promoter",
    )
    return promotion.assertion.assertion_id


def _seed_query_surface(tmp_path: Path) -> tuple[QuerySurfaceService, str]:
    """Create a seeded query surface with alias and evidence context."""

    review_service = _seed_review_service(tmp_path)
    first_assertion_id = _submit_accept_and_promote(
        review_service,
        predicate="oc:hold_command_role",
        person_entity_id="ent:person:eric_olson",
        person_name="Eric Olson",
        source_ref="notes/eric_olson.txt",
        claim_text="Eric Olson held the commander role at USSOCOM.",
    )
    second_assertion_id = _submit_accept_and_promote(
        review_service,
        predicate="oc:hold_command_role",
        person_entity_id="ent:person:admiral_eric_olson",
        person_name="Admiral Eric Olson",
        source_ref="notes/admiral_eric_olson.txt",
        claim_text="Admiral Eric Olson held the commander role at USSOCOM.",
    )

    identity_service = IdentityService(db_path=review_service.store.db_path)
    created = identity_service.create_identity_for_entity(
        entity_id="ent:person:eric_olson",
        created_by="analyst:identity",
        display_label="Eric Olson",
    )
    identity_service.attach_entity_alias(
        identity_id=created.identity.identity_id,
        entity_id="ent:person:admiral_eric_olson",
        attached_by="analyst:identity",
    )
    identity_service.attach_external_reference(
        identity_id=created.identity.identity_id,
        provider="analyst_registry",
        external_id="eric-olson-profile",
        attached_by="analyst:identity",
        reference_label="Eric Olson",
    )
    artifact_service = ArtifactLineageService(db_path=review_service.store.db_path)
    artifact = artifact_service.register_artifact(
        artifact_kind="source",
        uri="notes/eric_olson.txt",
        label="Eric Olson note",
    )
    first_candidate_id = CanonicalGraphService(
        db_path=review_service.store.db_path
    ).get_promoted_assertion(assertion_id=first_assertion_id).source_candidate_id
    artifact_service.link_candidate_artifact(
        candidate_id=first_candidate_id,
        artifact_id=artifact.artifact_id,
        support_kind="quoted_from",
        reference_detail="opening sentence",
    )
    return QuerySurfaceService(
        graph_service=CanonicalGraphService(db_path=review_service.store.db_path),
        identity_service=identity_service,
        review_service=review_service,
        artifact_service=artifact_service,
    ), second_assertion_id


def test_search_entities_matches_canonical_and_alias_names(tmp_path: Path) -> None:
    """Entity search should rank canonical and alias name matches deterministically."""

    service, second_assertion_id = _seed_query_surface(tmp_path)

    canonical_results = service.search_entities(EntitySearchRequest(query="Eric Olson"))
    alias_results = service.search_entities(EntitySearchRequest(query="Admiral Eric Olson"))

    assert canonical_results[0].entity_id == "ent:person:eric_olson"
    assert canonical_results[0].match_reason == "canonical_exact"
    assert alias_results[0].entity_id == "ent:person:admiral_eric_olson"
    assert alias_results[0].match_reason == "alias_exact"


def test_get_entity_returns_identity_and_linked_assertions(tmp_path: Path) -> None:
    """Entity detail should expose identity context and linked promoted assertions."""

    service, second_assertion_id = _seed_query_surface(tmp_path)
    detail = service.get_entity(GetEntityRequest(entity_id="ent:person:eric_olson"))

    assert detail.identity_bundle is not None
    assert detail.identity_bundle.identity.display_label == "Eric Olson"
    assert len(detail.identity_bundle.external_references) == 1
    linked_assertion_ids = {result.assertion_id for result in detail.linked_assertions}
    assert second_assertion_id in linked_assertion_ids
    assert len(linked_assertion_ids) == 2
    assert detail.display_label == "Eric Olson"


def test_search_promoted_assertions_filters_by_entity_and_text(tmp_path: Path) -> None:
    """Promoted-assertion search should support entity and claim-text filters."""

    service, second_assertion_id = _seed_query_surface(tmp_path)

    entity_results = service.search_promoted_assertions(
        AssertionSearchRequest(entity_id="ent:person:admiral_eric_olson")
    )
    text_results = service.search_promoted_assertions(
        AssertionSearchRequest(text_query="Admiral Eric Olson")
    )

    assert [result.assertion_id for result in entity_results] == [second_assertion_id]
    assert [result.assertion_id for result in text_results] == [second_assertion_id]
    assert entity_results[0].predicate == "oc:hold_command_role"


def test_get_promoted_assertion_includes_source_and_evidence(tmp_path: Path) -> None:
    """Assertion detail should include source candidate, epistemic, and evidence context."""

    service, second_assertion_id = _seed_query_surface(tmp_path)
    detail = service.get_promoted_assertion(
        GetPromotedAssertionRequest(assertion_id=second_assertion_id)
    )

    assert detail.promotion.assertion.assertion_id == second_assertion_id
    assert detail.source_candidate.candidate_id == detail.promotion.assertion.source_candidate_id
    assert detail.evidence.candidate.candidate_id == detail.source_candidate.candidate_id
    assert detail.evidence.source_artifact.source_ref == "notes/admiral_eric_olson.txt"
    assert detail.epistemic_report.epistemic_status == "active"


def test_get_evidence_returns_candidate_spans_and_artifact_links(tmp_path: Path) -> None:
    """Evidence lookup should expose supporting spans and linked artifacts."""

    service, _second_assertion_id = _seed_query_surface(tmp_path)
    first_result = service.search_promoted_assertions(
        AssertionSearchRequest(source_ref="notes/eric_olson.txt")
    )[0]
    evidence = service.get_evidence(GetEvidenceRequest(assertion_id=first_result.assertion_id))

    assert evidence.evidence_spans
    assert evidence.evidence_spans[0].text == "Eric Olson"
    assert evidence.artifact_links
    assert evidence.artifacts[0].label == "Eric Olson note"


def test_get_entity_fails_loudly_for_unknown_entity(tmp_path: Path) -> None:
    """Unknown promoted entities should raise a typed query-surface error."""

    service, _second_assertion_id = _seed_query_surface(tmp_path)

    with pytest.raises(QuerySurfaceNotFoundError, match="promoted entity not found"):
        service.get_entity(GetEntityRequest(entity_id="ent:missing"))


def test_list_entities_returns_alias_and_counts_in_browse_order(tmp_path: Path) -> None:
    """Entity browse should expose alias members with linked-assertion counts."""

    service, _second_assertion_id = _seed_query_surface(tmp_path)

    results = service.list_entities(EntityBrowseRequest(entity_type="oc:person"))

    assert [result.entity_id for result in results] == [
        "ent:person:admiral_eric_olson",
        "ent:person:eric_olson",
    ]
    assert results[0].display_label == "Admiral Eric Olson"
    assert results[0].linked_assertion_count == 2
    assert results[1].display_label == "Eric Olson"
    assert results[1].linked_assertion_count == 2


def test_list_promoted_assertions_filters_by_source_fields(tmp_path: Path) -> None:
    """Assertion browse should support source-ref and source-kind filtering."""

    service, second_assertion_id = _seed_query_surface(tmp_path)

    source_ref_results = service.list_promoted_assertions(
        AssertionBrowseRequest(source_ref="notes/admiral_eric_olson.txt")
    )
    source_kind_results = service.list_promoted_assertions(
        AssertionBrowseRequest(source_kind="text_file")
    )

    assert [result.assertion_id for result in source_ref_results] == [second_assertion_id]
    assert source_ref_results[0].source_candidate_id
    assert source_ref_results[0].source_ref == "notes/admiral_eric_olson.txt"
    assert source_ref_results[0].source_kind == "text_file"
    assert len(source_kind_results) == 2


def test_search_promoted_assertions_filters_by_source_fields(tmp_path: Path) -> None:
    """Promoted-assertion search should support provenance-based filters."""

    service, second_assertion_id = _seed_query_surface(tmp_path)

    source_ref_results = service.search_promoted_assertions(
        AssertionSearchRequest(source_ref="notes/admiral_eric_olson.txt")
    )
    source_kind_results = service.search_promoted_assertions(
        AssertionSearchRequest(source_kind="text_file")
    )

    assert [result.assertion_id for result in source_ref_results] == [second_assertion_id]
    assert len(source_kind_results) == 2

"""Tests for the first stable-identity and external-reference slice."""

from __future__ import annotations

from pathlib import Path

import pytest

from onto_canon6.core import (
    CanonicalGraphService,
    IdentityConflictError,
    IdentityService,
)
from onto_canon6.pipeline import ReviewService
from onto_canon6.surfaces import IdentityReportService


def _seed_review_service(tmp_path: Path) -> ReviewService:
    """Create one isolated review service for identity tests."""

    review_db_path = tmp_path / "review.sqlite3"
    overlay_root = tmp_path / "ontology_overlays"
    return ReviewService(
        db_path=review_db_path,
        overlay_root=overlay_root,
        default_acceptance_policy="record_only",
    )


def _submit_and_promote_candidate(
    review_service: ReviewService,
    *,
    predicate: str,
    entity_id: str,
    entity_type: str,
    source_ref: str,
) -> str:
    """Submit, accept, and promote one candidate for identity seeding."""

    submission = review_service.submit_candidate_assertion(
        payload={
            "predicate": predicate,
            "roles": {
                "subject": [
                    {
                        "entity_id": entity_id,
                        "entity_type": entity_type,
                    }
                ],
                "descriptor": [
                    {
                        "kind": "value",
                        "value_kind": "string",
                        "value": "test descriptor",
                    }
                ],
            },
        },
        profile_id="default",
        profile_version="1.0.0",
        submitted_by="analyst:identity-seed",
        source_kind="text_file",
        source_ref=source_ref,
        source_text="Test source text.",
    )
    accepted = review_service.review_candidate(
        candidate_id=submission.candidate.candidate_id,
        decision="accepted",
        actor_id="analyst:reviewer",
    )
    CanonicalGraphService(db_path=review_service.store.db_path).promote_candidate(
        candidate_id=accepted.candidate_id,
        promoted_by="analyst:graph-promoter",
    )
    return accepted.candidate_id


def test_create_identity_for_promoted_entity_is_idempotent(tmp_path: Path) -> None:
    """Creating an identity twice for the same promoted entity should reuse it."""

    review_service = _seed_review_service(tmp_path)
    _submit_and_promote_candidate(
        review_service,
        predicate="oc:identity_demo",
        entity_id="ent:person:eric_olson",
        entity_type="oc:person",
        source_ref="notes/identity_a.txt",
    )
    identity_service = IdentityService(db_path=review_service.store.db_path)

    first = identity_service.create_identity_for_entity(
        entity_id="ent:person:eric_olson",
        created_by="analyst:identity",
        display_label="Eric Olson",
    )
    second = identity_service.create_identity_for_entity(
        entity_id="ent:person:eric_olson",
        created_by="analyst:identity",
        display_label="Eric Olson",
    )

    assert second.identity.identity_id == first.identity.identity_id
    assert first.memberships[0].membership_kind == "canonical"
    assert len(first.memberships) == 1


def test_repeated_ingestion_of_same_entity_reuses_stable_identity(tmp_path: Path) -> None:
    """A repeated promoted entity id should resolve to the same local identity."""

    review_service = _seed_review_service(tmp_path)
    _submit_and_promote_candidate(
        review_service,
        predicate="oc:first_identity_demo",
        entity_id="ent:org:ussocom",
        entity_type="oc:organization",
        source_ref="notes/identity_first.txt",
    )
    identity_service = IdentityService(db_path=review_service.store.db_path)
    first = identity_service.create_identity_for_entity(
        entity_id="ent:org:ussocom",
        created_by="analyst:first",
        display_label="USSOCOM",
    )
    _submit_and_promote_candidate(
        review_service,
        predicate="oc:second_identity_demo",
        entity_id="ent:org:ussocom",
        entity_type="oc:organization",
        source_ref="notes/identity_second.txt",
    )

    second = identity_service.create_identity_for_entity(
        entity_id="ent:org:ussocom",
        created_by="analyst:second",
        display_label="USSOCOM",
    )

    assert second.identity.identity_id == first.identity.identity_id


def test_attach_alias_membership_groups_two_promoted_entities_under_one_identity(
    tmp_path: Path,
) -> None:
    """Alias attachment should explicitly group a second promoted entity id."""

    review_service = _seed_review_service(tmp_path)
    _submit_and_promote_candidate(
        review_service,
        predicate="oc:identity_alias_one",
        entity_id="ent:person:eric_olson",
        entity_type="oc:person",
        source_ref="notes/alias_one.txt",
    )
    _submit_and_promote_candidate(
        review_service,
        predicate="oc:identity_alias_two",
        entity_id="ent:person:admiral_eric_olson",
        entity_type="oc:person",
        source_ref="notes/alias_two.txt",
    )
    identity_service = IdentityService(db_path=review_service.store.db_path)
    created = identity_service.create_identity_for_entity(
        entity_id="ent:person:eric_olson",
        created_by="analyst:identity",
        display_label="Eric Olson",
    )

    alias_membership = identity_service.attach_entity_alias(
        identity_id=created.identity.identity_id,
        entity_id="ent:person:admiral_eric_olson",
        attached_by="analyst:identity",
    )
    report = IdentityReportService(identity_service=identity_service).build_report()

    assert alias_membership.membership_kind == "alias"
    assert report.summary.total_identities == 1
    assert report.summary.total_memberships == 2
    bundle = report.identity_bundles[0]
    assert {membership.entity_id for membership in bundle.memberships} == {
        "ent:person:eric_olson",
        "ent:person:admiral_eric_olson",
    }


def test_external_references_are_explicitly_attached_or_unresolved(tmp_path: Path) -> None:
    """External reference state should be explicit instead of hidden strings."""

    review_service = _seed_review_service(tmp_path)
    _submit_and_promote_candidate(
        review_service,
        predicate="oc:identity_external_ref",
        entity_id="ent:person:eric_olson",
        entity_type="oc:person",
        source_ref="notes/external_ref.txt",
    )
    identity_service = IdentityService(db_path=review_service.store.db_path)
    identity_bundle = identity_service.create_identity_for_entity(
        entity_id="ent:person:eric_olson",
        created_by="analyst:identity",
        display_label="Eric Olson",
    )

    attached = identity_service.attach_external_reference(
        identity_id=identity_bundle.identity.identity_id,
        provider="wikidata",
        external_id="Q5388397",
        attached_by="analyst:identity",
        reference_label="Eric Olson",
    )
    unresolved = identity_service.record_unresolved_external_reference(
        identity_id=identity_bundle.identity.identity_id,
        provider="wikidata",
        unresolved_note="Possible match needs review",
        attached_by="analyst:identity",
    )
    report = IdentityReportService(identity_service=identity_service).build_report()

    assert attached.reference_status == "attached"
    assert attached.external_id == "Q5388397"
    assert unresolved.reference_status == "unresolved"
    assert unresolved.external_id is None
    assert unresolved.unresolved_note == "Possible match needs review"
    assert report.summary.total_external_references == 2
    assert report.summary.external_reference_status_counts == {
        "attached": 1,
        "unresolved": 1,
    }


def test_entity_cannot_silently_join_two_different_identities(tmp_path: Path) -> None:
    """Identity membership conflicts should fail loudly."""

    review_service = _seed_review_service(tmp_path)
    _submit_and_promote_candidate(
        review_service,
        predicate="oc:identity_conflict_one",
        entity_id="ent:person:eric_olson",
        entity_type="oc:person",
        source_ref="notes/conflict_one.txt",
    )
    _submit_and_promote_candidate(
        review_service,
        predicate="oc:identity_conflict_two",
        entity_id="ent:person:admiral_eric_olson",
        entity_type="oc:person",
        source_ref="notes/conflict_two.txt",
    )
    identity_service = IdentityService(db_path=review_service.store.db_path)
    first = identity_service.create_identity_for_entity(
        entity_id="ent:person:eric_olson",
        created_by="analyst:first",
        display_label="Eric Olson",
    )
    second = identity_service.create_identity_for_entity(
        entity_id="ent:person:admiral_eric_olson",
        created_by="analyst:second",
        display_label="Admiral Eric Olson",
    )

    with pytest.raises(
        IdentityConflictError,
        match="entity is already attached to a different identity",
    ):
        identity_service.attach_entity_alias(
            identity_id=first.identity.identity_id,
            entity_id=second.memberships[0].entity_id,
            attached_by="analyst:merge",
        )

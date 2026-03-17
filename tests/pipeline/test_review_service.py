"""Tests for the persisted review and overlay pipeline slices."""

from __future__ import annotations

from pathlib import Path
import sys
from typing import Mapping

from pydantic import JsonValue
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))

from onto_canon6.ontology_runtime import clear_loader_caches  # noqa: E402
from onto_canon6.pipeline import (  # noqa: E402
    CandidateAssertionImport,
    CandidateSubmissionResult,
    EvidenceSpan,
    OverlayApplicationService,
    ProfileRef,
    ReviewService,
    ReviewStoreConflictError,
    SourceArtifactRef,
)
from onto_canon6.surfaces import ReviewReportService  # noqa: E402


def setup_function() -> None:
    """Reset cached donor profile state between tests."""

    clear_loader_caches()


def _make_review_service(tmp_path: Path) -> ReviewService:
    """Create a review service with isolated review DB and overlay root."""

    return ReviewService(
        db_path=tmp_path / "review.sqlite3",
        overlay_root=tmp_path / "ontology_overlays",
        default_acceptance_policy="record_only",
    )


def _make_overlay_service(
    tmp_path: Path,
    *,
    review_service: ReviewService,
) -> OverlayApplicationService:
    """Create a matching overlay application service for one test temp dir."""

    return OverlayApplicationService(
        db_path=review_service.store.db_path,
        overlay_root=tmp_path / "ontology_overlays",
    )


def _submit_candidate(
    service: ReviewService,
    *,
    payload: Mapping[str, object],
    profile_id: str,
    profile_version: str,
    submitted_by: str,
    source_ref: str,
    source_kind: str = "notebook",
) -> CandidateSubmissionResult:
    """Submit one candidate with explicit provenance into the review service."""

    return service.submit_candidate_assertion(
        payload=payload,
        profile_id=profile_id,
        profile_version=profile_version,
        submitted_by=submitted_by,
        source_kind=source_kind,
        source_ref=source_ref,
        source_label="phase test submission",
        source_metadata={"fixture": "test_review_service"},
    )


def test_submit_valid_dodaf_candidate_persists_reviewable_state(tmp_path: Path) -> None:
    """Valid closed-profile assertions should persist as reviewable candidates."""

    service = _make_review_service(tmp_path)

    result = _submit_candidate(
        service,
        payload={
            "predicate": "dodaf:activity_performs_resource",
            "roles": {
                "performer": [{"entity_id": "ent:performer:1", "entity_type": "dm2:Performer"}],
                "activity": [
                    {
                        "entity_id": "ent:activity:1",
                        "entity_type": "dm2:OperationalActivity",
                    }
                ],
                "resource": [{"entity_id": "ent:resource:1", "entity_type": "dm2:Resource"}],
            },
        },
        profile_id="dodaf",
        profile_version="0.1.0",
        submitted_by="analyst:test",
        source_ref="notebook://test/valid-dodaf",
    )

    assert result.candidate.validation_status == "valid"
    assert result.candidate.review_status == "pending_review"
    assert result.candidate.provenance.source_kind == "notebook"
    assert result.candidate.provenance.source_ref == "notebook://test/valid-dodaf"
    assert not result.proposals
    listed = service.list_candidate_assertions(review_status_filter="pending_review")
    assert [candidate.candidate_id for candidate in listed] == [result.candidate.candidate_id]


def test_submit_candidate_import_persists_claim_text_and_evidence_spans(tmp_path: Path) -> None:
    """Typed imports should persist source text, claim text, and verified spans."""

    service = _make_review_service(tmp_path)
    source_text = "Mission planning uses the radar system during the exercise."
    payload: dict[str, JsonValue] = {
        "predicate": "oc:uses_system_demo",
        "roles": {
            "subject": [{"entity_id": "ent:activity:mission_planning"}],
            "object": [{"entity_id": "ent:system:radar_system"}],
        },
    }
    candidate_import = CandidateAssertionImport(
        profile=ProfileRef(profile_id="default", profile_version="1.0.0"),
        payload=payload,
        submitted_by="analyst:text-import",
        source_artifact=SourceArtifactRef(
            source_kind="raw_text",
            source_ref="text://phase4/mission-planning",
            source_label="phase4 raw text fixture",
            source_metadata={"fixture": "phase4_import"},
            content_text=source_text,
        ),
        evidence_spans=(
            EvidenceSpan(start_char=0, end_char=16, text="Mission planning"),
            EvidenceSpan(start_char=26, end_char=38, text="radar system"),
        ),
        claim_text="Mission planning uses the radar system.",
    )

    result = service.submit_candidate_import(candidate_import=candidate_import)

    assert result.candidate.claim_text == "Mission planning uses the radar system."
    assert result.candidate.provenance.content_text == source_text
    assert result.candidate.evidence_spans == candidate_import.evidence_spans

    listed = service.list_candidate_assertions()
    assert listed[0].claim_text == "Mission planning uses the radar system."
    assert listed[0].evidence_spans == candidate_import.evidence_spans


def test_submit_invalid_candidate_persists_validation_snapshot(tmp_path: Path) -> None:
    """Invalid assertions should persist hard validation findings for review."""

    service = _make_review_service(tmp_path)

    result = _submit_candidate(
        service,
        payload={"roles": {}},
        profile_id="default",
        profile_version="1.0.0",
        submitted_by="analyst:test",
        source_ref="notebook://test/invalid-default",
    )

    assert result.candidate.validation_status == "invalid"
    assert result.candidate.review_status == "pending_review"
    assert [finding.code for finding in result.candidate.validation.hard_errors] == [
        "oc:hard_missing_predicate",
        "oc:hard_missing_roles",
    ]


def test_submit_candidate_import_requires_source_text_for_evidence_verification(
    tmp_path: Path,
) -> None:
    """Evidence spans should fail loudly when no source text is available."""

    service = _make_review_service(tmp_path)
    candidate_import = CandidateAssertionImport(
        profile=ProfileRef(profile_id="default", profile_version="1.0.0"),
        payload={"predicate": "oc:demo_predicate", "roles": {"subject": []}},
        submitted_by="analyst:text-import",
        source_artifact=SourceArtifactRef(
            source_kind="raw_text",
            source_ref="text://phase4/missing-text",
        ),
        evidence_spans=(EvidenceSpan(start_char=0, end_char=4, text="Demo"),),
    )

    with pytest.raises(
        ValueError,
        match="evidence spans require source_artifact.content_text",
    ):
        service.submit_candidate_import(candidate_import=candidate_import)


def test_submit_candidate_import_fails_on_mismatched_evidence_span(tmp_path: Path) -> None:
    """Evidence spans should fail loudly when offsets do not match the source text."""

    service = _make_review_service(tmp_path)
    candidate_import = CandidateAssertionImport(
        profile=ProfileRef(profile_id="default", profile_version="1.0.0"),
        payload={"predicate": "oc:demo_predicate", "roles": {"subject": []}},
        submitted_by="analyst:text-import",
        source_artifact=SourceArtifactRef(
            source_kind="raw_text",
            source_ref="text://phase4/mismatch",
            content_text="Alpha Beta",
        ),
        evidence_spans=(EvidenceSpan(start_char=0, end_char=5, text="Wrong"),),
    )

    with pytest.raises(
        ValueError,
        match="evidence span 0 text does not match source text",
    ):
        service.submit_candidate_import(candidate_import=candidate_import)


def test_mixed_mode_deduplicates_proposals_across_candidates(tmp_path: Path) -> None:
    """Repeated unknown predicates should reuse one persisted proposal record."""

    service = _make_review_service(tmp_path)
    payload = {
        "predicate": "oc:unknown_predicate_demo",
        "roles": {
            "subject": [{"entity_id": "ent:subject:1", "entity_type": "oc:person"}],
        },
    }

    first = _submit_candidate(
        service,
        payload=payload,
        profile_id="psyop_seed",
        profile_version="0.1.0",
        submitted_by="analyst:first",
        source_ref="notebook://test/mixed-1",
    )
    second = _submit_candidate(
        service,
        payload=payload,
        profile_id="psyop_seed",
        profile_version="0.1.0",
        submitted_by="analyst:second",
        source_ref="notebook://test/mixed-2",
    )

    assert first.candidate.validation_status == "needs_review"
    assert second.candidate.validation_status == "needs_review"
    assert len(first.proposals) == 1
    assert len(second.proposals) == 1
    assert first.proposals[0].proposal_id == second.proposals[0].proposal_id

    proposals = service.list_proposals(status_filter="pending")
    assert len(proposals) == 1
    assert proposals[0].candidate_ids == tuple(
        sorted([first.candidate.candidate_id, second.candidate.candidate_id])
    )


def test_candidate_accept_flow_persists_review_record(tmp_path: Path) -> None:
    """Valid candidates should transition from pending review to accepted."""

    service = _make_review_service(tmp_path)
    submission = _submit_candidate(
        service,
        payload={
            "predicate": "dodaf:activity_performs_resource",
            "roles": {
                "performer": [{"entity_id": "ent:performer:1", "entity_type": "dm2:Performer"}],
                "activity": [
                    {
                        "entity_id": "ent:activity:1",
                        "entity_type": "dm2:OperationalActivity",
                    }
                ],
                "resource": [{"entity_id": "ent:resource:1", "entity_type": "dm2:Resource"}],
            },
        },
        profile_id="dodaf",
        profile_version="0.1.0",
        submitted_by="analyst:test",
        source_ref="notebook://test/review-accept",
    )

    reviewed = service.review_candidate(
        candidate_id=submission.candidate.candidate_id,
        decision="accepted",
        actor_id="reviewer:test",
        note_text="candidate is structurally and semantically acceptable",
    )

    assert reviewed.review_status == "accepted"
    assert reviewed.review is not None
    assert reviewed.review.actor_id == "reviewer:test"
    assert reviewed.review.decision == "accepted"


def test_invalid_candidate_cannot_be_accepted(tmp_path: Path) -> None:
    """Invalid candidates should fail loudly on attempted acceptance."""

    service = _make_review_service(tmp_path)
    submission = _submit_candidate(
        service,
        payload={"roles": {}},
        profile_id="default",
        profile_version="1.0.0",
        submitted_by="analyst:test",
        source_ref="notebook://test/invalid-review",
    )

    with pytest.raises(ReviewStoreConflictError, match="invalid candidates cannot transition"):
        service.review_candidate(
            candidate_id=submission.candidate.candidate_id,
            decision="accepted",
            actor_id="reviewer:test",
        )


def test_reviewing_same_candidate_twice_conflicts(tmp_path: Path) -> None:
    """Candidate review should be terminal once one decision is recorded."""

    service = _make_review_service(tmp_path)
    submission = _submit_candidate(
        service,
        payload={
            "predicate": "dodaf:activity_performs_resource",
            "roles": {
                "performer": [{"entity_id": "ent:performer:1", "entity_type": "dm2:Performer"}],
                "activity": [
                    {
                        "entity_id": "ent:activity:1",
                        "entity_type": "dm2:OperationalActivity",
                    }
                ],
                "resource": [{"entity_id": "ent:resource:1", "entity_type": "dm2:Resource"}],
            },
        },
        profile_id="dodaf",
        profile_version="0.1.0",
        submitted_by="analyst:test",
        source_ref="notebook://test/review-conflict",
    )

    service.review_candidate(
        candidate_id=submission.candidate.candidate_id,
        decision="rejected",
        actor_id="reviewer:test",
    )

    with pytest.raises(ReviewStoreConflictError, match="terminal"):
        service.review_candidate(
            candidate_id=submission.candidate.candidate_id,
            decision="accepted",
            actor_id="reviewer:other",
        )


def test_accepting_proposal_uses_record_only_policy_by_default(tmp_path: Path) -> None:
    """Accepted proposals should record governance decisions without overlay apply by default."""

    service = _make_review_service(tmp_path)
    submission = _submit_candidate(
        service,
        payload={
            "predicate": "oc:unknown_predicate_demo",
            "roles": {
                "subject": [{"entity_id": "ent:subject:1", "entity_type": "oc:person"}],
            },
        },
        profile_id="psyop_seed",
        profile_version="0.1.0",
        submitted_by="analyst:test",
        source_ref="notebook://test/proposal-accept",
    )

    reviewed = service.review_proposal(
        proposal_id=submission.proposals[0].proposal_id,
        decision="accepted",
        actor_id="reviewer:test",
        note_text="reasonable new predicate",
    )

    assert reviewed.status == "accepted"
    assert reviewed.application_status == "recorded"
    assert reviewed.review is not None
    assert reviewed.review.acceptance_policy == "record_only"
    assert reviewed.review.actor_id == "reviewer:test"
    assert [proposal.proposal_id for proposal in service.list_proposals(status_filter="accepted")] == [
        reviewed.proposal_id
    ]


def test_accepting_mixed_profile_proposal_with_apply_to_overlay_sets_pending_apply(
    tmp_path: Path,
) -> None:
    """Mixed-profile proposals should carry a local overlay target and pending-apply state."""

    service = _make_review_service(tmp_path)
    submission = _submit_candidate(
        service,
        payload={
            "predicate": "oc:unknown_predicate_demo",
            "roles": {
                "subject": [{"entity_id": "ent:subject:1", "entity_type": "oc:person"}],
            },
        },
        profile_id="psyop_seed",
        profile_version="0.1.0",
        submitted_by="analyst:test",
        source_ref="notebook://test/proposal-apply",
    )

    reviewed = service.review_proposal(
        proposal_id=submission.proposals[0].proposal_id,
        decision="accepted",
        actor_id="reviewer:test",
        acceptance_policy="apply_to_overlay",
    )

    assert reviewed.target_pack is not None
    assert reviewed.application_status == "pending_overlay_apply"
    assert reviewed.review is not None
    assert reviewed.review.acceptance_policy == "apply_to_overlay"


def test_reviewing_same_proposal_twice_conflicts(tmp_path: Path) -> None:
    """Proposal review should be immutable once recorded."""

    service = _make_review_service(tmp_path)
    submission = _submit_candidate(
        service,
        payload={
            "predicate": "oc:unknown_predicate_demo",
            "roles": {
                "subject": [{"entity_id": "ent:subject:1", "entity_type": "oc:person"}],
            },
        },
        profile_id="psyop_seed",
        profile_version="0.1.0",
        submitted_by="analyst:test",
        source_ref="notebook://test/proposal-conflict",
    )

    service.review_proposal(
        proposal_id=submission.proposals[0].proposal_id,
        decision="rejected",
        actor_id="reviewer:test",
    )

    with pytest.raises(ReviewStoreConflictError, match="already reviewed"):
        service.review_proposal(
            proposal_id=submission.proposals[0].proposal_id,
            decision="accepted",
            actor_id="reviewer:other",
        )


def test_overlay_application_is_idempotent_and_updates_validation_behavior(tmp_path: Path) -> None:
    """Applied overlay predicates should become active on the next candidate submission."""

    service = _make_review_service(tmp_path)
    overlay_service = _make_overlay_service(tmp_path, review_service=service)
    initial = _submit_candidate(
        service,
        payload={
            "predicate": "oc:unknown_predicate_demo",
            "roles": {
                "subject": [{"entity_id": "ent:subject:1", "entity_type": "oc:person"}],
            },
        },
        profile_id="psyop_seed",
        profile_version="0.1.0",
        submitted_by="analyst:test",
        source_ref="notebook://test/overlay-initial",
    )
    reviewed = service.review_proposal(
        proposal_id=initial.proposals[0].proposal_id,
        decision="accepted",
        actor_id="reviewer:test",
        acceptance_policy="apply_to_overlay",
    )

    first_application = overlay_service.apply_proposal_to_overlay(
        proposal_id=reviewed.proposal_id,
        applied_by="reviewer:test",
    )
    second_application = overlay_service.apply_proposal_to_overlay(
        proposal_id=reviewed.proposal_id,
        applied_by="reviewer:test",
    )

    assert first_application.application_id == second_application.application_id
    assert first_application.overlay_pack.pack_id.endswith("__overlay")

    reapplied_candidate = _submit_candidate(
        service,
        payload={
            "predicate": "oc:unknown_predicate_demo",
            "roles": {
                "subject": [{"entity_id": "ent:subject:2", "entity_type": "oc:person"}],
            },
        },
        profile_id="psyop_seed",
        profile_version="0.1.0",
        submitted_by="analyst:test",
        source_ref="notebook://test/overlay-reapplied",
    )

    assert reapplied_candidate.candidate.validation_status == "valid"
    assert not reapplied_candidate.proposals


def test_overlay_application_requires_pending_overlay_apply_status(tmp_path: Path) -> None:
    """Record-only accepted proposals should fail loudly on explicit overlay application."""

    service = _make_review_service(tmp_path)
    overlay_service = _make_overlay_service(tmp_path, review_service=service)
    submission = _submit_candidate(
        service,
        payload={
            "predicate": "oc:unknown_predicate_demo",
            "roles": {
                "subject": [{"entity_id": "ent:subject:1", "entity_type": "oc:person"}],
            },
        },
        profile_id="psyop_seed",
        profile_version="0.1.0",
        submitted_by="analyst:test",
        source_ref="notebook://test/overlay-conflict",
    )
    reviewed = service.review_proposal(
        proposal_id=submission.proposals[0].proposal_id,
        decision="accepted",
        actor_id="reviewer:test",
        acceptance_policy="record_only",
    )

    with pytest.raises(ReviewStoreConflictError, match="pending_overlay_apply"):
        overlay_service.apply_proposal_to_overlay(
            proposal_id=reviewed.proposal_id,
            applied_by="reviewer:test",
        )


def test_review_report_surface_summarizes_filtered_state(tmp_path: Path) -> None:
    """The report surface should expose filtered candidates, proposals, and counts."""

    service = _make_review_service(tmp_path)
    accepted_candidate = _submit_candidate(
        service,
        payload={
            "predicate": "dodaf:activity_performs_resource",
            "roles": {
                "performer": [{"entity_id": "ent:performer:1", "entity_type": "dm2:Performer"}],
                "activity": [
                    {
                        "entity_id": "ent:activity:1",
                        "entity_type": "dm2:OperationalActivity",
                    }
                ],
                "resource": [{"entity_id": "ent:resource:1", "entity_type": "dm2:Resource"}],
            },
        },
        profile_id="dodaf",
        profile_version="0.1.0",
        submitted_by="analyst:test",
        source_ref="notebook://test/report-accepted",
    )
    pending_candidate = _submit_candidate(
        service,
        payload={
            "predicate": "oc:unknown_predicate_demo",
            "roles": {
                "subject": [{"entity_id": "ent:subject:1", "entity_type": "oc:person"}],
            },
        },
        profile_id="psyop_seed",
        profile_version="0.1.0",
        submitted_by="analyst:test",
        source_ref="notebook://test/report-pending",
    )
    service.review_candidate(
        candidate_id=accepted_candidate.candidate.candidate_id,
        decision="accepted",
        actor_id="reviewer:test",
    )

    report_service = ReviewReportService(review_service=service)
    accepted_report = report_service.build_report(review_status_filter="accepted")
    pending_proposal_report = report_service.build_report(
        proposal_status_filter="pending",
        profile_id="psyop_seed",
        profile_version="0.1.0",
    )

    assert accepted_report.summary.total_candidates == 1
    assert accepted_report.summary.candidate_review_status_counts == {"accepted": 1}
    assert accepted_report.candidates[0].candidate_id == accepted_candidate.candidate.candidate_id

    assert pending_proposal_report.summary.total_candidates == 1
    assert pending_proposal_report.summary.total_proposals == 1
    assert pending_proposal_report.summary.total_overlay_applications == 0
    assert pending_proposal_report.summary.proposal_status_counts == {"pending": 1}
    assert pending_proposal_report.candidates[0].candidate_id == pending_candidate.candidate.candidate_id


def test_review_report_includes_overlay_application_records(tmp_path: Path) -> None:
    """The report surface should distinguish applied overlay additions explicitly."""

    service = _make_review_service(tmp_path)
    overlay_service = _make_overlay_service(tmp_path, review_service=service)
    submission = _submit_candidate(
        service,
        payload={
            "predicate": "oc:unknown_predicate_demo",
            "roles": {
                "subject": [{"entity_id": "ent:subject:1", "entity_type": "oc:person"}],
            },
        },
        profile_id="psyop_seed",
        profile_version="0.1.0",
        submitted_by="analyst:test",
        source_ref="notebook://test/report-overlay",
    )
    reviewed = service.review_proposal(
        proposal_id=submission.proposals[0].proposal_id,
        decision="accepted",
        actor_id="reviewer:test",
        acceptance_policy="apply_to_overlay",
    )
    application = overlay_service.apply_proposal_to_overlay(
        proposal_id=reviewed.proposal_id,
        applied_by="reviewer:test",
    )

    report = ReviewReportService(
        review_service=service,
        overlay_service=overlay_service,
    ).build_report(profile_id="psyop_seed", profile_version="0.1.0")

    assert report.summary.total_overlay_applications == 1
    assert len(report.overlay_applications) == 1
    assert report.overlay_applications[0].application_id == application.application_id
    assert report.summary.overlay_pack_counts == {
        f"{application.overlay_pack.pack_id}@{application.overlay_pack.pack_version}": 1
    }

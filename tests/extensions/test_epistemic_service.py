"""Tests for the first epistemic extension slice."""

from __future__ import annotations

from pathlib import Path
import sys
from typing import Mapping

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))

from onto_canon6.extensions.epistemic import EpistemicService, EpistemicStoreConflictError  # noqa: E402
from onto_canon6.core import CanonicalGraphService  # noqa: E402
from onto_canon6.ontology_runtime import clear_loader_caches  # noqa: E402
from onto_canon6.pipeline import ReviewService  # noqa: E402
from onto_canon6.surfaces import EpistemicReportService  # noqa: E402


def setup_function() -> None:
    """Reset cached loader state between tests."""

    clear_loader_caches()


def _make_review_service(tmp_path: Path) -> ReviewService:
    """Create a review service with isolated persisted state for one test."""

    return ReviewService(
        db_path=tmp_path / "review.sqlite3",
        overlay_root=tmp_path / "ontology_overlays",
        default_acceptance_policy="record_only",
    )


def _submit_accepted_candidate(
    review_service: ReviewService,
    *,
    source_ref: str,
) -> str:
    """Persist and accept one candidate for epistemic tests."""

    submission = review_service.submit_candidate_assertion(
        payload={
            "predicate": "oc:epistemic_demo",
            "roles": {
                "subject": [{"entity_id": "ent:subject:demo"}],
            },
        },
        profile_id="default",
        profile_version="1.0.0",
        submitted_by="analyst:epistemic",
        source_kind="note",
        source_ref=source_ref,
    )
    reviewed = review_service.review_candidate(
        candidate_id=submission.candidate.candidate_id,
        decision="accepted",
        actor_id="analyst:reviewer",
    )
    return reviewed.candidate_id


def _submit_and_accept_candidate(
    review_service: ReviewService,
    *,
    payload: Mapping[str, object],
    source_ref: str,
) -> str:
    """Persist and accept one candidate with an explicit normalized payload."""

    submission = review_service.submit_candidate_assertion(
        payload=payload,
        profile_id="default",
        profile_version="1.0.0",
        submitted_by="analyst:epistemic",
        source_kind="note",
        source_ref=source_ref,
    )
    reviewed = review_service.review_candidate(
        candidate_id=submission.candidate.candidate_id,
        decision="accepted",
        actor_id="analyst:reviewer",
    )
    return reviewed.candidate_id


def _promote_candidate(review_service: ReviewService, *, candidate_id: str) -> str:
    """Promote one accepted candidate and return the assertion identifier."""

    promotion = CanonicalGraphService(db_path=review_service.store.db_path).promote_candidate(
        candidate_id=candidate_id,
        promoted_by="analyst:graph-promoter",
    )
    return promotion.assertion.assertion_id


def test_record_confidence_and_build_epistemic_report(tmp_path: Path) -> None:
    """Accepted candidates should support confidence assessments and report views."""

    review_service = _make_review_service(tmp_path)
    candidate_id = _submit_accepted_candidate(
        review_service,
        source_ref="notes/epistemic-confidence.txt",
    )
    epistemic_service = EpistemicService(db_path=review_service.store.db_path)

    confidence = epistemic_service.record_confidence(
        candidate_id=candidate_id,
        confidence_score=0.82,
        source_kind="user",
        actor_id="analyst:confidence",
        rationale="Human review judged the evidence strong but not conclusive.",
    )
    report = EpistemicReportService(epistemic_service=epistemic_service).build_candidate_report(
        candidate_id=candidate_id
    )

    assert confidence.candidate_id == candidate_id
    assert report.epistemic_status == "active"
    assert report.confidence is not None
    assert report.confidence.confidence_score == 0.82
    assert report.superseded_by is None
    assert report.supersedes == ()


def test_supersession_marks_prior_candidate_superseded(tmp_path: Path) -> None:
    """Supersession should attach only to accepted candidates and update reports."""

    review_service = _make_review_service(tmp_path)
    prior_candidate_id = _submit_accepted_candidate(
        review_service,
        source_ref="notes/prior.txt",
    )
    replacement_candidate_id = _submit_accepted_candidate(
        review_service,
        source_ref="notes/replacement.txt",
    )
    epistemic_service = EpistemicService(db_path=review_service.store.db_path)

    supersession = epistemic_service.record_supersession(
        prior_candidate_id=prior_candidate_id,
        replacement_candidate_id=replacement_candidate_id,
        actor_id="analyst:supersession",
        rationale="The replacement candidate narrows the older claim with better context.",
    )

    prior_report = epistemic_service.build_candidate_report(candidate_id=prior_candidate_id)
    replacement_report = epistemic_service.build_candidate_report(
        candidate_id=replacement_candidate_id
    )

    assert supersession.prior_candidate_id == prior_candidate_id
    assert prior_report.epistemic_status == "superseded"
    assert prior_report.superseded_by is not None
    assert prior_report.superseded_by.replacement_candidate_id == replacement_candidate_id
    assert replacement_report.epistemic_status == "active"
    assert len(replacement_report.supersedes) == 1
    assert replacement_report.supersedes[0].prior_candidate_id == prior_candidate_id


def test_extension_fails_loudly_for_non_accepted_candidates(tmp_path: Path) -> None:
    """The extension should reject confidence and supersession on unaccepted candidates."""

    review_service = _make_review_service(tmp_path)
    pending = review_service.submit_candidate_assertion(
        payload={"predicate": "oc:pending_epistemic_demo", "roles": {"subject": []}},
        profile_id="default",
        profile_version="1.0.0",
        submitted_by="analyst:epistemic",
        source_kind="note",
        source_ref="notes/pending.txt",
    )
    accepted_candidate_id = _submit_accepted_candidate(
        review_service,
        source_ref="notes/accepted.txt",
    )
    epistemic_service = EpistemicService(db_path=review_service.store.db_path)

    with pytest.raises(
        EpistemicStoreConflictError,
        match="epistemic extension requires accepted candidate",
    ):
        epistemic_service.record_confidence(
            candidate_id=pending.candidate.candidate_id,
            confidence_score=0.5,
            source_kind="user",
            actor_id="analyst:confidence",
        )

    with pytest.raises(
        EpistemicStoreConflictError,
        match="epistemic extension requires accepted candidate",
    ):
        epistemic_service.record_supersession(
            prior_candidate_id=accepted_candidate_id,
            replacement_candidate_id=pending.candidate.candidate_id,
            actor_id="analyst:supersession",
        )


def test_assertion_disposition_supports_weaken_reactivate_and_retract(tmp_path: Path) -> None:
    """Promoted assertions should support explicit non-terminal dispositions."""

    review_service = _make_review_service(tmp_path)
    candidate_id = _submit_and_accept_candidate(
        review_service,
        payload={
            "predicate": "oc:status_demo",
            "roles": {
                "subject": [{"entity_id": "ent:subject:status"}],
                "label": [{"kind": "value", "value_kind": "string", "value": "Status demo"}],
            },
        },
        source_ref="notes/status-demo.txt",
    )
    assertion_id = _promote_candidate(review_service, candidate_id=candidate_id)
    epistemic_service = EpistemicService(db_path=review_service.store.db_path)

    weakened = epistemic_service.record_assertion_disposition(
        assertion_id=assertion_id,
        target_status="weakened",
        actor_id="analyst:weaken",
        rationale="Evidence remains plausible but weaker than before.",
    )
    reactivated = epistemic_service.record_assertion_disposition(
        assertion_id=assertion_id,
        target_status="active",
        actor_id="analyst:reactivate",
        rationale="Follow-up review restored confidence in the assertion.",
    )
    retracted = epistemic_service.record_assertion_disposition(
        assertion_id=assertion_id,
        target_status="retracted",
        actor_id="analyst:retract",
        rationale="The assertion is no longer supportable.",
    )
    report = epistemic_service.build_promoted_assertion_report(assertion_id=assertion_id)

    assert weakened.prior_status == "active"
    assert weakened.target_status == "weakened"
    assert reactivated.prior_status == "weakened"
    assert reactivated.target_status == "active"
    assert retracted.prior_status == "active"
    assert report.epistemic_status == "retracted"
    assert report.current_disposition is not None
    assert report.current_disposition.target_status == "retracted"
    assert len(report.disposition_history) == 3


def test_retracted_assertion_disallows_further_transitions(tmp_path: Path) -> None:
    """Retracted promoted assertions should fail loudly on later transitions."""

    review_service = _make_review_service(tmp_path)
    candidate_id = _submit_and_accept_candidate(
        review_service,
        payload={
            "predicate": "oc:terminal_demo",
            "roles": {"subject": [{"entity_id": "ent:subject:terminal"}]},
        },
        source_ref="notes/terminal-demo.txt",
    )
    assertion_id = _promote_candidate(review_service, candidate_id=candidate_id)
    epistemic_service = EpistemicService(db_path=review_service.store.db_path)
    epistemic_service.record_assertion_disposition(
        assertion_id=assertion_id,
        target_status="retracted",
        actor_id="analyst:retract",
    )

    with pytest.raises(
        EpistemicStoreConflictError,
        match="invalid assertion transition",
    ):
        epistemic_service.record_assertion_disposition(
            assertion_id=assertion_id,
            target_status="active",
            actor_id="analyst:reactivate",
        )


def test_promoted_assertion_supersession_is_derived_from_candidate_supersession(tmp_path: Path) -> None:
    """Promoted assertion status should derive supersession from candidate review state."""

    review_service = _make_review_service(tmp_path)
    prior_candidate_id = _submit_and_accept_candidate(
        review_service,
        payload={
            "predicate": "oc:relationship_demo",
            "roles": {"subject": [{"entity_id": "ent:subject:olson"}]},
        },
        source_ref="notes/prior-promotion.txt",
    )
    replacement_candidate_id = _submit_and_accept_candidate(
        review_service,
        payload={
            "predicate": "oc:relationship_demo",
            "roles": {"subject": [{"entity_id": "ent:subject:olson"}]},
        },
        source_ref="notes/replacement-promotion.txt",
    )
    prior_assertion_id = _promote_candidate(review_service, candidate_id=prior_candidate_id)
    replacement_assertion_id = _promote_candidate(
        review_service,
        candidate_id=replacement_candidate_id,
    )
    epistemic_service = EpistemicService(db_path=review_service.store.db_path)
    epistemic_service.record_supersession(
        prior_candidate_id=prior_candidate_id,
        replacement_candidate_id=replacement_candidate_id,
        actor_id="analyst:supersession",
        rationale="The replacement candidate is more precise.",
    )

    report = epistemic_service.build_promoted_assertion_report(assertion_id=prior_assertion_id)

    assert report.epistemic_status == "superseded"
    assert report.superseded_by is not None
    assert report.superseded_by.replacement_candidate_id == replacement_candidate_id
    assert report.superseded_by_assertion_id == replacement_assertion_id


def test_promoted_assertion_report_derives_corroboration_and_tension(tmp_path: Path) -> None:
    """The promoted-assertion report should surface corroboration and tension deterministically."""

    review_service = _make_review_service(tmp_path)
    corroborating_payload = {
        "predicate": "oc:hold_command_role",
        "roles": {
            "commander": [{"entity_id": "ent:person:eric_olson"}],
            "organization": [{"entity_id": "ent:org:ussocom"}],
            "title": [{"kind": "value", "value_kind": "string", "value": "Commander"}],
        },
    }
    corroborating_a = _submit_and_accept_candidate(
        review_service,
        payload=corroborating_payload,
        source_ref="notes/corroborating-a.txt",
    )
    corroborating_b = _submit_and_accept_candidate(
        review_service,
        payload=corroborating_payload,
        source_ref="notes/corroborating-b.txt",
    )
    tension_a = _submit_and_accept_candidate(
        review_service,
        payload={
            "predicate": "oc:hold_command_role",
            "roles": {
                "commander": [{"entity_id": "ent:person:john_smith"}],
                "organization": [{"entity_id": "ent:org:joint_staff"}],
                "title": [{"kind": "value", "value_kind": "string", "value": "Commander"}],
            },
        },
        source_ref="notes/tension-a.txt",
    )
    tension_b = _submit_and_accept_candidate(
        review_service,
        payload={
            "predicate": "oc:hold_command_role",
            "roles": {
                "commander": [{"entity_id": "ent:person:john_smith"}],
                "organization": [{"entity_id": "ent:org:joint_staff"}],
                "title": [{"kind": "value", "value_kind": "string", "value": "Director"}],
            },
        },
        source_ref="notes/tension-b.txt",
    )
    corroborating_assertion_a = _promote_candidate(review_service, candidate_id=corroborating_a)
    corroborating_assertion_b = _promote_candidate(review_service, candidate_id=corroborating_b)
    _promote_candidate(review_service, candidate_id=tension_a)
    _promote_candidate(review_service, candidate_id=tension_b)
    epistemic_service = EpistemicService(db_path=review_service.store.db_path)

    report = epistemic_service.build_promoted_assertion_collection_report()

    assert report.summary.total_assertions == 4
    assert report.summary.total_corroboration_groups == 1
    assert report.summary.total_tension_pairs == 1
    corroboration_group = report.corroboration_groups[0]
    assert corroboration_group.assertion_ids == (
        corroborating_assertion_a,
        corroborating_assertion_b,
    )
    first_report = next(
        item for item in report.assertion_reports if item.assertion.assertion_id == corroborating_assertion_a
    )
    assert first_report.corroborating_assertion_ids == (corroborating_assertion_b,)
    assert first_report.tensions == ()
    tension_report = next(
        item
        for item in report.assertion_reports
        if item.assertion.source_candidate_id == tension_a
    )
    assert len(tension_report.tensions) == 1
    assert tension_report.tensions[0].tension_kind == "role_filler_conflict"

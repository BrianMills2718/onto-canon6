"""Tests for the first epistemic extension slice."""

from __future__ import annotations

from pathlib import Path
import sys

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))

from onto_canon6.extensions.epistemic import EpistemicService, EpistemicStoreConflictError  # noqa: E402
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

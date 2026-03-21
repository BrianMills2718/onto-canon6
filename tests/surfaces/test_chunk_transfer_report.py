"""Tests for the chunk-level transfer report surface."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import pytest

from onto_canon6.pipeline import ReviewService
from onto_canon6.surfaces import ChunkTransferReportService


def _submit_reviewed_candidate(
    *,
    review_service: ReviewService,
    source_ref: str,
    decision: Literal["accepted", "rejected"],
    predicate: str,
) -> None:
    """Persist and review one small candidate under one shared source_ref."""

    submission = review_service.submit_candidate_assertion(
        payload={"predicate": predicate, "roles": {}},
        profile_id="default",
        profile_version="1.0.0",
        submitted_by="analyst:test",
        source_kind="text_file",
        source_ref=source_ref,
        source_label=Path(source_ref).name,
        source_text=f"{predicate} evidence text",
    )
    review_service.review_candidate(
        candidate_id=submission.candidate.candidate_id,
        decision=decision,
        actor_id="analyst:reviewer",
    )


def test_chunk_transfer_report_classifies_positive_reviewed_chunk(tmp_path: Path) -> None:
    """A fully reviewed chunk with a high acceptance rate should be positive."""

    review_service = ReviewService(
        db_path=tmp_path / "review.sqlite3",
        permissive_review=True,
    )
    source_ref = "chunk://positive"
    _submit_reviewed_candidate(
        review_service=review_service,
        source_ref=source_ref,
        decision="accepted",
        predicate="oc:predicate_a",
    )
    _submit_reviewed_candidate(
        review_service=review_service,
        source_ref=source_ref,
        decision="accepted",
        predicate="oc:predicate_b",
    )
    _submit_reviewed_candidate(
        review_service=review_service,
        source_ref=source_ref,
        decision="accepted",
        predicate="oc:predicate_c",
    )
    _submit_reviewed_candidate(
        review_service=review_service,
        source_ref=source_ref,
        decision="accepted",
        predicate="oc:predicate_d",
    )
    _submit_reviewed_candidate(
        review_service=review_service,
        source_ref=source_ref,
        decision="rejected",
        predicate="oc:predicate_e",
    )

    report = ChunkTransferReportService(review_service=review_service).build_report(
        source_ref=source_ref,
        prompt_ref="onto_canon6.extraction.text_to_candidate_assertions_compact_v2@2",
        selection_task="budget_extraction",
    )

    assert report.summary.verdict == "positive"
    assert report.summary.accepted_candidates == 4
    assert report.summary.rejected_candidates == 1
    assert report.summary.acceptance_rate == pytest.approx(0.8)
    assert report.prompt_ref == "onto_canon6.extraction.text_to_candidate_assertions_compact_v2@2"
    assert report.selection_task == "budget_extraction"


def test_chunk_transfer_report_classifies_negative_reviewed_chunk(tmp_path: Path) -> None:
    """A fully reviewed chunk with no accepted candidates should be negative."""

    review_service = ReviewService(
        db_path=tmp_path / "review.sqlite3",
        permissive_review=True,
    )
    source_ref = "chunk://negative"
    _submit_reviewed_candidate(
        review_service=review_service,
        source_ref=source_ref,
        decision="rejected",
        predicate="oc:predicate_a",
    )
    _submit_reviewed_candidate(
        review_service=review_service,
        source_ref=source_ref,
        decision="rejected",
        predicate="oc:predicate_b",
    )

    report = ChunkTransferReportService(review_service=review_service).build_report(
        source_ref=source_ref,
    )

    assert report.summary.verdict == "negative"
    assert report.summary.accepted_candidates == 0
    assert report.summary.rejected_candidates == 2
    assert report.summary.acceptance_rate == 0.0


def test_chunk_transfer_report_fails_loud_when_pending_review_remains(tmp_path: Path) -> None:
    """The report should reject incomplete review state by default."""

    review_service = ReviewService(
        db_path=tmp_path / "review.sqlite3",
        permissive_review=True,
    )
    source_ref = "chunk://pending"
    review_service.submit_candidate_assertion(
        payload={"predicate": "oc:predicate_a", "roles": {}},
        profile_id="default",
        profile_version="1.0.0",
        submitted_by="analyst:test",
        source_kind="text_file",
        source_ref=source_ref,
        source_label="pending",
        source_text="pending evidence text",
    )

    with pytest.raises(
        ValueError,
        match="chunk transfer report requires review-complete candidates",
    ):
        ChunkTransferReportService(review_service=review_service).build_report(
            source_ref=source_ref,
        )

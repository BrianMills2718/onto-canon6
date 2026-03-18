"""Tests for the narrow Phase 8 artifact-lineage slice."""

from __future__ import annotations

from pathlib import Path
import sys

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))

from onto_canon6.artifacts import ArtifactLineageService, ArtifactStoreConflictError  # noqa: E402
from onto_canon6.ontology_runtime import clear_loader_caches  # noqa: E402
from onto_canon6.pipeline import ReviewService  # noqa: E402
from onto_canon6.surfaces import LineageReportService  # noqa: E402


def setup_function() -> None:
    """Reset cached profile state between tests."""

    clear_loader_caches()


def _make_review_service(tmp_path: Path) -> ReviewService:
    """Create a review service with isolated persisted state for one test."""

    return ReviewService(
        db_path=tmp_path / "review.sqlite3",
        overlay_root=tmp_path / "ontology_overlays",
        default_acceptance_policy="record_only",
    )


def test_candidate_lineage_report_exposes_source_and_analysis_support(tmp_path: Path) -> None:
    """A candidate report should show direct support links and ancestor artifacts."""

    review_service = _make_review_service(tmp_path)
    submission = review_service.submit_candidate_assertion(
        payload={
            "predicate": "oc:uses_reviewed_artifact_support",
            "roles": {
                "subject": [{"entity_id": "ent:account:x"}],
                "object": [{"entity_id": "ent:campaign:network"}],
            },
        },
        profile_id="default",
        profile_version="1.0.0",
        submitted_by="analyst:artifact-test",
        source_kind="report_file",
        source_ref="reports/campaign_summary.txt",
        source_label="campaign summary report",
        source_text="Account X appears central in the campaign network.",
    )

    artifact_service = ArtifactLineageService(db_path=review_service.store.db_path)
    source_artifact = artifact_service.register_artifact(
        artifact_kind="source",
        uri="reports/campaign_summary.txt",
        label="campaign summary report",
        metadata={"format": "txt"},
    )
    dataset_artifact = artifact_service.register_artifact(
        artifact_kind="derived_dataset",
        uri="derived/retweet_graph.graphml",
        label="retweet graph",
        metadata={"format": "graphml"},
    )
    analysis_artifact = artifact_service.register_artifact(
        artifact_kind="analysis_result",
        uri="analysis/centrality_scores.json",
        label="centrality scores",
        metadata={"metric": "betweenness"},
    )

    artifact_service.add_lineage_edge(
        parent_artifact_id=source_artifact.artifact_id,
        child_artifact_id=dataset_artifact.artifact_id,
    )
    artifact_service.add_lineage_edge(
        parent_artifact_id=dataset_artifact.artifact_id,
        child_artifact_id=analysis_artifact.artifact_id,
    )
    artifact_service.link_candidate_artifact(
        candidate_id=submission.candidate.candidate_id,
        artifact_id=source_artifact.artifact_id,
        support_kind="quoted_from",
        reference_detail="source paragraph 1",
    )
    artifact_service.link_candidate_artifact(
        candidate_id=submission.candidate.candidate_id,
        artifact_id=analysis_artifact.artifact_id,
        support_kind="supported_by_analysis",
        reference_detail="betweenness 0.89",
    )

    report = LineageReportService(artifact_service=artifact_service).build_candidate_report(
        candidate_id=submission.candidate.candidate_id
    )

    assert report.candidate.candidate_id == submission.candidate.candidate_id
    assert [link.support_kind for link in report.direct_artifact_links] == [
        "quoted_from",
        "supported_by_analysis",
    ]
    assert {artifact.artifact_kind for artifact in report.artifacts} == {
        "source",
        "derived_dataset",
        "analysis_result",
    }
    assert {(edge.parent_artifact_id, edge.child_artifact_id) for edge in report.lineage_edges} == {
        (source_artifact.artifact_id, dataset_artifact.artifact_id),
        (dataset_artifact.artifact_id, analysis_artifact.artifact_id),
    }


def test_candidate_artifact_link_fails_loud_on_mismatched_support_kind(tmp_path: Path) -> None:
    """Support-kind validation should reject links that contradict artifact kind."""

    review_service = _make_review_service(tmp_path)
    submission = review_service.submit_candidate_assertion(
        payload={"predicate": "oc:demo", "roles": {"subject": []}},
        profile_id="default",
        profile_version="1.0.0",
        submitted_by="analyst:artifact-test",
        source_kind="note",
        source_ref="notes/demo.txt",
    )
    artifact_service = ArtifactLineageService(db_path=review_service.store.db_path)
    source_artifact = artifact_service.register_artifact(
        artifact_kind="source",
        uri="notes/demo.txt",
    )

    with pytest.raises(
        ValueError,
        match="support_kind 'supported_by_analysis' is not valid for artifact_kind 'source'",
    ):
        artifact_service.link_candidate_artifact(
            candidate_id=submission.candidate.candidate_id,
            artifact_id=source_artifact.artifact_id,
            support_kind="supported_by_analysis",
        )


def test_candidate_artifact_link_conflict_fails_loudly(tmp_path: Path) -> None:
    """A reused candidate-artifact link should reject conflicting detail text."""

    review_service = _make_review_service(tmp_path)
    submission = review_service.submit_candidate_assertion(
        payload={"predicate": "oc:demo", "roles": {"subject": []}},
        profile_id="default",
        profile_version="1.0.0",
        submitted_by="analyst:artifact-test",
        source_kind="note",
        source_ref="notes/demo.txt",
    )
    artifact_service = ArtifactLineageService(db_path=review_service.store.db_path)
    analysis_artifact = artifact_service.register_artifact(
        artifact_kind="analysis_result",
        uri="analysis/demo.json",
    )

    artifact_service.link_candidate_artifact(
        candidate_id=submission.candidate.candidate_id,
        artifact_id=analysis_artifact.artifact_id,
        support_kind="supported_by_analysis",
        reference_detail="score 0.42",
    )

    with pytest.raises(
        ArtifactStoreConflictError,
        match="candidate artifact link already exists with different reference_detail",
    ):
        artifact_service.link_candidate_artifact(
            candidate_id=submission.candidate.candidate_id,
            artifact_id=analysis_artifact.artifact_id,
            support_kind="supported_by_analysis",
            reference_detail="score 0.43",
        )

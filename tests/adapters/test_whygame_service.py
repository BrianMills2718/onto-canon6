"""Tests for the successor-local WhyGame relationship adapter."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import TypeAdapter

from onto_canon6.adapters import WhyGameImportService
from onto_canon6.pipeline import ReviewService
from onto_canon6.surfaces import GovernedWorkflowBundleService

_WHYGAME_FIXTURE_ADAPTER = TypeAdapter(list[dict[str, object]])


def _load_fixture() -> list[dict[str, object]]:
    """Load the shared WhyGame relationship fixture used for Phase 14 proofs."""

    fixture_path = Path("tests/fixtures/whygame_relationship_facts.json")
    return _WHYGAME_FIXTURE_ADAPTER.validate_json(fixture_path.read_text(encoding="utf-8"))


def test_whygame_import_creates_reviewable_candidates_and_artifact_links(
    tmp_path: Path,
) -> None:
    """WhyGame relationship imports should persist candidates and visible artifact links."""

    review_service = ReviewService(
        db_path=tmp_path / "review.sqlite3",
        overlay_root=tmp_path / "overlays",
    )
    service = WhyGameImportService(review_service=review_service)

    request = service.build_default_request(
        facts=_load_fixture(),
        submitted_by="analyst:whygame-test",
        source_ref="whygame://fixture/ai-military",
        source_label="WhyGame fixture",
        artifact_uri="artifact://whygame/ai-military",
    )

    result = service.import_request(request=request)

    assert result.profile.profile_id == "whygame_minimal_strict"
    assert result.artifact is not None
    assert result.artifact.artifact_kind == "analysis_result"
    assert len(result.submissions) == 2
    assert len(result.artifact_links) == 2
    first_candidate = result.submissions[0].candidate
    assert first_candidate.validation_status == "valid"
    assert first_candidate.review_status == "pending_review"
    assert first_candidate.provenance.source_kind == "whygame_hypergraph"
    assert first_candidate.provenance.source_ref == "whygame://fixture/ai-military"
    assert first_candidate.provenance.source_metadata["fact_id"] == "wg_fact_001"
    assert first_candidate.claim_text == "AI integration supports military modernization."


def test_whygame_imported_provenance_flows_into_governed_bundle(tmp_path: Path) -> None:
    """Accepted WhyGame candidates should surface artifact provenance in the governed bundle."""

    review_service = ReviewService(
        db_path=tmp_path / "review.sqlite3",
        overlay_root=tmp_path / "overlays",
    )
    service = WhyGameImportService(review_service=review_service)
    result = service.import_request(
        request=service.build_default_request(
            facts=_load_fixture()[:1],
            submitted_by="analyst:whygame-test",
            source_ref="whygame://fixture/ai-military",
            source_label="WhyGame fixture",
            artifact_uri="artifact://whygame/ai-military",
        )
    )

    candidate_id = result.submissions[0].candidate.candidate_id
    review_service.review_candidate(
        candidate_id=candidate_id,
        decision="accepted",
        actor_id="analyst:reviewer",
    )
    bundle = GovernedWorkflowBundleService(review_service=review_service).build_bundle(
        candidate_ids=(candidate_id,),
    )

    candidate_bundle = bundle.candidate_bundles[0]
    assert candidate_bundle.candidate.candidate_id == candidate_id
    assert candidate_bundle.artifacts[0].uri == "artifact://whygame/ai-military"
    assert candidate_bundle.artifact_links[0].reference_detail == "wg_fact_001"


def test_whygame_import_rejects_non_relationship_fact_type(tmp_path: Path) -> None:
    """The narrow Phase 14 adapter should fail loudly on unsupported WhyGame facts."""

    review_service = ReviewService(
        db_path=tmp_path / "review.sqlite3",
        overlay_root=tmp_path / "overlays",
    )
    service = WhyGameImportService(review_service=review_service)

    with pytest.raises(ValueError):
        service.build_default_request(
            facts=[
                {
                    "id": "wg_fact_bad",
                    "fact_type": "QUESTION",
                    "roles": {"question": "Why?"},
                    "context": {},
                    "confidence": 1.0,
                    "metadata": {},
                }
            ],
            submitted_by="analyst:whygame-test",
            source_ref="whygame://fixture/bad",
        )

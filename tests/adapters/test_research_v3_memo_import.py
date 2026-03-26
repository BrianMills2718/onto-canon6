"""Tests for the research_v3 memo.yaml import adapter."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from onto_canon6.adapters.research_v3_import import (
    import_and_submit_memo,
    import_research_v3_memo,
    load_research_v3_memo,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures"
SAMPLE_MEMO = FIXTURES_DIR / "sample_memo.yaml"


def _write_memo_yaml(tmp_path: Path, memo_data: dict) -> Path:
    """Write a test memo.yaml file."""
    memo_path = tmp_path / "memo.yaml"
    with memo_path.open("w") as f:
        yaml.dump(memo_data, f)
    return memo_path


MINIMAL_MEMO = {
    "question": "What happened with Project Alpha?",
    "goal": "Determine the timeline and outcome of Project Alpha.",
    "key_findings": [
        {
            "claim": "Project Alpha received $10 million in funding in 2024.",
            "source_urls": ["https://example.com/alpha-funding"],
            "confidence": 0.8,
            "corroborated": True,
            "tags": ["funding", "project_alpha"],
        },
        {
            "claim": "The project was cancelled in Q3 2025 due to cost overruns.",
            "source_urls": [
                "https://example.com/alpha-cancellation",
                "https://example.com/gao-report",
            ],
            "confidence": 0.9,
            "corroborated": True,
            "tags": ["cancellation", "project_alpha"],
        },
        {
            "claim": "Three subcontractors were involved but only one delivered on time.",
            "source_urls": [],
            "confidence": 0.5,
            "corroborated": False,
            "tags": ["subcontractors"],
        },
    ],
}


class TestLoadResearchV3Memo:
    """Test basic memo.yaml loading."""

    def test_load_fixture(self) -> None:
        """The sample fixture loads without error."""
        data = load_research_v3_memo(SAMPLE_MEMO)
        assert "key_findings" in data
        assert len(data["key_findings"]) == 3

    def test_load_returns_dict(self, tmp_path: Path) -> None:
        """Loading a memo returns a dict."""
        memo_path = _write_memo_yaml(tmp_path, MINIMAL_MEMO)
        data = load_research_v3_memo(memo_path)
        assert isinstance(data, dict)
        assert data["question"] == "What happened with Project Alpha?"


class TestImportResearchV3Memo:
    """Test the memo import pipeline."""

    def test_correct_count(self, tmp_path: Path) -> None:
        """Parse memo.yaml produces correct number of CandidateAssertionImport objects."""
        memo_path = _write_memo_yaml(tmp_path, MINIMAL_MEMO)
        imports = import_research_v3_memo(memo_path)
        assert len(imports) == 3

    def test_provenance_source_kind(self, tmp_path: Path) -> None:
        """source_kind is set to research_v3_memo."""
        memo_path = _write_memo_yaml(tmp_path, MINIMAL_MEMO)
        imports = import_research_v3_memo(memo_path)
        for imp in imports:
            assert imp.source_artifact.source_kind == "research_v3_memo"

    def test_provenance_source_ref(self, tmp_path: Path) -> None:
        """source_ref encodes the memo filename and finding index."""
        memo_path = _write_memo_yaml(tmp_path, MINIMAL_MEMO)
        imports = import_research_v3_memo(memo_path)
        assert imports[0].source_artifact.source_ref == "memo.yaml:finding_0"
        assert imports[1].source_artifact.source_ref == "memo.yaml:finding_1"
        assert imports[2].source_artifact.source_ref == "memo.yaml:finding_2"

    def test_provenance_submitted_by(self, tmp_path: Path) -> None:
        """submitted_by defaults to adapter:research_v3_memo."""
        memo_path = _write_memo_yaml(tmp_path, MINIMAL_MEMO)
        imports = import_research_v3_memo(memo_path)
        for imp in imports:
            assert imp.submitted_by == "adapter:research_v3_memo"

    def test_confidence_in_metadata(self, tmp_path: Path) -> None:
        """Confidence is preserved in source_metadata."""
        memo_path = _write_memo_yaml(tmp_path, MINIMAL_MEMO)
        imports = import_research_v3_memo(memo_path)
        assert imports[0].source_artifact.source_metadata["confidence"] == 0.8
        assert imports[1].source_artifact.source_metadata["confidence"] == 0.9
        assert imports[2].source_artifact.source_metadata["confidence"] == 0.5

    def test_corroboration_in_metadata(self, tmp_path: Path) -> None:
        """Corroboration status is mapped into source_metadata."""
        memo_path = _write_memo_yaml(tmp_path, MINIMAL_MEMO)
        imports = import_research_v3_memo(memo_path)
        assert imports[0].source_artifact.source_metadata["corroboration_status"] == "corroborated"
        assert imports[2].source_artifact.source_metadata["corroboration_status"] == "unverified"

    def test_tags_in_metadata(self, tmp_path: Path) -> None:
        """Tags are preserved in source_metadata."""
        memo_path = _write_memo_yaml(tmp_path, MINIMAL_MEMO)
        imports = import_research_v3_memo(memo_path)
        assert imports[0].source_artifact.source_metadata["tags"] == ["funding", "project_alpha"]
        assert imports[2].source_artifact.source_metadata["tags"] == ["subcontractors"]

    def test_source_urls_in_metadata(self, tmp_path: Path) -> None:
        """Source URLs are preserved in source_metadata."""
        memo_path = _write_memo_yaml(tmp_path, MINIMAL_MEMO)
        imports = import_research_v3_memo(memo_path)
        assert imports[0].source_artifact.source_metadata["source_urls"] == [
            "https://example.com/alpha-funding",
        ]
        assert len(imports[1].source_artifact.source_metadata["source_urls"]) == 2

    def test_investigation_question_in_metadata(self, tmp_path: Path) -> None:
        """Investigation question is preserved in source_metadata."""
        memo_path = _write_memo_yaml(tmp_path, MINIMAL_MEMO)
        imports = import_research_v3_memo(memo_path)
        for imp in imports:
            assert imp.source_artifact.source_metadata["investigation_question"] == (
                "What happened with Project Alpha?"
            )

    def test_limit_parameter(self, tmp_path: Path) -> None:
        """limit parameter caps the number of candidates."""
        memo_path = _write_memo_yaml(tmp_path, MINIMAL_MEMO)
        imports = import_research_v3_memo(memo_path, limit=1)
        assert len(imports) == 1
        # Should be the first finding
        assert "$10 million" in imports[0].claim_text

    def test_empty_memo(self, tmp_path: Path) -> None:
        """Empty memo produces empty list without error."""
        memo_path = _write_memo_yaml(tmp_path, {"key_findings": []})
        imports = import_research_v3_memo(memo_path)
        assert len(imports) == 0

    def test_memo_without_findings_key(self, tmp_path: Path) -> None:
        """Memo missing key_findings key produces empty list."""
        memo_path = _write_memo_yaml(tmp_path, {"question": "test"})
        imports = import_research_v3_memo(memo_path)
        assert len(imports) == 0

    def test_claim_text_populated(self, tmp_path: Path) -> None:
        """claim_text is the finding's claim."""
        memo_path = _write_memo_yaml(tmp_path, MINIMAL_MEMO)
        imports = import_research_v3_memo(memo_path)
        assert "Project Alpha received $10 million" in imports[0].claim_text

    def test_content_text_matches_claim(self, tmp_path: Path) -> None:
        """content_text on the source artifact equals the claim."""
        memo_path = _write_memo_yaml(tmp_path, MINIMAL_MEMO)
        imports = import_research_v3_memo(memo_path)
        for imp in imports:
            assert imp.source_artifact.content_text == imp.claim_text

    def test_payload_has_predicate(self, tmp_path: Path) -> None:
        """Payload includes a minimal predicate."""
        memo_path = _write_memo_yaml(tmp_path, MINIMAL_MEMO)
        imports = import_research_v3_memo(memo_path)
        assert imports[0].payload["predicate"] == "rv3:asserts"

    def test_payload_has_confidence(self, tmp_path: Path) -> None:
        """Payload includes the confidence score."""
        memo_path = _write_memo_yaml(tmp_path, MINIMAL_MEMO)
        imports = import_research_v3_memo(memo_path)
        assert imports[0].payload["confidence"] == 0.8

    def test_payload_has_corroboration(self, tmp_path: Path) -> None:
        """Payload includes corroboration status string."""
        memo_path = _write_memo_yaml(tmp_path, MINIMAL_MEMO)
        imports = import_research_v3_memo(memo_path)
        assert imports[0].payload["research_v3_corroboration"] == "corroborated"
        assert imports[2].payload["research_v3_corroboration"] == "unverified"

    def test_custom_profile(self, tmp_path: Path) -> None:
        """Custom profile_id and version are passed through."""
        memo_path = _write_memo_yaml(tmp_path, MINIMAL_MEMO)
        imports = import_research_v3_memo(
            memo_path,
            profile_id="custom_profile",
            profile_version="2.0.0",
        )
        assert imports[0].profile.profile_id == "custom_profile"
        assert imports[0].profile.profile_version == "2.0.0"

    def test_custom_submitted_by(self, tmp_path: Path) -> None:
        """Custom submitted_by is passed through."""
        memo_path = _write_memo_yaml(tmp_path, MINIMAL_MEMO)
        imports = import_research_v3_memo(
            memo_path,
            submitted_by="agent:test_runner",
        )
        for imp in imports:
            assert imp.submitted_by == "agent:test_runner"

    def test_finding_with_empty_claim_skipped(self, tmp_path: Path) -> None:
        """Findings with empty claim text are skipped."""
        memo_data = {
            "question": "test",
            "key_findings": [
                {"claim": "", "confidence": 0.5},
                {"claim": "A real finding.", "confidence": 0.7},
            ],
        }
        memo_path = _write_memo_yaml(tmp_path, memo_data)
        imports = import_research_v3_memo(memo_path)
        assert len(imports) == 1
        assert "real finding" in imports[0].claim_text

    def test_fixture_file_import(self) -> None:
        """The bundled fixture file imports successfully."""
        imports = import_research_v3_memo(SAMPLE_MEMO)
        assert len(imports) == 3
        # Verify the fixture's investigation question
        for imp in imports:
            assert "lobbying" in imp.source_artifact.source_metadata["investigation_question"].lower()


class TestImportAndSubmitMemo:
    """Test the convenience submit wrapper."""

    def test_calls_review_service(self, tmp_path: Path) -> None:
        """import_and_submit_memo calls submit_candidate_import for each import."""

        class FakeCandidate:
            candidate_id = "cand_001"
            claim_text = "test claim"
            validation_status = "valid"

        class FakeResult:
            candidate = FakeCandidate()

        class FakeReviewService:
            def __init__(self) -> None:
                self.calls: list = []

            def submit_candidate_import(self, *, candidate_import):
                self.calls.append(candidate_import)
                return FakeResult()

        memo_path = _write_memo_yaml(tmp_path, MINIMAL_MEMO)
        service = FakeReviewService()
        results = import_and_submit_memo(memo_path, service)

        assert len(results) == 3
        assert len(service.calls) == 3
        assert results[0]["candidate_id"] == "cand_001"
        assert results[0]["validation_status"] == "valid"

    def test_limit_passed_through(self, tmp_path: Path) -> None:
        """limit kwarg is forwarded to import_research_v3_memo."""

        class FakeCandidate:
            candidate_id = "cand_001"
            claim_text = "test"
            validation_status = "valid"

        class FakeResult:
            candidate = FakeCandidate()

        class FakeReviewService:
            def __init__(self) -> None:
                self.calls: list = []

            def submit_candidate_import(self, *, candidate_import):
                self.calls.append(candidate_import)
                return FakeResult()

        memo_path = _write_memo_yaml(tmp_path, MINIMAL_MEMO)
        service = FakeReviewService()
        results = import_and_submit_memo(memo_path, service, limit=2)

        assert len(results) == 2
        assert len(service.calls) == 2

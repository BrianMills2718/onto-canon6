"""Tests for temporal qualifier extraction and export."""

from __future__ import annotations

import pytest

from onto_canon6.pipeline.text_extraction import ExtractedCandidate, ExtractedEvidenceSpan
from onto_canon6.pipeline import ProfileRef


class TestExtractedCandidateTemporalFields:
    """Test that temporal fields are correctly modeled."""

    def test_temporal_fields_optional(self) -> None:
        """valid_from and valid_to default to None."""
        candidate = ExtractedCandidate(
            predicate="test:pred",
            roles={"ARG0": [{"kind": "entity", "entity_type": "oc:person", "name": "Alice"}]},
            evidence_spans=[ExtractedEvidenceSpan(text="Alice did something.", start_char=0, end_char=20)],
        )
        assert candidate.valid_from is None
        assert candidate.valid_to is None

    def test_temporal_fields_set(self) -> None:
        """valid_from and valid_to can be set."""
        candidate = ExtractedCandidate(
            predicate="test:pred",
            roles={"ARG0": [{"kind": "entity", "entity_type": "oc:person", "name": "Alice"}]},
            evidence_spans=[ExtractedEvidenceSpan(text="Alice did something in 2023.", start_char=0, end_char=27)],
            valid_from="2023",
            valid_to="2024-06",
        )
        assert candidate.valid_from == "2023"
        assert candidate.valid_to == "2024-06"

    def test_temporal_fields_in_model_dump(self) -> None:
        """Temporal fields appear in model_dump when set."""
        candidate = ExtractedCandidate(
            predicate="test:pred",
            roles={"ARG0": [{"kind": "entity", "entity_type": "oc:person", "name": "Alice"}]},
            evidence_spans=[ExtractedEvidenceSpan(text="Test.", start_char=0, end_char=5)],
            valid_from="2023-06-05",
        )
        dumped = candidate.model_dump()
        assert dumped["valid_from"] == "2023-06-05"
        assert dumped["valid_to"] is None

    def test_temporal_fields_excluded_when_none(self) -> None:
        """Temporal fields excluded from model_dump(exclude_none=True)."""
        candidate = ExtractedCandidate(
            predicate="test:pred",
            roles={"ARG0": [{"kind": "entity", "entity_type": "oc:person", "name": "Alice"}]},
            evidence_spans=[ExtractedEvidenceSpan(text="Test.", start_char=0, end_char=5)],
        )
        dumped = candidate.model_dump(exclude_none=True)
        assert "valid_from" not in dumped
        assert "valid_to" not in dumped

    def test_temporal_in_json_schema(self) -> None:
        """Temporal fields appear in JSON schema for LLM structured output."""
        schema = ExtractedCandidate.model_json_schema()
        props = schema["properties"]
        assert "valid_from" in props
        assert "valid_to" in props
        # Both should be nullable (anyOf with string and null)
        vf = props["valid_from"]
        assert "description" in vf


class TestTemporalInFoundationExport:
    """Test temporal qualifiers in Foundation IR export."""

    def test_temporal_qualifiers_exported(self) -> None:
        """Temporal qualifiers appear in Foundation assertion qualifiers."""
        # This is an integration test that exercises the full path:
        # ExtractedCandidate → payload → DB → Foundation export
        # We test the export function directly with a mock assertion
        from onto_canon6.adapters.foundation_assertion_export import (
            promoted_assertion_to_foundation,
        )
        from onto_canon6.core.graph_models import PromotedGraphAssertionRecord

        assertion = PromotedGraphAssertionRecord(
            assertion_id="test_assertion",
            source_candidate_id="test_candidate",
            profile=ProfileRef(profile_id="test", profile_version="1.0.0"),
            predicate="test:pred",
            normalized_body={"predicate": "test:pred", "roles": {}, "valid_from": "2023-06-05", "valid_to": "2024-01"},
            claim_text="Test claim.",
            promoted_by="test",
            promoted_at="2026-03-26T00:00:00Z",
        )

        result = promoted_assertion_to_foundation(assertion, confidence=0.9)
        assert result.qualifiers.get("sys:valid_from") == "2023-06-05"
        assert result.qualifiers.get("sys:valid_to") == "2024-01"
        assert result.qualifiers.get("sys:confidence") == 0.9

    def test_no_temporal_no_qualifiers(self) -> None:
        """Assertions without temporal fields have no temporal qualifiers."""
        from onto_canon6.adapters.foundation_assertion_export import (
            promoted_assertion_to_foundation,
        )
        from onto_canon6.core.graph_models import PromotedGraphAssertionRecord

        assertion = PromotedGraphAssertionRecord(
            assertion_id="test_assertion",
            source_candidate_id="test_candidate",
            profile=ProfileRef(profile_id="test", profile_version="1.0.0"),
            predicate="test:pred",
            normalized_body={"predicate": "test:pred", "roles": {}},
            claim_text="Test claim.",
            promoted_by="test",
            promoted_at="2026-03-26T00:00:00Z",
        )

        result = promoted_assertion_to_foundation(assertion, confidence=None)
        assert "sys:valid_from" not in result.qualifiers
        assert "sys:valid_to" not in result.qualifiers

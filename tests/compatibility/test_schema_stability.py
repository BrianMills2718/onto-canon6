"""Schema stability gate tests (Plan 0026).

These tests verify that the 4 contractual surfaces have not had breaking
changes to their field names or types. They load canonical fixtures from
tests/fixtures/compatibility/ and compare against the current Pydantic models.

A failure here means a field was renamed, removed, or had its type changed.
This requires a Plan 0026 compatibility review before merging.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "compatibility"


def _load_fixture(name: str) -> dict:
    """Load a compatibility fixture by surface name."""
    path = FIXTURES_DIR / f"{name}.json"
    if not path.exists():
        pytest.skip(f"Fixture not found: {path}")
    return json.loads(path.read_text())


def _get_model_fields(model_class: type) -> dict[str, str]:
    """Get field names and type annotations from a Pydantic model."""
    return {k: str(v.annotation) for k, v in model_class.model_fields.items()}


class TestSurfaceA_PromotedGraph:
    """Compatibility check for promoted graph typed surface."""

    def test_assertion_record_fields(self) -> None:
        from onto_canon6.core.graph_models import PromotedGraphAssertionRecord
        fixture = _load_fixture("promoted_graph")
        expected = fixture["models"]["PromotedGraphAssertionRecord"]
        actual_fields = set(PromotedGraphAssertionRecord.model_fields.keys())
        expected_fields = set(expected["required_fields"])
        missing = expected_fields - actual_fields
        assert not missing, f"Breaking change: fields removed from PromotedGraphAssertionRecord: {missing}"

    def test_entity_record_fields(self) -> None:
        from onto_canon6.core.graph_models import PromotedGraphEntityRecord
        fixture = _load_fixture("promoted_graph")
        expected = fixture["models"]["PromotedGraphEntityRecord"]
        actual_fields = set(PromotedGraphEntityRecord.model_fields.keys())
        expected_fields = set(expected["required_fields"])
        missing = expected_fields - actual_fields
        assert not missing, f"Breaking change: fields removed from PromotedGraphEntityRecord: {missing}"

    def test_role_filler_record_fields(self) -> None:
        from onto_canon6.core.graph_models import PromotedGraphRoleFillerRecord
        fixture = _load_fixture("promoted_graph")
        expected = fixture["models"]["PromotedGraphRoleFillerRecord"]
        actual_fields = set(PromotedGraphRoleFillerRecord.model_fields.keys())
        expected_fields = set(expected["required_fields"])
        missing = expected_fields - actual_fields
        assert not missing, f"Breaking change: fields removed from PromotedGraphRoleFillerRecord: {missing}"


class TestSurfaceB_GovernedBundle:
    """Compatibility check for governed bundle export surface."""

    def test_workflow_bundle_fields(self) -> None:
        from onto_canon6.surfaces.governed_bundle import GovernedWorkflowBundle
        fixture = _load_fixture("governed_bundle")
        expected = fixture["models"]["GovernedWorkflowBundle"]
        actual_fields = set(GovernedWorkflowBundle.model_fields.keys())
        expected_fields = set(expected["required_fields"])
        missing = expected_fields - actual_fields
        assert not missing, f"Breaking change: fields removed from GovernedWorkflowBundle: {missing}"

    def test_candidate_bundle_fields(self) -> None:
        from onto_canon6.surfaces.governed_bundle import GovernedCandidateBundle
        fixture = _load_fixture("governed_bundle")
        expected = fixture["models"]["GovernedCandidateBundle"]
        actual_fields = set(GovernedCandidateBundle.model_fields.keys())
        expected_fields = set(expected["required_fields"])
        missing = expected_fields - actual_fields
        assert not missing, f"Breaking change: fields removed from GovernedCandidateBundle: {missing}"


class TestSurfaceC_FoundationIR:
    """Compatibility check for Foundation Assertion IR export surface."""

    def test_foundation_assertion_fields(self) -> None:
        from onto_canon6.adapters.foundation_assertion_export import FoundationAssertion
        fixture = _load_fixture("foundation_ir")
        expected = fixture["models"]["FoundationAssertion"]
        actual_fields = set(FoundationAssertion.model_fields.keys())
        expected_fields = set(expected["required_fields"])
        missing = expected_fields - actual_fields
        assert not missing, f"Breaking change: fields removed from FoundationAssertion: {missing}"


class TestSurfaceD_DigimonExport:
    """Compatibility check for DIGIMON v1 export seam."""

    def test_entity_record_fields(self) -> None:
        from onto_canon6.adapters.digimon_export import DigimonEntityRecord
        fixture = _load_fixture("digimon_v1_export")
        expected = fixture["models"]["DigimonEntityRecord"]
        actual_fields = set(DigimonEntityRecord.model_fields.keys())
        expected_fields = set(expected["required_fields"])
        missing = expected_fields - actual_fields
        assert not missing, f"Breaking change: fields removed from DigimonEntityRecord: {missing}"

    def test_relationship_record_fields(self) -> None:
        from onto_canon6.adapters.digimon_export import DigimonRelationshipRecord
        fixture = _load_fixture("digimon_v1_export")
        expected = fixture["models"]["DigimonRelationshipRecord"]
        actual_fields = set(DigimonRelationshipRecord.model_fields.keys())
        expected_fields = set(expected["required_fields"])
        missing = expected_fields - actual_fields
        assert not missing, f"Breaking change: fields removed from DigimonRelationshipRecord: {missing}"

    def test_field_types_stable(self) -> None:
        """Verify field types haven't changed incompatibly."""
        from onto_canon6.adapters.digimon_export import DigimonEntityRecord, DigimonRelationshipRecord
        fixture = _load_fixture("digimon_v1_export")

        for model_name, model_class in [
            ("DigimonEntityRecord", DigimonEntityRecord),
            ("DigimonRelationshipRecord", DigimonRelationshipRecord),
        ]:
            expected_types = fixture["models"][model_name]["field_types"]
            actual_types = _get_model_fields(model_class)
            for field, expected_type in expected_types.items():
                if field in actual_types:
                    assert actual_types[field] == expected_type, (
                        f"Breaking change: {model_name}.{field} type changed "
                        f"from {expected_type} to {actual_types[field]}"
                    )

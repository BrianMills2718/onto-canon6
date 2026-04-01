"""Round-trip contract test for onto-canon6 → DIGIMON boundary.

Validates that the Pydantic models at the boundary can serialize and
deserialize without data loss, and that producer/consumer schema
compatibility holds.
"""

from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from onto_canon6.adapters.digimon_export import (
    DigimonEntityRecord,
    DigimonExportBundle,
    DigimonRelationshipRecord,
)


# --- Fixtures ---


def _sample_entity() -> DigimonEntityRecord:
    return DigimonEntityRecord(
        entity_name="Shield AI",
        source_id="ent:progressive:shield_ai",
        entity_type="Corporation",
        description="Defense technology company",
        rank=1,
    )


def _sample_relationship() -> DigimonRelationshipRecord:
    return DigimonRelationshipRecord(
        src_id="Shield AI",
        tgt_id="US Department of Defense",
        relation_name="supply.01",
        description="Shield AI supplies autonomous systems to DoD",
        weight=0.85,
        source_id="asrt:progressive:001",
    )


def _sample_bundle() -> DigimonExportBundle:
    return DigimonExportBundle(
        entities=[_sample_entity()],
        relationships=[_sample_relationship()],
        source_onto_canon_db="/tmp/test.db",
    )


# --- Round-trip tests ---


class TestRoundTrip:
    """Verify JSONL serialization → deserialization preserves all fields."""

    def test_entity_round_trip(self) -> None:
        entity = _sample_entity()
        serialized = entity.model_dump_json()
        restored = DigimonEntityRecord.model_validate_json(serialized)
        assert restored == entity

    def test_relationship_round_trip(self) -> None:
        rel = _sample_relationship()
        serialized = rel.model_dump_json()
        restored = DigimonRelationshipRecord.model_validate_json(serialized)
        assert restored == rel

    def test_bundle_round_trip(self) -> None:
        bundle = _sample_bundle()
        serialized = bundle.model_dump_json()
        restored = DigimonExportBundle.model_validate_json(serialized)
        assert restored == bundle
        assert len(restored.entities) == 1
        assert len(restored.relationships) == 1

    def test_jsonl_format_round_trip(self) -> None:
        """Simulate JSONL export (one record per line) and re-parse."""
        entities = [_sample_entity()]
        relationships = [_sample_relationship()]

        # Export as JSONL
        entity_lines = [e.model_dump_json() for e in entities]
        rel_lines = [r.model_dump_json() for r in relationships]

        # Re-import from JSONL
        restored_entities = [
            DigimonEntityRecord.model_validate_json(line) for line in entity_lines
        ]
        restored_rels = [
            DigimonRelationshipRecord.model_validate_json(line) for line in rel_lines
        ]

        assert restored_entities == entities
        assert restored_rels == relationships


# --- Schema compatibility tests ---


class TestSchemaCompatibility:
    """Verify producer schema constraints (extra=forbid) work correctly."""

    def test_entity_rejects_extra_fields(self) -> None:
        with pytest.raises(ValidationError):
            DigimonEntityRecord(
                entity_name="Test",
                source_id="ent:test",
                unexpected_field="oops",  # type: ignore[call-arg]
            )

    def test_relationship_rejects_extra_fields(self) -> None:
        with pytest.raises(ValidationError):
            DigimonRelationshipRecord(
                src_id="A",
                tgt_id="B",
                unexpected_field="oops",  # type: ignore[call-arg]
            )

    def test_entity_requires_mandatory_fields(self) -> None:
        with pytest.raises(ValidationError):
            DigimonEntityRecord(entity_name="Test")  # missing source_id  # type: ignore[call-arg]

    def test_relationship_requires_mandatory_fields(self) -> None:
        with pytest.raises(ValidationError):
            DigimonRelationshipRecord(src_id="A")  # missing tgt_id  # type: ignore[call-arg]

    def test_entity_defaults_are_correct(self) -> None:
        entity = DigimonEntityRecord(entity_name="Test", source_id="ent:test")
        assert entity.entity_type == ""
        assert entity.description == ""
        assert entity.rank == 0

    def test_relationship_defaults_are_correct(self) -> None:
        rel = DigimonRelationshipRecord(src_id="A", tgt_id="B")
        assert rel.relation_name == ""
        assert rel.weight == 1.0
        assert rel.keywords == ""
        assert rel.source_id == ""


# --- JSON Schema generation test ---


class TestJsonSchema:
    """Verify that model_json_schema() produces valid schemas for downstream consumers."""

    def test_entity_schema_has_descriptions(self) -> None:
        schema = DigimonEntityRecord.model_json_schema()
        props = schema["properties"]
        for field_name in ["entity_name", "source_id", "entity_type", "description", "rank"]:
            assert field_name in props, f"Missing field: {field_name}"
            assert "description" in props[field_name], f"Missing description on {field_name}"

    def test_relationship_schema_has_descriptions(self) -> None:
        schema = DigimonRelationshipRecord.model_json_schema()
        props = schema["properties"]
        for field_name in ["src_id", "tgt_id", "relation_name", "description", "weight", "source_id"]:
            assert field_name in props, f"Missing field: {field_name}"
            assert "description" in props[field_name], f"Missing description on {field_name}"

    def test_bundle_schema_references_nested_models(self) -> None:
        schema = DigimonExportBundle.model_json_schema()
        # Bundle should reference entity and relationship schemas
        assert "entities" in schema["properties"]
        assert "relationships" in schema["properties"]

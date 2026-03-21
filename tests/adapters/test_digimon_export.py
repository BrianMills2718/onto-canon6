"""Tests for the Digimon export adapter.

Tests the mapping from onto-canon6 promoted graph assertions and entities
to Digimon-compatible ``EntityRecord`` and ``RelationshipRecord`` JSONL
output.

Tests run against the real review databases when available (Shield AI and
PSYOP), and also include a minimal fixture-based test that does not depend
on any real database files.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from onto_canon6.adapters.digimon_export import (
    DigimonEntityRecord,
    DigimonExportBundle,
    DigimonRelationshipRecord,
    export_for_digimon_from_db,
    write_digimon_jsonl,
)

SHIELD_AI_DB = Path("var/progressive_review_v2.sqlite3")
PSYOP_DB = Path("var/progressive_review_psyop.sqlite3")


def _insert_candidate(conn: sqlite3.Connection, candidate_id: str, *, claim_text: str = "") -> None:
    """Insert a minimal candidate assertion row for foreign key satisfaction.

    Uses explicit column names to stay resilient to schema evolution.
    """
    conn.execute(
        """
        INSERT INTO candidate_assertions(
            candidate_id, profile_id, profile_version, validation_status,
            review_status, payload_hash, payload_json, normalized_payload_json,
            validation_json, submitted_by, source_kind, source_ref,
            source_label, source_metadata_json, source_text, claim_text,
            submitted_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            candidate_id, "test", "1.0", "valid",
            "accepted", "hash", "{}", "{}",
            "[]", "tester", "text", "test_ref",
            "test", "{}", "test text", claim_text,
            "2026-01-01T00:00:00Z",
        ),
    )


def _has_promoted_data(db_path: Path) -> bool:
    """Check whether the DB exists and has promoted graph tables with data."""
    if not db_path.exists():
        return False
    try:
        conn = sqlite3.connect(db_path)
        count = conn.execute("SELECT COUNT(*) FROM promoted_graph_assertions").fetchone()[0]
        conn.close()
        return int(count) > 0
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Real-DB tests: Shield AI
# ---------------------------------------------------------------------------


@pytest.mark.skipif(
    not _has_promoted_data(SHIELD_AI_DB),
    reason="Shield AI review DB not available",
)
class TestShieldAIExport:
    """Export from the real Shield AI review database."""

    def test_export_produces_bundle_with_correct_counts(self) -> None:
        """Export produces a bundle with entities and relationships matching DB counts."""
        bundle = export_for_digimon_from_db(SHIELD_AI_DB)
        assert isinstance(bundle, DigimonExportBundle)
        # DB has 110 entities and 99 assertions
        assert len(bundle.entities) == 110
        assert len(bundle.relationships) > 0
        assert bundle.source_onto_canon_db == str(SHIELD_AI_DB.resolve())

    def test_entity_fields_map_correctly(self) -> None:
        """Entity fields are correctly mapped from onto-canon6 to Digimon format."""
        bundle = export_for_digimon_from_db(SHIELD_AI_DB)
        # Find Shield AI entity
        shield_entities = [e for e in bundle.entities if "Shield AI" in e.entity_name]
        assert len(shield_entities) >= 1
        shield = shield_entities[0]
        assert shield.entity_name == "Shield AI"
        assert shield.source_id == "ent:progressive:shield_ai"
        assert shield.entity_type == "Corporation"
        assert shield.rank == 0

    def test_relationship_fields_map_correctly(self) -> None:
        """Relationship fields are correctly mapped from assertions + role fillers."""
        bundle = export_for_digimon_from_db(SHIELD_AI_DB)
        # Find a contract relationship
        contract_rels = [
            r for r in bundle.relationships if r.relation_name == "contract_enter_agreement"
        ]
        assert len(contract_rels) >= 1
        first = contract_rels[0]
        assert first.src_id  # ARG0 entity name
        assert first.tgt_id  # ARG1 entity name
        assert first.relation_name == "contract_enter_agreement"
        assert first.source_id.startswith("gassert_")
        assert first.weight > 0

    def test_single_argument_predicates_handled(self) -> None:
        """Assertions with only ARG0 or only ARG1 produce relationships with one empty endpoint."""
        bundle = export_for_digimon_from_db(SHIELD_AI_DB)
        # Look for relationships with an empty src or tgt
        single_arg_rels = [
            r for r in bundle.relationships if r.src_id == "" or r.tgt_id == ""
        ]
        # The Shield AI DB has some single-argument assertions
        assert len(single_arg_rels) >= 1
        for rel in single_arg_rels:
            # At least one endpoint must be filled
            assert rel.src_id or rel.tgt_id


# ---------------------------------------------------------------------------
# Real-DB tests: PSYOP
# ---------------------------------------------------------------------------


@pytest.mark.skipif(
    not _has_promoted_data(PSYOP_DB),
    reason="PSYOP review DB not available",
)
class TestPSYOPExport:
    """Export from the real PSYOP review database."""

    def test_export_produces_bundle_with_correct_counts(self) -> None:
        """Export produces a bundle with entities and relationships matching DB counts."""
        bundle = export_for_digimon_from_db(PSYOP_DB)
        assert isinstance(bundle, DigimonExportBundle)
        assert len(bundle.entities) == 358
        assert len(bundle.relationships) > 0
        assert bundle.source_onto_canon_db == str(PSYOP_DB.resolve())


# ---------------------------------------------------------------------------
# JSONL round-trip
# ---------------------------------------------------------------------------


@pytest.mark.skipif(
    not _has_promoted_data(SHIELD_AI_DB),
    reason="Shield AI review DB not available",
)
class TestJSONLOutput:
    """Write JSONL files and verify they parse back correctly."""

    def test_write_and_read_back(self, tmp_path: Path) -> None:
        """JSONL files written from an export can be parsed back to matching records."""
        bundle = export_for_digimon_from_db(SHIELD_AI_DB)
        entities_path, relationships_path = write_digimon_jsonl(bundle, tmp_path)

        assert entities_path.exists()
        assert relationships_path.exists()

        # Parse entities
        with entities_path.open() as f:
            entity_lines = [json.loads(line) for line in f if line.strip()]
        assert len(entity_lines) == len(bundle.entities)
        for original, parsed in zip(bundle.entities, entity_lines):
            assert parsed["entity_name"] == original.entity_name
            assert parsed["source_id"] == original.source_id
            assert parsed["entity_type"] == original.entity_type
            assert parsed["rank"] == original.rank

        # Parse relationships
        with relationships_path.open() as f:
            rel_lines = [json.loads(line) for line in f if line.strip()]
        assert len(rel_lines) == len(bundle.relationships)
        for original, parsed in zip(bundle.relationships, rel_lines):
            assert parsed["src_id"] == original.src_id
            assert parsed["tgt_id"] == original.tgt_id
            assert parsed["relation_name"] == original.relation_name
            assert parsed["source_id"] == original.source_id
            assert parsed["weight"] == original.weight


# ---------------------------------------------------------------------------
# Fixture-based tests (no real DB dependency)
# ---------------------------------------------------------------------------


class TestFixtureBasedExport:
    """Tests using a minimal in-memory fixture for environments without the real DBs."""

    @pytest.fixture()
    def fixture_db(self, tmp_path: Path) -> Path:
        """Create a minimal review database with promoted graph data.

        Uses ``ReviewService`` and ``CanonicalGraphStore`` to create the full
        correct schema, then inserts test data directly via SQL.  This avoids
        maintaining a hand-rolled schema that drifts from the real store.
        """
        db_path = tmp_path / "test_review.sqlite3"
        # Let the real services initialize the full schema
        from onto_canon6.pipeline.service import ReviewService
        from onto_canon6.core.graph_store import CanonicalGraphStore

        ReviewService(db_path=db_path)
        CanonicalGraphStore(db_path)

        conn = sqlite3.connect(db_path)
        conn.execute("PRAGMA foreign_keys = OFF")

        # Insert candidate assertions (foreign key targets for promoted assertions)
        _insert_candidate(conn, "cand_1", claim_text="test claim")
        _insert_candidate(conn, "cand_2", claim_text="single arg claim")

        # Insert entities
        conn.execute(
            """INSERT INTO promoted_graph_entities VALUES (
                'ent:test:alice', 'Person', 'cand_1', '2026-01-01T00:00:00Z'
            )"""
        )
        conn.execute(
            """INSERT INTO promoted_graph_entities VALUES (
                'ent:test:acme', 'Corporation', 'cand_1', '2026-01-01T00:00:00Z'
            )"""
        )

        # Insert a two-argument assertion
        body = json.dumps({
            "predicate": "employ",
            "roles": {
                "ARG0": [{"kind": "entity", "entity_id": "ent:test:acme", "entity_type": "Corporation", "name": "ACME Corp"}],
                "ARG1": [{"kind": "entity", "entity_id": "ent:test:alice", "entity_type": "Person", "name": "Alice"}],
            },
            "confidence": 0.9,
        })
        conn.execute(
            """INSERT INTO promoted_graph_assertions VALUES (
                'gassert_test_1', 'cand_1', 'test', '1.0', 'employ', ?, 'ACME Corp employs Alice', 'tester', '2026-01-01T00:00:00Z'
            )""",
            (body,),
        )
        conn.execute(
            """INSERT INTO promoted_graph_role_fillers VALUES (
                'gassert_test_1', 'ARG0', 0, 'entity', 'ent:test:acme', 'Corporation', NULL, NULL
            )"""
        )
        conn.execute(
            """INSERT INTO promoted_graph_role_fillers VALUES (
                'gassert_test_1', 'ARG1', 0, 'entity', 'ent:test:alice', 'Person', NULL, NULL
            )"""
        )

        # Insert a single-argument assertion (only ARG1)
        body_single = json.dumps({
            "predicate": "return_come_back",
            "roles": {
                "ARG1": [{"kind": "entity", "entity_id": "ent:test:alice", "entity_type": "Person", "name": "Alice"}],
            },
            "confidence": 0.7,
        })
        conn.execute(
            """INSERT INTO promoted_graph_assertions VALUES (
                'gassert_test_2', 'cand_2', 'test', '1.0', 'return_come_back', ?, 'Alice returned', 'tester', '2026-01-01T00:00:00Z'
            )""",
            (body_single,),
        )
        conn.execute(
            """INSERT INTO promoted_graph_role_fillers VALUES (
                'gassert_test_2', 'ARG1', 0, 'entity', 'ent:test:alice', 'Person', NULL, NULL
            )"""
        )

        conn.commit()
        conn.close()
        return db_path

    def test_fixture_export_entity_count(self, fixture_db: Path) -> None:
        """Fixture DB exports the correct number of entities."""
        bundle = export_for_digimon_from_db(fixture_db)
        assert len(bundle.entities) == 2

    def test_fixture_export_relationship_count(self, fixture_db: Path) -> None:
        """Fixture DB exports the correct number of relationships."""
        bundle = export_for_digimon_from_db(fixture_db)
        assert len(bundle.relationships) == 2

    def test_fixture_entity_name_resolved(self, fixture_db: Path) -> None:
        """Entity names are resolved from assertion body, not from entity_id slug."""
        bundle = export_for_digimon_from_db(fixture_db)
        names = {e.entity_name for e in bundle.entities}
        assert "Alice" in names
        assert "ACME Corp" in names

    def test_fixture_entity_source_id_preserved(self, fixture_db: Path) -> None:
        """Entity source_id preserves the onto-canon6 entity_id."""
        bundle = export_for_digimon_from_db(fixture_db)
        source_ids = {e.source_id for e in bundle.entities}
        assert "ent:test:alice" in source_ids
        assert "ent:test:acme" in source_ids

    def test_fixture_two_arg_relationship(self, fixture_db: Path) -> None:
        """Two-argument assertion produces a relationship with both endpoints filled."""
        bundle = export_for_digimon_from_db(fixture_db)
        employ_rels = [r for r in bundle.relationships if r.relation_name == "employ"]
        assert len(employ_rels) == 1
        rel = employ_rels[0]
        assert rel.src_id == "ACME Corp"
        assert rel.tgt_id == "Alice"
        assert rel.relation_name == "employ"
        assert rel.description == "ACME Corp employs Alice"
        assert rel.weight == pytest.approx(0.9)
        assert rel.source_id == "gassert_test_1"

    def test_fixture_single_arg_relationship(self, fixture_db: Path) -> None:
        """Single-argument assertion produces a relationship with one empty endpoint."""
        bundle = export_for_digimon_from_db(fixture_db)
        return_rels = [r for r in bundle.relationships if r.relation_name == "return_come_back"]
        assert len(return_rels) == 1
        rel = return_rels[0]
        # Only ARG1, so src_id is empty
        assert rel.src_id == ""
        assert rel.tgt_id == "Alice"
        assert rel.weight == pytest.approx(0.7)

    def test_fixture_jsonl_roundtrip(self, fixture_db: Path, tmp_path: Path) -> None:
        """JSONL output from fixture DB parses back to matching records."""
        bundle = export_for_digimon_from_db(fixture_db)
        entities_path, relationships_path = write_digimon_jsonl(bundle, tmp_path / "out")

        with entities_path.open() as f:
            entity_records = [json.loads(line) for line in f if line.strip()]
        assert len(entity_records) == 2

        with relationships_path.open() as f:
            rel_records = [json.loads(line) for line in f if line.strip()]
        assert len(rel_records) == 2

    def test_empty_graph_produces_empty_bundle(self, tmp_path: Path) -> None:
        """An empty promoted graph produces an empty bundle without crashing."""
        db_path = tmp_path / "empty.sqlite3"
        from onto_canon6.pipeline.service import ReviewService
        from onto_canon6.core.graph_store import CanonicalGraphStore

        ReviewService(db_path=db_path)
        CanonicalGraphStore(db_path)

        bundle = export_for_digimon_from_db(db_path)
        assert len(bundle.entities) == 0
        assert len(bundle.relationships) == 0

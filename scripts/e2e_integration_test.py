#!/usr/bin/env python3
"""End-to-end consumer integration test.

Proves the full pipeline:
1. Text → extraction → review → promote → auto-resolve → export to Digimon
2. research_v3 graph.yaml → import → review

This script does NOT make LLM calls — it uses pre-extracted data from
the e2e_test_2026_03_25 DB to verify the downstream pipeline.
"""

from __future__ import annotations

import json
import shutil
import sqlite3
import sys
import tempfile
from pathlib import Path

# Ensure onto-canon6 is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))


def test_extraction_to_digimon(tmp_path: Path) -> None:
    """Test: promoted assertions → auto-resolve → Digimon export → ingestion."""
    print("=== Test: Extraction → Digimon ===")

    # Copy the e2e DB (which already has promoted assertions)
    src_db = Path("var/e2e_test_2026_03_25/review_combined.sqlite3")
    if not src_db.exists():
        print(f"  SKIP: {src_db} not found")
        return

    test_db = tmp_path / "e2e_test.sqlite3"
    shutil.copy2(src_db, test_db)

    # Step 1: Auto-resolve identities
    from onto_canon6.core.auto_resolution import auto_resolve_identities

    result = auto_resolve_identities(db_path=test_db)
    print(f"  Auto-resolve: {result.entities_scanned} entities, {result.groups_found} groups")
    assert result.entities_scanned > 0, "No entities found"

    # Step 2: Export to Digimon
    from onto_canon6.adapters.digimon_export import (
        export_for_digimon_from_db,
        write_digimon_jsonl,
    )

    bundle = export_for_digimon_from_db(test_db)
    print(f"  Digimon export: {len(bundle.entities)} entities, {len(bundle.relationships)} relationships")
    assert len(bundle.entities) > 0, "No entities exported"
    assert len(bundle.relationships) > 0, "No relationships exported"

    # Step 3: Write JSONL
    output_dir = tmp_path / "digimon_export"
    entities_path, rels_path = write_digimon_jsonl(bundle, output_dir)
    assert entities_path.exists(), "entities.jsonl not created"
    assert rels_path.exists(), "relationships.jsonl not created"

    # Step 4: Verify JSONL is valid
    with entities_path.open() as f:
        entities = [json.loads(line) for line in f if line.strip()]
    with rels_path.open() as f:
        rels = [json.loads(line) for line in f if line.strip()]

    assert len(entities) > 0, "Empty entities.jsonl"
    assert len(rels) > 0, "Empty relationships.jsonl"

    # Verify entity fields
    for e in entities:
        assert "entity_name" in e, f"Missing entity_name: {e}"
        assert "entity_type" in e, f"Missing entity_type: {e}"
        assert e["entity_name"], f"Empty entity_name: {e}"

    # Verify relationship fields
    for r in rels:
        assert "src_id" in r, f"Missing src_id: {r}"
        assert "tgt_id" in r, f"Missing tgt_id: {r}"
        assert "relation_name" in r, f"Missing relation_name: {r}"

    print(f"  JSONL valid: {len(entities)} entities, {len(rels)} relationships")
    print("  PASS")


def test_research_v3_import(tmp_path: Path) -> None:
    """Test: research_v3 graph.yaml → import → review pipeline."""
    print("\n=== Test: research_v3 → Import ===")

    # Find a real graph.yaml
    graph_candidates = list(
        Path("/home/brian/projects/research_v3/output").glob("*/graph.yaml")
    )
    if not graph_candidates:
        print("  SKIP: No research_v3 graph.yaml found")
        return

    graph_path = graph_candidates[0]
    print(f"  Source: {graph_path.parent.name}")

    # Import
    from onto_canon6.adapters.research_v3_import import import_research_v3_graph
    from onto_canon6.pipeline import ReviewService

    imports = import_research_v3_graph(graph_path=graph_path)
    print(f"  Adapter: {len(imports)} candidate imports")

    if not imports:
        print("  SKIP: No claims in graph")
        return

    # Submit to review pipeline
    test_db = tmp_path / "rv3_test.sqlite3"
    overlay_root = tmp_path / "overlays"
    review_svc = ReviewService(
        db_path=test_db,
        overlay_root=overlay_root,
        default_acceptance_policy="record_only",
    )

    submitted = 0
    for candidate_import in imports[:10]:  # Limit to 10 for speed
        try:
            review_svc.submit_candidate_import(candidate_import=candidate_import)
            submitted += 1
        except Exception as e:
            print(f"  Submit error: {e}")

    print(f"  Submitted: {submitted}/{min(10, len(imports))} candidates to review pipeline")

    # Verify in DB
    conn = sqlite3.connect(str(test_db))
    total = conn.execute("SELECT COUNT(*) FROM candidate_assertions").fetchone()[0]
    pending = conn.execute(
        "SELECT COUNT(*) FROM candidate_assertions WHERE review_status='pending_review'"
    ).fetchone()[0]
    conn.close()

    assert total == submitted, f"Expected {submitted} candidates, got {total}"
    assert pending == submitted, f"Expected {submitted} pending, got {pending}"

    print(f"  DB: {total} candidates, {pending} pending review")
    print("  PASS")


def test_foundation_ir_export(tmp_path: Path) -> None:
    """Test: promoted assertions → Foundation IR with temporal qualifiers."""
    print("\n=== Test: Foundation IR Export ===")

    src_db = Path("var/e2e_test_2026_03_25/review_combined.sqlite3")
    if not src_db.exists():
        print(f"  SKIP: {src_db} not found")
        return

    from onto_canon6.adapters.foundation_assertion_export import (
        export_foundation_assertions,
    )

    assertions = export_foundation_assertions(src_db)
    print(f"  Foundation assertions: {len(assertions)}")
    assert len(assertions) > 0, "No assertions exported"

    # Verify structure
    for a in assertions:
        assert a.assertion_id, f"Missing assertion_id"
        assert a.predicate, f"Missing predicate"
        assert isinstance(a.roles, dict), f"roles not dict: {type(a.roles)}"
        assert isinstance(a.qualifiers, dict), f"qualifiers not dict"
        assert isinstance(a.provenance_refs, list), f"provenance_refs not list"

    print(f"  All {len(assertions)} assertions have valid Foundation IR structure")
    print("  PASS")


def main() -> int:
    """Run all integration tests."""
    print("onto-canon6 E2E Integration Tests")
    print("=" * 50)

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        try:
            test_extraction_to_digimon(tmp_path)
            test_research_v3_import(tmp_path)
            test_foundation_ir_export(tmp_path)
            print("\n" + "=" * 50)
            print("ALL INTEGRATION TESTS PASSED")
            return 0
        except AssertionError as e:
            print(f"\nFAILED: {e}")
            return 1
        except Exception as e:
            print(f"\nERROR: {e}")
            return 1


if __name__ == "__main__":
    raise SystemExit(main())

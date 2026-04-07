"""Tests for the code_core ontology pack.

Verifies: pack loads, predicate count ≥25, all predicate_ids start with cc:,
role count ≥15, all role_ids start with cc.role., manifest is valid.
"""

from __future__ import annotations

import json

import pytest
import yaml

from onto_canon6.config import repo_root

_PACK_DIR = repo_root() / "ontology_packs" / "code_core" / "0.1.0"


class TestCodeCorePack:
    """Acceptance tests for the hand-authored code_core pack."""

    @pytest.fixture(autouse=True)
    def require_pack(self) -> None:
        if not _PACK_DIR.exists():
            pytest.skip("code_core pack not found")

    def test_predicate_types_count(self) -> None:
        """Pack must have at least 25 predicates."""
        lines = (_PACK_DIR / "predicate_types.jsonl").read_text().strip().splitlines()
        assert len(lines) >= 25, f"Expected ≥25 predicates, got {len(lines)}"

    def test_predicate_types_cc_prefix(self) -> None:
        """All predicate_ids must start with cc:."""
        rows = [json.loads(l) for l in (_PACK_DIR / "predicate_types.jsonl").read_text().splitlines()]
        bad = [r["predicate_id"] for r in rows if not r["predicate_id"].startswith("cc:")]
        assert not bad, f"predicate_ids missing cc: prefix: {bad}"

    def test_predicate_types_required_fields(self) -> None:
        """Each predicate row must have required fields."""
        rows = [json.loads(l) for l in (_PACK_DIR / "predicate_types.jsonl").read_text().splitlines()]
        for row in rows:
            assert "predicate_id" in row
            assert "family" in row
            assert "preferred_label" in row
            assert "status" in row
            assert row["status"] == "active"

    def test_key_predicates_present(self) -> None:
        """Critical predicates for the nanoGPT demo must be present."""
        rows = [json.loads(l) for l in (_PACK_DIR / "predicate_types.jsonl").read_text().splitlines()]
        ids = {r["predicate_id"] for r in rows}
        required = {
            "cc:implement_pattern",
            "cc:benchmark_performance",
            "cc:train_model",
            "cc:inherit",
            "cc:call",
            "cc:define",
        }
        missing = required - ids
        assert not missing, f"Required predicates missing: {missing}"

    def test_role_types_count(self) -> None:
        """Pack must have at least 15 role types."""
        lines = (_PACK_DIR / "role_types.jsonl").read_text().strip().splitlines()
        assert len(lines) >= 15, f"Expected ≥15 role types, got {len(lines)}"

    def test_role_types_cc_role_prefix(self) -> None:
        """All role_ids must start with cc.role."""
        rows = [json.loads(l) for l in (_PACK_DIR / "role_types.jsonl").read_text().splitlines()]
        bad = [r["role_id"] for r in rows if not r["role_id"].startswith("cc.role.")]
        assert not bad, f"role_ids missing cc.role. prefix: {bad}"

    def test_key_roles_present(self) -> None:
        """Critical roles for the nanoGPT demo must be present."""
        rows = [json.loads(l) for l in (_PACK_DIR / "role_types.jsonl").read_text().splitlines()]
        ids = {r["role_id"] for r in rows}
        required = {"cc.role.model", "cc.role.benchmark", "cc.role.score", "cc.role.implementer", "cc.role.pattern"}
        missing = required - ids
        assert not missing, f"Required roles missing: {missing}"

    def test_manifest_valid(self) -> None:
        """manifest.yaml must parse and have correct pack identity."""
        manifest = yaml.safe_load((_PACK_DIR / "manifest.yaml").read_text())
        assert manifest["pack"]["id"] == "code_core"
        assert manifest["pack"]["version"] == "0.1.0"
        assert manifest["capabilities"]["assertion_type"] == "n-ary"
        assert "predicate_types" in manifest["content"]
        assert "role_types" in manifest["content"]

"""Integration test for the import-research-v3 CLI command."""

from __future__ import annotations

import json
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

PYTHON = sys.executable
CLI_MODULE = "onto_canon6"


def _write_test_graph(tmp_path: Path) -> Path:
    """Write a minimal research_v3 graph.yaml for testing."""
    graph = {
        "goal": {"question": "test"},
        "entities": {
            "e1": {
                "id": "e1",
                "schema": "Company",
                "properties": {"name": ["TestCorp"]},
            },
            "e2": {
                "id": "e2",
                "schema": "Person",
                "properties": {"name": ["Jane Doe"]},
            },
        },
        "claims": [
            {
                "id": "C-test-001",
                "statement": "Jane Doe is CEO of TestCorp.",
                "entity_refs": ["e2", "e1"],
                "claim_type": "fact_claim",
                "source": {
                    "id": "s1",
                    "url": "https://example.com",
                    "source_type": "news",
                    "retrieved_at": "2026-03-26T00:00:00Z",
                },
                "corroboration_status": "unverified",
                "confidence": "high",
            },
        ],
    }
    path = tmp_path / "graph.yaml"
    with path.open("w") as f:
        yaml.dump(graph, f)
    return path


class TestImportResearchV3CLI:
    """Test the import-research-v3 CLI command end-to-end."""

    def test_import_produces_candidates(self, tmp_path: Path) -> None:
        """Import creates pending candidates in the review DB."""
        graph_path = _write_test_graph(tmp_path)
        db_path = tmp_path / "review.sqlite3"
        overlay_root = tmp_path / "overlays"

        result = subprocess.run(
            [
                PYTHON, "-m", CLI_MODULE,
                "import-research-v3",
                "--input", str(graph_path),
                "--review-db-path", str(db_path),
                "--overlay-root", str(overlay_root),
                "--output", "json",
            ],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).resolve().parent.parent.parent),
        )
        assert result.returncode == 0, f"CLI failed: {result.stderr}"

        output = json.loads(result.stdout)
        assert output["imported"] == 1
        assert len(output["candidates"]) == 1
        assert output["candidates"][0]["claim_text"] == "Jane Doe is CEO of TestCorp."

        # Verify DB
        conn = sqlite3.connect(str(db_path))
        count = conn.execute("SELECT COUNT(*) FROM candidate_assertions").fetchone()[0]
        conn.close()
        assert count == 1

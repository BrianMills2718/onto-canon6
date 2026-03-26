"""Integration test for the evaluate-rules CLI command."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

PYTHON = sys.executable
CLI_MODULE = "onto_canon6"
E2E_DB = Path("var/e2e_test_2026_03_25/review_combined.sqlite3")


@pytest.mark.skipif(not E2E_DB.exists(), reason="E2E test DB not available")
class TestEvaluateRulesCLI:
    """Test the evaluate-rules CLI command end-to-end."""

    def test_evaluate_simple_rules(self, tmp_path: Path) -> None:
        """Evaluate rules over real promoted assertions."""
        # Copy DB to temp
        test_db = tmp_path / "review.sqlite3"
        shutil.copy2(E2E_DB, test_db)

        # Write rules file
        rules_file = tmp_path / "rules.pl"
        rules_file.write_text(
            "authority_over(X, O) :- oc_hold_command_role(X, O).\n"
            "query(authority_over(X, Y)).\n"
        )

        result = subprocess.run(
            [
                PYTHON, "-m", CLI_MODULE,
                "evaluate-rules",
                "--review-db-path", str(test_db),
                "--rules-file", str(rules_file),
                "--output", "json",
            ],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).resolve().parent.parent.parent),
        )
        assert result.returncode == 0, f"CLI failed: {result.stderr}"

        output = json.loads(result.stdout)
        assert output["input_facts"] > 0
        assert output["rules_applied"] >= 1
        assert len(output["derived_facts"]) > 0
        assert output["errors"] == []

        # Verify we got authority_over facts
        terms = [f["term"] for f in output["derived_facts"]]
        assert any("authority_over" in t for t in terms)

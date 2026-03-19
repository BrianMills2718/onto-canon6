"""Integration tests for the CLI WhyGame relationship import surface."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import TypeAdapter

from onto_canon6 import cli as cli_module

_WHYGAME_FIXTURE_ADAPTER = TypeAdapter(list[dict[str, object]])


def _load_fixture() -> list[dict[str, object]]:
    """Load the shared WhyGame relationship fixture used for import-surface tests."""

    fixture_path = Path("tests/fixtures/whygame_relationship_facts.json")
    return _WHYGAME_FIXTURE_ADAPTER.validate_json(fixture_path.read_text(encoding="utf-8"))


def test_cli_import_whygame_relationships_review_promote_and_export(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The CLI should drive a WhyGame relationship file through import, review, promotion, and export."""

    review_db_path = tmp_path / "review.sqlite3"
    overlay_root = tmp_path / "overlays"
    input_path = tmp_path / "whygame_relationships.json"
    input_path.write_text(json.dumps(_load_fixture()[:1], indent=2), encoding="utf-8")

    exit_code = cli_module.main(
        [
            "import-whygame-relationships",
            "--input",
            str(input_path),
            "--submitted-by",
            "analyst:cli-whygame",
            "--artifact-uri",
            "artifact://whygame/cli",
            "--review-db-path",
            str(review_db_path),
            "--overlay-root",
            str(overlay_root),
            "--output",
            "json",
        ]
    )
    assert exit_code == 0
    import_output = json.loads(capsys.readouterr().out)
    candidate_id = str(import_output["submissions"][0]["candidate"]["candidate_id"])
    assert import_output["artifact"]["artifact_kind"] == "analysis_result"

    exit_code = cli_module.main(
        [
            "review-candidate",
            "--candidate-id",
            candidate_id,
            "--decision",
            "accepted",
            "--actor-id",
            "analyst:reviewer",
            "--review-db-path",
            str(review_db_path),
            "--output",
            "json",
        ]
    )
    assert exit_code == 0
    reviewed_candidate = json.loads(capsys.readouterr().out)
    assert reviewed_candidate["review_status"] == "accepted"

    exit_code = cli_module.main(
        [
            "promote-candidate",
            "--candidate-id",
            candidate_id,
            "--actor-id",
            "analyst:reviewer",
            "--review-db-path",
            str(review_db_path),
            "--output",
            "json",
        ]
    )
    assert exit_code == 0
    promoted_output = json.loads(capsys.readouterr().out)
    assert promoted_output["assertion"]["source_candidate_id"] == candidate_id

    exit_code = cli_module.main(
        [
            "export-governed-bundle",
            "--review-db-path",
            str(review_db_path),
            "--output",
            "json",
        ]
    )
    assert exit_code == 0
    bundle_output = json.loads(capsys.readouterr().out)
    assert bundle_output["summary"]["total_candidates"] == 1
    assert bundle_output["candidate_bundles"][0]["candidate"]["candidate_id"] == candidate_id
    assert bundle_output["candidate_bundles"][0]["artifacts"][0]["uri"] == "artifact://whygame/cli"

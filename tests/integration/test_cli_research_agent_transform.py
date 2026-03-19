"""Integration tests for the CLI research-agent transformation surface."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from onto_canon6 import cli as cli_module


def test_cli_converts_research_agent_entities_to_whygame(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The CLI should transform a producer entities file into a WhyGame facts file."""

    input_path = tmp_path / "entities.json"
    output_path = tmp_path / "whygame_relationships.json"
    input_path.write_text(
        json.dumps(
            [
                {
                    "name": "Shield AI",
                    "type": "organization",
                    "relationships": [
                        {
                            "entity": "Booz Allen Hamilton",
                            "type": "strategic_partner",
                            "detail": "Largest venture investment.",
                        }
                    ],
                }
            ],
            indent=2,
        ),
        encoding="utf-8",
    )

    exit_code = cli_module.main(
        [
            "convert-research-agent-entities-to-whygame",
            "--input",
            str(input_path),
            "--output-file",
            str(output_path),
            "--investigation-id",
            "shield_ai_full",
            "--output",
            "json",
        ]
    )

    assert exit_code == 0
    command_output = json.loads(capsys.readouterr().out)
    assert command_output["fact_count"] == 1
    assert output_path.exists()
    loaded = json.loads(output_path.read_text(encoding="utf-8"))
    assert loaded[0]["roles"]["from"] == "Shield AI"
    assert loaded[0]["roles"]["relationship"] == "strategic_partner"

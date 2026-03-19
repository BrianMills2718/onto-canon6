"""Integration tests for the CLI text-chunking helper."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from onto_canon6 import cli as cli_module


def test_cli_split_text_writes_chunks_and_manifest_json(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The CLI should split one long text file into chunk files deterministically."""

    input_path = tmp_path / "report.md"
    input_path.write_text(
        "# Introduction\n"
        + ("Alpha " * 120)
        + "\n\n## Analysis\n"
        + ("Bravo " * 140)
        + "\n\n## Conclusion\n"
        + ("Charlie " * 100),
        encoding="utf-8",
    )
    output_dir = tmp_path / "chunks"

    exit_code = cli_module.main(
        [
            "split-text",
            "--input",
            str(input_path),
            "--output-dir",
            str(output_dir),
            "--target-max-chars",
            "900",
            "--min-chunk-chars",
            "250",
            "--max-chunk-chars",
            "1000",
            "--output",
            "json",
        ]
    )

    assert exit_code == 0
    manifest = json.loads(capsys.readouterr().out)
    assert manifest["total_chunks"] >= 2
    manifest_path = output_dir / "manifest.json"
    assert manifest_path.exists()
    for chunk in manifest["chunks"]:
        assert Path(chunk["output_path"]).exists()

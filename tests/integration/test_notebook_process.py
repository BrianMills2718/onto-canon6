"""Integration tests for the local executable-journey notebook process."""

from __future__ import annotations

from pathlib import Path

import nbformat
from nbclient import NotebookClient

from onto_canon6.notebook_process import validate_notebook_registry


def test_notebook_registry_validates() -> None:
    """The local notebook registry should validate with concrete linked assets."""

    report = validate_notebook_registry()

    assert report.registry_path == "notebooks/notebook_registry.yaml"
    assert report.journey_count == 1
    assert report.auxiliary_notebook_count == 20
    assert report.phase_count == 14
    assert (
        "notebooks/00_master_governed_text_to_reviewed_assertions.ipynb"
        in report.validated_notebooks
    )


def test_master_journey_notebook_executes() -> None:
    """The canonical journey notebook should run top to bottom without hidden state."""

    notebook_path = Path("notebooks/00_master_governed_text_to_reviewed_assertions.ipynb")
    notebook = nbformat.read(notebook_path, as_version=4)  # type: ignore[no-untyped-call]

    client = NotebookClient(notebook, timeout=300, kernel_name="python3")
    client.execute()

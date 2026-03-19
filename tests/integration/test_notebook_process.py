"""Integration tests for the local executable-journey notebook process."""

from __future__ import annotations

from pathlib import Path
import re
from typing import cast

import nbformat
from nbclient import NotebookClient
from nbformat import NotebookNode

from onto_canon6.notebook_process import validate_notebook_registry


def test_notebook_registry_validates() -> None:
    """The local notebook registry should validate with concrete linked assets."""

    report = validate_notebook_registry()

    assert report.registry_path == "notebooks/notebook_registry.yaml"
    assert report.journey_count == 1
    assert report.auxiliary_notebook_count == 21
    assert report.phase_count == 15
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


def test_importing_notebooks_bootstrap_repo_paths() -> None:
    """Notebooks that import local packages should bootstrap repo-relative paths first.

    The notebook process is supposed to keep the canonical journey runnable from
    a normal Jupyter kernel, not only from an environment where `onto_canon6`
    was already installed editable. This test enforces a small, explicit rule:

    - if a notebook imports `onto_canon6` or `llm_client` anywhere,
    - its first code cell must contain the repo-path bootstrap snippet.
    """

    notebooks_dir = Path("notebooks")
    for notebook_path in sorted(notebooks_dir.glob("*.ipynb")):
        notebook = cast(
            NotebookNode,
            nbformat.read(notebook_path, as_version=4),  # type: ignore[no-untyped-call]
        )
        code_cells = [cell for cell in notebook.cells if cell.cell_type == "code"]
        if not code_cells:
            continue

        notebook_source = "\n".join(str(cell.source) for cell in code_cells)
        if re.search(
            r"(?m)^\\s*(?:from|import)\\s+(?:onto_canon6|llm_client)\\b",
            notebook_source,
        ) is None:
            continue

        first_code_source = str(code_cells[0].source)
        assert 'PROJECT_ROOT = Path.cwd().resolve()' in first_code_source, notebook_path
        assert 'PROJECT_ROOT / "src"' in first_code_source, notebook_path
        assert 'PROJECT_ROOT.parent / "llm_client"' in first_code_source, notebook_path
        assert 'sys.path.insert(0, candidate_str)' in first_code_source, notebook_path

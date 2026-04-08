"""Assemble the nanoGPT corpus and run the onto-canon6 extraction pipeline.

Fetches nanoGPT README and docstrings/comments from model.py, train.py, and
sample.py at a pinned commit, then runs the full pipeline:

  extract-text → accept-all → promote-all → export-digimon

All state is isolated to ``var/nanogpt_pipeline_run/`` — the default review DB
is not touched.

Usage::

    python scripts/run_nanogpt_extraction.py [--skip-fetch] [--skip-extract]

Options:
    --skip-fetch    Skip fetching files from GitHub (use existing var/nanogpt_corpus/)
    --skip-extract  Skip extraction (run accept/promote/export only)
"""

from __future__ import annotations

import argparse
import ast
import re
import subprocess
import sys
import textwrap
from pathlib import Path

try:
    import httpx
except ImportError:
    httpx = None  # type: ignore[assignment]

_REPO_ROOT = Path(__file__).parent.parent
_CORPUS_DIR = _REPO_ROOT / "var" / "nanogpt_corpus"
_RUN_DIR = _REPO_ROOT / "var" / "nanogpt_pipeline_run"
_REVIEW_DB = _RUN_DIR / "pipeline_review.sqlite3"

# Use master branch (commit pinning via SHA was not stable across GitHub CDN)
_NANOGPT_COMMIT = "master"
_NANOGPT_RAW = f"https://raw.githubusercontent.com/karpathy/nanoGPT/{_NANOGPT_COMMIT}"

_SOURCES = {
    "README.md": f"{_NANOGPT_RAW}/README.md",
    "model.py": f"{_NANOGPT_RAW}/model.py",
    "train.py": f"{_NANOGPT_RAW}/train.py",
    "sample.py": f"{_NANOGPT_RAW}/sample.py",
}

_PROFILE_ID = "code_core_permissive"
_PROFILE_VERSION = "0.1.0"
_SUBMITTED_BY = "run_nanogpt_extraction"
_GOAL = (
    "Extract all factual assertions about model components, training procedures, "
    "benchmarks, and code relationships directly supported by the source text. "
    "Focus on: what the GPT model implements and inherits, what benchmarks it achieves "
    "on which datasets, how training is configured, and how components relate to each other."
)


def fetch_corpus() -> None:
    """Fetch nanoGPT source files from GitHub and extract text for extraction."""
    if httpx is None:
        print("ERROR: httpx not installed. Run: pip install httpx", file=sys.stderr)
        sys.exit(1)

    _CORPUS_DIR.mkdir(parents=True, exist_ok=True)
    for existing in _CORPUS_DIR.iterdir():
        if existing.is_file():
            existing.unlink()

    for filename, url in _SOURCES.items():
        print(f"Fetching {filename} ...")
        resp = httpx.get(url, follow_redirects=True, timeout=30)
        resp.raise_for_status()
        raw = resp.text

        if filename == "README.md":
            _write_readme_corpus(raw)
            print(f"  → {_CORPUS_DIR} ({len(list(_CORPUS_DIR.glob('README*.md')))} README chunks)")
            continue
        if filename.endswith(".py"):
            text = _extract_docstrings_and_comments(raw, filename)
        else:
            text = raw

        out_path = _CORPUS_DIR / filename
        out_path.write_text(text, encoding="utf-8")
        print(f"  → {out_path} ({len(text):,} chars)")


def _write_readme_corpus(source: str) -> None:
    """Split the README into focused chunks so extraction sees narrower evidence."""
    sections = _split_markdown_sections(source)
    for index, (heading, body) in enumerate(sections, start=1):
        if len(body.strip()) < 120:
            continue
        slug = _slugify(heading)
        lines = [
            f"# Source: nanoGPT/README.md#{slug}",
            "",
            f"## {heading}",
            "",
            body.strip(),
        ]
        table_facts = _linearize_markdown_tables(body)
        if table_facts:
            lines.extend([
                "",
                "## Structured table facts",
                "",
                *table_facts,
            ])
        out_path = _CORPUS_DIR / f"README_{index:02d}_{slug}.md"
        out_path.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")


def _split_markdown_sections(source: str) -> list[tuple[str, str]]:
    """Return top-level README sections as standalone extraction units."""
    sections: list[tuple[str, str]] = []
    intro_lines: list[str] = []
    current_heading = "overview"
    current_lines: list[str] = []
    seen_heading = False

    for line in source.splitlines():
        if line.startswith("## "):
            if seen_heading:
                sections.append((current_heading, "\n".join(current_lines).strip()))
            else:
                intro_text = "\n".join(intro_lines).strip()
                if intro_text:
                    sections.append((current_heading, intro_text))
                seen_heading = True
            current_heading = line[3:].strip()
            current_lines = []
            continue

        if seen_heading:
            current_lines.append(line)
        else:
            intro_lines.append(line)

    if seen_heading:
        sections.append((current_heading, "\n".join(current_lines).strip()))
    else:
        intro_text = "\n".join(intro_lines).strip()
        if intro_text:
            sections.append((current_heading, intro_text))
    return sections


def _slugify(text: str) -> str:
    """Create stable ASCII filenames from README headings."""
    slug = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")
    return slug or "section"


def _linearize_markdown_tables(section_text: str) -> list[str]:
    """Rewrite markdown tables as short declarative facts for extraction."""
    lines = section_text.splitlines()
    facts: list[str] = []
    index = 0

    while index < len(lines) - 1:
        header = lines[index].strip()
        divider = lines[index + 1].strip()
        if not (header.startswith("|") and divider.startswith("|")):
            index += 1
            continue
        if "-" not in divider:
            index += 1
            continue

        headers = [cell.strip() for cell in header.strip("|").split("|")]
        index += 2
        while index < len(lines):
            row = lines[index].strip()
            if not row.startswith("|"):
                break
            cells = [cell.strip() for cell in row.strip("|").split("|")]
            if len(cells) == len(headers):
                parts = [
                    f"{name}={value}"
                    for name, value in zip(headers, cells)
                    if value and value != "-"
                ]
                if parts:
                    facts.append(f"- Table row: {', '.join(parts)}.")
            index += 1
    return facts


def _extract_docstrings_and_comments(source: str, filename: str) -> str:
    """Extract docstrings and comments from Python source for text extraction.

    Raw Python implementation lines have no semantic value for assertion extraction.
    We want the prose: module docstring, class docstrings, function docstrings,
    and inline # comments that explain design decisions.
    """
    lines = []
    lines.append(f"# Source: nanoGPT/{filename} (commit {_NANOGPT_COMMIT})\n")

    # Parse the AST to extract docstrings
    try:
        tree = ast.parse(source)
    except SyntaxError:
        # Fallback: return raw source with implementation lines stripped
        return "\n".join(
            line for line in source.splitlines()
            if line.strip().startswith("#") or '"""' in line or "'''" in line
        )

    declarations = _extract_python_declarations(tree)
    if declarations:
        lines.append("\n## Declarations\n")
        lines.extend(declarations)
        lines.append("")

    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            docstring = ast.get_docstring(node)
            if docstring and len(docstring.strip()) > 20:
                name = getattr(node, "name", "module")
                lines.append(f"\n## {name}\n")
                lines.append(textwrap.dedent(docstring).strip())
                lines.append("")

    # Also include # comment blocks (3+ consecutive comment lines = design note)
    comment_block: list[str] = []
    for line in source.splitlines():
        stripped = line.strip()
        if stripped.startswith("#") and len(stripped) > 5:
            comment_block.append(stripped[1:].strip())
        else:
            if len(comment_block) >= 2:
                lines.append("\n## Comment block\n")
                lines.append("\n".join(comment_block))
            comment_block = []

    result = "\n".join(lines)
    return result if result.strip() else f"# {filename}: no significant docstrings found\n"


def _extract_python_declarations(tree: ast.AST) -> list[str]:
    """Extract high-signal signatures that carry inheritance and API semantics."""
    declarations: list[str] = []

    for node in getattr(tree, "body", []):
        if isinstance(node, ast.ClassDef):
            bases = [ast.unparse(base) for base in node.bases] or ["object"]
            declarations.append(f"class {node.name}({', '.join(bases)})")
            for child in node.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    declarations.append(f"  def {child.name}{_format_signature(child)}")
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            declarations.append(f"def {node.name}{_format_signature(node)}")

    return declarations


def _format_signature(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    """Return a compact function signature using AST unparsing."""
    return f"({ast.unparse(node.args)})"


def run_extraction() -> None:
    """Run extract-text for each corpus file."""
    _RUN_DIR.mkdir(parents=True, exist_ok=True)

    corpus_files = sorted(_CORPUS_DIR.iterdir())
    if not corpus_files:
        print("ERROR: No corpus files found. Run with --skip-extract=False.", file=sys.stderr)
        sys.exit(1)

    for path in corpus_files:
        if not path.is_file():
            continue
        print(f"\nExtracting: {path.name} ...")
        _run(
            "onto-canon6", "extract-text",
            "--input", str(path),
            "--profile-id", _PROFILE_ID,
            "--profile-version", _PROFILE_VERSION,
            "--review-db-path", str(_REVIEW_DB),
            "--submitted-by", _SUBMITTED_BY,
            "--source-ref", f"nanogpt/{path.name}",
            "--source-label", f"nanoGPT {path.name}",
            "--goal", _GOAL,
        )


def accept_and_promote() -> None:
    """Accept all pending candidates and promote to the graph."""
    print("\nAccepting all candidates ...")
    _run("onto-canon6", "accept-all",
         "--review-db-path", str(_REVIEW_DB),
         "--actor-id", "run_nanogpt_extraction")

    print("Promoting all accepted candidates ...")
    _run("onto-canon6", "promote-all",
         "--review-db-path", str(_REVIEW_DB),
         "--actor-id", "run_nanogpt_extraction")


def export_digimon() -> None:
    """Export entities.jsonl and relationships.jsonl for the investigation browser."""
    print(f"\nExporting DIGIMON graph to {_RUN_DIR} ...")
    _run("onto-canon6", "export-digimon",
         "--review-db-path", str(_REVIEW_DB),
         "--output-dir", str(_RUN_DIR))

    # Generate role_labels.json for semantic edge labels
    print("Generating role_labels.json ...")
    _run("python", "scripts/generate_role_labels_json.py",
         "--output", str(_RUN_DIR / "role_labels.json"))

    # Summary
    entities = _RUN_DIR / "entities.jsonl"
    relationships = _RUN_DIR / "relationships.jsonl"
    e_count = len(entities.read_text().splitlines()) if entities.exists() else 0
    r_count = len(relationships.read_text().splitlines()) if relationships.exists() else 0
    print(f"\nExport complete:")
    print(f"  entities:      {e_count}")
    print(f"  relationships: {r_count}")
    print(f"  run dir:       {_RUN_DIR}")


def _run(*args: str) -> None:
    """Run a subprocess command, raising on failure."""
    result = subprocess.run(list(args), cwd=str(_REPO_ROOT), capture_output=False)
    if result.returncode != 0:
        print(f"ERROR: command failed: {' '.join(args)}", file=sys.stderr)
        sys.exit(result.returncode)


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Assemble nanoGPT corpus and run onto-canon6 extraction pipeline.",
    )
    parser.add_argument("--skip-fetch", action="store_true",
                        help="Skip fetching files from GitHub")
    parser.add_argument("--skip-extract", action="store_true",
                        help="Skip extraction (run accept/promote/export only)")
    args = parser.parse_args()

    if not args.skip_fetch:
        print("=== Fetching nanoGPT corpus ===")
        fetch_corpus()

    if not args.skip_extract:
        print("\n=== Running extraction ===")
        run_extraction()

    print("\n=== Accept, promote, export ===")
    accept_and_promote()
    export_digimon()

    print("\nDone. To view the graph:")
    print(f"  cd ~/projects/Digimon_for_KG_application")
    print(f"  ENTITIES={_RUN_DIR}/entities.jsonl \\")
    print(f"  RELATIONSHIPS={_RUN_DIR}/relationships.jsonl \\")
    print(f"  PROVENANCE_DB={_REVIEW_DB} \\")
    print(f"  make investigation-browser")


if __name__ == "__main__":
    main()

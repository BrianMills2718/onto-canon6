#!/usr/bin/env python3
"""Verify onto-canon6's supported local setup.

Checks the Python-side prerequisites and successor-local assets required for
the current proved workflow. Fails loudly when required pieces are missing and
reports optional pieces separately.
"""

from __future__ import annotations

from dataclasses import dataclass
import importlib.util
from pathlib import Path
import sys

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "src"))

from onto_canon6.config import get_config  # noqa: E402


@dataclass(frozen=True)
class SetupCheck:
    """One setup verification result."""

    label: str
    ok: bool
    required: bool
    detail: str
    remediation: str | None = None


def _module_check(module_name: str, *, required: bool, remediation: str) -> SetupCheck:
    """Return one import-availability check."""

    spec = importlib.util.find_spec(module_name)
    ok = spec is not None
    return SetupCheck(
        label=f"python module: {module_name}",
        ok=ok,
        required=required,
        detail="available" if ok else "missing",
        remediation=remediation if not ok else None,
    )


def _path_check(path: Path, *, label: str, required: bool, remediation: str) -> SetupCheck:
    """Return one path-existence check."""

    ok = path.exists()
    return SetupCheck(
        label=label,
        ok=ok,
        required=required,
        detail=str(path),
        remediation=remediation if not ok else None,
    )


def _print_check(check: SetupCheck) -> None:
    """Print one check result in a compact human-readable form."""

    if check.ok:
        status = "OK"
    elif check.required:
        status = "MISSING"
    else:
        status = "OPTIONAL"

    print(f"[{status}] {check.label}: {check.detail}")
    if check.remediation is not None:
        print(f"  fix: {check.remediation}")


def main() -> int:
    """Run setup verification and return a process exit code."""

    config = get_config()

    local_profiles = config.local_profiles_dir()
    local_packs = config.local_ontology_packs_dir()
    sumo_db = config.resolve_repo_path(config.evaluation.sumo_db_path)
    proof_db = _REPO_ROOT / "var" / "e2e_test_2026_03_25" / "review_combined.sqlite3"
    research_v3_output = _REPO_ROOT.parent / "research_v3" / "output"

    checks = [
        _module_check(
            "llm_client",
            required=True,
            remediation=f"{sys.executable} -m pip install -e ../llm_client",
        ),
        _module_check(
            "fastmcp",
            required=True,
            remediation=f"{sys.executable} -m pip install -e '.[dev]'",
        ),
        _module_check(
            "pytest",
            required=True,
            remediation=f"{sys.executable} -m pip install -e '.[dev]'",
        ),
        _module_check(
            "mypy",
            required=True,
            remediation=f"{sys.executable} -m pip install -e '.[dev]'",
        ),
        _module_check(
            "ruff",
            required=True,
            remediation=f"{sys.executable} -m pip install -e '.[dev]'",
        ),
        _path_check(
            local_profiles / "default" / "1.0.0" / "manifest.yaml",
            label="local default profile",
            required=True,
            remediation="restore profiles/default/1.0.0/manifest.yaml",
        ),
        _path_check(
            local_profiles / "dodaf" / "0.1.0" / "manifest.yaml",
            label="local dodaf profile",
            required=True,
            remediation="restore profiles/dodaf/0.1.0/manifest.yaml",
        ),
        _path_check(
            local_profiles / "psyop_seed" / "0.1.0" / "manifest.yaml",
            label="local psyop_seed profile",
            required=True,
            remediation="restore profiles/psyop_seed/0.1.0/manifest.yaml",
        ),
        _path_check(
            local_packs / "onto_canon_psyop_seed" / "0.1.0" / "manifest.yaml",
            label="local onto_canon_psyop_seed pack",
            required=True,
            remediation="restore ontology_packs/onto_canon_psyop_seed/0.1.0/manifest.yaml",
        ),
        _path_check(
            sumo_db,
            label="SUMO database",
            required=True,
            remediation="restore data/sumo_plus.db",
        ),
        _path_check(
            proof_db,
            label="canonical proof DB",
            required=True,
            remediation="restore or regenerate var/e2e_test_2026_03_25/review_combined.sqlite3",
        ),
        _path_check(
            research_v3_output,
            label="research_v3 output root",
            required=False,
            remediation="optional: clone ../research_v3 to enable the full smoke path",
        ),
    ]

    print("onto-canon6 setup verification")
    print("=" * 32)
    print(f"repo:        {_REPO_ROOT}")
    print(f"python:      {sys.executable}")
    print()

    failures = 0
    for check in checks:
        _print_check(check)
        if check.required and not check.ok:
            failures += 1

    print()
    if failures:
        print(f"FAILED: {failures} required setup item(s) missing")
        return 1

    print("Setup looks good.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

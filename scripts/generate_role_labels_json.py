"""Generate role_labels.json for the DIGIMON investigation browser.

Reads sumo_plus.db and emits a JSON file in the format expected by
``investigation_browser/backend/graph.py:_semantic_role()``:

    {predicate_id: {ARG0: named_label, ARG1: named_label, ...}}

The investigation browser loads this file at startup and uses it to resolve
ARG positions to semantic role names in graph edges. If the file is absent or
a predicate/arg pair is missing, the browser falls back to the bare ARG
position (e.g., "ARG0").

Usage::

    python scripts/generate_role_labels_json.py [--db PATH] [--output PATH]

Examples::

    # Write to the v11 pipeline run (default DIGIMON data dir)
    python scripts/generate_role_labels_json.py

    # Write to a specific directory
    python scripts/generate_role_labels_json.py \\
        --output /path/to/digimon/data/role_labels.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_REPO_ROOT / "src"))

from onto_canon6.packs.role_slots_lookup import RoleSlotsError, RoleSlotsLookup

_DEFAULT_DB = _REPO_ROOT / "data" / "sumo_plus.db"
_DEFAULT_OUTPUT = _REPO_ROOT / "var" / "iran_pipeline_run_v11" / "role_labels.json"


def generate_role_labels(
    db_path: Path,
    output_path: Path,
) -> dict[str, dict[str, str]]:
    """Generate role_labels.json from sumo_plus.db.

    Parameters
    ----------
    db_path:
        Path to sumo_plus.db.
    output_path:
        Path to write role_labels.json.

    Returns
    -------
    dict
        The mapping written to disk: ``{predicate_id: {arg_position: named_label}}``.
    """
    with RoleSlotsLookup(db_path) as lookup:
        mapping = lookup.all_role_labels()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(mapping, f, ensure_ascii=False, indent=None)

    return mapping


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Generate role_labels.json for the DIGIMON investigation browser.",
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=_DEFAULT_DB,
        help=f"Path to sumo_plus.db (default: {_DEFAULT_DB})",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=_DEFAULT_OUTPUT,
        help=f"Output path for role_labels.json (default: {_DEFAULT_OUTPUT})",
    )
    args = parser.parse_args()

    try:
        mapping = generate_role_labels(args.db, args.output)
    except RoleSlotsError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    predicate_count = len(mapping)
    role_slot_count = sum(len(v) for v in mapping.values())
    print(f"Written to: {args.output}")
    print(f"  predicates:  {predicate_count:,}")
    print(f"  role slots:  {role_slot_count:,}")


if __name__ == "__main__":
    main()

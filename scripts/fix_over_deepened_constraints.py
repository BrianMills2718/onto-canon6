"""Fix over-deepened ARG0 constraints: Human -> CognitiveAgent.

The LLM-driven constraint deepening pass pushed ~240 agent role_slots
from CognitiveAgent to Human, preventing Organizations from being valid
agents. CognitiveAgent is the correct level because it includes Human,
Organization, and Deity -- all of which can be grammatical agents in
OSINT text.

This script updates the canonical repo-local ``sumo_plus.db`` owned by
onto-canon6.

Usage:
    python scripts/fix_over_deepened_constraints.py [--dry-run]
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATHS = [PROJECT_ROOT / "data" / "sumo_plus.db"]

# Verbs that truly require a biological human body -- these keep 'Human'.
# If the process is inherently physiological (not metaphorical in any
# common usage), it stays as Human.
KEEP_HUMAN: frozenset[str] = frozenset({
    # Biological reproduction / pregnancy
    "bear_children",
    "conceive_make_babies",
    # Physiological involuntary processes
    "cough_hack",
    "hack_cough",  # alias sense
    "sweat_perspire",
    "snivel_drippy_nose",
    "faint_pass_out",
    "black_fall_asleep",
    "pass_faint_lose_consciousness",
    "bleed_feel_grief",
    "ache_suffer_dull_pain",
    "chafe_feel_irritated",
    # Personal hygiene requiring a body
    "bathe_have_bath",
})


def fix_constraints(db_path: Path, *, dry_run: bool = False) -> int:
    """Update Human -> CognitiveAgent for agent role_slots.

    Returns the number of rows updated.
    """
    if not db_path.exists():
        print(f"  SKIP (not found): {db_path}")
        return 0

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    # Count before.
    cursor = conn.execute(
        "SELECT COUNT(*) FROM role_slots "
        "WHERE type_constraint = 'Human' AND abstract_role = 'agent'"
    )
    before = cursor.fetchone()[0]

    if before == 0:
        print(f"  {db_path.name}: no Human+agent constraints found (already fixed?)")
        conn.close()
        return 0

    # Get the IDs that should be excluded.
    placeholders = ",".join("?" for _ in KEEP_HUMAN)
    cursor = conn.execute(
        f"SELECT COUNT(*) FROM role_slots "
        f"WHERE type_constraint = 'Human' AND abstract_role = 'agent' "
        f"AND event_sense_id IN ({placeholders})",
        tuple(KEEP_HUMAN),
    )
    keep_count = cursor.fetchone()[0]

    will_update = before - keep_count

    if dry_run:
        print(f"  {db_path.name}: would update {will_update}/{before} rows "
              f"(keeping {keep_count} biological-only)")
        conn.close()
        return will_update

    # Perform the update: all Human+agent except biological-only.
    cursor = conn.execute(
        f"UPDATE role_slots SET type_constraint = 'CognitiveAgent' "
        f"WHERE type_constraint = 'Human' AND abstract_role = 'agent' "
        f"AND event_sense_id NOT IN ({placeholders})",
        tuple(KEEP_HUMAN),
    )
    updated = cursor.rowcount
    conn.commit()

    # Verify.
    cursor = conn.execute(
        "SELECT COUNT(*) FROM role_slots "
        "WHERE type_constraint = 'Human' AND abstract_role = 'agent'"
    )
    after = cursor.fetchone()[0]

    print(f"  {db_path.name}: updated {updated} rows "
          f"({before} -> {after} Human+agent remaining)")
    conn.close()
    return updated


def main() -> None:
    """Run the constraint fix on the canonical local database."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Show what would change without modifying the database.",
    )
    args = parser.parse_args()

    total = 0
    for db_path in DB_PATHS:
        print(f"Processing: {db_path}")
        total += fix_constraints(db_path, dry_run=args.dry_run)

    action = "Would update" if args.dry_run else "Updated"
    print(f"\n{action} {total} total rows across all databases.")


if __name__ == "__main__":
    main()

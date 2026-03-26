#!/usr/bin/env python3
"""Print extraction and identity summary stats for a review DB."""

from __future__ import annotations

import argparse
import sqlite3
import sys


def main() -> int:
    """Print summary stats."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--db-path", default="var/review_state.sqlite3")
    args = parser.parse_args()

    conn = sqlite3.connect(args.db_path)

    total = conn.execute("SELECT COUNT(*) FROM candidate_assertions").fetchone()[0]
    accepted = conn.execute(
        "SELECT COUNT(*) FROM candidate_assertions WHERE review_status='accepted'"
    ).fetchone()[0]
    rejected = conn.execute(
        "SELECT COUNT(*) FROM candidate_assertions WHERE review_status='rejected'"
    ).fetchone()[0]
    pending = conn.execute(
        "SELECT COUNT(*) FROM candidate_assertions WHERE review_status='pending_review'"
    ).fetchone()[0]

    has_promoted = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='promoted_graph_assertions'"
    ).fetchone()
    promoted = (
        conn.execute("SELECT COUNT(*) FROM promoted_graph_assertions").fetchone()[0]
        if has_promoted else 0
    )

    rate = f"{100 * accepted / total:.0f}%" if total else "n/a"
    print(f"Candidates: {total} (accepted={accepted}, rejected={rejected}, pending={pending})")
    print(f"Promoted:   {promoted}")
    print(f"Acceptance: {rate}")

    # Identity stats
    has_identity = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='graph_identities'"
    ).fetchone()
    if has_identity:
        ident_total = conn.execute("SELECT COUNT(*) FROM graph_identities").fetchone()[0]
        ident_multi = conn.execute(
            "SELECT COUNT(*) FROM "
            "(SELECT identity_id, COUNT(*) as cnt FROM graph_identity_memberships "
            "GROUP BY identity_id HAVING cnt > 1)"
        ).fetchone()[0]
        auto_resolved = conn.execute(
            "SELECT COUNT(*) FROM graph_identities WHERE created_by='auto:resolution'"
        ).fetchone()[0]
        print(
            f"Identities: {ident_total} "
            f"(multi-member={ident_multi}, auto-resolved={auto_resolved})"
        )

    # Epistemic stats
    has_epistemic = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='epistemic_confidence_assessments'"
    ).fetchone()
    if has_epistemic:
        conf_count = conn.execute(
            "SELECT COUNT(*) FROM epistemic_confidence_assessments"
        ).fetchone()[0]
        avg_conf = conn.execute(
            "SELECT AVG(confidence_score) FROM epistemic_confidence_assessments"
        ).fetchone()[0]
        print(
            f"Epistemic:  {conf_count} confidence scores "
            f"(avg={avg_conf:.2f})" if avg_conf else f"Epistemic:  {conf_count} confidence scores"
        )

    conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Show recent llm_client call summaries for one project.

This script exists for Plan 0043. The current blocker is no longer generic
prompt quality; it is same-model live-path divergence. A small reproducible
observability view is more useful than ad hoc SQL when diagnosing whether a
project-level run diverged at extraction, judge-filter, or per-candidate
review.
"""

from __future__ import annotations

import argparse
import os
import sqlite3
from pathlib import Path


def main() -> None:
    """Load recent calls for one project and print a compact summary."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True, help="Exact llm_client project name.")
    parser.add_argument("--limit", type=int, default=20, help="Maximum rows to print.")
    parser.add_argument(
        "--task",
        help="Optional exact task filter (for example budget_extraction or judging).",
    )
    args = parser.parse_args()

    db_path = os.environ.get(
        "LLM_CLIENT_DB_PATH",
        str(Path.home() / "projects/data/llm_observability.db"),
    )
    db = sqlite3.connect(db_path)
    db.row_factory = sqlite3.Row
    try:
        query = """
            SELECT timestamp, task, model, error, response, trace_id, latency_s, cost
            FROM llm_calls
            WHERE project = ?
        """
        params: list[object] = [args.project]
        if args.task:
            query += " AND task = ?"
            params.append(args.task)
        query += " ORDER BY id DESC LIMIT ?"
        params.append(args.limit)
        rows = db.execute(query, tuple(params)).fetchall()
    finally:
        db.close()

    print(f"{len(rows)} call(s) for project={args.project!r}")
    print()
    for row in rows:
        print(_format_row(row))
        print()


def _format_row(row: sqlite3.Row) -> str:
    """Render one llm_calls row as compact multiline text."""

    response_excerpt = _response_excerpt(row["response"])
    trace = row["trace_id"] or ""
    return "\n".join(
        [
            f"timestamp: {row['timestamp']}",
            f"task: {row['task']}",
            f"model: {row['model']}",
            f"trace_id: {trace}",
            f"latency_s: {row['latency_s']}",
            f"cost: {row['cost']}",
            f"error: {row['error']}",
            f"response_excerpt: {response_excerpt}",
        ]
    )


def _response_excerpt(raw: object) -> str:
    """Return one short response summary without dumping the full payload."""

    if raw is None:
        return "null"
    text = str(raw)
    if len(text) <= 240:
        return text
    return text[:237] + "..."


if __name__ == "__main__":
    main()

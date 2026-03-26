"""Show recent extraction failures with raw response and validation errors."""

import argparse
import json
import os
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path


def _get(row: sqlite3.Row, key: str, default: object = None) -> object:
    """Safe get from sqlite3.Row which doesn't support .get()."""
    try:
        return row[key]
    except (IndexError, KeyError):
        return default


def main() -> None:
    parser = argparse.ArgumentParser(description="Show extraction failures")
    parser.add_argument("--days", type=int, default=1, help="Look back N days")
    parser.add_argument("--limit", type=int, default=10, help="Max results")
    parser.add_argument("--trace", help="Filter to specific trace_id")
    args = parser.parse_args()

    db_path = os.environ.get(
        "LLM_CLIENT_DB_PATH",
        str(Path.home() / "projects/data/llm_observability.db"),
    )
    db = sqlite3.connect(db_path)
    db.row_factory = sqlite3.Row

    if args.trace:
        rows = db.execute(
            "SELECT * FROM llm_calls WHERE trace_id = ? ORDER BY timestamp",
            (args.trace,),
        ).fetchall()
        print(f"{len(rows)} calls for trace {args.trace}")
        for r in rows:
            _print_call(r, verbose=True)
        return

    cutoff = (datetime.now(timezone.utc) - timedelta(days=args.days)).isoformat()
    rows = db.execute(
        """SELECT timestamp, model, error, response, validation_errors,
                  schema_hash, retry_count, response_format_type, trace_id
           FROM llm_calls
           WHERE error IS NOT NULL AND task = 'fast_extraction'
           AND timestamp >= ?
           ORDER BY timestamp DESC LIMIT ?""",
        (cutoff, args.limit),
    ).fetchall()

    print(f"{len(rows)} extraction failures in last {args.days} day(s)")
    print()
    for r in rows:
        _print_call(r, verbose=False)


def _print_call(r: sqlite3.Row, *, verbose: bool) -> None:
    ts = str(r["timestamp"])[:19]
    model = r["model"]
    retries = _get(r,"retry_count")
    schema = _get(r,"schema_hash")
    trace = _get(r,"trace_id", "")

    print(f"--- {ts} model={model} retries={retries} schema={schema} trace={trace[:20]} ---")

    error = _get(r,"error")
    if error:
        print(f"  error: {str(error)[:150]}")

    val_errors = _get(r,"validation_errors")
    if val_errors:
        try:
            errs = json.loads(val_errors)
            for e in errs[:5]:
                loc = " -> ".join(str(x) for x in e.get("loc", ()))
                msg = e.get("msg", "?")
                print(f"  validation: {loc}: {msg}")
        except (json.JSONDecodeError, TypeError):
            print(f"  validation_errors: {val_errors[:200]}")

    response = _get(r,"response")
    if response:
        resp = str(response)
        if '"roles"' in resp:
            idx = resp.find('"roles"')
            print(f"  roles: {resp[idx:idx+120]}...")
        else:
            print(f"  response: {resp[:120]}...")

    if verbose:
        cost = _get(r,"cost")
        tokens = _get(r,"total_tokens")
        latency = _get(r,"latency_s")
        fmt = _get(r,"response_format_type")
        path = _get(r,"execution_path")
        if cost is not None:
            print(f"  cost=${cost:.4f} tokens={tokens} latency={latency:.1f}s")
        print(f"  format={fmt} path={path}")

    print()


if __name__ == "__main__":
    main()

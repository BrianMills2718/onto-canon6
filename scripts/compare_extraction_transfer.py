"""Compare one live extraction artifact against one prompt-eval item.

This is a thin wrapper over `onto_canon6.evaluation.transfer_comparison`.
It exists for Plan 0040 so operators can reproduce the live-vs-parity diff
without manually querying SQLite and multiple JSON artifacts.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from onto_canon6.evaluation.transfer_comparison import compare_transfer_surfaces


def main() -> int:
    """Run the comparison and print JSON to stdout."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--observability-db", required=True, type=Path)
    parser.add_argument("--prompt-eval-run-id", required=True)
    parser.add_argument("--prompt-eval-item-id", required=True)
    parser.add_argument("--live-candidates-path", required=True, type=Path)
    args = parser.parse_args()

    comparison = compare_transfer_surfaces(
        observability_db_path=args.observability_db,
        prompt_eval_run_id=args.prompt_eval_run_id,
        prompt_eval_item_id=args.prompt_eval_item_id,
        live_candidates_path=args.live_candidates_path,
    )
    print(json.dumps(comparison.to_jsonable(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

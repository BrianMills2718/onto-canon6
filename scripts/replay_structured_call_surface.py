"""Replay one captured structured call through sync or async llm_client API."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from onto_canon6.evaluation.extraction_call_replay import replay_structured_call_surface


def main() -> int:
    """Replay the captured call and print the parsed payload as JSON."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--observability-db", required=True, type=Path)
    parser.add_argument("--call-id", required=True, type=int)
    parser.add_argument(
        "--public-api",
        required=True,
        choices=("call_llm_structured", "acall_llm_structured"),
    )
    parser.add_argument("--trace-id", required=True)
    parser.add_argument("--task", required=True)
    parser.add_argument("--max-budget", required=True, type=float)
    parser.add_argument("--project")
    args = parser.parse_args()

    result = replay_structured_call_surface(
        observability_db_path=args.observability_db,
        call_id=args.call_id,
        public_api=args.public_api,
        trace_id=args.trace_id,
        task=args.task,
        max_budget=args.max_budget,
        project=args.project,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

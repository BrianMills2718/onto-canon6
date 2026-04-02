"""Compare one live extraction call against one prompt-eval call surface.

This wrapper exists for Plan 0045 so operators can produce one reproducible
JSON artifact from observability instead of hand-writing Python sqlite queries
for each chunk-localization pass.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from onto_canon6.evaluation.extraction_path_comparison import compare_extraction_call_surfaces


def main() -> int:
    """Run the call-surface comparison and print JSON to stdout."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--observability-db", required=True, type=Path)
    parser.add_argument("--live-project", required=True)
    parser.add_argument("--live-task", default="budget_extraction")
    parser.add_argument("--prompt-eval-prompt-ref", required=True)
    parser.add_argument("--prompt-eval-trace-id", required=True)
    args = parser.parse_args()

    comparison = compare_extraction_call_surfaces(
        observability_db_path=args.observability_db,
        live_project=args.live_project,
        live_task=args.live_task,
        prompt_eval_prompt_ref=args.prompt_eval_prompt_ref,
        prompt_eval_trace_id=args.prompt_eval_trace_id,
    )
    print(json.dumps(comparison.to_jsonable(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

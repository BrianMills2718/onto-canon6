"""Render and compare live vs prompt-eval extraction prompt surfaces."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from onto_canon6.evaluation.prompt_surface_parity import (
    compare_prompt_surfaces,
    compare_prompt_surfaces_for_case,
)
from onto_canon6.evaluation.service import load_benchmark_fixture


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI for prompt-surface parity rendering."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, help="Source chunk/text file.")
    parser.add_argument("--profile-id")
    parser.add_argument("--profile-version")
    parser.add_argument("--source-kind", default="text_file")
    parser.add_argument("--source-ref")
    parser.add_argument("--source-label")
    parser.add_argument("--case-id", required=True)
    parser.add_argument(
        "--fixture",
        type=Path,
        help="Benchmark fixture JSON containing the named case.",
    )
    parser.add_argument("--output", choices=("json",), default="json")
    return parser


def main() -> int:
    """Render both prompt surfaces and print the comparison as JSON."""

    args = build_parser().parse_args()
    if args.fixture is not None:
        fixture = load_benchmark_fixture(args.fixture)
        cases = [case for case in fixture.cases if case.case_id == args.case_id]
        if len(cases) != 1:
            raise SystemExit(f"expected exactly one case {args.case_id!r} in {args.fixture}")
        comparison = compare_prompt_surfaces_for_case(case=cases[0])
    else:
        required = {
            "--input": args.input,
            "--profile-id": args.profile_id,
            "--profile-version": args.profile_version,
            "--source-ref": args.source_ref,
        }
        missing = [flag for flag, value in required.items() if value is None]
        if missing:
            raise SystemExit(
                "manual mode requires " + ", ".join(missing) + " when --fixture is not supplied"
            )
        comparison = compare_prompt_surfaces(
            source_text=args.input.read_text(encoding="utf-8"),
            profile_id=args.profile_id,
            profile_version=args.profile_version,
            source_kind=args.source_kind,
            source_ref=args.source_ref,
            source_label=args.source_label,
            case_id=args.case_id,
        )
    print(json.dumps(comparison.to_jsonable(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

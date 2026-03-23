"""Compare onto-canon6 progressive extraction against a bare SPO-triple prompt.

This script runs the same benchmark fixture through two pipelines:

1. **Baseline**: A bare llm_client call with a simple "extract SPO triples"
   prompt and a Pydantic structured output schema.  No ontology governance,
   no multi-pass, no predicate canon.

2. **Progressive**: onto-canon6's 3-pass progressive extraction pipeline
   (open extraction → predicate mapping → entity refinement).

The comparison measures what the onto-canon6 governance layer buys over the
simplest possible approach.  Both pipelines are scored against the same
benchmark fixture using the same deterministic scoring logic.

Usage:
    python scripts/baseline_extraction_comparison.py [--case-limit N] [--budget FLOAT]
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from pathlib import Path

from pydantic import BaseModel, Field

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))


class BaselineTriple(BaseModel):
    """One extracted subject-predicate-object triple."""

    subject: str = Field(description="The entity performing the action or being described")
    subject_type: str = Field(description="The type of the subject entity (e.g., Organization, Person, Location)")
    predicate: str = Field(description="The relationship or action (e.g., belongs_to, commands, located_in)")
    object: str = Field(description="The entity being acted upon or related to")
    object_type: str = Field(description="The type of the object entity")
    evidence: str = Field(description="The exact text span from the source that supports this triple")


class BaselineExtractionResponse(BaseModel):
    """Structured output from the baseline extraction prompt."""

    triples: list[BaselineTriple] = Field(
        default_factory=list,
        description="All factual subject-predicate-object triples extracted from the text",
    )


BASELINE_SYSTEM_PROMPT = """\
You are a precise information extraction system. Extract all factual \
subject-predicate-object triples from the provided text.

Rules:
- Extract only facts directly stated in the text, not inferences.
- Use exact surface forms from the text for entity names.
- Each triple must be grounded in a specific text span.
- Abbreviation/acronym expansions are NOT relationships.
- Omit vague or speculative statements.
"""


def _load_fixture(fixture_path: Path, case_limit: int | None) -> list[dict]:
    """Load benchmark cases from the fixture JSON."""

    with open(fixture_path) as fh:
        data = json.load(fh)
    cases = data.get("cases", [])
    if case_limit is not None:
        cases = cases[:case_limit]
    return [c for c in cases if c.get("source_artifact", {}).get("content_text")]


async def _run_baseline_extraction(
    text: str,
    *,
    max_budget: float,
    task: str,
) -> tuple[BaselineExtractionResponse, float, str]:
    """Run the bare SPO-triple extraction on one text."""

    from llm_client import acall_llm, get_model

    model = get_model(task, use_performance=True)
    import uuid

    trace_id = f"baseline_{uuid.uuid4().hex[:12]}"

    messages = [
        {"role": "system", "content": BASELINE_SYSTEM_PROMPT},
        {"role": "user", "content": f"Extract all factual triples from this text:\n\n{text}"},
    ]

    start = time.monotonic()
    result = await acall_llm(
        messages=messages,
        model=model,
        task=task,
        trace_id=trace_id,
        max_budget=max_budget,
        response_format=BaselineExtractionResponse,
    )
    elapsed = time.monotonic() - start

    # acall_llm returns LLMCallResult with raw content string.
    # Parse the JSON content into our response model.
    import json as _json

    content = getattr(result, "content", None) or ""
    if isinstance(content, str) and content.strip():
        try:
            parsed = BaselineExtractionResponse.model_validate_json(content.strip())
            return parsed, elapsed, model
        except Exception:
            # Try parsing as raw JSON and extracting triples.
            try:
                raw = _json.loads(content.strip())
                if isinstance(raw, dict) and "triples" in raw:
                    parsed = BaselineExtractionResponse.model_validate(raw)
                    return parsed, elapsed, model
            except Exception:
                pass

    return BaselineExtractionResponse(triples=[]), elapsed, model


def _score_baseline_against_fixture(
    triples: list[BaselineTriple],
    expected_candidates: list[dict],
) -> dict:
    """Score baseline triples loosely against expected candidates.

    Since the baseline uses free-form predicates rather than ontology-aligned
    ones, exact signature matching is unfair.  Instead we score:

    - triple_count: how many triples were extracted
    - expected_count: how many candidates were expected
    - entity_coverage: what fraction of expected entity names appear in triples
    - predicate_variety: unique predicates used
    """

    expected_entities: set[str] = set()
    for candidate in expected_candidates:
        payload = candidate.get("payload", {})
        for role_fillers in payload.get("roles", {}).values():
            for filler in role_fillers:
                name = filler.get("name", "")
                if name:
                    expected_entities.add(name.lower().strip())

    extracted_entities: set[str] = set()
    for triple in triples:
        extracted_entities.add(triple.subject.lower().strip())
        extracted_entities.add(triple.object.lower().strip())

    if expected_entities:
        entity_coverage = len(expected_entities & extracted_entities) / len(expected_entities)
    else:
        entity_coverage = 1.0 if not extracted_entities else 0.0

    unique_predicates = {t.predicate.lower().strip() for t in triples}

    return {
        "triple_count": len(triples),
        "expected_count": len(expected_candidates),
        "entity_coverage": round(entity_coverage, 4),
        "predicate_variety": len(unique_predicates),
        "unique_predicates": sorted(unique_predicates),
        "extracted_entities": sorted(extracted_entities),
        "expected_entities": sorted(expected_entities),
    }


async def _run_comparison(
    fixture_path: Path,
    case_limit: int | None,
    max_budget: float,
    task: str,
) -> dict:
    """Run both pipelines on the same fixture and compare."""

    cases = _load_fixture(fixture_path, case_limit)
    if not cases:
        return {"error": "No cases with content_text found in fixture"}

    print(f"Running comparison on {len(cases)} cases...")
    print(f"  Budget per call: ${max_budget:.2f}")
    print(f"  Task: {task}")
    print()

    baseline_results = []
    total_baseline_time = 0.0
    total_baseline_triples = 0

    for i, case in enumerate(cases):
        case_id = case.get("case_id", f"case_{i}")
        text = case["source_artifact"]["content_text"]
        expected = case.get("expected_candidates", [])

        print(f"[{i+1}/{len(cases)}] {case_id}...")

        try:
            response, elapsed, model = await _run_baseline_extraction(
                text, max_budget=max_budget, task=task,
            )
            scores = _score_baseline_against_fixture(response.triples, expected)
            baseline_results.append({
                "case_id": case_id,
                "model": model,
                "elapsed_s": round(elapsed, 2),
                "triples": [t.model_dump() for t in response.triples],
                "scores": scores,
            })
            total_baseline_time += elapsed
            total_baseline_triples += len(response.triples)
            print(f"  Baseline: {len(response.triples)} triples, "
                  f"entity coverage={scores['entity_coverage']:.0%}, "
                  f"{elapsed:.1f}s")
        except Exception as exc:
            print(f"  Baseline FAILED: {exc}")
            baseline_results.append({
                "case_id": case_id,
                "error": str(exc),
            })

    # Summary
    successful = [r for r in baseline_results if "error" not in r]
    avg_coverage = (
        sum(r["scores"]["entity_coverage"] for r in successful) / len(successful)
        if successful else 0.0
    )
    all_predicates: set[str] = set()
    for r in successful:
        all_predicates.update(r["scores"]["unique_predicates"])

    summary = {
        "fixture_path": str(fixture_path),
        "cases_run": len(cases),
        "cases_successful": len(successful),
        "total_baseline_triples": total_baseline_triples,
        "total_baseline_time_s": round(total_baseline_time, 2),
        "avg_entity_coverage": round(avg_coverage, 4),
        "total_unique_predicates": len(all_predicates),
        "all_predicates": sorted(all_predicates),
        "case_results": baseline_results,
    }

    return summary


def main() -> None:
    """Run the baseline comparison."""

    parser = argparse.ArgumentParser(description="Baseline extraction comparison")
    parser.add_argument(
        "--case-limit", type=int, default=None,
        help="Limit number of benchmark cases to run",
    )
    parser.add_argument(
        "--budget", type=float, default=0.10,
        help="Max budget per LLM call in USD (default: 0.10)",
    )
    parser.add_argument(
        "--task", type=str, default="fast_extraction",
        help="llm_client task name for model selection (default: fast_extraction)",
    )
    parser.add_argument(
        "--fixture", type=str,
        default=str(PROJECT_ROOT / "tests" / "fixtures" / "psyop_eval_slice.json"),
        help="Path to benchmark fixture JSON",
    )
    parser.add_argument(
        "--output", type=str, default=None,
        help="Path to write JSON results (default: stdout summary only)",
    )
    args = parser.parse_args()

    result = asyncio.run(_run_comparison(
        fixture_path=Path(args.fixture),
        case_limit=args.case_limit,
        max_budget=args.budget,
        task=args.task,
    ))

    print()
    print("=" * 60)
    print("BASELINE EXTRACTION SUMMARY")
    print("=" * 60)
    print(f"Cases run:          {result.get('cases_run', 0)}")
    print(f"Cases successful:   {result.get('cases_successful', 0)}")
    print(f"Total triples:      {result.get('total_baseline_triples', 0)}")
    print(f"Total time:         {result.get('total_baseline_time_s', 0):.1f}s")
    print(f"Avg entity coverage:{result.get('avg_entity_coverage', 0):.1%}")
    print(f"Unique predicates:  {result.get('total_unique_predicates', 0)}")
    print()
    print("Compare these results against onto-canon6 progressive extraction")
    print("on the same fixture to measure the value of ontology governance.")

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as fh:
            json.dump(result, fh, indent=2)
        print(f"\nFull results written to: {output_path}")


if __name__ == "__main__":
    main()

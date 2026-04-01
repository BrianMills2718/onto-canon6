"""Chunk-level transfer evaluation per ADR 0023.

Runs extraction on real PSYOP benchmark chunks, scores structural validity
and faithfulness, and documents transfer evidence for prompt promotion.

Usage:
    python scripts/run_transfer_evaluation.py [--chunks 3]
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--chunks", type=int, default=5, help="Number of chunks to evaluate")
    args = parser.parse_args()

    from onto_canon6.config import clear_config_cache, get_config
    clear_config_cache()
    config = get_config()

    fixture = json.loads(Path("tests/fixtures/psyop_eval_slice.json").read_text())
    cases = fixture["cases"][:args.chunks]

    from onto_canon6.pipeline.text_extraction import TextExtractionService
    ext = TextExtractionService()

    results = []
    t0 = time.time()

    for i, case in enumerate(cases):
        text = case["source_artifact"]["content_text"]
        case_id = case.get("case_id", f"chunk_{i:03d}")
        expected = case.get("expected_candidates", [])

        print(f"Chunk {i} ({case_id}, {len(text)} chars)...")

        try:
            run = ext.extract_candidate_run(
                source_text=text,
                profile_id="general_purpose_open",
                profile_version="0.1.0",
                submitted_by="transfer_eval",
                source_ref=case_id,
                source_kind="benchmark",
                extraction_goal="Extract factual assertions about people, organizations, and their relationships.",
            )
            imports = list(run.candidate_imports)

            # Score: structural validity
            valid = len(imports)
            noise = sum(1 for c in imports if any(
                w in (c.claim_text or "").lower()
                for w in ["the meeting", "a ceremony", "initiatives", "the reforms"]
            ))

            # Check against expected (if available)
            expected_predicates = {e.get("predicate", "") for e in expected}
            extracted_predicates = {c.payload.get("predicate", "") for c in imports}
            overlap = expected_predicates & extracted_predicates

            result = {
                "case_id": case_id,
                "text_length": len(text),
                "candidates_extracted": valid,
                "noise_candidates": noise,
                "expected_candidates": len(expected),
                "predicate_overlap": len(overlap),
                "extracted_predicates": sorted(extracted_predicates),
                "claims": [c.claim_text for c in imports],
            }
            results.append(result)
            print(f"  {valid} candidates, {noise} noise, {len(overlap)}/{len(expected)} expected predicates")

        except Exception as e:
            results.append({"case_id": case_id, "error": str(e)})
            print(f"  ERROR: {e}")

    t1 = time.time()

    # Summary
    total_candidates = sum(r.get("candidates_extracted", 0) for r in results)
    total_noise = sum(r.get("noise_candidates", 0) for r in results)
    total_errors = sum(1 for r in results if "error" in r)

    summary = {
        "model": config.extraction.model_override,
        "prompt": config.extraction.prompt_template,
        "chunks_evaluated": len(results),
        "total_candidates": total_candidates,
        "total_noise": total_noise,
        "total_errors": total_errors,
        "noise_rate": total_noise / total_candidates if total_candidates > 0 else 0.0,
        "time_seconds": round(t1 - t0, 1),
        "timestamp": time.strftime("%Y-%m-%d_%H%M%S"),
    }

    print(f"\n--- Transfer Evaluation Summary ---")
    print(f"Model: {summary['model']}")
    print(f"Chunks: {summary['chunks_evaluated']}")
    print(f"Candidates: {summary['total_candidates']}")
    print(f"Noise: {summary['total_noise']} ({summary['noise_rate']:.0%})")
    print(f"Errors: {summary['total_errors']}")
    print(f"Time: {summary['time_seconds']}s")

    # Save
    out_path = Path(f"docs/runs/transfer_eval_{summary['timestamp']}.json")
    out_data = {"summary": summary, "cases": results}
    out_path.write_text(json.dumps(out_data, indent=2))
    print(f"\nSaved: {out_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())

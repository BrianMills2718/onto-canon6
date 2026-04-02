"""E2E integration test: grounded-research → epistemic-contracts → onto-canon6.

Loads a real grounded-research handoff.json, converts through shared contracts,
imports into onto-canon6 review pipeline, and verifies assertions are stored.

Usage:
    python scripts/e2e_grounded_research_integration.py \
        --handoff ~/projects/grounded-research/output/eu_russia_sanctions/handoff.json
"""

from __future__ import annotations

import argparse
import json
import logging
import sqlite3
import sys
import tempfile
from pathlib import Path

# Add grounded-research to path for shared_export
sys.path.insert(0, str(Path.home() / "projects" / "grounded-research" / "src"))

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def run_integration(handoff_path: Path) -> dict:
    """Run the full integration chain and return results."""

    # Step 1: Load handoff.json through grounded-research's bridge
    logger.info("Step 1: Loading handoff from %s", handoff_path)
    from grounded_research.shared_export import load_handoff_claims

    shared_claims = load_handoff_claims(handoff_path)
    logger.info("  Loaded %d shared ClaimRecords", len(shared_claims))

    # Step 2: Convert to onto-canon6 candidates through import adapter
    logger.info("Step 2: Converting to onto-canon6 CandidateAssertionImports")
    from onto_canon6.adapters.grounded_research_import import import_shared_claims

    candidates = import_shared_claims(shared_claims)
    logger.info("  Created %d candidate imports", len(candidates))

    # Step 3: Submit to onto-canon6 review pipeline
    logger.info("Step 3: Submitting to onto-canon6 review pipeline")
    from onto_canon6.pipeline.service import ReviewService

    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "integration_test.sqlite3"
        review_service = ReviewService(db_path=db_path)

        submitted_ids = []
        for candidate in candidates:
            result = review_service.submit_candidate_import(
                candidate_import=candidate,
            )
            submitted_ids.append(result.candidate.candidate_id)

        logger.info("  Submitted %d candidates", len(submitted_ids))

        # Step 4: Verify assertions are in the database
        logger.info("Step 4: Verifying assertions in database")
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row

        rows = conn.execute(
            "SELECT candidate_id, review_status, claim_text FROM candidate_assertions"
        ).fetchall()
        logger.info("  Found %d candidate assertions in DB", len(rows))

        # Check evidence spans
        span_count = conn.execute(
            "SELECT COUNT(*) FROM candidate_evidence_spans"
        ).fetchone()[0]
        logger.info("  Found %d evidence spans in DB", span_count)

        # Source artifacts are stored inline with candidates, not in a separate table
        source_count = conn.execute(
            "SELECT COUNT(*) FROM candidate_assertions WHERE source_kind IS NOT NULL"
        ).fetchone()[0]
        logger.info("  Found %d candidates with source artifacts", source_count)

        conn.close()

        # Build results
        results = {
            "handoff_path": str(handoff_path),
            "shared_claims_count": len(shared_claims),
            "candidates_count": len(candidates),
            "submitted_count": len(submitted_ids),
            "db_assertions_count": len(rows),
            "db_evidence_spans": span_count,
            "db_source_artifacts": source_count,
            "claims": [
                {
                    "id": c.id,
                    "statement": c.statement[:100],
                    "confidence": c.confidence.score if c.confidence else None,
                    "status": c.status,
                    "source_ids_count": len(c.source_ids),
                }
                for c in shared_claims
            ],
            "all_assertions_stored": len(rows) == len(candidates),
            "all_have_evidence": span_count >= len(candidates),
        }

        # Print summary
        print("\n" + "=" * 60)
        print("E2E INTEGRATION TEST RESULTS")
        print("=" * 60)
        print(f"Handoff: {handoff_path.name}")
        print(f"Claims loaded:     {results['shared_claims_count']}")
        print(f"Candidates created: {results['candidates_count']}")
        print(f"Submitted to DB:   {results['submitted_count']}")
        print(f"DB assertions:     {results['db_assertions_count']}")
        print(f"DB evidence spans: {results['db_evidence_spans']}")
        print(f"DB source artifacts: {results['db_source_artifacts']}")
        print(f"All stored:        {'PASS' if results['all_assertions_stored'] else 'FAIL'}")
        print(f"All have evidence: {'PASS' if results['all_have_evidence'] else 'FAIL'}")
        print("=" * 60)

        if results["all_assertions_stored"] and results["all_have_evidence"]:
            print("\nINTEGRATION TEST: PASS")
        else:
            print("\nINTEGRATION TEST: FAIL")

        return results


def main():
    parser = argparse.ArgumentParser(
        description="E2E integration test: grounded-research → onto-canon6"
    )
    parser.add_argument(
        "--handoff",
        type=Path,
        default=Path.home() / "projects" / "grounded-research" / "output" / "eu_russia_sanctions" / "handoff.json",
        help="Path to grounded-research handoff.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Path to write JSON results",
    )
    args = parser.parse_args()

    if not args.handoff.exists():
        logger.error("Handoff file not found: %s", args.handoff)
        sys.exit(1)

    results = run_integration(args.handoff)

    if args.output:
        args.output.write_text(json.dumps(results, indent=2))
        logger.info("Results written to %s", args.output)

    sys.exit(0 if results["all_assertions_stored"] else 1)


if __name__ == "__main__":
    main()

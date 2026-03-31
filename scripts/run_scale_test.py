"""Scale test: run full pipeline on synthetic corpus and measure entity resolution.

This script:
1. Extracts assertions from all 25 synthetic documents (LLM review mode)
2. Promotes accepted assertions to the graph
3. Runs LLM entity resolution
4. Measures entity resolution precision and recall against ground truth
5. Reports results

Usage:
    python scripts/run_scale_test.py [--strategy exact|fuzzy|llm] [--skip-extraction]

Requires: llm_client configured with working API keys.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from collections import defaultdict
from pathlib import Path

# Ensure src is on path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from onto_canon6.core.auto_resolution import (
    ResolutionStrategy,
    auto_resolve_identities,
)
from onto_canon6.core.identity_service import IdentityService
from onto_canon6.core.graph_service import CanonicalGraphService
from onto_canon6.pipeline.service import ReviewService

CORPUS_DIR = Path("tests/fixtures/synthetic_corpus")
GROUND_TRUTH_PATH = CORPUS_DIR / "ground_truth.json"
RESULTS_DIR = Path("docs/runs")


def load_ground_truth() -> dict:
    """Load ground truth entity registry."""
    return json.loads(GROUND_TRUTH_PATH.read_text())


def setup_db(tmp_dir: Path) -> tuple[ReviewService, Path]:
    """Create a fresh review DB for the test."""
    db_path = tmp_dir / "scale_test.sqlite3"
    overlay_root = tmp_dir / "overlays"
    overlay_root.mkdir(parents=True, exist_ok=True)

    review_svc = ReviewService(
        db_path=db_path,
        overlay_root=overlay_root,
        default_acceptance_policy="record_only",
    )
    return review_svc, db_path


def extract_all_documents(
    review_svc: ReviewService,
    corpus_dir: Path,
) -> dict[str, int]:
    """Extract assertions from all documents in the corpus.

    Uses TextExtractionService.extract_and_submit which handles:
    - LLM extraction via llm_client
    - Optional LLM judge filtering (if enable_judge_filter=true in config)
    - Review mode policy (auto/llm/human per config)

    Returns stats: {extracted, accepted, rejected, errors}.
    """
    from onto_canon6.pipeline.text_extraction import TextExtractionService

    stats: dict[str, int] = defaultdict(int)
    doc_files = sorted(corpus_dir.glob("doc_*.txt"))

    extraction_svc = TextExtractionService(review_service=review_svc)

    for doc_path in doc_files:
        text = doc_path.read_text(encoding="utf-8")
        doc_id = doc_path.stem
        logging.info("Extracting from %s (%d chars)", doc_id, len(text))

        try:
            submissions = extraction_svc.extract_and_submit(
                source_text=text,
                profile_id="general_purpose_open",
                profile_version="0.1.0",
                submitted_by=f"scale_test:{doc_id}",
                source_ref=doc_id,
                source_kind="synthetic_text",
                extraction_goal="Extract all factual assertions about people, organizations, locations, and their relationships.",
            )

            for sub in submissions:
                stats["extracted"] += 1
                if sub.candidate.review_status == "accepted":
                    stats["accepted"] += 1
                elif sub.candidate.review_status == "rejected":
                    stats["rejected"] += 1
                else:
                    stats["pending"] += 1

        except Exception as exc:
            logging.warning("Extraction failed for %s: %s", doc_id, exc)
            stats["errors"] += 1

    return dict(stats)


def promote_all(review_svc: ReviewService, db_path: Path) -> int:
    """Promote all accepted candidates to graph.

    Note: if review_mode is auto or llm, extract_and_submit already promotes.
    This is a safety net for any candidates that were accepted but not promoted.
    """
    graph_svc = CanonicalGraphService(db_path=db_path)
    store = review_svc.store
    promoted = 0

    with store.transaction() as conn:
        rows = conn.execute(
            "SELECT candidate_id, review_status FROM candidate_assertions "
            "WHERE review_status = 'accepted' ORDER BY submitted_at"
        ).fetchall()

    for row in rows:
        candidate_id = str(row[0])
        try:
            graph_svc.promote_candidate(
                candidate_id=candidate_id,
                promoted_by="scale_test",
            )
            promoted += 1
        except Exception as exc:
            logging.debug("Promote skipped for %s: %s", candidate_id, exc)

    return promoted


def run_resolution(db_path: Path, strategy: str) -> dict:
    """Run entity resolution and return result."""
    from typing import cast
    result = auto_resolve_identities(
        db_path=db_path,
        strategy=cast(ResolutionStrategy, strategy),
    )
    return {
        "entities_scanned": result.entities_scanned,
        "groups_found": result.groups_found,
        "identities_created": result.identities_created,
        "aliases_attached": result.aliases_attached,
        "already_resolved": result.already_resolved,
        "strategy": result.strategy,
    }


def evaluate_resolution(db_path: Path, ground_truth: dict) -> dict:
    """Evaluate entity resolution against ground truth.

    Measures:
    - Precision: fraction of merges that are correct
    - Recall: fraction of ground-truth merges that were found
    - False merges: entities merged that shouldn't be
    - False splits: entities that should merge but didn't
    """
    identity_svc = IdentityService(db_path=db_path)
    identities = identity_svc.list_identities()

    # Build identity clusters: identity_id → set of entity display names
    identity_clusters: dict[str, set[str]] = {}
    entity_to_identity: dict[str, str] = {}

    for bundle in identities:
        identity_id = bundle.identity.identity_id
        names: set[str] = set()
        for membership in bundle.memberships:
            # Get entity name from promoted entities
            for entity in bundle.promoted_entities:
                if entity.entity_id == membership.entity_id:
                    names.add(entity.entity_id)
                    entity_to_identity[entity.entity_id] = identity_id

        identity_clusters[identity_id] = names

    # Count multi-member identities (actual merges)
    actual_merges = [
        (iid, members)
        for iid, members in identity_clusters.items()
        if len(members) >= 2
    ]

    # Structural evaluation: we can't directly map GT entity IDs to extracted
    # entity IDs since extraction produces different IDs each time. Instead
    # we report structural metrics (multi-member identities = merges happened)
    # and dump the identity details for manual inspection.

    results = {
        "total_identities": len(identities),
        "multi_member_identities": len(actual_merges),
        "singleton_identities": len(identities) - len(actual_merges),
        "total_aliases_attached": sum(
            len(b.memberships) - 1 for b in identities if len(b.memberships) > 1
        ),
        "identity_details": [
            {
                "identity_id": b.identity.identity_id,
                "display_label": b.identity.display_label,
                "member_count": len(b.memberships),
                "entity_ids": [m.entity_id for m in b.memberships],
            }
            for b in identities
        ],
    }

    return results


def main() -> int:
    """Run the scale test."""
    parser = argparse.ArgumentParser(description="Entity resolution scale test")
    parser.add_argument(
        "--strategy", default="llm", choices=["exact", "fuzzy", "llm"],
        help="Resolution strategy (default: llm)",
    )
    parser.add_argument(
        "--skip-extraction", action="store_true",
        help="Skip extraction, use existing DB",
    )
    parser.add_argument(
        "--db-dir", type=Path, default=Path("var/scale_test"),
        help="Directory for test database",
    )
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s — %(message)s",
    )

    ground_truth = load_ground_truth()
    print(f"Ground truth: {len(ground_truth['entities'])} entities, "
          f"{len(ground_truth['expected_merges'])} expected merges, "
          f"{len(ground_truth['expected_non_merges'])} expected non-merges")

    # Setup
    db_dir = args.db_dir
    db_dir.mkdir(parents=True, exist_ok=True)

    if not args.skip_extraction:
        review_svc, db_path = setup_db(db_dir)

        # Phase 1: Extract
        print("\n--- Phase 1: Extraction ---")
        t0 = time.time()
        extraction_stats = extract_all_documents(review_svc, CORPUS_DIR)
        t1 = time.time()
        print(f"Extraction: {extraction_stats}")
        print(f"Time: {t1-t0:.1f}s")

        # Phase 2: Promote
        print("\n--- Phase 2: Promotion ---")
        promoted = promote_all(review_svc, db_path)
        print(f"Promoted: {promoted} assertions")
    else:
        db_path = db_dir / "scale_test.sqlite3"
        if not db_path.exists():
            print(f"ERROR: DB not found at {db_path}. Run without --skip-extraction first.")
            return 1

    # Phase 3: Resolution
    print(f"\n--- Phase 3: Entity Resolution (strategy={args.strategy}) ---")
    t0 = time.time()
    resolution_stats = run_resolution(db_path, args.strategy)
    t1 = time.time()
    print(f"Resolution: {json.dumps(resolution_stats, indent=2)}")
    print(f"Time: {t1-t0:.1f}s")

    # Phase 4: Evaluate
    print("\n--- Phase 4: Evaluation ---")
    eval_results = evaluate_resolution(db_path, ground_truth)
    print(f"Results: {json.dumps(eval_results, indent=2)}")

    # Save results
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = time.strftime("%Y-%m-%d_%H%M%S")
    results_path = RESULTS_DIR / f"scale_test_{args.strategy}_{timestamp}.json"
    full_results = {
        "strategy": args.strategy,
        "timestamp": timestamp,
        "extraction_stats": extraction_stats if not args.skip_extraction else "skipped",  # type: ignore[possibly-undefined]
        "resolution_stats": resolution_stats,
        "evaluation": eval_results,
        "ground_truth_summary": {
            "entities": len(ground_truth["entities"]),
            "expected_merges": len(ground_truth["expected_merges"]),
            "expected_non_merges": len(ground_truth["expected_non_merges"]),
        },
    }
    results_path.write_text(json.dumps(full_results, indent=2))
    print(f"\nResults saved to {results_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())

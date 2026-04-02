"""Full pipeline E2E: research_v3 → onto-canon6 → DIGIMON export.

Runs the complete chain on real data:
1. Load research_v3 graph.yaml → shared ClaimRecords
2. Import into onto-canon6 review pipeline
3. Accept all candidates (auto-accept for bulk import)
4. Promote accepted candidates to graph
5. Run entity resolution
6. Export to DIGIMON format
7. Verify results

Usage:
    python scripts/full_pipeline_e2e.py \
        --graph ~/projects/research_v3/output/20260315_190332_investigate_booz_allen_hamilton_lobbying/graph.yaml \
        --output-dir var/full_pipeline_e2e
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path.home() / "projects" / "research_v3"))

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def run_pipeline(graph_path: Path, output_dir: Path, strategy: str = "exact") -> dict:
    """Run the full pipeline and return results."""

    output_dir.mkdir(parents=True, exist_ok=True)
    review_db_path = output_dir / "pipeline_review.sqlite3"

    # Clean slate
    if review_db_path.exists():
        review_db_path.unlink()

    # Step 1: Load research_v3 graph → shared ClaimRecords
    logger.info("Step 1: Loading research_v3 graph.yaml")
    from shared_export import load_graph_claims

    shared_claims = load_graph_claims(graph_path)
    logger.info("  Loaded %d shared ClaimRecords", len(shared_claims))

    # Step 2: Import into onto-canon6
    logger.info("Step 2: Importing into onto-canon6")
    from onto_canon6.adapters.grounded_research_import import import_shared_claims

    candidates = import_shared_claims(shared_claims)
    logger.info("  Created %d candidate imports", len(candidates))

    # Step 3: Submit to review pipeline
    logger.info("Step 3: Submitting to review pipeline")
    from onto_canon6.pipeline.service import ReviewService

    review_service = ReviewService(db_path=review_db_path)
    submitted_ids = []
    for candidate in candidates:
        result = review_service.submit_candidate_import(candidate_import=candidate)
        submitted_ids.append(result.candidate.candidate_id)
    logger.info("  Submitted %d candidates", len(submitted_ids))

    # Step 4: Accept all candidates
    logger.info("Step 4: Accepting all candidates")
    accepted_count = 0
    for cid in submitted_ids:
        try:
            review_service.review_candidate(
                candidate_id=cid,
                decision="accepted",
                actor_id="pipeline:auto_accept",
            )
            accepted_count += 1
        except Exception as e:
            logger.warning("  Failed to accept %s: %s", cid, e)
    logger.info("  Accepted %d / %d candidates", accepted_count, len(submitted_ids))

    # Step 5: Promote accepted candidates
    logger.info("Step 5: Promoting accepted candidates")
    from onto_canon6.core.graph_service import CanonicalGraphService

    graph_service = CanonicalGraphService(db_path=review_db_path)
    promoted_count = 0
    for cid in submitted_ids:
        try:
            graph_service.promote_candidate(
                candidate_id=cid,
                promoted_by="pipeline:promoter",
            )
            promoted_count += 1
        except Exception as e:
            logger.debug("  Skip promote %s: %s", cid, e)
    logger.info("  Promoted %d candidates", promoted_count)

    # Step 6: Run entity resolution
    logger.info("Step 6: Running entity resolution")
    from onto_canon6.core.auto_resolution import auto_resolve_identities

    resolution_result = auto_resolve_identities(
        db_path=review_db_path,
        strategy=strategy,
    )
    logger.info(
        "  Resolution: %d entities scanned → %d groups → %d identities (%d aliases)",
        resolution_result.entities_scanned,
        resolution_result.groups_found,
        resolution_result.identities_created,
        resolution_result.aliases_attached,
    )

    # Step 7: Export to DIGIMON
    logger.info("Step 7: Exporting to DIGIMON format")
    from onto_canon6.adapters.digimon_export import export_for_digimon_from_db

    bundle = export_for_digimon_from_db(review_db_path)

    entities_path = output_dir / "entities.jsonl"
    relationships_path = output_dir / "relationships.jsonl"

    import dataclasses

    with open(entities_path, "w") as f:
        for e in bundle.entities:
            f.write(json.dumps(dataclasses.asdict(e)) + "\n")

    with open(relationships_path, "w") as f:
        for r in bundle.relationships:
            f.write(json.dumps(dataclasses.asdict(r)) + "\n")

    entity_count = len(bundle.entities)
    relationship_count = len(bundle.relationships)
    logger.info(
        "  Exported %d entities, %d relationships",
        entity_count,
        relationship_count,
    )

    # Build results
    results = {
        "graph_path": str(graph_path),
        "shared_claims": len(shared_claims),
        "candidates_submitted": len(submitted_ids),
        "candidates_accepted": accepted_count,
        "candidates_promoted": promoted_count,
        "resolution": {
            "entities_scanned": resolution_result.entities_scanned,
            "groups_found": resolution_result.groups_found,
            "identities_created": resolution_result.identities_created,
            "aliases_attached": resolution_result.aliases_attached,
        },
        "digimon_export": {
            "entities": entity_count,
            "relationships": relationship_count,
            "entities_path": str(entities_path),
            "relationships_path": str(relationships_path),
        },
    }

    # Summary
    print("\n" + "=" * 60)
    print("FULL PIPELINE E2E RESULTS")
    print("=" * 60)
    print(f"Source: {graph_path.name}")
    print(f"Claims loaded:        {results['shared_claims']}")
    print(f"Candidates submitted: {results['candidates_submitted']}")
    print(f"Candidates accepted:  {results['candidates_accepted']}")
    print(f"Candidates promoted:  {results['candidates_promoted']}")
    print(f"Entities scanned:     {results['resolution']['entities_scanned']}")
    print(f"Identity groups:      {results['resolution']['groups_found']}")
    print(f"Identities created:   {results['resolution']['identities_created']}")
    print(f"Aliases attached:     {results['resolution']['aliases_attached']}")
    print(f"DIGIMON entities:     {results['digimon_export']['entities']}")
    print(f"DIGIMON relationships: {results['digimon_export']['relationships']}")
    print("=" * 60)

    # Write results
    results_path = output_dir / "pipeline_results.json"
    results_path.write_text(json.dumps(results, indent=2))
    logger.info("Results written to %s", results_path)

    return results


def main():
    parser = argparse.ArgumentParser(description="Full pipeline E2E: research_v3 → DIGIMON")
    parser.add_argument(
        "--graph",
        type=Path,
        default=Path.home() / "projects" / "research_v3" / "output" / "20260315_190332_investigate_booz_allen_hamilton_lobbying" / "graph.yaml",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("var/full_pipeline_e2e"),
    )
    parser.add_argument(
        "--strategy",
        default="exact",
        choices=["exact", "fuzzy", "llm"],
        help="Entity resolution strategy",
    )
    args = parser.parse_args()

    if not args.graph.exists():
        logger.error("Graph file not found: %s", args.graph)
        sys.exit(1)

    run_pipeline(args.graph, args.output_dir, strategy=args.strategy)


if __name__ == "__main__":
    main()

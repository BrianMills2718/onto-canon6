"""Full pipeline E2E: research_v3 or grounded-research → onto-canon6 → DIGIMON export.

Runs the complete chain on real data:
1. Load shared ClaimRecords (from research_v3 graph.yaml OR grounded-research handoff.json)
2. Import into onto-canon6 review pipeline
3. Accept all candidates (auto-accept for bulk import)
4. Promote accepted candidates to graph
5. Run entity resolution
6. Export to DIGIMON format
7. Verify results

Usage (research_v3):
    python scripts/full_pipeline_e2e.py \
        --graph ~/projects/research_v3/output/.../graph.yaml \
        --output-dir var/full_pipeline_e2e

Usage (research_v3 loop memo):
    python scripts/full_pipeline_e2e.py \
        --memo ~/projects/research_v3/output/.../memo.yaml \
        --output-dir var/full_pipeline_memo

Usage (grounded-research):
    python scripts/full_pipeline_e2e.py \
        --handoff ~/projects/grounded-research/output/palantir/handoff.json \
        --output-dir var/full_pipeline_gr
"""

from __future__ import annotations

import argparse
import importlib
import json
import logging
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def _prepend_sys_path(path: Path) -> None:
    """Prepend one path to sys.path once."""

    normalized_path = str(path.resolve())
    if normalized_path not in sys.path:
        sys.path.insert(0, normalized_path)


def _find_repo_root(start_path: Path, *, required_children: tuple[str, ...]) -> Path:
    """Infer a repo root by walking up from an input artifact path."""

    resolved = start_path.resolve()
    candidates = [resolved] if resolved.is_dir() else [resolved.parent]
    candidates.extend(resolved.parents)
    for candidate in candidates:
        if all((candidate / child).exists() for child in required_children):
            return candidate
    raise RuntimeError(
        "Could not infer repository root from input path "
        f"{start_path}. Expected children: {required_children}"
    )


def _load_research_v3_claims(
    *,
    graph_path: Path | None = None,
    memo_path: Path | None = None,
    research_v3_repo: Path | None = None,
) -> list[object]:
    """Load shared ClaimRecords from research_v3 graph or memo artifacts."""

    input_path = graph_path or memo_path
    if input_path is None:
        raise ValueError("graph_path or memo_path is required")
    repo_root = (
        research_v3_repo.resolve()
        if research_v3_repo is not None
        else _find_repo_root(input_path, required_children=("shared_export.py", "pyproject.toml"))
    )
    _prepend_sys_path(repo_root)
    shared_export = importlib.import_module("shared_export")
    if graph_path is not None:
        return shared_export.load_graph_claims(graph_path)
    return shared_export.load_memo_claims(memo_path)


def _load_grounded_research_claims(
    *,
    handoff_path: Path,
    grounded_research_repo: Path | None = None,
) -> list[object]:
    """Load shared ClaimRecords from grounded-research handoff artifacts."""

    repo_root = (
        grounded_research_repo.resolve()
        if grounded_research_repo is not None
        else _find_repo_root(
            handoff_path,
            required_children=("src/grounded_research/shared_export.py", "pyproject.toml"),
        )
    )
    _prepend_sys_path(repo_root / "src")
    shared_export = importlib.import_module("grounded_research.shared_export")
    return shared_export.load_handoff_claims(handoff_path)


def run_pipeline(
    output_dir: Path,
    strategy: str = "exact",
    graph_path: Path | None = None,
    memo_path: Path | None = None,
    handoff_path: Path | None = None,
    research_v3_repo: Path | None = None,
    grounded_research_repo: Path | None = None,
) -> dict:
    """Run the full pipeline and return results.

    Exactly one of graph_path, memo_path, or handoff_path must be provided.
    """
    provided_inputs = [graph_path is not None, memo_path is not None, handoff_path is not None]
    if sum(provided_inputs) != 1:
        raise ValueError("Exactly one of graph_path, memo_path, or handoff_path must be provided")

    output_dir.mkdir(parents=True, exist_ok=True)
    review_db_path = output_dir / "pipeline_review.sqlite3"

    # Clean slate
    if review_db_path.exists():
        review_db_path.unlink()

    # Step 1: Load shared ClaimRecords from source
    if graph_path:
        logger.info("Step 1: Loading research_v3 graph.yaml from %s", graph_path)
        shared_claims = _load_research_v3_claims(
            graph_path=graph_path,
            research_v3_repo=research_v3_repo,
        )
        source_label = graph_path.name
        source_kind = "research_v3_graph"
    elif memo_path:
        logger.info("Step 1: Loading research_v3 memo.yaml from %s", memo_path)
        shared_claims = _load_research_v3_claims(
            memo_path=memo_path,
            research_v3_repo=research_v3_repo,
        )
        source_label = memo_path.name
        source_kind = "research_v3_memo"
    else:
        logger.info("Step 1: Loading grounded-research handoff.json from %s", handoff_path)
        shared_claims = _load_grounded_research_claims(
            handoff_path=handoff_path,
            grounded_research_repo=grounded_research_repo,
        )
        source_label = handoff_path.name  # type: ignore[union-attr]
        source_kind = "grounded_research_handoff"
    logger.info("  Loaded %d shared ClaimRecords", len(shared_claims))
    if not shared_claims:
        raise RuntimeError(f"No shared ClaimRecords loaded from {source_label}")

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
    accept_failures: list[str] = []
    for cid in submitted_ids:
        try:
            review_service.review_candidate(
                candidate_id=cid,
                decision="accepted",
                actor_id="pipeline:auto_accept",
            )
            accepted_count += 1
        except Exception as e:
            accept_failures.append(f"{cid}: {e}")
    if accept_failures:
        raise RuntimeError(
            "Acceptance failed for "
            f"{len(accept_failures)} candidate(s). First failure: {accept_failures[0]}"
        )
    logger.info("  Accepted %d / %d candidates", accepted_count, len(submitted_ids))

    # Step 5: Promote accepted candidates
    logger.info("Step 5: Promoting accepted candidates")
    from onto_canon6.core.graph_service import CanonicalGraphService

    graph_service = CanonicalGraphService(db_path=review_db_path)
    promoted_count = 0
    promotion_failures: list[str] = []
    for cid in submitted_ids:
        try:
            graph_service.promote_candidate(
                candidate_id=cid,
                promoted_by="pipeline:promoter",
            )
            promoted_count += 1
        except Exception as e:
            promotion_failures.append(f"{cid}: {e}")
    if promotion_failures:
        raise RuntimeError(
            "Promotion failed for "
            f"{len(promotion_failures)} candidate(s). First failure: {promotion_failures[0]}"
        )
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
        "source": str(graph_path or memo_path or handoff_path),
        "source_kind": source_kind,
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
    print(f"Source: {source_label}")
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
    parser = argparse.ArgumentParser(
        description="Full pipeline E2E: research_v3 or grounded-research → onto-canon6 → DIGIMON"
    )
    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument("--graph", type=Path, help="research_v3 graph.yaml path")
    source_group.add_argument("--memo", type=Path, help="research_v3 memo.yaml path")
    source_group.add_argument("--handoff", type=Path, help="grounded-research handoff.json path")
    parser.add_argument(
        "--research-v3-repo",
        type=Path,
        help="Optional explicit research_v3 repo root when the input artifact is outside that repo.",
    )
    parser.add_argument(
        "--grounded-research-repo",
        type=Path,
        help="Optional explicit grounded-research repo root when the handoff artifact is outside that repo.",
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

    if args.graph and not args.graph.exists():
        logger.error("Graph file not found: %s", args.graph)
        sys.exit(1)
    if args.memo and not args.memo.exists():
        logger.error("Memo file not found: %s", args.memo)
        sys.exit(1)
    if args.handoff and not args.handoff.exists():
        logger.error("Handoff file not found: %s", args.handoff)
        sys.exit(1)

    run_pipeline(
        output_dir=args.output_dir,
        strategy=args.strategy,
        graph_path=args.graph,
        memo_path=args.memo,
        handoff_path=args.handoff,
        research_v3_repo=args.research_v3_repo,
        grounded_research_repo=args.grounded_research_repo,
    )


if __name__ == "__main__":
    main()

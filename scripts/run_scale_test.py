"""Scale test: run the governed pipeline and emit a decision-grade value-proof report.

This script:
1. Extracts assertions from all 25 synthetic documents (LLM review mode)
2. Promotes accepted assertions to the graph
3. Runs LLM entity resolution
4. Scores the result against the official ground-truth and question fixtures
5. Writes one typed value-proof report under ``docs/runs/``

Usage:
    python scripts/run_scale_test.py [--strategy exact|fuzzy|llm] [--skip-extraction]

Requires: llm_client configured with working API keys.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import logging
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

# Ensure src is on path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from onto_canon6.core.auto_resolution import (
    ResolutionStrategy,
    auto_resolve_identities,
)
from onto_canon6.core.graph_service import CanonicalGraphService
from onto_canon6.evaluation import (
    EntityResolutionGroundTruth,
    ValueProofQuestionFixture,
    build_entity_resolution_value_proof_report,
    load_entity_resolution_ground_truth,
    load_value_proof_questions,
)
from onto_canon6.pipeline.service import ReviewService

CORPUS_DIR = Path("tests/fixtures/synthetic_corpus")
GROUND_TRUTH_PATH = CORPUS_DIR / "ground_truth.json"
QUESTIONS_PATH = CORPUS_DIR / "questions.json"
RESULTS_DIR = Path("docs/runs")


@dataclass(frozen=True)
class ExtractionSummary:
    """Structured summary for one scale-test extraction pass."""

    extracted: int = 0
    accepted: int = 0
    rejected: int = 0
    pending: int = 0
    errors: int = 0
    transient_failures: int = 0
    retry_passes_used: int = 0
    failed_docs: tuple[str, ...] = ()
    recovered_docs: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        """Return a stable JSON-serializable summary for CLI printing."""

        return {
            "extracted": self.extracted,
            "accepted": self.accepted,
            "rejected": self.rejected,
            "pending": self.pending,
            "errors": self.errors,
            "transient_failures": self.transient_failures,
            "retry_passes_used": self.retry_passes_used,
            "failed_docs": list(self.failed_docs),
            "recovered_docs": list(self.recovered_docs),
        }


def load_ground_truth() -> EntityResolutionGroundTruth:
    """Load ground truth entity registry."""
    return load_entity_resolution_ground_truth(GROUND_TRUTH_PATH)


def load_questions() -> ValueProofQuestionFixture:
    """Load the fixed cross-document question fixture."""

    return load_value_proof_questions(QUESTIONS_PATH)


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
    *,
    selection_task: str,
    model_override: str | None,
    judge_model_override: str | None,
    retry_failed_docs: int = 0,
    retry_delay_seconds: float = 0.0,
) -> ExtractionSummary:
    """Extract assertions from all documents in the corpus.

    Uses TextExtractionService.extract_and_submit which handles:
    - LLM extraction via llm_client
    - Optional LLM judge filtering (if enable_judge_filter=true in config)
    - Review mode policy (auto/llm/human per config)

    Returns a structured summary, including any residual failed docs after the
    bounded retry pass.
    """
    from onto_canon6.pipeline.text_extraction import TextExtractionService

    doc_files = sorted(corpus_dir.glob("doc_*.txt"))
    docs_by_id = {doc_path.stem: doc_path for doc_path in doc_files}

    extraction_svc = TextExtractionService(
        review_service=review_svc,
        selection_task=selection_task,
        model_override=model_override,
        judge_model_override=judge_model_override,
    )

    stats: dict[str, int] = defaultdict(int)
    failed_docs = _extract_documents_once(
        extraction_svc=extraction_svc,
        doc_paths=doc_files,
        stats=stats,
    )
    recovered_docs: list[str] = []
    retry_passes_used = 0

    for retry_index in range(retry_failed_docs):
        if not failed_docs:
            break
        retry_passes_used += 1
        failed_ids = tuple(sorted(failed_docs))
        logging.warning(
            "scale-test extraction retry pass %d/%d for failed docs: %s",
            retry_index + 1,
            retry_failed_docs,
            ", ".join(failed_ids),
        )
        if retry_delay_seconds > 0:
            time.sleep(retry_delay_seconds)
        retry_doc_paths = [docs_by_id[doc_id] for doc_id in failed_ids]
        retry_failures = _extract_documents_once(
            extraction_svc=extraction_svc,
            doc_paths=retry_doc_paths,
            stats=stats,
        )
        recovered_now = sorted(set(failed_docs) - set(retry_failures))
        if recovered_now:
            logging.info(
                "scale-test extraction recovered docs after retry pass %d: %s",
                retry_index + 1,
                ", ".join(recovered_now),
            )
            recovered_docs.extend(recovered_now)
        failed_docs = retry_failures

    if failed_docs:
        logging.error(
            "scale-test extraction left residual failed docs after %d retry pass(es): %s",
            retry_passes_used,
            ", ".join(sorted(failed_docs)),
        )

    return ExtractionSummary(
        extracted=stats["extracted"],
        accepted=stats["accepted"],
        rejected=stats["rejected"],
        pending=stats["pending"],
        errors=len(failed_docs),
        transient_failures=len(recovered_docs),
        retry_passes_used=retry_passes_used,
        failed_docs=tuple(sorted(failed_docs)),
        recovered_docs=tuple(sorted(recovered_docs)),
    )


def _extract_documents_once(
    *,
    extraction_svc: Any,
    doc_paths: list[Path],
    stats: dict[str, int],
) -> list[str]:
    """Extract one list of documents and return the doc ids that still failed."""

    failed_docs: list[str] = []
    for doc_path in doc_paths:
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
            failed_docs.append(doc_id)

    return failed_docs


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


def run_resolution(
    db_path: Path,
    strategy: str,
    *,
    resolution_model_override: str | None,
) -> dict[str, int | str]:
    """Run entity resolution and return result."""
    from typing import cast
    result = auto_resolve_identities(
        db_path=db_path,
        strategy=cast(ResolutionStrategy, strategy),
        model_override=resolution_model_override,
    )
    return {
        "entities_scanned": result.entities_scanned,
        "groups_found": result.groups_found,
        "identities_created": result.identities_created,
        "aliases_attached": result.aliases_attached,
        "already_resolved": result.already_resolved,
        "strategy": result.strategy,
    }


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
    parser.add_argument(
        "--selection-task",
        default="fast_extraction",
        help="llm_client task used for extraction model selection",
    )
    parser.add_argument(
        "--model-override",
        default=None,
        help="Optional explicit extraction model override for this run",
    )
    parser.add_argument(
        "--judge-model-override",
        default=None,
        help="Optional explicit judge-model override for this run",
    )
    parser.add_argument(
        "--resolution-model-override",
        default=None,
        help="Optional explicit LLM resolution model override for this run",
    )
    parser.add_argument(
        "--retry-failed-docs",
        type=int,
        default=1,
        help="How many bounded retry passes to run over docs that fail extraction (default: 1)",
    )
    parser.add_argument(
        "--retry-delay-seconds",
        type=float,
        default=5.0,
        help="Seconds to wait before retrying failed docs (default: 5.0)",
    )
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s — %(message)s",
    )

    ground_truth = load_ground_truth()
    questions = load_questions()
    print(
        f"Ground truth: {len(ground_truth.entities)} entities, "
        f"{len(ground_truth.expected_merges)} expected merges, "
        f"{len(ground_truth.expected_non_merges)} expected non-merges"
    )
    print(f"Questions: {len(questions.questions)} fixed cross-document checks")

    # Setup
    db_dir = args.db_dir
    db_dir.mkdir(parents=True, exist_ok=True)

    if not args.skip_extraction:
        review_svc, db_path = setup_db(db_dir)

        # Phase 1: Extract
        print("\n--- Phase 1: Extraction ---")
        t0 = time.time()
        extraction_stats = extract_all_documents(
            review_svc,
            CORPUS_DIR,
            selection_task=args.selection_task,
            model_override=args.model_override,
            judge_model_override=args.judge_model_override,
            retry_failed_docs=max(args.retry_failed_docs, 0),
            retry_delay_seconds=max(args.retry_delay_seconds, 0.0),
        )
        t1 = time.time()
        print(f"Extraction: {extraction_stats.as_dict()}")
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
    resolution_stats = run_resolution(
        db_path,
        args.strategy,
        resolution_model_override=args.resolution_model_override,
    )
    t1 = time.time()
    print(f"Resolution: {json.dumps(resolution_stats, indent=2)}")
    print(f"Time: {t1-t0:.1f}s")

    # Phase 4: Evaluate
    print("\n--- Phase 4: Evaluation ---")
    report = build_entity_resolution_value_proof_report(
        db_path=db_path,
        ground_truth=ground_truth,
        questions=questions,
        strategy=args.strategy,
    )
    print(
        json.dumps(
            {
                "precision": report.pairwise_metrics.precision,
                "recall": report.pairwise_metrics.recall,
                "false_merges": len(report.pairwise_metrics.false_merge_pairs),
                "false_splits": len(report.pairwise_metrics.false_split_pairs),
                "unmatched": report.pairwise_metrics.unmatched_observation_count,
                "ambiguous": report.pairwise_metrics.ambiguous_observation_count,
                "question_answer_rate": report.question_summary.answer_rate,
                "question_accuracy": report.question_summary.accuracy_over_all_questions,
            },
            indent=2,
        )
    )

    # Save results
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = time.strftime("%Y-%m-%d_%H%M%S")
    results_path = RESULTS_DIR / f"scale_test_{args.strategy}_{timestamp}.json"
    results_path.write_text(
        json.dumps(report.model_dump(mode="json"), indent=2),
        encoding="utf-8",
    )
    print(f"\nResults saved to {results_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())

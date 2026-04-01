"""Run the bare entity-extraction baseline on the official synthetic corpus.

This baseline deliberately avoids the onto-canon6 governance and identity stack.
It:

1. extracts explicit named-entity surface forms from each corpus document;
2. treats every extracted mention as its own singleton cluster; and
3. scores the result with the same value-proof evaluator used by the governed
   resolution path.

The goal is not to be clever. The goal is to produce the simplest honest
comparison artifact on the same corpus and fixed question set.
"""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
from importlib import import_module
import json
from pathlib import Path
import sys
import uuid

from pydantic import BaseModel, ConfigDict, Field

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))

CORPUS_DIR = PROJECT_ROOT / "tests" / "fixtures" / "synthetic_corpus"
GROUND_TRUTH_PATH = CORPUS_DIR / "ground_truth.json"
QUESTIONS_PATH = CORPUS_DIR / "questions.json"
PROMPT_TEMPLATE = "prompts/evaluation/bare_entity_extraction.yaml"
RESULTS_DIR = PROJECT_ROOT / "docs" / "runs"


class BareEntityMention(BaseModel):
    """One bare extracted named-entity surface form."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, description="Exact surface form from the source text")
    evidence: str = Field(
        min_length=1,
        description="Short excerpt from the source text supporting the entity mention",
    )


class BareEntityExtractionResponse(BaseModel):
    """Structured response for the bare mention-extraction baseline."""

    model_config = ConfigDict(extra="forbid")

    entities: list[BareEntityMention] = Field(
        default_factory=list,
        description="Distinct named-entity surface forms found in the source text",
    )


def run_bare_entity_baseline(
    *,
    corpus_dir: Path,
    output_path: Path | None,
    selection_task: str,
    max_budget: float,
) -> Path:
    """Run the bare baseline and write one decision-grade report."""

    from onto_canon6.evaluation import (
        EntityObservation,
        build_value_proof_report_from_observations,
        load_entity_resolution_ground_truth,
        load_value_proof_questions,
    )

    llm_client = import_module("llm_client")
    render_prompt = llm_client.render_prompt
    call_llm_structured = llm_client.call_llm_structured
    get_model = llm_client.get_model

    selected_model = get_model(selection_task, use_performance=True)
    observations: list[EntityObservation] = []
    doc_paths = sorted(corpus_dir.glob("doc_*.txt"))
    if not doc_paths:
        raise RuntimeError(f"no synthetic corpus docs found under {corpus_dir}")

    for doc_path in doc_paths:
        source_ref = doc_path.stem
        source_text = doc_path.read_text(encoding="utf-8")
        trace_id = f"bare_entity_baseline_{source_ref}_{uuid.uuid4().hex[:10]}"
        messages = render_prompt(
            PROMPT_TEMPLATE,
            source_ref=source_ref,
            source_text=source_text,
        )
        response, _meta = call_llm_structured(
            selected_model,
            messages,
            response_model=BareEntityExtractionResponse,
            task=selection_task,
            trace_id=trace_id,
            max_budget=max_budget,
        )
        seen_names: set[str] = set()
        for index, mention in enumerate(response.entities):
            normalized_name = mention.name.strip()
            if normalized_name in seen_names:
                continue
            seen_names.add(normalized_name)
            entity_id = f"bare_{source_ref}_{index:03d}"
            observations.append(
                EntityObservation(
                    entity_id=entity_id,
                    entity_type=None,
                    first_candidate_id=f"bare_candidate_{source_ref}_{index:03d}",
                    predicted_cluster_id=entity_id,
                    observed_names=(normalized_name,),
                    source_refs=(source_ref,),
                    matched_ground_truth_entity_id=None,
                    match_status="unmatched",
                    match_reason="ground-truth matching not yet run",
                    candidate_ground_truth_entity_ids=(),
                )
            )

    ground_truth = load_entity_resolution_ground_truth(GROUND_TRUTH_PATH)
    questions = load_value_proof_questions(QUESTIONS_PATH)
    report = build_value_proof_report_from_observations(
        state_ref=f"bare-baseline:{corpus_dir}",
        observations=tuple(observations),
        ground_truth=ground_truth,
        questions=questions,
        strategy="bare_baseline",
    )

    resolved_output_path = output_path or (
        RESULTS_DIR
        / f"scale_test_bare_{datetime.now(UTC).strftime('%Y-%m-%d_%H%M%S')}.json"
    )
    resolved_output_path.parent.mkdir(parents=True, exist_ok=True)
    resolved_output_path.write_text(
        json.dumps(report.model_dump(mode="json"), indent=2),
        encoding="utf-8",
    )
    return resolved_output_path


def main() -> int:
    """Run the bare baseline and print the output artifact path."""

    parser = argparse.ArgumentParser(description="Bare entity baseline over the synthetic corpus")
    parser.add_argument(
        "--corpus-dir",
        type=Path,
        default=CORPUS_DIR,
        help="Path to the synthetic corpus directory",
    )
    parser.add_argument(
        "--task",
        default="fast_extraction",
        help="llm_client task name used for model selection",
    )
    parser.add_argument(
        "--budget",
        type=float,
        default=0.10,
        help="Maximum per-call budget in USD",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional explicit output JSON path",
    )
    args = parser.parse_args()

    output_path = run_bare_entity_baseline(
        corpus_dir=args.corpus_dir,
        output_path=args.output,
        selection_task=args.task,
        max_budget=args.budget,
    )
    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

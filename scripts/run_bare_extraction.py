"""Bare extraction baseline: extract entities and relationships without ontology.

This is the Phase 4d comparison baseline. Uses a simple prompt to extract
entities and relationships as JSON, with no ontology validation, no governance
review, and no entity resolution. The goal is to measure what onto-canon6's
pipeline adds over naive extraction.

Usage:
    python scripts/run_bare_extraction.py [--output-dir var/bare_extraction]

Output:
- entities.json: all extracted entities across all documents
- relationships.json: all extracted relationships
- entity_resolution.json: name-based dedup results (simple exact match)
"""

from __future__ import annotations

import asyncio
import json
import logging
import sys
import time
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

CORPUS_DIR = Path("tests/fixtures/synthetic_corpus")
GROUND_TRUTH_PATH = CORPUS_DIR / "ground_truth.json"

BARE_EXTRACTION_PROMPT = """Extract all entities (people, organizations, places) and relationships from the following text.

For each entity, provide:
- name: the entity's name as it appears in the text
- type: person, organization, location, or other

For each relationship, provide:
- subject: the source entity name
- predicate: the relationship type (e.g., "commands", "located_at", "works_for")
- object: the target entity name

Return a JSON object with "entities" and "relationships" arrays.

Text:
{text}
"""


def normalize(name: str) -> str:
    """Simple name normalization for bare extraction dedup."""
    return " ".join(name.lower().strip().split())


async def extract_document(text: str, doc_id: str, model: str) -> dict:
    """Extract entities and relationships from one document using bare prompt."""
    from llm_client import acall_llm

    messages = [
        {"role": "user", "content": BARE_EXTRACTION_PROMPT.format(text=text)},
    ]

    result = await acall_llm(
        model,
        messages,
        task="bare_extraction_baseline",
        trace_id=f"bare_extraction.{doc_id}",
        max_budget=0.25,
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "BareExtraction",
                "schema": {
                    "type": "object",
                    "properties": {
                        "entities": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "type": {"type": "string"},
                                },
                                "required": ["name", "type"],
                            },
                        },
                        "relationships": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "subject": {"type": "string"},
                                    "predicate": {"type": "string"},
                                    "object": {"type": "string"},
                                },
                                "required": ["subject", "predicate", "object"],
                            },
                        },
                    },
                    "required": ["entities", "relationships"],
                },
            },
        },
    )

    response_text = result.content if hasattr(result, "content") else str(result)
    return json.loads(response_text)


def deduplicate_entities(all_entities: list[dict]) -> dict:
    """Simple name-based entity dedup (the bare extraction equivalent of resolution)."""
    groups: dict[str, list[dict]] = defaultdict(list)
    for entity in all_entities:
        key = normalize(entity["name"])
        groups[key].append(entity)

    deduped = []
    for key, group in groups.items():
        canonical = max(group, key=lambda e: len(e["name"]))  # longest name variant
        deduped.append({
            "canonical_name": canonical["name"],
            "type": canonical["type"],
            "variant_count": len(group),
            "variants": list({e["name"] for e in group}),
        })

    return {
        "total_before_dedup": len(all_entities),
        "total_after_dedup": len(deduped),
        "entities": deduped,
    }


def score_against_ground_truth(dedup_result: dict) -> dict:
    """Score bare extraction entity resolution against ground truth."""
    gt = json.loads(GROUND_TRUTH_PATH.read_text())

    found_gt: set[str] = set()
    for entity in dedup_result["entities"]:
        norm_name = normalize(entity["canonical_name"])
        for gt_id, gt_entity in gt["entities"].items():
            for variant in gt_entity["name_variants"]:
                if normalize(variant) == norm_name:
                    found_gt.add(gt_id)

    expected = set(gt["entities"].keys())
    return {
        "gt_entities_found": sorted(found_gt),
        "gt_entities_missed": sorted(expected - found_gt),
        "recall": len(found_gt) / len(expected) if expected else 0.0,
        "total_extracted_entities": dedup_result["total_after_dedup"],
        "expected_entities": len(expected),
    }


async def main() -> int:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=Path("var/bare_extraction"))
    parser.add_argument("--model", default="gemini/gemini-2.5-flash")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s — %(message)s",
    )

    args.output_dir.mkdir(parents=True, exist_ok=True)

    doc_files = sorted(CORPUS_DIR.glob("doc_*.txt"))
    all_entities: list[dict] = []
    all_relationships: list[dict] = []
    extraction_stats: dict[str, int] = defaultdict(int)

    print(f"Extracting from {len(doc_files)} documents...")
    t0 = time.time()

    for doc_path in doc_files:
        text = doc_path.read_text(encoding="utf-8")
        doc_id = doc_path.stem
        try:
            result = await extract_document(text, doc_id, args.model)
            entities = result.get("entities", [])
            relationships = result.get("relationships", [])
            for e in entities:
                e["source_doc"] = doc_id
            for r in relationships:
                r["source_doc"] = doc_id
            all_entities.extend(entities)
            all_relationships.extend(relationships)
            extraction_stats["docs_extracted"] += 1
            extraction_stats["entities"] += len(entities)
            extraction_stats["relationships"] += len(relationships)
            logging.info("Extracted %d entities, %d relationships from %s",
                         len(entities), len(relationships), doc_id)
        except Exception as exc:
            logging.error("Failed to extract from %s: %s", doc_id, exc)
            extraction_stats["errors"] += 1

    t1 = time.time()
    print(f"Extraction: {dict(extraction_stats)}")
    print(f"Time: {t1-t0:.1f}s")

    # Save raw extractions
    (args.output_dir / "entities.json").write_text(json.dumps(all_entities, indent=2))
    (args.output_dir / "relationships.json").write_text(json.dumps(all_relationships, indent=2))

    # Deduplicate
    dedup = deduplicate_entities(all_entities)
    (args.output_dir / "entity_resolution.json").write_text(json.dumps(dedup, indent=2))
    print(f"\nDedup: {dedup['total_before_dedup']} → {dedup['total_after_dedup']} entities")

    # Score
    scores = score_against_ground_truth(dedup)
    print(f"GT recall: {scores['recall']:.1%} ({len(scores['gt_entities_found'])}/{scores['expected_entities']})")
    print(f"GT found: {scores['gt_entities_found']}")
    print(f"GT missed: {scores['gt_entities_missed']}")

    # Save results
    results = {
        "strategy": "bare_extraction",
        "model": args.model,
        "timestamp": time.strftime("%Y-%m-%d_%H%M%S"),
        "extraction_stats": dict(extraction_stats),
        "extraction_time_s": round(t1-t0, 1),
        "dedup": {
            "before": dedup["total_before_dedup"],
            "after": dedup["total_after_dedup"],
        },
        "ground_truth_scores": scores,
    }
    results_path = Path("docs/runs") / f"bare_extraction_{results['timestamp']}.json"
    results_path.write_text(json.dumps(results, indent=2))
    print(f"\nResults saved to {results_path}")

    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))

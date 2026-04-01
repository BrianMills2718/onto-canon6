"""Score scale test results against ground truth.

Matches identity clusters from the scale test to ground truth entities by
checking whether entity display names match any known name variant. Then
measures precision (correct merges / total merges) and recall (found merges /
expected merges).

Usage:
    python scripts/score_scale_test.py docs/runs/scale_test_llm_2026-03-31_160705.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

GROUND_TRUTH_PATH = Path("tests/fixtures/synthetic_corpus/ground_truth.json")


def normalize(name: str) -> str:
    """Normalize for fuzzy comparison."""
    return " ".join(name.lower().strip(" .,;:").split())


def load_ground_truth() -> dict:
    return json.loads(GROUND_TRUTH_PATH.read_text())


def match_entity_to_gt(entity_id: str, display_label: str, gt: dict) -> str | None:
    """Try to match an extracted entity name to a ground truth entity ID.

    Returns GT entity ID (e.g., "E001") or None.
    """
    norm_label = normalize(display_label)

    for gt_id, gt_entity in gt["entities"].items():
        for variant in gt_entity["name_variants"]:
            norm_variant = normalize(variant)
            # Check if the display label contains the variant or vice versa
            if norm_label == norm_variant:
                return gt_id
            # Also check if entity_id contains the normalized variant
            norm_eid = normalize(entity_id.split(":")[-1].replace("_", " "))
            if norm_eid == norm_variant:
                return gt_id
    return None


def score_results(results_path: Path) -> dict:
    """Score a scale test result file against ground truth."""
    gt = load_ground_truth()
    results = json.loads(results_path.read_text())
    details = results["evaluation"]["identity_details"]

    # For each identity cluster, try to match members to GT entities
    cluster_gt_mapping: list[dict] = []

    for cluster in details:
        if cluster["member_count"] < 2:
            continue

        # Try to match the display label to a GT entity
        display = cluster["display_label"]
        gt_match = match_entity_to_gt("", display, gt)

        # Also try matching individual entity IDs
        member_gt_ids: set[str] = set()
        for eid in cluster["entity_ids"]:
            # Extract the name part from entity IDs like "ent:auto:xxx:type:name_here"
            parts = eid.split(":")
            if len(parts) >= 5:
                name_part = parts[-1].replace("_", " ")
                m = match_entity_to_gt(eid, name_part, gt)
                if m:
                    member_gt_ids.add(m)

        if gt_match:
            member_gt_ids.add(gt_match)

        cluster_gt_mapping.append({
            "display_label": display,
            "member_count": cluster["member_count"],
            "gt_entities": sorted(member_gt_ids),
            "is_correct_merge": len(member_gt_ids) == 1 and len(member_gt_ids) > 0,
            "is_false_merge": len(member_gt_ids) > 1,
            "is_noise": len(member_gt_ids) == 0,
        })

    # Count results
    correct_merges = sum(1 for c in cluster_gt_mapping if c["is_correct_merge"])
    false_merges = sum(1 for c in cluster_gt_mapping if c["is_false_merge"])
    noise_clusters = sum(1 for c in cluster_gt_mapping if c["is_noise"])
    total_multi_clusters = len(cluster_gt_mapping)

    # Check which GT entities were found (recall)
    expected_merges = gt["expected_merges"]
    gt_entities_found: set[str] = set()
    for c in cluster_gt_mapping:
        gt_entities_found.update(c["gt_entities"])

    expected_gt_ids = {m["entity"].replace("entity", "E") if "entity" not in m else m["entity"]
                       for m in expected_merges}
    # The expected merges reference entity IDs like "E001"
    expected_gt_ids = set()
    for m in expected_merges:
        expected_gt_ids.add(m["entity"])

    found_expected = expected_gt_ids & gt_entities_found
    missed_expected = expected_gt_ids - gt_entities_found

    # Check expected non-merges
    expected_non_merges = gt["expected_non_merges"]
    non_merge_violations = []
    for nm in expected_non_merges:
        nm_entities = set(nm["entities"])
        for c in cluster_gt_mapping:
            if len(nm_entities & set(c["gt_entities"])) > 1:
                non_merge_violations.append({
                    "expected_separate": nm["entities"],
                    "found_merged_in": c["display_label"],
                    "description": nm["description"],
                })

    # Also check for the E001/E011 false merge specifically
    smith_clusters = [c for c in cluster_gt_mapping
                      if "E001" in c["gt_entities"] or "E011" in c["gt_entities"]]

    precision = correct_merges / total_multi_clusters if total_multi_clusters > 0 else 0.0
    recall = len(found_expected) / len(expected_gt_ids) if expected_gt_ids else 0.0

    return {
        "strategy": results.get("strategy", "unknown"),
        "total_multi_member_clusters": total_multi_clusters,
        "correct_merges": correct_merges,
        "false_merges": false_merges,
        "noise_clusters": noise_clusters,
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "expected_merges_found": sorted(found_expected),
        "expected_merges_missed": sorted(missed_expected),
        "non_merge_violations": non_merge_violations,
        "smith_clusters": smith_clusters,
        "cluster_details": cluster_gt_mapping,
    }


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python scripts/score_scale_test.py <results.json>")
        return 1

    results_path = Path(sys.argv[1])
    if not results_path.exists():
        print(f"File not found: {results_path}")
        return 1

    scores = score_results(results_path)

    print(f"Strategy: {scores['strategy']}")
    print(f"\n--- Precision / Recall ---")
    print(f"Precision: {scores['precision']:.1%} ({scores['correct_merges']}/{scores['total_multi_member_clusters']} multi-member clusters are correct)")
    print(f"Recall:    {scores['recall']:.1%} ({len(scores['expected_merges_found'])}/{len(scores['expected_merges_found']) + len(scores['expected_merges_missed'])} expected merges found)")
    print(f"False merges: {scores['false_merges']}")
    print(f"Noise clusters: {scores['noise_clusters']} (entities not in ground truth)")

    print(f"\n--- Expected Merges ---")
    print(f"Found: {scores['expected_merges_found']}")
    print(f"Missed: {scores['expected_merges_missed']}")

    if scores['non_merge_violations']:
        print(f"\n--- Non-Merge Violations (FALSE MERGES) ---")
        for v in scores['non_merge_violations']:
            print(f"  {v['expected_separate']} merged in '{v['found_merged_in']}': {v['description']}")
    else:
        print(f"\n--- No non-merge violations (all expected separations held) ---")

    if scores['smith_clusters']:
        print(f"\n--- Smith disambiguation test ---")
        for c in scores['smith_clusters']:
            print(f"  '{c['display_label']}': GT={c['gt_entities']}, correct={c['is_correct_merge']}")

    print(f"\n--- Cluster Details ---")
    for c in scores['cluster_details']:
        status = "CORRECT" if c['is_correct_merge'] else ("FALSE MERGE" if c['is_false_merge'] else "NOISE")
        print(f"  [{status}] {c['display_label']:45s} members={c['member_count']} gt={c['gt_entities']}")

    # Save scores
    score_path = results_path.with_suffix(".scores.json")
    score_path.write_text(json.dumps(scores, indent=2))
    print(f"\nScores saved to {score_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())

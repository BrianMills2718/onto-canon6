"""Run the full onto-canon6 pipeline on real research_v3 investigation data.

Imports claims from research_v3 graph.yaml files, extracts assertions via LLM,
accepts, promotes, and resolves entities.

Usage:
    python scripts/run_real_investigation.py [--max-claims 20]
"""

from __future__ import annotations

import json
import logging
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

INVESTIGATION_PATHS = [
    Path("/home/brian/projects/research_v3/output/20260315_071621_investigate_booz_allen_hamilton_federal_/graph.yaml"),
    Path("/home/brian/projects/research_v3/output/20260315_180355_investigate_booz_allen_hamilton_lobbying/graph.yaml"),
]

DB_DIR = Path("var/real_investigation")


def main() -> int:
    import argparse
    import yaml

    parser = argparse.ArgumentParser()
    parser.add_argument("--max-claims", type=int, default=20, help="Max claims to extract per investigation")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s — %(message)s",
    )

    DB_DIR.mkdir(parents=True, exist_ok=True)
    db_path = DB_DIR / "investigation.sqlite3"

    # Clean start
    if db_path.exists():
        db_path.unlink()

    from onto_canon6.config import clear_config_cache
    clear_config_cache()
    from onto_canon6.pipeline.text_extraction import TextExtractionService
    from onto_canon6.pipeline.service import ReviewService
    from onto_canon6.core.graph_service import CanonicalGraphService
    from onto_canon6.core.auto_resolution import auto_resolve_identities

    overlay_root = DB_DIR / "overlays"
    overlay_root.mkdir(parents=True, exist_ok=True)

    review_svc = ReviewService(
        db_path=db_path,
        overlay_root=overlay_root,
        default_acceptance_policy="record_only",
    )
    ext_svc = TextExtractionService(review_service=review_svc)
    graph_svc = CanonicalGraphService(db_path=db_path)

    t0 = time.time()
    total_extracted = 0
    total_accepted = 0
    total_promoted = 0

    for inv_path in INVESTIGATION_PATHS:
        if not inv_path.exists():
            print(f"Skipping {inv_path} (not found)")
            continue

        data = yaml.safe_load(inv_path.read_text())
        claims = data.get("claims", [])[:args.max_claims]
        inv_name = inv_path.parent.name

        print(f"\n=== {inv_name} ({len(claims)} claims) ===")

        for i, claim in enumerate(claims):
            text = claim.get("statement", claim.get("claim", ""))
            if not text or len(text) < 20:
                continue

            print(f"  Claim {i}: {text[:60]}...")

            try:
                submissions = ext_svc.extract_and_submit(
                    source_text=text,
                    profile_id="general_purpose_open",
                    profile_version="0.1.0",
                    submitted_by=f"investigation:{inv_name}",
                    source_ref=f"{inv_name}:claim_{i}",
                    source_kind="research_v3_claim",
                    extraction_goal="Extract factual assertions about organizations, people, contracts, and relationships.",
                )

                for sub in submissions:
                    total_extracted += 1
                    if sub.candidate.review_status == "accepted":
                        total_accepted += 1
                        try:
                            graph_svc.promote_candidate(
                                candidate_id=sub.candidate.candidate_id,
                                promoted_by="investigation_pipeline",
                            )
                            total_promoted += 1
                        except Exception:
                            pass  # Already promoted or promotion conflict

                print(f"    → {len(submissions)} candidates")

            except Exception as exc:
                print(f"    → ERROR: {type(exc).__name__}: {str(exc)[:80]}")

    t1 = time.time()
    print(f"\n=== Extraction Complete ({t1-t0:.0f}s) ===")
    print(f"Extracted: {total_extracted}, Accepted: {total_accepted}, Promoted: {total_promoted}")

    # Entity resolution
    if total_promoted > 0:
        print("\n=== Entity Resolution ===")
        t2 = time.time()
        result = auto_resolve_identities(
            db_path=db_path,
            strategy="exact",
            require_llm_review=False,  # Fast first pass
        )
        t3 = time.time()
        print(f"Entities: {result.entities_scanned}, Groups: {result.groups_found}")
        print(f"Identities: {result.identities_created}, Aliases: {result.aliases_attached}")
        print(f"Time: {t3-t2:.1f}s")

    # Summary
    import sqlite3
    conn = sqlite3.connect(str(db_path))
    entities = conn.execute("SELECT COUNT(*) FROM promoted_graph_entities").fetchone()[0]
    assertions = conn.execute("SELECT COUNT(*) FROM promoted_graph_assertions").fetchone()[0]
    try:
        identities = conn.execute("SELECT COUNT(*) FROM graph_identities").fetchone()[0]
        multi = conn.execute(
            "SELECT COUNT(*) FROM graph_identities WHERE identity_id IN "
            "(SELECT identity_id FROM graph_identity_memberships GROUP BY identity_id HAVING COUNT(*) > 1)"
        ).fetchone()[0]
    except Exception:
        identities = 0
        multi = 0

    print(f"\n=== Final State ===")
    print(f"Promoted assertions: {assertions}")
    print(f"Promoted entities: {entities}")
    print(f"Identities: {identities} ({multi} multi-member)")
    print(f"Total time: {time.time()-t0:.0f}s")

    # Save summary
    summary = {
        "investigations": [str(p) for p in INVESTIGATION_PATHS],
        "max_claims_per_investigation": args.max_claims,
        "extracted": total_extracted,
        "accepted": total_accepted,
        "promoted": total_promoted,
        "entities": entities,
        "assertions": assertions,
        "identities": identities,
        "multi_member_identities": multi,
        "total_time_s": round(time.time() - t0, 1),
        "timestamp": time.strftime("%Y-%m-%d_%H%M%S"),
    }
    out_path = Path(f"docs/runs/real_investigation_{summary['timestamp']}.json")
    out_path.write_text(json.dumps(summary, indent=2))
    print(f"\nResults saved to {out_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())

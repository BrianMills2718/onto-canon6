# Phase 14 Agent Surface and Adapter Shape

Updated: 2026-03-18

## Purpose

This note locks the smallest Phase 14 slice that restores real agent utility
and one real adapter without recreating the v1 monolith.

## Requirements

The slice must:

1. expose at least one richer agent-facing boundary than the CLI;
2. recover one real adapter through an explicit typed contract;
3. keep the richer surface thin and service-backed;
4. keep imported adapter provenance visible through existing review, artifact,
   and governed-bundle surfaces;
5. fail loudly on unsupported adapter input rather than silently skipping it.

The slice must not:

1. recreate the v1 MCP tool sprawl;
2. add a second workflow runtime around the proved services;
3. import all WhyGame or DIGIMON shapes at once;
4. bypass the candidate-review path.

## Chosen Shape

Phase 14 uses:

1. `fastmcp` as the richer surface;
2. a local `whygame_minimal` ontology pack plus `whygame_minimal_strict`
   profile;
3. a successor-local WhyGame relationship adapter that converts WhyGame
   `RELATIONSHIP` facts into candidate assertions.

The imported assertion shape is:

1. predicate: `whygame:relationship`
2. roles:
   - `source_concept` -> entity filler
   - `target_concept` -> entity filler
   - `relationship_label` -> string value filler

The adapter also:

1. records request-level source provenance on each candidate;
2. records fact-level source metadata such as fact id, confidence, and context;
3. optionally registers one `analysis_result` artifact for the WhyGame batch
   and links imported candidates back to it.

## Tool Set

The first MCP surface exposes only:

1. `canon6_import_whygame_relationships`
2. `canon6_list_candidates`
3. `canon6_list_proposals`
4. `canon6_review_candidate`
5. `canon6_review_proposal`
6. `canon6_apply_overlay`
7. `canon6_promote_candidate`
8. `canon6_export_governed_bundle`

## Acceptance Criteria

Phase 14 counts as successful if:

1. the repo has a local ADR describing the chosen surface and adapter shape;
2. WhyGame relationship facts import into reviewable candidate assertions
   through an explicit typed successor-local contract;
3. imported WhyGame candidate provenance is visible in the governed-bundle
   export;
4. the MCP surface remains a thin wrapper over existing services;
5. one integration test proves the richer surface can import, review, and
   export through MCP-callable functions;
6. one notebook proves the chosen adapter and surface on a real local slice.

## Deferred Questions

Still intentionally deferred:

1. DIGIMON recovery;
2. broader WhyGame fact-type support;
3. large MCP tool expansion;
4. whether any later richer surface should be UI-first instead of MCP-first.

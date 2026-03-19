# Run Summary: 2026-03-18 PSYOP Stage 1

## Status

Completed.

This was the first real non-fixture `onto-canon6` workflow run over local
research outputs from the earlier `onto-canon` lineage.

## Corpus

Copied into the local run directory from `../onto-canon/research_outputs/`:

1. `stage1_query2_20251118_122424.md`
2. `stage1_query3_20251118_122613.md`
3. `stage1_query4_20251118_122813.md`

The live extraction path ultimately ran on bounded chunk files derived from all
three copied documents.

## Runtime

- profile: `psyop_seed@0.1.0`
- review DB: `var/real_runs/2026-03-18_psyop_stage1/review_state_v3.sqlite3`
- overlay root: `var/real_runs/2026-03-18_psyop_stage1/ontology_overlays_v3`
- outputs root: `var/real_runs/2026-03-18_psyop_stage1/outputs`

## Acceptance Criteria Result

1. Three non-fixture source documents were copied into the local run directory
   and processed through the live extraction path via deterministic chunking.
   Pass.
2. Live extraction persisted candidate assertions into the isolated review
   database without notebook fixtures or test doubles. Pass.
3. At least five candidate assertions received explicit human review decisions.
   Pass.
4. Ontology proposals were not generated in this run, so proposal review and
   overlay application were not exercised. Neutral.
5. Accepted candidates were promoted into the durable graph slice. Pass.
6. Governed-bundle and promoted-graph exports were produced from the real-run
   state. Pass.
7. A concrete friction log exists. Pass.

## Results

- candidate assertions persisted: `16`
- accepted candidates: `6`
- rejected candidates: `10`
- pending candidates: `0`
- promoted assertions: `6`

Accepted promoted assertions in the final export:

1. `4th PSYOP Group (Airborne) -> Army`
2. `8th PSYOP Group (Airborne) -> Army`
3. `193rd Special Operations Wing -> Air Force`
4. `Naval Reserve PSYOP AV Unit -> Navy`
5. `4th Psychological Operations Group (Airborne) -> 1st Special Forces Command (Airborne)`
6. `Operation Enduring Freedom -> Afghanistan`

Rejected patterns that mattered:

1. alias-like self-reference candidates such as `USAFRICOM -> U.S. Africa Command`
2. vague narrative claims that were structurally valid but not useful governed
   assertions
3. predicate misfits such as `use_organizational_form` or `hold_command_role`
   where the text really supported a different relation

## Key Outputs

- `var/real_runs/2026-03-18_psyop_stage1/outputs/governed_bundle_v4.json`
- `var/real_runs/2026-03-18_psyop_stage1/outputs/promoted_graph_report_v4.json`
- `var/real_runs/2026-03-18_psyop_stage1/outputs/01_chunk_001_budget_extract_v3.json`
- `var/real_runs/2026-03-18_psyop_stage1/outputs/01_chunk_004_extract_v3.json`
- `var/real_runs/2026-03-18_psyop_stage1/outputs/02_chunk_001_extract_v1.json`
- `var/real_runs/2026-03-18_psyop_stage1/outputs/03_chunk_001_extract_v1.json`

## What Broke During the Run

1. whole-report extraction selected an impractical long-thinking model path and
   forced the introduction of deterministic chunking
2. evidence offsets from live extraction were unreliable enough that the
   extractor had to resolve offsets from quoted evidence text
3. live extraction needed source-scoped local entity-id derivation because
   reviewer-meaningful names were often available before stable ids
4. the graph-promotion slice failed on normalized-only value fillers, which was
   a real contract bug and was fixed during the run

## Decision

This run is enough to satisfy the post-Phase-15 adoption gate once.

It is not evidence for a new broad phase by itself. Any later roadmap
extension should point to concrete friction from this run or a later real
consumer workflow rather than to parity pressure alone.

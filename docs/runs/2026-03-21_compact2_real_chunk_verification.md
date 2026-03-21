# Run Summary: 2026-03-21 compact2 Real Chunk Verification

## Purpose

Verify the broad-benchmark winner on the operational extraction path without
changing the repo-wide live extraction prompt.

This run also proves the bounded override path:

1. extraction-service prompt override;
2. explicit prompt reference override;
3. explicit prompt-render budget override; and
4. the same Stage 1 chunk that previously exposed the Phase B overbinding
   errors.

## Runtime

Bounded operational lane:

- project: `onto-canon6-compact2-real-chunk-max10`
- task: `budget_extraction`
- prompt template:
  `prompts/extraction/text_to_candidate_assertions_compact_v2.yaml`
- prompt ref: `onto_canon6.extraction.text_to_candidate_assertions_compact_v2@1`
- prompt render budget:
  - `max_candidates_per_call = 10`
  - `max_evidence_spans_per_candidate = 1`
- review db:
  `var/real_runs/2026-03-21_compact2_real_chunk_verification/review_state_max10.sqlite3`
- reviewed candidate snapshot:
  `var/real_runs/2026-03-21_compact2_real_chunk_verification/outputs/01_stage1_query2__chunk_002_compact2_max10_candidates_reviewed.json`

Source chunk:

- `var/real_runs/2026-03-21_phase_b_prompt_verification/chunks/01_stage1_query2/01_stage1_query2__chunk_002.md`

## Important Implementation Note

Two real blockers had to be resolved before this run was possible:

1. the extraction service needed an explicit prompt override path with prompt
   provenance and render-budget overrides;
2. the shared `llm_client` sync structured path had to stop leaking the
   private lifecycle monitor into provider kwargs.

Prompt-eval templates themselves were not reused directly on the live
extraction path, because they are experiment assets with a different input
contract. The operational verification therefore used a new extraction-
compatible compact prompt asset instead:

- `prompts/extraction/text_to_candidate_assertions_compact_v2.yaml`

## Result

Extraction produced `9` valid candidates:

- `oc:hold_command_role`: `5`
- `oc:operation_occurs_in_location`: `2`
- `oc:belongs_to_organization`: `1`
- `oc:express_concern`: `1`

Notably absent compared with the earlier Phase B chunk run:

- no JPOTF organizational-form / creation candidate

## Review Outcome

Bounded review accepted `8` of `9` candidates and rejected `1`, for an
`88.9%` acceptance rate.

Accepted:

1. all five `oc:hold_command_role` commander-table rows
2. both `oc:operation_occurs_in_location` operation headings
3. the NDU-review `oc:express_concern` candidate

Rejected:

1. the `4th PSYOP Group -> USSOCOM` `oc:belongs_to_organization` candidate,
   because this chunk still does not directly support the USSOCOM membership
   claim

## What This Means

This is a meaningful improvement over the earlier bounded chunk run:

1. the same chunk still keeps the useful commander/location/concern facts;
2. the JPOTF false positive is gone on the operational path, not just in
   prompt_eval;
3. the remaining miss is the same directly-grounded membership inference issue
   already known from Phase B;
4. the override path is now good enough to test candidate prompt assets on real
   chunks before promoting them to repo defaults.

## Decision

The next useful quality step is not more prompt-experiment plumbing.

It is:

1. run a second explicit real chunk through the same bounded compact-v2
   operational path; then
2. if the result is similarly strong, decide whether compact-v2 should replace
   the current live extraction prompt.

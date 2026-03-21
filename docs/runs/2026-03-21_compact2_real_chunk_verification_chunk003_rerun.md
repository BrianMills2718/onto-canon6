# Run Summary: 2026-03-21 compact2 Real Chunk Verification Chunk 003 Rerun

## Purpose

Verify whether the prompt-eval `compact@3` win on the new prose-heavy strict-
omit cases transfers to the live `extract-text` path on the same real chunk.

This rerun used the extraction-compatible compact prompt with a bumped prompt
reference:

- `onto_canon6.extraction.text_to_candidate_assertions_compact_v2@2`

## Runtime

Bounded operational lane:

- project: `onto-canon6-compact2-real-chunk-003-rerun`
- task: `budget_extraction`
- prompt template:
  `prompts/extraction/text_to_candidate_assertions_compact_v2.yaml`
- prompt ref: `onto_canon6.extraction.text_to_candidate_assertions_compact_v2@2`
- prompt render budget:
  - `max_candidates_per_call = 10`
  - `max_evidence_spans_per_candidate = 1`
- review db:
  `var/real_runs/2026-03-21_compact2_real_chunk_verification_chunk003_rerun/review_state_max10.sqlite3`
- reviewed candidate snapshot:
  `var/real_runs/2026-03-21_compact2_real_chunk_verification_chunk003_rerun/outputs/01_stage1_query2__chunk_003_compact2_max10_candidates_reviewed.json`

Source chunk:

- `var/real_runs/2026-03-21_phase_b_prompt_verification/chunks/01_stage1_query2/01_stage1_query2__chunk_003.md`

## Active-Call Observation

The active-call query again behaved correctly:

1. the run appeared as a live structured call with the new prompt ref;
2. `activity_state` remained truthfully `waiting`;
3. `process_alive` stayed `True`; and
4. the row disappeared after completion.

So the remaining problem was not liveness or orchestration.

## Result

The operational rerun did not inherit the prompt-eval win.

Extraction produced `6` structurally valid candidates:

- `oc:express_concern`: `5`
- `oc:limit_capability`: `1`

All `6` candidates were rejected in review.

Rejected pattern summary:

1. five `oc:express_concern` candidates still invented `USSOCOM` as the
   speaker for analytical narration;
2. one `oc:limit_capability` candidate still anchored the subject too loosely
   as `PSYOP`.

## What This Means

There is now an explicit transfer gap:

1. the prompt-eval `compact@3` prompt handles the new strict-omit cases;
2. the extraction-compatible compact prompt on the full operational chunk still
   over-extracts the same prose-heavy analytical material; and
3. the repo should not treat the prompt-eval win as sufficient evidence for
   live-prompt promotion.

The likely causes are now narrower:

1. the prompt-eval asset and the extraction-compatible asset are still not
   equivalent enough;
2. the longer multi-paragraph chunk context changes model behavior even when
   the local sentence-level benchmark cases are fixed; or
3. both factors matter.

## Decision

The next useful step is not another blind prompt tweak.

It is to compare the prompt-eval and operational compact prompt renderings and
determine why the benchmark improvement is not transferring to the real chunk
path.

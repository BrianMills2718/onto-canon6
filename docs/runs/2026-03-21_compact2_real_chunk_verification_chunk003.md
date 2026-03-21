# Run Summary: 2026-03-21 compact2 Real Chunk Verification Chunk 003

## Purpose

Run the same bounded compact-v2 operational override path on a second explicit
real Stage 1 chunk to test whether the earlier strong chunk-002 result
generalizes beyond commander/location/concrete concern text.

This run intentionally targeted a more analytical prose-heavy slice rather than
another mostly tabular or heading-driven chunk.

## Runtime

Bounded operational lane:

- project: `onto-canon6-compact2-real-chunk-003`
- task: `budget_extraction`
- prompt template:
  `prompts/extraction/text_to_candidate_assertions_compact_v2.yaml`
- prompt ref: `onto_canon6.extraction.text_to_candidate_assertions_compact_v2@1`
- prompt render budget:
  - `max_candidates_per_call = 10`
  - `max_evidence_spans_per_candidate = 1`
- review db:
  `var/real_runs/2026-03-21_compact2_real_chunk_verification_chunk003/review_state_max10.sqlite3`
- reviewed candidate snapshot:
  `var/real_runs/2026-03-21_compact2_real_chunk_verification_chunk003/outputs/01_stage1_query2__chunk_003_compact2_max10_candidates_reviewed.json`

Source chunk:

- `var/real_runs/2026-03-21_phase_b_prompt_verification/chunks/01_stage1_query2/01_stage1_query2__chunk_003.md`

## Active-Call Observation

During execution, `get_active_llm_calls(project=...)` behaved as intended:

1. the run appeared as one active structured call;
2. `activity_state` was truthfully `waiting`;
3. `process_alive` remained `True`; and
4. the row disappeared after the run completed.

This run did not expose a new liveness or orchestration problem. The failure
mode was semantic extraction quality.

## Result

Extraction produced `5` structurally valid candidates:

- `oc:express_concern`: `4`
- `oc:limit_capability`: `1`

All five candidates came from analytical prose rather than directly named
speaker/action statements.

Representative patterns:

1. analytical limitation sentences were turned into `oc:express_concern` with
   `speaker = USSOCOM` even though the chunk names no speaker;
2. the command-and-control paragraph was turned into `oc:limit_capability`
   anchored on `subject = PSYOP`, which is looser than the source text
   actually supports.

## Review Outcome

Bounded review rejected all `5` candidates for a `0%` acceptance rate.

Rejected patterns:

1. four `oc:express_concern` candidates were rejected because the analytical
   narration names no speaker, so the extraction must not invent `USSOCOM` as
   the speaker;
2. one `oc:limit_capability` candidate was rejected because the capability
   limitation mapping was too loose and over-anchored the subject as `PSYOP`.

## What This Means

This run does not invalidate the earlier chunk-002 win. It does show that the
current compact-v2 guidance does not yet generalize across prose-heavy
analytical sections.

The important outcome is now explicit:

1. the bounded operational override path works on a second real chunk;
2. the current failure is semantic, not structural;
3. the next extraction-quality step should target narrator-analysis and
   unnamed-speaker overreach, not more infrastructure work; and
4. compact-v2 should not replace the repo-default live extraction prompt yet.

## Decision

The next useful move is:

1. add one or more discriminative benchmark cases derived from this analytical
   prose failure mode;
2. tighten prompt guidance against inventing a speaker for report narration or
   commentary; and
3. rerun the focused prompt-eval lane before reconsidering live-prompt
   promotion.

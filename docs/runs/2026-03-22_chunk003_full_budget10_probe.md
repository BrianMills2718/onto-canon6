# Run Summary: 2026-03-22 chunk003 Full-Chunk Budget-10 Probe

## Purpose

Test whether the candidate-budget mismatch between prompt-eval `compact`
(`max_candidates_per_case = 1`) and the live extraction compact runs
(`max_candidates_per_call = 10`) is a major contributor to the chunk-003
transfer gap.

## Runtime

Focused fixture:

- fixture id: `psyop_eval_slice_v5_chunk003_full_focus`
- case:
  `psyop_017_full_chunk003_analytical_context_strict_omit`

One-off probe:

1. baseline kept its normal prompt_eval configuration;
2. compact was cloned into a temporary `compact_budget10` variant;
3. `compact_budget10` used the same prompt template as prompt-eval compact but
   with `max_candidates_per_case = 10`; and
4. the probe ran under:
   - project: `onto-canon6-chunk003-full-budget10`
   - execution id: `bb588143dd26`
   - model: `openrouter/deepseek/deepseek-chat`
   - task: `budget_extraction`

## Result

The budget change alone was enough to break the full-chunk compact benchmark
win.

Variant summary:

1. `baseline`
   - `mean_score = 0.25`
   - false positives on the full chunk
2. `compact_budget10`
   - `mean_score = 0.25`
   - false positives on the full chunk

`compact_budget10` example output produced three `oc:express_concern`
candidates from the same "effectiveness of PSYOP was often limited ..."
sentence, all attributed to `USSOCOM` with `subject = PSYOP`.

## What This Means

Candidate-budget parity is now a confirmed part of the live/prompt-eval gap.

This does not prove it is the only cause, but it does prove the gap is not
just:

1. chunk length;
2. prompt asset wording; or
3. a vague operational mystery.

The compact prompt-eval win on the full chunk depended in part on forcing the
model to keep the candidate set extremely small. When that cap moved to the
live extraction budget of `10`, the same full chunk again produced analytical-
prose false positives.

## Decision

The next useful parity step is to build an explicit operational-parity
prompt-eval lane for compact extraction:

1. extraction-compatible prompt asset;
2. extraction-style render path; and
3. live candidate/evidence budgets.

Without that, prompt-eval compact wins will keep overstating operational
readiness.

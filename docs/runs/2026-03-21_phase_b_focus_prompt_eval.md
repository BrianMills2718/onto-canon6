# Run Summary: 2026-03-21 Phase B Focus Prompt Eval

## Purpose

Test the real-chunk-derived failure modes cheaply before doing more live
Stage 1 reruns.

The new focused fixture isolates three Phase B problems exposed by
`01_stage1_query2__chunk_002`:

1. unsupported parent-organization inference from local context
2. named institutional concern that should remain extractable
3. JPOTF establishment text that should not become `use_organizational_form`

## Fixture

Temporary focused fixture generated from `tests/fixtures/psyop_eval_slice.json`:

- `var/evaluation_runs/psyop_eval_slice_phase_b_focus.json`
- fixture id: `psyop_eval_slice_v3_phase_b_focus`

Included case ids:

1. `psyop_006_context_only_membership_strict_omit`
2. `psyop_007_named_institutional_concern`
3. `psyop_008_jpotf_establishment_not_org_form`

## Runtime

- command: `run-extraction-prompt-experiment`
- selection task: `budget_extraction`
- comparison method: `bootstrap`
- replicates: `2`
- project: `onto-canon6-phase-b-focus-prompt-eval`
- output artifact:
  `var/evaluation_runs/psyop_eval_slice_phase_b_focus_prompt_eval.json`

## Result

Variant summaries:

- `compact = 0.44`, `exact_f1 = 0.2`, `count_alignment = 0.6`, `n_errors = 1`
- `hardened = 0.2833`
- `baseline = 0.275`
- `single_response_hardened = 0.2417`

No bootstrap comparison was significant.

## What This Means

1. The new focused fixture is doing useful work. It separates variants and
   catches regressions that the earlier Phase A fixture did not cover.
2. The previously best clean variant (`single_response_hardened`) does not
   generalize cleanly to these real-chunk-derived cases.
3. `compact` currently performs best on this slice, but it still had one
   provider-rate-limit failure, so it is not an automatic new default.

## Important Rejected Attempt

A prompt-only wording change was tested immediately before this focused run:

- generic warning against inferring relationships from surrounding context
- generic warning that “establishment of X” does not imply
  `use_organizational_form`

That wording was not kept. On the same real chunk it:

1. removed the acceptable named institutional concern candidate
2. failed to eliminate the unsupported `4th PSYOP Group -> USSOCOM` inference
3. failed to eliminate the JPOTF form misuse

So the right outcome was to keep the previous prompt wording, expand the
fixture, and let the benchmark drive the next change.

## Decision

The next prompt iteration should target the new Phase B focus cases
explicitly. It should not assume that the earlier Phase A winner remains the
best choice once real-chunk overbinding cases are included.

# Run Summary: 2026-03-21 v4 Prompt Eval compact@3

## Purpose

Test whether the chunk-003 prose-heavy failure modes can be turned into
discriminative benchmark cases and whether the compact prompt can be improved
against them without immediately mutating the live extraction default.

This run used the updated fixture and prompt only. It was a prompt-eval
boundary check, not a live extraction promotion decision.

## Runtime

Bounded prompt-eval lane:

- project: `onto-canon6-compact3-v4-sweep`
- task: `budget_extraction`
- fixture: `tests/fixtures/psyop_eval_slice.json`
- fixture id: `psyop_eval_slice_v4`
- comparison method: `none`
- runs per variant: `1`
- output artifact:
  `var/evaluation_runs/psyop_eval_slice_v4_prompt_eval_compact3_none.json`

New discriminative cases:

1. `psyop_009_report_narration_without_named_speaker_strict_omit`
2. `psyop_010_limit_capability_without_named_subject_strict_omit`

## Result

The updated compact prompt was the clear winner on the new fixture:

- `compact`: `mean_score = 0.7275`, `structural_usable_rate = 1.0`,
  `exact_f1 = 0.6`, `n_errors = 0`
- `baseline`: `mean_score = 0.2375`, `structural_usable_rate = 0.6`,
  `exact_f1 = 0.1`
- `hardened`: `mean_score = 0.325`, `n_errors = 1`
- `single_response_hardened`: `mean_score = 0.4344`, `n_errors = 2`

On the two new chunk-003-derived cases specifically:

1. `compact` returned `candidates: []` on both strict-omit cases and scored
   `1.0` on both;
2. `baseline` and `hardened` still over-extracted `limit_capability`;
3. `single_response_hardened` failed structurally on one of the new cases with
   a multiple-tool-call error.

## What This Means

This is a real prompt-eval improvement, not just a narrative claim. The new
benchmark cases are successfully discriminating the prose-heavy overreach
pattern, and the updated compact prompt now handles those benchmark cases
cleanly.

However, this run is still only a harness result. It does not prove that the
same gain transfers to the full operational extraction path on the longer
chunk.

## Decision

The next required step is operational transfer verification on the same real
chunk, using the updated extraction-compatible compact prompt with a bumped
prompt ref. Do not promote the compact prompt into the repo default based on
this prompt-eval win alone.

# Run Summary: 2026-03-22 chunk003 Full-Chunk Focus Prompt Eval

## Purpose

Test whether the prompt-eval lane can reproduce the exact full-chunk chunk-003
failure when the entire chunk is frozen into the benchmark fixture as one
strict-omit case.

This run answers a narrower question than the live observability reconstruction:

1. if the prompt-eval compact variant sees the full chunk, does it also
   over-extract the same analytical-prose candidates as the live extraction
   compact-v3 run; or
2. does the failure only appear on the operational extraction path.

## Runtime

Focused temporary fixture:

- source fixture: `tests/fixtures/psyop_eval_slice.json`
- focused fixture id: `psyop_eval_slice_v5_chunk003_full_focus`
- focused case:
  `psyop_017_full_chunk003_analytical_context_strict_omit`

Execution:

- command: `run-extraction-prompt-experiment`
- execution id: `2f83c34b1cb9`
- selection task: `budget_extraction`
- model: `openrouter/deepseek/deepseek-chat`
- runs per variant: `1`
- comparison method: `none`
- observability project: `onto-canon6-chunk003-full-v5`

## Result

Variant summary:

1. `compact`
   - `mean_score = 1.0`
   - `example_output = {"candidates": []}`
2. `baseline`
   - `mean_score = 0.25`
   - false positive:
     `oc:belongs_to_organization` from
     `USSOCOM’s PSYOP programs between 2001 and 2015 ...`
3. `hardened`
   - `mean_score = 0.25`
   - false positives:
     `oc:belongs_to_organization` and `oc:hold_command_role`
4. `single_response_hardened`
   - `mean_score = 0.25`
   - false positives:
     `oc:limit_capability` and `oc:express_concern`

Active-call verification:

1. the run appeared under `get_active_llm_calls(project="onto-canon6-chunk003-full-v5")`
   while live; and
2. the active row cleared after completion.

## What This Means

This result changes the diagnosis again, in a useful way.

The exact full chunk now exists in the benchmark lane, and the prompt-eval
`compact` variant handles it perfectly. But the live operational
`text_to_candidate_assertions_compact_v3@1` extraction run on the same chunk
still produced four analytical-prose false positives before review.

So the remaining gap is not well explained by chunk length alone.

The more likely mismatch is now:

1. prompt-eval compact asset/path versus operational extraction compact-v3
   asset/path;
2. prompt render differences between the prompt-eval and extraction surfaces;
3. or another operational extraction-path difference that is not simply "full
   chunk is longer".

## Decision

The next useful step is to diff the prompt-eval compact prompt asset and render
path against the operational extraction compact-v3 asset and render path.

Do not treat this as evidence that another generic chunk-length or context
experiment should come first.

# Run Summary: 2026-03-22 chunk003 Context-Focus Prompt Eval

## Purpose

Evaluate the surviving chunk-003 analytical-prose failure spans in a tighter
prompt-eval lane after freezing them into the benchmark fixture as explicit
sentence-only and short-local-context strict-omit cases.

This run exists to answer a narrower question than the live chunk transfer
reports:

1. is the `compact` prompt still semantically strong on the surviving
   chunk-003 failure spans when they are isolated into local evaluation cases;
2. do short local context windows reproduce the live failure; and
3. does the next step belong in prompt wording or in full-chunk operational
   behavior.

## Runtime

Focused temporary fixture:

- source fixture: `tests/fixtures/psyop_eval_slice.json`
- focused fixture id: `psyop_eval_slice_v5_chunk003_context_focus`
- focused cases:
  1. `psyop_011_hearts_and_minds_narration_strict_omit`
  2. `psyop_012_ethical_legal_questions_without_local_speaker_strict_omit`
  3. `psyop_013_local_context_report_narration_without_named_speaker_strict_omit`
  4. `psyop_014_local_context_hearts_and_minds_narration_strict_omit`
  5. `psyop_015_local_context_limit_capability_without_named_subject_strict_omit`
  6. `psyop_016_local_context_ethical_questions_with_following_scrutiny_strict_omit`

Execution:

- command: `run-extraction-prompt-experiment`
- execution id: `edf14d1233a3`
- selection task: `budget_extraction`
- model: `openrouter/deepseek/deepseek-chat`
- runs per variant: `1`
- comparison method: `none`
- observability project: `onto-canon6-chunk003-context-v5`

## Result

Variant summary:

1. `compact`
   - `mean_score = 0.85`
   - `successful_trials = 5/6`
   - `failure_counts = {multiple_tool_calls: 1}`
2. `hardened`
   - `mean_score = 0.3125`
   - `successful_trials = 6/6`
3. `single_response_hardened`
   - `mean_score = 0.3125`
   - `successful_trials = 6/6`
4. `baseline`
   - `mean_score = 0.2292`
   - `successful_trials = 6/6`

Observed case-level signal:

1. `compact` returned `candidates: []` and scored `1.0` on
   `psyop_011_hearts_and_minds_narration_strict_omit`.
2. `compact` also returned `candidates: []` and scored `1.0` on the
   local-context ethical/scrutiny case
   `psyop_016_local_context_ethical_questions_with_following_scrutiny_strict_omit`.
3. `baseline`, `hardened`, and `single_response_hardened` all still
   over-extracted false positives on at least some of the new sentence-only or
   local-context strict-omit cases.
4. The remaining `compact` failure was not a semantic false positive. It was a
   prompt-eval runtime failure on
   `psyop_012_ethical_legal_questions_without_local_speaker_strict_omit`
   categorized as `multiple_tool_calls`, even though the model content itself
   was semantically an empty-candidates response.

## What This Means

This run strengthens the full-chunk-context hypothesis.

The important shift is:

1. `compact` is now strong on the surviving chunk-003 failure spans when they
   are tested as sentence-only or short-local-context cases;
2. the remaining prompt-eval problem is primarily one reliability issue
   (`multiple_tool_calls`) rather than another semantic miss; and
3. the live chunk-003 transfer failure now looks more like a full-chunk
   operational/context problem than a local prompt wording problem.

## Decision

The next extraction-quality step should not be another broad prompt rewrite.

It should be:

1. compare compact behavior on the full chunk against these shorter local
   windows to identify what the longer context is reintroducing;
2. reconstruct the operational prompt/render path if possible; and
3. separately track the `multiple_tool_calls` compact prompt-eval failure as
   an experiment-reliability issue so it does not get confused with semantic
   extraction quality.

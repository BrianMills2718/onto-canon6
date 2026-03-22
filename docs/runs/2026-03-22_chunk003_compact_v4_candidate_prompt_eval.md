# Run Summary: 2026-03-22 chunk003 Compact-v4 Candidate Prompt Eval

## Purpose

Test the first compact prompt revision against the honest operational-parity
benchmark surface before spending more time on live extraction reruns.

The candidate prompt revision was intentionally narrow. It tightened:

1. invented or weakly-attributed institutional speakers;
2. analytical concern extraction from summary prose; and
3. loose `limit_capability` extraction from evaluative narration.

## Candidate Assets

1. live extraction candidate:
   `prompts/extraction/text_to_candidate_assertions_compact_v4.yaml`
2. prompt-eval operational mirror:
   `prompts/extraction/prompt_eval_text_to_candidate_assertions_compact_operational_parity_v2.yaml`

## Runtime

Full-chunk focused run:

1. fixture:
   `psyop_017_full_chunk003_analytical_context_strict_omit`
2. execution id: `e6073a26d7ec`
3. model: `openrouter/deepseek/deepseek-chat`
4. task: `budget_extraction`
5. `comparison_method = none`
6. `n_runs = 1`

Context-focus run:

1. cases:
   - `psyop_011_hearts_and_minds_narration_strict_omit`
   - `psyop_012_ethical_legal_questions_without_local_speaker_strict_omit`
   - `psyop_013_local_context_report_narration_without_named_speaker_strict_omit`
   - `psyop_014_local_context_hearts_and_minds_narration_strict_omit`
   - `psyop_015_local_context_limit_capability_without_named_subject_strict_omit`
   - `psyop_016_local_context_ethical_questions_with_following_scrutiny_strict_omit`
2. execution id: `27c1452fb1c8`
3. model: `openrouter/deepseek/deepseek-chat`
4. task: `budget_extraction`
5. `comparison_method = none`
6. `n_runs = 1`

## Result

Full-chunk focused run:

1. `compact`
   - `mean_score = 1.0`
   - example output: `{"candidates": []}`
2. `compact_operational_parity`
   - `mean_score = 1.0`
   - example output: `{"candidates": []}`

Context-focus run:

1. `compact`
   - `mean_score = 0.875`
2. `compact_operational_parity`
   - `mean_score = 0.875`

The full-chunk result is the key change. The earlier operational-parity lane
was reproducing chunk-003 false positives at `0.25`. The compact-v4 candidate
prompt moved that same parity lane to `1.0` on the frozen full chunk.

## What This Means

This is the first compact prompt candidate with evidence that the full-chunk
chunk-003 analytical-prose failure is probably fixable by prompt revision
rather than only by changing the evaluation harness.

It is not yet a promotion decision. The evidence is still bounded:

1. one full-chunk case;
2. one local chunk-003 case family; and
3. one replicate per variant.

## Non-Adopted Follow-Up

A second tighter rule aimed at the remaining oversight-language miss was tested
after these runs and then reverted. It overfit the local frozen cases and
reintroduced `limit_capability` false positives on the hearts-and-minds
spans.

That overfit attempt is not part of the current candidate prompt state.

## Decision

The next useful step is not another prompt-only iteration.

It is a real chunk-003 operational extraction rerun using the compact-v4
candidate prompt through the existing prompt-override workflow, followed by
normal review and transfer reporting.

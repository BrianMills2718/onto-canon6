# Run Summary: 2026-03-22 chunk003 Parity Fix Check

## Purpose

Test whether the remaining compact-v4 live-vs-prompt-eval gap was mostly
caused by obvious parity drift in the prompt-eval setup.

The two explicit fixes were:

1. make the compact operational-parity prompt asset match the live compact-v4
   system prompt exactly; and
2. make the full chunk-003 benchmark case use the real live chunk metadata
   (`source_kind`, `source_ref`, `source_label`) instead of benchmark
   placeholders.

## Runtime

Focused fixture:

1. case:
   `psyop_017_full_chunk003_analytical_context_strict_omit`
2. execution id: `61d29dbfc884`
3. model: `openrouter/deepseek/deepseek-chat`
4. task: `budget_extraction`
5. `comparison_method = none`
6. `n_runs = 1`

Live comparison target:

1. project: `onto-canon6-compact4-real-chunk-003`
2. prompt ref:
   `onto_canon6.extraction.text_to_candidate_assertions_compact_v4@1`
3. live call id in shared observability: `201213`

## Result

The parity fixes did remove the obvious setup drift, but they did not remove
the transfer gap.

Prompt-eval result after the fix:

1. `compact_operational_parity = 1.0`
2. example output: `{"candidates": []}`

Shared observability comparison:

1. system prompt:
   - live chars: `7024`
   - parity chars: `7024`
   - diff: none
2. user prompt:
   - live chars: `6779`
   - parity chars: `6860`
   - remaining differences:
     - prompt-eval still says `Extract candidate assertions from this source material.`
     - prompt-eval still prepends `Case input:`
     - prompt-eval still adds `Case id: psyop_017_full_chunk003_analytical_context_strict_omit`
3. responses:
   - live: three false-positive candidates
   - parity: `{"candidates":[]}`

## What This Means

Yes, there was an onto-canon6 prompt-eval parity problem worth fixing.

But after fixing the obvious parity drift, the compact-v4 live-vs-prompt-eval
gap still remained. So the repo should not treat this as proof that
`prompt_eval` itself is generically broken.

The remaining gap is now more specific:

1. the prompt-eval wrapper text may still be enough to shift the model; or
2. separate live vs prompt-eval provider invocations may have meaningful
   variance even at `temperature = 0`; or
3. some other live runtime-path difference still matters.

## Decision

The next useful fix is not another blind parity tweak.

The repo now needs either:

1. a deeper live-vs-parity call comparison; or
2. an extract-text-native replay evaluator if promotion decisions need
   certification-grade operational evidence.

# 2026-04-01 Live-Path Divergence Decision

## Scope

Closeout note for `docs/plans/0043_24h_live_path_divergence_block.md`.

This note answers the bounded question left by Plan `0042`:

**What is the dominant remaining blocker after the revised compact candidate
stays strong in prompt-eval but still fails on the live chunk-003 path under
the same selected model?**

## Canonical Artifacts

1. `docs/runs/2026-04-01_semantic_transfer_residual_decision.md`
2. `docs/runs/2026-04-01_chunk002_prompt_surface_parity_v5.json`
3. `docs/runs/2026-04-01_chunk003_prompt_surface_parity_v5.json`
4. `docs/runs/2026-04-01_chunk003_full_chunk_prompt_eval_report_v3.json`
5. `docs/runs/2026-04-01_chunk003_semantic_transfer_diff_compact5.json`
6. `docs/runs/2026-04-01_chunk003_transfer_report_compact5.json`
7. `docs/runs/2026-04-01_chunk003_live_path_calls.md`

## Current Fact Pattern

The revised candidate pair is:

1. live prompt:
   `onto_canon6.extraction.text_to_candidate_assertions_compact_v5@1`
2. prompt-eval parity prompt:
   `onto_canon6.extraction.prompt_eval_text_to_candidate_assertions_compact_operational_parity@3`

Prompt-eval on chunk `003`:

1. selected model:
   `gemini/gemini-2.5-flash`
2. predicted payload:
   `{"candidates":[]}`
3. score:
   `1.0`

Live chunk-003 run:

1. extraction task:
   `budget_extraction`
2. extraction model:
   `gemini/gemini-2.5-flash`
3. extractor response:
   `4` candidates
4. prompt-eval vs live body overlap:
   `0`
5. review path:
   - `judge_filter` labeled all four `supported`
   - each per-candidate `judging` call also labeled `supported`
   - transfer report therefore recorded `4` accepted candidates

## What This Rules Out

This block rules out two weaker explanations:

1. **Not model-family drift.**
   The prompt-eval and live runs used the same selected model.
2. **Not review-only divergence.**
   The extractor had already diverged before review, because the raw live
   output contained four candidates while prompt-eval returned zero.

## Dominant Blocker

The dominant blocker is now best described as:

**live extraction-path behavior under the live render contract**

with a secondary caveat:

**the review/judge path is amplifying the problem by accepting those
live-only candidates instead of rejecting them.**

This is narrower than the old "semantic prompt residual" label but broader than
"judge is wrong" alone:

1. the divergence begins at extraction output;
2. the live user-surface contract still differs from prompt-eval by the
   stable wrapper family already documented in `0041` and regenerated for
   `v5/@3`;
3. the review path then compounds the bad live output by labeling it
   supported.

## Decision

Plan `0043` is complete.

It narrows the active blocker to:

1. live extraction-path behavior under the current live prompt/render surface;
2. secondary review/judge permissiveness on the resulting candidates.

The next bounded step should therefore test prompt/render contract alignment
directly instead of making another generic semantic prompt revision.

## Next Bounded Step

The next block should:

1. hold the selected model fixed;
2. align the live and prompt-eval user-surface contract as directly as the repo
   allows;
3. rerun chunk `003` under that aligned surface; and
4. decide whether wrapper alignment materially narrows the live divergence
   before touching review/judge policy.

# 2026-04-01 Semantic Transfer Residual Decision

## Scope

Closeout note for
`docs/plans/0042_24h_semantic_transfer_residual_block.md`.

This note answers the bounded question owned by that block:

**Can one narrow compact-prompt revision suppress the named semantic transfer
residuals without losing chunk-002 positive-control behavior?**

## Canonical Artifacts

Incoming residual evidence:

1. `docs/runs/2026-04-01_full_chunk_transfer_parity_decision.md`
2. `docs/runs/2026-04-01_chunk002_live_vs_parity_diff.json`
3. `docs/runs/2026-04-01_chunk003_live_vs_parity_diff.json`

Body-level comparison artifacts:

1. `docs/runs/2026-04-01_chunk002_semantic_transfer_diff.json`
2. `docs/runs/2026-04-01_chunk003_semantic_transfer_diff.json`

Prompt revision artifacts:

1. `prompts/extraction/text_to_candidate_assertions_compact_v5.yaml`
2. `prompts/extraction/prompt_eval_text_to_candidate_assertions_compact_operational_parity_v3.yaml`
3. `docs/runs/2026-04-01_chunk002_full_chunk_prompt_eval_report_v3.json`
4. `docs/runs/2026-04-01_chunk003_full_chunk_prompt_eval_report_v3.json`

Live rerun artifacts:

1. `var/real_runs/2026-04-01_compact5_real_chunk_verification_chunk003/outputs/extract_manifest.json`
2. `docs/runs/2026-04-01_chunk003_transfer_report_compact5.json`
3. `docs/runs/2026-04-01_chunk003_semantic_transfer_diff_compact5.json`

## What Changed

The bounded prompt revision added only the instructions justified by the
frozen residuals:

1. `hold_command_role` now requires a named individual commander in the same
   span plus an explicit role-holding relation;
2. `limit_capability` now rejects possessive-topic anchoring unless the same
   clause explicitly states the named subject was limited; and
3. analytical wrap-up / conclusion discourse gets an even stronger default
   omission rule.

The revised candidate pair is:

1. live prompt:
   `onto_canon6.extraction.text_to_candidate_assertions_compact_v5@1`
2. prompt-eval parity prompt:
   `onto_canon6.extraction.prompt_eval_text_to_candidate_assertions_compact_operational_parity@3`

## Prompt-Eval Result

The revised parity lane remained stable on the two canonical chunks with the
same selected model in both runs:

1. selected model:
   `gemini/gemini-2.5-flash`
2. chunk `002`:
   - `mean_score = 0.9078`
   - `exact_f1 = 0.8889`
   - `count_alignment = 0.8`
   - `structural_usable_rate = 1.0`
3. chunk `003`:
   - `mean_score = 1.0`
   - `exact_f1 = 1.0`
   - `count_alignment = 1.0`
   - `structural_usable_rate = 1.0`
   - predicted `candidates: []`

So the bounded prompt revision did **not** break the chunk-002 positive control
inside prompt-eval and did preserve the strict-omit behavior on chunk `003`.

## Live Result

The live rerun on chunk `003` did **not** recover transfer.

Runtime:

1. selected task: `budget_extraction`
2. prompt:
   `onto_canon6.extraction.text_to_candidate_assertions_compact_v5@1`
3. project:
   `onto-canon6-compact5-real-chunk-003`

Observed result:

1. live extraction produced `4` candidates;
2. transfer report marked all `4` as `accepted`;
3. verdict was `positive`.

But the semantic comparison against the matching prompt-eval run says:

1. `shared = 0`
2. `only_live = 4`
3. `only_prompt_eval = 0`
4. `body_shared = 0`
5. `body_only_live = 4`
6. `body_only_prompt_eval = 0`

The live-only family is still exactly the kind of prose-heavy overreach this
block was meant to remove:

1. three `oc:limit_capability` candidates from analytical prose; and
2. one `oc:express_concern` candidate from oversight/scrutiny narration.

## Decision

Plan `0042` does **not** clear the extraction promotion gate.

The bounded prompt revision was useful evidence, but it did not solve the live
blocker:

1. prompt-eval remained strong on both canonical chunks;
2. the live chunk-003 path still diverged completely from the matching
   prompt-eval case;
3. the divergence happened under the same selected model;
4. therefore the next blocker is no longer "we need one more semantic prompt
   tweak."

The next blocker is **same-model live-path divergence**:

1. live extraction and prompt-eval still behave differently under the revised
   candidate pair;
2. the remaining question is whether that divergence comes mainly from:
   - the live-vs-parity user-surface contract,
   - extraction-service path behavior outside prompt-eval,
   - or review/judge acceptance on the live path.

## Next Bounded Step

The next block should:

1. freeze the same-model divergence contract around chunk `003`;
2. prove exactly which surface/path difference remains between prompt-eval and
   live extraction under the revised candidate pair; and
3. decide whether the next fix belongs in:
   - prompt/render contract alignment,
   - live extraction path behavior,
   - or review/judge policy.

# Extraction Transfer Certification Decision

Date: 2026-04-01
Plan: `0040_24h_extraction_transfer_certification_block.md`

## Decision

The current compact operational-parity candidate is **not promotable**.

This is now evidence-backed, not inferred:

1. chunk `003` still fails live transfer;
2. chunk `002` transfers positively on the live path; but
3. full-chunk prompt-eval parity and live extraction still diverge materially
   even on that positive-control chunk.

So the active blocker is no longer "we do not have a positive control." The
active blocker is: **the full-chunk prompt-eval/live certification contract is
still not tight enough to justify promotion.**

## Canonical Artifacts

Chunk `003` residual:

1. `docs/runs/2026-04-01_extraction_transfer_gap_localization.md`
2. `docs/runs/2026-04-01_chunk003_live_vs_parity_diff.json`
3. `docs/runs/2026-03-22_chunk003_full_operational_parity_prompt_eval.md`
4. `docs/runs/2026-03-22_compact4_real_chunk_verification_chunk003.md`

Chunk `002` positive-control certification:

1. `var/evaluation_runs/certification_fixtures/2026-04-01_chunk002_full_chunk_fixture.json`
2. `docs/runs/2026-04-01_chunk002_full_chunk_prompt_eval_report.json`
3. `docs/runs/2026-04-01_chunk002_transfer_report_compact4.json`
4. `docs/runs/2026-04-01_chunk002_live_vs_parity_diff.json`
5. `var/real_runs/2026-04-01_compact4_real_chunk_verification_chunk002/outputs/01_stage1_query2__chunk_002_compact4_max10_candidates_reviewed.json`

## Chunk `002` Result

Live compact-v4 transfer is strongly positive on the corrected worktree path:

1. total candidates: `10`
2. accepted: `10`
3. rejected: `0`
4. verdict: `positive`

Prompt-eval parity also looks strong at the aggregate score level:

1. variant: `compact_operational_parity`
2. model: `gemini/gemini-2.5-flash`
3. case mean score: `0.9078`
4. exact_f1: `0.8889`
5. count_alignment: `0.8`
6. structural_usable_rate: `1.0`

But the artifact diff still shows real disagreement:

1. prompt-eval candidates: `10`
2. live reviewed candidates: `10`
3. strict shared signatures: `1`
4. shared signatures ignoring `claim_text`: `7`
5. prompt-eval-only families:
   - `oc:operation_occurs_in_location` (`Operation Enduring Freedom`,
     `Operation Iraqi Freedom`)
   - `oc:belongs_to_organization` with `Army PSYOP unit`
6. live-only families:
   - `oc:limit_capability`
   - `oc:use_organizational_form`
   - `oc:belongs_to_organization` with `Army`

That means chunk `002` proves the live path can transfer positively, but it
does **not** prove prompt-eval parity is faithful enough for promotion.

## Chunk `003` Result

Chunk `003` remains the hard blocker:

1. prompt-eval parity candidates: `0`
2. live compact-v4 candidates: `3`
3. shared candidates: `0`
4. live-only predicates:
   - `oc:limit_capability`
   - `oc:express_concern`
   - `oc:hold_command_role`
5. live transfer verdict: `negative`

So the prose-heavy full-chunk stress case still fails on the live path even
after compact-v4 tightening.

## What Changed During Execution

Two execution findings materially affected certification and are now part of
the operating contract:

1. **Worktree execution must use `PYTHONPATH=src`.**
   Running `python -m onto_canon6` from the isolated worktree without
   `PYTHONPATH=src` imported the editable install from the main checkout
   instead of the worktree source tree. That produced invalid intermediate
   certification artifacts and had to be discarded.
2. **Prompt-eval report `execution_id` is not the diff helper's `run_id`.**
   The transfer helper reads `experiment_items.run_id`; the prompt-eval report
   only exposes `execution_id`. The correct per-variant run ids had to be
   recovered from `experiment_runs`.

## Conclusion

Plan `0040` resolved the old ambiguity:

1. the compact operational-parity lane is not blocked merely by missing
   positive-control evidence;
2. it is blocked by **full-chunk live/parity disagreement**; and
3. the next bounded extraction block should narrow that disagreement rather
   than start another broad prompt-rewrite campaign.

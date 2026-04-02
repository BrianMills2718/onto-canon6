# 2026-04-02 Post-Parity Semantic Recovery Decision

## Scope

Closeout note for
`docs/plans/0050_24h_post_parity_semantic_recovery_block.md`.

The bounded question was:

**Can one bounded semantic prompt revision improve strict-omit behavior on the
repaired chunk-003 analytical path without reopening prompt-path drift?**

## Canonical Artifacts

1. `docs/runs/2026-04-02_prompt_parity_repair_decision.md`
2. `docs/runs/2026-04-02_chunk003_post_repair_prompt_eval_report.json`
3. `docs/runs/2026-04-02_chunk003_post_parity_semantic_recovery_report.json`
4. `docs/runs/2026-04-02_chunk003_live_temp0_replayed_via_async.json`

## What Changed

The bounded semantic revision added two stronger omission rules to the live
compact prompt and the repaired operational-parity prompt:

1. do not split coordinated governance-process nouns into multiple
   `express_concern` speakers;
2. treat retrospective `was limited` / `was hampered` / `reducing impact`
   language as analytical wrap-up unless the same span states a concrete
   limiting event.

## Result

The change altered the chunk-003 family, but it did **not** improve the score
or restore strict-omit behavior.

Post-change compact operational-parity case diagnostics stayed flat:

1. `mean_score = 0.25`
2. `exact_f1 = 0.0`
3. `count_alignment = 0.0`
4. `structural_usable_rate = 1.0`

The family changed like this:

1. the old repaired baseline produced `5` candidates:
   - `3` `oc:limit_capability`
   - `2` `oc:express_concern`
2. the new attempt produced `4` candidates:
   - `2` `oc:limit_capability`
   - `1` `oc:express_concern`
   - `1` `oc:belongs_to_organization`
3. that is not an improvement:
   - the `hearts and minds` limitation disappeared, but
   - a late `belongs_to_organization` candidate appeared, and
   - the case still failed the strict-omit target entirely.

## Decision

Plan `0050` is complete as a **failed bounded semantic attempt**.

That failure is still useful:

1. prompt-surface parity remains intact;
2. the semantic blocker is now narrower than "analytical prose in general";
3. the next miss family is the interaction between analytical section context
   and late quantitative/retrospective summary sentences.

## Next Bounded Step

The next block should focus on analytical-section suppression more directly:

1. section-heading and retrospective-summary context should strengthen omission,
   not loosen it;
2. late quantitative summary sentences in the same analytical chunk should not
   spill into `belongs_to_organization` when the block is otherwise strict-omit.

That next block is tracked as
`docs/plans/0051_24h_analytical_section_suppression_block.md`.

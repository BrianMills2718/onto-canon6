# Decision Note: 2026-04-02 abstract-result and citation suppression follow-up

## Scope

This note closes Plan `0053` against the repaired chunk-003 strict-omit case:

- case: `psyop_017_full_chunk003_analytical_context_strict_omit`
- active prompt under test:
  `onto_canon6.extraction.prompt_eval_text_to_candidate_assertions_compact_operational_parity@3`
- compared observability executions:
  - `bb8be70d4504` (`0052` after)
  - `81cffac9c8df` (`0053` after)

## What Changed

Plan `0053` added stronger hard-negative prompt rules:

1. abstract evaluative `limit_capability` fillers such as `effectiveness`,
   `impact`, and `credibility` should be omitted;
2. retrospective subject labels such as `"hearts and minds" campaigns` and
   `PSYOP messages` should not support `limit_capability` alone;
3. citation titles, bibliography references, and passive `was reported` prose
   should not become `send_report`.

## Verified Result

The hard-negative prompt revision did **not** shrink the compact-operational-
parity family. It widened again.

Observed compact-operational-parity outputs:

1. `0052` after (`bb8be70d4504`, call `293582`):
   - 5 candidates
   - predicates:
     - `oc:limit_capability`
     - `oc:limit_capability`
     - `oc:limit_capability`
     - `oc:express_concern`
     - `oc:send_report`
2. `0053` after (`81cffac9c8df`, call `293780`):
   - 6 candidates
   - predicates:
     - `oc:limit_capability`
     - `oc:limit_capability`
     - `oc:limit_capability`
     - `oc:create_organizational_unit`
     - `oc:express_concern`
     - `oc:send_report`

Aggregate score stayed flat again:

1. `mean_score = 0.25`
2. `exact_f1 = 0.0`
3. `count_alignment = 0.0`
4. `structural_usable_rate = 1.0`

## Interpretation

The model did not honor the intended hard negatives in the way this block
needed:

1. the three abstract-result `limit_capability` candidates all survived;
2. the governance-reaction `express_concern` candidate survived;
3. the citation/report `send_report` candidate survived; and
4. a new `create_organizational_unit` candidate appeared from the sentence
   about `USSOCOM` and the `JPOTF model`.

At this point the active uncertainty is no longer just prompt wording. The
full chunk itself contains explicit factual sentences that overlap with several
already-modeled local strict-omit failure families:

1. `JPOTF` / establishment narration (`psyop_008`)
2. `hearts and minds` narration (`psyop_011`, `psyop_014`)
3. ethical/legal questions with following scrutiny (`psyop_012`, `psyop_016`)
4. report/citation narration (`psyop_009`, `psyop_013`)
5. loose capability narration (`psyop_010`, `psyop_015`)

So the next blocker may be benchmark-contract mismatch:

1. either chunk `017` is still a truthful zero-candidate full-chunk control;
2. or the strict-omit full-chunk contract is now misaligned with the broad
   extraction goal and should be revised explicitly rather than fought with
   more prompt churn.

## Decision

Plan `0053` is complete as a failed prompt-only suppression attempt.

The next bounded block should audit the chunk-003 benchmark contract before
more prompt revisions:

1. validate whether `psyop_017_full_chunk003_analytical_context_strict_omit`
   should remain strict omit under the current extraction goal;
2. decide whether the right fix is:
   - keep strict omit and change the extractor,
   - split the full chunk into only the local strict-omit controls,
   - or allow accepted alternatives / a narrowed extraction goal.

# Decision Note: 2026-04-02 predicate-locality gate follow-up

## Scope

This note closes Plan `0052` against the repaired chunk-003 strict-omit case:

- case: `psyop_017_full_chunk003_analytical_context_strict_omit`
- active prompt under test:
  `onto_canon6.extraction.prompt_eval_text_to_candidate_assertions_compact_operational_parity@3`
- compared observability executions:
  - `90003aea587c` (`0051` before)
  - `b349a4681e04` (`0051` after)
  - `bb8be70d4504` (`0052` after)

## What Changed

Plan `0052` tightened predicate-local eligibility:

1. `express_concern` now requires an explicit concern/speech-act style signal
   rather than mere governance reaction language;
2. `limit_capability` now says abstract result nouns and broad retrospective
   labels are not enough by themselves;
3. the repair stayed bounded to the live compact and parity-v3 prompt surfaces.

## Verified Result

The compact-operational-parity spillover family **shrunk**, but it did not
clear the core semantic blocker.

Observed compact-operational-parity outputs:

1. `0051` before (`90003aea587c`, call `293120`):
   - 4 candidates
   - predicates:
     - `oc:limit_capability`
     - `oc:limit_capability`
     - `oc:express_concern`
     - `oc:belongs_to_organization`
2. `0051` after (`b349a4681e04`, call `293168`):
   - 6 candidates
   - predicates:
     - `oc:limit_capability`
     - `oc:limit_capability`
     - `oc:limit_capability`
     - `oc:express_concern`
     - `oc:express_concern`
     - `oc:belongs_to_organization`
3. `0052` after (`bb8be70d4504`, call `293582`):
   - 5 candidates
   - predicates:
     - `oc:limit_capability`
     - `oc:limit_capability`
     - `oc:limit_capability`
     - `oc:express_concern`
     - `oc:send_report`

Aggregate score stayed flat:

1. `mean_score = 0.25`
2. `exact_f1 = 0.0`
3. `count_alignment = 0.0`
4. `structural_usable_rate = 1.0`

## Interpretation

Plan `0052` did one useful thing:

1. it collapsed the split concern-speaker family back into one
   `express_concern` candidate; and
2. it removed the direct staffing-summary `belongs_to_organization` spillover.

But the remaining blocker is still explicit:

1. the abstract-result `limit_capability` family survived unchanged
   (`effectiveness`, `credibility`, `impact`);
2. the governance-reaction `express_concern` family still survived in combined
   form; and
3. the staffing-summary residue shifted into a new citation/report-style
   `oc:send_report` spillover around `SOCOM Fact Book 2013`.

So the next blocker is narrower than `0052`:

1. hard-negative suppression for abstract evaluative `limit_capability`
   fillers and retrospective campaign/message labels;
2. stronger governance-reaction suppression for `express_concern`; and
3. explicit citation/report suppression so `was reported` or bibliography-style
   references do not become `send_report`.

## Runtime Caveat

The first `0052` rerun under `LLM_CLIENT_TIMEOUT_POLICY=ban` stalled after the
baseline variant. The successful decision artifact came from rerunning the same
bounded command with `LLM_CLIENT_TIMEOUT_POLICY=allow`. That is a harness
uncertainty, not a semantic classification uncertainty.

## Decision

Plan `0052` is complete and useful, but not sufficient.

It narrowed the family from `6` to `5` and replaced the old staffing-summary
spillover with a clearer citation/report spillover. The next bounded block
should therefore target hard-negative abstract-result suppression plus
citation/report suppression.

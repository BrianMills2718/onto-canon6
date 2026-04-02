# Decision Note: 2026-04-02 analytical-section suppression follow-up

## Scope

This note closes Plan `0051` against the repaired chunk-003 strict-omit case:

- case: `psyop_017_full_chunk003_analytical_context_strict_omit`
- active prompt under test:
  `onto_canon6.extraction.prompt_eval_text_to_candidate_assertions_compact_operational_parity@3`
- compared artifacts:
  - `docs/runs/2026-04-02_chunk003_post_parity_semantic_recovery_report.json`
  - `docs/runs/2026-04-02_chunk003_analytical_section_suppression_report.json`

## What Changed

Plan `0051` added two bounded suppression rules to both the live compact prompt
and the repaired prompt-eval parity prompt:

1. analytical section headings such as `Effectiveness and Limitations`,
   `Ethical and Legal Considerations`, `Personnel and Resource Trends`, and
   `Conclusion and Opinion` strengthen the omission default;
2. aggregate staffing/resource summaries such as `total strength`,
   `a substantial proportion`, and `personnel were dedicated to` should not
   become `belongs_to_organization` without a concrete member unit.

## Verified Result

The bounded suppression change did **not** shrink the compact operational-parity
spillover family.

Observed compact-operational-parity outputs from observability:

1. before (`execution_id=90003aea587c`, call `293120`):
   - 4 candidates
   - predicates:
     - `oc:limit_capability`
     - `oc:limit_capability`
     - `oc:express_concern`
     - `oc:belongs_to_organization`
2. after (`execution_id=b349a4681e04`, call `293168`):
   - 6 candidates
   - predicates:
     - `oc:limit_capability`
     - `oc:limit_capability`
     - `oc:limit_capability`
     - `oc:express_concern`
     - `oc:express_concern`
     - `oc:belongs_to_organization`

Aggregate score also stayed flat:

1. `mean_score = 0.25`
2. `exact_f1 = 0.0`
3. `count_alignment = 0.0`
4. `structural_usable_rate = 1.0`

## Interpretation

The repair failed in the exact way that matters:

1. the late staffing-summary `belongs_to_organization` spillover survived;
2. the governance-process concern family split into two speakers
   (`Congressional oversight`, `public scrutiny`) instead of shrinking; and
3. a new retrospective `limit_capability` candidate was introduced from the
   `"hearts and minds" campaigns ... undermined credibility` sentence.

So the active blocker is no longer "analytical sections need another generic
omission rule." The narrower blocker is:

1. `express_concern` is still being inferred from governance/review reactions
   without an explicit concern act; and
2. `limit_capability` is still accepting abstract result nouns such as
   `effectiveness`, `impact`, and `credibility` as if they were concrete
   operational capabilities.

## Decision

Plan `0051` is closed as a failed bounded suppression attempt.

The next bounded block is predicate-local, not section-local:

1. tighten `express_concern` to explicit concern/speech-act evidence only;
2. tighten `limit_capability` to concrete operational capabilities instead of
   abstract result nouns;
3. keep the existing staffing-summary omission rule, but do not spend another
   block on section-heading language alone.

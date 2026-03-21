# Run Summary: 2026-03-21 Phase B Focus Prompt Eval v2

## Purpose

Rerun the focused v3 extraction slice after two changes:

1. add case-level diagnostics with representative successful outputs; and
2. tighten the `compact` prompt against the exact real-chunk failure shapes.

The goal was to see whether one prompt variant could:

1. omit context-only membership inference;
2. keep the named institutional concern case alive; and
3. omit bare JPOTF-establishment over-extraction.

## Runtime

- command:
  `env LLM_CLIENT_PROJECT=onto-canon6-v3-focus-diag2 LLM_CLIENT_TIMEOUT_POLICY=ban ./.venv/bin/python -m onto_canon6 run-extraction-prompt-experiment --fixture-path /tmp/onto-canon6-v3-focus.json --n-runs 1 --comparison-method none --selection-task budget_extraction --output json`
- selection task: `budget_extraction`
- comparison method: `none`
- replicates: `1`
- project: `onto-canon6-v3-focus-diag2`
- output artifact:
  `var/evaluation_runs/psyop_eval_slice_phase_b_focus_prompt_eval_v2.json`
- execution id: `7912ca822b3e`

## Result

Variant summaries:

- `compact = 0.7833`, `exact_f1 = 0.6667`, `count_alignment = 1.0`, `structural_usable_rate = 1.0`
- `single_response_hardened = 0.2833`
- `hardened = 0.2`
- `baseline = 0.1833`

Focused case behavior:

1. `psyop_006_context_only_membership_strict_omit`
   - `compact` now returns `candidates: []`
   - other variants still over-extract `oc:belongs_to_organization`
2. `psyop_007_named_institutional_concern`
   - `compact` now returns one valid `oc:express_concern` candidate
   - `baseline` still over-splits into two concern/dissatisfaction candidates
   - `hardened` and `single_response_hardened` still miss exact-match fidelity
3. `psyop_008_jpotf_establishment_not_org_form`
   - `compact` now returns `candidates: []`
   - other variants still force `oc:create_organizational_unit`

## What Changed

The winning prompt change was narrow:

1. descriptive appositives are treated as descriptions of the same entity, not
   evidence of organizational membership;
2. bare establishment mentions are treated as background context, not creation
   events, unless the source states a reviewable creation fact; and
3. named institutions/reviews are allowed to act as `express_concern` speakers.

## Operational Notes

The active-call query remained useful during the run:

1. all live prompt-experiment calls showed up under
   `get_active_llm_calls(project="onto-canon6-v3-focus-diag2")`;
2. opaque structured calls stayed honestly in `waiting`; and
3. the query returned `[]` after the run finished.

## Decision

`compact@2` is now the leading prompt-eval candidate for the v3 focus slice.

The next useful step is not another blind rewrite. It is:

1. rerun the broader v3 benchmark with `compact@2`; then
2. if it still holds up, rerun bounded real-chunk verification before deciding
   whether to promote any of this wording into the main live extraction prompt.

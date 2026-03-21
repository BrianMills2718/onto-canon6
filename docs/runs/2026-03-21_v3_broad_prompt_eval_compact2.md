# Run Summary: 2026-03-21 Broad v3 Prompt Eval with compact@2

## Purpose

Test whether the focused `compact@2` win still holds on the broader v3
benchmark before touching the main live extraction prompt or another real
document chunk.

## Runtime

- command:
  `env LLM_CLIENT_PROJECT=onto-canon6-v3-broad-compact2 LLM_CLIENT_TIMEOUT_POLICY=ban ./.venv/bin/python -m onto_canon6 run-extraction-prompt-experiment --n-runs 2 --comparison-method bootstrap --selection-task budget_extraction --output json`
- selection task: `budget_extraction`
- comparison method: `bootstrap`
- replicates: `2`
- project: `onto-canon6-v3-broad-compact2`
- output artifact:
  `var/evaluation_runs/psyop_eval_slice_v3_prompt_eval_compact2_broad.json`
- execution id: `56f02c6e9369`

## Result

Variant summaries:

- `compact = 0.6571`, `exact_f1 = 0.5`, `count_alignment = 0.8214`, `structural_usable_rate = 1.0`, `n_errors = 2`
- `single_response_hardened = 0.4628`
- `hardened = 0.38`
- `baseline = 0.2928`

Bootstrap comparisons:

- `compact` vs `baseline`: significant improvement, CI `[0.1451, 0.5738]`
- `hardened` vs `baseline`: not significant
- `single_response_hardened` vs `baseline`: not significant

## Compact@2 Case Behavior

Strong cases:

1. `psyop_003_alias_expansion_parenthetical_only` -> exact match
2. `psyop_005_unattributed_opinion_strict_omit` -> exact match on the
   successful trial
3. `psyop_006_context_only_membership_strict_omit` -> exact match on the
   successful trial
4. `psyop_008_jpotf_establishment_not_org_form` -> exact match across both
   trials

Still weak:

1. `psyop_001_designation_change` -> under-extraction / fidelity miss
2. `psyop_002_concerns_about_truth_based_shift` -> only partial semantic fit
3. `psyop_004_subordinate_unit_belongs_to_organization` -> improved but not
   yet exact
4. `psyop_007_named_institutional_concern` -> structurally good, still not
   exact-match faithful

## Remaining Structural Failures

`compact@2` still had two structural errors across the broader run:

1. one `multiple_tool_calls` failure on `psyop_006`
2. one `schema_validation_error` on `psyop_005`, where the model tried to emit
   an `unknown` speaker with `raw: null` before also producing a successful
   empty-candidate trial

These are no longer the dominant story, but they are still the main reason the
lane does not yet satisfy the plan’s “repeatably with no structural trial
failures” acceptance bar.

## Operational Note

`get_active_llm_calls(project="onto-canon6-v3-broad-compact2")` briefly showed
live opaque structured calls in `waiting` during the run and returned `[]`
after the process settled, so the active-call visibility remained useful and
truthful on the broader sweep too.

## Decision

`compact@2` is now the strongest extraction prompt-eval lane on the broader v3
benchmark, and the improvement over baseline is statistically meaningful.

The next useful step is a bounded real-chunk verification path that can use
this non-default prompt without mutating the repo-wide live extraction default.

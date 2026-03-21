# Expanded Fixture Prompt Eval Baseline

Status: completed
Date: 2026-03-21

## Purpose

Record the first real prompt-eval baseline over the expanded
`psyop_eval_slice_v2` fixture and the immediate follow-up guardrail rerun.

This run exists to answer one narrow question: after expanding the fixture
with the new alias / subordinate-unit / unattributed-opinion cases, what is
the actual prompt-variant baseline before more extraction work?

## Commands

Initial expanded baseline:

```bash
env LLM_CLIENT_PROJECT=onto-canon6-extraction-expanded-fixture \
  LLM_CLIENT_TIMEOUT_POLICY=ban \
  ./.venv/bin/python -m onto_canon6 run-extraction-prompt-experiment \
  --case-limit 5 \
  --n-runs 2 \
  --comparison-method bootstrap \
  --selection-task budget_extraction \
  --output json
```

Guardrail rerun after propagating semantic guardrails and explicit `kind`
requirements across the prompt-eval variants:

```bash
env LLM_CLIENT_PROJECT=onto-canon6-extraction-expanded-fixture-guardrails-v2 \
  LLM_CLIENT_TIMEOUT_POLICY=ban \
  ./.venv/bin/python -m onto_canon6 run-extraction-prompt-experiment \
  --case-limit 5 \
  --n-runs 2 \
  --comparison-method bootstrap \
  --selection-task budget_extraction \
  --output json
```

Saved outputs:

- `var/evaluation_runs/expanded_fixture_prompt_eval_2026-03-21.json`
- `var/evaluation_runs/expanded_fixture_prompt_eval_2026-03-21_guardrails_v2.json`

## Results

### Initial Expanded Baseline

| Variant | Successful Trials | Mean Score | exact_f1 | structural_usable_rate | count_alignment |
|---|---:|---:|---:|---:|---:|
| `baseline` | 10/10 | 0.235 | 0.0 | 0.75 | 0.475 |
| `compact` | 10/10 | 0.27 | 0.0 | 0.90 | 0.45 |
| `hardened` | 10/10 | 0.22 | 0.0 | 0.70 | 0.45 |
| `single_response_hardened` | 10/10 | 0.26 | 0.0 | 0.90 | 0.35 |

Bootstrap comparisons: no significant winner.

### Guardrail + `kind` Rerun

| Variant | Successful Trials | Mean Score | exact_f1 | structural_usable_rate | count_alignment |
|---|---:|---:|---:|---:|---:|
| `baseline` | 10/10 | 0.2475 | 0.0 | 0.85 | 0.35 |
| `compact` | 10/10 | 0.20 | 0.0 | 0.50 | 0.75 |
| `hardened` | 10/10 | 0.17 | 0.0 | 0.50 | 0.45 |
| `single_response_hardened` | 10/10 | 0.24 | 0.0 | 0.70 | 0.65 |

Bootstrap comparisons: still no significant winner.

## Dry Review Notes

The run detail exposed the following semantic patterns on the expanded
fixture:

1. `psyop_001_designation_change`
   - variants still tend to under-extract this case
   - candidate-budget pressure matters because the reference case expects
     multiple supported candidates, not just one designation-change event

2. `psyop_002_concerns_about_truth_based_shift`
   - variants still collapse or mis-bind the concern/capability structure
   - one candidate is often emitted where the fixture expects two

3. `psyop_003_alias_expansion_parenthetical_only`
   - the false-positive pattern is now measured directly by the fixture
   - prompt guardrails are necessary but not yet enough to separate variants
     clearly at the score level

4. `psyop_004_subordinate_unit_belongs_to_organization`
   - this case shows the benchmark-contract ambiguity clearly
   - semantically correct outputs can still miss exact match because the
     extraction boundary derives local `ent:auto:*` IDs while the fixture is
     written in reviewer-style preferred IDs

5. `psyop_005_unattributed_opinion_strict_omit`
   - the fixture now measures the strict-profile omit behavior directly
   - explicit `kind` guidance fixed one real model-output schema failure on
     the bounded rerun path

## Conclusions

1. The expanded prompt-eval harness is operationally usable.
   - no trial-level structural failure counts remained after the prompt
     contract tightened around `kind`

2. Prompt-only guardrails are not yet enough to produce a clear best
   variant.
   - the rankings moved
   - the comparisons remained non-significant

3. `exact_f1 = 0.0` across both expanded sweeps is now a real planning
   signal, not just a bad run.
   - the exact-match lane is still partly confounded by extraction-boundary
     normalization vs reviewer-style fixture payloads

4. The next useful work is not more infrastructure.
   - decide whether the fixture exact-match lane should use
     extraction-boundary normalized payloads
   - decide whether at least one variant should get a larger candidate budget
     for multi-fact cases like designation change
   - continue semantic prompt iteration only after those choices are explicit

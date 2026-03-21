# Expanded Fixture Prompt Eval Baseline

Status: completed
Date: 2026-03-21

## Purpose

Record the first real prompt-eval baselines over the expanded
`psyop_eval_slice_v2` fixture, the immediate follow-up guardrail rerun, and
the contract-aligned rerun that changed Phase A exact scoring to use
extraction-boundary semantics.

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

Contract-aligned rerun after making Phase A exact scoring ignore reviewer-only
entity IDs and downstream value-normalization shape:

```bash
env LLM_CLIENT_PROJECT=onto-canon6-extraction-expanded-fixture-contract-aligned \
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
- `var/evaluation_runs/expanded_fixture_prompt_eval_2026-03-21_contract_aligned.json`

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

### Contract-Aligned Rerun

| Variant | Successful Trials | Mean Score | exact_f1 | structural_usable_rate | count_alignment |
|---|---:|---:|---:|---:|---:|
| `baseline` | 10/10 | 0.34 | 0.20 | 0.70 | 0.35 |
| `compact` | 9/10 | 0.3639 | 0.2222 | 0.5556 | 0.8056 |
| `hardened` | 10/10 | 0.335 | 0.20 | 0.60 | 0.55 |
| `single_response_hardened` | 10/10 | 0.345 | 0.20 | 0.60 | 0.65 |

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
   - this case was the clearest benchmark-contract ambiguity in the first
     two sweeps
   - the contract-aligned rerun removed that reviewer-ID confound, which is
     why `exact_f1` finally moved off zero

5. `psyop_005_unattributed_opinion_strict_omit`
   - the fixture now measures the strict-profile omit behavior directly
   - explicit `kind` guidance fixed one real model-output schema failure on
     the bounded rerun path

6. Compact-variant residual structural failure
   - the contract-aligned rerun still had one `compact` trial fail on
     `psyop_001_designation_change`
   - the live error was an unnamed entity filler (`subject` with neither
     `name` nor `entity_id`)
   - this is now a real remaining extractor issue, not a scoring-contract
     artifact

## Conclusions

1. The expanded prompt-eval harness is operationally usable.
   - no trial-level structural failure counts remained after the prompt
     contract tightened around `kind`

2. The original `exact_f1 = 0.0` result was partly a scoring-contract
   problem.
   - once Phase A exact scoring moved to extraction-boundary semantics,
     every successful variant achieved `exact_f1 > 0.0`
   - Phase A is now measuring extractor behavior instead of reviewer-only
     IDs and downstream value normalization shape

3. Prompt-only guardrails are still not enough to produce a clear best
   variant.
   - the rankings moved again after the contract alignment
   - the comparisons remained non-significant

4. The next useful work is not more evaluation infrastructure.
   - keep the D0 contract split: prompt-eval exact scoring at the extraction
     boundary, stricter reviewer-style fidelity later
   - do dry review on the remaining semantic misses, especially
     designation-change under-extraction and concern/capability binding
   - fix the surviving unnamed-entity structural failure before trusting
     `compact` as a default candidate

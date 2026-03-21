# Phase A Prompt-Eval Dry Review

Status: completed
Date: 2026-03-21

## Purpose

Persist the case-by-case dry review and failure taxonomy for the expanded
Phase A prompt-eval campaign after the scoring contract was fixed and the
targeted `single_response_hardened` pass was measured.

This note exists so the next extraction-quality step starts from the real
remaining failure patterns, not from the earlier benchmark-contract noise.

## Scope

Primary interpretation point:

- `var/evaluation_runs/expanded_fixture_prompt_eval_2026-03-21_zero_omit_aligned.json`
- `var/evaluation_runs/expanded_fixture_prompt_eval_2026-03-21_single_response_v2.json`

Winning clean variant:

- `single_response_hardened` from the `single_response_v2` run

## Case Review

### `psyop_001_designation_change`

Observed pattern:

- hardest case in the fixture
- one sentence supports multiple linked facts
- most variants still emit only one `oc:replace_designation` candidate
- the winning `single_response_v2` replicate split correctly once
  (`oc:replace_designation` + `oc:hold_command_role`) but still failed to do
  so consistently

Dominant failure taxonomy:

- `multi_fact_under_extraction`
- `unnamed_entity_filler`
- `schema_validation_error`

Implication:

- the prompt needs to keep treating one sentence as potentially supporting
  more than one candidate
- this is now the main remaining semantic difficulty, not a scoring issue

### `psyop_002_concerns_about_truth_based_shift`

Observed pattern:

- the text often collapses into one concern-style candidate
- the capability-effect candidate is still omitted too often
- one run emitted `oc:criticize_change`, which is too generic for the
  supported concern/effect pair

Dominant failure taxonomy:

- `wrong_predicate`
- `multi_fact_under_extraction`

Implication:

- the current best variant still needs better separation between
  `oc:express_concern` and `oc:limit_capability`

### `psyop_003_alias_expansion_parenthetical_only`

Observed pattern:

- strict omit now scores correctly when the extractor returns `[]`
- the winning `single_response_v2` variant omitted correctly in both
  observed runs
- baseline and hardened variants still hallucinated relationship-like
  candidates in earlier runs

Dominant failure taxonomy:

- `alias_self_reference`

Implication:

- this case is now mostly a control case
- the main lesson was scoring: zero-candidate truth must score as success

### `psyop_004_subordinate_unit_belongs_to_organization`

Observed pattern:

- predicate choice is now stable across variants
- the remaining problem is structural: some runs left `entity_type` blank or
  returned a non-exact evidence span
- the `single_response_v2` variant improved this by requiring `entity_type`
  on named entities

Dominant failure taxonomy:

- `missing_entity_type`
- `bad_evidence_span`

Implication:

- predicate semantics are largely solved here
- evidence precision remains a narrower follow-up issue

### `psyop_005_unattributed_opinion_strict_omit`

Observed pattern:

- strict omit behavior is now measured honestly
- the winning `single_response_v2` variant omitted correctly in both runs
- baseline continued to produce false-positive concern candidates with vague
  or invented speakers

Dominant failure taxonomy:

- `unattributed_opinion`

Implication:

- the strict-profile omit rule is now working in the winning variant
- this is no longer the main blocker for Phase A

## Cross-Case Conclusions

1. The earlier `exact_f1 = 0.0` problem was partly a scoring bug.
   Zero-candidate strict-omit cases must count as exact agreement when both
   expected and observed are empty.

2. `single_response_hardened` is the best clean variant from this iteration.
   It improved:
   - multi-fact splitting somewhat
   - typed entity filler quality
   - strict-omit behavior

3. The remaining high-value failure classes are now:
   - `multi_fact_under_extraction`
   - `wrong_predicate` on concern/effect collapse
   - `bad_evidence_span`

4. `compact` can still score high, but its historical structural volatility
   makes it a worse promotion candidate than `single_response_hardened`.

## Next Recommended Move

Move to Phase B real-document verification using the current
`single_response_v2` winning state, not the later discarded evidence-span
experiment.

The main live extraction prompt now mirrors that winning guidance, so Phase B
does not need a separate prompt-selector mechanism first.

The next verification question is no longer “which Phase A prompt is best?”
It is “does the winning clean variant actually improve acceptance and review
quality on the real Stage 1 corpus?”

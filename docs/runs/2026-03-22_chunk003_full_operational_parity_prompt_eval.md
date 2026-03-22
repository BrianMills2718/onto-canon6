# Run Summary: 2026-03-22 chunk003 Full-Chunk Operational-Parity Prompt-Eval

## Purpose

Build and prove an explicit compact prompt-eval lane that matches the live
compact extraction semantics and candidate budget closely enough to serve as an
operational-readiness proxy.

## Runtime

Focused fixture:

- fixture id: `psyop_eval_slice_v5`
- case:
  `psyop_017_full_chunk003_analytical_context_strict_omit`

Configured variant:

1. name: `compact_operational_parity`
2. prompt template:
   `prompts/extraction/prompt_eval_text_to_candidate_assertions_compact_operational_parity.yaml`
3. prompt ref:
   `onto_canon6.extraction.prompt_eval_text_to_candidate_assertions_compact_operational_parity@1`
4. budget:
   - `max_candidates_per_case = 10`
   - `max_evidence_spans_per_candidate = 1`

Run configuration:

1. project: `onto-canon6`
2. execution id: `280130358336`
3. model: `openrouter/deepseek/deepseek-chat`
4. task: `budget_extraction`
5. `comparison_method = none`
6. `n_runs = 1`

## Result

Variant summary:

1. `baseline`
   - `mean_score = 0.25`
2. `hardened`
   - `mean_score = 0.25`
3. `compact`
   - `mean_score = 1.0`
   - example output: `{"candidates": []}`
4. `compact_operational_parity`
   - `mean_score = 0.25`
   - reproduced the live analytical-prose false positives
5. `single_response_hardened`
   - `mean_score = 0.25`

Representative `compact_operational_parity` false positives:

1. `oc:express_concern`
   - speaker: `USSOCOM`
   - topic: `cultural misunderstandings, insufficient coordination...`
2. `oc:express_concern`
   - speaker: `USSOCOM`
   - topic: `the limitations observed... underscore the need for ongoing reform...`
3. `oc:express_concern`
   - speaker: `Congressional oversight`
   - topic: `new ethical and legal questions...`
4. `oc:limit_capability`
   - subject: `PSYOP`
   - capability: `effectiveness`

## What This Means

The operational-parity lane succeeded at its intended job.

It did not make compact extraction better. It made the benchmark more honest.

The old prompt-eval `compact` lane is still useful for narrow small-budget
prompt comparisons, but it is not a reliable proxy for the live compact
extraction path on this chunk. The new `compact_operational_parity` lane is.

## Decision

Future compact prompt changes should be judged against
`compact_operational_parity` whenever the question is operational transfer.

If a compact prompt only wins on the old budget-1 `compact` lane and still
fails on `compact_operational_parity`, it should not be treated as ready for
live extraction promotion.

# 2026-04-01 Extraction Transfer Gap Localization

## Scope

Phase 2 evidence note for
`docs/plans/0040_24h_extraction_transfer_certification_block.md`.

This note localizes the current live-vs-parity gap for the compact
operational-parity extraction candidate without yet adding a new helper.

## Frozen Surfaces

Live extraction candidate:

1. task: `budget_extraction`
2. prompt template:
   `prompts/extraction/text_to_candidate_assertions_compact_v4.yaml`
3. prompt ref:
   `onto_canon6.extraction.text_to_candidate_assertions_compact_v4@1`

Prompt-eval operational-parity surface:

1. variant: `compact_operational_parity`
2. prompt template:
   `prompts/extraction/prompt_eval_text_to_candidate_assertions_compact_operational_parity_v2.yaml`
3. prompt ref:
   `onto_canon6.extraction.prompt_eval_text_to_candidate_assertions_compact_operational_parity@2`
4. model in the canonical prompt-eval run:
   `openrouter/deepseek/deepseek-chat`

## Chunk 003: Exact Gap

### Prompt-eval parity full-chunk result

Source:

1. `docs/runs/2026-03-22_chunk003_compact_v4_candidate_prompt_eval.md`
2. observability run:
   `experiment_runs.run_id = 0f664c022900`

Item:

1. `psyop_017_full_chunk003_analytical_context_strict_omit`

Predicted payload:

```json
{"candidates":[]}
```

Score:

1. `score = 1.0`
2. `exact_f1 = 1.0`
3. `structural_usable_rate = 1.0`
4. `count_alignment = 1.0`

### Live chunk-003 result

Source:

1. `docs/runs/2026-03-22_compact4_real_chunk_verification_chunk003.md`
2. transfer report:
   `var/evaluation_runs/chunk_transfer_reports/2026-03-22_chunk_003_transfer_report_compact4.json`
3. reviewed candidate snapshot:
   `var/real_runs/2026-03-22_compact4_real_chunk_verification_chunk003/outputs/01_stage1_query2__chunk_003_compact4_max10_candidates.json`

Result:

1. `3` structurally valid candidates
2. `0` accepted
3. `3` rejected
4. verdict `negative`

Rejected candidate families:

1. `oc:limit_capability`
   - invented concrete subject `USSOCOM’s PSYOP programs`
   - converted analytical narration into a concrete limitation fact
2. `oc:express_concern`
   - treated narration as an attributed concern event
3. `oc:hold_command_role`
   - turned generic mention of capable `USSOCOM commanders` into a concrete
     role-holding fact

### Interpretation

For chunk `003`, the gap is exact and no longer vague:

1. the current prompt-eval operational-parity lane says the candidate should
   emit `candidates: []`;
2. the current live extraction candidate still emits three rejected candidates;
3. therefore the transfer gap is not an aggregate-scoring illusion.

## Chunk 002: Positive-Control Coverage Gap

The repo still has a positive live transfer artifact for the older compact-v2
gate:

1. `docs/runs/2026-03-21_chunk_transfer_gate_compact2.md`
2. `var/evaluation_runs/chunk_transfer_reports/2026-03-21_chunk_002_transfer_report.json`
   - `8/9` accepted
   - verdict `positive`

But the repo does **not** yet have an equivalent current-generation artifact
pair for the compact-v4 candidate:

1. no frozen prompt-eval parity chunk-002 artifact for the compact-v4 lane;
2. no frozen live compact-v4 chunk-002 transfer artifact.

That means chunk `002` still lacks the exact current-generation live-vs-parity
comparison needed for certification-grade positive-control evidence.

## Decision

Phase 2 has localized the chunk-003 gap precisely enough to proceed.

What remains open before certification can close:

1. a reproducible comparison path is still needed so the live-vs-parity gap is
   not reconstructed manually each time;
2. chunk `002` still needs current-generation positive-control coverage for the
   same compact-v4 candidate lane.

That is why the next step is the minimum certification helper, not another
prompt rewrite.

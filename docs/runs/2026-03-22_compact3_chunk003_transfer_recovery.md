# Run Summary: 2026-03-22 compact3 Chunk 003 Transfer Recovery

## Purpose

Recover the missing chunk-level transfer artifact for the already reviewed
`compact3` real-chunk verification slice on Stage 1 chunk 003, then record
whether the prompt-eval `compact@3` win transferred to the live extraction
workflow.

This note is an artifact-recovery pass, not a new extraction run.

## Runtime

Recovered from the existing reviewed store:

- review db:
  `var/real_runs/2026-03-21_compact3_real_chunk_verification_chunk003/review_state_max10.sqlite3`
- source ref:
  `var/real_runs/2026-03-21_phase_b_prompt_verification/chunks/01_stage1_query2/01_stage1_query2__chunk_003.md`
- recovered transfer report:
  `var/evaluation_runs/chunk_transfer_reports/2026-03-21_chunk_003_transfer_report_compact3.json`

Recovery command:

```bash
cd ~/projects/onto-canon6
./.venv/bin/python -m onto_canon6 export-chunk-transfer-report \
  --review-db-path var/real_runs/2026-03-21_compact3_real_chunk_verification_chunk003/review_state_max10.sqlite3 \
  --source-ref var/real_runs/2026-03-21_phase_b_prompt_verification/chunks/01_stage1_query2/01_stage1_query2__chunk_003.md \
  --prompt-template prompts/extraction/text_to_candidate_assertions_compact_v3.yaml \
  --prompt-ref onto_canon6.extraction.text_to_candidate_assertions_compact_v3@1 \
  --selection-task budget_extraction \
  --output json
```

## Prompt-Provenance Note

The current review store does not persist extraction prompt metadata.

So the prompt annotation on the recovered transfer report is an explicit
operator annotation inferred from the dated campaign chronology:

1. `docs/runs/2026-03-21_v4_prompt_eval_compact3_none.md` established the
   `compact3` prompt-eval win;
2. the only tracked `compact3` extraction asset in the repo is
   `prompts/extraction/text_to_candidate_assertions_compact_v3.yaml`; and
3. the reviewed store being summarized here is the matching
   `2026-03-21_compact3_real_chunk_verification_chunk003` lane.

That inference is strong enough for campaign accounting, but it is not the
same thing as prompt provenance being persisted directly in the review DB.

## Result

The recovered transfer report shows a negative live transfer result:

1. total candidates: `4`
2. accepted: `0`
3. rejected: `4`
4. acceptance rate: `0.0`
5. verdict: `negative`

Predicate mix:

1. `oc:express_concern`: `3`
2. `oc:limit_capability`: `1`

## What This Means

`compact3` improved the bounded benchmark lane, but it still did not transfer
to the live chunk-003 extraction path.

Relative to the earlier `compact2@2` chunk-003 rerun:

1. the live candidate count dropped from `6` to `4`; but
2. the acceptance rate stayed at `0.0`; so
3. the real failure is still transfer, not merely overproduction volume.

## Decision

The next useful extraction-quality step is not another blind prompt rewrite.

It is to compare the operational compact2 and compact3 chunk-003 behaviors
directly:

1. compare persisted candidate payloads and rejection patterns on the same
   source chunk;
2. determine what the prompt-eval strict-omit win is not controlling in the
   full chunk context; and
3. only then decide whether the next fix belongs in prompt wording, prompt
   render shape, chunking, or model/task choice.

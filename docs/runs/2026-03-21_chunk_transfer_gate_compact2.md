# Chunk Transfer Gate for Compact-v2

Date: 2026-03-21
Prompt family: `text_to_candidate_assertions_compact_v2`
Prompt ref: `onto_canon6.extraction.text_to_candidate_assertions_compact_v2@2`
Selection task: `budget_extraction`

## Purpose

Prove the new chunk-level transfer gate on one positive and one negative real
PSYOP Stage 1 chunk so live prompt promotion can cite transfer evidence rather
than sentence-level prompt-eval alone.

## Commands

Positive transfer chunk:

```bash
cd ~/projects/onto-canon6
./.venv/bin/python -m onto_canon6 export-chunk-transfer-report \
  --review-db-path var/real_runs/2026-03-21_compact2_real_chunk_verification/review_state_max10.sqlite3 \
  --source-ref text://phase-b/2026-03-21/01_stage1_query2/chunk_002_compact2_max10 \
  --prompt-template prompts/extraction/text_to_candidate_assertions_compact_v2.yaml \
  --prompt-ref onto_canon6.extraction.text_to_candidate_assertions_compact_v2@2 \
  --selection-task budget_extraction \
  --output json
```

Negative transfer chunk:

```bash
cd ~/projects/onto-canon6
./.venv/bin/python -m onto_canon6 export-chunk-transfer-report \
  --review-db-path var/real_runs/2026-03-21_compact2_real_chunk_verification_chunk003_rerun/review_state_max10.sqlite3 \
  --source-ref var/real_runs/2026-03-21_phase_b_prompt_verification/chunks/01_stage1_query2/01_stage1_query2__chunk_003.md \
  --prompt-template prompts/extraction/text_to_candidate_assertions_compact_v2.yaml \
  --prompt-ref onto_canon6.extraction.text_to_candidate_assertions_compact_v2@2 \
  --selection-task budget_extraction \
  --output json
```

Saved artifacts:

1. `var/evaluation_runs/chunk_transfer_reports/2026-03-21_chunk_002_transfer_report.json`
2. `var/evaluation_runs/chunk_transfer_reports/2026-03-21_chunk_003_transfer_report.json`

## Results

Positive transfer chunk:

1. source ref: `text://phase-b/2026-03-21/01_stage1_query2/chunk_002_compact2_max10`
2. total candidates: `9`
3. accepted: `8`
4. rejected: `1`
5. acceptance rate: `0.8889`
6. verdict: `positive`

Negative transfer chunk:

1. source ref:
   `var/real_runs/2026-03-21_phase_b_prompt_verification/chunks/01_stage1_query2/01_stage1_query2__chunk_003.md`
2. total candidates: `6`
3. accepted: `0`
4. rejected: `6`
5. acceptance rate: `0.0`
6. verdict: `negative`

## Interpretation

This is the intended use of the gate:

1. sentence-level prompt-eval alone was not enough to justify live prompt
   promotion;
2. the same compact family now has explicit evidence of one strong transfer
   chunk and one failed transfer chunk; and
3. the next extraction-quality step should target the chunk-003 prose-heavy
   narrator/speaker and loose capability-anchoring failures specifically,
   rather than assuming the sentence-level win is sufficient.

## Note on Source Refs

The transfer command keys on the exact `source_ref` stored in the review DB,
not on a guessed chunk file path. Current real runs use two conventions:

1. `chunk_002` used a `text://...` source ref on the operational extraction
   run;
2. `chunk_003` rerun used the chunk file path string as the source ref.

So when a report says `no candidates found for source_ref=...`, first verify
the persisted source ref rather than assuming the chunk path string matches the
stored review provenance.

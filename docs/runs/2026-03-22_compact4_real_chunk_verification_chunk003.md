# Run Summary: 2026-03-22 compact4 Real Chunk Verification Chunk 003

## Purpose

Test whether the compact-v4 candidate prompt transfers from the bounded
prompt-eval checkpoints to the real `extract-text` workflow on the same
analytical chunk-003 slice.

## Runtime

Bounded operational lane:

1. project: `onto-canon6-compact4-real-chunk-003`
2. task: `budget_extraction`
3. prompt template:
   `prompts/extraction/text_to_candidate_assertions_compact_v4.yaml`
4. prompt ref:
   `onto_canon6.extraction.text_to_candidate_assertions_compact_v4@1`
5. prompt render budget:
   - `max_candidates_per_call = 10`
   - `max_evidence_spans_per_candidate = 1`
6. review db:
   `var/real_runs/2026-03-22_compact4_real_chunk_verification_chunk003/review_state_max10.sqlite3`
7. reviewed candidate snapshot:
   `var/real_runs/2026-03-22_compact4_real_chunk_verification_chunk003/outputs/01_stage1_query2__chunk_003_compact4_max10_candidates.json`
8. transfer report:
   `var/evaluation_runs/chunk_transfer_reports/2026-03-22_chunk_003_transfer_report_compact4.json`

Source chunk:

- `var/real_runs/2026-03-21_phase_b_prompt_verification/chunks/01_stage1_query2/01_stage1_query2__chunk_003.md`

## Result

The live compact-v4 rerun improved the candidate volume but not the transfer
verdict.

Extraction produced `3` structurally valid candidates:

1. `oc:limit_capability`: `1`
2. `oc:express_concern`: `1`
3. `oc:hold_command_role`: `1`

Review rejected all `3` candidates.

Rejected pattern summary:

1. `oc:limit_capability`
   - still turned the analytical effectiveness sentence into a concrete
     limitation event by inventing `USSOCOM’s PSYOP programs` as the subject
2. `oc:express_concern`
   - still treated the oversight/scrutiny sentence as an explicitly
     attributed concern event
3. `oc:hold_command_role`
   - still converted conclusion narration about generic `USSOCOM commanders`
     into a concrete command-role holding fact

Transfer summary:

1. `accepted_candidates = 0`
2. `rejected_candidates = 3`
3. `acceptance_rate = 0.0`
4. verdict `negative`

## What This Means

The compact-v4 candidate prompt is directionally better on the live chunk but
not yet good enough.

Compared with earlier live chunk-003 runs:

1. compact-v2 rerun: `6` rejected candidates
2. compact-v3 rerun: `4` rejected candidates
3. compact-v4 rerun: `3` rejected candidates

So the prompt revision did reduce over-extraction. But it did not actually
solve live transfer.

## Decision

The next useful step is to compare this live compact-v4 output directly
against the `compact_operational_parity` full-chunk prompt-eval win and
determine why prompt-eval still overstates live readiness on this slice.

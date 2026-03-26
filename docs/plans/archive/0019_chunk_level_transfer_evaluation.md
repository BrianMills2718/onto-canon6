# Chunk-Level Transfer Evaluation

Status: complete

Last updated: 2026-03-21
Workstream: post-bootstrap extraction R&D (ADR-0022, ADR-0023)

## Purpose

Add an explicit chunk-level evaluation slice so prompt-eval wins can be tested
for transfer to the real multi-paragraph extraction workflow before live prompt
promotion.

This plan exists because the `v4` prompt-eval compact win did not transfer to
the full operational chunk-003 rerun.

## Outcome

This plan is now complete.

`onto-canon6` now has a stable chunk-level transfer artifact:

```bash
python -m onto_canon6 export-chunk-transfer-report ...
```

The command summarizes one reviewed `source_ref` from one review store and
records:

1. the review DB used for the slice;
2. the reviewed chunk `source_ref`;
3. optional prompt template/ref and selection-task annotations;
4. compact per-candidate review outcomes; and
5. a config-backed transfer verdict: `positive`, `mixed`, or `negative`.

The proof slice for the current compact prompt family is now explicit:

1. positive transfer chunk:
   - `chunk_002`
   - `8/9` accepted
   - verdict `positive`
   - artifact:
     `var/evaluation_runs/chunk_transfer_reports/2026-03-21_chunk_002_transfer_report.json`
2. negative transfer chunk:
   - `chunk_003` rerun
   - `0/6` accepted
   - verdict `negative`
   - artifact:
     `var/evaluation_runs/chunk_transfer_reports/2026-03-21_chunk_003_transfer_report.json`

The dated operator note for that proof is:

1. `docs/runs/2026-03-21_chunk_transfer_gate_compact2.md`

## Acceptance Criteria

This plan is complete only when all of the following are true:

1. `onto-canon6` has a repeatable chunk-level evaluation artifact or command
   that can score or summarize transfer on explicit multi-paragraph chunks;
2. that slice can distinguish at least:
   - sentence-level prompt-eval win with chunk-level transfer success, and
   - sentence-level prompt-eval win with chunk-level transfer failure;
3. the current compact prompt family has been checked through that slice on at
   least one positive and one negative chunk;
4. live prompt promotion decisions can cite chunk-level transfer evidence
   instead of relying on sentence-level prompt-eval alone.

This plan fails if:

1. the new slice is just another dated run note without a stable contract;
2. it collapses back into unstructured analyst review with no explicit transfer
   artifact; or
3. it silently weakens chunk-grounding or reviewability in order to make
   transfer scores look better.

## Current Inputs

The plan starts from existing evidence:

1. sentence-level prompt-eval fixture `v4` can isolate narrator-analysis and
   loose capability anchoring failures;
2. compact recovers those `v4` cases inside prompt-eval;
3. the same prompt family still fails on the full chunk-003 operational rerun;
4. rendered prompt comparison suggests the bigger transfer difference is the
   multi-paragraph user payload, not only residual system-prompt wording.

## Implemented Slice

The completed slice is intentionally narrow:

1. `ChunkTransferReportService` summarizes one reviewed `source_ref`;
2. `export-chunk-transfer-report` exposes that summary on the operational CLI;
3. config-backed transfer thresholds now live under `evaluation.chunk_transfer`;
4. prompt promotion can now cite both sentence-level prompt-eval evidence and
   chunk-level transfer evidence, rather than relying on sentence-level wins
   alone.

## Known Risks and Uncertainties

1. chunk-level transfer may still depend heavily on document composition and
   not generalize from only two chunks.
2. review-based transfer checks may need a lightweight normalization layer to
   stay comparable across reruns.
3. there is a risk of rebuilding another benchmark surface that duplicates the
   live review workflow too closely instead of summarizing transfer clearly.

## Non-Goals

1. replacing the current sentence-level prompt-eval lane;
2. promoting a live extraction prompt automatically just because one plan is
   complete;
3. introducing whole-document synthesis or looser grounding semantics.

## Next Use

Use this slice as the live-prompt promotion gate:

1. if a prompt variant wins sentence-level prompt-eval but fails chunk-level
   transfer, do not promote it;
2. if a prompt variant wins both, the next question becomes broader corpus
   verification or default-prompt promotion;
3. current compact evidence is still mixed overall because `chunk_002`
   transfers positively while `chunk_003` remains negative.

# Chunk-Level Transfer Evaluation

Status: active

Last updated: 2026-03-21
Workstream: post-bootstrap extraction R&D (ADR-0022, ADR-0023)

## Purpose

Add an explicit chunk-level evaluation slice so prompt-eval wins can be tested
for transfer to the real multi-paragraph extraction workflow before live prompt
promotion.

This plan exists because the `v4` prompt-eval compact win did not transfer to
the full operational chunk-003 rerun.

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

## Build Order

1. define the smallest chunk-level evaluation contract:
   - input chunk
   - prompt asset/ref
   - output artifact
   - review or scoring summary
   - transfer verdict
2. choose one positive transfer chunk and one negative transfer chunk from the
   current PSYOP Stage 1 work;
3. implement the smallest stable artifact or CLI/report surface that records
   chunk-level transfer results;
4. prove the slice on the current compact prompt family;
5. only then decide whether live prompt promotion is justified or whether the
   next work belongs in prompt design or extraction architecture.

## Known Risks and Uncertainties

1. chunk-level transfer may still depend heavily on document composition and
   not generalize from only two chunks.
2. review-based transfer checks may need a lightweight normalization layer to
   stay comparable across reruns.
3. there is a risk of rebuilding another benchmark surface that duplicates the
   live review workflow too closely instead of summarizing transfer clearly.

## Non-Goals

1. replacing the current sentence-level prompt-eval lane;
2. promoting a live extraction prompt during this plan by default;
3. introducing whole-document synthesis or looser grounding semantics.

# 24h Live Chunk-003 Semantic Residual Block

Status: active
Phase status:
- Phase 1 pending
- Phase 2 pending
- Phase 3 pending
- Phase 4 pending
- Phase 5 pending

Last updated: 2026-04-02
Workstream: post-review-alignment live semantic hardening for chunk `003`

## Purpose

Plan `0058` fixed the live review contract and reduced the chunk-003
false-positive family, but it did not clear the transfer gate. The remaining
accepted chunk-003 candidates are now a smaller extraction-boundary residual,
not a review-contract bug.

This block exists to harden the live compact prompt against that residual while
preserving the chunk-002 positive control and the corrected benchmark fixture.

## Scope

This block intentionally covers only:

1. the remaining accepted chunk-003 analytical-prose `oc:limit_capability`
   family;
2. the remaining personnel-allocation-to-membership over-extraction family;
3. targeted benchmark or diagnostic coverage needed to keep that family visible;
4. one fresh live rerun on chunk `002` and chunk `003`.

Out of scope:

1. reopening the live review contract from Plan `0058`;
2. new broad benchmark redesign;
3. new transfer chunks; and
4. wider queryability or consumer-integration work.

## Pre-Made Decisions

1. Work stays in the isolated `codex/onto-canon6-integration-planning`
   worktree.
2. The live review contract from Plan `0058` stays frozen.
3. Chunk `002` remains the positive control and chunk `003` remains the
   prose-heavy stress case.
4. Prompt work is limited to the compact extraction prompt family:
   - `prompts/extraction/text_to_candidate_assertions_compact_v5.yaml`
   - `prompts/extraction/prompt_eval_text_to_candidate_assertions_compact_operational_parity_v3.yaml`
5. The prompt ref may be bumped if the prompt changes materially.
6. The fresh rerun root for this block is:
   - `var/real_runs/2026-04-02_live_chunk003_semantic_residual/`
7. One new local regression case may be added only if needed to lock the
   personnel-allocation-not-membership family.

## Gate

This block succeeds only if:

1. the remaining chunk-003 accepted family is reduced materially;
2. chunk `002` remains a positive live transfer control;
3. chunk `003` no longer reports a misleading positive result on the same
   residual family; and
4. the repo states clearly whether the lane is now transfer-clear or still
   blocked on a smaller explicit residual.

## Phase Order

### Phase 1: Freeze The Residual Contract

#### Tasks

1. close Plan `0058` truthfully;
2. freeze the exact remaining chunk-003 accepted candidates as the incoming
   contract;
3. decide whether one new local regression case is required for the
   personnel-allocation family.

#### Success criteria

1. the residual family is explicit and bounded;
2. the new block is active in the authority docs.

### Phase 2: Add The Smallest Missing Regression Coverage

#### Tasks

1. add or update the minimum benchmark/diagnostic coverage needed for the
   remaining residual;
2. keep the change local to the current failure family;
3. verify the new coverage before prompt edits.

#### Success criteria

1. the remaining live residual is visible in local verification;
2. the coverage change is bounded.

### Phase 3: Harden The Compact Prompt Family

#### Tasks

1. revise the compact extraction prompt family to avoid:
   - abstract evaluative `limit_capability` narration; and
   - personnel-allocation-to-membership over-extraction;
2. keep the changes mirrored across the live/prompt-eval compact surfaces;
3. update any prompt-surface parity tests as needed.

#### Success criteria

1. the new prompt family verifies cleanly on targeted tests;
2. the changes are bounded to the named residual family.

### Phase 4: Rerun Chunk 002 And Chunk 003

#### Tasks

1. rerun chunk `002` with the revised compact prompt;
2. rerun chunk `003` with the revised compact prompt;
3. export both reviewed transfer reports;
4. compare the new chunk-003 accepted set against the frozen residual
   contract.

#### Success criteria

1. fresh chunk rerun artifacts exist;
2. chunk `002` remains positive;
3. chunk `003` no longer reproduces the same residual family unchanged.

### Phase 5: Classify Promotion Posture And Close Out

#### Tasks

1. write the decision note;
2. update `CLAUDE.md`, `TODO.md`, `HANDOFF.md`, `docs/STATUS.md`,
   `docs/plans/CLAUDE.md`, `docs/plans/0014_extraction_quality_baseline.md`,
   and `KNOWLEDGE.md`;
3. mark the block complete only when the worktree is clean.

#### Success criteria

1. the lane status is explicit and decision-grade;
2. the next blocker is named precisely if the lane is still not promotable;
3. the worktree is clean.

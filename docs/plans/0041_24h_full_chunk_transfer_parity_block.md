# 24h Full-Chunk Transfer Parity Block

Status: active
Phase status:
- Phase 1 completed
- Phase 2 pending
- Phase 3 pending
- Phase 4 pending
- Phase 5 pending

Last updated: 2026-04-01
Workstream: narrow the residual full-chunk prompt-eval/live disagreement left
after Plan `0040`

## Purpose

Plan `0040` answered the promotion question honestly:

1. chunk `002` now proves the live compact-v4 path can transfer positively;
2. chunk `003` still fails live transfer; and
3. prompt-eval parity still disagrees with live extraction on both named
   chunks at the full-chunk level.

This block exists to answer the next narrower question:

**Is the remaining extraction blocker mainly a prompt/render contract problem,
or is it still a genuine semantic extraction mismatch between prompt-eval and
the live extract-text path?**

## Scope

This block intentionally covers only:

1. the compact-v4 live extraction prompt;
2. the `compact_operational_parity@2` prompt-eval lane;
3. the two canonical chunks already frozen by Plan `0040`;
4. prompt/render-path observability needed to compare those surfaces
   honestly; and
5. a decision on the dominant residual blocker family.

Out of scope:

1. broad new prompt rewrites before the parity residual is localized;
2. model-family swaps;
3. new ontology/runtime features;
4. any DIGIMON or entity-resolution work.

## Pre-Made Decisions

1. Work stays in the isolated `codex/onto-canon6-integration-planning`
   worktree.
2. All Python execution in this block must use the worktree source tree via
   `PYTHONPATH=src`.
3. The canonical residual evidence is:
   - `docs/runs/2026-04-01_extraction_transfer_certification.md`
   - `docs/runs/2026-04-01_chunk002_live_vs_parity_diff.json`
   - `docs/runs/2026-04-01_chunk003_live_vs_parity_diff.json`
   - `docs/runs/2026-04-01_chunk002_transfer_report_compact4.json`
4. The next block must prefer observability and replay aids over prompt edits.
5. If a helper needs a run id from prompt-eval observability, it must use the
   real `experiment_runs.run_id`, not the report `execution_id`.

## Gate

This block succeeds only if:

1. the repo can point to exact full-chunk live vs prompt-eval render/input
   differences for chunks `002` and `003`;
2. those differences are classified into one of:
   - prompt/render contract difference,
   - semantic extraction difference,
   - or remaining review/judge/runtime-path difference;
3. one minimal aid exists to reproduce that classification from the repo; and
4. the closeout note states which blocker family is dominant and what the next
   bounded extraction step must be.

## Phase Order

### Phase 1: Freeze The Residual Contract

#### Tasks

1. restate the `0040` result as the incoming contract for this block;
2. enumerate the exact residual mismatches on chunk `002` and chunk `003`;
3. record the known execution caveats (`PYTHONPATH=src`, run-id mapping).

#### Success criteria

1. no future work in this block depends on vague "parity is off" language;
2. the named residuals are concrete enough to verify against artifacts.

Progress note:

1. the incoming decision note is now frozen in:
   `docs/runs/2026-04-01_extraction_transfer_certification.md`
2. the canonical residual artifacts are now explicit:
   - `docs/runs/2026-04-01_chunk002_live_vs_parity_diff.json`
   - `docs/runs/2026-04-01_chunk003_live_vs_parity_diff.json`
   - `docs/runs/2026-04-01_chunk002_transfer_report_compact4.json`
3. the two execution caveats are now part of the contract, not conversational
   knowledge:
   - worktree runtime commands must use `PYTHONPATH=src`
   - prompt-eval `execution_id` is not the same as observability `run_id`

### Phase 2: Reconstruct Prompt Surfaces

#### Tasks

1. render or reconstruct the live extraction prompt surface for one named
   chunk;
2. render or reconstruct the prompt-eval operational-parity prompt surface for
   the same chunk;
3. capture the exact message/context differences.

#### Success criteria

1. the repo can show the prompt/context delta directly;
2. the delta is saved under `docs/runs/` or `var/` as a reproducible artifact.

### Phase 3: Land The Minimum Parity Aid

#### Tasks

1. implement the smallest helper needed to emit or compare those prompt
   surfaces reproducibly;
2. add verification for that helper.

#### Success criteria

1. future parity diagnosis no longer depends on ad hoc shell reconstruction;
2. the helper does not become a second extraction runtime.

### Phase 4: Classify The Dominant Residual

#### Tasks

1. run the parity aid on chunks `002` and `003`;
2. decide whether the dominant blocker is prompt/render contract or semantic
   extraction behavior;
3. record any secondary runtime/judge caveats separately.

#### Success criteria

1. one dominant blocker family is named explicitly;
2. the decision is backed by chunk `002` and chunk `003`, not by one chunk
   only.

### Phase 5: Closeout

#### Tasks

1. write the decision note;
2. refresh `CLAUDE.md`, `HANDOFF.md`, `KNOWLEDGE.md`, `TODO.md`,
   `docs/STATUS.md`, and `docs/plans/CLAUDE.md`;
3. either close this block or activate the next bounded extraction block from
   the named residual.

#### Success criteria

1. the next extraction block is narrowed to one explicit blocker family;
2. top-level docs truthfully reflect the new active block.

## Failure Modes

1. the block turns into another generic prompt-tuning cycle;
2. prompt-eval and live disagreement is described only through aggregate
   scores;
3. worktree/main-checkout import ambiguity reappears;
4. the closeout collapses prompt/render differences and semantic differences
   into one bucket.

## Exit Criteria

This block is complete only when:

1. all five phases above meet their success criteria;
2. the worktree is clean;
3. the repo contains committed parity-localization artifacts and a decision
   note.

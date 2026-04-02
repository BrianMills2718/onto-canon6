# 24h Post-Parity Semantic Recovery Block

Status: active
Phase status:
- Phase 1 pending
- Phase 2 pending
- Phase 3 pending
- Phase 4 pending
- Phase 5 pending

Last updated: 2026-04-02
Workstream: recover chunk-003 semantic quality after prompt-side parity repairs

## Purpose

Plan `0049` proved the prompt-side parity repairs worked:

1. prompt_eval no longer collapses to `0` candidates on chunk `003`;
2. the repaired prompt_eval output is now near the live family instead of the
   old prompt_eval failure family; and
3. the remaining blocker is semantic extraction quality, not transport or
   prompt-wrapper drift.

This block exists to answer the next explicit question:

**What bounded semantic change can improve strict-omit behavior on the repaired
chunk-003 analytical path without reopening prompt-path divergence?**

## Scope

This block intentionally covers only:

1. the repaired compact operational-parity prompt surface;
2. chunk `003` as the canonical analytical strict-omit stress case;
3. semantic extraction behavior before review.

Out of scope:

1. new prompt-surface parity work;
2. review/judge policy changes;
3. broad fixture sweeps before the bounded chunk recovers.

## Pre-Made Decisions

1. Work stays in the isolated `codex/onto-canon6-integration-planning`
   worktree.
2. All Python execution in this block must use `PYTHONPATH=src`.
3. The incoming decision note is:
   `docs/runs/2026-04-02_prompt_parity_repair_decision.md`.
4. Do not reopen `Case id` or `Case input` prompt plumbing unless the new
   evidence directly contradicts the repair decision.
5. The first lever is bounded semantic prompt revision on the repaired parity
   surface, not another extraction-path or template-wrapper investigation.

## Gate

This block succeeds only if:

1. the repo names one bounded semantic blocker family on chunk `003`;
2. one bounded semantic change is implemented against the repaired parity
   surface;
3. one post-change artifact shows whether the chunk-003 family improved or not;
4. the closeout says whether the next blocker is still semantic or has moved
   again.

## Phase Order

### Phase 1: Freeze The Post-Parity Semantic Contract

#### Tasks

1. freeze the post-repair prompt_eval/live family on chunk `003`;
2. name the exact semantic miss family that remains.

#### Success criteria

1. the active blocker is no longer described as prompt parity;
2. one semantic miss family is named explicitly.

### Phase 2: Land One Bounded Semantic Change

#### Tasks

1. revise the repaired operational-parity prompt only in the smallest semantic
   way that targets the active miss family;
2. keep the repaired wrapper/case-id parity intact.

#### Success criteria

1. one bounded semantic revision lands;
2. prompt-surface parity does not regress.

### Phase 3: Re-run The Chunk-003 Diagnostic

#### Tasks

1. rerun the bounded chunk-003 prompt_eval diagnostic after the semantic
   revision;
2. capture the new artifact.

#### Success criteria

1. there is one committed post-change chunk-003 artifact;
2. the result can be compared directly to the incoming repaired baseline.

### Phase 4: Classify The Result

#### Tasks

1. decide whether the semantic revision improved the chunk family, failed, or
   shifted the blocker again;
2. record any narrow uncertainty separately.

#### Success criteria

1. one dominant result is named explicitly;
2. it is artifact-backed.

### Phase 5: Closeout

#### Tasks

1. write the decision note;
2. refresh `CLAUDE.md`, `HANDOFF.md`, `KNOWLEDGE.md`, `TODO.md`,
   `docs/STATUS.md`, and `docs/plans/CLAUDE.md`;
3. either close this block or activate the next narrower block.

#### Success criteria

1. the next active blocker is narrower than `0050`;
2. top-level docs truthfully reflect the semantic recovery status.

## Exit Criteria

This block is complete only when:

1. all five phases above meet their success criteria;
2. the worktree is clean;
3. the repo contains committed semantic-recovery artifacts and a decision note.

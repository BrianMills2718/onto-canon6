# 24h Limit-Capability Enforcement Block

Status: active
Phase status:
- Phase 1 completed
- Phase 2 completed
- Phase 3 completed
- Phase 4 pending
- Phase 5 pending

Last updated: 2026-04-02
Workstream: deterministic enforcement for the remaining abstract chunk-003 limit-capability family

## Purpose

Plan `0059` proved that another bounded prompt hardening pass can reduce the
chunk-003 live residual, but it still leaves three abstract evaluative
`oc:limit_capability` claims accepted. Those claims are already covered by the
local strict-omit contract (`013` and `014`), so the next move is not another
generic prompt rewrite. It is one bounded enforcement seam that makes the live
path honor the documented boundary reliably.

## Scope

This block intentionally covers only:

1. the remaining abstract evaluative `oc:limit_capability` family;
2. one bounded enforcement seam in the live extraction/review path;
3. targeted tests for that seam; and
4. one fresh rerun on chunk `002` and chunk `003`.

Out of scope:

1. new benchmark redesign;
2. unrelated predicate families;
3. reopening the review contract from Plan `0058`; and
4. new transfer chunks.

## Pre-Made Decisions

1. Work stays in the isolated `codex/onto-canon6-integration-planning`
   worktree.
2. The remaining family is frozen as the three accepted chunk-003
   `oc:limit_capability` claims from Plan `0059`.
3. The live review contract from Plan `0058` stays frozen.
4. The enforcement seam must be bounded and family-level, not benchmark-row
   hardcoding.
5. Chunk `002` remains the positive control and chunk `003` remains the
   prose-heavy stress case.
6. The fresh rerun root for this block is:
   - `var/real_runs/2026-04-02_limit_capability_enforcement/`

## Gate

This block succeeds only if:

1. the remaining abstract `limit_capability` family is blocked or downgraded
   deterministically in the live path;
2. targeted tests cover that enforcement seam;
3. chunk `002` remains positive; and
4. chunk `003` no longer accepts the same three abstract `limit_capability`
   claims.

## Phase Order

### Phase 1: Freeze The Remaining Family

#### Tasks

1. close Plan `0059` truthfully;
2. freeze the exact remaining chunk-003 accepted claims as the incoming
   contract;
3. record the current local benchmark cases that already govern this family.

#### Success criteria

1. the owned family is explicit and bounded;
2. the new block is active in the authority docs.

### Phase 2: Land One Bounded Enforcement Seam

#### Tasks

1. add one deterministic guard for abstract evaluative `limit_capability`
   candidates in the live path;
2. keep the rule framed at the failure-family level rather than per benchmark
   row;
3. avoid changing unrelated predicates or review policies.

#### Success criteria

1. the live path enforces the documented family boundary;
2. the code change is narrow and observable.

### Phase 3: Verify The Enforcement Seam

#### Tasks

1. add/update targeted tests for the abstract `limit_capability` family;
2. run the narrow verification slice before fresh reruns.

#### Success criteria

1. targeted tests pass;
2. the family is visible in local verification.

### Phase 4: Rerun Chunk 002 And Chunk 003

#### Tasks

1. rerun chunk `002` under a fresh DB;
2. rerun chunk `003` under the same fresh DB;
3. export both transfer reports;
4. compare the new chunk-003 accepted set against the frozen residual family.

#### Success criteria

1. fresh rerun artifacts exist;
2. chunk `002` remains positive;
3. chunk `003` no longer accepts the same abstract `limit_capability` family.

### Phase 5: Classify Promotion Posture And Close Out

#### Tasks

1. write the decision note;
2. refresh `CLAUDE.md`, `TODO.md`, `HANDOFF.md`, `docs/STATUS.md`,
   `docs/plans/CLAUDE.md`, `docs/plans/0014_extraction_quality_baseline.md`,
   and `KNOWLEDGE.md`;
3. mark the block complete only when the worktree is clean.

#### Success criteria

1. the next blocker or promotion posture is explicit and decision-grade;
2. the worktree is clean.

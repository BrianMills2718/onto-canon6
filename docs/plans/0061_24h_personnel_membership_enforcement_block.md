# 24h Personnel-Membership Enforcement Block

Status: active
Phase status:
- Phase 1 completed
- Phase 2 completed
- Phase 3 completed
- Phase 4 pending
- Phase 5 pending

Last updated: 2026-04-02
Workstream: deterministic enforcement for the remaining staffing-summary
membership leak on chunk `003`

## Purpose

Plan `0060` proved that the abstract evaluative `oc:limit_capability` family
can be blocked deterministically on the live path. That leaves one smaller
live-transfer residual: a staffing-summary sentence still turns into an
accepted `oc:belongs_to_organization` claim on chunk `003`.

This block owns only that residual family. It is not a broad prompt rewrite
and it is not a benchmark redesign.

## Scope

This block intentionally covers only:

1. the remaining staffing-summary `oc:belongs_to_organization` family;
2. one bounded live-path enforcement seam for that family;
3. targeted tests for that seam; and
4. one fresh rerun on chunk `002` and chunk `003`.

Out of scope:

1. changes to unrelated predicates;
2. new benchmark fixture redesign;
3. reopening the review contract from Plan `0058`; and
4. widening beyond the named chunk-transfer gate.

## Pre-Made Decisions

1. Work stays in the isolated `codex/onto-canon6-integration-planning`
   worktree.
2. The owned family is frozen as the remaining accepted chunk-003
   staffing-summary `oc:belongs_to_organization` candidate from Plan `0060`.
3. The active local benchmark guard is
   `psyop_017_personnel_dedication_not_membership_strict_omit`.
4. The enforcement seam must be family-level, not benchmark-row hardcoding.
5. Chunk `002` remains the positive control and chunk `003` remains the
   prose-heavy stress case.
6. The fresh rerun root for this block is:
   - `var/real_runs/2026-04-02_personnel_membership_enforcement/`

## Gate

This block succeeds only if:

1. the staffing-summary membership family is blocked or downgraded
   deterministically in the live path;
2. targeted tests cover that enforcement seam;
3. chunk `002` remains positive; and
4. chunk `003` no longer accepts the same staffing-summary
   `oc:belongs_to_organization` claim.

## Phase Order

### Phase 1: Freeze The Remaining Family

#### Tasks

1. close Plan `0060` truthfully;
2. freeze the exact remaining chunk-003 accepted claim as the incoming
   contract; and
3. restate the governing local benchmark guard for this family.

#### Success criteria

1. the owned family is explicit and bounded; and
2. the new block is active in the authority docs.

### Phase 2: Land One Bounded Enforcement Seam

#### Tasks

1. add one deterministic guard for staffing-summary
   `oc:belongs_to_organization` claims in the live path;
2. keep the rule family-level rather than benchmark-row specific; and
3. avoid changing unrelated predicates or review policies.

#### Success criteria

1. the live path enforces the documented family boundary; and
2. the code change is narrow and observable.

### Phase 3: Verify The Enforcement Seam

#### Tasks

1. add/update targeted tests for the staffing-summary family; and
2. run the narrow verification slice before fresh reruns.

#### Success criteria

1. targeted tests pass; and
2. the family is visible in local verification.

### Phase 4: Rerun Chunk 002 And Chunk 003

#### Tasks

1. rerun chunk `002` under a fresh DB;
2. rerun chunk `003` under the same fresh DB;
3. export both transfer reports; and
4. compare the new chunk-003 accepted set against the frozen residual family.

#### Success criteria

1. fresh rerun artifacts exist;
2. chunk `002` remains positive; and
3. chunk `003` no longer accepts the same staffing-summary membership claim.

### Phase 5: Classify Promotion Posture And Close Out

#### Tasks

1. write the decision note;
2. refresh `CLAUDE.md`, `TODO.md`, `HANDOFF.md`, `docs/STATUS.md`,
   `docs/plans/CLAUDE.md`, `docs/plans/0014_extraction_quality_baseline.md`,
   and `KNOWLEDGE.md`; and
3. mark the block complete only when the worktree is clean.

#### Success criteria

1. the next blocker or promotion posture is explicit and decision-grade; and
2. the worktree is clean.

# 24h Entity Resolution Negative-Control Recovery Block

Status: active
Phase status:
- Phase 1 pending
- Phase 2 pending
- Phase 3 pending
- Phase 4 pending
- Phase 5 pending

Last updated: 2026-04-01
Workstream: restore fresh-run same-surname safety and negative same-entity
answerability after Plan 0035 closed the alias-family residuals

## Purpose

Plan 0035 closed the three residual alias families from the clean-measurement
baseline, but the fresh clean rerun exposed a different blocker:

1. the titled-person bridge reopened `John Smith` / `James Smith` false merges;
2. `q05` regressed from safe negative control to answered-but-wrong;
3. `q06` remained unanswered on the fresh rerun even though `q09` now proves
   the `GWU` canonical surface can resolve.

This block owns only those residual fresh-run blockers. It must preserve the
newly closed alias families from Plan 0035 (`q02`, `q04`, `q08`) while
restoring same-surname person safety and resolving the remaining negative
control question behavior.

## Scope

This block intentionally covers only:

1. same-surname person safety for the `John Smith` / `James Smith` family on
   fresh clean runs;
2. bounded hardening of titled-person bridge logic so initials and titles still
   help `John Smith` clusters without pulling in incompatible full names;
3. diagnosis and repair of the `Washington` / `George Washington University`
   negative-control question if it remains unanswered after Phase 2;
4. one fresh rerun on a new DB;
5. closeout of `0025`, `CLAUDE.md`, `docs/STATUS.md`, `HANDOFF.md`,
   `KNOWLEDGE.md`, `docs/plans/CLAUDE.md`, and `TODO.md`.

Out of scope:

1. new evaluator semantics;
2. broad new alias-surface mining beyond the bounded residual needed for `q06`;
3. widening query/browse capabilities;
4. DIGIMON or consumer-boundary work;
5. changing the synthetic corpus or question fixture.

## Pre-Made Decisions

1. Work stays in the isolated `codex/onto-canon6-integration-planning`
   worktree.
2. Plan 0035 is complete and the fresh clean rerun artifact for this block is:
   `docs/runs/scale_test_llm_2026-04-01_110321.json`.
3. The next repair begins with same-surname person safety, not more
   organization-family widening.
4. Any new safeguard must preserve the `q02`, `q04`, and `q08` wins from Plan
   0035.
5. The bridge logic may use role/title evidence, initials, and observed full
   given-name anchors, but it must not merge two incompatible explicit full
   person names only because they share a surname and title family.
6. `q06` is treated as a negative-control answerability problem: the desired
   outcome is answered-and-correct (`False`), not silence.
7. Every verified phase gets its own commit.

## Gate

This block succeeds only if a fresh rerun satisfies all of the following:

1. all `25` source documents survive extraction;
2. pairwise precision stays at or above `0.95`;
3. pairwise recall stays at or above the fresh-clean floor of `0.88` from the
   corrected fixed-sample diagnostic artifact, or any shortfall is explicitly
   explained by remaining unmatched observations rather than new false merges;
4. false merges return to `0`;
5. fixed-question answer rate reaches at least `0.90`;
6. fixed-question accuracy over all questions reaches at least `0.90`;
7. `q01`, `q02`, `q04`, `q05`, `q07`, `q08`, and `q09` are answered and
   correct;
8. `q06` is either answered and correct on the fresh rerun, or localized to one
   explicit residual mention family in the decision note with a bounded next
   step.

If the rerun still misses this gate, the block still counts as complete only if
the remaining miss is explicit, measurement-valid, and narrower than the
current same-surname safety blocker.

## Phase Order

### Phase 1: Freeze The Fresh-Run Residual Contract

#### Tasks

1. close Plan 0035 truthfully in the docs;
2. activate Plan 0036 in `CLAUDE.md`, the plans index, `0025`, `TODO.md`, and
   other top-level trackers;
3. freeze the fresh-run residuals (`q05`, `q06`) and the gate above.

#### Success criteria

1. active docs point at Plan 0036 rather than Plan 0035;
2. the next implementation choices are explicit enough to execute without new
   questions.

### Phase 2: Restore Same-Surname Person Safety

#### Tasks

1. localize exactly why `James Smith` re-enters the titled `John Smith` cluster
   on the fresh clean rerun;
2. tighten titled-person bridging so initial/surname shorthand still joins the
   correct full-name anchor without merging incompatible explicit given names;
3. add or update targeted regression tests covering:
   - `John Smith` / `General John Smith` / `Gen. Smith` / `Gen. J. Smith`
     positive merges;
   - `James Smith` remaining separate even when title-bearing surname mentions
     are present;
   - no regression to the pre-0035 title-bridge miss.

#### Success criteria

1. targeted tests pass;
2. the repair is family-level, not benchmark-string specific;
3. the false-merge family in the fresh rerun has a concrete root-cause fix.

### Phase 3: Recover The Remaining Negative-Control Answerability

#### Tasks

1. rerun or inspect the localized `q06` matching path after Phase 2;
2. if `q06` is still unanswered, identify the exact residual mention family
   (for example unmatched `Washington`, suppressed institution mention, or
   ambiguous cluster assignment);
3. land one bounded repair only if the residual is clear and testable;
4. add or update targeted regression tests for the `Washington` / `George
   Washington University` negative-control path.

#### Success criteria

1. the remaining `q06` behavior is explicit and measurement-valid;
2. any repair stays bounded to the diagnosed family;
3. same-surname person safety remains green.

### Phase 4: Rerun The Fresh Value Proof

#### Tasks

1. rerun the LLM strategy on a fresh DB after Phases 2-3;
2. verify `25/25` document survival directly from the DB;
3. inspect the new question scores and pairwise metrics against the gate.

#### Success criteria

1. a fresh JSON artifact exists under `docs/runs/`;
2. the rerun is measurement-valid;
3. the artifact is sufficient to decide whether the safety regression is
   closed.

### Phase 5: Closeout

#### Tasks

1. write the decision-grade run note;
2. refresh `0025`, `CLAUDE.md`, `docs/STATUS.md`, `HANDOFF.md`,
   `KNOWLEDGE.md`, `docs/plans/CLAUDE.md`, and `TODO.md`;
3. mark this block completed.

#### Success criteria

1. top-level docs describe the current decision truthfully;
2. the worktree is left clean with committed checkpoints only.

## Failure Modes

1. tightening titled-person bridges overcorrects and re-splits `Gen. Smith` /
   `General John Smith`;
2. the repair silently depends on corpus-specific strings instead of a general
   same-surname safety rule;
3. `q06` is still conflated with evaluator behavior rather than a real mention
   / cluster residual;
4. the rerun regresses `q02`, `q04`, or `q08` while restoring `q05`.

## Exit Criteria

This block is complete only when:

1. all five phases above meet their success criteria;
2. the worktree is clean;
3. the repo contains committed code, tests, rerun artifacts, and docs for the
   negative-control recovery decision.

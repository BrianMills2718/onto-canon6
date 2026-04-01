# 24h Entity Resolution Alias-Family Completion Block

Status: active
Phase status:
- Phase 1 pending
- Phase 2 pending
- Phase 3 pending
- Phase 4 pending
- Phase 5 pending

Last updated: 2026-04-01
Workstream: bounded closure of the three residual answerability misses after
Plan 0034

## Purpose

Convert the clean-measurement baseline from Plan 0034 into a final
decision-grade repair pass.

Plan 0034 proved that measurement hygiene is no longer the blocker. The clean
rerun survived all `25/25` documents and improved pairwise recall to `0.746`
with zero false merges. The remaining misses are now narrow and explicit:

1. `q02`: `USSOCOM` and one `U.S. Special Operations Command` observation still
   land in different predicted clusters because the latter carries a generic /
   missing entity type and never joins the organization family;
2. `q04`: `Ft. Bragg` and `Fort Liberty` still remain split even after the
   clean rerun, so one bounded installation-equivalence repair is now justified;
3. `q08`: `the Agency` remains unanswered because observed
   `oc:government_agency` mentions do not match ground-truth
   `oc:government_organization`.

This block owns only those three residual families and the rerun needed to
prove they are closed.

## Scope

This block intentionally covers only:

1. organization-family recovery for missing / generic entity types that should
   resolve with organization mentions;
2. organization-family compatibility for `government_agency` ↔
   `government_organization`;
3. one bounded installation-equivalence repair for renamed military
   installations;
4. one fresh rerun on a new DB;
5. closeout of `0025`, `CLAUDE.md`, `docs/STATUS.md`, `HANDOFF.md`,
   `KNOWLEDGE.md`, and `TODO.md`.

Out of scope:

1. changing the synthetic corpus, ground truth, or question fixture;
2. broad ontology-family rewrites outside the three localized failure families;
3. new retrieval/query-surface work;
4. DIGIMON or consumer-boundary work;
5. replacing the current LLM resolution strategy with a different architecture.

## Pre-Made Decisions

1. Work stays in the isolated `codex/onto-canon6-integration-planning`
   worktree.
2. Plan 0034 is treated as completed with a clean baseline recorded in:
   `docs/runs/2026-04-01_entity_resolution_clean_measurement.md`.
3. The first repair in this block is family / alias-surface repair, not more
   measurement harness work.
4. `government_agency` and `government_organization` are pre-approved as the
   same conservative organization family.
5. Missing / generic promoted entity types may be treated as organization-like
   only when the name itself carries strong organization signal. Do not make
   unknown types merge broadly by default.
6. Installation-equivalence work must stay bounded to installation-like names.
   Do not add broad place-alias logic.
7. Every verified phase gets its own commit.

## Gate

This block succeeds only if a fresh rerun satisfies all of the following:

1. all `25` source documents still survive extraction;
2. pairwise precision stays at or above `0.95`;
3. pairwise recall stays at or above the clean-measurement baseline of `0.746`;
4. false merges stay at `0`;
5. fixed-question answer rate reaches at least `0.90`;
6. fixed-question accuracy over all questions reaches at least `0.90`;
7. `q02`, `q04`, and `q08` are all answered and correct.

If the rerun still misses this gate, the block still counts as complete if the
remaining miss is explicit, localized, and recorded in the decision note.

## Phase Order

### Phase 1: Freeze The Residual Failure Contract

#### Tasks

1. record the clean-measurement baseline from Plan 0034;
2. activate Plan 0035 in `CLAUDE.md`, the plans index, `0025`, and `TODO.md`;
3. freeze the three residual failure families and the gate above.

#### Success criteria

1. active docs point at Plan 0035 rather than Plan 0034;
2. the next implementation choices are explicit enough to execute without new
   questions.

### Phase 2: Repair Organization-Family Drift

#### Tasks

1. add the bounded family repair so `government_agency` and
   `government_organization` compare conservatively inside the organization
   family;
2. add name-aware family inference for missing / generic entity types when the
   name itself is strongly organization-like;
3. add or update targeted tests covering:
   - `U.S. Special Operations Command` with missing / generic type joining the
     organization family;
   - `government_agency` ↔ `government_organization` compatibility;
   - the fixed evaluator path for `q02` and `q08`.

#### Success criteria

1. targeted tests pass;
2. the repair is family-level, not benchmark-string specific;
3. `q02` and `q08` become reachable on surviving promoted observations.

### Phase 3: Land The Bounded Installation-Equivalence Repair

#### Tasks

1. localize the surviving `Ft. Bragg` / `Fort Liberty` split at the
   post-resolution grouping level;
2. add one bounded repair for installation rename / redesignation equivalence;
3. add targeted tests covering the split and the intended merge path.

#### Success criteria

1. the repair is scoped to installation-like names only;
2. targeted regression tests pass;
3. the same-surname person safety family remains green.

### Phase 4: Rerun The Value Proof

#### Tasks

1. rerun the LLM strategy on a fresh DB after Phases 2-3;
2. verify `25/25` document survival directly from the DB;
3. inspect the new question scores and pairwise metrics against the gate.

#### Success criteria

1. a fresh JSON artifact exists under `docs/runs/`;
2. the rerun is measurement-valid;
3. the artifact is sufficient to decide whether the three residual families are
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

1. organization-family repair broadens unknown-type handling so far that it
   invites new false merges;
2. installation-equivalence logic leaks into broad place-matching behavior;
3. the rerun regresses precision or reintroduces false merges while trying to
   recover the last three questions;
4. the closeout note reports only aggregate metrics and does not state whether
   `q02`, `q04`, and `q08` were actually closed.

## Exit Criteria

This block is complete only when:

1. all five phases above meet their success criteria;
2. the worktree is clean;
3. the repo contains committed code, tests, rerun artifacts, and docs for the
   alias-family completion decision.

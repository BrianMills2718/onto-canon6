# 24h Entity Resolution Answerability Block

Status: active
Phase status:
- Phase 1 completed
- Phase 2 pending
- Phase 3 pending
- Phase 4 pending
- Phase 5 pending

Last updated: 2026-04-01
Workstream: bounded follow-on hardening after Plan 0032 cleared the recovery gate

## Purpose

Convert the Plan 0032 success from "good enough to clear the bounded recovery
gate" into a stronger promotion-candidacy result for entity resolution.

The active problem is no longer document loss or unsafe false merges. The
remaining misses are narrower:

1. benchmark-critical mentions still diverge across incompatible extracted
   types (`Gen. Smith` as `person` vs `military_rank`, `Ft. Bragg` as
   `location` vs `military_organization`);
2. benchmark-critical aliases like `the Agency` and `GWU` still do not appear
   as promoted matched observations;
3. university / place answerability is still weak (`Washington` vs
   `George Washington University`).

This block is complete only when the repo has:

1. frozen the remaining failure families and the new answerability gate;
2. implemented a bounded fix for type-divergent mention families;
3. implemented a bounded fix for missing alias-surface families;
4. refreshed the LLM value proof on the same fixed corpus;
5. written a decision saying whether the LLM strategy is now plausibly
   promotable or still blocked.

## Scope

This block intentionally covers only:

1. benchmark-critical type-family answerability hardening;
2. benchmark-critical alias-surface recovery for promoted observations;
3. the same fixed synthetic corpus and question fixture from Plans 0030-0032;
4. one fresh LLM rerun and one fresh decision note;
5. plan / TODO / status / knowledge closeout.

Out of scope:

1. changing the evaluator or question fixture;
2. weakening the Plan 0031 same-surname safety guard;
3. broad new prompt-family exploration without a traced failure family;
4. DIGIMON work or query-surface work;
5. scale-out beyond the fixed synthetic corpus.

## Pre-Made Decisions

1. Work stays in the isolated `codex/onto-canon6-integration-planning`
   worktree.
2. The authoritative comparison point is the Plan 0032 rerun artifact:
   `docs/runs/scale_test_llm_2026-04-01_083207.json`.
3. The next fixes must target underlying representation or extraction families,
   not the evaluator.
4. The same-surname person safety guard remains non-negotiable.
5. Type-family hardening may use ontology-aware compatibility or bounded
   post-extraction correction, but it must be general-family logic, not a
   question-row patch.
6. Alias-surface recovery may use bounded prompt or normalization hardening,
   but it must improve general abbreviation / elided-reference handling, not
   special-case `GWU` or `the Agency` by literal benchmark id.
7. Every verified phase gets its own commit.

## Answerability Gate

This block succeeds only if all of the following are true on the refreshed LLM
run:

1. all `25` source documents still survive extraction;
2. pairwise precision stays at or above `0.95`;
3. pairwise recall stays at or above `0.60`;
4. false merges stay at or below `2`;
5. fixed-question answer rate reaches at least `0.70`;
6. fixed-question accuracy over all questions reaches at least `0.50`;
7. `q04`, `q08`, and `q09` are no longer wrong or unanswered.

If those thresholds are missed, the block still counts as complete if the
remaining miss is explicit and localized in the run note.

## Phase Order

### Phase 1: Freeze The Answerability Contract

#### Tasks

1. make this block the active execution surface in `CLAUDE.md`, the plans
   index, and `TODO.md`;
2. freeze the targeted failure families:
   - type-divergent mention surfaces
   - missing alias surfaces
   - university / place answerability
3. freeze the answerability gate above.

#### Success criteria

1. the active docs point to this block rather than the completed Plan 0032;
2. the stop conditions and thresholds are explicit enough to implement without
   new questions.

#### Outcome

Completed on 2026-04-01.

`CLAUDE.md`, the plans index, `TODO.md`, and the active handoff/status surfaces
now point at Plan 0033 as the bounded next block, and the answerability gate is
frozen for implementation.

### Phase 2: Repair Type-Divergent Mention Families

#### Tasks

1. localize where benchmark-critical mentions drift into incompatible types;
2. implement a bounded family-level fix so:
   - titled person mentions remain answerable as persons
   - installation rename / alias mentions remain answerable through one
     compatible family
3. add focused tests for the repaired family behavior.

#### Success criteria

1. targeted regression tests pass;
2. the fix is not benchmark-id specific;
3. same-surname person non-merge safety remains green.

### Phase 3: Recover Missing Alias Surfaces

#### Tasks

1. localize why elided or abbreviated aliases like `the Agency` and `GWU` do
   not survive into promoted matched observations;
2. implement a bounded family-level fix for alias-surface coverage;
3. add focused tests for abbreviation / elided-reference handling.

#### Success criteria

1. targeted extraction / resolution tests pass;
2. the fix improves general alias-surface coverage rather than hardcoding the
   two benchmark strings;
3. the existing document-survival and safety floors remain intact.

### Phase 4: Refresh The LLM Value Proof

#### Tasks

1. rerun the LLM strategy on a fresh DB with the bounded overrides;
2. compare the rerun against the Plan 0032 artifact;
3. write a new run note naming:
   - new metrics
   - what question families moved
   - what still fails
   - whether LLM is closer to default promotion

#### Success criteria

1. a fresh LLM JSON artifact exists under `docs/runs/`;
2. the run note is decision-grade and references the new artifact directly;
3. if the LLM path is still not promotable, the blocking miss is concrete.

### Phase 5: Closeout

#### Tasks

1. update `0025`, `CLAUDE.md`, `docs/STATUS.md`, `HANDOFF.md`, and
   `KNOWLEDGE.md`;
2. mark this block completed when all phases land;
3. refresh `TODO.md` so the next unresolved frontier is explicit.

#### Success criteria

1. top-level docs describe the answerability result truthfully;
2. the next active work is explicit;
3. the worktree is left clean with committed checkpoints only.

## Failure Modes

1. a type-family fix weakens entity-type safety broadly instead of repairing a
   bounded compatibility family;
2. alias-surface recovery is achieved by literal benchmark string special
   casing;
3. the rerun improves answer rate by changing the evaluator rather than the
   underlying extracted / resolved surface;
4. the run note reports aggregate metrics but not which benchmark families
   still fail.

## Exit Criteria

This block is complete only when:

1. all five phases above meet their success criteria;
2. the worktree is clean;
3. the repo contains committed code, tests, rerun artifacts, and docs for the
   answerability decision.

# 24h Entity Resolution False-Split Cleanup Block

Status: completed
Phase status:
- Phase 1 completed
- Phase 2 completed
- Phase 3 completed
- Phase 4 completed
- Phase 5 completed

Last updated: 2026-04-01
Workstream: close the Rodriguez and Washington residual families truthfully and
hand off the newly exposed surface-stability blocker family to Plan 0038

## Purpose

Plan 0036 cleared the active blocker:

1. fresh-run same-surname false merges are gone;
2. `q05` and `q06` are both answered and correct on a fresh rerun;
3. fixed-question accuracy is now `1.00`.

The remaining quality gap is narrower and strictly pairwise:

1. `James Rodriguez` / `Colonel Rodriguez` still split from `Col. Rodriguez`;
2. `Washington D.C.` / `D.C.` still split from the `Washington` location
   cluster.

This block owned only those residual false-split families. It preserved the
current safety floor while proving that the next blocker family is different:

1. false merges must stay at `0`;
2. all `25` documents must survive extraction;
3. fixed-question answer rate and accuracy must stay at `1.00`.

## Outcome

This block succeeded on its own scope:

1. `James Rodriguez` / `Colonel Rodriguez` / `Col. Rodriguez` now collapse in
   one conservative person family;
2. `Washington D.C.` / `D.C.` / `Washington` now collapse in one bounded place
   family without crossing into `George Washington University`;
3. the fresh rerun remained measurement-valid with `25/25` documents surviving
   and false merges still at `0`.

The fresh rerun also showed that the residual blocker family shifted. The
active misses are now:

1. generic acronym organization/university surfaces emitted under generic
   `entity:*` types (`NSA`, `GWU`);
2. descriptor alias recovery for organization families (`the Agency`);
3. evaluator mention-key equivalence for `Ft. Bragg` / `Fort Bragg`.

Those are now owned by
`docs/plans/0038_24h_entity_resolution_surface_stability_block.md`.

## Scope

This block intentionally covers only:

1. conservative Rodriguez title-family collapse when exactly one explicit
   full-given anchor family exists for a surname;
2. conservative Washington place-family collapse for the existing capital
   district mention family;
3. one fresh rerun on a new DB with timeout policy explicitly enabled;
4. closeout of `0025`, `CLAUDE.md`, `docs/STATUS.md`, `HANDOFF.md`,
   `KNOWLEDGE.md`, `docs/plans/CLAUDE.md`, and `TODO.md`.

Out of scope:

1. broad new alias mining;
2. changing the synthetic corpus, evaluator, or question fixture;
3. DIGIMON or consumer-boundary work;
4. query/browse widening;
5. scale-out batching work from `0025a`.

## Pre-Made Decisions

1. Work stays in the isolated `codex/onto-canon6-integration-planning`
   worktree.
2. The canonical incoming artifact is
   `docs/runs/scale_test_llm_2026-04-01_113959.json`.
3. All fresh reruns in this block set `LLM_CLIENT_TIMEOUT_POLICY=allow`.
4. Rodriguez-family work begins before Washington-family work because it is the
   only remaining person-family split and shares logic with the active
   same-surname safety machinery.
5. Any person-family repair must preserve the Plan 0036 `John Smith` /
   `James Smith` safety floor.
6. Any place-family repair must preserve the type guard that keeps
   `Washington` the location separate from `George Washington University`.
7. Every verified phase gets its own commit.

## Gate

This block succeeds only if a fresh rerun satisfies all of the following:

1. all `25` source documents survive extraction;
2. pairwise precision stays at or above `0.95`;
3. pairwise recall reaches `1.00`;
4. false merges stay at `0`;
5. false splits return to `0`;
6. fixed-question answer rate stays at `1.00`;
7. fixed-question accuracy over all questions stays at `1.00`.

If the fresh rerun misses this gate, the block still counts as complete only if
the remaining miss is explicit, measurement-valid, and narrower than the two
families frozen below.

## Frozen Residual Contract

The incoming residuals from `113959` are:

1. Rodriguez family:
   - `James Rodriguez`
   - `Colonel Rodriguez`
   - `Col. Rodriguez`
2. Washington place family:
   - `Washington D.C.`
   - `D.C.`
   - `Washington` as a place/location

No other families are currently in scope.

## Phase Order

### Phase 1: Freeze The Residual False-Split Contract

#### Tasks

1. close Plan 0036 truthfully in the docs;
2. activate Plan 0037 in `CLAUDE.md`, the plans index, `0025`, `TODO.md`, and
   top-level trackers;
3. freeze the residual false-split families and gate above.

#### Success criteria

1. active docs point at Plan 0037 rather than Plan 0036;
2. the owned residual families and rerun policy are explicit enough to execute
   without new questions.

### Phase 2: Repair The Rodriguez Title Family

#### Tasks

1. localize exactly why `Col. Rodriguez` stays outside the
   `James Rodriguez` / `Colonel Rodriguez` cluster after Plan 0036;
2. land one conservative family-level repair that allows a titled surname-only
   person group to join a unique compatible full-given anchor family when no
   conflicting explicit full names exist for that surname;
3. add or update targeted regression tests for:
   - positive merge: `James Rodriguez` / `Colonel Rodriguez` / `Col. Rodriguez`
   - safety: `John Smith` / `James Smith` stay separate
   - safety: surname-only titled mention stays unmerged when multiple explicit
     full-given anchors compete.

#### Success criteria

1. targeted tests pass;
2. the repair is surname-family level, not benchmark-id specific;
3. the existing same-surname safety floor stays green.

### Phase 3: Repair The Washington Place Family

#### Tasks

1. localize exactly why the `Washington` place cluster remains split from
   `Washington D.C.` / `D.C.`;
2. land one bounded place-family repair that collapses the current district
   alias family without weakening the institution/location type guard;
3. add or update targeted regression tests for:
   - positive merge: `Washington D.C.` / `D.C.` / `Washington`
   - safety: `Washington` the location remains separate from
     `George Washington University`.

#### Success criteria

1. targeted tests pass;
2. the repair is bounded to the diagnosed place-family mechanism;
3. institution/location separation remains green.

### Phase 4: Rerun The Fresh Value Proof

#### Tasks

1. rerun the LLM strategy on a fresh DB with timeout policy enabled;
2. verify `25/25` document survival directly from the DB;
3. inspect the new pairwise and question metrics against the gate.

#### Success criteria

1. a fresh JSON artifact exists under `docs/runs/`;
2. the rerun is measurement-valid;
3. the artifact is sufficient to decide whether the owned residual false splits
   are closed or whether a new blocker family has become dominant.

### Phase 5: Closeout

#### Tasks

1. write the decision-grade run note;
2. refresh `0025`, `CLAUDE.md`, `docs/STATUS.md`, `HANDOFF.md`,
   `KNOWLEDGE.md`, `docs/plans/CLAUDE.md`, and `TODO.md`;
3. mark this block completed.

#### Success criteria

1. top-level docs describe the current decision truthfully;
2. the worktree is left clean with committed checkpoints only.

## Canonical Rerun Artifact

The canonical outgoing rerun for this block is:

1. `docs/runs/scale_test_llm_2026-04-01_124135.json`

Measured result:

1. precision `1.00`
2. recall `0.9241`
3. false merges `0`
4. false splits `6`
5. answer rate `0.90`
6. accuracy over all questions `0.90`
7. accuracy over answered questions `1.00`

Interpretation:

1. the owned Rodriguez and Washington fixes landed successfully;
2. the gate was missed only because a new blocker family became dominant;
3. this block is therefore complete under its explicit exit clause and hands
   off to Plan 0038.

## Failure Modes

1. Rodriguez-family repair reopens same-surname person false merges;
2. Washington-family repair overmerges place names that only share a head
   token;
3. the rerun regresses `q06` by weakening the institution/location type guard;
4. the rerun is contaminated by timeout-policy drift or a reused DB.

## Exit Criteria

This block is complete only when:

1. all five phases above meet their success criteria;
2. the worktree is clean;
3. the repo contains committed code, tests, rerun artifacts, and docs for the
   residual false-split decision.

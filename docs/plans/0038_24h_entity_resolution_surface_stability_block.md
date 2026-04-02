# 24h Entity Resolution Surface Stability Block

Status: completed
Phase status:
- Phase 1 completed
- Phase 2 completed
- Phase 3 completed
- Phase 4 completed
- Phase 5 completed

Last updated: 2026-04-01
Workstream: close the original `0038` blocker family truthfully and hand off
fresh-run stability to Plan `0039`

## Purpose

Plan 0037 truthfully closed its own target families, but the fresh rerun showed
that the active blocker family is now different and narrower:

1. generic acronym organization/university mentions emitted under `entity:*`
   types (`NSA`, `GWU`) still split from their long-form clusters;
2. organization descriptor aliases like `the Agency` still do not collapse
   reliably into the governing CIA family on fresh reruns;
3. the evaluator still misses the `Ft. Bragg` / `Fort Bragg` same-entity
   question because mention lookup does not yet use bounded installation
   equivalence keys.

This block owned only those three residual seams. It preserved the current
safety floor:

1. false merges stay at `0`;
2. all `25` source documents survive extraction;
3. `q01` through `q10` remain structurally answerable without reopening the
   same-surname false-merge family.

## Scope

This block intentionally covers only:

1. conservative organization-family routing for generic acronym surfaces so
   `NSA` and `GWU` can join long-form organization / university families;
2. deterministic descriptor-alias signatures from source text so `the Agency`
   can attach to the CIA family when the context explicitly supports it;
3. evaluator mention-key stability for bounded installation equivalence
   (`Ft. Bragg` / `Fort Bragg` / `Fort Liberty`);
4. one fresh rerun on a new DB with `LLM_CLIENT_TIMEOUT_POLICY=allow`;
5. closeout of `0025`, `CLAUDE.md`, `docs/STATUS.md`, `HANDOFF.md`,
   `KNOWLEDGE.md`, `docs/plans/CLAUDE.md`, and `TODO.md`.

Out of scope:

1. broad new alias mining beyond the bounded descriptor-head list;
2. changing the synthetic corpus, evaluator fixtures, or question wording;
3. DIGIMON or consumer-boundary widening;
4. query/browse widening;
5. scale-out batching work from `0025a`.

## Pre-Made Decisions

1. Work stays in the isolated `codex/onto-canon6-integration-planning`
   worktree.
2. The canonical incoming artifact is
   `docs/runs/scale_test_llm_2026-04-01_124135.json`.
3. All reruns in this block set `LLM_CLIENT_TIMEOUT_POLICY=allow`.
4. Acronym-family repair lands before descriptor-alias repair because the
   current residual false splits show that family drift is the first-order
   blocker for both `NSA` and `GWU`.
5. Descriptor alias repair must consume only explicit source-text evidence and
   remain bounded to organization-family groups.
6. Evaluator mention-key repair must reuse the same bounded installation
   equivalence contract as runtime resolution rather than inventing a second
   rename list.
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
the remaining miss is explicit, measurement-valid, and narrower than the three
families frozen below.

## Frozen Residual Contract

The incoming residuals from `124135` are:

1. organization acronym family:
   - `National Security Agency`
   - `NSA`
2. descriptor alias family:
   - `CIA`
   - `Central Intelligence Agency`
   - `the Agency`
3. university acronym family:
   - `George Washington University`
   - `GWU`
4. same-entity evaluator lookup:
   - `Ft. Bragg`
   - `Fort Bragg`
   - `Fort Liberty`

No other families are in scope.

## Outcome

This block materially improved the owned family and produced one near-gate fresh
rerun:

1. `docs/runs/scale_test_llm_2026-04-01_131124.json`
   - precision `1.00`
   - recall `0.9756`
   - false merges `0`
   - false splits `2`
   - answer rate `0.80`
   - accuracy over all questions `0.80`
2. the original `NSA`, `GWU`, `the Agency`, and `Ft. Bragg` seams are no longer
   all active in the same way they were at the start of `0038`;
3. the remaining misses shifted again on the next fresh rerun, which exposed a
   broader rerun-stability problem driven by extraction-shape drift.

The counterexample rerun is:

1. `docs/runs/scale_test_llm_2026-04-01_132119.json`

That artifact reopened:

1. `the Agency`
2. `4th POG`
3. `D.C.`
4. `GWU`

Those are now owned by
`docs/plans/0039_24h_entity_resolution_rerun_stability_block.md`.

## Phase Order

### Phase 1: Freeze The Surface-Stability Contract

#### Tasks

1. close Plan 0037 truthfully in the docs;
2. activate Plan 0038 in `CLAUDE.md`, the plans index, `0025`, `TODO.md`, and
   top-level trackers;
3. freeze the residual blocker families and gate above.

#### Success criteria

1. active docs point at Plan 0038 rather than Plan 0037 as the current block;
2. the owned residual families and rerun policy are explicit enough to execute
   without new questions.

Progress note:

1. completed in commit `613efa9`, which closed Plan 0037 truthfully, activated
   Plan 0038, and checked in the canonical incoming rerun artifacts.

### Phase 2: Recover Generic Acronym Organization Families

#### Tasks

1. localize exactly why generic acronym mentions like `NSA` and `GWU` remain
   outside organization-family clustering when emitted as `entity:*`;
2. land one conservative family-level repair that lets single-token
   acronym-like generic mentions join the organization family without weakening
   person/place separation;
3. add or update targeted regression tests for:
   - positive merge: `National Security Agency` / `NSA`
   - positive merge: `George Washington University` / `GWU`
   - safety: person initials like `J. Smith` remain in the person family
   - safety: place abbreviations like `D.C.` remain in the place family

#### Success criteria

1. targeted tests pass;
2. the repair is family-level, not benchmark-id specific;
3. existing person/place family boundaries stay green.

Progress note:

1. landed in `src/onto_canon6/core/auto_resolution.py` with targeted regression
   coverage for `NSA`, `GWU`, and short place-abbreviation safety.

### Phase 3: Recover Organization Descriptor Alias Collapse

#### Tasks

1. localize exactly why `the Agency` still stays outside the CIA cluster on a
   fresh rerun;
2. land one bounded descriptor-alias repair that uses explicit source-text
   evidence only and stays within the organization family;
3. add or update targeted regression tests for:
   - positive merge: `CIA` / `the Agency`
   - safety: descriptor signatures do not merge unrelated organization groups
   - safety: descriptor signatures do not cross family boundaries

#### Success criteria

1. targeted tests pass;
2. the repair is source-evidence-bound and deterministic;
3. descriptor aliasing does not introduce false merges.

Progress note:

1. landed as a one-to-one descriptor bridge between definite descriptor-only
   organization groups and unique source-backed anchors.

### Phase 4: Repair Evaluator Mention-Key Stability

#### Tasks

1. localize exactly why `q04` remains unanswered after `Fort Liberty` and
   `Ft. Bragg` are already merged in the durable graph;
2. land one bounded evaluator repair that reuses installation equivalence keys
   for mention lookup;
3. add or update targeted regression tests for:
   - positive lookup: `Ft. Bragg` resolves through the `Fort Bragg` /
     `Fort Liberty` equivalence family
   - safety: unrelated mention lookup keys do not expand

#### Success criteria

1. targeted tests pass;
2. the evaluator uses the same bounded equivalence contract as runtime
   resolution;
3. the fix is measurement-surface only, not a data-fixture hack.

Progress note:

1. `_derived_mention_keys()`, `_cluster_ids_for_mention()`, and
   `_ground_truth_ids_for_mention()` now reuse the bounded installation
   equivalence contract.

### Phase 5: Rerun The Fresh Value Proof And Close Out

#### Tasks

1. rerun the LLM strategy on a fresh DB with timeout policy enabled;
2. verify `25/25` document survival directly from the DB;
3. inspect the new pairwise and question metrics against the gate;
4. write the decision-grade run note;
5. refresh `0025`, `CLAUDE.md`, `docs/STATUS.md`, `HANDOFF.md`,
   `KNOWLEDGE.md`, `docs/plans/CLAUDE.md`, and `TODO.md`;
6. mark this block completed.

#### Success criteria

1. a fresh JSON artifact exists under `docs/runs/`;
2. the rerun is measurement-valid;
3. top-level docs describe the current decision truthfully;
4. the worktree is left clean with committed checkpoints only.

## Failure Modes

1. acronym-family routing pulls person initials into organization groups;
2. descriptor aliasing overmerges generic organization phrases;
3. evaluator mention-key expansion hides a real runtime split instead of
   measuring it honestly;
4. the rerun regresses the zero-false-merge safety floor or reopens a completed
   question family;
5. the rerun is contaminated by timeout-policy drift or a reused DB.

## Exit Criteria

This block is complete only when:

1. all five phases above meet their success criteria;
2. the worktree is clean;
3. the repo contains committed code, tests, rerun artifacts, and docs for the
   residual surface-stability decision.

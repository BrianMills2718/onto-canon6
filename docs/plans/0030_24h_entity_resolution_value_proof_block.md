# 24h Entity Resolution Value-Proof Block

Status: completed
Phase status:
- Phase 1 completed
- Phase 2 completed
- Phase 3 completed
- Phase 4 completed
- Phase 5 completed

Last updated: 2026-04-01
Workstream: bounded 24-hour execution block for Plan 0025 Phase 4

## Outcome

Completed.

The repo now has:

1. a frozen value-proof corpus;
2. a typed decision-grade evaluator;
3. exact, bare-baseline, and LLM run artifacts;
4. a written comparison note in
   `docs/runs/2026-04-01_entity_resolution_value_proof.md`;
5. refreshed top-level docs that state the result truthfully.

Decision from the block:

1. the bare baseline is not competitive;
2. LLM clustering materially improves recall over exact matching;
3. LLM clustering is not ready for default promotion yet because false merges
   and fixed-question regressions are still real.

## Purpose

Convert Plan 0025 from a structural "the harness runs" state into a
decision-grade value-proof state.

This block is complete only when the repo has:

1. an explicit official value-proof corpus;
2. decision-grade entity-resolution metrics against ground truth;
3. a simpler bare-extraction comparison path on the same corpus;
4. a fixed cross-document question set;
5. at least one fully documented exact-strategy run on the official corpus.

## Scope

This block is intentionally narrower than "solve all entity resolution
questions forever." It covers exactly:

1. the existing synthetic military/OSINT corpus in
   `tests/fixtures/synthetic_corpus`;
2. exact-strategy and LLM-strategy evaluation hooks for `onto-canon6`;
3. one bare-extraction baseline over the same corpus;
4. one fixed cross-document question fixture;
5. documentation and run-note closure.

Scale-out beyond this corpus remains outside the block and stays under
`0025a_entity_resolution_scale_out.md`.

## Pre-Made Decisions

1. The official Phase 4 value-proof corpus is the existing synthetic
   military/OSINT corpus under `tests/fixtures/synthetic_corpus`.
2. Work stays in the isolated worktree branch
   `codex/onto-canon6-integration-planning`.
3. Ground-truth scoring is pairwise over extracted promoted entities that can
   be matched to the ground-truth registry; unmatched extracted entities are
   tracked explicitly, not silently discarded.
4. The first decision-grade report must include:
   - precision
   - recall
   - false-merge pairs
   - false-split pairs
   - unmatched extracted entities
5. The bare baseline is a simple structured extraction path over the same
   corpus with no ontology governance, no review workflow, and no identity
   resolution.
6. The cross-document question set is a checked-in JSON fixture, not an
   implicit notebook-only artifact.
7. The first guaranteed run order is:
   - exact strategy
   - bare baseline
   - LLM strategy if the runtime environment supports it cleanly
8. Every verified phase gets its own commit.
9. Uncertainties are logged in the plan or `TODO.md`, but execution continues
   unless a real blocker prevents safe implementation.

## Frozen Evaluation Rules

The first decision-grade evaluator uses these exact rules:

1. Observations are promoted graph entities enriched with:
   - observed mention names recovered from promoted assertion role fillers;
   - source document refs recovered from the review DB;
   - predicted cluster ids from the identity subsystem, with singleton fallback
     to `entity_id` when no identity exists.
2. Ground-truth matching is name-first:
   - normalize observed names and ground-truth variants with the same
     `_normalize_name()` logic used by auto-resolution;
   - gather all ground-truth candidates whose normalized variants match;
   - apply entity-type compatibility as a hard filter when the observation has
     an explicit type.
3. If multiple same-type candidates remain, use source-doc overlap as a
   tiebreaker:
   - choose the unique candidate with the highest overlap count if that count
     is greater than zero;
   - otherwise mark the observation `ambiguous`.
4. Observations with no unique ground-truth match remain explicit as
   `unmatched` or `ambiguous`. They are tracked in the report and are not
   silently folded into precision/recall.
5. Pairwise precision/recall are computed only over uniquely matched
   observations:
   - predicted positive pair = two observations in the same predicted cluster;
   - gold positive pair = two observations matched to the same ground-truth
     entity;
   - false merge = predicted positive but gold negative;
   - false split = gold positive but predicted negative.
6. Fixed-question scoring uses the matched observation set:
   - `same_entity` requires both mentions to resolve to unique predicted
     clusters;
   - `canonical_entity` requires the mention to resolve to a unique matched
     ground-truth entity;
   - unanswered questions remain explicit and lower answer-rate metrics.

## Baseline Report Shape

The bare baseline and the governed resolution path must converge on the same
top-level artifact shape:

1. run metadata:
   - strategy
   - timestamp
   - db/output path
2. ground-truth summary:
   - entity count
   - expected merge count
   - expected non-merge count
3. observation list:
   - entity id / cluster id
   - observed names
   - source refs
   - match status / matched ground-truth id
4. pairwise metrics:
   - matched / unmatched / ambiguous counts
   - predicted positives
   - gold positives
   - true positives
   - false positives
   - false negatives
   - precision / recall
   - concrete false-merge / false-split pairs
5. question summary and per-question scores

## Phase Order

### Phase 1: Freeze Corpus And Evaluation Contracts

Implement the missing fixtures and contract decisions so the rest of the block
has no hidden stop points.

#### Tasks

1. add a fixed cross-document question fixture for the official corpus;
2. document the exact evaluation rules for:
   - entity-resolution mapping
   - pairwise precision/recall
   - false merges / false splits
   - unmatched extracted entities
3. define the baseline report shape and where it will be written.

#### Success criteria

1. the official corpus is explicit;
2. the scoring rules are precise enough to implement without guesswork;
3. the question set is checked in and versioned.

### Phase 2: Implement Decision-Grade Evaluator

Add one shared evaluation module plus deterministic tests.

#### Tasks

1. implement typed ground-truth + result models;
2. implement matching from extracted promoted entities to ground-truth entities;
3. implement pairwise precision/recall and false-merge / false-split reporting;
4. implement question-fixture loading and deterministic answer scoring helpers;
5. add evaluation-unit tests.

#### Success criteria

1. the evaluator can score a promoted graph DB against ground truth;
2. tests cover the core matching and metrics logic;
3. no structural-only "identity count" placeholder remains the only metric.

### Phase 3: Upgrade Runners And Operator Surface

Wire the evaluator into reproducible scripts and Make targets.

#### Tasks

1. upgrade `scripts/run_scale_test.py` to emit decision-grade metrics;
2. add a bare-baseline corpus runner over the same fixture;
3. add or update Make targets for the value-proof surface;
4. ensure outputs land in `docs/runs/`.

#### Success criteria

1. exact and LLM runs can emit decision-grade reports;
2. the bare baseline emits a comparable artifact shape;
3. an operator can run the value-proof surfaces without reconstructing flags.

### Phase 4: Execute The First Full Value-Proof Slice

Run the official corpus through the upgraded surface and record the outcome.

#### Tasks

1. run the exact-strategy value-proof report;
2. run the bare baseline on the same corpus;
3. run the LLM strategy if the environment supports it without new blockers;
4. write a run note summarizing:
   - metrics
   - key false merges / false splits
   - whether LLM clustering beats the cheaper path clearly enough

#### Success criteria

1. at least the exact-strategy report and bare baseline report exist;
2. the run note is concrete enough to support a strategy decision;
3. if the LLM run is blocked, the blocker is explicit and localized.

### Phase 5: Closeout

Refresh top-level status/plan surfaces to reflect the landed value-proof block.

#### Tasks

1. update `0025`, `0024`, `CLAUDE.md`, `docs/STATUS.md`, and `HANDOFF.md`;
2. mark this block complete when all required phases land;
3. update `TODO.md` so the next unresolved frontier is explicit.

#### Success criteria

1. the repo no longer describes Plan 0025 as "metrics missing" if they landed;
2. top-level docs point at the current evidence and next work truthfully;
3. the worktree is left clean with committed checkpoints only.

## Failure Modes

1. the block stops at new scripts without real runs;
2. pairwise scoring is hand-wavy or silently drops ambiguous cases;
3. the baseline comparison is so different in shape that it cannot inform a
   strategy decision;
4. the run note reports totals only and omits the concrete false-merge /
   false-split evidence.

## Exit Criteria

This block is complete only when:

1. all five phases above meet their success criteria;
2. the worktree is clean;
3. the repo contains committed code, fixtures, run artifacts, and docs for the
   value-proof surface.

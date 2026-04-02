# 24h Entity Resolution Rerun Stability Block

Status: complete
Phase status:
- Phase 1 completed
- Phase 2 completed
- Phase 3 completed
- Phase 4 completed
- Phase 5 completed

Last updated: 2026-04-01
Workstream: convert the best `0038` rerun into a repeatable fresh-run result

## Purpose

Plan 0038 proved that the repo can get very close to the gate on a fresh rerun,
but it also exposed a new blocker: rerun stability across extraction-shape
drift.

Two fresh reruns now define the outgoing truth from `0038`:

1. `docs/runs/scale_test_llm_2026-04-01_131124.json`
   - precision `1.00`
   - recall `0.9756`
   - false merges `0`
   - false splits `2`
   - answer rate `0.80`
   - accuracy over all questions `0.80`
   - remaining misses: `Washington` place-family split and `Gen. J. Smith`
     evaluator ambiguity
2. `docs/runs/scale_test_llm_2026-04-01_132119.json`
   - precision `1.00`
   - recall `0.9009`
   - false merges `0`
   - false splits `11`
   - answer rate `0.80`
   - accuracy over all questions `0.80`
   - reopened misses: `the Agency`, `4th POG`, `D.C.`, and `GWU`

The core problem is no longer just one alias family. Fresh reruns can still
change the extraction surface enough to reopen resolution/evaluation misses even
when the deterministic resolution layer improved.

This block owns that rerun-stability problem.

## Scope

This block intentionally covers only:

1. deterministic normalization / bridge logic for extraction-shape drift that
   reopens known alias families (`D.C.`, `4th POG`, `the Agency`);
2. bounded measurement or lookup hardening only when the runtime state is
   already correct and the evaluator is what drifted;
3. documenting whether `GWU` remains an entity-resolution problem or is now an
   upstream extraction problem that must move to Plan `0014`;
4. at least two fresh reruns on new DBs with `LLM_CLIENT_TIMEOUT_POLICY=allow`;
5. truthful closeout in `0025`, `CLAUDE.md`, `docs/STATUS.md`, `HANDOFF.md`,
   `KNOWLEDGE.md`, `docs/plans/CLAUDE.md`, and `TODO.md`.

Out of scope:

1. broad prompt redesign without first proving the residual is upstream;
2. consumer-boundary or DIGIMON work;
3. query/browse widening;
4. scale-out work from `0025a`.

## Pre-Made Decisions

1. Work stays in the isolated `codex/onto-canon6-integration-planning`
   worktree.
2. The canonical incoming comparison pair is:
   - `docs/runs/scale_test_llm_2026-04-01_131124.json`
   - `docs/runs/scale_test_llm_2026-04-01_132119.json`
3. The new question is stability, not best-case cherry-picking.
4. If a residual is shown to be upstream extraction non-determinism rather than
   entity-resolution logic, record that explicitly and move it to Plan `0014`
   instead of forcing more resolution heuristics.
5. Every verified phase gets its own commit.

## Gate

This block succeeds only if:

1. two consecutive fresh reruns on new DBs are measurement-valid;
2. both reruns keep false merges at `0`;
3. both reruns keep precision at or above `0.95`;
4. both reruns answer all `10/10` fixed questions correctly; or
5. any remaining miss is explicitly shown to be outside entity resolution and
   handed off to Plan `0014` with evidence.

## Frozen Incoming Residual Contract

The instability families now frozen for this block are:

1. place abbreviation drift:
   - `Washington D.C.`
   - `D.C.`
   - `Washington`
2. acronymized military-unit alias drift:
   - `4th PSYOP Group`
   - `4th POG`
3. descriptor alias drift:
   - `CIA`
   - `Central Intelligence Agency`
   - `the Agency`
4. composite acronym carrier drift:
   - `George Washington University`
   - `GWU`
   - `researchers at GWU`

## Phase Order

### Phase 1: Freeze The Rerun-Stability Contract

#### Tasks

1. close Plan `0038` truthfully in the docs;
2. activate Plan `0039` in `CLAUDE.md`, the plans index, `0025`, `TODO.md`,
   and top-level trackers;
3. freeze the incoming artifact pair and the residual families above.

#### Success criteria

1. active docs point at `0039` as the current block;
2. the rerun-stability problem is explicit enough to execute without new
   questions.

Progress note:

1. completed in commit `0af9a12`, which closed `0038` truthfully, activated
   `0039`, and checked in the canonical incoming artifact pair.

### Phase 2: Recover Deterministic Alias Bridges For Reopened Runtime Families

#### Tasks

1. localize which reopened families can still be handled honestly in the
   deterministic resolution layer;
2. land bounded repairs for:
   - unknown `D.C.` / district-place drift
   - `4th POG` / `4th PSYOP Group` alias drift
   - descriptor alias drift only if the runtime evidence is explicit
3. add or update targeted regression tests for each landed repair.

#### Success criteria

1. targeted tests pass;
2. the repairs are family-level, not benchmark-id specific;
3. the zero-false-merge floor stays green.

Progress note:

1. commit `f9ad185` landed the first bounded repair slice:
   - unknown `D.C.` now has a bounded district-place bridge back into the
     `Washington D.C.` family;
   - `4th POG` now shares a bounded alias signature with
     `4th PSYOP Group`;
   - `4th POG(A)` remains separate.
2. fresh rerun `docs/runs/scale_test_llm_2026-04-01_145141.json` proved the
   bounded `D.C.` / `4th POG` repair slice is effective on a new DB:
   - precision `1.00`
   - recall `0.9643`
   - false merges `0`
   - false splits `4`
   - answer rate `1.00`
   - accuracy over all questions `1.00`
3. descriptor-alias drift is still not pre-approved for broader deterministic
   bridge logic. The remaining false-split family is `the Agency` versus
   `CIA` / `Central Intelligence Agency`, and the current residual is still a
   descriptor-only mention without a same-source anchor. This block will not
   force a cross-document descriptor merge heuristic just to recover those
   non-question pairwise splits.

### Phase 3: Classify Composite-Acronym Residuals Honestly

#### Tasks

1. determine whether `GWU` is still a resolution/evaluator problem or has
   become an upstream extraction-shape problem;
2. if it is still in resolution scope, land one bounded repair;
3. if it is upstream, record the evidence and hand it off to Plan `0014`
   instead of forcing another resolution heuristic.

#### Success criteria

1. the repo no longer treats `GWU` as an unspecified residual;
2. the owning plan is explicit and justified by evidence.

Current classification:

1. fresh rerun `145141` emitted a standalone `George Washington University`
   mention again, and `q09` returned to answered-and-correct. `GWU` is
   therefore no longer an open residual for this block.
2. `researchers at GWU` remains an unmatched extraction shape in the same rerun,
   but it is no longer blocking question scoring and does not justify more
   entity-resolution heuristics inside this block.
3. `the Agency` remains a descriptor-only false-split family in `145141`, but
   it no longer blocks any fixed question. The owned question-answerability
   problem is therefore cleared; any future attempt to merge descriptor-only
   mentions across documents should be treated as higher-risk work, not as a
   prerequisite for closing this block.

### Phase 4: Prove Fresh-Run Stability

#### Tasks

1. run two fresh reruns on new DBs with timeout policy enabled;
2. compare both artifacts against the gate;
3. localize any remaining instability by family and owning layer.

#### Success criteria

1. two fresh artifacts exist under `docs/runs/`;
2. the comparison is sufficient to decide whether stability is achieved.

Progress note:

1. first fresh rerun `docs/runs/scale_test_llm_2026-04-01_145141.json` is now
   in hand and clears the question-level gate on a new DB while preserving the
   zero-false-merge floor.
2. second fresh rerun `docs/runs/scale_test_llm_2026-04-01_152927.json` also
   cleared the question-level gate on a new DB:
   - precision `1.00`
   - recall `0.9346`
   - false merges `0`
   - false splits `7`
   - answer rate `1.00`
   - accuracy over all questions `1.00`
3. the rerun-stability gate is therefore satisfied at the question/safety
   level even though pairwise false splits still drift across fresh reruns.

### Phase 5: Closeout

#### Tasks

1. write the decision-grade stability note;
2. refresh `0025`, `CLAUDE.md`, `docs/STATUS.md`, `HANDOFF.md`,
   `KNOWLEDGE.md`, `docs/plans/CLAUDE.md`, and `TODO.md`;
3. mark this block completed.

#### Success criteria

1. top-level docs describe the stability decision truthfully;
2. the worktree is left clean with committed checkpoints only.

Progress note:

1. decision note:
   `docs/runs/2026-04-01_entity_resolution_rerun_stability.md`
2. Plan `0039` is now complete. Its gate was satisfied by the fresh rerun pair
   `145141` and `152927`.
3. the remaining false-split drift is recorded as follow-on quality work, not
   unfinished `0039` scope.

## Failure Modes

1. deterministic bridges become a dumping ground for upstream extraction drift;
2. fresh reruns are compared dishonestly by selecting only the best artifact;
3. `GWU` keeps being treated as a resolution bug when the extractor never emits
   the university entity on some runs;
4. the zero-false-merge floor regresses while chasing recall.

## Exit Criteria

This block is complete only when:

1. all five phases above meet their success criteria;
2. the worktree is clean;
3. the repo contains committed code, tests, rerun artifacts, and docs for the
   rerun-stability decision.

## Closeout Decision

Plan `0039` is complete.

Why:

1. two consecutive fresh reruns on new DBs now exist;
2. both reruns kept false merges at `0`;
3. both reruns kept precision above the declared `0.95` floor;
4. both reruns answered all `10/10` fixed questions correctly.

What remains open after closure:

1. descriptor-only `the Agency` false splits can still reopen at the pairwise
   level;
2. `Washington D.C.` / `Washington` / `D.C.` can still drift at the pairwise
   level even when the fixed question set stays green;
3. those residuals are future hardening questions, not blockers to close this
   bounded rerun-stability block.

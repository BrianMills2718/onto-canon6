# 24h Entity Resolution Clean Measurement Block

Status: active
Phase status:
- Phase 1 completed
- Phase 2 completed
- Phase 3 completed
- Phase 4 pending
- Phase 5 pending

Last updated: 2026-04-01
Workstream: clean-rerun recovery after Plan 0033 localized the remaining misses

## Purpose

Convert the Plan 0033 localization result into a gate-valid measurement.

Plan 0033 did useful work: it recovered alias-surface coverage and narrowed the
remaining failure family. But its refreshed rerun was not measurement-valid
because transient provider connectivity failures dropped 9 source documents
during extraction.

This block owns the next bounded pass:

1. make the measurement harness robust enough to recover from transient
   extraction failures without silently accepting a partial corpus;
2. fix the real institution-family compatibility miss that leaves `GWU` /
   `George Washington University` unmatched;
3. rerun on a clean corpus;
4. only if the clean rerun still leaves `q04` wrong, add one bounded
   installation-equivalence repair and rerun again;
5. write the decision-grade closeout.

## Scope

This block intentionally covers only:

1. scale-harness resilience for transient extraction failures;
2. bounded institution-family compatibility repair;
3. bounded installation-equivalence repair only if still required after a
   clean rerun;
4. one clean rerun and, if needed, one follow-up rerun after the installation
   repair;
5. plan / TODO / status / knowledge closeout.

Out of scope:

1. changing the fixed corpus, ground truth, or question fixture;
2. weakening the same-surname person safety family;
3. broad ontology-family rewrites beyond the bounded institution family;
4. DIGIMON work or query-surface work;
5. replacing the current LLM strategy with a different resolution architecture.

## Pre-Made Decisions

1. Work stays in the isolated `codex/onto-canon6-integration-planning`
   worktree.
2. Plan 0033 is treated as completed with an explicit miss localized in:
   `docs/runs/2026-04-01_entity_resolution_answerability_rerun.md`.
3. The first fix in this block is measurement hygiene, not more clustering
   heuristics.
4. The institution-family repair is pre-approved:
   `oc:university` and `oc:educational_institution` belong to the same
   conservative organization/institution resolution family.
5. Installation-equivalence logic does **not** land pre-emptively. It activates
   only if `q04` remains wrong after one clean rerun with full document
   survival.
6. Any harness retry behavior must log loudly and must still leave a run
   obviously invalid if documents remain missing after the retry pass.
7. Every verified phase gets its own commit.

## Gate

This block succeeds only if a fresh clean rerun satisfies all of the following:

1. all `25` source documents survive extraction;
2. pairwise precision stays at or above `0.95`;
3. pairwise recall stays at or above `0.60`;
4. false merges stay at or below `2`;
5. fixed-question answer rate reaches at least `0.70`;
6. fixed-question accuracy over all questions reaches at least `0.50`;
7. `q08` and `q09` are no longer unanswered;
8. `q04` is no longer wrong or, if still wrong after a clean rerun, a bounded
   installation-equivalence repair is implemented and a second clean rerun is
   recorded.

If the second clean rerun still misses the gate, the block still counts as
complete if the remaining miss is explicit and localized in the decision note.

## Phase Order

### Phase 1: Freeze The Clean-Measurement Contract

#### Tasks

1. record the Plan 0033 rerun outcome and make this block the active execution
   surface in `CLAUDE.md`, the plans index, `0025`, and `TODO.md`;
2. freeze the three remaining failure classes:
   - transient extraction-loss during measurement runs
   - institution-family mismatch (`university` / educational institution)
   - installation-equivalence only if still needed after a clean rerun
3. freeze the gate above.

#### Success criteria

1. active docs point at Plan 0034 rather than Plan 0033;
2. the stop conditions and phase order are explicit enough to implement
   without new questions.

#### Outcome

Completed on 2026-04-01.

Plan 0033 is now closed honestly, the failed-measurement rerun is recorded in
`docs/runs/2026-04-01_entity_resolution_answerability_rerun.md`, and the active
execution surfaces (`CLAUDE.md`, `docs/plans/CLAUDE.md`, `0025`, and `TODO.md`)
now point at Plan 0034.

### Phase 2: Harden Measurement Hygiene

#### Tasks

1. localize where `scripts/run_scale_test.py` records per-document extraction
   failures and how it reports them;
2. add one bounded retry pass for transient extraction failures:
   - retry only documents that failed extraction
   - log the failed-doc set before retry
   - log the residual failed-doc set after retry
3. add focused tests for the retry bookkeeping if the logic is factored into
   pure helpers; otherwise add a deterministic script-level regression test for
   the new failure summary behavior.

#### Success criteria

1. a run with transient failures does not silently look equivalent to a clean
   run;
2. the harness can retry failed docs once without manual intervention;
3. if docs still fail after retry, the run remains explicitly invalid.

#### Outcome

Completed on 2026-04-01.

Landed changes:

1. `scripts/run_scale_test.py` now has a bounded doc-level retry pass for
   transient extraction failures via `--retry-failed-docs` and
   `--retry-delay-seconds`;
2. extraction summaries now report residual failed docs and recovered docs
   explicitly instead of collapsing everything into one opaque `errors` count;
3. deterministic regression coverage now pins the retry bookkeeping in
   `tests/integration/test_run_scale_test.py`.

### Phase 3: Repair Institution-Family Compatibility

#### Tasks

1. land the bounded type-family repair so `oc:university` and
   `oc:educational_institution` match conservatively;
2. add targeted tests covering:
   - observation ↔ ground-truth type matching
   - `GWU` / `George Washington University` question answerability on the fixed
     evaluator surface
3. keep the existing same-surname and place/org family safeguards green.

#### Success criteria

1. targeted regression tests pass;
2. the repair is family-level, not benchmark-string specific;
3. `q09` can become answerable on surviving promoted observations.

#### Outcome

Completed on 2026-04-01.

Landed changes:

1. `oc:university` now resolves within the same conservative organization /
   institution family as `oc:educational_institution`;
2. targeted compatibility coverage now pins this family in
   `tests/core/test_auto_resolution.py`;
3. the evaluator surface now exercises the real surviving `George Washington
   University` / `GWU` path with `oc:university` observations in
   `tests/evaluation/test_entity_resolution_value_proof.py`.

### Phase 4: Run One Clean Rerun

#### Tasks

1. rerun the LLM strategy on a fresh DB with the new harness behavior;
2. verify `25/25` document survival directly from the DB;
3. inspect `q04`, `q08`, and `q09` in the fresh artifact;
4. if `q04` is now correct, skip Phase 5 implementation and go directly to
   closeout.

#### Success criteria

1. a fresh JSON artifact exists under `docs/runs/`;
2. the rerun is measurement-valid (`25/25` docs survive);
3. the artifact is sufficient to decide whether installation-equivalence work
   is still needed.

### Phase 5: Conditional Installation-Equivalence Repair And Closeout

#### Tasks

1. if the clean rerun still leaves `q04` wrong, localize the exact surviving
   Fort Bragg / Fort Liberty split and add one bounded installation-family
   repair;
2. rerun on a fresh DB after that repair;
3. write the decision-grade run note and refresh `0025`, `CLAUDE.md`,
   `docs/STATUS.md`, `HANDOFF.md`, `KNOWLEDGE.md`, and `TODO.md`;
4. mark this block completed.

#### Success criteria

1. either the first clean rerun clears the gate or the second rerun makes the
   remaining miss explicit and localized;
2. top-level docs describe the current decision truthfully;
3. the worktree is left clean with committed checkpoints only.

## Failure Modes

1. the harness retry pass hides partial-corpus failure instead of surfacing it
   more clearly;
2. institution-family repair broadens organization compatibility so far that it
   invites new false merges;
3. installation-equivalence logic is added before a clean rerun proves it is
   still necessary;
4. the final run note reports aggregate metrics without naming the exact
   question families that still fail.

## Exit Criteria

This block is complete only when:

1. all five phases above meet their success criteria;
2. the worktree is clean;
3. the repo contains committed code, tests, rerun artifacts, and docs for the
   clean-measurement decision.

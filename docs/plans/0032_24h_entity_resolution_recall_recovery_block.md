# 24h Entity Resolution Recall Recovery Block

Status: completed
Phase status:
- Phase 1 completed
- Phase 2 completed
- Phase 3 completed
- Phase 4 completed
- Phase 5 completed

Last updated: 2026-04-01
Workstream: bounded 24-hour recall/answerability recovery after Plan 0031

## Purpose

Convert the post-Plan-0031 entity-resolution result from "safe but still too
weak" into a stronger LLM strategy that can recover alias-heavy matches and
question answerability without reintroducing the eliminated false-merge family.

This block is complete only when the repo has:

1. removed the extraction/schema failure that dropped `doc_06` from the
   hardened LLM rerun;
2. improved deterministic or validated handling for the benchmark-critical
   alias families that still block recall and unique-cluster answerability;
3. refreshed the LLM value-proof artifact on the same fixed corpus;
4. a written decision saying whether the LLM strategy is now closer to
   promotion or still blocked.

## Scope

This block intentionally covers only:

1. extraction-boundary hardening for the same-day schema failure family
   (`kind: "event"` / invalid unknown filler shape);
2. resolution-time recall and answerability hardening for benchmark-critical
   abbreviations, acronyms, and rename/alias families;
3. the fixed synthetic corpus and question fixture from Plan 0030 / Plan 0031;
4. one fresh LLM rerun and one fresh decision note;
5. plan/TODO/status/knowledge closeout.

Out of scope:

1. scale-out beyond the synthetic corpus;
2. changing the evaluator or question fixture;
3. DIGIMON or query-surface work;
4. a new identity architecture;
5. promoting the LLM strategy by assertion alone without rerun evidence.

## Pre-Made Decisions

1. Work stays in the isolated `codex/onto-canon6-integration-planning`
   worktree.
2. `exact` remains the default precision floor unless this block's rerun clears
   the hardening gate below.
3. The same synthetic corpus and fixed question set remain authoritative.
4. The extraction/schema fix should remove document loss without inventing a
   new core filler kind. Fix the boundary or candidate-level salvage path, not
   the ontology model.
5. Alias/answerability recovery should prefer deterministic normalization,
   abbreviation expansion, and conservative validation before broader prompt
   churn.
6. The same-surname person safety guard from Plan 0031 must not be weakened.
7. Every verified phase gets its own commit.

## Recovery Gate

This block succeeds only if all of the following are true on the refreshed LLM
run:

1. extraction completes with zero document-level losses on the `25`-document
   corpus;
2. pairwise precision is at or above `0.95`;
3. pairwise recall is at or above `0.40`;
4. false merges are at or below `2`;
5. fixed-question answer rate is at or above `0.50`;
6. fixed-question accuracy over all questions is at or above `0.30`.

If those thresholds are missed, the block still counts as complete if the
remaining miss is explicit and localized in the run note.

## Phase Order

### Phase 1: Freeze The Recovery Contract

#### Tasks

1. make this block the active execution surface in `CLAUDE.md`, the plans
   index, and `TODO.md`;
2. freeze the targeted failure families:
   - extraction/schema failure that dropped `doc_06`
   - organization/installation alias splits (`USSOCOM`, `Fort Bragg`)
   - abbreviated person mention / unique-cluster failures (`Gen. Smith`,
     `Adm. Olson`)
3. freeze the recovery gate above.

#### Success criteria

1. the active docs point to this block rather than the completed Plan 0031;
2. the stop conditions and thresholds are explicit enough to implement without
   new questions.

#### Outcome

Completed on 2026-04-01.

The block is now the active execution surface in `CLAUDE.md`, the plans index,
and `TODO.md`, and the recovery gate is frozen for the next implementation
pass.

### Phase 2: Remove Extraction Document Loss

#### Tasks

1. reproduce and localize the `unsupported filler kind: 'event'` /
   malformed-unknown failure family at the extraction boundary;
2. fix the boundary so one malformed candidate no longer causes a whole
   document to disappear from the scale-test run;
3. add focused tests that prove the offending shape is handled loudly and the
   document still yields the valid candidates around it.

#### Success criteria

1. the targeted extraction tests pass;
2. the block has a concrete explanation for why `doc_06` was lost;
3. the next rerun can preserve all `25` documents unless a new explicit error
   occurs.

#### Outcome

Completed on 2026-04-01.

Landed changes:

1. `TextExtractionResponse` now drops unparseable candidate payloads before the
   whole response parse fails;
2. malformed candidates are logged loudly and the remaining valid candidates
   survive for the same document;
3. targeted extraction tests now pin both contracts:
   - filler-level validation still raises for malformed fillers
   - response-level parsing salvages valid candidates instead of losing the
     whole document

The concrete explanation for the Plan 0031 `doc_06` loss is now narrower:
malformed candidate payloads with unsupported filler kinds or malformed unknown
shapes were poisoning the whole response before candidate-level salvage ran.

### Phase 3: Recover Alias And Answerability Families

#### Tasks

1. improve deterministic or validated handling for benchmark-critical
   org/install/person abbreviation families;
2. add or refine tests for:
   - `USSOCOM` vs `U.S. Special Operations Command`
   - `Ft. Bragg` vs `Fort Liberty`
   - `Adm. Olson` vs `Eric Olson`
   - `Gen. Smith` / `General John Smith` unique-cluster answerability
3. keep the Plan 0031 same-surname safety family green while doing so.

#### Success criteria

1. the targeted regression tests pass;
2. the changes are general family-level fixes, not benchmark-row patches;
3. same-surname person false merges remain blocked.

#### Outcome

Completed on 2026-04-01.

Landed changes:

1. LLM output groups now go through a deterministic equivalence-collapse pass
   after the existing same-surname safety guard;
2. collapse signatures are intentionally narrow:
   - identical normalized names across clusters
   - same full person name across clusters
   - acronym/long-form organization signatures for common
     org/university/agency shapes
3. focused tests now pin the intended safe families:
   - `General John Smith` / `John Smith`
   - `USSOCOM` / `U.S. Special Operations Command`
   - acronym signature generation for `GWU`, `CIA`, and `USSOCOM`

The Phase 3 contract stays narrow: it improves deterministic recovery for
obvious alias families without weakening the Plan 0031 same-surname split
guard.

### Phase 4: Refresh The LLM Value Proof

#### Tasks

1. rerun the LLM strategy on a fresh DB with the bounded judge and resolution
   overrides;
2. compare the rerun against Plan 0031;
3. write a new run note naming:
   - new metrics
   - whether all `25` docs survived
   - what improved
   - what still fails
   - whether LLM is promotable

#### Success criteria

1. a fresh LLM JSON artifact exists under `docs/runs/`;
2. the run note is decision-grade and references the new artifact directly;
3. if the LLM path is still not promotable, the blocking miss is concrete.

#### Outcome

Completed on 2026-04-01.

Fresh rerun artifacts now exist:

1. `docs/runs/scale_test_llm_2026-04-01_083207.json`
2. `docs/runs/2026-04-01_entity_resolution_recall_recovery_rerun.md`

The rerun cleared the bounded recovery gate:

1. all `25` source documents survived extraction;
2. precision `1.00`;
3. recall `0.615`;
4. false merges `0`;
5. answer rate `0.50`;
6. accuracy over all questions `0.40`.

This block therefore closes as a success. The remaining misses are no longer
document-loss blockers; they are narrower answerability families that now move
to the next bounded execution block.

### Phase 5: Closeout

#### Tasks

1. update `0025`, `CLAUDE.md`, `docs/STATUS.md`, `HANDOFF.md`, and
   `KNOWLEDGE.md`;
2. mark this block completed when all phases land;
3. refresh `TODO.md` so the next unresolved frontier is explicit.

#### Success criteria

1. top-level docs describe the recall-recovery result truthfully;
2. the next active work is explicit;
3. the worktree is left clean with committed checkpoints only.

#### Outcome

Completed on 2026-04-01.

The top-level docs now record Plan 0032 as complete, and the next active
bounded execution surface is Plan 0033.

## Failure Modes

1. the extraction/schema fix silently drops bad candidates or documents without
   logging the loss;
2. alias recovery is achieved by weakening the Plan 0031 safety guard;
3. the rerun note reports aggregate metrics but not document survival or
   question answerability;
4. a benchmark-specific patch makes one question pass without improving the
   broader alias family.

## Exit Criteria

This block is complete only when:

1. all five phases above meet their success criteria;
2. the worktree is clean;
3. the repo contains committed code, tests, rerun artifacts, and docs for the
   recall-recovery decision.

# 24h Full-Chunk Strict-Omit Contract Audit

Status: complete
Phase status:
- Phase 1 complete
- Phase 2 complete
- Phase 3 complete
- Phase 4 complete
- Phase 5 complete

Last updated: 2026-04-02
Workstream: audit whether the full chunk-003 strict-omit contract is still
truthful after repeated prompt-side suppression failures

## Purpose

Plans `0051` through `0053` repeatedly failed to suppress the same full-chunk
residual family by prompt wording alone. The surviving candidates overlap with
already-modeled local strict-omit cases and one explicit `JPOTF` establishment
sentence.

This block exists to answer the next question:

**Is `psyop_017_full_chunk003_analytical_context_strict_omit` still a truthful
zero-candidate benchmark contract under the current extraction goal, or has the
remaining blocker shifted into benchmark-contract mismatch?**

## Scope

This block intentionally covers only:

1. benchmark case
   `psyop_017_full_chunk003_analytical_context_strict_omit`;
2. its relationship to the local strict-omit cases already in the fixture;
3. the current broad extraction goal used by the prompt-eval harness;
4. decision documentation for whether the contract should stay or change.

Out of scope:

1. new prompt revisions before the audit result is written;
2. review/judge policy changes;
3. broad multi-case benchmark reruns;
4. changing fixture expectations without an explicit audit-backed decision

## Pre-Made Decisions

1. Work stays in the isolated `codex/onto-canon6-integration-planning`
   worktree.
2. The incoming decision note is:
   `docs/runs/2026-04-02_abstract_result_and_citation_decision.md`.
3. Do not assume the fixture is wrong or right; prove it from repo evidence.
4. The audit must compare chunk `017` against the already-modeled local
   negative controls (`008` through `016`) before recommending any change.
5. If the audit concludes the contract is ambiguous, record that explicitly and
   stop short of changing the benchmark fixture without user sign-off.

## Gate

This block succeeds only if:

1. the repo has one explicit written answer to whether chunk `017` should
   remain strict omit;
2. that answer is backed by artifact evidence and local-case comparison;
3. any required user decision is isolated narrowly.

## Phase Order

### Phase 1: Freeze The Contract Question

#### Tasks

1. freeze the `0053` surviving full-chunk family;
2. enumerate the overlapping local strict-omit cases that already model the
   same failure families.

#### Success criteria

1. the audit target is explicit and bounded;
2. overlapping local cases are named concretely.

### Phase 2: Compare Full-Chunk Contract To Local Controls

#### Tasks

1. compare the surviving full-chunk candidate families to local strict-omit
   cases `008` through `016`;
2. decide whether chunk `017` is:
   - redundant aggregation of known strict-omit patterns,
   - a valid full-chunk negative control,
   - or a mixed-content case that conflicts with the broad extraction goal.

#### Success criteria

1. the full-chunk contract is classified into one of those buckets;
2. the classification is artifact-backed.

### Phase 3: Define The Allowed Next Moves

#### Tasks

1. write the explicit option set if the contract is ambiguous:
   - keep strict omit and harden extractor
   - split/remove the full chunk case
   - convert to accepted alternatives
   - narrow the extraction goal
2. pre-state which options require user sign-off.

#### Success criteria

1. the repo has an unambiguous option set;
2. user-decision boundaries are explicit.

### Phase 4: Record The Audit Result

#### Tasks

1. write the audit decision note;
2. update the active extraction-quality plan to point at the real blocker.

#### Success criteria

1. one dominant audit result is named;
2. it is linked from the active plan stack.

### Phase 5: Closeout

#### Tasks

1. refresh `CLAUDE.md`, `HANDOFF.md`, `KNOWLEDGE.md`, `TODO.md`,
   `docs/STATUS.md`, and `docs/plans/CLAUDE.md`;
2. either activate the next implementation block or stop with one narrow user
   decision request if the fixture contract itself needs sign-off.

#### Success criteria

1. the next step is explicit;
2. any required user input is narrowed to one contract decision.

## Exit Criteria

This block is complete only when:

1. all five phases above meet their success criteria;
2. the worktree is clean;
3. the repo contains a committed contract-audit note and updated plan stack.

## Outcome

Plan `0054` is complete.

The audit result is explicit:

1. chunk `017` is not a clean full-chunk negative control anymore;
2. it re-aggregates several already-modeled local strict-omit families; and
3. it also contains explicit factual sentences that are not obviously strict
   omit under the broad extraction goal.

Audit artifact:

- `docs/runs/2026-04-02_full_chunk_strict_omit_contract_audit.md`

The next step is now a narrow user contract decision, not another autonomous
prompt or runtime tweak.

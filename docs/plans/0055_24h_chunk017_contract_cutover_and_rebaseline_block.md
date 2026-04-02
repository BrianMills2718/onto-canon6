# 24h Chunk-017 Contract Cutover And Rebaseline Block

Status: complete
Phase status:
- Phase 1 complete
- Phase 2 complete
- Phase 3 complete
- Phase 4 complete

Last updated: 2026-04-02
Workstream: extraction-quality contract cutover after the chunk-017 audit

## Purpose

Plan `0054` proved that
`psyop_017_full_chunk003_analytical_context_strict_omit`
is not a truthful zero-candidate control under the current broad extraction
goal. The user approved the recommended contract action:

1. remove/demote chunk `017` as a strict-omit gate; and
2. rely on the cleaner local strict-omit controls `008` through `016`.

This block exists to make that approval real in the repo, rerun the bounded
benchmark on the corrected fixture, and state the next blocker honestly.

## Scope

This block intentionally covers only:

1. the benchmark fixture and service tests that still encode chunk `017` as a
   zero-candidate gate;
2. the active extraction-quality and authority docs that still say a user
   decision is pending;
3. one bounded prompt-eval rerun on the corrected fixture;
4. one decision note that states the next extraction-quality blocker after the
   cutover.

Out of scope:

1. new prompt wording changes;
2. review/judge policy changes;
3. new real-chunk transfer runs;
4. changing the broad extraction goal itself.

## Pre-Made Decisions

1. Work stays in the isolated `codex/onto-canon6-integration-planning`
   worktree.
2. The benchmark contract change is already decided. Do not reopen whether
   chunk `017` should remain strict omit.
3. The fixture change will be expressed as a new fixture revision rather than
   silently mutating the old contract in place.
4. Chunk `017` is removed from the strict-omit benchmark fixture instead of
   being converted to accepted alternatives in this block.
5. The local strict-omit controls `008` through `016` remain the authoritative
   negative controls for this failure family.
6. The rerun stays bounded to the prompt-eval experiment surface already used
   by Plan `0014`; this block does not certify live promotion.
7. If the corrected rerun still shows the compact operational-parity lane as
   non-promotable, record the next blocker explicitly instead of starting a new
   repair block inside this plan.

## Gate

This block succeeds only if:

1. the fixture and tests no longer encode chunk `017` as a strict-omit case;
2. the active docs no longer claim a pending user decision on chunk `017`;
3. one bounded prompt-eval rerun exists on the corrected fixture; and
4. the repo records one explicit next blocker after the corrected rerun.

## Phase Order

### Phase 1: Freeze The Approved Contract

#### Tasks

1. create this cutover plan and make it the active 24h extraction block;
2. update `CLAUDE.md`, `docs/plans/CLAUDE.md`, `TODO.md`, and
   `docs/plans/0014_extraction_quality_baseline.md` so they no longer say a
   user decision is pending;
3. record the approved contract action as:
   "chunk `017` removed from the strict-omit gate; local controls `008`-`016`
   remain authoritative."

#### Success criteria

1. the authority docs point at Plan `0055`, not Plan `0054`, as the active
   extraction block;
2. no active doc still says chunk `017` is waiting on user sign-off.

### Phase 2: Cut Over The Fixture And Tests

#### Tasks

1. remove chunk `017` from `tests/fixtures/psyop_eval_slice.json`;
2. bump the fixture id to a new revision;
3. update the benchmark service test so it validates the corrected fixture
   contract truthfully.

#### Success criteria

1. the fixture has one fewer case and no chunk-017 strict-omit record;
2. the service-level benchmark tests pass on the corrected contract.

### Phase 3: Rebaseline The Corrected Benchmark

#### Tasks

1. run one bounded extraction prompt experiment against the corrected fixture;
2. save the JSON report under `docs/runs/`;
3. write a short decision note that states whether the corrected fixture
   changes the promotion posture or only removes a benchmark-contract
   distortion.

#### Success criteria

1. one corrected-fixture rerun artifact exists;
2. the repo has one written answer about what the next blocker is after the
   contract cutover.

### Phase 4: Closeout

#### Tasks

1. update `HANDOFF.md`, `docs/STATUS.md`, `KNOWLEDGE.md`, and
   `docs/plans/CLAUDE.md`;
2. mark this block complete only if the rerun and blocker note both exist;
3. either activate the next bounded extraction-quality block or leave the next
   blocker explicitly under Plan `0014`.

#### Success criteria

1. the next step is explicit;
2. the worktree is clean;
3. the plan stack is truthful.

## Exit Criteria

This block is complete only when:

1. all four phases above meet their success criteria;
2. the corrected fixture and tests are committed;
3. the corrected-fixture rerun artifact and blocker note are committed; and
4. the worktree is clean.

## Outcome

Plan `0055` is complete.

Artifacts:

1. `docs/runs/2026-04-02_chunk017_cutover_prompt_eval_report.json`
2. `docs/runs/2026-04-02_chunk017_contract_cutover_decision.md`

Result:

1. chunk `017` is removed from the strict-omit gate in fixture `v6`;
2. the corrected rerun proved the contract distortion is gone; but
3. the compact operational-parity lane remains non-promotable because the real
   residual family is now `001`, `002`, `007`, and `008`.

The next active block is:

- `docs/plans/0056_24h_corrected_fixture_semantic_recovery_block.md`

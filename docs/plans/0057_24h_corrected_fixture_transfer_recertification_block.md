# 24h Corrected-Fixture Transfer Recertification Block

Status: complete
Phase status:
- Phase 1 complete
- Phase 2 complete
- Phase 3 complete
- Phase 4 complete
- Phase 5 complete

Last updated: 2026-04-02
Workstream: live chunk-transfer recertification after corrected-fixture benchmark recovery

## Purpose

Plan `0056` restored the compact operational-parity lane to the top score on
the corrected benchmark fixture, but Plan `0014` still requires named real
chunk-transfer evidence before promotion.

This block exists to rerun the two canonical transfer chunks with the improved
compact prompt and decide whether the lane is now promotable or still blocked on
live chunk behavior.

## Scope

This block intentionally covers only:

1. live `extract-text` runs for the two named transfer chunks;
2. reviewed transfer reports for those two chunks;
3. one decision note that compares the new reports to the existing transfer
   posture.

Out of scope:

1. new benchmark cases;
2. new prompt-eval experiments;
3. broad review-policy changes;
4. changing the named transfer chunks.

## Pre-Made Decisions

1. Work stays in the isolated `codex/onto-canon6-integration-planning`
   worktree.
2. The canonical transfer chunks remain:
   - `chunk_002` as the positive control
   - `chunk_003` as the prose-heavy stress case
3. The live prompt override for this block is:
   - template:
     `prompts/extraction/text_to_candidate_assertions_compact_v5.yaml`
   - prompt ref:
     `onto_canon6.extraction.text_to_candidate_assertions_compact_v5@2`
4. The selection task remains `budget_extraction`.
5. Use one fresh review DB for this block under a dedicated `var/real_runs/...`
   directory.
6. This block may end either with improved transfer evidence or with a truthful
   statement that chunk `003` is still the blocker.
7. The frozen runtime paths for this block are:
   - run root:
     `var/real_runs/2026-04-02_corrected_fixture_transfer_recertification/`
   - review DB:
     `var/real_runs/2026-04-02_corrected_fixture_transfer_recertification/review_state.sqlite3`
   - chunk `002` input:
     `/home/brian/projects/onto-canon6/var/real_runs/2026-03-21_phase_b_prompt_verification/chunks/01_stage1_query2/01_stage1_query2__chunk_002.md`
   - chunk `003` input:
     `/home/brian/projects/onto-canon6/var/real_runs/2026-03-21_phase_b_prompt_verification/chunks/01_stage1_query2/01_stage1_query2__chunk_003.md`
   - chunk `002` source ref:
     `text://phase-b/2026-04-02/01_stage1_query2/chunk_002_compact_v5r2`
   - chunk `003` source ref:
     `text://phase-b/2026-04-02/01_stage1_query2/chunk_003_compact_v5r2`

## Gate

This block succeeds only if:

1. both named chunks are rerun live with the improved prompt override;
2. both reviewed chunk-transfer reports exist;
3. the repo states clearly whether the lane is now promotable or still blocked.

## Phase Order

### Phase 1: Freeze The Transfer Contract

#### Tasks

1. restate the `0056` result as the incoming contract;
2. define the fresh run directory, review DB path, source refs, and report
   artifact paths;
3. keep the prompt override/ref explicit.

#### Success criteria

1. the live transfer runtime contract is frozen;
2. the output paths are explicit.

### Phase 2: Rerun Chunk 002 Positive Control

#### Tasks

1. run `extract-text` on the named chunk-002 source with the improved prompt;
2. export the reviewed candidate snapshot if needed;
3. export the chunk-transfer report.

#### Success criteria

1. one reviewed chunk-002 transfer report exists;
2. the positive-control verdict is explicit.

### Phase 3: Rerun Chunk 003 Stress Case

#### Tasks

1. run `extract-text` on the named chunk-003 source with the improved prompt;
2. export the reviewed candidate snapshot if needed;
3. export the chunk-transfer report.

#### Success criteria

1. one reviewed chunk-003 transfer report exists;
2. the stress-case verdict is explicit.

### Phase 4: Classify Promotion Posture

#### Tasks

1. compare the new chunk reports against the standing Plan `0014` promotion
   gate;
2. decide whether the lane is promotable, still transfer-blocked, or newly
   mixed.

#### Success criteria

1. the promotion posture is explicit;
2. the blocker is named if the lane is still not promotable.

### Phase 5: Closeout

#### Tasks

1. write the decision note;
2. refresh `CLAUDE.md`, `TODO.md`, `HANDOFF.md`, `docs/STATUS.md`,
   `docs/plans/CLAUDE.md`, and `docs/plans/0014_extraction_quality_baseline.md`;
3. mark the block complete only when the worktree is clean.

#### Success criteria

1. the result is decision-grade;
2. the worktree is clean;
3. the next step is explicit.

## Outcome

This block reran both named live chunks, but it did not certify the lane as
promotable.

1. chunk `002` remained a clean positive control under the corrected compact
   prompt;
2. chunk `003` produced a nominally positive transfer report; but
3. that positive verdict was not trustworthy once compared against corrected
   benchmark fixture `v6`.

The decisive mismatch is semantic, not bookkeeping:

1. chunk-003 accepted `oc:limit_capability` and `oc:express_concern`
   candidates that restate the same abstract evaluative prose now covered by
   strict-omit controls `011`, `012`, `015`, and `016`;
2. the transfer report classifies success only from accepted/rejected counts;
3. the live `review_mode: llm` path currently auto-accepts
   `partially_supported` candidates as if they were fully supported; and
4. the live judge prompt does not yet encode the corrected omit semantics
   strongly enough for analytical-prose chunk transfer.

Decision:

1. Plan `0057` is complete as a truthful recertification audit;
2. the compact operational-parity lane is still **not promotable**; and
3. the next owned block is review-contract alignment, not another transfer
   summary.

The successor active plan is Plan `0058`.

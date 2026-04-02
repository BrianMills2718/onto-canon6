# 24h Default Extraction Cutover Block

Status: complete
Phase status:
- Phase 1 completed
- Phase 2 completed
- Phase 3 completed
- Phase 4 completed
- Phase 5 completed

Last updated: 2026-04-02
Workstream: promote the proved compact operational-parity lane into the repo
default extraction surface

## Purpose

Plans `0057` through `0061` narrowed and then cleared the named real-chunk
transfer blocker families. The next question is no longer whether the compact
operational-parity lane can survive the current transfer gate. It is whether
the proved candidate should replace the current repo-default extraction
configuration.

This block owns only that promotion/cutover decision and its bounded default
surface changes.

## Scope

This block intentionally covers only:

1. promotion certification for the current compact operational-parity lane;
2. the minimal config/default changes needed to make it the repo default;
3. targeted tests for those default-surface changes; and
4. one no-override live verification on chunk `002` and chunk `003`.

Out of scope:

1. new prompt experimentation;
2. new benchmark fixture changes;
3. broader extraction redesign; and
4. widening beyond the current proved candidate.

## Pre-Made Decisions

1. Work stays in the isolated `codex/onto-canon6-integration-planning`
   worktree.
2. The candidate being evaluated is fixed:
   - `selection_task: budget_extraction`
   - `prompt_template: prompts/extraction/text_to_candidate_assertions_compact_v5.yaml`
   - `prompt_ref: onto_canon6.extraction.text_to_candidate_assertions_compact_v5@3`
3. The live review contract from Plan `0058` stays frozen.
4. The live-path guards from Plans `0060` and `0061` stay in place.
5. Chunk `002` remains the positive real-chunk control.
6. Chunk `003` remains the corrected-contract prose-heavy stress case.
7. The fresh no-override verification root for this block is:
   - `var/real_runs/2026-04-02_default_extraction_cutover/`

## Gate

This block succeeds only if:

1. the promotion record is explicit and cites both benchmark and real-chunk
   transfer evidence;
2. repo-default extraction config points at the proved candidate rather than
   the legacy default surface;
3. targeted tests cover the new defaults; and
4. a fresh no-override live rerun keeps chunk `002` positive and chunk `003`
   free of accepted spillover.

## Phase Order

### Phase 1: Freeze The Promotion Contract

#### Tasks

1. close Plan `0061` truthfully;
2. freeze the exact candidate to be promoted; and
3. restate the benchmark and transfer artifacts that justify the cutover.

#### Success criteria

1. the candidate and evidence base are explicit; and
2. the new block is active in the authority docs.

### Phase 2: Change The Repo Defaults

#### Tasks

1. update repo-default extraction config to the proved candidate;
2. keep the cutover minimal: selection task plus prompt template/ref only; and
3. avoid unrelated config churn.

#### Success criteria

1. the repo-default extraction surface now points at the promoted candidate; and
2. the change remains narrow and reviewable.

### Phase 3: Verify The Default Surface

#### Tasks

1. update targeted tests for config/default extraction behavior; and
2. run the narrow verification slice before fresh live reruns.

#### Success criteria

1. targeted tests pass; and
2. default-surface behavior is visible in local verification.

### Phase 4: Rerun Chunk 002 And Chunk 003 Without Overrides

#### Tasks

1. rerun chunk `002` with repo defaults and no prompt/selection-task override;
2. rerun chunk `003` under the same fresh DB;
3. export both transfer reports; and
4. confirm the no-override default path preserves the proved transfer posture.

#### Success criteria

1. fresh no-override rerun artifacts exist;
2. chunk `002` remains positive; and
3. chunk `003` has no accepted spillover family.

### Phase 5: Closeout

#### Tasks

1. write the promotion/cutover decision note;
2. refresh `CLAUDE.md`, `TODO.md`, `HANDOFF.md`, `docs/STATUS.md`,
   `docs/plans/CLAUDE.md`, `docs/plans/0014_extraction_quality_baseline.md`,
   and `KNOWLEDGE.md`; and
3. mark the block complete only when the worktree is clean.

#### Success criteria

1. the repo-default promotion posture is explicit and decision-grade; and
2. the worktree is clean.

## Outcome

This block completed its owned job. The proved compact operational-parity lane
is now the repo-default extraction surface.

What changed:

1. repo-default extraction config now points at the compact operational-parity
   candidate (`budget_extraction` plus `text_to_candidate_assertions_compact_v5@3`);
2. targeted config/pipeline tests now enforce those defaults; and
3. a fresh no-override rerun under
   `var/real_runs/2026-04-02_default_extraction_cutover/` preserved the
   desired transfer posture: chunk `002` stayed positive and chunk `003`
   stayed free of accepted spillover.

Decision:

1. Plan `0062` is complete and truthful; and
2. there is no active extraction-transfer cleanup block remaining under
   Plan `0014`.

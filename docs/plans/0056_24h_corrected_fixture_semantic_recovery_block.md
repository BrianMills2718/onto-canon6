# 24h Corrected-Fixture Semantic Recovery Block

Status: complete
Phase status:
- Phase 1 complete
- Phase 2 complete
- Phase 3 complete
- Phase 4 complete
- Phase 5 complete

Last updated: 2026-04-02
Workstream: extraction-quality semantic recovery after chunk-017 contract cutover

## Purpose

Plan `0055` removed the mixed-content chunk-017 distortion and reran the
corrected benchmark fixture. That rerun proved the remaining blocker is a
narrower semantic family under `compact_operational_parity`:

1. `psyop_001_designation_change`
2. `psyop_002_concerns_about_truth_based_shift`
3. `psyop_007_named_institutional_concern`
4. `psyop_008_jpotf_establishment_not_org_form`

This block exists to recover those residuals without regressing the now-clean
strict-omit controls.

## Scope

This block intentionally covers only:

1. the corrected benchmark fixture `psyop_eval_slice_v6`;
2. the compact operational-parity prompt lane and its live-aligned compact
   prompt sibling;
3. the residual benchmark cases `001`, `002`, `007`, and `008`;
4. one focused rerun and one corrected-fixture rerun.

Out of scope:

1. new benchmark cases;
2. live chunk-transfer certification;
3. review/judge policy changes;
4. benchmark-goal changes.

## Pre-Made Decisions

1. Work stays in the isolated `codex/onto-canon6-integration-planning`
   worktree.
2. `psyop_eval_slice_v6` remains frozen during this block.
3. Cases `005`, `006`, and `009` through `016` are regression guards and must
   not be weakened to improve the residual cases.
4. Prompt changes must be mirrored across:
   - `prompts/extraction/prompt_eval_text_to_candidate_assertions_compact_operational_parity_v3.yaml`
   - `prompts/extraction/text_to_candidate_assertions_compact_v5.yaml`
5. This block may improve the lane or prove that one more bounded semantic
   attempt still fails. Either outcome is acceptable if documented truthfully.

## Gate

This block succeeds only if:

1. the repo has one explicit bounded attempt against cases `001`, `002`, `007`,
   and `008`;
2. the strict-omit regression guards remain intact;
3. the corrected-fixture rerun is recorded; and
4. the repo states clearly whether the lane improved enough to keep pursuing
   prompt recovery or whether a different blocker is now dominant.

## Phase Order

### Phase 1: Freeze The Residual Contract

#### Tasks

1. restate the `0055` decision as the incoming contract;
2. freeze the residual cases and current scores;
3. define the regression guard set explicitly.

#### Success criteria

1. the owned residual family is explicit;
2. the non-regression set is explicit.

### Phase 2: Localize The Remaining Semantic Failures

#### Tasks

1. compare expected vs actual outputs for `001`, `002`, `007`, and `008`;
2. classify each miss as count spillover, predicate drift, role-filler drift,
   or unsupported candidate emission;
3. decide one bounded prompt strategy that covers the family.

#### Success criteria

1. the residuals are classified concretely;
2. the next prompt change is narrow and pre-decided.

### Phase 3: Land One Bounded Prompt Revision

#### Tasks

1. update both compact prompt surfaces in lockstep;
2. extend prompt tests only as needed to pin the new instruction family;
3. keep the change bounded to the frozen residual family.

#### Success criteria

1. one bounded prompt revision is landed;
2. prompt-surface tests pass.

### Phase 4: Rerun The Focus Slice And Corrected Fixture

#### Tasks

1. run a focused rerun over cases `001`, `002`, `007`, and `008`;
2. if the focus result is not structurally broken, run one corrected-fixture
   rerun on `psyop_eval_slice_v6`;
3. save both artifacts under `docs/runs/`.

#### Success criteria

1. one focused rerun artifact exists;
2. one corrected-fixture rerun artifact exists or the focus rerun truthfully
   blocks the broader rerun;
3. the regression guards are checked explicitly.

### Phase 5: Closeout

#### Tasks

1. write the decision note;
2. refresh `CLAUDE.md`, `TODO.md`, `HANDOFF.md`, `docs/STATUS.md`,
   `docs/plans/CLAUDE.md`, and `docs/plans/0014_extraction_quality_baseline.md`;
3. either close the block with an improved lane or state the next blocker
   explicitly.

#### Success criteria

1. the result is decision-grade;
2. the worktree is clean;
3. the next step is explicit.

## Outcome

Plan `0056` is complete.

Artifacts:

1. `docs/runs/2026-04-02_corrected_fixture_focus_report.json`
2. `docs/runs/2026-04-02_corrected_fixture_full_report.json`
3. `docs/runs/2026-04-02_corrected_fixture_semantic_recovery_decision.md`

Result:

1. `compact_operational_parity` regained the benchmark lead on corrected
   fixture `v6`;
2. `psyop_008` is repaired and the strict-omit regression guards remain clean;
3. the lane is still not promotable from benchmark evidence alone because the
   named real chunk-transfer gate has not yet been rerun.

The next active block is:

- `docs/plans/0057_24h_corrected_fixture_transfer_recertification_block.md`

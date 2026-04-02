# 24h Wrapper Alignment Block

Status: complete
Phase status:
- Phase 1 completed
- Phase 2 completed
- Phase 3 completed
- Phase 4 completed
- Phase 5 completed

Last updated: 2026-04-01
Workstream: narrow the post-0043 blocker from generic live-path divergence to
prompt/render wrapper alignment

## Purpose

Plan `0043` proved:

1. the revised compact candidate still diverges on the live chunk-003 path;
2. the divergence happens before review;
3. prompt-eval and live used the same selected model; and
4. the stable remaining path difference still includes the live-vs-parity user
   wrapper.

This block exists to answer the next explicit question:

**If the live extraction path is aligned more closely to the prompt-eval user
surface, does the chunk-003 divergence narrow materially?**

## Scope

This block intentionally covers only:

1. chunk `003` as the canonical strict-omit stress case;
2. chunk `002` as a regression guard;
3. the `compact_v5` / parity `@3` candidate pair;
4. wrapper/render contract alignment experiments under the same model; and
5. one bounded live rerun under an aligned surface.

Out of scope:

1. review/judge policy rewrites before wrapper alignment is tested;
2. broader prompt rewrites unrelated to wrapper alignment;
3. entity-resolution work or consumer integration work.

## Pre-Made Decisions

1. Work stays in the isolated `codex/onto-canon6-integration-planning`
   worktree.
2. All Python execution in this block must use `PYTHONPATH=src`.
3. The incoming decision note is:
   `docs/runs/2026-04-01_live_path_divergence_decision.md`.
4. The canonical candidate pair remains:
   - `onto_canon6.extraction.text_to_candidate_assertions_compact_v5@1`
   - `onto_canon6.extraction.prompt_eval_text_to_candidate_assertions_compact_operational_parity@3`
5. The first repair lever is user-surface / wrapper alignment, not review
   policy.

## Gate

This block succeeds only if:

1. the repo can run one aligned-surface live chunk rerun;
2. the result says clearly whether wrapper alignment narrows the divergence;
3. the closeout names the next blocker family explicitly.

## Phase Order

### Phase 1: Freeze The Wrapper-Alignment Contract

#### Tasks

1. restate the `0043` decision as the incoming contract;
2. freeze the current wrapper difference artifacts;
3. freeze chunk `002` as the regression guard only.

#### Success criteria

1. the active question is now wrapper alignment, not generic divergence;
2. the current artifacts are enough to test that question directly.

Progress note:

1. the incoming decision note is now frozen in:
   `docs/runs/2026-04-01_live_path_divergence_decision.md`
2. the current wrapper-difference artifacts are explicit:
   - `docs/runs/2026-04-01_chunk002_prompt_surface_parity_v5.json`
   - `docs/runs/2026-04-01_chunk003_prompt_surface_parity_v5.json`
3. chunk `002` is now explicitly the regression guard only.

### Phase 2: Build One Aligned Surface Candidate

#### Tasks

1. define the narrowest live-prompt override that aligns the live user surface
   toward the prompt-eval wrapper;
2. keep system instructions and model selection fixed as much as possible;
3. document exactly what changed.

#### Success criteria

1. the aligned surface differs narrowly from the current live prompt;
2. the repo can explain why that surface is the right experiment.

Progress note:

1. the aligned live candidate landed as
   `prompts/extraction/text_to_candidate_assertions_compact_v6_wrapper_align.yaml`;
2. the change is intentionally narrow: only the live user wrapper was aligned
   closer to the prompt-eval `Case input:` form.

### Phase 3: Verify The Aligned Surface

#### Tasks

1. run prompt-surface comparison for the aligned candidate;
2. run one live chunk-003 rerun with the aligned surface;
3. compare the resulting output against prompt-eval and the prior live run.

#### Success criteria

1. one aligned-surface live artifact exists;
2. the effect of wrapper alignment is visible in committed artifacts.

Progress note:

1. the aligned surface artifact now exists:
   `docs/runs/2026-04-01_chunk003_prompt_surface_parity_v6.json`
2. the aligned live rerun artifacts now exist:
   - `docs/runs/2026-04-01_chunk003_transfer_report_compact6_wrapper_align.json`
   - `docs/runs/2026-04-01_chunk003_semantic_transfer_diff_compact6_wrapper_align.json`

### Phase 4: Classify The Result

#### Tasks

1. decide whether wrapper alignment materially reduced the divergence;
2. if not, name the next blocker as extraction-path behavior or review/judge
   behavior.

#### Success criteria

1. the repo exits the block with one narrower blocker family;
2. the result is backed by artifacts rather than intuition.

Progress note:

1. wrapper alignment did not reduce the divergence;
2. it widened the live-only family from `4` to `6` candidates with `0`
   shared bodies against prompt-eval.

### Phase 5: Closeout

#### Tasks

1. write the decision note;
2. refresh `CLAUDE.md`, `HANDOFF.md`, `KNOWLEDGE.md`, `TODO.md`,
   `docs/STATUS.md`, and `docs/plans/CLAUDE.md`;
3. either close this block or activate the next narrower block.

#### Success criteria

1. the next block is narrower than `0044`;
2. top-level docs truthfully reflect the new blocker family.

Progress note:

1. the decision note now exists:
   `docs/runs/2026-04-01_wrapper_alignment_decision.md`
2. the next bounded block is now explicit:
   `docs/plans/0045_24h_extraction_path_block.md`

## Failure Modes

1. the block reopens broad prompt editing instead of wrapper alignment;
2. the aligned surface quietly changes more than the wrapper contract;
3. chunk `002` regression guard disappears.

## Exit Criteria

This block is complete only when:

1. all five phases above meet their success criteria;
2. the worktree is clean;
3. the repo contains committed wrapper-alignment artifacts and a decision note.

## Closeout

Plan `0044` is complete.

It answered its bounded question honestly:

1. wrapper alignment is not the main rescue lever;
2. the live divergence survives and worsens even after that alignment;
3. the next blocker is now deeper live extraction-path behavior, tracked under
   Plan `0045`.

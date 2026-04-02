# 24h Extraction-Path Block

Status: complete
Phase status:
- Phase 1 completed
- Phase 2 completed
- Phase 3 completed
- Phase 4 completed
- Phase 5 completed

Last updated: 2026-04-01
Workstream: narrow the post-0044 blocker from wrapper alignment to live
extraction-path behavior

## Purpose

Plan `0044` proved wrapper alignment is not enough:

1. the aligned live wrapper reduced the prompt-surface delta;
2. the live chunk-003 divergence did not narrow; and
3. the aligned wrapper actually widened the live-only candidate family.

This block exists to answer the next explicit question:

**What part of the live extraction path still causes chunk-003 divergence after
wrapper alignment is ruled out?**

## Scope

This block intentionally covers only:

1. chunk `003` as the canonical stress case;
2. the current aligned wrapper candidate as the incoming live surface;
3. extraction-path behavior before review;
4. comparison between prompt-eval and live extraction-service behavior under
   the same prompt/model pair.

Out of scope:

1. review/judge policy rewrites unless extraction-path behavior is ruled out;
2. broad new prompt rewrites;
3. entity-resolution or consumer work.

## Pre-Made Decisions

1. Work stays in the isolated `codex/onto-canon6-integration-planning`
   worktree.
2. All Python execution in this block must use `PYTHONPATH=src`.
3. The incoming decision note is:
   `docs/runs/2026-04-01_wrapper_alignment_decision.md`.
4. The first repair lever is extraction-path localization, not more wrapper or
   prompt tweaking.

## Gate

This block succeeds only if:

1. the repo can name the dominant extraction-path surface still causing the
   divergence;
2. at least one reproducible diagnostic artifact exists for that surface;
3. the closeout says whether the next fix belongs in extraction-service
   behavior or review/judge behavior.

## Phase Order

### Phase 1: Freeze The Extraction-Path Contract

#### Tasks

1. restate the `0044` decision as the incoming contract;
2. freeze the current aligned-wrapper failure artifacts;
3. keep chunk `002` as the regression guard only.

#### Success criteria

1. the active blocker is no longer described as wrapper alignment;
2. the current artifacts are enough to localize the next surface.

Progress note:

1. the incoming decision note is now frozen in:
   `docs/runs/2026-04-01_wrapper_alignment_decision.md`
2. the aligned-wrapper failure artifacts are now explicit:
   - `docs/runs/2026-04-01_chunk003_prompt_surface_parity_v6.json`
   - `docs/runs/2026-04-01_chunk003_transfer_report_compact6_wrapper_align.json`
   - `docs/runs/2026-04-01_chunk003_semantic_transfer_diff_compact6_wrapper_align.json`
3. chunk `002` remains the regression guard only; chunk `003` remains the
   localization target.

### Phase 2: Compare Extraction-Service Behavior Directly

#### Tasks

1. identify the remaining path differences after wrapper alignment;
2. capture those differences in a reproducible artifact;
3. separate extraction-path behavior from review amplification.

#### Success criteria

1. the repo can point to exact extraction-path differences rather than only
   final candidate mismatches;
2. the artifact is committed and reusable.

Progress note:

1. the extraction-path comparison artifact now exists:
   `docs/runs/2026-04-02_chunk003_extraction_call_surface_diff.json`
2. that artifact proved the first real live-path difference beyond prompt
   wording:
   - live omitted `temperature=0.0`
   - prompt-eval passed `temperature=0.0`
3. a follow-on aligned rerun artifact now exists:
   `docs/runs/2026-04-02_chunk003_extraction_call_surface_diff_temp0_relref.json`
4. after aligning temperature and relative `source_ref`, the remaining
   differences narrowed to:
   - `call_llm_structured` vs `acall_llm_structured`
   - timeout `60` vs `0`
   - the prompt_eval-only `Case id` line and one blank line before
     `Source text:`

### Phase 3: Land One Narrow Diagnostic Aid

#### Tasks

1. implement the smallest helper/instrumentation needed to replay or summarize
   the extraction-path divergence;
2. add verification for that aid.

#### Success criteria

1. future diagnosis does not depend on conversational SQL snippets;
2. the aid remains bounded to extraction-path behavior.

Progress note:

1. the bounded helper landed as:
   - `src/onto_canon6/evaluation/extraction_path_comparison.py`
   - `scripts/compare_extraction_call_surfaces.py`
   - `tests/evaluation/test_extraction_path_comparison.py`
2. the live extraction service now also supports a bounded temperature override
   for honest extraction-path experiments without changing default behavior.

### Phase 4: Classify The Dominant Blocker

#### Tasks

1. decide whether the remaining blocker is extraction-service behavior or
   review/judge behavior;
2. record secondary caveats separately.

#### Success criteria

1. one dominant blocker family is named explicitly;
2. the classification is backed by committed artifacts.

Progress note:

1. the temperature omission was real but not dominant:
   - before temperature/source-ref alignment, the aligned live rerun had `6`
     accepted candidates
   - after temperature/source-ref alignment, the rerun still had `5`
     accepted candidates
   - both reruns had `0` body-level overlap with prompt-eval
2. the dominant blocker therefore remains live extraction-service behavior
   before review, not review/judge policy.

### Phase 5: Closeout

#### Tasks

1. write the decision note;
2. refresh `CLAUDE.md`, `HANDOFF.md`, `KNOWLEDGE.md`, `TODO.md`,
   `docs/STATUS.md`, and `docs/plans/CLAUDE.md`;
3. either close this block or activate the next narrower block.

#### Success criteria

1. the next block is narrower than `0045`;
2. top-level docs truthfully reflect the new blocker family.

Progress note:

1. the decision note now exists:
   `docs/runs/2026-04-02_extraction_path_decision.md`
2. the next bounded block is now explicit:
   `docs/plans/0046_24h_sync_async_and_caseid_residual_block.md`

## Exit Criteria

This block is complete only when:

1. all five phases above meet their success criteria;
2. the worktree is clean;
3. the repo contains committed extraction-path artifacts and a decision note.

## Closeout

Plan `0045` is complete.

It answered its bounded question honestly:

1. the live path was missing at least one real control-plane input
   (`temperature=0.0`);
2. aligning that control-plane input and the relative `source_ref` still did
   not recover chunk-003 transfer; and
3. the remaining blocker is now narrower than "extraction path in general":
   it is the residual between the sync live structured-call path and the
   prompt_eval async path, plus the remaining prompt_eval-only `Case id`
   metadata line.

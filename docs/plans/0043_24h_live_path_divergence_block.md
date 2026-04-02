# 24h Live-Path Divergence Block

Status: active
Phase status:
- Phase 1 completed
- Phase 2 pending
- Phase 3 pending
- Phase 4 pending
- Phase 5 pending

Last updated: 2026-04-01
Workstream: narrow the post-0042 blocker from generic semantic prompt tuning
to same-model live-path divergence

## Purpose

Plan `0042` proved something narrower and more useful than another prompt win:

1. the revised compact candidate stayed strong in prompt-eval on chunk `002`
   and chunk `003`;
2. the live chunk-003 rerun still diverged completely; and
3. that divergence happened under the same selected model.

This block exists to answer the next explicit question:

**Why does the live extraction path still diverge from prompt-eval on chunk
`003` under the same model and the revised compact candidate pair?**

## Scope

This block intentionally covers only:

1. chunk `003` as the canonical strict-omit stress case;
2. chunk `002` only as a regression guard;
3. the revised compact candidate pair from `0042`;
4. live-vs-prompt-eval path differences under the same model; and
5. one bounded classification of the dominant remaining divergence surface.

Out of scope:

1. broad new prompt rewrites before the divergence is localized;
2. entity-resolution work;
3. ontology/runtime feature changes;
4. consumer integration work.

## Pre-Made Decisions

1. Work stays in the isolated `codex/onto-canon6-integration-planning`
   worktree.
2. All Python execution in this block must use `PYTHONPATH=src`.
3. The incoming decision note is:
   `docs/runs/2026-04-01_semantic_transfer_residual_decision.md`.
4. The canonical candidate pair is:
   - `onto_canon6.extraction.text_to_candidate_assertions_compact_v5@1`
   - `onto_canon6.extraction.prompt_eval_text_to_candidate_assertions_compact_operational_parity@3`
5. The canonical divergence artifacts are:
   - `docs/runs/2026-04-01_chunk002_prompt_surface_parity_v5.json`
   - `docs/runs/2026-04-01_chunk003_prompt_surface_parity_v5.json`
   - `docs/runs/2026-04-01_chunk003_full_chunk_prompt_eval_report_v3.json`
   - `docs/runs/2026-04-01_chunk003_transfer_report_compact5.json`
   - `docs/runs/2026-04-01_chunk003_semantic_transfer_diff_compact5.json`
6. The first repair lever is path-difference localization, not another broad
   prompt tweak.

## Gate

This block succeeds only if:

1. the repo can name the dominant same-model divergence surface explicitly;
2. at least one reproducer or diagnostic aid exists for that surface;
3. the closeout says whether the next fix belongs in prompt/render alignment,
   extraction path behavior, or review/judge behavior.

## Phase Order

### Phase 1: Freeze The Divergence Contract

#### Tasks

1. restate the `0042` decision as the incoming contract;
2. freeze the exact same-model evidence for chunk `003`;
3. record chunk `002` as the regression guard only.

#### Success criteria

1. the repo no longer describes the blocker as generic prompt quality;
2. the active blocker is named as a same-model path divergence.

Progress note:

1. the incoming decision note is now frozen in:
   `docs/runs/2026-04-01_semantic_transfer_residual_decision.md`
2. the same-model evidence is explicit:
   - prompt-eval chunk `003` selected model:
     `gemini/gemini-2.5-flash`
   - live chunk `003` selection task:
     `budget_extraction`
   - live chunk `003` still produced `4` live-only accepted candidates
3. chunk `002` is now explicitly the regression guard only, not the main
   localization target.

### Phase 2: Compare Path Surfaces Directly

#### Tasks

1. identify the remaining live-vs-prompt-eval path differences under the
   revised candidate pair;
2. capture those differences in a reproducible artifact;
3. separate prompt wrapper differences from extraction/review behavior.

#### Success criteria

1. the repo can point to exact path differences instead of inference;
2. the artifact is committed and reusable.

### Phase 3: Land One Narrow Diagnostic Or Repair Aid

#### Tasks

1. implement the smallest helper or instrumentation needed to replay the
   divergence honestly;
2. add verification for that aid.

#### Success criteria

1. future divergence diagnosis is not ad hoc;
2. the aid does not become a second extraction runtime.

### Phase 4: Classify The Dominant Live-Path Blocker

#### Tasks

1. decide whether the divergence is dominated by prompt/render contract,
   extraction path behavior, or review/judge acceptance;
2. record any secondary caveats separately.

#### Success criteria

1. one dominant blocker family is named explicitly;
2. the classification is backed by committed artifacts.

### Phase 5: Closeout

#### Tasks

1. write the decision note;
2. refresh `CLAUDE.md`, `HANDOFF.md`, `KNOWLEDGE.md`, `TODO.md`,
   `docs/STATUS.md`, and `docs/plans/CLAUDE.md`;
3. either close this block or activate the next narrower extraction block.

#### Success criteria

1. the next block is narrower than `0043`, not broader;
2. top-level docs truthfully reflect the new blocker family.

## Failure Modes

1. the block reopens generic semantic prompt tuning without localizing the
   path difference;
2. live review acceptance is treated as proof of semantic correctness without
   comparison artifacts;
3. chunk `002` regression guard disappears from the docs.

## Exit Criteria

This block is complete only when:

1. all five phases above meet their success criteria;
2. the worktree is clean;
3. the repo contains committed divergence artifacts and a decision note.

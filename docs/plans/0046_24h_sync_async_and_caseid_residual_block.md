# 24h Sync/Async And Case-Id Residual Block

Status: complete
Phase status:
- Phase 1 completed
- Phase 2 completed
- Phase 3 completed
- Phase 4 completed
- Phase 5 completed

Last updated: 2026-04-02
Workstream: narrow the post-0045 blocker from generic extraction-path behavior
to the remaining sync/async structured-call residual and prompt_eval-only
`Case id` metadata

## Purpose

Plan `0045` proved something narrower than "the extractor still diverges":

1. live extraction had been omitting `temperature=0.0`;
2. aligning `temperature=0.0` and the relative `source_ref` still did not
   recover chunk-003 transfer; and
3. after that alignment, the remaining differences were limited to:
   - `call_llm_structured` vs `acall_llm_structured`
   - timeout control (`60` vs `0`)
   - the prompt_eval-only `Case id` metadata line and one blank line.

This block exists to answer the next explicit question:

**Is the residual chunk-003 divergence now dominated by the llm_client sync vs
async structured-call path, or by the last prompt-eval-only `Case id`
metadata?**

## Scope

This block intentionally covers only:

1. chunk `003` as the canonical strict-omit stress case;
2. the aligned `compact_v6_wrapper_align` live prompt as the incoming live
   surface;
3. the prompt_eval parity prompt `@3` as the comparison surface;
4. replay and comparison work before review.

Out of scope:

1. broad new semantic prompt rewriting;
2. review/judge policy rewrites;
3. entity-resolution or consumer work.

## Pre-Made Decisions

1. Work stays in the isolated `codex/onto-canon6-integration-planning`
   worktree.
2. All Python execution in this block must use `PYTHONPATH=src`.
3. The incoming decision note is:
   `docs/runs/2026-04-02_extraction_path_decision.md`.
4. Do not add benchmark-specific `Case id` text to the default operational live
   prompt just to make one benchmark row pass.
5. The first lever is bounded replay/localization of the remaining residual,
   not another generic extraction prompt rewrite.

## Gate

This block succeeds only if:

1. the repo can say whether the remaining residual is dominated by:
   - sync vs async structured-call behavior; or
   - the prompt_eval-only `Case id` metadata line;
2. at least one reproducible artifact exists for that answer;
3. the closeout says whether the next fix belongs in llm_client invocation
   parity or in bounded prompt metadata handling.

## Phase Order

### Phase 1: Freeze The Residual Contract

#### Tasks

1. restate the `0045` decision as the incoming contract;
2. freeze the temperature/source-ref aligned artifacts;
3. keep chunk `002` as the regression guard only.

#### Success criteria

1. the active blocker is no longer described as generic extraction-path
   behavior;
2. the remaining residual is bounded to sync/async behavior and `Case id`
   metadata.

### Phase 2: Replay The Remaining Residuals Directly

#### Tasks

1. compare the same rendered prompt under sync vs async structured-call paths
   where the repo can do so honestly;
2. compare the remaining `Case id` metadata effect without broadening the
   live prompt contract;
3. capture those differences in committed artifacts.

#### Success criteria

1. the repo can point to exact residual behavior rather than layered
   speculation;
2. the artifact is committed and reusable.

### Phase 3: Land One Bounded Replay Aid

#### Tasks

1. implement the smallest helper needed to replay or compare the residuals;
2. add verification for that helper.

#### Success criteria

1. residual diagnosis does not depend on ad hoc notebook cells or shell
   snippets;
2. the helper remains bounded to the residual family.

### Phase 4: Classify The Dominant Residual

#### Tasks

1. decide whether the remaining blocker belongs to llm_client invocation parity
   or prompt metadata parity;
2. record any secondary caveats separately.

#### Success criteria

1. one dominant residual family is named explicitly;
2. the classification is backed by committed artifacts.

### Phase 5: Closeout

#### Tasks

1. write the decision note;
2. refresh `CLAUDE.md`, `HANDOFF.md`, `KNOWLEDGE.md`, `TODO.md`,
   `docs/STATUS.md`, and `docs/plans/CLAUDE.md`;
3. either close this block or activate the next narrower block.

#### Success criteria

1. the next block is narrower than `0046`;
2. top-level docs truthfully reflect the new blocker family.

## Exit Criteria

This block is complete only when:

1. all five phases above meet their success criteria;
2. the worktree is clean;
3. the repo contains committed residual-localization artifacts and a decision
   note.

## Closeout

Plan `0046` is complete.

It answered its bounded question truthfully:

1. sync-vs-async `llm_client` public API behavior was not the dominant blocker;
2. prompt-side metadata was dominant instead, starting with the prompt_eval-only
   `Case id:` line; and
3. the next bounded block became prompt metadata repair, not more extraction-path
   speculation.

# 24h Post-Repair Transfer Block

Status: complete
Phase status:
- Phase 1 completed
- Phase 2 completed
- Phase 3 completed
- Phase 4 completed
- Phase 5 completed

Last updated: 2026-04-02
Workstream: rerun chunk-003 transfer after prompt_eval case-id and wrapper
repairs

## Purpose

Plans `0046` through `0048` narrowed and repaired the prompt-side parity
surface:

1. `Case id:` no longer appears in extraction prompt_eval input by default;
2. prompt_eval extraction templates no longer prepend `Case input:` before
   `{input}`;
3. the rendered chunk-003 compact operational-parity surface now differs from
   live only by a trailing newline, not by substantive content lines.

This block exists to answer the next explicit question:

**After the prompt-surface repairs, does the compact operational-parity lane
now transfer honestly on chunk `003`, or is there still a semantic residual
between prompt_eval and live extraction?**

## Scope

This block intentionally covers only:

1. the repaired compact operational-parity prompt_eval variant;
2. the chunk `003` stress case from `psyop_eval_slice.json`;
3. comparison against the existing live temp0+relref artifact family.

Out of scope:

1. broad benchmark reruns across the whole fixture;
2. review/judge policy changes;
3. entity-resolution work;
4. new prompt rewrites beyond the already-landed parity repairs.

## Pre-Made Decisions

1. Work stays in the isolated `codex/onto-canon6-integration-planning`
   worktree.
2. All Python execution in this block must use `PYTHONPATH=src`.
3. The incoming repair surfaces are:
   - `docs/plans/0047_24h_case_metadata_parity_block.md`
   - `docs/plans/0048_24h_prompt_wrapper_parity_block.md`
4. The bounded benchmark run should use one-case diagnostic mode rather than a
   broad fixture sweep.
5. The comparison target remains the committed live replay/artifact family from
   the temp0+relref chunk-003 localization work.

## Gate

This block succeeds only if:

1. the repo produces one post-repair chunk-003 prompt_eval artifact;
2. that artifact is compared explicitly against the live temp0+relref family;
3. the closeout says whether the active extraction blocker is now resolved,
   narrowed to a semantic residual, or still transport/runtime unstable.

## Phase Order

### Phase 1: Freeze The Repaired Prompt Contract

#### Tasks

1. freeze the repaired prompt-surface artifacts from Plans `0047` and `0048`;
2. define the exact one-case rerun shape.

#### Success criteria

1. the incoming prompt contract is explicit and reproducible;
2. the rerun target is one named case, not a moving slice.

### Phase 2: Run One Bounded Post-Repair PromptEval Check

#### Tasks

1. run the repaired compact operational-parity variant on the chunk-003 case
   in diagnostic mode;
2. capture the prompt_eval output artifact.

#### Success criteria

1. one committed post-repair prompt_eval artifact exists for chunk `003`;
2. the run is bounded enough to be repeatable.

### Phase 3: Compare Against The Live Artifact Family

#### Tasks

1. compare the repaired prompt_eval output to the live temp0+relref family;
2. summarize predicate/candidate-family agreement or disagreement explicitly.

#### Success criteria

1. the repo can say what still differs, not just that it differs;
2. the comparison is artifact-backed.

### Phase 4: Classify The Remaining Blocker

#### Tasks

1. decide whether the remaining blocker is now resolved, semantic, or runtime;
2. record any uncertainty separately and narrowly.

#### Success criteria

1. one dominant post-repair status is named explicitly;
2. the classification is backed by the rerun artifact.

### Phase 5: Closeout

#### Tasks

1. write the decision note;
2. refresh `CLAUDE.md`, `HANDOFF.md`, `KNOWLEDGE.md`, `TODO.md`,
   `docs/STATUS.md`, and `docs/plans/CLAUDE.md`;
3. either close this block or activate the next narrower block.

#### Success criteria

1. the repo truthfully states what changed after the parity repairs;
2. the next block, if any, is narrower than `0049`.

## Exit Criteria

This block is complete only when:

1. all five phases above meet their success criteria;
2. the worktree is clean;
3. the repo contains committed post-repair rerun artifacts and a decision note.

## Closeout

Plan `0049` is complete.

The post-repair rerun answered the right question:

1. prompt-side parity repairs restored a real prompt_eval chunk-003 output;
2. the active blocker is no longer prompt-surface plumbing;
3. the remaining blocker is semantic extraction quality on the repaired
   analytical chunk-003 path, tracked by Plan `0050`.

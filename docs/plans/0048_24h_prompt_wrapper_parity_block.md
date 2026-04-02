# 24h Prompt-Wrapper Parity Block

Status: complete
Phase status:
- Phase 1 completed
- Phase 2 completed
- Phase 3 completed
- Phase 4 completed
- Phase 5 completed

Last updated: 2026-04-02
Workstream: remove the remaining prompt_eval-only extraction wrapper heading
after case-id metadata has been removed

## Purpose

Plan `0046` and the opening slice of Plan `0047` proved two distinct prompt-side
effects on chunk `003`:

1. removing only `Case id:` from the prompt_eval async replay changed the
   parsed result from `0` candidates to `5`;
2. removing `Case id:` plus the prompt_eval-only `Case input:` wrapper heading
   changed the parsed result from `5` to `4`; and
3. that `4`-candidate result matches the live async replay count.

This block exists to answer the next explicit question:

**Can the repo remove the prompt_eval-only `Case input:` extraction wrapper by
default so the prompt_eval operational-parity lane stops carrying model-visible
scaffolding that live extraction does not use?**

## Scope

This block intentionally covers only:

1. prompt_eval extraction prompt templates that currently wrap `{input}` in
   `Case input:`;
2. prompt-surface parity helpers and tests;
3. one real chunk-003 rendered or replay-backed proof artifact after the fix.

Out of scope:

1. live extraction prompt rewrites;
2. benchmark fixture changes;
3. review/judge behavior;
4. broader semantic prompt editing beyond removing the wrapper heading.

## Pre-Made Decisions

1. Work stays in the isolated `codex/onto-canon6-integration-planning`
   worktree.
2. All Python execution in this block must use `PYTHONPATH=src`.
3. The incoming decision surfaces are:
   - `docs/plans/0046_24h_sync_async_and_caseid_residual_block.md`
   - `docs/plans/0047_24h_case_metadata_parity_block.md`
4. The fix belongs in prompt_eval extraction templates, not the live extraction
   prompt.
5. Keep the extraction prompt body otherwise unchanged unless one exact wrapper
   line cannot be removed cleanly.

## Gate

This block succeeds only if:

1. extraction prompt_eval templates no longer prepend `Case input:` before
   `{input}`;
2. rendered prompt surfaces and tests prove that change;
3. one real chunk-003 artifact shows the wrapper heading is no longer present;
4. the closeout names the next narrower blocker, if any.

## Phase Order

### Phase 1: Freeze The Wrapper Contract

#### Tasks

1. freeze the replay artifact that proved the `Case input:` heading still
   changes the parsed chunk-003 result;
2. record which prompt templates currently add the wrapper.

#### Success criteria

1. the active blocker is no longer generic "prompt metadata";
2. the repo names the exact wrapper line as the target.

### Phase 2: Remove The Wrapper From Extraction Templates

#### Tasks

1. remove `Case input:` scaffolding from the extraction prompt_eval templates
   that still prepend it;
2. keep `{input}` itself intact.

#### Success criteria

1. the templates no longer add the wrapper heading;
2. extraction prompt_eval still renders valid user prompts.

### Phase 3: Update Tests And Parity Helpers

#### Tasks

1. update tests that still expect the wrapper heading;
2. rerun the narrow prompt/parity suite.

#### Success criteria

1. the new prompt contract is enforced by tests;
2. verification passes without broad unrelated churn.

### Phase 4: Produce One Real Proof Artifact

#### Tasks

1. render or replay one real chunk-003 artifact after the template repair;
2. record whether the user-message difference shrank again.

#### Success criteria

1. one committed artifact proves the wrapper is gone on the real residual case;
2. the artifact supports a truthful next-step decision.

### Phase 5: Closeout

#### Tasks

1. write the decision note;
2. refresh `CLAUDE.md`, `HANDOFF.md`, `KNOWLEDGE.md`, `TODO.md`,
   `docs/STATUS.md`, and `docs/plans/CLAUDE.md`;
3. either close this block or activate the next narrower block.

#### Success criteria

1. the repo truthfully states whether wrapper removal settled the current
   prompt-side parity blocker;
2. any next block is narrower than `0048`.

## Exit Criteria

This block is complete only when:

1. all five phases above meet their success criteria;
2. the worktree is clean;
3. the repo contains committed wrapper-parity artifacts and a decision note.

## Closeout

Plan `0048` is complete.

It removed the remaining prompt_eval-only wrapper heading:

1. extraction prompt_eval templates no longer prepend `Case input:` before
   `{input}`;
2. the real chunk-003 rendered user prompt now has no remaining content-line
   diff against the live user prompt; and
3. the next bounded question became post-repair transfer behavior under the
   repaired prompt surface, tracked by Plan `0049`.

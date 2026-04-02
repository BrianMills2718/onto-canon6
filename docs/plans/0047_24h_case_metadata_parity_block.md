# 24h Case-Metadata Parity Block

Status: complete
Phase status:
- Phase 1 completed
- Phase 2 completed
- Phase 3 completed
- Phase 4 completed
- Phase 5 completed

Last updated: 2026-04-02
Workstream: remove prompt_eval-only case metadata from the extraction prompt
surface without losing diagnostic traceability

## Purpose

Plan `0046` localized the remaining chunk-003 residual more tightly than any
earlier block:

1. replaying the captured prompt_eval chunk-003 prompt through the sync facade
   still returned `0` candidates;
2. replaying the captured live temp0+relref prompt through the async facade
   still returned non-empty candidates; and
3. replaying the prompt_eval async prompt **without only the `Case id:` line**
   flipped the parsed result from `0` candidates to `5`.

This block exists to answer the next explicit question:

**Can the repo remove prompt_eval-only `Case id` metadata from the extraction
prompt surface by default, while preserving case identity outside the model
prompt, and thereby restore honest live/prompt_eval parity?**

## Scope

This block intentionally covers only:

1. the extraction prompt_eval input formatter;
2. the compact operational-parity prompt surface;
3. prompt_eval configuration and tests for extraction experiments;
4. one real chunk-003 rendered or replay-backed proof artifact after the fix.

Out of scope:

1. live extraction prompt rewrites;
2. prompt_eval judge prompts;
3. review/judge policy changes;
4. broad new benchmark fixture edits.

## Pre-Made Decisions

1. Work stays in the isolated `codex/onto-canon6-integration-planning`
   worktree.
2. All Python execution in this block must use `PYTHONPATH=src`.
3. The incoming decision surface is:
   `docs/plans/0046_24h_sync_async_and_caseid_residual_block.md`.
4. `case_id` must remain available in experiment input ids, diagnostics, and
   observability provenance even when it is removed from the model prompt.
5. The default extraction prompt_eval surface should optimize for operational
   parity with live extraction, not benchmark-only metadata convenience.
6. Do not add benchmark-specific metadata to the live extraction prompt in
   response to this block.

## Gate

This block succeeds only if:

1. extraction prompt_eval inputs omit the `Case id:` line by default;
2. case identity remains present in non-prompt control surfaces;
3. the rendered compact operational-parity prompt surface no longer differs
   from live extraction because of `Case id:` metadata;
4. at least one committed artifact proves the new default aligns with the
   chunk-003 residual diagnosis; and
5. the closeout names the next narrower blocker, if any, after the metadata
   repair.

## Phase Order

### Phase 1: Freeze The Metadata-Parity Contract

#### Tasks

1. restate the `0046` decision as the incoming contract;
2. freeze the replay artifacts that proved `Case id:` dominance;
3. record which non-prompt surfaces must still retain case identity.

#### Success criteria

1. the active blocker is no longer described as generic prompt metadata;
2. the repo says explicitly that `Case id:` is the bounded target and that
   observability ids stay intact.

### Phase 2: Land The Formatter Policy

#### Tasks

1. add one explicit extraction prompt_eval policy for whether case ids appear
   in model input;
2. make the default operational extraction prompt_eval path omit `Case id:`;
3. keep source kind, ref, and label behavior unchanged unless required by the
   same bounded evidence.

#### Success criteria

1. the extraction prompt_eval path no longer injects `Case id:` by default;
2. experiment input ids and observability still carry the case id.

### Phase 3: Update Parity Surfaces And Tests

#### Tasks

1. update prompt-surface comparison helpers to reflect the new default;
2. add or update tests for the formatter policy;
3. verify the narrow affected suite.

#### Success criteria

1. repo tests prove the new policy rather than relying on conversation;
2. the parity helper shows the rendered user-message difference shrinking.

### Phase 4: Produce One Real Proof Artifact

#### Tasks

1. render or replay one real chunk-003 artifact through the new default;
2. record whether the parity gap is materially reduced after the fix.

#### Success criteria

1. there is one committed artifact tied to the real residual case;
2. the artifact supports a truthful next-step decision.

### Phase 5: Closeout

#### Tasks

1. write the decision note;
2. refresh `CLAUDE.md`, `HANDOFF.md`, `KNOWLEDGE.md`, `TODO.md`,
   `docs/STATUS.md`, and `docs/plans/CLAUDE.md`;
3. either close this block or activate the next narrower block.

#### Success criteria

1. the repo truthfully states whether the `Case id:` repair resolved the
   active parity residual or only narrowed it;
2. the next active block, if any, is narrower than `0047`.

## Exit Criteria

This block is complete only when:

1. all five phases above meet their success criteria;
2. the worktree is clean;
3. the repo contains committed metadata-parity artifacts and a decision note.

## Closeout

Plan `0047` is complete.

It landed the bounded repair it was supposed to land:

1. extraction prompt_eval input no longer includes `Case id:` by default;
2. experiment ids and observability still preserve case identity; and
3. the next narrower blocker became the prompt_eval-only `Case input:` wrapper
   heading, tracked by Plan `0048`.

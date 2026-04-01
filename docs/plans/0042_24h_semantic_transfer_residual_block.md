# 24h Semantic Transfer Residual Block

Status: active
Phase status:
- Phase 1 pending
- Phase 2 pending
- Phase 3 pending
- Phase 4 pending
- Phase 5 pending

Last updated: 2026-04-01
Workstream: narrow the post-0041 extraction blocker from prompt-surface
uncertainty to one bounded semantic transfer family

## Purpose

Plan `0041` closed the prompt-surface question honestly:

1. the live and prompt-eval system messages are identical;
2. the remaining user-surface difference is a stable wrapper family;
3. that wrapper family is present on both canonical chunks; and
4. the chunk-specific residuals are still semantic.

This block exists to answer the next narrower question:

**Can the compact live extraction candidate be tightened enough to suppress the
named semantic residual families without losing chunk-002 positive-control
coverage?**

## Scope

This block intentionally covers only:

1. the current compact live extraction prompt candidate;
2. the same `compact_operational_parity` prompt-eval lane used in `0041`;
3. semantic residuals frozen by chunk `002` and chunk `003`;
4. body-level live-vs-parity comparison that does not let `claim_text`
   dominate the signal; and
5. one bounded prompt revision plus bounded verification.

Out of scope:

1. broad model-family swaps;
2. new ontology/runtime features;
3. new review-policy changes;
4. DIGIMON / consumer work;
5. another prompt-surface reconstruction loop.

## Pre-Made Decisions

1. Work stays in the isolated `codex/onto-canon6-integration-planning`
   worktree.
2. All Python execution in this block must use `PYTHONPATH=src`.
3. The incoming decision note is:
   `docs/runs/2026-04-01_full_chunk_transfer_parity_decision.md`.
4. The canonical semantic residual artifacts are:
   - `docs/runs/2026-04-01_chunk002_live_vs_parity_diff.json`
   - `docs/runs/2026-04-01_chunk003_live_vs_parity_diff.json`
   - `docs/runs/2026-04-01_chunk002_prompt_surface_parity.json`
   - `docs/runs/2026-04-01_chunk003_prompt_surface_parity.json`
5. The positive control remains chunk `002`.
6. The prose-heavy strict-omit stress case remains chunk `003`.
7. The first repair lever is prompt-level semantic tightening, not a new
   post-processing rejection path.

## Gate

This block succeeds only if:

1. the repo can show body-level live-vs-parity residuals without `claim_text`
   noise dominating the result;
2. one bounded prompt revision is justified by those residuals, not by generic
   prompt churn;
3. the revised lane improves the named residual family on prompt-eval;
4. at least one live rerun is executed on a named chunk; and
5. the closeout states clearly whether the semantic residual is now narrowed,
   recovered, or still promotion-blocking.

## Phase Order

### Phase 1: Freeze The Semantic Residual Contract

#### Tasks

1. restate the `0041` decision as the incoming contract;
2. enumerate the chunk-002 body-level residuals;
3. enumerate the chunk-003 live-only overreach families.

#### Success criteria

1. the active blocker is named in semantic terms, not as a generic "parity"
   mismatch;
2. chunk `002` and chunk `003` each contribute one explicit residual family.

### Phase 2: Land A Body-Level Comparison Aid

#### Tasks

1. extend or add the narrowest helper needed to compare candidates by
   predicate/roles without `claim_text`;
2. add targeted verification for that helper;
3. save a semantic residual artifact for chunk `002` and chunk `003`.

#### Success criteria

1. the repo can prove chunk `002` is mostly body-aligned while chunk `003`
   remains semantically divergent;
2. future diagnosis no longer depends on ad hoc REPL snippets.

### Phase 3: Make One Bounded Prompt Revision

#### Tasks

1. update the compact extraction prompt candidate only where the residual
   evidence justifies it;
2. target analytical narrator overreach and unsupported subject/speaker
   invention explicitly;
3. avoid broad prompt churn unrelated to chunk `002` / `003`.

#### Success criteria

1. the prompt diff is small and traceable to the named residual families;
2. the repo can explain why each changed instruction exists.

### Phase 4: Verify The Revision

#### Tasks

1. rerun bounded prompt-eval verification on chunk `002` and chunk `003`;
2. if prompt-eval improves honestly, run at least one live chunk rerun;
3. record whether chunk `002` stays a positive control and whether chunk `003`
   improves.

#### Success criteria

1. verification uses explicit named artifacts, not conversational claims;
2. the result is strong enough to decide whether the candidate advanced or not.

### Phase 5: Closeout

#### Tasks

1. write the decision note;
2. refresh `CLAUDE.md`, `HANDOFF.md`, `KNOWLEDGE.md`, `TODO.md`,
   `docs/STATUS.md`, and `docs/plans/CLAUDE.md`;
3. either close this block or activate the next narrower extraction block.

#### Success criteria

1. the next blocker family is explicit if this block does not clear the gate;
2. the repo no longer describes the active blocker as "prompt parity" after
   this block.

## Failure Modes

1. claim-text wording dominates the semantic diagnosis again;
2. the block reopens generic prompt experimentation;
3. live reruns are skipped even if prompt-eval improves;
4. chunk `002` positive-control behavior is allowed to regress silently.

## Exit Criteria

This block is complete only when:

1. all five phases above meet their success criteria;
2. the worktree is clean;
3. the repo contains committed semantic residual artifacts and a decision note.

# Handoff: onto-canon6 — 2026-04-02

## Session Focus

Plan `0064` execution and closeout in the isolated worktree branch
`codex/onto-canon6-query-wt`.

## What Landed

Committed in the isolated worktree as:

- `74f99b0` — `Activate identity browse widening block`
- `6eb7594` — `Add identity-aware query browse filters`

Main effects:

1. entity browse now supports `has_identity`, `provider`, and
   `reference_status` filters;
2. entity search can now match on attached external ids and reference labels;
3. browse results now expose identity presence plus attached/unresolved
   external-reference counts and provider summaries;
4. CLI and MCP mirror the widened query contract; and
5. the widened surface is proved operationally in
   `docs/runs/2026-04-02_identity_external_reference_browse_real_proof.md`.

## Current State

1. Plan `0064` is complete.
2. Plan `0028` remains the umbrella queryability plan.
3. There is no active 24h block right now.
4. The next narrowed queryability choice is first-class source-artifact query
   unless reprioritized by new evidence.

## Recommended Next Step

If work continues:

1. keep substantial autonomous work on isolated worktree branches by default;
2. decide whether source-artifact query becomes the next 24h block; and
3. do not reopen the extraction-transfer chain or widen the DIGIMON seam as a
   substitute for that queryability choice.

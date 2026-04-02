# 24h Query Browse Widening Block

Status: active

Last updated: 2026-04-02
Workstream: Plan 0028 widening/hardening after first read-only slice

## Purpose

Turn the landed first read-only query surface into a genuinely usable browse
surface for operators and agents.

The first slice already proved deterministic search/get over promoted state.
This block widens that slice in one bounded direction only:

1. add true browse/list operations instead of forcing every read through a
   search query;
2. add source-centric promoted-assertion filtering so provenance can be used as
   a first-class entrypoint; and
3. prove the widened surface on real promoted data.

This block is complete only when the widened browse surface is implemented,
verified, documented, and no active ambiguity remains about what the next
queryability slice should be.

## Pre-Made Decisions

1. The block stays read-only. No CRUD, no mutation, no review-state folding.
2. The widened surface remains over promoted state only.
3. The new browse operations live in `QuerySurfaceService`; CLI and MCP stay
   thin wrappers.
4. The block adds exactly two widened query capabilities:
   - entity browsing/listing
   - promoted-assertion browsing with source-centric filters
5. Provenance widening uses `source_ref` and optional `source_kind` filters on
   promoted assertions. This block does not introduce a standalone artifact
   search subsystem.
6. Existing `list-promoted-assertions` should become query-surface-backed
   instead of remaining a separate raw graph read.
7. `list-identities` remains separate in this block. Folding identity browse
   into the query surface is explicitly deferred.
8. Search semantics from Plan 0028 remain unchanged. Browse is additive, not a
   silent mutation of the search contract.
9. The block runs in the isolated worktree branch only and merges back after
   every declared phase is complete and verified.

## Success Criteria

The block succeeds only when all of the following are true:

1. docs/plans/0014, 0024, 0028, `TODO.md`, and `CLAUDE.md` all agree that the
   extraction-transfer chain is complete and that this block is the active 24h
   execution surface;
2. `QuerySurfaceService` exposes deterministic entity-browse and
   promoted-assertion-browse methods with typed request/response contracts;
3. source-centric promoted-assertion filtering works by `source_ref` and
   optional `source_kind`;
4. CLI exposes the widened browse operations without inventing a second query
   model;
5. MCP exposes the same widened operations with aligned parameter shapes;
6. targeted unit/integration tests cover the new service, CLI, and MCP paths;
7. one real-proof run note demonstrates the widened browse surface on a real
   promoted DB.

This block fails if any of the following are true:

1. the work widens into a generic retrieval platform or DIGIMON replacement;
2. browse semantics are split across old graph-specific commands and the query
   service without a clear source of truth;
3. source-centric lookup requires raw SQLite inspection or ad hoc scripts;
4. docs still imply an active extraction-transfer rescue block after this work
   begins.

## Phase Order

### Phase 1 — Freeze Post-Merge Queryability Contract

1. create this plan and make it the active 24h block;
2. update `CLAUDE.md`, `docs/plans/CLAUDE.md`, `TODO.md`, and the relevant plan
   surfaces so the active frontier is unambiguous;
3. restate Plan 0014 as a policy reference, not an active transfer-hardening
   block.

**Acceptance**

1. one active 24h block is named everywhere;
2. no top-level doc still implies Plans `0057`-`0062` are the active work;
3. the widened queryability scope is fixed before code changes begin.

### Phase 2 — Add Typed Browse Contracts And Service Support

1. add typed browse request/result models for entity listing and
   promoted-assertion listing;
2. add `source_ref` and `source_kind` filters to promoted-assertion browse;
3. implement deterministic ordering in `QuerySurfaceService`;
4. keep error semantics explicit and fail loud on unsupported combinations.

**Acceptance**

1. one service owns browse/search semantics for the widened slice;
2. source-centric assertion listing works without raw DB access;
3. service tests cover browse ordering and provenance filters.

### Phase 3 — CLI And MCP Widening

1. add `list-entities` as a query-surface-backed CLI command;
2. route `list-promoted-assertions` through the query surface and add
   provenance filters there;
3. add matching MCP browse tools with aligned argument shapes;
4. keep existing search/get commands intact.

**Acceptance**

1. human CLI users can browse promoted state without synthetic search terms;
2. agents can browse the same widened surface through MCP;
3. CLI and MCP do not drift from the typed service contract.

### Phase 4 — Real-Proof Verification

1. run the widened browse surface against a real promoted DB;
2. demonstrate one entity-browse case and one source-centric assertion-browse
   case;
3. record the exact commands, DB, and proof outputs in `docs/runs/`.

**Acceptance**

1. widened browse/query works on real promoted data, not only fixtures;
2. the proof note is specific enough for another operator to reproduce.

### Phase 5 — Closeout

1. update `README.md`, `docs/STATUS.md`, `HANDOFF.md`, and Plan 0028 with the
   landed widened state;
2. truthfully mark this block complete;
3. identify the next query-surface question explicitly instead of leaving a
   vague “more hardening later” note.

**Acceptance**

1. the widened surface is discoverable from the repo’s top-level reading order;
2. the next-active uncertainty is narrowed to one or two concrete follow-on
   options.

## Verification

Minimum verification for this block:

1. targeted query-surface service tests;
2. targeted CLI integration tests;
3. targeted MCP integration tests;
4. `ruff` and `mypy` on touched code;
5. one real-proof run note under `docs/runs/`.

## Uncertainty Handling

If a new uncertainty appears during this block:

1. write it into this plan, `TODO.md`, and `KNOWLEDGE.md`;
2. continue on the next bounded phase unless the uncertainty changes the
   contract itself;
3. stop only if the uncertainty is a real contract decision the user must make.

## Open Questions

### Q1: Should identity browse/list eventually fold into the query surface?
**Status:** Deferred
**Decision for this block:** No. Keep `list-identities` separate.

### Q2: Should source-artifact search become its own first-class query subsystem?
**Status:** Deferred
**Decision for this block:** No. Use source-centric assertion filters only.

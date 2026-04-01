# 24h Query Surface Execution Block

Status: active
Phase status:
- Phase 1 complete
- Phase 2 complete
- Phase 3 next

Last updated: 2026-03-31
Workstream: bounded 24-hour autonomous implementation block

## Purpose

Execute the first read-only query/browse surface from
[0028_query_browse_surface.md](0028_query_browse_surface.md) end to end in one
autonomous block:

1. shared read service
2. CLI wrappers
3. MCP wrappers
4. verification on real proof data
5. documentation/status closeout

## Scope

This execution block is intentionally narrower than the full long-term
queryability story. It implements exactly the first five target operations:

1. `search-entities`
2. `get-entity`
3. `search-promoted-assertions`
4. `get-promoted-assertion`
5. `get-evidence`

Anything broader is out of scope unless a blocker forces a local refactor.

## Pre-Made Decisions

1. The implementation stays in the isolated worktree branch
   `codex/onto-canon6-integration-planning`.
2. The service is read-only and operates on promoted state only.
3. Existing report surfaces are reused where useful, but query semantics live
   in one dedicated read service.
4. CLI and MCP wrappers must stay thin and match the same service contracts.
5. Unsupported filters and inconsistent provenance links fail loudly.
6. Verification requires deterministic tests plus one real-proof walkthrough on
   the canonical local review DB.
7. Every verified phase gets its own commit.
8. Uncertainties are logged in the plan or TODO tracker, but work continues
   unless the uncertainty blocks safe implementation.

## Phase Order

### Phase 1: Shared Read Service

Implement the typed request/response models and service methods for the five
operations.

**Success criteria**

1. one shared read service exists;
2. service-level tests cover all five operations;
3. no raw SQLite rows leak through the public service contract.

### Phase 2: CLI Surface

Add the five CLI commands on top of the shared read service.

**Success criteria**

1. all five commands exist and are wired through the same service;
2. CLI tests cover success and failure semantics;
3. JSON output is scriptable and deterministic.

### Phase 3: MCP Surface

Add thin MCP tools for the same five operations.

**Success criteria**

1. MCP parameter shapes align with the service contracts;
2. integration tests cover the new tools;
3. no second query model is introduced.

### Phase 4: Real-Proof Verification

Exercise the new surface against the canonical local proof DB.

**Success criteria**

1. one entity/alias lookup is verified on real promoted data;
2. one promoted assertion lookup is verified on real promoted data;
3. one evidence/provenance lookup is verified on real promoted data.

### Phase 5: Closeout

Update docs, status, handoff, and TODO state to reflect the landed surface.

**Success criteria**

1. top-level docs mention the new query surface truthfully;
2. the plan stack records what landed and what remains next;
3. the execution block can be marked complete.

## Failure Modes

1. the implementation drifts into a general retrieval platform;
2. CLI and MCP wrappers diverge from the shared service semantics;
3. evidence lookup ships without enough provenance context to be trustworthy;
4. the run ends with partial uncommitted work instead of a clean rollback point.

## Exit Criteria

This execution block is complete only when all five phases above meet their
success criteria and the repo is left with committed, verified increments.

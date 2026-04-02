# 24h Identity / External-Reference Browse Block

Status: complete

Last updated: 2026-04-02
Workstream: query-surface widening after Plan `0063`

## Purpose

Widen the landed read-only query surface so operators and agents can browse and
search promoted entities through identity and external-reference state, not only
through canonical names and source-centric assertion context.

This block exists because the first browse widening slice is complete, but the
next truthful user question is now:

1. which promoted entities already have stable identities;
2. which identities carry attached or unresolved external references; and
3. how can an operator find those entities without dropping back to
   identity-specific maintenance commands?

## Why Now

Plan `0063` landed a real browse surface, but it remains weak on the exact
identity/external-reference workflows already owned by `onto-canon6`:

1. `get-entity` can return identity bundles, but browse/search cannot filter by
   external-reference state;
2. operators can record external references through identity commands, but the
   query surface does not expose a read-first way to find them again; and
3. the next narrowed follow-on named in `TODO.md`, `0027`, and `0028` is
   identity/external-reference-aware browse.

## Non-Goals

This block does not:

1. add any identity mutation to the query surface;
2. expose raw identity tables as the public contract;
3. build first-class source-artifact query beyond current source-centric
   assertion filters;
4. widen the DIGIMON seam; or
5. add embedding, fuzzy, or LLM-mediated query behavior.

## Pre-Made Decisions

1. The next widening choice is identity/external-reference-aware browse, not
   first-class source-artifact query.
2. The widening happens inside the existing entity browse/search/detail surface,
   not through a second parallel "identity query" API.
3. The first slice must cover both attached and unresolved external-reference
   state.
4. Search remains deterministic and exact-ranking-based.
5. The first search expansion should match against:
   - canonical entity names
   - alias names
   - attached external ids
   - attached reference labels
6. The first search expansion should **not** treat unresolved notes as free-text
   search input.
7. Browse filtering should support:
   - `entity_type`
   - `has_identity`
   - `provider`
   - `reference_status`
8. `EntityBrowseResult` should expose enough summary state that operators do not
   need a second call just to tell whether an entity has identity or external
   references.
9. `EntityDetail` should remain the detailed identity/external-reference view;
   no second detail endpoint is needed.
10. The operational proof may seed explicit external references into a copy of a
    real promoted DB, because the current real proof DB carries the
    `graph_external_references` table but no persisted rows.

## Contract Decisions

### Request/Filter Surface

`EntityBrowseRequest` should support:

1. `entity_type`
2. `has_identity`
3. `provider`
4. `reference_status`
5. `limit`

`EntitySearchRequest` should support:

1. `query`
2. `entity_type`
3. `provider`
4. `reference_status`
5. `limit`

### Browse/Search Semantics

1. `provider` filters only entities whose identity bundle contains at least one
   matching external reference provider.
2. `reference_status` filters only entities whose identity bundle contains at
   least one matching attached/unresolved record.
3. `has_identity=true` means the entity must belong to an identity bundle.
4. `has_identity=false` means the entity must not belong to an identity bundle.
5. Search ranking order expands to:
   - canonical exact
   - alias exact
   - external id exact
   - external label exact
   - canonical/alias prefix
   - external id/reference-label prefix
   - canonical/alias substring
   - external id/reference-label substring

### Response Surface

`EntityBrowseResult` should additionally expose:

1. `has_identity`
2. `attached_external_reference_count`
3. `unresolved_external_reference_count`
4. `external_reference_providers`

`EntitySearchResult` should additionally allow match reasons for external ids
and reference labels.

## Phases

### Phase 0. Authority Cleanup And Block Activation

Update the authority docs so they truthfully name this block as the active
follow-on after `0063`.

Success criteria:

1. `CLAUDE.md`, `TODO.md`, `docs/plans/CLAUDE.md`, `0024`, and `0027` all point
   at this block;
2. stale references to `0025` or `0063` as the next-active block are removed;
3. the continuous-execution rule names this block explicitly.

### Phase 1. Query Contract Widening

Add the typed request/response changes needed for identity/external-reference
filtering and search.

Success criteria:

1. the model layer captures the widened filters and result summaries;
2. unsupported combinations still fail loudly through model or service
   validation;
3. the widened contract is reflected in `0028`.

### Phase 2. Service Implementation And Unit Coverage

Implement the widened browse/search semantics in `QuerySurfaceService`.

Success criteria:

1. browse filters work over identity presence, provider, and reference status;
2. entity search can find a promoted entity via attached external id and
   reference label;
3. browse results expose identity/external-reference summary counts;
4. unit tests cover canonical-name, alias, external-id, and provider/status
   paths.

### Phase 3. CLI And MCP Widening

Expose the widened filters through the shared CLI/MCP surface.

Success criteria:

1. `list-entities` accepts identity/external-reference filters;
2. `search-entities` accepts identity/external-reference filters and returns
   widened match reasons;
3. MCP mirrors the same filter set;
4. integration tests cover the widened CLI/MCP behavior.

### Phase 4. Operational Proof And Closeout

Prove the widened surface against a copy of a real promoted DB and close the
doc stack truthfully.

Success criteria:

1. one proof note under `docs/runs/` records the exact commands and artifact;
2. the proof uses a copy of a real promoted DB with seeded identity/external
   reference rows if the source DB lacks them;
3. `README.md`, `STATUS.md`, `HANDOFF.md`, `0028`, and this plan reflect the
   landed state;
4. the worktree is clean and ready for merge-back.

## Failure Modes

1. the query surface grows a second overlapping identity API instead of
   widening the existing entity surface;
2. external-reference search silently ignores provider/status filters;
3. result summaries omit enough context that users still have to fall back to
   maintenance commands;
4. the proof claims "real external-reference browse" without disclosing that
   the real DB had to be seeded on a copy.

## Verification

Minimum verification for block closeout:

1. `pytest -q tests/surfaces/test_query_surface.py tests/integration/test_query_cli.py tests/integration/test_mcp_server.py`
2. `ruff check` on touched query-surface, CLI, MCP, and test files
3. `mypy` on touched query-surface, CLI, and MCP modules
4. one recorded operational proof under `docs/runs/`

## Exit Condition

This block is complete when:

1. identity/external-reference-aware browse is implemented end to end;
2. the authority docs name the next narrowed choice after this block rather
   than leaving it vague; and
3. the worktree branch is ready for explicit merge-back to `main`.

# Query And Browse Surface

Status: complete (2026-04-02)

Last updated: 2026-04-02
Workstream: next-active deferred parity capability after Lane 5 ordering

## Purpose

Recover the missing "use `onto-canon6` as a queryable governed knowledge base"
surface without broadening the repo into a general retrieval engine.

This plan addresses the deferred parity row
"concept/entity browsing and search" from
[0005_v1_capability_parity_matrix.md](0005_v1_capability_parity_matrix.md).

## Why Now

`onto-canon6` is now:

1. self-contained after donor cutover;
2. explicit about contract stability;
3. chosen as a real producer for DIGIMON;
4. now has a first-class read/query surface over promoted knowledge, with the next widening choice narrowed explicitly.

The repo can now serve the first practical governed-knowledge browse/search questions, but it still does not cover every read workflow an operator or agent may eventually need. The still-relevant questions are:

1. what entities exist;
2. what promoted assertions mention them;
3. what evidence supports those assertions; and
4. how aliases/identities connect across the promoted graph.

## Non-Goals

This plan does not:

1. add direct concept/belief CRUD;
2. add vector retrieval, graph analytics, or QA-specific routing;
3. replace DIGIMON as the retrieval-oriented consumer;
4. expose raw SQLite tables as the contract;
5. build domain-specific helper commands before a general browse/search base
   exists.

## Pre-Made Decisions

1. The first slice is **read-only**.
2. The contract is over typed promoted-graph and identity/evidence surfaces,
   not raw database tables.
3. The core implementation lives in a shared service layer; CLI and MCP are
   thin wrappers over the same typed results.
4. The first slice covers **promoted state only**:
   candidate/proposal review surfaces remain separate and are not folded into
   this query plan.
5. Search is deterministic and explicit, not embedding-based or LLM-mediated.
6. Name search should operate over canonical names plus alias membership when
   available.
7. Results should fail loud on unsupported filters or unknown ids; no silent
   fallback to broader scans.
8. The first useful surface should answer "where is this entity/assertion/evidence"
   before it tries to answer arbitrary investigative questions.

## Current Baseline

The repo already has narrow read surfaces:

1. CLI:
   - `list-candidates`
   - `list-proposals`
   - `list-promoted-assertions`
   - `list-recanonicalization-events`
   - `list-identities`
2. report/export surfaces:
   - promoted graph report
   - governed bundle export
   - Foundation IR export
   - DIGIMON export

The missing gap was a true browse/search surface over promoted knowledge and its
supporting evidence. Plans `0029`, `0063`, and `0064` now land that base
surface plus the first two widening steps. The remaining question is not
whether queryability exists, but which bounded follow-on should widen it next.

### Phase 0 Inventory Snapshot (2026-03-31)

Existing reusable seams:

1. `CanonicalGraphService`
   - `list_promoted_assertions()`
   - `get_promoted_assertion(assertion_id=...)`
   - `get_promotion_result(assertion_id=...)`
2. `IdentityService`
   - `list_identities()`
   - `get_identity_bundle(identity_id=...)`
3. `ReviewService`
   - `get_candidate_assertion(candidate_id=...)`
   - `list_proposals(...)`
4. report surfaces
   - `PromotedGraphReportService`
   - `IdentityReportService`
   - `LineageReportService`
   - `EpistemicReportService`

Current thin CLI access points:

1. `list-promoted-assertions`
2. `list-identities`
3. `export-identity-report`
4. promoted-graph report export
5. governed-bundle export

What is still missing for queryability after Plans `0029`, `0063`, and `0064`:

1. first-class source-artifact query beyond source-centric assertion filters
2. any broader read surface beyond promoted-state browse/search/get

## Target Surface

The minimum useful browse/search slice should support exactly these operations:

1. **Search entities**
   - by canonical name, alias text, and optional entity type
2. **Get entity**
   - return identity/alias context plus linked promoted assertions
3. **Search promoted assertions**
   - by predicate, entity reference, and free-text match over claim text
4. **Get promoted assertion**
   - return normalized roles, linked entities, confidence/epistemic state, and
     provenance refs
5. **Get evidence**
   - return source/evidence references and excerptable source-text context when
     available for a promoted assertion or linked candidate

Everything else is explicitly out of scope for the first slice.

## Proposed Contracts

### Service Layer

Add one dedicated read service, with typed request/response models, for example:

1. `search_entities(...)`
2. `get_entity(...)`
3. `search_promoted_assertions(...)`
4. `get_promoted_assertion(...)`
5. `get_evidence_bundle(...)`

The exact class/module name can be chosen at implementation time, but the
service must own the query semantics so CLI and MCP stay thin.

### CLI Surface

The first CLI should likely add:

1. `search-entities`
2. `get-entity`
3. `search-promoted-assertions`
4. `get-promoted-assertion`
5. `get-evidence`

### MCP Surface

The first MCP layer should mirror the CLI/service capabilities rather than
inventing a different query grammar.

### Phase 1 Contract Decisions (2026-03-31)

The first implementation should use one dedicated module for typed query
contracts plus one read service that returns those models.

Recommended model set:

1. `EntitySearchRequest`
2. `EntitySearchResult`
3. `GetEntityRequest`
4. `EntityDetail`
5. `AssertionSearchRequest`
6. `AssertionSearchResult`
7. `GetPromotedAssertionRequest`
8. `PromotedAssertionDetail`
9. `GetEvidenceRequest`
10. `EvidenceBundle`

Recommended service surface:

1. `search_entities(request: EntitySearchRequest) -> tuple[EntitySearchResult, ...]`
2. `get_entity(request: GetEntityRequest) -> EntityDetail`
3. `search_promoted_assertions(request: AssertionSearchRequest) -> tuple[AssertionSearchResult, ...]`
4. `get_promoted_assertion(request: GetPromotedAssertionRequest) -> PromotedAssertionDetail`
5. `get_evidence(request: GetEvidenceRequest) -> EvidenceBundle`

## Search Semantics

These are fixed unless a later ADR changes them.

1. **Entity search ranking**
   - exact canonical-name match
   - exact alias match
   - exact external-id / reference-label match
   - prefix match
   - substring match
2. **Entity search filters**
   - `query`
   - optional `entity_type`
   - optional `provider`
   - optional `reference_status`
   - optional `limit`
3. **Assertion search filters**
   - optional `predicate`
   - optional `entity_id`
   - optional `text_query`
   - optional `limit`
4. **Evidence lookup**
   - by `assertion_id` as the primary path
   - optional candidate/provenance expansion when directly available
5. **Ordering**
   - deterministic and documented; no "best effort" ordering language

## Failure Semantics

These are fixed for the first slice:

1. invalid filter combinations are `ValueError` at the service boundary;
2. unsupported filter keys are not ignored silently;
3. missing entity/assertion ids raise the repo's typed not-found errors where
   those already exist, or a dedicated query-layer not-found error if needed;
4. empty search results are valid and return an empty tuple, not an error;
5. evidence lookup fails loudly if the referenced promoted assertion exists but
   the supporting candidate/provenance link is inconsistent.

## Response Content Decisions

1. `EntitySearchResult` should include:
   - canonical `identity_id` when available
   - matched `entity_id`
   - display label / matched name
   - entity type
   - match reason including external-id/reference-label matches
2. `EntityDetail` should include:
   - identity bundle when present
   - linked promoted assertion ids
   - linked canonical/alias memberships
   - attached and unresolved external references
3. `AssertionSearchResult` should include:
   - `assertion_id`
   - `predicate`
   - `claim_text`
   - linked entity ids
   - optional confidence/disposition summary
4. `PromotedAssertionDetail` should include:
   - promotion result
   - linked source candidate
   - linked epistemic summary
   - direct provenance refs / artifact links where available
5. `EvidenceBundle` should include:
   - supporting candidate id
   - source text / claim text when available
   - evidence spans
   - provenance/artifact links
   - source metadata refs when available

## Execution Plan

### Phase 0: Inventory Existing Read Paths

1. map current CLI/MCP/report surfaces that already expose pieces of promoted
   state;
2. identify which service/repository modules already provide reusable reads;
3. define the minimal missing read methods instead of duplicating report code.

**Acceptance**

1. implementation starts from real existing seams;
2. the plan does not accidentally duplicate existing report logic.

**Implementation status (2026-03-31): inventory complete**

### Phase 1: Define Typed Query Contracts

1. define request/response models for the five target operations;
2. decide field meanings and failure semantics up front;
3. keep open surfaces typed broadly and truthfully.

**Acceptance**

1. every operation has a typed request/response shape;
2. unsupported filters are explicit errors, not ignored inputs.

**Implementation status (2026-03-31): contract shape pre-decided**

### Phase 2: Implement Shared Read Service

1. add the read service over promoted assertions, entities, identities, and
   provenance/evidence links;
2. keep all DB access behind typed service methods;
3. do not expose raw SQL rows as the user-facing contract.

**Acceptance**

1. one service owns the query semantics;
2. the service can satisfy the five target operations deterministically.

**Implementation status (2026-03-31): complete via `QuerySurfaceService`**

### Phase 3: Add CLI Wrappers

1. add the five CLI commands above;
2. keep them thin and JSON-friendly;
3. preserve existing list/report commands until overlap is intentionally
   resolved later.

**Acceptance**

1. humans can inspect promoted knowledge without opening SQLite directly;
2. CLI output is stable enough for scripting and review.

**Implementation status (2026-03-31): complete**

### Phase 4: Add MCP Wrappers

1. add thin MCP tools for the same five operations;
2. keep the MCP parameter shapes aligned with the service contracts;
3. avoid adding broad natural-language "search everything" tools in the first
   slice.

**Acceptance**

1. agents can browse the governed store directly;
2. MCP tools do not invent a second query model.

**Implementation status (2026-03-31): complete**

### Phase 5: Verify With Real Proof Data

1. verify against the canonical local proof DB;
2. include at least one identity/alias case and one evidence/provenance case;
3. update README or consumer notes only after the surface is actually usable.

**Acceptance**

1. the repo can demonstrate the query surface on real promoted data;
2. parity row "concept/entity browsing and search" is no longer deferred.

**Implementation status (2026-03-31): complete via
`docs/runs/2026-03-31_query_surface_real_proof.md`**

## Required Checks

At minimum, implementation should add:

1. service-level tests for each target operation;
2. CLI tests for the command wiring and failure semantics;
3. MCP integration coverage if MCP wrappers are added in the same slice;
4. one real-proof note or smoke verification over the canonical review DB.

## Acceptance

This plan is ready to promote from `planned` to active implementation when:

1. Phase 0 inventory is complete;
2. the typed query contract is written;
3. the service/CLI/MCP boundary is pre-decided;
4. there is no remaining ambiguity about whether the first slice is promoted
   state only.

The capability is complete enough to mark the parity row recovered when:

1. the five target operations exist;
2. they work on real promoted data;
3. agents and humans can browse governed knowledge without direct SQLite
   inspection.

**Current state (2026-04-02):** the first read-only slice is landed and proved.
Further work under this plan is now widening/hardening work, not first-slice
recovery. The active widening execution block is
[0063_24h_query_browse_widening_block.md](0063_24h_query_browse_widening_block.md).

## Failure Modes

1. the first slice expands into a full retrieval platform and duplicates
   DIGIMON;
2. CLI and MCP wrappers diverge because the service contract was not fixed
   first;
3. evidence/provenance lookup is omitted, yielding a browse surface with weak
   trust value;
4. candidate/proposal review queries are mixed into the promoted-state browse
   surface and make the contract muddy.

## Open Questions / Uncertainty Tracking

### Q1: Should the first implementation add both CLI and MCP, or land CLI first and MCP immediately after?
**Status:** Resolved
**Resolution:** both thin wrappers landed in the same execution block after the
shared service was verified.

### Q2: Should entity search include unresolved external-reference state in the first slice?
**Status:** Resolved
**Why it matters:** external-reference state exists, but it may be better to
keep the first browse surface focused on names, aliases, and promoted
assertions.
**Resolution:** no. The first slice keeps entity search focused on names and
entity type. External-reference state remains available through `get-entity`.

### Q3: Should evidence lookup expose raw source-text excerpts by default or only references unless explicitly requested?
**Status:** Resolved
**Why it matters:** provenance is more useful with excerpts, but source-text
payload size and privacy may matter.
**Resolution:** yes, for the first local/operator-facing slice. `EvidenceBundle`
returns source text when it is already present in stored provenance.

## Landed Through Plan 0063

The query surface now includes:

1. entity search and deterministic entity browse;
2. entity detail with linked promoted assertions;
3. promoted-assertion search and deterministic promoted-assertion browse;
4. `source_ref` and `source_kind` filters on promoted assertions;
5. CLI commands: `list-entities`, `search-entities`, `get-entity`,
   `list-promoted-assertions`, `search-promoted-assertions`,
   `get-promoted-assertion`, and `get-evidence`; and
6. matching MCP browse/search/get tools.

## Next Narrowed Follow-Ons

After Plan `0063`, the next truthful queryability choices are:

1. identity/external-reference-aware browse and filters; or
2. first-class source-artifact query beyond source-centric assertion filters.

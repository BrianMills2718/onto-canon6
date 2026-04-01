# Schema Stability Gate

Status: active

Last updated: 2026-03-31
Workstream: Lane 3 of the post-cutover program

## Current State (2026-03-31)

Phase 2 and the minimum Phase 3 gate are now implemented in this repo:

1. deterministic compatibility artifacts exist under
   `tests/fixtures/compatibility/` for all four gated surfaces;
2. owner checks load those artifacts through `tests/compatibility_helpers.py`;
3. the current baseline verification command is:
   `pytest -q tests/core/test_graph_service.py tests/surfaces/test_governed_bundle.py tests/adapters/test_foundation_assertion_export.py tests/adapters/test_digimon_export.py`

Lane 3 is still active because two things remain open:

1. Q3: whether the DIGIMON consumer proof should become an automated
   cross-repo check;
2. Phase 4: classification and release-note policy for future
   breaking/compatibility-risking changes.

## Purpose

Turn Lane 3 of [0024_post_cutover_program.md](0024_post_cutover_program.md)
into an executable compatibility program instead of a vague promise to
"stabilize schemas."

This plan defines:

1. which `onto-canon6` surfaces are contractual;
2. what counts as a breaking change for each surface;
3. which verification artifacts must exist before a surface can be called
   stable;
4. which changes are allowed to remain experimental.

## Why Now

Lane 2 now has a real first downstream consumer: DIGIMON. That makes "schema
stability" no longer a future nice-to-have. The repo now has at least four
surfaces that other code can rely on:

1. the promoted-graph typed runtime surface used by internal services and
   adapters;
2. the governed bundle export surface;
3. the Foundation Assertion IR export surface;
4. the DIGIMON v1 export seam (`entities.jsonl` / `relationships.jsonl`).

Without an explicit stability gate, the repo can accidentally:

1. change an export shape while thinking it is "just internal refactoring";
2. redefine field meaning without a compatibility check;
3. promote a new consumer while every surface is still implicitly provisional.

## Non-Goals

This plan does not:

1. freeze the raw SQLite schema as a public contract;
2. freeze experimental entity-resolution outputs from Plan 0025;
3. force DIGIMON's richer interchange experiment to happen now;
4. require a general ecosystem registry or release-management framework.

## Pre-Made Decisions

These decisions are fixed for this plan unless a later ADR changes them.

1. **The stability gate applies to consumer-observed typed/model/export
   surfaces, not directly to raw database tables.**
   The SQLite schema may evolve as long as the typed service/export contracts
   remain compatible or are migrated explicitly.
2. **The first gated surfaces are exactly four.**
   No more and no fewer:
   - promoted graph typed surface
   - governed bundle surface
   - Foundation Assertion IR export
   - DIGIMON v1 export seam
3. **Lane 3 is about compatibility truthfulness, not maximum rigidity.**
   We are defining what must be checked before changing a surface, not
   promising that no surface will ever change.
4. **Additive changes are not automatically safe.**
   They are classified as:
   - non-breaking for repo-internal typed surfaces only when existing required
     fields and semantics remain unchanged;
   - compatibility-risking for consumer-facing exports until a consumer or
     parser proves tolerance.
5. **The DIGIMON v1 seam remains supported but explicitly narrow.**
   Lane 3 stabilizes the current thin export/import contract as it exists today;
   it does not silently upgrade that seam into richer alias/passage/provenance
   interchange.
6. **Compatibility evidence must be reproducible from fixtures or real proof
   artifacts already in the repo.**
   Manual memory of a past run does not count.
7. **Every surface gets one owner check.**
   A surface is not "gated" unless at least one concrete test, fixture, or
   snapshot check is named as its compatibility owner.

## Contract Tiers

### Tier 1: Repo-Internal Durable Typed Surfaces

These are not "public APIs" for the whole ecosystem, but they are relied on by
multiple internal services and adapters and therefore need explicit compatibility
rules.

#### Surface A: Promoted Graph Typed Surface

**Primary files**

- `src/onto_canon6/core/graph_models.py`
- `src/onto_canon6/core/graph_service.py`
- `src/onto_canon6/surfaces/graph_report.py`

**Current checks**

- `tests/core/test_graph_service.py`

**Stability target**

The typed meaning of:

- `PromotedGraphAssertionRecord`
- `PromotedGraphRoleFillerRecord`
- `PromotedGraphEntityRecord`
- `CanonicalGraphPromotionResult`

must remain compatible enough that existing surfaces and adapters can still
consume promoted graph state without ad hoc rewrites.

**Breaking changes**

1. removing or renaming required fields on any of the typed models;
2. changing field types incompatibly;
3. changing the meaning of `filler_kind`, `entity_id`, `value`, or
   `normalized_body.roles`;
4. changing promotion semantics so existing idempotence or accepted-only
   assumptions no longer hold;
5. changing report traversal so promoted graph reports no longer expose
   candidate-backed governance context.

**Potentially compatible but gated**

1. adding optional fields to promoted graph models;
2. adding new report summary counters;
3. adding new normalized-body qualifiers outside existing role semantics.

**Owner check**

`tests/core/test_graph_service.py` remains the baseline check until a dedicated
promoted-graph compatibility fixture exists.

### Tier 2: Consumer-Facing Export Surfaces

These are the actual Lane 3 focus because downstream code may parse or depend
on them directly.

#### Surface B: Governed Bundle Surface

**Primary files**

- `src/onto_canon6/surfaces/governed_bundle.py`
- `src/onto_canon6/cli.py` (`export-bundle`)
- `src/onto_canon6/mcp_server.py` (`canon6_export_governed_bundle`)

**Current checks**

- `tests/surfaces/test_governed_bundle.py`
- `tests/integration/test_mcp_server.py`

**Stability target**

The bundle must remain a truthful export of:

- accepted candidate assertions;
- linked ontology-governance state;
- artifact lineage;
- epistemic state;
- explicit scope and summary metadata.

**Breaking changes**

1. removing or renaming top-level bundle fields:
   `workflow_id`, `generated_at`, `scope`, `candidate_bundles`, `summary`;
2. removing or renaming existing fields on `GovernedCandidateBundle`;
3. changing the accepted-candidate export scope by default;
4. changing failure semantics for invalid explicit `candidate_ids`;
5. dropping artifact-lineage or epistemic fields that are currently part of the
   exported record.

**Potentially compatible but gated**

1. adding new optional summary counters;
2. adding new optional bundle metadata fields;
3. adding new optional candidate enrichments while preserving existing fields.

**Owner checks**

- `tests/surfaces/test_governed_bundle.py`
- `tests/integration/test_mcp_server.py`

#### Surface C: Foundation Assertion IR Export

**Primary files**

- `src/onto_canon6/adapters/foundation_assertion_export.py`

**Current checks**

- `tests/adapters/test_foundation_assertion_export.py`
- `tests/pipeline/test_temporal_qualifiers.py`

**Stability target**

Every exported Foundation assertion must preserve:

- `assertion_id`
- `predicate`
- role filler meaning
- qualifiers
- confidence semantics
- provenance refs

for the current supported export shape.

**Breaking changes**

1. removing or renaming required Foundation fields;
2. changing entity filler structure so `entity_id`, `name`, or `entity_type`
   no longer map cleanly;
3. dropping `provenance_refs` or changing them away from source-candidate
   traceability without an explicit contract revision;
4. changing temporal qualifier names or confidence qualifier semantics;
5. removing identity-driven `alias_ids` enrichment without replacing it with an
   explicit equivalent.

**Potentially compatible but gated**

1. adding optional qualifiers;
2. adding optional filler metadata beyond the current shape;
3. expanding Foundation export coverage to more promoted assertions while
   preserving existing field semantics.

**Owner checks**

- `tests/adapters/test_foundation_assertion_export.py`
- `tests/pipeline/test_temporal_qualifiers.py`

#### Surface D: DIGIMON v1 Export Seam

**Primary files**

- `src/onto_canon6/adapters/digimon_export.py`
- DIGIMON consumer: `scripts/import_onto_canon_jsonl.py`,
  `Core/Interop/onto_canon_import.py`

**Current checks**

- `tests/adapters/test_digimon_export.py`
- consumer-side proof in DIGIMON:
  `tests/unit/test_onto_canon_import.py`

**Stability target**

The supported v1 seam is:

1. `entities.jsonl`
2. `relationships.jsonl`
3. current field names and meanings expected by DIGIMON's importer

Nothing richer is implied.

**Breaking changes**

1. renaming the export files;
2. removing or renaming required entity fields:
   `entity_name`, `source_id`, `entity_type`, `description`, `rank`;
3. removing or renaming required relationship fields:
   `src_id`, `tgt_id`, `relation_name`, `description`, `weight`, `keywords`,
   `source_id`;
4. changing current missing-endpoint emission semantics without coordinating the
   DIGIMON importer contract;
5. changing field meaning so DIGIMON's importer would still parse the file but
   interpret the graph differently.

**Potentially compatible but gated**

1. adding extra JSON fields that DIGIMON currently ignores;
2. improving descriptions or keywords while preserving existing required fields;
3. tightening docs around repo-root invocation requirements.

**Owner checks**

- `tests/adapters/test_digimon_export.py`
- DIGIMON-side `tests/unit/test_onto_canon_import.py`
- one real export/import proof over the Shield AI review DB remains the current
  proof artifact for the supported v1 seam

## Compatibility Policy

### What counts as stable

A surface may be called "stable enough to rely on" only when all of the
following are true:

1. its breaking-change rules are written down in this plan or a successor ADR;
2. its owner checks are green;
3. at least one reproducible fixture, snapshot, or real proof artifact is named;
4. repo docs describe the surface as supported rather than experimental.

### What does not count as stable

The following are explicitly insufficient:

1. "the code looks the same";
2. one manual CLI run with no recorded artifact;
3. an adapter test with no consumer-side proof for a consumer-facing seam;
4. saying a surface is "schema-stable" without naming which fields are gated.

## Phase 2 Decision Update (2026-03-31)

Phase 2 now has a concrete artifact layout. The compatibility artifacts will
live under `tests/fixtures/compatibility/` with one directory per gated
surface.

### Artifact Inventory

| Surface | Compatibility artifact | Owner test/check | Normalization rules |
|---------|------------------------|------------------|---------------------|
| Surface A — promoted graph typed surface | `tests/fixtures/compatibility/promoted_graph/minimal_promotion_result.json` | `tests/core/test_graph_service.py` | normalize generated ids and timestamps: `assertion_id`, `source_candidate_id`, `first_candidate_id`, `promoted_at`, `created_at` |
| Surface B — governed bundle surface | `tests/fixtures/compatibility/governed_bundle/minimal_governed_bundle.json` | `tests/surfaces/test_governed_bundle.py` with secondary CLI/MCP coverage in `tests/integration/test_mcp_server.py` | normalize `generated_at`, candidate/proposal/artifact ids, overlay-application ids, epistemic timestamps, and any temp-path-like values |
| Surface C — Foundation Assertion IR export | `tests/fixtures/compatibility/foundation_ir/minimal_foundation_assertion.json` | `tests/adapters/test_foundation_assertion_export.py` with temporal coverage in `tests/pipeline/test_temporal_qualifiers.py` | no timestamp normalization by default; keep deterministic helper ids and sorted alias lists |
| Surface D — DIGIMON v1 export seam | `tests/fixtures/compatibility/digimon_v1/minimal_entities.jsonl` and `tests/fixtures/compatibility/digimon_v1/minimal_relationships.jsonl` | `tests/adapters/test_digimon_export.py` plus DIGIMON `tests/unit/test_onto_canon_import.py` | fixture pair should be deterministic; real-data proof notes do not replace the fixture pair |

### Artifact Design Decisions

1. **Surface A snapshots the promotion result, not the raw DB.**
   The artifact represents the typed promotion surface consumed by adapters and
   reports, not internal SQLite rows.
2. **Surface B snapshots the Python bundle export shape, not the CLI text
   rendering.**
   CLI and MCP checks remain secondary path verification over the same typed
   structure.
3. **Surface C uses one minimal deterministic assertion fixture, with temporal
   qualifiers covered by the existing temporal test instead of a second
   snapshot.**
4. **Surface D uses a fixture pair because the contract is intrinsically a
   two-file seam.**
   That pair is the compatibility artifact.
5. **Real proof artifacts remain supplemental evidence only.**
   The Shield AI export/import proof is important, but Lane 3's baseline gate
   needs deterministic local artifacts first.

### Normalization Policy

1. normalize generated identifiers when the value is an implementation detail
   rather than a contract field;
2. preserve identifiers when they are the contract field under test
   (for example Foundation `assertion_id` in the minimal deterministic helper);
3. strip timestamps and temp paths from snapshots unless the timestamp field is
   itself contractual;
4. sort unordered collections before writing snapshots when the surface does not
   promise insertion order;
5. keep role ordering and JSONL row ordering stable whenever the consumer
   currently relies on deterministic order.

## Execution Plan

### Phase 0: Freeze The Surface Inventory

1. adopt the four surfaces above as the authoritative Lane 3 scope;
2. reject scope creep unless a real consumer now depends on another surface;
3. link Lane 3 in Plan 0024 to this plan.

**Acceptance**

1. Lane 3 has one execution surface;
2. the plan index points to this file;
3. no additional contract surface is implied by vague wording elsewhere.

### Phase 1: Add Explicit Compatibility Rules To Repo Docs

1. update the current-program docs to name this plan as Lane 3's execution
   surface;
2. keep the supported/exported vs experimental distinction explicit;
3. document where DIGIMON-side verification lives for Surface D.

**Acceptance**

1. top-level planning docs no longer say only "schema stability" without a
   concrete execution surface;
2. DIGIMON-facing docs do not overclaim richer interchange support.

### Phase 2: Define Minimal Compatibility Artifacts

1. create the artifact files listed in the Phase 2 decision table;
2. implement the normalization policy above in reusable helper code if needed;
3. keep all baseline compatibility artifacts under
   `tests/fixtures/compatibility/`;
4. use real proof artifacts only as supplemental evidence, not as the sole
   compatibility gate.

**Acceptance**

1. each surface has one named compatibility artifact path;
2. normalization rules are pre-decided before implementation;
3. future implementation does not need to decide where fixtures live.

**Implementation status (2026-03-31): complete**

### Phase 3: Implement The Minimum Gate

1. add or tighten the owner checks so each surface has at least one explicit
   compatibility check;
2. do not broaden the implementation beyond the four surfaces above;
3. ensure the checks fail loudly when a gated field or behavior changes.

#### Phase 3 Pre-Made Decisions

1. **Extend the existing owner tests instead of creating a new compatibility
   test suite.**
   The compatibility assertions should live in:
   - `tests/core/test_graph_service.py`
   - `tests/surfaces/test_governed_bundle.py`
   - `tests/adapters/test_foundation_assertion_export.py`
   - `tests/adapters/test_digimon_export.py`
2. **Put shared snapshot/normalization helpers in one dedicated test helper
   module rather than copying logic into each test file.**
   Default location:
   `tests/compatibility_helpers.py`
3. **Do not add a new Make target for Lane 3 yet.**
   The first implementation slice should rely on the existing targeted pytest
   commands listed in this plan.
4. **Use file-based expected artifacts checked into the repo, not inline giant
   Python literals.**
   The tests should load the files under `tests/fixtures/compatibility/`.
5. **Do not automate cross-repo DIGIMON proof execution in this first slice.**
   Keep the DIGIMON import unit as the automated consumer-side owner check and
   keep the real Shield AI proof as documented supplemental evidence.

**Acceptance**

1. every surface has one runnable compatibility owner check;
2. Lane 3 can point to actual commands/tests instead of intentions.

**Implementation status (2026-03-31): minimum gate complete**

### Phase 4: Classify Future Changes

1. define the release-note expectation for:
   - breaking
   - compatibility-risking
   - non-breaking
2. require plan or ADR updates when a breaking change is intentional;
3. require consumer coordination before breaking Surface C or D.

**Acceptance**

1. future agents can classify a change without reopening architecture debate;
2. consumer-facing exports cannot change casually.

## Required Checks

These are the current baseline checks. Phase 3 may refine them, but Lane 3
must not claim completion without at least these classes of evidence.

| Surface | Baseline check |
|---------|----------------|
| Promoted graph typed surface | `pytest -q tests/core/test_graph_service.py` |
| Governed bundle surface | `pytest -q tests/surfaces/test_governed_bundle.py tests/integration/test_mcp_server.py` |
| Foundation Assertion IR export | `pytest -q tests/adapters/test_foundation_assertion_export.py tests/pipeline/test_temporal_qualifiers.py` |
| DIGIMON v1 export seam | `pytest -q tests/adapters/test_digimon_export.py` plus DIGIMON `tests/unit/test_onto_canon_import.py` |

## Failure Modes

1. a raw DB migration is mistaken for a safe compatibility-preserving change
   without checking typed/export surfaces;
2. a consumer-facing field is added or repurposed and everyone assumes parsers
   will ignore it;
3. DIGIMON v1 support is overclaimed as a richer interchange contract;
4. Foundation IR and governed bundle drift independently even though both are
   supposed to express governed promoted state;
5. a passing unit test suite masks an unverified consumer seam because no
   cross-repo proof artifact is maintained.

## Open Questions / Uncertainty Tracking

### Q1: Should Lane 3 snapshot raw JSON outputs or normalize them first?
**Status:** Resolved
**Decision:** normalize volatile fields first; do not snapshot raw temp paths
or timestamps.

### Q2: Does Surface A need a dedicated compatibility fixture beyond `test_graph_service.py`?
**Status:** Resolved
**Decision:** yes. Surface A will use
`tests/fixtures/compatibility/promoted_graph/minimal_promotion_result.json`
with `tests/core/test_graph_service.py` as the owner check.

### Q3: Should the DIGIMON consumer proof remain a real-data smoke artifact or become a fully automated cross-repo check?
**Status:** Open
**Decision pressure:** Low for now
**Current default:** keep the real-data proof note as the baseline and defer a
fully automated cross-repo check until the v1 seam stops shifting operationally.

### Q4: Should additive optional fields on Foundation IR and governed bundle be treated as breaking by default?
**Status:** Resolved for now
**Decision:** treat them as compatibility-risking, not automatically safe.
They require explicit check updates and doc review before promotion.

## Exit Criteria

Lane 3 is ready to close only when:

1. the four surfaces above are the explicit authoritative scope;
2. each surface has written breaking-change rules;
3. each surface has at least one reproducible compatibility owner check;
4. the repo can name which future changes are breaking, compatibility-risking,
   or non-breaking without reopening the plan.

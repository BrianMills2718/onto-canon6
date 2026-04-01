# Schema Stability Gate

Status: complete (all 4 phases done, all exit criteria met)

Last updated: 2026-04-01
Workstream: Lane 3 of the post-cutover program

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

### Phase 2: Define Minimal Compatibility Artifacts — COMPLETE (2026-04-01)

Fixtures live under `tests/fixtures/compatibility/`:
- `promoted_graph.json` — Surface A (3 models)
- `governed_bundle.json` — Surface B (2 models)
- `foundation_ir.json` — Surface C (1 model)
- `digimon_v1_export.json` — Surface D (2 models)

Each fixture records the model's required field names and type annotations.
Volatile fields (timestamps, nondeterministic IDs) are not in the fixture —
only field schema contracts.

### Phase 3: Implement The Minimum Gate — COMPLETE (2026-04-01)

9 tests in `tests/compatibility/test_schema_stability.py`:
- Surface A: 3 tests (assertion, entity, role_filler field checks)
- Surface B: 2 tests (workflow_bundle, candidate_bundle field checks)
- Surface C: 1 test (foundation_assertion field check)
- Surface D: 3 tests (entity fields, relationship fields, type stability)

All tests verify that required fields are not removed and types are not
changed. Breaking changes produce explicit assertion messages naming the
affected model and field.

### Phase 4: Classify Future Changes — COMPLETE (2026-04-01)

Every change that touches a gated surface must be classified before merging.

#### Breaking changes (require ADR + consumer coordination)

A change is **breaking** if it would cause existing consumers to fail or
produce incorrect results without code changes on their side:

1. Removing or renaming a required field on any gated model.
2. Changing a field's type incompatibly (e.g., `str` → `int`, `list` → `dict`).
3. Changing the semantic meaning of a field (e.g., `weight` from confidence to
   frequency) without renaming it.
4. Changing export file names or CLI command names that consumers invoke.
5. Changing promotion, acceptance, or review semantics that alter what data
   appears in exports.

**Required before landing a breaking change:**
- New ADR documenting the change and rationale
- Consumer coordination: notify DIGIMON maintainer (for Surface D) or
  Foundation IR consumers (for Surface C) before merging
- Update the canonical compatibility fixture to match the new schema
- All compatibility tests must pass against the updated fixtures

#### Compatibility-risking changes (require fixture review)

A change is **compatibility-risking** if it might affect consumers but
doesn't necessarily break them:

1. Adding a new optional field to a gated model.
2. Adding a new value to an enum-like string field.
3. Changing default values for optional fields.
4. Adding new entries to export files (e.g., new entity types).

**Required before landing:**
- Review whether any consumer parses with `extra="forbid"` (would reject new fields)
- Update compatibility fixtures if field lists change
- No ADR required, but document in commit message

#### Non-breaking changes (no special process)

1. Internal code refactoring that doesn't change model field names or types.
2. Adding new tests or fixtures.
3. Changing prompt templates (affects extraction quality, not schema).
4. Changing model selection (affects extraction quality, not schema).
5. Documentation updates.

#### Examples

| Change | Classification | Required |
|--------|---------------|----------|
| Rename `entity_name` to `name` on DigimonEntityRecord | Breaking | ADR + DIGIMON coordination |
| Add `confidence_source: str \| None` to FoundationAssertion | Compatibility-risking | Fixture review |
| Change extraction model from gemini-2.5-flash to gemini-3-flash | Non-breaking | Commit message |
| Remove `description` from DigimonRelationshipRecord | Breaking | ADR + DIGIMON coordination |
| Add new test in tests/compatibility/ | Non-breaking | Nothing special |

## Required Checks

### Schema compatibility gate (Phase 3, implemented 2026-04-01)

```bash
pytest -q tests/compatibility/test_schema_stability.py
```

9 tests covering all 4 surfaces. Fails loud when gated fields are removed or
types change.

### Surface-specific baseline checks

| Surface | Compatibility check | Functional check |
|---------|-------------------|-----------------|
| Promoted graph | `tests/compatibility/test_schema_stability.py::TestSurfaceA_PromotedGraph` | `tests/core/test_graph_service.py` |
| Governed bundle | `tests/compatibility/test_schema_stability.py::TestSurfaceB_GovernedBundle` | `tests/surfaces/test_governed_bundle.py` |
| Foundation IR | `tests/compatibility/test_schema_stability.py::TestSurfaceC_FoundationIR` | `tests/adapters/test_foundation_assertion_export.py` |
| DIGIMON v1 export | `tests/compatibility/test_schema_stability.py::TestSurfaceD_DigimonExport` | `tests/adapters/test_digimon_export.py` + DIGIMON-side tests |

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
**Status:** Resolved (2026-04-01)
**Decision:** Fixture strategy is schema-contract based (field names + types),
not snapshot-based. No volatile fields in fixtures. Normalization not needed.

### Q2: Does Surface A need a dedicated compatibility fixture beyond `test_graph_service.py`?
**Status:** Resolved (2026-04-01)
**Decision:** Yes — `tests/fixtures/compatibility/promoted_graph.json` now
exists with field contracts for all 3 models. `test_schema_stability.py`
checks it.

### Q3: Should the DIGIMON consumer proof remain a real-data smoke artifact or become a fully automated cross-repo check?
**Status:** Resolved for now
**Decision:** Real-data proof note remains the baseline. The schema compatibility
test (`TestSurfaceD_DigimonExport`) catches field-level breaks. Cross-repo
automation deferred until v1 seam stabilizes further.

### Q4: Should additive optional fields on Foundation IR and governed bundle be treated as breaking by default?
**Status:** Resolved (2026-04-01)
**Decision:** Treat as compatibility-risking (Phase 4 classification). Requires
fixture review but not ADR or consumer coordination.

## Exit Criteria — ALL MET (2026-04-01)

| Criterion | Status |
|---|---|
| Four surfaces are the explicit authoritative scope | ✓ Phase 0 |
| Each surface has written breaking-change rules | ✓ Phases 1 + 4 |
| Each surface has at least one reproducible compatibility check | ✓ Phase 3 (9 tests) |
| Future changes classifiable as breaking/compatible/non-breaking | ✓ Phase 4 |

**Plan 0026 is COMPLETE.** Lane 3 of Plan 0024 is closed.

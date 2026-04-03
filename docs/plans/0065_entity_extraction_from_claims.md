# Plan 0065 — Entity Extraction from grounded-research Claims

**Created**: 2026-04-02  
**Status**: planned (not yet active)  
**Trigger**: Palantir pipeline validation showed 22 claims promoted → 0 DIGIMON entities

## Problem

grounded-research exports `ClaimRecord` objects with `claim_type="fact_claim"`.
These are imported into onto-canon6 via `import_shared_claims()` which creates
assertions with predicate `shared:fact_claim` — a role-free predicate (no ARG0/ARG1).

Role-free assertions produce no DIGIMON relationships (`digimon_export.py:348`
skips assertions with zero entity fillers). They also produce no DIGIMON
entities since entity nodes are derived from entity fillers.

**Result**: the entire grounded-research → onto-canon6 → DIGIMON pipeline
produces a governed claim store but an empty entity graph. DIGIMON becomes
a claim database, not a knowledge graph.

**For the research_v3 path**, this is not a problem because research_v3
already extracts FtM-typed entities with ARG0/ARG1 roles. Entity-rich
grounded-research runs are the gap.

## Implementation Note: entity_refs Already Exists

**Critical finding (Plan 0032 Phase 3)**: `ClaimRecord` already has an
`entity_refs: list[EntityReference]` field. The onto-canon6 import adapter
at `adapters/grounded_research_import.py:56-70` ALREADY handles it:

```python
elif claim.entity_refs:
    # Build minimal roles from entity references so promotion can extract entities.
    role_names = ["subject", "object", "indirect_object", "modifier"]
    for i, eref in enumerate(claim.entity_refs):
        rname = role_names[i] if i < len(role_names) else f"arg{i}"
        roles_dict[rname] = [{"kind": "entity", "entity_id": eref.entity_id,
                               "entity_type": eref.entity_type, "name": eref.name}]
```

**Implication**: No new field needed. No schema change to epistemic-contracts.
grounded-research just needs to **populate `entity_refs`** in the ClaimRecord
it exports, and the adapter will automatically map them to role fillers.

`entity_refs` vs `entity_annotations` — these are the SAME concept:
- `entity_refs` = the existing `ClaimRecord` field for structured entity references
- `entity_annotations` = the name used in the original plan doc (now superseded)

The correct term going forward is `entity_refs` (it's the actual field name).

## Two Options

### Option A: NER Post-Processing in onto-canon6 Import Adapter

Add a step in `adapters/grounded_research_import.py` that runs NER over the
claim `statement` text, synthesizes `entity_refs` before creating the assertion.

**Pros:** No changes to grounded-research or epistemic-contracts  
**Cons:** Requires LLM call per claim at import time; entity types are guessed;
adds cost and latency to a deterministic adapter

### Option B: grounded-research Populates entity_refs (Recommended)

grounded-research adds an entity extraction stage (Stage 5b or post-Stage 5)
that extracts subject/object entities from each claim and populates
`entity_refs` in the ClaimRecord before export.

```python
# grounded-research sets this on each ClaimRecord:
claim.entity_refs = [
    EntityReference(entity_id="E-001", name="Palantir Technologies Inc.",
                    entity_type="organization"),
    EntityReference(entity_id="E-002", name="U.S. Army",
                    entity_type="government_org"),
]
```

The onto-canon6 import adapter **already reads this field** — no onto-canon6
changes needed once grounded-research populates it.

**Pros:**
- Entity refs grounded in evidence context (grounded-research has the evidence)
- onto-canon6 import stays thin and deterministic (no LLM calls)
- Backward compatible — `entity_refs` defaults to empty list
- No schema changes needed anywhere

**Cons:** grounded-research must implement the entity extraction stage first

## Decision

**Option B — grounded-research populates entity_refs (existing field).**

**Scope**: Changes needed in ONE place only (not three):
1. grounded-research: add entity extraction stage → populate `entity_refs`
2. epistemic-contracts: NO CHANGE (field already exists)
3. onto-canon6: NO CHANGE (adapter already handles entity_refs)

## Implementation Scope (Revised — One Repo Only)

### grounded-research only

- Add entity extraction stage (Stage 5b) after adjudication
- LLM prompt: given claim statement + evidence context, extract subject and
  object entities with name and entity_type
- Populate `entity_refs: list[EntityReference]` on each ClaimRecord before export
- `EntityReference(entity_id, name, entity_type)` is already in epistemic-contracts
- The `shared_export.py` `_load_handoff_stage_based()` passes entity data through

### epistemic-contracts — NO CHANGE NEEDED

`ClaimRecord.entity_refs: list[EntityReference]` already exists.

### onto-canon6 — NO CHANGE NEEDED

`adapters/grounded_research_import.py:56-70` already handles `entity_refs` → role fillers.

## Acceptance Criteria

1. Palantir handoff.json with entity_refs populated → `make pipeline-gr` produces
   `>0` DIGIMON entities and `>0` DIGIMON relationships
2. EU sanctions handoff.json (no entity_refs) still imports as role-free claims
3. No regression on existing 562 onto-canon6 tests
4. grounded-research: 2 new tests for entity_refs round-trip

## Sequencing

**Not yet active.** Activates when a grounded-research session adds Stage 5b
entity extraction. Current priority: Plan 0066 (Anduril investigation) using
the research_v3 path, which already produces entity-rich output via FtM entities.

## Failure Modes

- LLM entity extraction produces wrong entity types → entity resolution normalizes;
  document in KNOWLEDGE.md
- Unary claims ("Palantir is profitable") → leave entity_refs empty; falls back
  to role-free import automatically
- entity_refs populated but entity_type strings don't map to oc: types → import
  adapter uses the string as-is; entity resolution will normalize later

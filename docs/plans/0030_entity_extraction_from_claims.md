# Plan 0030 — Entity Extraction from grounded-research Claims

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

## Two Options

### Option A: NER Post-Processing in onto-canon6 Import Adapter

Add a step in `adapters/grounded_research_import.py` that runs NER over the
claim `statement` text, identifies entity mentions, and synthesizes
ARG0/ARG1 role fillers before creating the candidate assertion.

**Pros:**
- No changes to grounded-research or epistemic-contracts
- onto-canon6 controls entity extraction quality

**Cons:**
- NER over free-text claim statements is noisy — claims like "Palantir holds an
  Enterprise Agreement with the U.S. Army" would need to produce
  `ARG0: Palantir, ARG1: U.S. Army` — requires LLM call per claim
- Adds LLM cost and latency to the import adapter
- Entity types are guessed, not grounded in grounded-research's actual evidence
- Entity resolution will have to fix names derived from LLM NER

### Option B: grounded-research Emits Entity-Role Annotations (Recommended)

grounded-research adds an entity annotation stage (Stage 5b or post-Stage 5)
that annotates each claim with structured entity pairs:

```json
{
  "claim_id": "CL-001",
  "statement": "Palantir holds an Enterprise Agreement with the U.S. Army",
  "entity_annotations": [
    {"role": "subject", "name": "Palantir Technologies Inc.", "entity_type": "organization"},
    {"role": "object", "name": "U.S. Army", "entity_type": "government_org"}
  ]
}
```

These annotations are included in the handoff.json (extending `ClaimLedgerEntry`)
and surfaced in `ClaimRecord` via a new optional field `entity_annotations`.

The `import_shared_claims()` adapter in onto-canon6 maps annotations to
typed role fillers: subject→ARG0, object→ARG1.

**Pros:**
- Entity annotations are grounded in grounded-research's adjudication context
- grounded-research models see the evidence when annotating — better quality
- onto-canon6 import stays thin (no LLM calls)
- entity_annotations is optional — existing handoffs without it still work

**Cons:**
- Requires changes in 3 places: grounded-research stage, epistemic-contracts
  `ClaimRecord`, onto-canon6 import adapter
- grounded-research must be updated before this produces results

## Decision

**Recommended: Option B.**

Rationale:
1. Quality — grounded-research models have evidence context that onto-canon6 lacks
2. Separation of concerns — import adapter stays deterministic
3. Backward compatibility — optional field, existing handoffs unaffected
4. Matches the existing pattern — research_v3 already does this at the source

## Implementation Scope

### grounded-research (owned by grounded-research team/session)

- Add `entity_annotations: list[EntityAnnotation] | None = None` to
  `ClaimLedgerEntry` model
- Add Stage 5b LLM prompt: given claim statement + evidence, extract
  subject/object entity pairs with entity type
- Run Stage 5b after Stage 5 (adjudication), before handoff export
- Include annotations in `stage_5_verification_result.updated_claim_ledger[]`

### epistemic-contracts (shared library)

- Add `entity_annotations: list[EntityAnnotation] | None = None` to `ClaimRecord`
- Define `EntityAnnotation(role: str, name: str, entity_type: str)` dataclass

### onto-canon6 (this repo)

- Update `adapters/grounded_research_import.py::import_shared_claims()`:
  if `claim.entity_annotations` is not None:
    - create typed role fillers from subject/object annotations
    - map entity_type strings to onto-canon6 CURIE types (org→`oc:Organization` etc.)
  else:
    - import as role-free `shared:fact_claim` (current behavior — backward compatible)
- Update `load_handoff_claims()` tests in grounded-research to use fixtures with annotations

## Acceptance Criteria

1. Palantir handoff.json with entity annotations → `make pipeline-gr` produces
   `>0` DIGIMON entities and `>0` DIGIMON relationships
2. EU sanctions handoff.json (no annotations) still imports correctly as role-free claims
3. No regression on existing 562 onto-canon6 tests
4. grounded-research: 2 new tests for annotated claims round-trip

## Sequencing

This plan is **not yet active**. It activates when:
- Either: a fresh grounded-research session is started to add entity annotation
- Or: the team decides Option A (import-side NER) is preferable

Current priority: Plan 0031 (next real investigation) using the research_v3 path,
which already produces entity-rich output.

## Failure Modes

- LLM entity extraction produces wrong entity types → entity resolution must
  normalize; document in KNOWLEDGE.md
- subject/object model doesn't cover all claim structures (e.g., unary claims
  "Palantir is profitable") → annotations field is None for unary claims, falls
  back to role-free import
- epistemic-contracts schema change breaks existing consumers → add field as
  optional with `None` default to maintain backward compatibility

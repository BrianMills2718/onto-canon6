# Shared-Assertion Semantics Evaluation

**Date:** 2026-04-04  
**Status:** Decision document — thin semantics are sufficient for the current phase with identified enrichment path  
**Context:** Closes the open question from Plan 0070 and HANDOFF.md session 7

---

## What "Thin Shared-Assertion Semantics" Currently Means

The memo transport path (research_v3 → epistemic-contracts → onto-canon6 → DIGIMON)
produces DIGIMON relationship records with the predicate `shared:assertion` for every
finding regardless of the actual relationship type described. This happens because:

1. **research_v3 memo findings never set `predicate`** — the `_finding_to_shared()`
   function in `research_v3/shared_export.py` always constructs `ClaimRecord` with
   `claim_type="assertion"` and `predicate=None`.

2. **onto-canon6 falls back to `shared:{claim_type}`** — in
   `adapters/grounded_research_import.py`, when `claim.predicate` is None the
   import adapter sets `payload["predicate"] = f"shared:{claim.claim_type}"`,
   yielding the string `"shared:assertion"`.

3. **DIGIMON flat export uses the predicate verbatim** — the DIGIMON export adapter
   writes `relation_name=assertion.predicate`, so every memo-derived edge in
   DIGIMON carries the label `"shared:assertion"`.

The result: a claim like *"Palantir was awarded a $250M contract by the DoD"* and a
claim like *"Keith Alexander joined Palantir's board"* both produce a DIGIMON edge
labelled `shared:assertion`. The entity nodes (Palantir, DoD, Keith Alexander) are
properly typed; only the relationships are undifferentiated.

**The graph-backed path is not affected.** Claims sourced from `research_v3 graph.yaml`
carry explicit `claim_type` values (`relationship_claim`, `financial_claim`, etc.) and
sometimes explicit predicates; these flow through as richer edge labels
(e.g., `shared:relationship_claim`). The Foundation IR export is also unaffected
because it exports the full `PromotedGraphAssertionRecord` with `normalized_body`,
not the flat DIGIMON view.

---

## Limitations of Thin Semantics

### Limitation 1 — Relationship-Specific Graph Queries Are Impossible

A consumer working with the DIGIMON graph cannot issue relationship-type-specific
queries using the memo-derived subgraph. Queries like:

- "Find all contracts awarded to Palantir" (vs. "Find all board appointments at Palantir")
- "Show employment relationships in this graph"
- "What financial transactions flow through this entity?"

…return the same undifferentiated set of `shared:assertion` edges. The entities are
queryable; the semantic structure of the relationships is not. For OSINT use cases where
the *type* of connection between organisations matters (employment, contract, investment,
enforcement action), this is a material limitation. It collapses semantically distinct
relationship classes into a single uninformative label.

### Limitation 2 — Cross-Investigation Tension Detection Cannot Distinguish Claim Types

The epistemic engine's tension detection (implemented in `extensions/`) flags
confidence conflicts between assertions sharing the same predicate. When all memo
findings carry `shared:assertion`, the engine treats *any* two claims about the same
pair of entities as potentially in tension — even claims about entirely different
relationship types. A claim that Palantir *won* a contract and a separate claim that
Palantir *lost* a bid for a different contract will both be labelled `shared:assertion`
and may surface as spurious tensions, reducing the signal quality of conflict detection.
Conversely, genuine predicate-level conflicts (e.g., two sourced values for an
acquisition price) are indistinguishable from unrelated assertions, making conflict
resolution harder for both agents and humans.

### Limitation 3 (Secondary) — Downstream Semantic Validation Is Blocked

Domain-specific constraint validation (e.g., "a `shared:financial_claim` must carry a
currency and an amount") cannot be applied to memo-derived assertions because the
finer-grained predicate is absent. This blocks the eventual implementation of
pack-level predicate validators and means that ontology pack rules cannot fire on the
most common claim type in live investigations.

---

## Is the Current State Sufficient?

**Yes — for the current phase.** The memo transport now reaches DIGIMON with correctly
typed entities and non-zero relationship counts (proof: Palantir contract-profile run →
23 findings → 28 entities + 23 DIGIMON edges). The research workbench can navigate
entities and read claim text. No active consumer is blocked by generic edge labels today.

**No — for the phase described in the Roadmap Tier 1 goal.** The definition of "done"
requires a real OSINT investigation that uses onto-canon6 as its governed assertion
store *providing answers*, not just storing claims. Answering relationship-specific
queries (the core OSINT value) requires typed edges. Generic `shared:assertion` labels
are sufficient proof-of-transport but not sufficient for production OSINT value.

The current state is therefore correct to leave in place while other prerequisites
(diverse domain coverage, stable consumer integration) are completed, but it should not
be treated as a permanent design.

---

## Proposed Next Steps

### Option A — Enrich at Import (Recommended for Onto-Canon6 Phase)

Add an optional predicate-inference step inside `adapters/grounded_research_import.py`
(or a dedicated `adapters/predicate_enrichment.py` module) that, for claims with
`predicate=None` and non-empty `entity_refs`, calls a lightweight LLM to classify the
relationship type from the claim text and entity types.

```
ClaimRecord(predicate=None, statement="Palantir was awarded $250M contract by DoD")
    ↓ (predicate_enrichment, optional, off by default)
ClaimRecord(predicate="oc:awarded_contract")
    ↓ (existing import path, unchanged)
PromotedGraphAssertionRecord(predicate="oc:awarded_contract")
    ↓ (existing DIGIMON export, unchanged)
DigimonRelationshipRecord(relation_name="oc:awarded_contract")
```

**Properties:**
- Transparent to research_v3 (no upstream change required)
- Controlled by import config flag (`enrich_predicates: true/false`)
- Testable within onto-canon6 CI using fixed claim fixtures
- Cost is proportional to memo size (~1 LLM classification call per claim batch)
- Preserves existing fallback for claims with no entity refs

### Option B — Enrich at Source (Higher Leverage, Higher Scope)

Extend `research_v3/shared_export.py` to infer and set `predicate` on `ClaimRecord`
during memo export. This benefits all consumers of epistemic-contracts simultaneously
but requires coordinated changes across two repos.

### Option C — Do Nothing (Defer Indefinitely)

Accept that DIGIMON receives untyped memo edges and rely on the full claim text for
any semantic interpretation. This is viable if consumers are always LLM-powered
(which can read `description` fields) and never need graph-traversal semantics.
Not recommended once the workbench enters production use.

### Decision

**Proceed with Option A, gated on the first consumer that needs typed edges.**

Specifically:
1. Leave the current thin semantics in place for all active investigations.
2. When an investigation query is formulated that requires relationship-type
   discrimination (e.g., "show all employment relationships"), implement
   Option A (import-side predicate inference, off by default, toggled per import).
3. Register a predicate vocabulary for memo claims in
   `ontology_packs/shared_import/` before implementation so the enrichment
   produces stable, typed labels rather than free-form strings.
4. Document the predicate vocabulary in a follow-on ADR before merging.

No code changes are needed now. This document captures the decision so that the
next session working on consumer query semantics starts from a clear architectural
position rather than re-deriving the analysis.

---

## Integration Points for Shared Assertions

The shared-assertion semantic seam touches five concrete locations in the
onto-canon6 codebase. Each is an integration point where richer semantics could
be introduced. The table below maps each point to its role in the pipeline and
the enrichment opportunity it presents.

### Point 1 — Import Adapter Predicate Fallback

**File:** `src/onto_canon6/adapters/grounded_research_import.py`
**Mechanism:** When `claim.predicate` is `None`, the adapter sets
`payload["predicate"] = f"shared:{claim.claim_type}"`.
**Enrichment opportunity:** Insert an optional predicate-inference call *before*
the fallback. If inference succeeds, set `payload["predicate"]` to the inferred
value; otherwise fall through to the existing `shared:{claim_type}` default.
This is the recommended Option A insertion point.

### Point 2 — Ontology Pack Predicate Vocabulary

**File:** `ontology_packs/shared_import/0.1.0/predicate_types.jsonl`
**Mechanism:** Declares the six known predicate IDs (`shared:fact_claim`,
`shared:relationship_claim`, `shared:financial_claim`, `shared:temporal_claim`,
`shared:finding`, `shared:assertion`).
**Enrichment opportunity:** Extend the vocabulary with domain-specific predicates
(e.g., `oc:awarded_contract`, `oc:board_appointment`, `oc:employed_by`) so that
inferred predicates from Point 1 land in a controlled vocabulary rather than
producing free-form strings. This vocabulary extension must precede any
enrichment implementation (see Decision item 3).

### Point 3 — Epistemic Tension Detection

**File:** `src/onto_canon6/extensions/epistemic/service.py`
(method `_build_tension_record`)
**Mechanism:** Tension pairs are only created between assertions sharing the same
predicate. With all memo claims as `shared:assertion`, every pair of claims on
the same entity pair is eligible for tension, inflating spurious detections.
**Enrichment opportunity:** Richer predicates from Point 1 would naturally reduce
tension noise because claims about different relationship types would no longer
share a predicate. No changes needed in the tension engine itself — it already
filters by predicate equality.

### Point 4 — DIGIMON Export Adapter

**File:** `src/onto_canon6/adapters/digimon_export.py`
(method `_convert_relationships`)
**Mechanism:** Sets `relation_name=assertion.predicate` verbatim on every
exported `DigimonRelationshipRecord`.
**Enrichment opportunity:** None needed here directly — the export is already
faithful to whatever predicate is stored. Once Point 1 produces richer
predicates, DIGIMON edges automatically carry the enriched labels without export
changes.

### Point 5 — Import Profile Configuration

**File:** `profiles/shared_import_permissive/0.1.0/manifest.yaml`
**Mechanism:** The permissive profile uses `mode: open` and
`proposal_policy: reject`, accepting any claim without requiring known
predicates.
**Enrichment opportunity:** When the predicate vocabulary (Point 2) is extended,
a stricter profile variant could be introduced that validates inferred predicates
against the pack vocabulary. The permissive profile should remain the default for
backward compatibility.

### Point 6 — research_v3 Claim-Type Mapping (Cross-Repo)

**File:** `src/onto_canon6/adapters/research_v3_import.py`
(function `_map_claim_type_to_predicate`)
**Mechanism:** Maps graph-backed research_v3 claim types to `rv3:`-prefixed
predicates (`rv3:asserts_fact`, `rv3:asserts_relationship`, etc.). This mapping
is *not* used for memo-backed claims because they arrive via
`grounded_research_import.py`, not `research_v3_import.py`.
**Enrichment opportunity:** If Option B (source-side enrichment) were chosen,
the analogous mapping logic would need to be added in
`research_v3/shared_export.py`. For Option A, this file requires no changes.

### Comparison: Graph-Backed vs Memo-Backed Predicate Paths

| Aspect | Graph-backed (graph.yaml) | Memo-backed (memo.yaml) |
|--------|--------------------------|------------------------|
| Import adapter | `research_v3_import.py` | `grounded_research_import.py` |
| Source claim_type | Explicit (`relationship_claim`, etc.) | Always `"assertion"` |
| Predicate mapping | `_map_claim_type_to_predicate()` → `rv3:*` | Fallback → `shared:assertion` |
| DIGIMON edge labels | Richer (`shared:relationship_claim`, etc.) | Undifferentiated (`shared:assertion`) |
| Tension detection | Lower noise (distinct predicates) | Higher noise (same predicate for all) |

---

## Query Validation Evidence (2026-04-05)

Three real OSINT queries were run against the Iran DIGIMON graph (63 entities,
62 relationships, sourced from an Iran disinformation investigation via the
research_v3 → onto-canon6 → DIGIMON pipeline). Full run record:
`docs/runs/2026-04-05_consumer_query_validation.md`.

| Query | Score (0-2) | Entities matched | Rels | Provenance |
|-------|------------|-----------------|------|------------|
| IRGC influence operations | 2 | 7 keyword + 15 PPR | 37 | 100% |
| Iran social media disinformation | 2 | 5 keyword + 15 PPR | 37 | 100% |
| APT42 cyber operations | 2 | 4 keyword + 15 PPR | 38 | 100% |
| **Mean** | **2.0** | — | — | — |

All three queries returned relevant entities with sourced relationship
descriptions. The lack of typed predicates did not prevent useful answers —
analysts receive entity context, substantive relationship text, and primary
sources in each result.

**Query validation verdict: thin semantics are sufficient for the current phase.**

The "consumer is blocked" threshold was not met. Option A remains the correct
enrichment path but the trigger condition has not been reached.

---

## Summary

| Dimension | Current State |
|-----------|--------------|
| Memo transport to DIGIMON | ✅ Working (23 claims → 23 relationships proven) |
| Entity typing downstream | ✅ Correct entity types preserved |
| Relationship predicate typing | ⚠️ All memo edges are `shared:assertion` |
| Foundation IR export | ✅ Full predicate + role structure preserved |
| Graph-backed path (graph.yaml) | ✅ Richer claim_type labels |
| Relationship-specific queries | ❌ Not possible on memo-derived subgraph |
| Tension detection quality | ⚠️ Spurious tensions possible across claim types |
| Pack-level predicate validators | ❌ Blocked for memo claims |
| Consumer query value (Iran graph) | ✅ Mean score 2.0/2.0 on 3 real OSINT queries |
| Recommended action | Defer enrichment; implement Option A when first query-type consumer appears |

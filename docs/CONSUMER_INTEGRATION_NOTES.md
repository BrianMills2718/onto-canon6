# Consumer Integration Notes (2026-03-26)

Notes for agents working on onto-canon6 consumer integration.

## research_v3 — Primary Consumer

research_v3 produces two output formats:

### Path A: graph.yaml (KnowledgeGraph with Claims) — ADAPTER BUILT

The `graph.yaml` output contains a `KnowledgeGraph` with:
- `entities`: dict of FtM entity dicts (schema, properties)
- `claims`: list of `Claim` objects (statement, entity_refs, claim_type,
  source, corroboration_status, confidence)

**Adapter**: `src/onto_canon6/adapters/research_v3_import.py`
**CLI**: `onto-canon6 import-research-v3 --input graph.yaml`
**Tested**: 48 claims from Booz Allen lobbying investigation imported.

Entity type mapping: FtM schema → oc: type (15 schemas mapped).
Confidence: corroboration_status × confidence_label → float score.
Provenance: source URL, retrieval timestamp, source_type preserved.

### Path B: InvestigationMemo with Findings — ADAPTER NOT BUILT

The `InvestigationMemo` (from `loop_models.py`) contains `Finding` objects:
- `claim`: str — factual statement
- `source_urls`: list[str]
- `confidence`: float (0-1)
- `corroborated`: bool
- `tags`: list[str]

This is the structured output from the investigation loop. No adapter exists
yet. Simpler than Path A (no FtM entities, no entity_refs).

**Integration path when needed**: Feed Finding.claim as evidence text through
the extraction pipeline. Map confidence directly. Map corroborated → epistemic
confidence boost.

## DIGIMON — Secondary Consumer

**Export adapter**: `src/onto_canon6/adapters/digimon_export.py`
**CLI**: `onto-canon6 export-digimon --output-dir path/`
**Tested**: 20 entities + 16 relationships → 19 merged nodes in Digimon GraphML.
**DIGIMON importer**: `Digimon_for_KG_application/Core/Interop/onto_canon_import.py`

Weight mapping: onto-canon6 confidence (0-1) → Digimon edge weight directly.
Default confidence=1.0 → weight=1.0.

Import direction (DIGIMON → onto-canon6) not built. Deferred until a use case
requires importing DIGIMON analysis results back into the assertion store.

## Open Questions

1. **Bulk ingestion**: Can the governed review workflow handle 61+ findings
   from one investigation? May need a trusted-source fast path (bulk accept
   + promote) for high-confidence corroborated claims.

2. **Consumer-side adoption**: Adapters exist but neither consumer has wired
   them into their actual workflow. Next step is proving consumer-side usage.

3. **Entity resolution across investigations**: auto_resolution.py does
   exact-name matching. Cross-investigation resolution (where entity names
   vary) needs fuzzy matching or Q-code resolution.

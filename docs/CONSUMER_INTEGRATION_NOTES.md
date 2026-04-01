# Consumer Integration Notes (2026-03-31)

Notes for agents working on onto-canon6 consumer integration.

## DIGIMON — First Supported Consumer

**Export adapter**: `src/onto_canon6/adapters/digimon_export.py`
**CLI**: `onto-canon6 export-digimon --output-dir path/`
**DIGIMON importer**: `Digimon_for_KG_application/Core/Interop/onto_canon_import.py`
**Supported workflow**:

1. export from the `onto-canon6` repo root via the installed `onto-canon6`
   console script
2. import from the DIGIMON repo root via
   `scripts/import_onto_canon_jsonl.py`
3. consume the resulting GraphML artifact through DIGIMON's existing graph
   retrieval/runtime surfaces

**Tested**: real Shield AI promoted graph re-verified on 2026-03-31.

Current proof:

1. `110` entities and `99` relationships exported
2. imported into DIGIMON as `110` nodes and `78` edges
3. `16` single-endpoint relationships skipped by the importer
4. remaining relationship delta explained by DIGIMON duplicate-endpoint merge
   semantics

Weight mapping: onto-canon6 confidence (0-1) → DIGIMON edge weight directly.
Default confidence=1.0 → weight=1.0.

Import direction (DIGIMON → onto-canon6) not built. Deferred until a use case
requires importing DIGIMON analysis results back into the assertion store.

The supported seam is intentionally thin. It does **not** yet carry:

1. alias memberships
2. passage artifacts
3. assertion role structure
4. richer provenance envelope

Richer interchange remains experimental under DIGIMON Plan 23.

## research_v3 — Secondary Consumer

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

## Open Questions

1. **Bulk ingestion**: Can the governed review workflow handle 61+ findings
   from one investigation? May need a trusted-source fast path (bulk accept
   + promote) for high-confidence corroborated claims.

2. **Consumer-side depth**: DIGIMON now has a supported thin v1 workflow, but
   richer passage/alias/provenance interchange is still unbuilt. research_v3
   still has adapter proof more than downstream consumer adoption.

3. **Entity resolution across investigations**: auto_resolution.py does
   exact-name matching. Cross-investigation resolution (where entity names
   vary) needs fuzzy matching or Q-code resolution.

# Consumer Integration Notes (updated 2026-03-31)

Notes for agents working on onto-canon6 consumer integration.

## DIGIMON — First Adopted Consumer (Plan 0024 Lane 2)

**Decision (2026-03-31)**: DIGIMON is the first chosen Lane 2 consumer.

**Verified v1 workflow (2026-03-31)**:

1. From onto-canon6 repo root:
   ```
   .venv/bin/onto-canon6 export-digimon \
     --review-db-path var/progressive_review_v2.sqlite3 \
     --output-dir <export_dir>
   ```
2. From DIGIMON repo root:
   ```
   .venv/bin/python scripts/import_onto_canon_jsonl.py \
     --entities <export_dir>/entities.jsonl \
     --relationships <export_dir>/relationships.jsonl \
     --working-dir <artifact_root> \
     --dataset-name <dataset_name> --force
   ```
3. Query via DIGIMON's entity/relationship retrieval surfaces.

**Verification results (2026-03-31 against Shield AI review DB)**:
- Export: 110 entities, 99 relationships
- Import: 110 nodes, 78 edges (16 single-endpoint relationships skipped,
  remainder from DIGIMON's duplicate-endpoint merge semantics)

**Export adapter**: `src/onto_canon6/adapters/digimon_export.py`
**CLI**: `onto-canon6 export-digimon --output-dir path/`
**DIGIMON importer**: `scripts/import_onto_canon_jsonl.py` (in DIGIMON repo)

Weight mapping: onto-canon6 confidence (0-1) → Digimon edge weight directly.
Default confidence=1.0 → weight=1.0.

**Known gaps in v1 seam**:
- Flat and lossy: alias memberships, role structure, passages, evidence refs,
  and richer provenance are not exported
- DIGIMON importer requires invocation from DIGIMON repo root (Config2.yaml
  loaded via relative path)
- Import direction (DIGIMON → onto-canon6) not built

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

**Integration path when needed**: Feed Finding.claim as evidence text through
the extraction pipeline. Map confidence directly. Map corroborated → epistemic
confidence boost.

## Open Questions

1. **Bulk ingestion**: Can the governed review workflow handle 61+ findings
   from one investigation? May need a trusted-source fast path (bulk accept
   + promote) for high-confidence corroborated claims.

2. **Entity resolution across investigations**: LLM-based cross-document
   entity clustering implemented (Plan 0025). Configurable: `require_llm_review`
   validates all merges with LLM context. Scale test in progress.

3. **Richer DIGIMON interchange**: Current v1 seam is flat entity/relationship
   JSONL. Future: alias memberships, passage artifacts, evidence refs,
   assertion-passage links via Foundation IR format.

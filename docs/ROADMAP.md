# onto-canon6 Roadmap

Updated: 2026-04-05

## Where We Are

onto-canon6 is a **proven governed-assertion middleware** with:

- 592 tests (562 original + 30 cross-project contract boundary tests), 0 failures
- 100% precision / 100% recall entity resolution (25-doc synthetic corpus)
- +70% cross-document QA improvement over bare extraction
- Schema stability gate (9 tests across 4 consumer surfaces)
- Cross-project contract boundary tests (B1–B7, research_v3 → onto-canon6 → DIGIMON)
- Graph-backed full pipeline proofs on real artifacts:
  - Booz Allen: 123 claims -> 60 entities + 123 relationships
  - Anduril: 22 claims -> 17 entities + 22 relationships
- Memo-backed shared-claim proof on real artifacts:
  - Palantir memo: 61 claims -> 40 entities + 61 relationships
  - Iran disinformation: 62 findings -> 63 entities + 62 relationships
- Fresh live memo-backed final proof under the promoted contract profile:
  - Palantir final run: 23 claims -> 28 entities + 23 relationships
- Consumer query validation (2026-04-05): 3 real OSINT queries, mean 2.0/2.0, 100% provenance
- Query/browse surface: entity, assertion, identity, source-artifact browse
- Compact operational-parity extraction prompt promoted as default
- Cross-project integration via shared contracts (graph + memo + grounded-research paths proven)

Historical plans `0024`-`0071` are closed or active. The Tier 1 pipeline and
consumer value goals are met. Remaining work is Tier 2 scale and Tier 3 capability
expansion, both deferred to concrete triggers.

## What "Done" Looks Like

onto-canon6 is done when:

1. ✅ A real OSINT investigation uses it as its governed assertion store
   (Iran disinformation: 63 entities, 62 rels. Consumer query validation: mean 2.0/2.0)
2. ✅ Cross-project data flows end-to-end without manual intervention
   (research_v3 → onto-canon6 → DIGIMON, one-command pipeline proven)
3. ✅ The parity matrix has no ambiguous rows (Plans 0024-0071 closed)
4. ✅ No consumer depends on unstable contracts (schema stability gate, B1–B7 tests)

**All four "done" criteria are met as of 2026-04-05.** onto-canon6 is in
operational maintenance mode. New work activates only at concrete consumer triggers
(typed edges needed, corpus exceeds 500 docs, new consumer appears).

## Priorities (Next 3-6 Months)

### Tier 1: Make It Real (current)

| Item | Status | What's Left |
|------|--------|-------------|
| Full pipeline E2E | **DONE** | Graph-backed proof (Booz Allen, Anduril). Memo-backed proof on Palantir (40 entities, 61 rels) and fresh live contract-profile run (28 entities, 23 rels). Iran disinformation investigation: 63 entities + 62 rels. Consumer query validation (2026-04-05): 3 real OSINT queries, mean score 2.0/2.0, 100% provenance. Thin `shared:assertion` semantics confirmed sufficient — see `docs/assertion_semantics_evaluation.md`. |
| grounded-research → onto-canon6 E2E | **DONE** | 8 EU sanctions claims stored |
| research_v3 → shared contracts | **DONE** | `load_graph_claims()` and `load_memo_claims()` both export `ClaimRecord`s, and the memo path now carries `entity_refs` that produce graph objects downstream. Remaining gap is richer relation semantics, not transport. |
| Evidence quality utils | **DONE** | estimate_recency + detect_staleness extracted |
| LLM resolution on real corpus | **DONE** | 1 merge found (Booz Allen name variant). Confidence weight fix landed. |
| Source-artifact query | **DONE** | list-sources, search-sources, get-source (CLI + MCP) |
| One-command consumer flow | **DONE** | `make pipeline INPUT=graph.yaml`, `make pipeline-gr INPUT=handoff.json`, and `make pipeline-rv3-memo INPUT=memo.yaml` all exist. Memo-driven DIGIMON value is now proven on repaired, checkpoint, and final fresh-live artifacts. The promoted contract profile stops naturally on graph readiness and writes final memo/report artifacts. |
| grounded-research pipeline | **DONE** | make pipeline-gr INPUT=handoff.json |
| Anduril investigation (new domain) | **DONE** | 22 claims, 17 entities (Lattice, Altius, Barracuda, Ghost, Roadrunner, Brian Schimpf, Trae Stephens + contracts), 22 rels. Defense tech domain proven. |

### Tier 2: Scale & Quality

| Item | Plan | Status |
|------|------|--------|
| Diverse domain extraction | 0014 | **DONE** — extraction quality baseline proven (2 real-chunk verifications, mean_score=0.63916) |
| Entity resolution 500+ docs | 0025a | Deferred — tiered pipeline design exists |
| Cross-investigation conflict | ADR 0024 | **DONE** — flag-only policy adopted, 871 tensions verified |
| DIGIMON weight validation | 0020 Gap 5 | **DONE** — 6 distinct weights (0.1-1.0) verified |

### Tier 3: Capability Expansion (deferred-but-protected)

| Item | Trigger |
|------|---------|
| ProbLog → llm_client | When a second consumer needs inference |
| Bulk ingestion fast path | When >10K assertions per import |
| Temporal inference | When a consumer needs temporal reasoning |
| DIGIMON import (bidirectional) | When a consumer requests it |
| Multi-consumer query federation | When a second consumer appears |
| Entity resolution 500+ docs | When corpus exceeds current scale |
| Degree distribution as graph health metric | When corpus reaches 200+ nodes — measure power-law fit; flat/random distribution signals extraction is producing isolated clusters rather than a hub-and-spoke graph |
| Scale-free construction heuristic | When degree distribution metric shows non-power-law shape — extraction policy change: prefer attaching new claims to existing high-degree entities (preferential attachment) over creating new isolated nodes |

### Abandoned

| Item | Rationale |
|------|-----------|
| Lead/investigation management | Not onto-canon6's concern — belongs in research_v3 |

## Active Dependencies

| From | To | Contract | Status |
|------|-----|----------|--------|
| grounded-research | epistemic-contracts | `load_handoff_claims()` → `ClaimRecord` | Proven |
| research_v3 | epistemic-contracts | `load_graph_claims()` / `load_memo_claims()` → `ClaimRecord` | Proven; memo path now graph-producing |
| epistemic-contracts | onto-canon6 | `import_shared_claims()` → `CandidateAssertionImport` | Proven |
| onto-canon6 | DIGIMON | `export-digimon` → `entities.jsonl` / `relationships.jsonl` | Proven |
| onto-canon6 | Foundation IR | `foundation_assertion_export.py` | Proven |

## Key Decisions In Effect

1. **Model**: `gemini/gemini-2.5-flash` (runtime default; gemini-3-flash-preview was target but ~30-60s/call in production)
2. **Config**: `review_mode: llm`, `enable_judge_filter: true` (`require_llm_review` is not a real config field)
3. **Resolution**: `default_strategy: exact`; LLM merge review stays non-default until the recall gate passes
4. **Shared contracts**: epistemic-contracts library (not llm_client)
5. **ProbLog**: stays in onto-canon6 until second consumer
6. **DIGIMON**: first consumer, thin v1 seam (flat JSONL export/import)
7. **Extraction**: compact operational-parity prompt is repo default (Plan 0062)

## Authority Chain

| Document | Governs |
|----------|---------|
| This file | Forward-looking priorities and "what done looks like" |
| `CLAUDE.md` | Strategic direction + active execution block |
| `docs/STATUS.md` | What is and isn't proven |
| `docs/plans/0005_v1_capability_parity_matrix.md` | Full capability vision |
| `HANDOFF.md` | Session-level handoff and immediate priorities |

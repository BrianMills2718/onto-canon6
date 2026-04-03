# onto-canon6 Roadmap

Updated: 2026-04-02

## Where We Are

onto-canon6 is a **proven governed-assertion middleware** with:

- 562 collected tests and the full suite passing locally
- 100% precision / 100% recall entity resolution (25-doc synthetic corpus)
- +70% cross-document QA improvement over bare extraction
- Schema stability gate (9 tests across 4 consumer surfaces)
- Graph-backed full pipeline proofs on real artifacts:
  - Booz Allen: 123 claims -> 60 entities + 123 relationships
  - Anduril: 22 claims -> 17 entities + 22 relationships
- Memo-backed shared-claim proof on a real artifact:
  - Palantir memo: 61 claims -> 61 promoted assertions -> 0 entities + 0 relationships
- Query/browse surface: entity, assertion, identity, source-artifact browse
- Compact operational-parity extraction prompt promoted as default
- Cross-project integration via shared contracts (graph + handoff proven; memo export now wired)

Historical plans `0024`-`0066` are closed. Plan `0067` is the active
end-goal convergence block for memo-path truth, reproducibility, and consumer
value closure.

## What "Done" Looks Like

onto-canon6 is done when:

1. A real OSINT investigation uses it as its governed assertion store
   (not just smoke tests — real investigation, real value)
2. Cross-project data flows end-to-end without manual intervention
   (research_v3 → grounded-research → onto-canon6 → DIGIMON → answers)
3. The parity matrix has no ambiguous rows
4. No consumer depends on unstable contracts

## Priorities (Next 3-6 Months)

### Tier 1: Make It Real (current)

| Item | Status | What's Left |
|------|--------|-------------|
| Full pipeline E2E | **PARTIAL** | Graph-backed proof is done (Booz Allen, Anduril). Memo-backed path now runs through `make pipeline-rv3-memo`, but the Palantir memo still yields `0` entities / `0` relationships because claims arrive as free text without reusable role/entity structure. |
| grounded-research → onto-canon6 E2E | **DONE** | 8 EU sanctions claims stored |
| research_v3 → shared contracts | **DONE** | `load_graph_claims()` and `load_memo_claims()` both export `ClaimRecord`s. Remaining gap is semantic richness, not transport. |
| Evidence quality utils | **DONE** | estimate_recency + detect_staleness extracted |
| LLM resolution on real corpus | **DONE** | 1 merge found (Booz Allen name variant). Confidence weight fix landed. |
| Source-artifact query | **DONE** | list-sources, search-sources, get-source (CLI + MCP) |
| One-command consumer flow | **PARTIAL** | `make pipeline INPUT=graph.yaml`, `make pipeline-gr INPUT=handoff.json`, and `make pipeline-rv3-memo INPUT=memo.yaml` all exist. Memo-driven DIGIMON value is still unresolved. |
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

### Abandoned

| Item | Rationale |
|------|-----------|
| Lead/investigation management | Not onto-canon6's concern — belongs in research_v3 |

## Active Dependencies

| From | To | Contract | Status |
|------|-----|----------|--------|
| grounded-research | epistemic-contracts | `load_handoff_claims()` → `ClaimRecord` | Proven |
| research_v3 | epistemic-contracts | `load_graph_claims()` / `load_memo_claims()` → `ClaimRecord` | Graph proven; memo proven mechanically |
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

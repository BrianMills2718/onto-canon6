# onto-canon6 Roadmap

Updated: 2026-04-02

## Where We Are

onto-canon6 is a **proven governed-assertion middleware** with:

- 451 tests passing
- 100% precision / 100% recall entity resolution (25-doc synthetic corpus)
- +70% cross-document QA improvement over bare extraction
- Schema stability gate (9 compatibility tests across 4 consumer surfaces)
- DIGIMON adopted as first consumer (110 entities, 99 relationships verified)
- Transfer evaluation passed, extraction prompt promoted with evidence
- Cross-project integration via epistemic-contracts (3 projects wired)

All internal plans (0024-0027) are complete. The post-cutover program is done.

## What "Done" Looks Like

onto-canon6 is done when:

1. A real OSINT investigation uses onto-canon6 as its governed assertion store
   (not just a smoke test — a real investigation with real value)
2. Cross-project data flows end-to-end without manual intervention
   (research_v3 → grounded-research → onto-canon6 → DIGIMON → answers)
3. The parity matrix has no ambiguous rows
4. No consumer depends on unstable contracts

## Priorities (Next 3-6 Months)

### Tier 1: Integration Hardening (current)

These are the highest-value items. They turn "proven adapters" into "real
data flowing end-to-end."

| Item | Status | What's Left |
|------|--------|-------------|
| grounded-research → onto-canon6 E2E | **DONE** (2026-04-02) | 8 claims from EU sanctions handoff successfully stored |
| research_v3 → shared contracts | **DONE** (2026-04-02) | 123 claims from Booz Allen investigation exported |
| Evidence quality utils in shared lib | **DONE** (2026-04-02) | estimate_recency + detect_staleness extracted |
| DIGIMON v1 consumer workflow | Proven | Need one-command invocation from DIGIMON side |
| Full pipeline test (research → adjudicate → govern → query) | Not started | Run the complete chain on one investigation |

### Tier 2: Scale & Quality

These matter once the integration plumbing is solid.

| Item | Plan | Status |
|------|------|--------|
| Extraction quality on real diverse corpora | 0014 | Ongoing — gemini-3-flash-preview is strong but only tested on military/PSYOP |
| Entity resolution at 500+ docs | 0025a | Deferred — tiered pipeline design exists, no consumer needs it yet |
| Non-unity confidence weight validation | 0020 Gap 5 | Open — DIGIMON weight semantics untested on varied confidence |
| Cross-investigation conflict detection | STATUS.md #3 | Not started — tension detection exists but no cross-investigation policy |

### Tier 3: Capability Expansion

These are deferred-but-protected capabilities from the parity matrix.

| Item | Parity Status | Trigger |
|------|---------------|---------|
| Concept/entity browsing MCP | Next-active (CLI done) | When agents need more than CLI |
| ProbLog → llm_client | Deferred | When a second consumer needs inference |
| Bulk ingestion fast path | Protected-deferred | When >10K assertions per import |
| Temporal inference | Protected-deferred | When a consumer needs temporal reasoning |
| DIGIMON import (bidirectional) | Consumer-blocked | When a consumer requests it |
| Frame ontology browsing | Protected-deferred | Low priority |
| Multi-consumer query federation | Vision | When a second consumer appears |
| Entity resolution 500+ docs | Protected-deferred (0025a) | When corpus exceeds current scale |

### Abandoned

| Item | Rationale |
|------|-----------|
| Lead/investigation management | Not onto-canon6's concern — belongs in research_v3 |

## Active Dependencies

| From | To | Contract | Status |
|------|-----|----------|--------|
| grounded-research | epistemic-contracts | `load_handoff_claims()` → `ClaimRecord` | Proven |
| research_v3 | epistemic-contracts | `load_graph_claims()` → `ClaimRecord` | Proven |
| epistemic-contracts | onto-canon6 | `import_shared_claims()` → `CandidateAssertionImport` | Proven |
| onto-canon6 | DIGIMON | `export-digimon` → `entities.jsonl` / `relationships.jsonl` | Proven |
| onto-canon6 | Foundation IR | `foundation_assertion_export.py` | Proven |

## Key Decisions In Effect

1. **Model**: `gemini/gemini-3-flash-preview` (extraction + resolution)
2. **Config**: `review_mode: llm`, `enable_judge_filter: true`, `require_llm_review: true`
3. **Resolution**: `default_strategy: exact` with LLM review of all merges
4. **Shared contracts**: epistemic-contracts library (not llm_client)
5. **ProbLog**: stays in onto-canon6 until second consumer
6. **DIGIMON is first consumer**: thin v1 seam (flat JSONL export/import)

## Authority Chain

| Document | Governs |
|----------|---------|
| This file | Forward-looking priorities and "what done looks like" |
| `CLAUDE.md` | Strategic direction + active execution block |
| `docs/STATUS.md` | What is and isn't proven |
| `docs/plans/0005_v1_capability_parity_matrix.md` | Full capability vision |
| `HANDOFF.md` | Session-level handoff and immediate priorities |
| `docs/plans/0024_post_cutover_program.md` | Historical post-cutover execution record |

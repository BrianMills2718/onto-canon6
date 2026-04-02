# Handoff: onto-canon6 — 2026-04-02

## Current State

- **558 tests, 0 failures**
- Tier 1: **all DONE**
- Tier 2: materially advanced (conflict policy ADR, role-free promotion, weight fix)
- Active plans: 0014 (extraction quality), 0020 (vision gaps), 0028 (queryability)
- No active 24h execution block
- DIGIMON consumer verified: 60 nodes + 26 edges from Booz Allen pipeline
- Adapter tests in grounded-research (8) and research_v3 (11) repos

## Recent Work (2026-04-02)

- CLAUDE.md rewritten (502 → ~155 lines)
- Source-artifact browse/query (list/search/get, CLI + MCP)
- One-command pipeline: `make pipeline INPUT=graph.yaml`
- DIGIMON weight fix: confidence flows through (6 distinct weights)
- Role-free assertion promotion
- Cross-investigation conflict policy (ADR 0024)
- 7 integration tests for cross-project pipeline
- 58 intermediate run records archived
- STATUS.md "What Is Not Proven" updated
- DIGIMON consumer import verified on real data
- Adapter tests added to grounded-research (8) and research_v3 (11)

## What's Next

1. **Run a new investigation end-to-end** — fresh grounded-research run through
   the complete pipeline (not reusing existing outputs)
2. **Broader domain corpora** — run pipeline on non-lobbying/non-sanctions data
3. **Entity resolution scale-out** (Plan 0025a) — when corpus exceeds 500 docs
4. **ProbLog to llm_client** — when second consumer needs inference

## What's NOT Next (deferred with rationale)

- Bulk ingestion fast path — no consumer needs >10K assertions yet
- Temporal inference — no consumer needs temporal reasoning yet
- DIGIMON bidirectional import — no use case yet
- Multi-consumer federation — only one consumer exists
- Concept/belief CRUD — governed review workflow sufficient at current scale

## Known Issues

1. **Codex worktree merges overwrite main** — need coordination protocol
2. **58 skipped DIGIMON relationships** — missing endpoints (entities referenced
   as fillers but not extracted as standalone entities)
3. **gemini-3-flash-preview slow** — ~30-60s per structured output call

## Authority Chain

| Document | Governs |
|----------|---------|
| `CLAUDE.md` | Strategic direction + active execution |
| `docs/ROADMAP.md` | Forward-looking priorities |
| `docs/STATUS.md` | What is and isn't proven |
| `docs/plans/CLAUDE.md` | Plan index |

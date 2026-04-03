# Handoff: onto-canon6 — 2026-04-02 (session 2)

## Current State

- **558 tests, 0 failures**
- Tier 1: **all DONE**
- Tier 2: **all DONE** (conflict policy ADR, role-free promotion, weight fix, extraction quality baseline, diverse domain)
- Active plans: none (0025a deferred — activates at 500+ docs)
- No active 24h execution block
- DIGIMON consumer verified: 60 nodes + 26 edges from Booz Allen pipeline
- Adapter tests in grounded-research (10) and research_v3 (11) repos

## Recent Work (2026-04-02, session 2)

- Plan 0014 closed: extraction quality baseline proven (chunk_001 + chunk_002, mean_score=0.64)
- Plan 0028 closed: query/browse surface complete (8 CLI + MCP commands)
- Plan 0020 deferred: Gaps 1-9 complete; Gap 10 blocked on OpenClaw runtime
- grounded-research pipeline added: `make pipeline-gr INPUT=handoff.json`
- `load_handoff_claims()` extended: handles both Tyler V1 and stage-based formats
- Stage-based confidence: `min(evidence_label_weight, status_weight)` — contested capped
- Palantir investigation pipeline validated: 22 claims, stage-based format, cross-domain
- 2 new grounded-research tests for stage-based format (10 total, all pass)
- KNOWLEDGE.md: PSYOP analytical prose behavior documented
- ROADMAP.md Tier 2 updated: all items DONE

## What's Next

1. **Entity extraction from claim statements** — grounded-research claims produce 0
   DIGIMON entities because `shared:fact_claim` is role-free; adding NER over
   claim text would enable entity-role pairs from that pipeline
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
   (see COORDINATION.md when written in Plan 0029)
2. **gemini-3-flash-preview slow** — ~30-60s per structured output call;
   runtime default changed to gemini-2.5-flash (see ROADMAP.md)

## Resolved (previously "known issues")

- **58 "skipped" DIGIMON relationships** — not a bug. `digimon_export.py:348`
  intentionally skips assertions with zero entity fillers. Value-only assertions
  (revenue figures, dates, attribute values) produce no relationship because they
  have no ARG0/ARG1 entity pair. The "58 skipped" count from Booz Allen reflects
  this correct filter. No fix needed.

## Authority Chain

| Document | Governs |
|----------|---------|
| `CLAUDE.md` | Strategic direction + active execution |
| `docs/ROADMAP.md` | Forward-looking priorities |
| `docs/STATUS.md` | What is and isn't proven |
| `docs/plans/CLAUDE.md` | Plan index |

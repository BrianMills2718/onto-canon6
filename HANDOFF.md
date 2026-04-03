# Handoff: onto-canon6 — 2026-04-02 (session 3)

## Current State

- **562 tests, 0 failures**
- Tier 1: **all DONE**
- Tier 2: **all DONE** (conflict policy ADR, role-free promotion, weight fix, extraction quality baseline, diverse domain)
- Active plans: Plan 0066 BLOCKED on Gemini rate limit (pipeline proven, Anduril investigation pending)
- Deferred: 0025a (500+ docs), 0065 (entity extraction — activates when grounded-research adds Stage 5b)
- DIGIMON consumer verified: 60 entities + 123 relationships (Booz Allen pipeline, STRATEGY=exact)
- Adapter tests in grounded-research (10) and research_v3 (11) repos

## Recent Work (2026-04-02, session 3 — Plan 0032 overnight sprint)

- Plan 0032 Phases 1-6 executed:
  - Phase 1: Renamed collision plans 0030/0031 → 0065/0066
  - Phase 2: Test counts corrected 558→562, config.yaml strategy=exact (LLM failed recall gate)
  - Phase 3: Plan 0065 clarified — entity_refs field already exists, adapter already handles it; 1-repo scope (not 3)
  - Phase 4: CLAUDE.md execution policy decision tree with 6 concrete cases
  - Phase 5: Pipeline re-verified with Booz Allen fallback (123→60→123); Anduril blocked by Gemini 429
  - Phase 6: Docs updated, 562 tests confirmed, push pending
- KNOWLEDGE.md: 4 new entries (rate limit, pytest invocation, strategy config, plan numbering)
- COORDINATION.md: multi-agent merge protocol created

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

1. **Anduril investigation** (Plan 0066) — retry when Gemini quota resets. Run:
   ```bash
   cd ~/projects/research_v3
   python run.py "What are Anduril Industries' major U.S. government contracts, key personnel, and primary products as of 2024-2025?" --config config_test.yaml --output ~/projects/research_v3/output/anduril_20260402
   ```
   Then: `make pipeline INPUT=<graph.yaml> STRATEGY=exact`
2. **Entity extraction from claim statements** (Plan 0065) — grounded-research
   needs Stage 5b to populate `entity_refs` in ClaimRecord; onto-canon6 adapter
   already handles entity_refs → role fillers (no onto-canon6 changes needed)
3. **Broader domain corpora** — run pipeline on non-lobbying/non-sanctions data
4. **Entity resolution scale-out** (Plan 0025a) — when corpus exceeds 500 docs
5. **ProbLog to llm_client** — when second consumer needs inference

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

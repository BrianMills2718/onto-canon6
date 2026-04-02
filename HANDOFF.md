# Handoff: onto-canon6 — 2026-04-02

## Session Summary

### Evening session (Claude Code)
- CLAUDE.md rewritten: 502 → 161 lines (radical compression)
- plans/CLAUDE.md: 40+ active → 4 active entries
- ROADMAP.md restored (deleted by Codex merge)
- 5 Codex-merge test regressions fixed: 551 passed, 0 failed
- Source-artifact browse/query: list-sources, search-sources, get-source (CLI + MCP)
- One-command pipeline: `make pipeline INPUT=graph.yaml`
- DIGIMON weight fix: confidence now flows through (6 distinct weights verified)
- Cross-investigation tension detection: 871 tensions, 6 corroboration groups
  on combined Booz Allen + EU sanctions corpus
- LLM resolution on real corpus: 1 alias merge found

### Earlier sessions
- Full pipeline E2E: research_v3 → onto-canon6 → DIGIMON (123 claims)
- E2E integration: grounded-research → epistemic-contracts → onto-canon6 (8 claims)
- Plan 56 Phase 5: research_v3 shared_export.py
- Shared import profile (shared_import_permissive)
- Evidence quality scoring extracted to epistemic-contracts
- Codex: Plans 0030-0064 (entity resolution, extraction transfer, query browse)

## Current State

- **551 tests, 0 failures**
- Tier 1 priorities: **all DONE** (full pipeline, source query, one-command, weight validation)
- Active plans: 0014 (extraction quality), 0020 (vision gaps), 0028 (queryability)
- No active 24h execution block

## What's Next

1. **Cross-investigation conflict policy** — tensions detected (871) but no
   policy for resolving conflicts across investigations
2. **Entity resolution scale-out** (Plan 0025a) — when corpus exceeds 500 docs
3. **Broader domain corpora** — run pipeline on diverse real investigations
4. **ProbLog to llm_client** — when second consumer needs inference

## Known Issues

1. **Codex worktree merges overwrite main** — need coordination protocol
2. **grounded-research claims without entity_refs don't promote** — they have
   no roles, so promotion fails. Need role-free assertion support or enrich
   imported claims with entity extraction.

## Authority Chain

| Document | Governs |
|----------|---------|
| `CLAUDE.md` | Strategic direction + active execution |
| `docs/ROADMAP.md` | Forward-looking priorities |
| `docs/STATUS.md` | What is and isn't proven |
| `docs/plans/CLAUDE.md` | Plan index |

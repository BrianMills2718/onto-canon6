# Handoff: onto-canon6 — 2026-04-02

## Session Summary (2026-04-02, two sessions)

### Session 1 (Claude Code, early morning)
- E2E integration: grounded-research → epistemic-contracts → onto-canon6 (8 EU sanctions claims, PASS)
- Plan 56 Phase 5: research_v3 shared_export.py (123 Booz Allen claims with FtM IDs)
- Full pipeline E2E: research_v3 → onto-canon6 → DIGIMON (123 claims → 60 entities + 123 relationships)
- Shared import profile: `shared_import_permissive` (imported claims validate as needs_review)
- Evidence quality scoring: extracted to epistemic-contracts (estimate_recency + detect_staleness)
- All 21 pre-existing test failures fixed (503 → 503 pass)
- epistemic-contracts cleanup: README, .gitignore, build artifacts removed
- Documentation: CLAUDE.md rewritten (502 → 171 lines), ROADMAP.md created

### Session 2 (Codex, worktrees)
- Plans 0063-0064: Query browse widening + identity/external-reference browse
- Entity search now supports identity, provider, reference_status filters
- CLI + MCP surfaces widened with source-centric provenance entrypoints
- 43 new tests added (503 → 546)
- Plans 0030-0062: Entity resolution hardening + extraction transfer certification
  (extensive 24h block series in isolated worktrees)

### Session 3 (Claude Code, evening — current)
- Fixed 5 test failures from Codex merge: 551 passed, 0 failed
- CLAUDE.md radically compressed (502 → 171 lines)
- plans/CLAUDE.md cleaned up (40+ active → 4 active)
- ROADMAP.md restored

## Current State

- **551 tests, 0 failures**
- All plans through 0064 complete
- Active: 0014 (extraction quality), 0020 (vision gaps), 0028 (queryability)
- No active 24h execution block

## What Needs Doing Next

### HIGH PRIORITY

1. **LLM resolution on real corpus** — the full pipeline E2E used exact-name
   only, producing 0 aliases. LLM resolution would find real merges in the
   Booz Allen data (name variants, abbreviations).

2. **Source-artifact query** — next queryability slice per Plan 0028. Agents
   should be able to browse by source document, not just by entity.

3. **Ecosystem docs update** — ECOSYSTEM_STATUS.md and CAPABILITY_BOUNDARIES.md
   in project-meta don't reflect the integration work or query widening.

### MEDIUM PRIORITY

4. **One-command consumer flow** — the DIGIMON v1 seam requires separate CLI
   invocations from each repo. A single script for the consumer path.

5. **Validation profile for shared claims** — `shared:fact_claim` predicates
   produce `needs_review` not `valid`. Consider whether imported claims from
   trusted sources should auto-validate.

### LOWER PRIORITY

6. **ProbLog to llm_client** — when second consumer needs inference
7. **Cross-investigation conflict detection** — tension exists, no policy
8. **Non-unity DIGIMON weight validation** — confidence semantics untested

## Known Issues

1. **Codex worktree merges overwrite fixes** — merge from isolated worktrees
   reverts changes made on main. Need coordination protocol.
2. **gemini-3-flash-preview slow** — ~30-60s per structured output call
3. **gemini-2.5-flash quota** — 10K requests/day limit

## Authority Chain

| Document | Governs |
|----------|---------|
| `CLAUDE.md` | Strategic direction + active execution |
| `docs/ROADMAP.md` | Forward-looking priorities |
| `docs/STATUS.md` | What is and isn't proven |
| `docs/plans/CLAUDE.md` | Plan index |

## Previous Handoffs

- 2026-04-02: Doc compression, test fixes, integration E2E, full pipeline
- 2026-04-01: Plans 0030-0064 (Codex), entity resolution + extraction transfer
- 2026-03-31: Strategic review, Plan 0025, judge filter fix
- 2026-03-28: Documentation authority cleanup, DIGIMON boundary review

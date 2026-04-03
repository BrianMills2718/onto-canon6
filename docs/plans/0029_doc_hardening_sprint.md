# Plan 0029 — Documentation Hardening Sprint

**Created**: 2026-04-02  
**Status**: complete (2026-04-02)  
**Owner**: claude-code overnight run

## Mission

Fix all inconsistencies, ambiguities, and gaps identified in the 2026-04-02 audit.
Make every doc truthful. Add missing dependencies. Add config validation.
Clarify long-term planning gaps. Leave the repo in a state where any agent
can start fresh and have a completely accurate picture.

## Acceptance Criteria

Every phase has binary pass/fail. Sprint is done when all phases pass.

1. pyproject.toml declares all runtime deps (rapidfuzz, problog)
2. Test count is correct and consistent across CLAUDE.md, ROADMAP.md, HANDOFF.md
3. Model override decision is explicit and consistent in config vs. docs
4. ProbLog described as "available, no consumer yet" not "deferred"
5. Stale "5 Codex failures" line removed from CLAUDE.md
6. Config Pydantic validation model exists, loads config, fails fast on bad input
7. Config validation has tests
8. DIGIMON 58-relationships documented as expected behavior (value-only assertions), not a bug
9. COORDINATION.md written — Codex merge protocol exists
10. STATUS.md "What Is Proven" reorganized by subsystem with ToC
11. Plan 0029_entity_extraction.md written — grounded-research entity gap designed
12. Plan 0030_next_investigation.md written — concrete next investigation defined
13. All changes committed and pushed

## Failure Modes

- Config validation breaks existing tests → revert, investigate, rewrite to not break
- rapidfuzz/problog version pinning conflicts → add as optional deps with try/except guard
- STATUS.md reorganization loses items → verify line count before/after

## Phases

### Phase 1: Deps + Doc Quick Fixes ✓ COMPLETE
- [x] pyproject.toml: add rapidfuzz>=3.0, problog>=2.1
- [x] CLAUDE.md: fix test count 546→558, remove Codex failures line, fix ProbLog framing
- [x] ROADMAP.md: fix test count 551→558, update model decision (gemini-2.5-flash)
- **Result**: 558 passed, 0 failures

### Phase 2: Config Validation Tests ✓ COMPLETE
- [x] Config Pydantic model already existed (comprehensive, extra="forbid")
- [x] Added 4 failure-mode tests: unknown key, negative budget, invalid review_mode, model assertion
- **Result**: 562 passed, 0 failures

### Phase 3: DIGIMON Relationships Clarification ✓ COMPLETE
- [x] Confirmed: digimon_export.py:348 skips zero-entity-filler assertions (correct behavior)
- [x] HANDOFF.md: removed from Known Issues, added to Resolved section
- **Result**: 562 passed, 0 failures

### Phase 4: Codex Coordination Protocol ✓ COMPLETE
- [x] COORDINATION.md: 9-rule multi-agent merge protocol
- [x] CLAUDE.md: pointer in Working Rules
- **Result**: COORDINATION.md exists

### Phase 5: STATUS.md Reorganization ✓ COMPLETE
- [x] Added quick-nav ToC with 14 subsystem groups
- [x] Added subsystem group headers throughout What Is Proven (90 items)
- [x] Fixed stale Immediate Next Step (was pointing to Plan 0014)
- [x] Fixed stale Current Risks #12 (marked Plan 0014 as RESOLVED)
- **Result**: 562 passed, 0 failures

### Phase 6: Entity Extraction Gap Plan ✓ COMPLETE
- [x] docs/plans/0030_entity_extraction_from_claims.md written
- [x] Option analysis: Option B (grounded-research native) recommended
- [x] Implementation scope defined across 3 repos

### Phase 7: Next Real Investigation Plan ✓ COMPLETE
- [x] docs/plans/0031_next_real_investigation.md written
- [x] Topic: Anduril Industries (defense tech, distinct domain)
- [x] Acceptance criteria defined (≥20 claims, ≥10 entities, ≥5 relationships, ≥1 merge)
- [x] Uses research_v3 path until Plan 0030 lands

### Phase 8: Cleanup + Push ✓ COMPLETE
- [x] docs/plans/CLAUDE.md: Plans 0029/0030/0031 added to Active Plans table
- [x] Full pytest: 562 passed, 0 failures
- [x] Pushed

## Pre-Made Decisions

- Model decision: `gemini/gemini-2.5-flash` is the actual runtime default. ROADMAP.md said `gemini-3-flash-preview` which was the intended target but is slow (30-60s/call). Update ROADMAP to say "gemini-2.5-flash (runtime default); gemini-3-flash-preview was target but too slow for production use."
- rapidfuzz version: `>=3.0` (stable API since 3.0, token_sort_ratio interface unchanged)
- problog version: `>=2.1` (current stable)
- Config validation: use Pydantic v2 `model_config = ConfigDict(extra="forbid")` so unknown keys fail loud
- Reorganize STATUS.md in place — do not split into multiple files
- Entity extraction plan: recommend Option B (grounded-research native) but don't implement yet — just plan
- Next investigation: Anduril (defense tech, good entity density, non-overlapping with existing domains)

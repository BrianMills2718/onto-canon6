# Plan 0029 — Documentation Hardening Sprint

**Created**: 2026-04-02  
**Status**: active  
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

### Phase 1: Deps + Doc Quick Fixes
- [ ] pyproject.toml: add rapidfuzz>=3.0, problog>=2.1
- [ ] CLAUDE.md: fix test count 546→558, remove Codex failures line, fix ProbLog framing
- [ ] ROADMAP.md: fix test count 551→558, update model decision (gemini-2.5-flash is actual runtime default)
- [ ] Commit: "[Plan 0029] Fix deps, test counts, model decision, ProbLog framing"
- **Pass**: `pip install -e .` succeeds, `pytest -q` shows 558 passed

### Phase 2: Config Validation Model
- [ ] Create `src/onto_canon6/config_schema.py` — Pydantic v2 model for config.yaml
  - Validate model_override is a valid string
  - Validate numeric bounds (max_budget_usd > 0, timeout_seconds > 0)
  - Validate prompt_template path is non-empty
  - Fail loud on unknown top-level keys
- [ ] Wire into `src/onto_canon6/config.py` load path
- [ ] Add `tests/test_config_schema.py` — 5 tests: valid config, bad model, bad budget, missing required key, unknown key
- [ ] Commit: "[Plan 0029] Config validation model"
- **Pass**: 558+5 = 563 tests pass, bad config raises ValidationError with clear message

### Phase 3: DIGIMON Relationships Clarification
- [ ] Read digimon_export.py lines 343-349 to confirm: skipped = zero entity fillers = value-only assertions
- [ ] Update HANDOFF.md "Known Issues": remove item 2 (58 skipped relationships) OR reframe as
  "value-only assertions (revenue, dates, attributes) produce no DIGIMON relationship — expected behavior"
- [ ] Update STATUS.md if referenced there
- [ ] Commit: "[Plan 0029] Clarify DIGIMON value-only assertion behavior"
- **Pass**: HANDOFF.md no longer lists this as an open bug

### Phase 4: Codex Coordination Protocol
- [ ] Write `COORDINATION.md` — merge protocol for multi-agent environment
  - Rule 1: check `~/.claude/coordination/claims/` before starting work
  - Rule 2: claim scope in KNOWLEDGE.md `## Active Decisions` before multi-file edits
  - Rule 3: Codex worktree must `git pull --rebase` before merging to main
  - Rule 4: agent completes its scope before another starts on overlapping files
- [ ] Add pointer in CLAUDE.md "Working Rules" section
- [ ] Commit: "[Plan 0029] Add Codex coordination protocol"
- **Pass**: COORDINATION.md exists and explains the worktree merge problem concretely

### Phase 5: STATUS.md Reorganization
- [ ] Read STATUS.md fully
- [ ] Group "What Is Proven" 68 items into subsystems:
  - Review & Promotion (items 1-N)
  - Extraction (items N-M)
  - Entity Resolution (items M-P)
  - Export / Consumer Integration (items P-Q)
  - Schema & Stability (items Q-R)
  - Query Surface (items R-S)
  - Cross-Project Pipeline (items S-T)
- [ ] Add ToC at top of "What Is Proven" section
- [ ] Commit: "[Plan 0029] Reorganize STATUS.md What Is Proven by subsystem"
- **Pass**: STATUS.md has ToC, items grouped, no items lost (verify count before/after)

### Phase 6: Entity Extraction Gap Plan
- [ ] Write `docs/plans/0030_entity_extraction_from_claims.md`
  - Problem: grounded-research claims are `shared:fact_claim` (role-free) → 0 DIGIMON entities
  - Two options: (A) NER post-processing in onto-canon6 import adapter; (B) grounded-research emits entity-role pairs natively
  - Recommended: Option B — grounded-research adds an entity extraction stage that annotates claims with subject/object entities before handoff; onto-canon6 import adapter maps these to role fillers
  - Define ClaimRecord extension or new field for entity annotations
  - Define acceptance criteria: Palantir pipeline produces >0 DIGIMON entities
- [ ] Commit: "[Plan 0030] Entity extraction from grounded-research claims — plan"
- **Pass**: Plan doc exists with clear option analysis and recommendation

### Phase 7: Next Real Investigation Plan
- [ ] Write `docs/plans/0031_next_real_investigation.md`
  - Topic: concrete OSINT question (not lobbying, not sanctions, not Palantir)
  - Suggested: "What are Anduril Industries' major U.S. government contracts and key personnel?"
    (defense tech company, different domain, good entity density for entity resolution testing)
  - Pipeline: grounded-research fresh run → onto-canon6 → DIGIMON
  - Acceptance criteria:
    - At least 20 claims promoted
    - At least 10 DIGIMON entities produced (requires entity extraction from Phase 6 plan OR using research_v3 path)
    - Entity resolution finds at least 1 merge (name variant)
    - Report generated and human-readable
  - Note: Until Plan 0030 (entity extraction) lands, use research_v3 path for entity-dense output
- [ ] Commit: "[Plan 0031] Next real investigation — Anduril Industries"
- **Pass**: Plan doc exists with concrete topic, acceptance criteria, and pipeline path

### Phase 8: Cleanup + Push
- [ ] Verify all plans listed in docs/plans/CLAUDE.md
- [ ] Update docs/plans/CLAUDE.md: add 0029, 0030, 0031 to Active Plans table
- [ ] Run full pytest: confirm 563+ passing, 0 failures
- [ ] Push onto-canon6
- **Pass**: Remote is up to date, CI green, all phases complete

## Pre-Made Decisions

- Model decision: `gemini/gemini-2.5-flash` is the actual runtime default. ROADMAP.md said `gemini-3-flash-preview` which was the intended target but is slow (30-60s/call). Update ROADMAP to say "gemini-2.5-flash (runtime default); gemini-3-flash-preview was target but too slow for production use."
- rapidfuzz version: `>=3.0` (stable API since 3.0, token_sort_ratio interface unchanged)
- problog version: `>=2.1` (current stable)
- Config validation: use Pydantic v2 `model_config = ConfigDict(extra="forbid")` so unknown keys fail loud
- Reorganize STATUS.md in place — do not split into multiple files
- Entity extraction plan: recommend Option B (grounded-research native) but don't implement yet — just plan
- Next investigation: Anduril (defense tech, good entity density, non-overlapping with existing domains)

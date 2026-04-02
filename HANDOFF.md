# Handoff: onto-canon6 + ecosystem — 2026-04-02

## Session Scope (2026-03-31 to 2026-04-02)

Three-day session covering onto-canon6 strategic review, entity resolution
implementation, schema stability gates, neurosymbolic value proof, and
shared epistemic infrastructure extraction. ~55 commits across 4 repos.

## What Was Accomplished

### onto-canon6 — All Plans Complete

| Plan | Result |
|---|---|
| 0024 Lane 1 (Docs) | Done — all docs consistent |
| 0024 Lane 2 (Consumer) | Done — DIGIMON adopted, v1 workflow verified (110 entities, 99 relationships) |
| 0024 Lane 3 (Schema) | Done — Plan 0026 complete (9 tests, change classification) |
| 0024 Lane 4 (Extraction) | Done — transfer evaluation passed, prompt promoted |
| 0024 Lane 5 (Parity) | Done — reprioritized: browsing=next-active, lead mgmt=abandoned |
| 0025 (Entity Resolution) | Done — 100%/100% precision/recall with exact+LLM review |
| 0026 (Schema Stability) | Done — 4 surfaces, 9 compatibility tests, change classification policy |

### Key Technical Achievements

1. **gemini-3-flash-preview fix**: The empty-roles regression was caused by
   `additionalProperties` + nested `$ref` in the JSON schema. Fixed by replacing
   `dict[str, list[Filler]]` with `list[RoleEntry]` (standard Gemini workaround).
   gemini-3-flash now produces 100% precision, 100% recall, 0 noise.

2. **Neurosymbolic value proof**: 9 extracted facts from 2 Booz Allen investigations
   → ProbLog inference with 4 rules → 14 derived facts. Correctly identifies
   lobbying network, strongest ties (dual relationships), corporate reach through
   subsidiaries. No single source document contains these answers.

3. **Entity resolution**: Title normalization + LLM clustering + type hierarchy
   (SUMO is-a). 50% dedup on real Booz Allen data. 100%/100% on synthetic.

4. **Cross-doc QA**: +70% improvement vs bare extraction (90% vs 20% on 10 questions).

### epistemic-contracts — NEW shared library

Created `~/projects/epistemic-contracts/` with 6 Pydantic union models:
- ConfidenceScore, SourceRecord, EvidenceItem, EvidenceSpan, EntityReference,
  ClaimRecord, DisputeRecord
- 18 tests, pip-installable
- GitHub: BrianMills2718/epistemic-contracts (private)

### Integration Adapters Built

| From | To | Adapter | Status |
|---|---|---|---|
| grounded-research | shared contracts | `shared_export.py` | Built, smoke-tested |
| shared contracts | onto-canon6 | `grounded_research_import.py` | Built, smoke-tested |
| onto-canon6 | shared contracts | `shared_contracts.py` | Built, smoke-tested |
| research_v3 | shared contracts | Not yet built | Plan 56 Phase 5 |

### CAPABILITY_BOUNDARIES.md

New vision document mapping overlapping implementations across 4 projects.
Identifies 5 capabilities implemented independently, 5 shared infrastructure
candidates, and 4 missing integration contracts.

## Current State

### Config (onto-canon6)
- `review_mode: llm`
- `enable_judge_filter: true`
- `model_override: gemini/gemini-3-flash-preview` (extraction + resolution)
- `require_llm_review: true`
- `default_strategy: exact`

### Tests
- onto-canon6: 451 passing
- epistemic-contracts: 18 passing
- grounded-research: existing suite (not re-run this session)

### Repos Pushed
- `BrianMills2718/onto-canon6` (private) — all commits pushed
- `BrianMills2718/project-meta` — all commits pushed
- `BrianMills2718/epistemic-contracts` (private) — all commits pushed
- `BrianMills2718/grounded-research` (private) — shared_export.py pushed

## What Needs Doing Next

### HIGH PRIORITY — Verify before building more

1. **End-to-end integration test**: Run grounded-research on a real topic →
   export via shared_export.py → import into onto-canon6 via
   grounded_research_import.py → verify assertions in promoted graph.
   The adapters were smoke-tested with manually constructed objects but NOT
   tested against actual grounded-research Tyler pipeline output.

2. **Fresh documentation review**: 55 commits over 3 days. Stale references
   likely. A fresh session should do a systematic pass of:
   - onto-canon6 CLAUDE.md (execution block is stale)
   - ECOSYSTEM_STATUS.md (Data bucket description may be stale)
   - Plan 56 (update Phases 1-4 as complete)
   - CAPABILITY_BOUNDARIES.md (verify against actual code)

3. **epistemic-contracts cleanup**: Needs README.md. The egg-info and __pycache__
   directories were committed (before .gitignore was added). Clean up.

### MEDIUM PRIORITY — Plan 56 completion

4. **Plan 56 Phase 5**: Wire research_v3 boundary. Create adapter that exports
   research_v3 Finding/Claim to shared ClaimRecord. Preserve FtM entity IDs
   as external_ids in EntityReference.

5. **Evidence quality scoring as shared utility**: grounded-research's
   `evidence_utils.py` has recency scoring and staleness detection. Extract
   to epistemic-contracts as utility functions (not just models).

### LOWER PRIORITY — Future work

6. **Concept/entity browsing MCP surface**: CLI commands shipped (list-entities,
   search-entities, get-entity). MCP tools only if agents need more than CLI.
   The `/query-onto-canon6` skill teaches agents to use CLI.

7. **ProbLog to llm_client**: FRAMEWORK.md says inference should be domain-agnostic
   infrastructure. Currently onto-canon6-local. Move when a second consumer needs it.

8. **Scale the real investigation pipeline**: 7 claims processed in the Booz Allen
   test. Full 111 claims would take ~2 hours with gemini-3-flash-preview.

## Known Issues

1. **var/scale_test/scale_test.sqlite3 identity tables corrupted**: The
   require_llm_review test cleared the graph_identities table. Needs rebuild
   (`rm -rf var/scale_test && python scripts/run_scale_test.py --strategy exact`).

2. **gemini-2.5-flash quota**: 10K requests/day limit. Use gemini-3-flash-preview
   or gemini-2.5-flash-lite as alternatives.

3. **gemini-3-flash-preview slow**: ~30-60s per structured output call.
   Extraction of 25 documents takes ~30 minutes.

4. **epistemic-contracts egg-info committed**: .gitignore was added after first
   commit. Clean up in next session.

5. **Judge filter uses `call_llm_structured`**: Fixed API mismatch (added
   `_JudgeResult` Pydantic model), but the judge adds ~3s per candidate.
   With `enable_judge_filter: true`, bulk extraction is slower.

## Authority Chain

| Document | What it governs |
|---|---|
| onto-canon6/CLAUDE.md | Strategic direction + active execution |
| onto-canon6/docs/plans/CLAUDE.md | Plan index and status |
| project-meta/vision/FRAMEWORK.md | Architecture north star |
| project-meta/vision/CAPABILITY_BOUNDARIES.md | Cross-project ownership |
| project-meta/vision/ECOSYSTEM_STATUS.md | Current state |
| project-meta/docs/plans/56_shared_epistemic_infrastructure.md | Shared infra extraction plan |

## Previous Handoffs

- 2026-03-31: Strategic review, Plan 0025 Phase 1-3, judge filter fix
- 2026-03-28: Documentation authority cleanup, DIGIMON boundary review
- 2026-03-26: Final bootstrap session, 430 tests, review modes wired

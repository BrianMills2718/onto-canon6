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

## What Was Done (2026-04-02 session)

1. **E2E integration test PASS** — real grounded-research EU sanctions handoff
   (8 claims) → epistemic-contracts → onto-canon6 review pipeline. All stored.
   Required fixing: `load_handoff_claims()` bridge (handoff.json uses simplified
   format, not ClaimLedgerEntry), `content_text` on SourceArtifactRef for
   evidence span verification.

2. **Documentation inconsistencies fixed** — CLAUDE.md execution block updated,
   STATUS.md date fixed, README.md test count fixed, Plan 0024 marked complete,
   plans/CLAUDE.md cleaned up.

3. **epistemic-contracts cleaned up** — README.md added, committed egg-info
   removed from git, .gitignore expanded.

4. **Plan 56 Phase 5 complete** — research_v3 `shared_export.py` created with
   `load_graph_claims()`. 123 Booz Allen claims with FtM entity IDs preserved.
   15 FtM→oc: type mappings.

5. **Evidence quality scoring extracted** — `estimate_recency()` and
   `detect_staleness()` now in epistemic-contracts. 17 new tests (35 total).

6. **Long-term roadmap written** — `docs/ROADMAP.md` with priorities, "what done
   looks like", dependency map, and authority chain.

## What Needs Doing Next

### HIGH PRIORITY

1. **Full pipeline E2E test** — research_v3 investigation → grounded-research
   adjudication → onto-canon6 governance → DIGIMON query. No single test covers
   the complete chain yet.

2. **DIGIMON one-command consumer flow** — The v1 export/import seam works but
   requires separate CLI invocations from each repo. A single command or script
   that runs the full consumer path.

3. **Validation profile for shared claims** — Imported claims get
   `validation_status=invalid` because `general_purpose_open` doesn't recognize
   `shared:fact_claim` as a predicate. Need a profile or bypass for imported claims.

### MEDIUM PRIORITY

4. **Concept/entity browsing MCP surface** — CLI done, MCP if agents need it.
5. **ProbLog to llm_client** — when second consumer needs inference.
6. **Scale real investigation** — full 111 Booz Allen claims through the pipeline.

### LOWER PRIORITY

7. **Cross-investigation conflict detection** — tension detection exists but no
   cross-investigation policy.
8. **Non-unity DIGIMON weight validation** — confidence semantics untested on
   varied-confidence slice.

## Known Issues

1. **var/scale_test/scale_test.sqlite3 identity tables corrupted**: The
   require_llm_review test cleared the graph_identities table. Needs rebuild
   (`rm -rf var/scale_test && python scripts/run_scale_test.py --strategy exact`).

2. **gemini-2.5-flash quota**: 10K requests/day limit. Use gemini-3-flash-preview
   or gemini-2.5-flash-lite as alternatives.

3. **gemini-3-flash-preview slow**: ~30-60s per structured output call.
   Extraction of 25 documents takes ~30 minutes.

4. ~~**epistemic-contracts egg-info committed**~~ — RESOLVED (2026-04-02).

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

- 2026-04-02: Doc cleanup, E2E integration test, Plan 56 Phase 5, evidence utils, roadmap
- 2026-03-31: Strategic review, Plan 0025 Phase 1-3, judge filter fix
- 2026-03-28: Documentation authority cleanup, DIGIMON boundary review
- 2026-03-26: Final bootstrap session, 430 tests, review modes wired

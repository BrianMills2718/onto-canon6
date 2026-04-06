# Handoff: onto-canon6 — 2026-04-05 (session 8)

## Current State

Plan `0071` (Consumer Value Validation) is complete.

**All four ROADMAP "done" criteria are met.** onto-canon6 is operational.

## What Was Done This Session

### 1. Cross-project contract boundary tests (30 tests, B1–B7)

Added `tests/integration/test_contract_boundaries.py` and
`tests/integration/conftest_research_v3.py` covering the full chain:

- B1: research_v3 → ClaimRecord (shared_export field correctness)
- B2: ClaimRecord → CandidateAssertionImport (adapter field mapping)
- B3: candidate pipeline lifecycle (submit → review → promote)
- B4: promoted graph structure (entity + assertion correctness)
- B5: onto-canon6 → DIGIMON export (schema + field validation)
- B6: end-to-end source_urls provenance (full chain traceability)
- B7: contract failure modes (ValueError on bad input)

All 30 pass. Committed and pushed.

### 2. epistemic-contracts CLAUDE.md fix

research_v3 consumer row corrected from "not yet wired" to "Operational since
2026-04-03." Consumer table converted to structured format. Committed and pushed.

### 3. ECOSYSTEM.md created

`~/projects/ECOSYSTEM.md` — single source of truth for the full provenance
chain: research_v3 → epistemic-contracts → onto-canon6 → DIGIMON. Field mapping
tables, failure modes, CLI commands, integration status, deferred work.

### 4. Plan 0071 — Consumer Value Validation

Validated that the Iran DIGIMON graph (63 entities, 62 rels) answers real OSINT
queries with useful results:

| Query | Score | Entities | Rels | Provenance |
|-------|-------|----------|------|------------|
| IRGC influence operations | 2/2 | 7+15 | 37 | 100% |
| Iran social media disinformation | 2/2 | 5+15 | 37 | 100% |
| APT42 cyber operations | 2/2 | 4+15 | 38 | 100% |

Full run note: `docs/runs/2026-04-05_consumer_query_validation.md`

### 5. LLM entity resolution promotion decision

Gate passed (Plan 0039: precision 1.00, recall 0.9643, 0 false merges, 10/10
questions). Decision: **retain `default_strategy: exact`** for cost/latency
reasons on small corpora. LLM strategy available via config override when needed.

Decision note: `docs/runs/2026-04-05_entity_resolution_promotion_decision.md`

### 6. Documentation cleanup

- Plan 0067 marked completed (was "active" despite all phases done)
- TODO.md rewritten to reflect true current frontier
- ROADMAP.md "Where We Are" updated with 592 tests, Iran investigation, query validation
- ROADMAP.md Tier 1 "Full pipeline E2E" marked DONE with evidence
- ROADMAP.md "done" criteria all marked ✅
- `docs/assertion_semantics_evaluation.md` updated with query validation evidence

## Verification

All tests passing:
- `pytest tests/ -q` → 592 tests, 0 failures
- `pytest tests/integration/test_contract_boundaries.py -v` → 30 passed in 1.1s
- Consumer query validation: 3 queries, mean 2.0/2.0

## Known Open Items (not blockers)

1. **Option A predicate enrichment** — deferred until first consumer requests
   typed edges. Decision documented in `docs/assertion_semantics_evaluation.md`.
2. **Provenance scripts relocation** — `scripts/provenance_report.py` and
   `scripts/digimon_query.py` are consumer-side tools that belong in DIGIMON.
   Noted in ECOSYSTEM.md. Deferred until DIGIMON stabilizes.
3. **Cross-project CI** — auto-run contract tests on schema change. Medium
   priority, no concrete trigger yet.
4. **Entity resolution 500+ docs** — activates when corpus exceeds scale.
5. **Stochasticity characterization** — extraction variance across runs. Not
   measured. Low priority until a real consistency problem appears.

## Next Session

onto-canon6 is in maintenance mode. New work requires one of:
- A consumer requests typed edges → implement Option A
- A new producer or consumer appears → extend contracts
- Corpus exceeds 500 docs → activate LLM resolution as default
- A query failure surfaces → diagnostic and fix

The most valuable next investments are probably **in research_v3** (richer
investigation tooling) or **in DIGIMON** (MCP tools, provenance surface) rather
than in onto-canon6 itself.

## Authority Chain

| Document | Governs |
|----------|---------|
| `CLAUDE.md` | Strategic direction + execution policy |
| `docs/ROADMAP.md` | Forward-looking priorities (all Tier 1 done) |
| `docs/plans/0071_consumer_value_validation_block.md` | This session's plan |
| `docs/runs/2026-04-05_consumer_query_validation.md` | Query validation evidence |
| `docs/runs/2026-04-05_entity_resolution_promotion_decision.md` | LLM resolution decision |
| `docs/assertion_semantics_evaluation.md` | Thin-semantics decision + evidence |
| `~/projects/ECOSYSTEM.md` | Cross-project pipeline single source of truth |

# Handoff: onto-canon6

**Date**: 2026-03-26
**From**: Claude Code (Phase 2 — hardening, integration, quality)
**Session**: 12 Phase 2 commits on top of 12 Phase 1 commits (24 total this day)

---

## What This Session Delivered

### Phase 1: All 10 Vision Gaps Closed (Plan 0020)

| Gap | Status | Key Result |
|-----|--------|------------|
| 1. Predicate names | ALREADY CLOSED | 4,669 names exist in sumo_plus.db |
| 2. Non-military domain | COMPLETED | Financial + academic text: 82% structural validity |
| 3. Entity resolution | COMPLETED | auto_resolution.py: exact name match, USSOCOM merged |
| 4. Temporal qualifiers | COMPLETED | valid_from/valid_to in extraction + Foundation IR |
| 5. Digimon export | COMPLETED | 19 merged nodes, 16 edges in GraphML |
| 6. research_v3 adapter | COMPLETED | FtM mapping (15 schemas), 48 claims imported |
| 7. Epistemic on data | COMPLETED | 16 scored, 1 supersession, 19 tensions |
| 8. ProbLog spike | COMPLETED | 45 derived facts, decision: use ProbLog |
| 9. Second vocabulary | COMPLETED | dodaf_minimal: 7 candidates, 100% validation |
| 10. Autonomous ops | COMPLETED | .openclaw/ success-criteria + mission-spec |

### Phase 2: Hardening and Integration

| Task | Status | Key Result |
|------|--------|------------|
| Tests: auto_resolution | COMPLETED | 13 tests (merge, idempotent, case-insensitive) |
| Tests: research_v3_import | COMPLETED | 21 tests (mapping, confidence, provenance) |
| Tests: temporal qualifiers | COMPLETED | 7 tests (model, Foundation IR export) |
| CLI: import-research-v3 | COMPLETED | 48 claims from real investigation → review DB |
| CLI: evaluate-rules | COMPLETED | ProbLog over DB: 16 facts → 45 derived |
| General-purpose pack | COMPLETED | 15 entity types, 10 predicates, open profile |
| make summary + identity | COMPLETED | Identity and epistemic stats in summary |
| Non-military benchmark | COMPLETED | 6 cases across 2 domains |
| E2E integration test | COMPLETED | 3 tests: Digimon, research_v3, Foundation IR |
| Foundation export bugfix | COMPLETED | Missing db_path and row_factory fixed |

---

## New Code

| Path | What |
|------|------|
| `src/onto_canon6/core/auto_resolution.py` | Automated entity resolution |
| `src/onto_canon6/adapters/research_v3_import.py` | research_v3 graph.yaml adapter |
| `src/onto_canon6/extensions/problog_adapter.py` | ProbLog fact-store adapter |
| `ontology_packs/general_purpose/0.1.0/` | General-purpose ontology pack |
| `profiles/general_purpose_open/0.1.0/` | Open profile for general extraction |
| `.openclaw/` | OpenClaw success criteria + mission spec |
| `scripts/show_summary.py` | Enhanced summary with identity/epistemic stats |
| `scripts/e2e_integration_test.py` | E2E consumer integration tests |
| `tests/core/test_auto_resolution.py` | 13 tests |
| `tests/adapters/test_research_v3_import.py` | 21 tests |
| `tests/pipeline/test_temporal_qualifiers.py` | 7 tests |
| `tests/fixtures/nonmilitary_eval_slice.json` | 6-case benchmark fixture |

## CLI Commands Added

| Command | Purpose |
|---------|---------|
| `auto-resolve-identities` | Group entities by name match |
| `import-research-v3` | Import graph.yaml claims to review pipeline |
| `evaluate-rules` | Evaluate ProbLog rules over promoted assertions |

---

## Environment

- Model: `gemini/gemini-2.5-flash` (stable, used for all extractions)
- ProbLog: installed in shared venv
- All tests pass (~300+ tests)
- E2E integration test passes (3/3)

## Next Steps

1. **Extraction quality iteration** — still the #1 bottleneck (37.5% acceptance)
2. **Prompt experiment analysis** — experiment may still be running (backgrounded)
3. **Fuzzy entity resolution** — extend auto_resolution with Levenshtein/embedding
4. **ProbLog rule library** — define reusable rules for common inference patterns
5. **Digimon operator exercise** — install igraph/rapidfuzz in Digimon venv

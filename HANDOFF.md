# Handoff: onto-canon6

**Date**: 2026-03-26
**Scope**: documentation/status cleanup, Gap 5 DIGIMON validation, dependency install

## What Is Actually Proven

### Plan 0020 status

| Gap | Status | Notes |
|---|---|---|
| 1. Predicate names | Closed | Already existed in `sumo_plus.db` |
| 2. Non-military domain testing | Closed | Financial + academic slices exercised |
| 3. Automated entity resolution | Closed, narrow | Exact-name auto-resolution only |
| 4. Temporal qualifiers | Closed | Extraction + Foundation IR export |
| 5. DIGIMON export/import/query | Closed | Export, import, operator query, and non-unity weight semantics all proven |
| 6. research_v3 adapter | Closed, adapter-level | `graph.yaml` import proven on real data |
| 7. Epistemic engine on real data | Closed, narrow | Real-data tension/supersession proof exists |
| 8. ProbLog spike | Closed, spike-level | Build-vs-buy answered: use ProbLog |
| 9. Second vocabulary | Closed | `dodaf_minimal` exercised through E2E extraction |
| 10. OpenClaw autonomous operation | Partially closed | Repo-local spec exists; runtime proof still missing |

### Real DIGIMON proof completed this session

- Missing DIGIMON runtime deps were installed in the project venv (`igraph`, `rapidfuzz`, `loguru`, `unidecode`).
- Real promoted assertions were exported from `var/e2e_test_2026_03_25/review_combined.sqlite3`.
- Export result: `20` entity rows, `16` relationship rows.
- DIGIMON import result: `results/onto_canon_e2e_20260325/er_graph/nx_data.graphml` with `19` merged nodes and `16` edges.
- DIGIMON runtime proof: `relationship.onehop` over seed `USSOCOM` returned the expected neighborhood, including the commanders and PSYOP-connected units.

## Key Context For The Next Agent

- `model_override` in config is `gemini/gemini-2.5-flash`. This is the working model. `gemini-3-flash-preview` regressed.
- Evidence span resolution is intentionally `strict=False`; bad spans are skipped, not fatal.
- The Makefile path is real and useful: `make extract`, `make candidates`, `make accept`, `make promote`, `make summary`, `make failures`, `make diagnose`.
- `llm_client` `main` now has the observability columns `schema_hash`, `response_format_type`, and `validation_errors`.
- Pre-commit hook bugs:
  - `MP-026`: `project-meta` `validate_plan.py`
  - `MP-027`: `llm_client`, fixed earlier in this session lineage

## What Was Corrected In Docs

- `README.md` now points to Plans `0014`, `0019`, and `0020` as the active plan surface, and treats `0001` as historical bootstrap record.
- `docs/SUCCESSOR_CHARTER.md` now distinguishes the historical roadmap from the active gap-closure plan.
- `docs/plans/0001_successor_roadmap.md` is marked as a completed historical baseline rather than an active plan.
- `docs/STATUS.md` no longer claims that OpenClaw runtime proof and full consumer-side adoption are already complete.
- `docs/plans/0020_vision_gap_closure.md` now marks Gap 5 and Gap 10 as partial rather than fully closed.
- `CLAUDE.md` and `AGENTS.md` no longer say "all 10 vision gaps are closed."

## Highest-Value Next Steps

1. Prove consumer-side adoption, not just repo-local adapters:
   `research_v3 -> onto-canon6` from the consumer side, and a DIGIMON-side runbook or command path that uses the imported graph in normal workflow.
2. Prove Gap 10 for real:
   run OpenClaw against onto-canon6 and show that repo-local `.openclaw` contracts are actually consumed by the mission runner.
3. Close the last Gap 5 semantic question:
   validate DIGIMON weight handling on a non-unity-confidence slice.
4. Upgrade entity resolution from exact-match only:
   use `rapidfuzz` rather than hand-rolling fuzzy matching.

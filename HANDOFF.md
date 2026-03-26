# Handoff: onto-canon6

**Date**: 2026-03-26
**Scope**: Phase 3 — audit fixes, fuzzy resolution, extraction quality, judge filter

## What Is Actually Proven

| Gap | Status | Evidence |
|---|---|---|
| 1. Predicate names | Closed | Already in sumo_plus.db |
| 2. Non-military domain | Closed | Financial + academic + DoDAF |
| 3. Entity resolution | Closed | Exact + fuzzy (rapidfuzz) |
| 4. Temporal qualifiers | Closed | Extraction + Foundation IR |
| 5. DIGIMON export | Closed | Export + import + query + non-unity confidence weights |
| 6. research_v3 adapter | Closed (adapter-level) | graph.yaml import, 48 real claims |
| 7. Epistemic on data | Closed | 16 scored, 19 tensions, 1 supersession |
| 8. ProbLog spike | Closed | 45 derived facts, decision: use ProbLog |
| 9. Second vocabulary | Closed | dodaf_minimal E2E |
| 10. OpenClaw | Partially closed | Spec exists, no runtime proof |

## Key Findings This Phase

### Extraction quality is NOT the bottleneck we thought

The operational prompt (`text_to_candidate_assertions.yaml`) scored **88%
structural validity** across all 17 PSYOP benchmark cases (35/40 valid
candidates, 15/17 cases with output, 0 errors, 71s total). This is dramatically
better than the experiment variants (25%).

**Root cause of the experiment failure**: the experiment config lacked
`model_override`, causing task-based model selection to route through
OpenRouter (55% timeout rate). Fixed: `model_override: gemini/gemini-2.5-flash`
now set in experiment config.

### Documentation audit corrected overclaims

Review agent correctly identified Gap 5 and Gap 10 as partial, not fully closed.
Gap 5 is now fully closed (epistemic confidence wired into Digimon weight).
Gap 10 remains partial (spec only, no runtime proof).

## What Was Built This Phase

| Deliverable | Description |
|------------|-------------|
| Fuzzy entity resolution | rapidfuzz token_sort_ratio + entity-type guard |
| LLM-judge quality filter | Optional post-extraction filter (config-gated) |
| Experiment reliability fix | model_override added to experiment config |
| Gap 5 full closure | Epistemic confidence → Digimon edge weight |
| Project-meta convergence updates | DIGIMON + research_v3 docs updated |
| Documentation audit | 6 inconsistencies fixed, 4 ambiguities documented |

## Key Context

- Model: `gemini/gemini-2.5-flash` (stable, <2s direct API calls)
- `LLM_CLIENT_TIMEOUT_POLICY=ban` — timeouts disabled in this env
- 405 tests passing
- Operational prompt: 88% structural validity on full benchmark
- Judge filter: wired but off by default (`enable_judge_filter: false`)

## Next Steps

1. **Enable and test judge filter** on a real extraction run
2. **Run experiment with fixed model_override** to get real variant comparison
3. **Prove consumer-side adoption** (research_v3 and DIGIMON workflow)
4. **Run real OpenClaw mission** to close Gap 10

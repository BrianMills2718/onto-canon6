# TODO

## Active Block

No active plan. Plan `0071` completed 2026-04-05.
All ROADMAP Tier 1 goals are met. onto-canon6 is in maintenance mode.

### Plan 0071 — completed 2026-04-05
- [x] Plan 0067 marked completed
- [x] LLM entity resolution promotion decision note written
- [x] 3 OSINT queries run against Iran DIGIMON graph (mean 2.0/2.0)
- [x] Query evidence added to assertion_semantics_evaluation.md
- [x] Verdict: thin semantics sufficient for current phase
- [x] ROADMAP.md Tier 1 updated — Full pipeline E2E marked DONE
- [x] HANDOFF.md updated

## Current State (2026-04-05)

Most recently completed blocks:
- Plan `0070` — graph-value stop policy, promoted contract profile
  (Palantir: 23 findings → 28 entities + 23 DIGIMON rels)
- Plan `0069` — non-Gemini fresh memo proof
- Plan `0068` — memo semantic lift

What is proven end-to-end:
- Full pipeline: research_v3 → onto-canon6 → DIGIMON (63 entities, 62 rels, Iran)
- Memo path (research_v3 memo.yaml → ClaimRecord → onto-canon6 → DIGIMON)
- Graph path (research_v3 graph.yaml → ClaimRecord → onto-canon6 → DIGIMON)
- grounded-research path (Palantir, EU sanctions)
- Entity resolution: 25-doc PSYOP corpus — precision 1.00, recall 0.9643, 0 false merges, 10/10 questions

What is NOT yet proven:
- Consumer value: does the DIGIMON graph actually answer real OSINT questions?

## Longer-Term Queue

- [ ] Option A predicate enrichment — activates when first consumer needs typed edges
- [ ] Entity resolution 500+ docs — activates when corpus exceeds scale
- [ ] Cross-project CI — auto-run contract tests on schema change (medium)
- [ ] Provenance scripts relocation — move to DIGIMON when it stabilizes as consumer
- [ ] Revisit first-class source-artifact query after Plan `0068`
- [ ] Revisit richer DIGIMON interchange only through DIGIMON Plan 23
- [ ] Revisit trusted bulk ingestion only if real workflow makes review the bottleneck

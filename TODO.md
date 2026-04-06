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

## Planning Gaps (added 2026-04-05)

Items confirmed as real strategic gaps not yet tracked anywhere:

- [ ] **Consumer value gate** — "What is NOT yet proven" above has no acceptance threshold.
      Define: N real OSINT questions, M% correct answers from DIGIMON using onto-canon6 graphs,
      before onto-canon6-backed graphs are declared production-ready as a graph source.
      Currently the proof is 3 synthetic queries at 2.0/2.0 — too thin to gate on.
      *Activates next: this is the #1 blocker for calling the system useful.*

- [ ] **DIGIMON feedback loop** — pipeline is unidirectional. When DIGIMON fails to
      retrieve an entity or resolve an alias, there is no path back to onto-canon6.
      Define a lightweight feedback mechanism: e.g., a structured "missed entity" log
      from DIGIMON benchmark runs that can be reviewed in onto-canon6 to update
      canonicalization rules. This closes the improvement loop.

- [ ] **LLM resolution promotion gate** — Plan 0071 notes `default_strategy: exact`
      stays for now but defers the promotion decision indefinitely. Define the explicit
      conditions: corpus size threshold, query recall gap, per-query cost budget.
      Without a gate, this decision silently drifts as corpus grows.

- [ ] **Extraction quality on new domains** — proven on defense tech (Palantir) and
      disinformation (Iran). Financial crime, supply chain, or biotech domains will hit
      different failure modes: technical jargon, dense entity networks, weak co-reference.
      Before expanding the pipeline to new domains, run a small extraction quality test
      (10-20 docs) and record the failure family.

- [ ] **Query surface observability audit** — CLAUDE.md Principles require `task=`,
      `trace_id=`, `max_budget=` on all llm_client calls. Query surfaces (entity search,
      assertion search, identity browse) added in Plans 0028/0063/0064 have not been
      audited for compliance with these fields. Run `make errors` after a query session
      and verify no unbounded calls appear.

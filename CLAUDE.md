# onto-canon6

Governed-assertion middleware for the ecosystem. Takes candidate assertions
from text or external producers, reviews them, and promotes durable graph
state for downstream consumers.

## Read First

1. `README.md`
2. `docs/SUCCESSOR_CHARTER.md`
3. `docs/STATUS.md`
4. `docs/ROADMAP.md` — forward-looking priorities and "what done looks like"
5. `HANDOFF.md` — session handoff and immediate priorities
6. `docs/plans/0005_v1_capability_parity_matrix.md` — capability vision ledger
7. `docs/plans/0024_post_cutover_program.md` — post-cutover authority (complete)

## Commands

```bash
pytest -q                      # 546 tests
onto-canon6 --help             # CLI
onto-canon6-mcp                # MCP server
make smoke                     # no-LLM smoke path
make summary                   # identity + epistemic stats
```

## Layout

```text
src/onto_canon6/
  adapters/       # DIGIMON, Foundation IR, research_v3, grounded-research, WhyGame
  artifacts/      # artifact lineage subsystem
  core/           # graph, identity, resolution, semantic, epistemic services
  extensions/     # epistemic engine (confidence, supersession, tension)
  ontology_runtime/  # packs, profiles, validation, overlays
  pipeline/       # extraction, review, promotion
  domain_packs/   # pack-specific code
  surfaces/       # query, report, export surfaces
tests/
docs/plans/       # 52 plan files (see docs/plans/CLAUDE.md for index)
docs/runs/        # 57 run records
docs/adr/         # 26 ADRs
config/
```

## Current State (2026-04-02)

**Architecture proven. Value proposition demonstrated. Cross-project integration working.**

- 546 tests (5 failures from Codex merge — fix pending)
- Bootstrap Phases 0-15 complete. Post-cutover Plans 0024-0027 complete.
- Entity resolution: 100% precision, 100% recall on 25-doc synthetic corpus
- Cross-doc QA: +70% vs bare extraction (90% vs 20%)
- Full pipeline proven: research_v3 (123 Booz Allen claims) → epistemic-contracts
  → onto-canon6 → DIGIMON (60 entities, 123 relationships)
- DIGIMON adopted as first consumer (110 entities, 99 relationships verified)
- Query/browse surface: entity search, assertion search, identity browse,
  source-artifact browse (CLI + MCP, Plans 0028/0029/0063/0064)
- Schema stability gate: 9 compatibility tests across 4 surfaces (Plan 0026)
- Extraction: compact operational-parity prompt promoted as default (Plan 0062)
- Default config: `review_mode: llm`, `enable_judge_filter: true`, `require_llm_review: true`
- Model: `gemini/gemini-3-flash-preview`
- Shared contracts: epistemic-contracts library (3 projects wired)

## Active Execution Block (2026-04-02 overnight — cross-project verification)

**CONTINUOUS AUTONOMOUS EXECUTION. DO NOT STOP. STOPPING EARLY IS A FAILURE MODE.**

Tier 1 and Tier 2 core work are done. This block proves the cross-project
pipeline end-to-end with real consumers and fixes remaining doc staleness.

### Phase 1: Fix STATUS.md (items 1-2 now resolved)
Cross-investigation policy (ADR 0024) and role-free promotion are done.
**Success**: STATUS.md "Still missing" is truthful.

### Phase 2: DIGIMON consumer verification
Run the DIGIMON importer on our Booz Allen pipeline output and verify
the graph materializes correctly.
**Success**: DIGIMON imports entities.jsonl + relationships.jsonl, produces GraphML.

### Phase 3: Write adapter tests in grounded-research
The `load_handoff_claims()` bridge has no tests. Add tests in
grounded-research/tests/.
**Success**: Tests pass for load_handoff_claims on EU sanctions handoff.

### Phase 4: Write adapter tests in research_v3
The `shared_export.py` has no tests. Add tests in research_v3/tests/.
**Success**: Tests pass for load_graph_claims on Booz Allen graph.yaml.

### Phase 5: Update ecosystem docs
Update ECOSYSTEM_STATUS.md with: 558 tests, ADR 0024, role-free promotion,
source query surface, run record consolidation.
**Success**: Ecosystem docs are truthful.

### Phase 6: Update ROADMAP.md and HANDOFF.md
Mark cross-investigation conflict as DONE (ADR adopted), role-free as DONE.
Update "What's Next" to reflect actual remaining work.
**Success**: Forward-looking docs are current.

### Phase 7: Push all repos
**Success**: onto-canon6, grounded-research, research_v3, project-meta pushed.

**Pre-made decisions:**
- DIGIMON import: use existing scripts/import_onto_canon_jsonl.py
- Adapter tests: lightweight, fixture-based, no LLM calls
- Commit each verified phase immediately
- Do not stop between phases

- **Extraction is a producer, not core.** Don't couple core governance logic
  to extraction-specific assumptions.
- **Resolution strategies are consumer-chosen.** onto-canon6 provides
  infrastructure, consumers choose the strategy.

## Integration Decisions (2026-03-24)

1. **Entity type CURIE namespacing** — RESOLVED. `oc:` and `sumo:` prefixes.
2. **Provenance model** — DECIDED. onto-canon6 exposes its own provenance.
   Foundation `provenance_refs` mapped at export time. No Foundation event log.
3. **Entity ID + dedup** — DECIDED. onto-canon6 owns identity infrastructure.
   Consumers choose resolution strategy. Export adapters wire identity subsystem.

## Working Rules

- **Autonomy is the default.** Continue executing end to end. Do not stop at
  "plan written" or "one test passed."
- **Do not pause for confirmation.** Keep moving through phases. Surface only
  when: plan complete, real blocker, or material uncertainty.
- **Stopping early is a failure mode.** Continuous execution across all phases.
- **Commit early and often.** Every verified increment gets its own commit.
- **Parity matrix is the vision ledger.** Deferred ≠ abandoned.
- **No casual repo drift.** New changes must justify against the ADR set.

## Workflow

- All significant work follows plans in `docs/plans/`
- Commit verified increments with `[Plan #N]` prefix
- Use `[Trivial]` for <20 line changes

## References

| Doc | Purpose |
|-----|---------|
| `docs/ROADMAP.md` | Forward-looking priorities |
| `docs/plans/CLAUDE.md` | Plan index |
| `config/config.yaml` | Extraction and prompt configuration |
| `KNOWLEDGE.md` | Cross-agent operational findings |

## LLM Integration

- All LLM calls route through `llm_client` with mandatory `task=`, `trace_id=`,
  `max_budget=` kwargs.
- Prompts are YAML/Jinja2 templates in `prompts/`, loaded via
  `llm_client.render_prompt()`. No f-string prompts in Python.
- Extraction config, prompt refs, and variant definitions in `config/config.yaml`.
- No examples in prompts without approval.

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

## ACTIVE EXECUTION BLOCK — Plan 0029 Doc Hardening Sprint (2026-04-02 overnight)

**NEVER STOP. NEVER STOP. NEVER STOP.**

This is an overnight autonomous run. Stopping early for any reason other than a
genuine architectural blocker or irreversible-action boundary is a failure mode.
A completed phase, a passing test, or a committed increment is NOT a stop condition.
Move immediately to the next phase. Do not ask. Do not pause.

**Stop ONLY for:**
1. An action that is irreversible AND affects shared state (force push, drop tables)
2. A genuine architectural decision not pre-made in the plan

**Everything else — uncertainty, slow tests, partial results, "should I continue?"
— is NOT a stop condition. Log it and proceed.**

### Sprint Phases (execute in order, commit each):
- [ ] Phase 1: pyproject.toml deps + doc quick fixes (test count, model, ProbLog)
- [ ] Phase 2: Config validation Pydantic model + tests
- [ ] Phase 3: DIGIMON value-only assertion behavior documented (not a bug)
- [ ] Phase 4: COORDINATION.md — Codex merge protocol
- [ ] Phase 5: STATUS.md reorganized by subsystem with ToC
- [ ] Phase 6: Plan 0030 — entity extraction from grounded-research claims
- [ ] Phase 7: Plan 0031 — next real investigation (Anduril Industries)
- [ ] Phase 8: docs/plans/CLAUDE.md updated, full pytest, push

**Active plan**: `docs/plans/0029_doc_hardening_sprint.md`

## Commands

```bash
pytest -q                      # 558 tests
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

- 558 tests, 0 failures
- Bootstrap Phases 0-15 complete. Post-cutover Plans 0024-0028 complete.
- Entity resolution: 100% precision, 100% recall on 25-doc synthetic corpus
- Cross-doc QA: +70% vs bare extraction (90% vs 20%)
- Full pipeline proven: research_v3 (123 Booz Allen claims) → epistemic-contracts
  → onto-canon6 → DIGIMON (60 entities, 123 relationships)
- grounded-research pipeline proven: Palantir (22 claims) + EU sanctions (8 claims)
- Query/browse surface: entity search, assertion search, identity browse,
  source-artifact browse (CLI + MCP, Plans 0028/0063/0064)
- Schema stability gate: 9 compatibility tests across 4 surfaces (Plan 0026)
- Extraction: compact operational-parity prompt promoted as default (Plan 0062)
- Default config: `review_mode: llm`, `enable_judge_filter: true`, `require_llm_review: true`
- Model: `gemini/gemini-2.5-flash` (runtime default; gemini-3-flash-preview was target but too slow)
- Shared contracts: epistemic-contracts library (3 projects wired)
- ProbLog adapter: available (`onto-canon6 evaluate-rules`), no consumer uses it yet

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
- **Multi-agent coordination**: See `COORDINATION.md` before starting multi-file
  changes. Pull before edit. Rebase worktrees before merging.

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

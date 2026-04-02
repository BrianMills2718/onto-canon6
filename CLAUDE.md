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

## Active Execution Block (2026-04-02 overnight)

**CONTINUOUS AUTONOMOUS EXECUTION. DO NOT STOP. STOPPING EARLY IS A FAILURE MODE.**

Execute all phases in order. Commit each verified phase immediately.
Do not pause between phases. The only valid stop conditions are:
1. All phases are complete
2. A real architectural uncertainty not covered by this plan
3. An irreversible action affecting shared state

### Phase 1: Fix 5 test failures from Codex merge
Re-apply fixes overwritten by Codex worktree merges:
- `test_cli_flow.py`: add `extraction_goal` kwarg to `_FakeTextExtractionService`
- `test_mcp_server.py`: `list_tools()` → `get_tools()` (FastMCP API)
- `notebook_registry.yaml`: remove stale plan file references
- Master journey notebook: fix Q-code Q5388397→Q348250, add `extraction_goal`
**Success**: `pytest` shows 0 failures.

### Phase 2: Clean up plans/CLAUDE.md
Move 35+ completed 24h blocks from Active to Completed table.
**Success**: Active Plans table has ≤5 entries.

### Phase 3: Restore docs/ROADMAP.md
Recreate forward-looking roadmap (deleted by Codex merge).
**Success**: One document that answers "what should I work on next?"

### Phase 4: Update HANDOFF.md
Merge both sessions' work into one coherent handoff.
**Success**: New session can understand full state from HANDOFF alone.

### Phase 5: Update README.md
Fix test count, update maturity, add cross-project integration.
**Success**: README reflects current state.

### Phase 6: LLM resolution on Booz Allen corpus
Run full_pipeline_e2e.py with strategy=llm for real entity merges.
**Success**: Resolution finds real alias merges.

### Phase 7: Ecosystem docs update
Update ECOSYSTEM_STATUS.md, CAPABILITY_BOUNDARIES.md, Plan 56.
**Success**: Ecosystem docs consistent with code.

### Phase 8: Final verification + push
Full test suite, push all repos.
**Success**: 0 failures, all repos pushed.

**Pre-made decisions:**
- Model: `gemini/gemini-3-flash-preview`
- Config: `review_mode: llm`, `enable_judge_filter: true`
- Commit each verified phase immediately
- Do not stop between phases

## Composability Principle

onto-canon6 is a composable toolkit, not a monolithic application:

- **Vocabulary is pluggable.** Packs and profiles are the mechanism. Don't
  hardcode assumptions about specific predicates or entity types.
- **Extensions are pluggable.** The epistemic engine is ONE extension. Keep
  extensions in `extensions/`, not in core.
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

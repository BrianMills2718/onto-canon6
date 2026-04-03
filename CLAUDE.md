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

## Continuous Execution Policy

**═══════════════════════════════════════════════════**
**  NEVER STOP. NEVER STOP. NEVER STOP.             **
**  STOPPING EARLY IS THE FAILURE MODE.              **
**  PLAN COMPLETE IS NOT A STOP CONDITION.           **
**  ONE GREEN TEST IS NOT A STOP CONDITION.          **
**  ONE COMMIT IS NOT A STOP CONDITION.              **
**  THIS BLOCK IS NOT DONE UNTIL A REAL MEMO         **
**  PRODUCES REAL GRAPH STRUCTURE.                   **
**═══════════════════════════════════════════════════**

Autonomous runs execute all phases of the active plan continuously without
pausing for confirmation. The agent is expected to move from phase to phase
the moment a phase is verified and committed. Not asking "should I continue?"
is correct behavior — the answer is always yes unless a hard stop condition
is met.

**Hard stop conditions (the ONLY valid reasons to stop):**
1. An irreversible action affecting shared state that was NOT explicitly
   pre-made in the active plan (force push to main, DROP TABLE in production)
2. A genuine architectural decision not covered by the active plan, where
   proceeding either direction would require undoing work later

**Everything below is NOT a stop condition — log it and keep moving:**
- A metric falls 1 short of the acceptance gate → document shortfall, proceed
- An LLM call times out → wait 300s, try gemini/gemini-2.5-flash-lite fallback
- A test is flapping → retry once; if still failing, log in KNOWLEDGE.md and skip
- "Should I continue?" → yes, always
- The work is large or multi-commit → that is expected; continue
- research_v3 retrieval returns fewer sources than expected → proceed with what's there
- An unexpected file exists → investigate before deleting, then proceed
- A plan produces partial results → commit what's verified, continue

**Decision tree for common ambiguous cases:**

| Situation | Action |
|-----------|--------|
| Investigation produces N-1 claims (just under threshold) | Document in KNOWLEDGE.md, proceed. Thresholds are quality guides, not binary blockers. |
| LLM model slow/timeout | Wait 300s. Switch to `gemini/gemini-2.5-flash-lite`. Log switch. |
| research_v3 run produces <5 sources | Still run pipeline. Log "thin retrieval". |
| Test fails that wasn't failing before | If caused by current changes: fix first. If pre-existing: log, skip, continue. |
| Plan acceptance criterion is ambiguous | Use metric proxies defined in plan doc. Document interpretation. |
| research_v3 completely fails to run | Use Booz Allen fallback graph.yaml (always available at `~/projects/research_v3/output/20260315_190332_.../graph.yaml`) |

**Active plan**: none currently open. Most recently completed:
`docs/plans/0069_24h_non_gemini_fresh_memo_proof.md`

**Current sprint phases:**
- [x] Phase 0: Authority activation (`CLAUDE.md`, plan index, TODO, progress anchor)
- [x] Phase 1: research_v3 fresh-run config override support
- [x] Phase 2: Claude runtime profile and verification
- [x] Phase 3: fresh live memo proof
- [x] Phase 4: onto-canon6 pipeline proof
- [x] Phase 5: Truth surfaces and closeout

## Commands

```bash
pytest -q                      # 562 tests
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

## Current State (2026-04-03)

**Architecture proven. A fresh live non-Gemini memo checkpoint now produces graph value without repair; the next gap is deciding runtime promotion, tightening loop stop behavior, and deciding whether thin shared-assertion semantics are sufficient.**

- 562 tests, 0 failures
- Bootstrap Phases 0-15 complete. Post-cutover Plans 0024-0028 complete.
- Entity resolution: 100% precision, 100% recall on 25-doc synthetic corpus
- Cross-doc QA: +70% vs bare extraction (90% vs 20%)
- Full pipeline proven: research_v3 (123 Booz Allen claims) → epistemic-contracts
  → onto-canon6 → DIGIMON (60 entities, 123 relationships)
- Memo path proven: real Palantir memo (61 findings) → shared contracts →
  onto-canon6 → DIGIMON (40 entities, 61 relationships)
- Fresh live memo checkpoint proven: Palantir round-4 Claude checkpoint
  (34 findings) → shared contracts → onto-canon6 → DIGIMON
  (34 entities, 30 relationships)
- grounded-research pipeline proven: Palantir (22 claims) + EU sanctions (8 claims)
- Query/browse surface: entity search, assertion search, identity browse,
  source-artifact browse (CLI + MCP, Plans 0028/0063/0064)
- Schema stability gate: 9 compatibility tests across 4 surfaces (Plan 0026)
- Extraction: compact operational-parity prompt promoted as default (Plan 0062)
- Default config: `review_mode: llm`, `enable_judge_filter: true`
- Model: `gemini/gemini-2.5-flash` (runtime default; gemini-3-flash-preview was target but too slow)
- Shared contracts: epistemic-contracts library (3 projects wired)
- ProbLog adapter: available (`onto-canon6 evaluate-rules`), no consumer uses it yet

## Documented Open Uncertainty (2026-04-03)

This is intentionally unresolved. Do not treat it as decided unless a later
plan closes it with proof.

- **Runtime promotion is still open.** `research_v3/config_loop_claude_runtime.yaml`
  is now a proved option for contract-style investigations, but it is not yet
  promoted as the default runtime for that class of work.
- **Stop behavior is still open.** Fresh contract investigations can now
  produce downstream-usable memo and graph structure before loop confidence is
  high enough to stop. It is not yet decided whether the loop should stop once
  graph value is already present, or continue until the current confidence gate
  is met.
- **Temporary operating rule.** Treat the Claude runtime as a verified option,
  not a global default. Treat proof-grade memo checkpoints as valid downstream
  consumer artifacts when they already satisfy graph acceptance, but do not
  describe them as completed final-report runs.

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

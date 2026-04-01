# Handoff: onto-canon6 — 2026-04-01

## Session Focus

Plan 0031: 24h entity-resolution hardening block in the isolated
worktree branch `codex/onto-canon6-integration-planning`.

## What Landed

Committed in the isolated worktree as:

- `b83de81` — `Start Plan 0031 entity resolution hardening block`
- `9a7b3c3` — `Fix auto-review judge parity for Plan 0031`
- `78bbc8f` — `Harden Plan 0031 resolution decisions`
- `41d8f02` — `Close Plan 0031 hardening block`

Main effects:

1. the stale `_judge_candidate()` seam now honors explicit bounded judge-model
   overrides and no longer fail-opens to acceptance on judge failure;
2. deterministic person-name hardening removed the prior same-surname false
   merge family;
3. subtype-equivalent org/place mentions are no longer pre-rejected before LLM
   clustering;
4. fresh hardened exact and LLM rerun artifacts now live in:
   - `docs/runs/scale_test_exact_2026-04-01_073211.json`
   - `docs/runs/scale_test_llm_2026-04-01_074236.json`
   - `docs/runs/2026-04-01_entity_resolution_hardening_rerun.md`

## Current State

1. Plan 0031 is complete.
2. The hardening block succeeded on safety, not on promotion:
   - hardened exact: precision `1.00`, recall `0.244`, false merges `0`,
     answer rate `0.80`, accuracy `0.40`
   - hardened llm: precision `1.00`, recall `0.308`, false merges `0`,
     answer rate `0.20`, accuracy `0.20`
3. The prior `John Smith` / `James Smith` false-merge family is no longer the
   active blocker.
4. Plan 0025 remains active, and the next narrow frontier is:
   - extraction/schema failure that emitted `kind: "event"` and dropped
     `doc_06` from the hardened LLM rerun
   - unresolved alias-heavy org / installation families
   - weak unique-cluster resolution for abbreviated person mentions

# Handoff: onto-canon6 — 2026-04-01

## Session Focus

Plan 0030: 24h entity-resolution value-proof execution block in the isolated
worktree branch `codex/onto-canon6-integration-planning`.

## What Landed

Committed in the isolated worktree as:

- `b942ce4` — `Freeze value-proof contracts and add evaluator`
- `d5558b6` — `Add value-proof runners and operator targets`
- `e7e5515` — `Advance Plan 0030 with exact and bare value-proof runs`

Main effects:

1. Plan 0025 now has a frozen question fixture, typed evaluator, and
   reproducible exact / bare / LLM comparison artifacts.
2. The decision note now lives in
   `docs/runs/2026-04-01_entity_resolution_value_proof.md`.
3. The repo no longer truthfully says "metrics missing" for Plan 0025.

## Current State

1. Plan 0030 is complete.
2. Plan 0025 remains active, but the unresolved work is now narrow:
   - same-surname person false merges in the LLM strategy
   - unresolved organization / installation aliases
   - stale `_judge_candidate()` model-override seam
3. The next decision is not "do we have evidence?" but "what hardening work is
   required before the LLM strategy can replace exact matching as default?"

# Handoff: onto-canon6 — 2026-03-31

## Session Focus

Lane 3 closure, Lane 4 policy clarification, Lane 5 ordering, and then full
implementation of the first queryability slice in the isolated worktree branch
`codex/onto-canon6-integration-planning`.

## What Landed

Committed in the isolated worktree as:

- `e280b60` — `Plan Lane 3 compatibility artifacts`
- `4caebdf` — `Refine Lane 3 implementation decisions`
- `ebcb384` — `Add Lane 3 compatibility fixtures and checks`
- `a3c598b` — `Update Lane 3 plan status after gate landing`
- `ace01e9` — `Close Lane 3 schema gate planning`
- `3062f49` — `Clarify Lane 4 extraction promotion gate`
- `e8f9c8f` — `Plan Lane 5 deferred parity ordering`
- `99fff08` — `Plan browse and search capability recovery`
- `9412854` — `Refresh top-level docs for current plan stack`
- `d8d6f97` — `Align legacy trackers with current program`
- `a7489db` — `Refresh tracker metadata and handoff`
- `4e9123c` — `Refresh consumer proof references`
- `4c78dff` — `Complete query surface inventory`
- `1b7d6c5` — `Pre-make query surface contracts`
- `f994cb8` — `Start 24h query surface execution block`
- `502289d` — `Add read-only query surface service`
- `da42cbe` — `Add query surface CLI commands`
- `754eb4d` — `Add query surface MCP tools`
- `fc95d4e` — `Record query surface real-proof verification`

Main effects:

1. Lane 3 is now genuinely closed in docs and tests, not just "planned":
   deterministic compatibility fixtures exist for promoted graph, governed
   bundle, Foundation IR, and DIGIMON v1 export.
2. Lane 4 now has an explicit promotion gate in
   `docs/plans/0014_extraction_quality_baseline.md`.
3. Lane 5 now executes through
   `docs/plans/0027_deferred_parity_reprioritization.md`, which classifies
   deferred parity work into next-active / protected-deferred /
   consumer-blocked / abandoned-with-rationale.
4. The next-active queryability recovery plan now exists as
   `docs/plans/0028_query_browse_surface.md`, and its first read-only slice is
   now landed end to end through `docs/plans/0029_24h_query_surface_execution_block.md`.
5. The first read-only query surface now exists across:
   - shared service: `src/onto_canon6/surfaces/query_surface.py`
   - typed contracts: `src/onto_canon6/surfaces/query_models.py`
   - CLI: `search-entities`, `get-entity`, `search-promoted-assertions`,
     `get-promoted-assertion`, `get-evidence`
   - MCP: matching `canon6_*` tools in `src/onto_canon6/mcp_server.py`
   - proof note: `docs/runs/2026-03-31_query_surface_real_proof.md`
6. `README.md`, `CLAUDE.md`, `docs/STATUS.md`, the plans index, the parity
   matrix, and the vision-gap tracker now point to the same current Lane 3-5
   stack instead of leaving it implicit.

## Current Recommended Next Step

If work continues:

1. stay on `codex/onto-canon6-integration-planning`;
2. keep the planning stream on `codex/onto-canon6-integration-planning` even
   though the main checkout is currently clean, so follow-on work stays
   isolated from active implementation threads;
3. the next unresolved implementation frontier is still Plan 0025 value proof;
4. queryability work after this should be hardening/widening under Plan 0028,
   not redoing the first slice.

## Current State

- isolated worktree branch clean after the commits above
- main `/home/brian/projects/onto-canon6` checkout is currently clean, but this
  planning stream should still continue in the isolated worktree branch

# Handoff: onto-canon6 — 2026-03-28

## Session Focus

Documentation-authority cleanup, post-cutover program clarification, and
architecture review of the DIGIMON boundary.

## What Landed

### 1. Documentation authority cleanup

Committed on `main` as:

- `6854cfe` — `Clarify post-cutover documentation authority`

Main effects:

1. added `docs/plans/0024_post_cutover_program.md`
2. removed broken current-plan references from top-level reading surfaces
3. aligned README / charter / status / active plans around one current
   post-cutover program
4. marked `0021` completed
5. reduced `0022` to residual historical cleanup
6. made `0022a` clearly historical/pre-cutover

### 2. Current post-cutover execution authority

The intended reading/authority split is now:

1. `docs/plans/0005_v1_capability_parity_matrix.md`
   - full preserved capability vision
2. `docs/plans/0024_post_cutover_program.md`
   - ordered execution lanes after cutover
3. `docs/plans/0020_vision_gap_closure.md`
   - ecosystem-gap tracker

The repo is no longer supposed to infer current program order from scattered
historical plans.

## DIGIMON Boundary Review

### Strategic conclusion

The long-term split remains:

1. `onto-canon6` owns governed semantic/canonical state
2. DIGIMON should own retrieval-oriented projections and retrieval runtime
3. analysis is conceptually separate, but does not need a repo split now

### Important nuance

The current DIGIMON adapter surface is still thinner than that long-term
architecture implies.

`src/onto_canon6/adapters/digimon_export.py` currently exports a flat entity /
relationship JSONL shape. It does not yet export:

1. alias memberships
2. passage artifacts
3. evidence refs
4. assertion-to-passage links
5. artifact-lineage context

So the advice was:

1. do **not** move retrieval projections into onto-canon6 core
2. do **not** assume the current DIGIMON export is already the right semantic
   interchange
3. consider Foundation-style assertion export as the stronger basis for any
   richer future DIGIMON contract

### Foundation export relevance

`src/onto_canon6/adapters/foundation_assertion_export.py` is closer to the
likely long-term interchange shape than `digimon_export.py` because it already
preserves:

1. typed role fillers
2. alias ids
3. qualifiers
4. assertion identity

## Recommended Next Actions

1. Execute Plan 0024 Lane 2:
   choose and prove the first real consumer workflow.
2. Define Lane 3 schema-stability gates explicitly.
3. Treat any DIGIMON convergence beyond the current adapter as a deliberate
   richer interchange effort, not as a casual extension of the flat export.
4. Keep extraction-quality hardening under Plan 0014 tied to transfer evidence.

## Current Repo State

- `main` clean after the doc-authority cleanup commit
- no uncommitted changes from this session

# Handoff: onto-canon6

**Date**: 2026-03-26
**Session**: All remaining items completed

---

## What Was Done (final batch)

| Item | Commit | Result |
|------|--------|--------|
| Wire review_mode auto-flow | `1651ee1` | extract_and_submit auto-accepts+promotes when review_mode=auto |
| Fix MCP test | `8b7b224` | Use list_tools() instead of _tool_manager._tools |
| Verify llm_client fixes | verified | Registry + IPv4 fixes on main via merged PRs |
| Archive stale docs | `0091cd0` | 16 plans moved to archive/, KNOWLEDGE.md deleted |
| Evidence grounding validator | `6ed3086` | Flags ungrounded candidates (_grounding_status) |
| Dynamic predicate filtering | `a61ec70` | ODKE+ snippet pattern, keyword relevance ranking |

## Current State

- **430 tests passing**, 0 failures
- **4 active plans**: 0001 (historical), 0005 (parity matrix), 0014 (extraction quality), 0020 (gap tracker)
- **16 archived plans** in docs/plans/archive/
- All deferred items in parity matrix verified accurate

## Key Capabilities Added This Session

### Configurable Review Modes
`config.yaml: pipeline.review_mode: human|auto|llm`
- `human`: manual accept/reject (default)
- `auto`: auto-accept + auto-promote all valid candidates
- `llm`: LLM-judge decides accept/reject, auto-promote accepted
- Batch CLI: `accept-all`, `promote-all`, `make govern` (full auto)

### ODKE+ Patterns
- **Evidence grounding**: candidates flagged as ungrounded when no evidence spans resolve
- **Dynamic predicate filtering**: `max_predicates_in_prompt` config renders only relevant predicates
- **LLM-judge quality filter**: optional post-extraction filter (enable_judge_filter)

## Environment
- Model: `gemini/gemini-2.5-flash` (direct API, <2s)
- `LLM_CLIENT_FORCE_IPV4` auto-detected on WSL2
- `review_mode: human` (default), change to `auto` for batch processing
- ProbLog, rapidfuzz in shared venv

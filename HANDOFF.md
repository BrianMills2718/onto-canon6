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

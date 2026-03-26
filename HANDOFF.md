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

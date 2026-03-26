# Handoff: onto-canon6

**Date**: 2026-03-26
**From**: Claude Code (marathon session — vision gaps + hardening + strategic review)
**Duration**: ~8 hours continuous

---

## Session Summary

This session completed three phases of work plus a strategic review:

### Phase 1: All 10 Vision Gaps (Plan 0020)
Closed 9/10 gaps fully, 1 partially (Gap 10 — OpenClaw runtime proof missing).

### Phase 2: Hardening + Integration
55 new tests, 3 CLI commands, general-purpose pack, ProbLog adapter, E2E test.

### Phase 3: Strategic Review + Quality
Documentation audit, fuzzy entity resolution, experiment reliability fix,
LLM-judge filter, batch CLI, configurable review modes.

### Cross-Repo Fixes
- **llm_client**: Model registry fix (demote broken gemini-3-flash-preview),
  IPv4 auto-detect for WSL2 (fixes 600s Gemini connection hangs)
- **onto-canon5**: Softened role_type_violation from hard to soft
- **project-meta**: Updated DIGIMON and research_v3 convergence docs

---

## What Is Actually Proven

| Capability | Evidence |
|-----------|---------|
| Extraction quality | 92% LLM-judge reasonable, 100% structural validity (after soft type fix) |
| Multi-domain | Financial, academic, military, DoDAF — all work |
| Entity resolution | Exact + fuzzy (rapidfuzz) with entity-type guard |
| Temporal qualifiers | valid_from/valid_to in extraction + Foundation IR |
| Digimon bridge | Export + import + operator query + non-unity confidence weights |
| research_v3 bridge | graph.yaml import (48 real claims) + CLI |
| Epistemic engine | 16 scored, 19 tensions, 1 supersession on real data |
| ProbLog rules | 45 derived facts with probability propagation |
| Composability | dodaf_minimal + general_purpose packs + psyop_seed coexist |
| Batch pipeline | `make govern` = accept-all → promote-all → auto-resolve in 1 cmd |
| 405 tests | All passing (1 unrelated MCP test fails — FastMCP API change) |

---

## What Is NOT Proven

| Item | Status |
|------|--------|
| OpenClaw runtime | Spec files exist, no mission runner has consumed them |
| Consumer adoption | Bridges proven in isolation, not wired into consumer workflows |
| Review mode: llm | Config field added, LLM-judge filter wired, but `review_mode: "llm"` auto-flow not implemented end-to-end |
| Scale | Largest run: 40 candidates from 17 benchmark cases. No bulk test. |

---

## Incomplete Work (for next agent)

### 1. Finish configurable review_mode implementation
**Status**: Config field `review_mode` added (human|auto|llm). Batch CLI works.
Auto-accept pipeline works via `make govern`. But the `review_mode` config is
not yet read by `extract_and_submit()` to auto-trigger the pipeline. Currently
the caller must choose to call accept-all/promote-all explicitly.

**What's needed**: In `TextExtractionService.extract_and_submit()`, after
extracting, check `config.pipeline.review_mode`:
- `"auto"`: auto-accept + auto-promote all valid candidates
- `"llm"`: run LLM-judge, accept supported, reject unsupported, promote accepted
- `"human"`: current behavior (leave as pending_review)

### 2. Archive stale docs (task #38)
229 markdown files. Completed phase plans (0002-0010) should move to
`docs/plans/archive/`. Status headers were added but files not moved.

### 3. Evidence grounding validator (task #39, ODKE+ pattern)
Evidence spans exist but aren't used for automated grounding validation.
Wire a check: if evidence span text doesn't match source text, flag the
candidate. Cheap string matching, no LLM cost.

### 4. Dynamic predicate catalog filtering (task #40, ODKE+ pattern)
Current prompt renders the full predicate catalog. For the 4,669-predicate
sumo_plus.db, this would be enormous. ODKE+ generates entity-specific
"ontology snippets." Implement: pre-filter predicates by keyword relevance
to source text, render only top 10-20 in the prompt.

### 5. Fix MCP server test
`tests/integration/test_mcp_server.py::test_phase14_mcp_tools_are_registered`
fails because FastMCP API changed (`_tool_manager` attribute removed). Need
to update the test to use the current FastMCP introspection API.

### 6. llm_client registry + IPv4 fixes may need re-merge
Commits `c0660b7` (registry fix) and `45cbdba` (IPv4 auto-detect) exist in
llm_client history but current HEAD `70c2f9e` may not include them (diverged
branches). Verify with `git log --graph` and merge if needed.

---

## Key Context

### Environment
- Model: `gemini/gemini-2.5-flash` (stable, <2s direct API calls)
- `LLM_CLIENT_TIMEOUT_POLICY=ban` — disables request timeouts, NOT socket timeouts
- `LLM_CLIENT_FORCE_IPV4=1` should be set on WSL2 (auto-detected if llm_client IPv4 fix is merged)
- Python: `/home/brian/projects/.venv/bin/python` (shared venv)
- ProbLog, rapidfuzz installed in shared venv

### Extraction quality
- Operational prompt: 92% judge-reasonable, 100% structural validity
- Experiment variants: now work (100% success after model_override fix) but score lower (0.35-1.0)
- API reliability: direct Gemini is <2s; OpenRouter adds 600s IPv6 hangs on WSL2

### Brian's vision (important for framing)
onto-canon6 is **foundational infrastructure** in a 3-bucket ecosystem (Data /
Operations / Orchestration). The goal is NOT consumer-driven delivery — it's
stability and composability so the ecosystem works when all pieces are ready.
Don't apply "ship to consumers now" pressure. Read
`~/projects/project-meta/vision/FRAMEWORK.md` for the north star.

### Files that matter
| File | Purpose |
|------|---------|
| `config/config.yaml` | All config including review_mode, model_override |
| `src/onto_canon6/pipeline/text_extraction.py` | Core extraction (1107 lines) |
| `src/onto_canon6/core/auto_resolution.py` | Entity resolution (exact + fuzzy) |
| `src/onto_canon6/extensions/problog_adapter.py` | ProbLog fact-store adapter |
| `docs/plans/0020_vision_gap_closure.md` | Active gap tracker |
| `docs/plans/0005_v1_capability_parity_matrix.md` | Long-term capability ledger |
| `docs/AUDIT_2026_03_26.md` | Strategic review findings |
| `.openclaw/success-criteria.yaml` | OpenClaw mission spec (not runtime-proven) |

### Known bugs
- `tests/integration/test_mcp_server.py` — FastMCP API change
- llm_client registry/IPv4 commits may need re-merge
- `KNOWLEDGE.md` is empty (either populate or delete)

---

## Commit Log This Session (onto-canon6)

```
0992bef Add configurable review modes + batch accept/promote CLI
8ba53bd Re-run experiment with model_override fix — 100% success, 0 timeouts
cff3b1d Close Gap 5 fully — wire epistemic confidence into Digimon export
247d369 Add fuzzy entity resolution via rapidfuzz token_sort_ratio
d7a7c1f Fix experiment reliability — add model_override to experiment config
a97223a Documentation audit: fix 6 inconsistencies, update parity matrix
7706eb8 [Unplanned] Align docs with real gap-closure status
bd6ed33 Update STATUS.md — 12 new proven capabilities (items 79-90)
13f26c6 Add CLI integration tests for import-research-v3 and evaluate-rules
822ab8e Add identity and epistemic stats to make summary
61a0a5a Build ProbLog fact-store adapter and evaluate-rules CLI
401b457 Create general-purpose ontology pack — 15 entity types, 10 predicates
e5c95b7 Wire import-research-v3 CLI
265aaf2 Add tests for temporal qualifiers
58034de Add tests for research_v3_import — 21 tests
1f2288e Add tests for auto_resolution — 13 tests
dc2345a [Gap 10] Autonomous operation — success criteria and mission spec
84fd99b [Gap 6] research_v3 adapter — FtM entity mapping + claim import
de1cd7b [Gap 8] ProbLog spike — 45 derived facts
49e51df [Gap 7] Epistemic engine on real data
d368d0c [Gap 4] Temporal qualifiers
a8a7226 [Gap 3] Automated entity resolution
44f5ff2 [Gap 2] Non-military domain testing
b32d38f [Gap 1] Already closed
f1ed4a9 [Gap 9] Second vocabulary proof
```

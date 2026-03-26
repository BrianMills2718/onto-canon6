# Handoff: onto-canon6

**Date**: 2026-03-26 (final)
**From**: Claude Code (strategic review + implementation + audit + e2e proof + planning, 2.5 days)
**Session**: 47 onto-canon6 commits, plus llm_client and project-meta fixes

---

## What This Session Delivered

### Schema Enforcement
- **Discriminated union filler types** (`534a52c`): `ExtractedEntityFiller`,
  `ExtractedValueFiller`, `ExtractedUnknownFiller`. entity_type and name required
  at JSON Schema level. LLMs cannot produce null entity_type.
- **No provider enforces value-level constraints** (minProperties, minLength) at
  decode time. This is universal across OpenAI, Gemini, Claude, OpenRouter.
  Fix applied to llm_client (pending commit due to hook bug MP-027).

### Extraction Pipeline
- **Goal-conditioned extraction** — `extraction_goal` is required. Narrow goals
  improve discrimination (3/3 strict-omit correct). CLI: `--goal "..."`.
- **single_response_hardened** promoted as operational prompt with gpt-5.4-mini.
- **model_override** config field for pinning specific models.

### Evaluation
- **accepted_alternatives** in benchmark scoring (14 alternatives across 4 cases).
- **Baseline comparison** proves governance value (43% entity coverage, no
  discrimination, fragmented triples without ontology).

### Integration
- **Foundation Assertion IR adapter** with identity subsystem alias_ids wired.
- **Integration decisions**: provenance = wrapper adds envelope; entity identity =
  onto-canon6 owns infrastructure, consumers choose strategy.
- **Composability principle**: vocabulary, extensions, extraction, resolution are
  all pluggable. Don't refactor until second consumer exists.
- **Framework.md updated**: onto-canon owns governed ABox (not just TBox).

### Documentation Audit (project-meta)
- FRAMEWORK.md: health warning, onto-canon glossary, provenance date refreshed
- FOUNDATION.md: "Deferred from v1" section, EVENT_TAXONOMY cross-link
- Plans 09/12/16/13: status corrections (deferred criteria, clarified scope,
  tuning issues, v2-archived note)
- Archived AGENT_CODING_FRAMEWORK.md and GOVERNANCE_SNAPSHOT.md
- Root .claude/CLAUDE.md: AGENTS.md generation, module relocations, task_graph
  vs OpenClaw boundary
- Hook bugs MP-026/MP-027 documented in meta-process/ISSUES.md

---

## Next Steps (Priority Order)

### ~~1. Fix extraction prompt for e2e flow~~ DONE (2026-03-25)

E2E pipeline proven. Root cause: gemini-3-flash-preview regressed. Fix:
switch to gemini-2.5-flash (stable). model_override wired into extraction
service. Shared evidence span resolver built in llm_client. Makefile
targets working: extract → candidates → accept → promote → summary.

### ~~1. Create clear plans for all 10 vision gaps~~ DONE

Plan 0020 (`docs/plans/0020_vision_gap_closure.md`) covers all 10 gaps with
acceptance criteria, uncertainties, dependencies, and priority ordering.

### 1. (NEW) Review Plan 0020 and start Gap 5 (Digimon real-data export)

Brian wants unambiguous plans for each gap between the vision and current
state. Each plan must identify uncertainties explicitly, be consistent with
`~/projects/.claude/CLAUDE.md`, and follow the principle: "document the full
vision, design for it, defer implementation."

Gap table to plan:

| # | Gap | Current State | Uncertainties |
|---|-----|---------------|---------------|
| 1 | Human-readable predicate names | Not generated | LLM pass over 4,669 senses? Manual? |
| 2 | Non-military domain testing | Only PSYOP text | Which domain? Financial? Academic? |
| 3 | Automated entity resolution | Manual create-identity | What matching strategy? Name-only? Q-code? LLM? |
| 4 | Temporal qualifiers | Deferred by ADR | When to un-defer? Which consumer needs them? |
| 5 | Digimon real-data export test | Adapter exists, untested | Does Digimon's graph builder accept the format? |
| 6 | research_v3 → onto-canon6 adapter | Not started | Entity mapping: FtM → SUMO compatible? |
| 7 | Epistemic engine on real data | Built, untested | What triggers tension? What data has contradictions? |
| 8 | Custom logic / ProbLog spike | Not started | ProbLog vs custom Datalog? Integration with SQLite facts? |
| 9 | Second vocabulary (composability proof) | Designed, 1 vocab tested | Which vocabulary? DoDAF already has a minimal pack |
| 10 | Autonomous operation (OpenClaw) | Not started | success-criteria.yaml format? What makes a "successful" extraction mission? |

Each plan should go in `docs/plans/` following the meta-process plan template.
Plans should be concrete enough for an agent to execute autonomously.

**2026-03-26 progress:**
- Plan 0020 reviewed and tightened for ecosystem consistency:
  - Gap 5 now explicitly depends on a DIGIMON import contract, not an assumed
    graph-builder capability
  - Gap 6 now calls out Foundation Assertion IR / schema-stability alignment
  - Gap 8 no longer treats interpreter placement as undecided; `FRAMEWORK.md`
    already assigns it to Operations (`llm_client`)
  - Gap 2 now notes that "comparable quality" needs an explicit threshold
- Real Gap 5 export completed:
  - `onto-canon6 export-digimon --review-db-path var/e2e_test_2026_03_25/review_combined.sqlite3`
    wrote 20 entity rows and 16 relationship rows
  - DIGIMON now has `scripts/import_onto_canon_jsonl.py`, which imported that
    export into
    `Digimon_for_KG_application/results/onto_canon_e2e_20260325/er_graph/nx_data.graphml`
  - Import result: 19 nodes, 16 edges. The only collapsed duplicate was
    `USSOCOM` (two exported source IDs with the same display name)
  - NetworkX inspection of the imported graph confirms the expected `USSOCOM`
    neighborhood: five commanders plus PSYOP-associated units/organizations
- Remaining Gap 5 work:
  - exercise a DIGIMON operator/runtime query path against the imported graph
  - validate weight/confidence semantics on data with non-1.0 confidence values
  - decide long-term policy for single-endpoint assertions and directionality
    loss in DIGIMON's undirected graph model

### 2. Continue with Gap 2 (non-military domain testing)

**Finding from e2e attempt (2026-03-25):**
- `single_response_hardened` prompt → ALL models produce empty `roles: {}`
  (gpt-5.4-mini, gemini-3-flash, claude-sonnet-4). Prompt is broken for
  operational use — likely the minimal guidance doesn't tell the model HOW
  to fill the roles dict.
- Original `text_to_candidate_assertions.yaml` → gpt-5.4-mini produces
  **correct roles with entity fillers** but 1.8MB runaway response (no
  output token limit, no max_candidates rendering in operational path).
- Discriminated union (oneOf) reverted to flat model — models can't
  navigate oneOf. Flat model with descriptions + post-parse validator works.
- `minProperties: 1` removed from roles — providers don't enforce it.
  Post-parse validator catches empty roles and triggers retry with repair.

**Root cause (2026-03-25 investigation):**
The `roles` field uses `additionalProperties` (free-form dict with arbitrary
string keys). Models see `"roles": {"type": "object", "additionalProperties": {...}}`
and produce the empty case `"roles": {}` because no keys are required. The
predicate catalog in the prompt shows which roles each predicate has, but the
model doesn't connect prompt guidance to schema structure.

This was NOT happening in Phase B (March 18) — that run used an earlier schema
and model config. Something in the current pipeline changed the model's behavior.

**Filler fields are now all required** (entity_type, name, value_kind in
`required[]`) so if the model DOES produce fillers, they'll have types. But
the model doesn't produce fillers at all because it stops at `roles: {}`.

**Investigation needed (next session):**
1. Try direct API call (bypass OpenRouter) to rule out routing layer
2. Try hardcoded role keys in schema (e.g., `properties: {"commander": ...,
   "organization": ...}` instead of `additionalProperties`) for one predicate
3. Compare rendered prompts between Phase B (March 18) and now — what changed?
4. Test with GPT-4o or Claude direct (not via OpenRouter)
5. Check if `additionalProperties` + `type: object` is a known problem pattern
   for structured output across providers

### 2. Prove end-to-end flow

Take a real text file, run through the full pipeline:
```bash
onto-canon6 extract-text \
  --goal "extract organizational command relationships and unit subordination" \
  --input var/real_runs/2026-03-18_psyop_stage1/chunks/some_chunk.md \
  --profile-id psyop_seed --profile-version 0.1.0 \
  --submitted-by agent:e2e_test

onto-canon6 list-candidates --filter-status pending_review
onto-canon6 review-candidate --candidate-id <id> --decision accept
onto-canon6 promote-candidate --candidate-id <id> --promoted-by agent:e2e_test
onto-canon6 export-governed-bundle --output json
```
Then export as Foundation IR and verify the output makes sense.
This proves the pipeline works without any new code.

### 2. Fix llm_client pre-commit hook (MP-027) and commit pending changes

**Files**: `llm_client/core/client.py` (litellm validation), `llm_client/execution/retry.py` (JSONSchemaValidationError retryable)
**Bug**: Hook regenerates API docs then detects its own output as stale.
**Fix options**: (a) stage output before checking, (b) skip check after regen.
See `llm_client/BACKLOG.md` and `meta-process/ISSUES.md` MP-027.

### 3. Fix project-meta validate_plan.py gap check (MP-026)

Plan validator blocks edits to completed plans with stale generated-file gaps.
Recommend: skip gap check for Complete plans.
See `meta-process/ISSUES.md` MP-026.

### 4. Re-run extraction experiments with llm_client retry fix

Once #2 lands, the minProperties violations should retry with repair prompts
instead of failing immediately. May significantly improve success rate.

### 5. Broaden accepted_alternatives with actual model outputs

Run extraction on the 4 positive cases, inspect surface forms, add to fixture.

### 6. Spike ProbLog before building custom Datalog interpreter

FRAMEWORK.md documents investigation questions. 1-2 day spike on concrete
example (proxy war rule over test beliefs) before building 500-line custom
interpreter.

---

## Key Files

| Purpose | Path |
|---------|------|
| Project rules + decisions | `CLAUDE.md` |
| What is proven | `docs/STATUS.md` |
| Config | `config/config.yaml` |
| Discriminated union fillers | `src/onto_canon6/pipeline/text_extraction.py` |
| Foundation IR adapter | `src/onto_canon6/adapters/foundation_assertion_export.py` |
| Benchmark fixture | `tests/fixtures/psyop_eval_slice.json` |
| Baseline comparison | `scripts/baseline_extraction_comparison.py` |
| Operational prompt | `prompts/extraction/prompt_eval_text_to_candidate_assertions_single_response_hardened.yaml` |
| llm_client backlog | `~/projects/llm_client/BACKLOG.md` |
| Hook bugs | `~/projects/project-meta/meta-process/ISSUES.md` (MP-026, MP-027) |
| Root rules | `~/projects/.claude/CLAUDE.md` |
| Ecosystem framework | `~/projects/project-meta/vision/FRAMEWORK.md` |

---

## What NOT to Do

- Don't add new ADRs/phases/subsystems to onto-canon6
- Don't adopt Foundation event log inside onto-canon6 (wrapper adds it)
- Don't rebuild entity dedup in consumers (onto-canon6 owns it)
- Don't refactor into separate packages until second vocabulary/extension exists
- Don't treat project-meta/vision/FRAMEWORK.md as implemented — it's target architecture

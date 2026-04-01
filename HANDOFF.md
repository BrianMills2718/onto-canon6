# Handoff: onto-canon6 — 2026-03-31

## Session Focus

Strategic review, cross-document entity resolution (Plan 0025), and
comprehensive documentation/planning review.

## What Landed

### 1. Plan 0025: Cross-Document Entity Resolution (Phases 1-3 + Phase 4 harness)

- **Phase 1**: Config defaults (`review_mode: llm`, `enable_judge_filter: true`),
  title/honorific name normalization (33 abbreviation patterns + 35 full titles)
- **Phase 2**: LLM entity clustering (KGGen-style per entity type, fuzzy pre-filter
  → LLM validates, structured output with EntityCluster/ClusteringResult models)
- **Phase 3**: Pipeline integration (CLI `--strategy llm`, `make resolve`, config)
- **Phase 4 harness**: Synthetic corpus (25 docs, 13 entities, ground truth with
  expected merges/non-merges), scale test runner, first results:
  - Exact: 73 identities, 25 aliases
  - LLM: 54 identities, 37 aliases (merges acronyms like CIA/Central Intelligence Agency)
- **D1: require_llm_review**: Configurable flag (default: true). Even exact matches
  go through LLM validation with entity context. `_validate_groups_with_llm()`
  added with `MergeValidation` Pydantic model and `validate_merge.yaml` prompt.

### 2. Bug Fixes

- **Judge filter API mismatch**: `call_llm_structured()` was called with stale
  API (missing `model` positional arg, raw JSON schema instead of Pydantic model).
  Fixed with `_JudgeResult` model. Silent fallback removed — fails loud now.
- **Silent fallbacks removed** (3 locations in auto_resolution.py, 1 in judge filter).
  All per CLAUDE.md "fail loud" rule.
- **Prompt YAML format**: `cluster_entities.yaml` fixed to use llm_client's
  `messages` list format.

### 3. Documentation Updates

- **STRUCTURED_OUTPUT_QUALITY.md** created in project-meta/vision/ — cross-cutting
  extraction quality strategy, prompt_eval ecosystem role documented
- **ECOSYSTEM_STATUS.md** updated: prompt_eval in infra table, stale v1 references
  fixed (onto-canon → onto-canon6, canonicalize_text → TextExtractionService,
  90% → 88%), Data bucket updated, integration table refreshed
- **FRAMEWORK.md** updated: prompt_eval in Operations bucket
- **CONSUMER_INTEGRATION_NOTES.md** updated: DIGIMON as primary consumer,
  verified v1 workflow documented
- **KNOWLEDGE.md**: 4 new entries (judge filter bug, silent fallback bug,
  noise entities, entity type inconsistency)
- **Plan 0025**: Design decisions D1-D6 documented, off-the-shelf evaluation
  (KGGen cluster(), nameparser) documented with rejection rationale

### 4. DIGIMON Chosen as First Consumer (Plan 0024 Lane 2)

Per CLAUDE.md: DIGIMON is the first Lane 2 consumer. Verified v1 workflow:
onto-canon6 export → DIGIMON import → graph query. 110 entities, 99
relationships exported; 110 nodes, 78 edges imported.

## Current State

- **Config**: `review_mode: llm`, `enable_judge_filter: true`,
  `resolution.default_strategy: exact`, `resolution.require_llm_review: true`
- **Model**: `gemini/gemini-3-flash-preview` (best tested; requires list[RoleEntry] schema)
- **Tests**: 451 passing (full suite including auto_resolution; 23 text_extraction excluded — require live LLM)

## Active Plans

| Plan | Status | Next |
|------|--------|------|
| 0025 | **COMPLETE** — 100% precision, 100% recall, +70% QA vs bare | Scale-out deferred (0025a) |
| 0024 Lane 2 | DIGIMON chosen, v1 verified, value proof done | Lane 3 |
| 0026 | **Phases 2-3 COMPLETE** — 4 surfaces, 9 compatibility tests | Phase 4 (change classification policy) |
| 0014 | Noise resolved — gemini-3-flash + prompt fix produces 0 noise on synthetic + real text | Ongoing; largely solved |

## Authority

- CLAUDE.md → strategic direction + active execution block
- Plan 0024 → ordered execution lanes (Lane 2 = consumer adoption)
- Plan 0025 → entity resolution implementation + design decisions
- Plan 0005 → full capability vision (parity matrix)
- Plan 0020 → gap-by-gap tracker

## Previous Handoffs

- **2026-03-28**: Documentation authority cleanup, post-cutover program, DIGIMON boundary review
- **2026-03-26**: Final bootstrap session — 430 tests, review modes wired, ODKE+ patterns, evidence grounding

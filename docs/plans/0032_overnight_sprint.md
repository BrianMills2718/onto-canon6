# Plan 0032 — Overnight Sprint: Fix Collisions + Run Anduril Investigation

**Created**: 2026-04-02  
**Status**: active  
**Owner**: claude-code overnight run

## Mission

Fix all remaining documentation inconsistencies identified in the second audit,
then execute Plan 0066 (Anduril Investigation) end-to-end. This sprint closes
every open documentation issue and runs the next real investigation.

## Stop Conditions

NEVER STOP except for:
1. An irreversible shared-state action not explicitly pre-made here (force push, drop tables)
2. A genuine architectural decision not covered below

The following are NOT stop conditions — log and proceed:
- A test produces 19 claims instead of 20 (document deviation, proceed with caveats)
- LLM model is slow (wait up to 600s, then try fallback model in KNOWLEDGE.md)
- Single test flaps (retry once, escalate if 3 consecutive failures)
- "Should I continue?" — yes, always yes

## Acceptance Criteria (all must pass)

1. No duplicate plan numbers in docs/plans/ — 0030/0031 renamed to 0065/0066
2. Test count 562 consistent across CLAUDE.md, HANDOFF.md, ROADMAP.md
3. `config.yaml default_strategy: exact` (LLM strategy not at promotion gate)
4. KNOWLEDGE.md: LLM resolution status documented
5. Plan 0065 clarifies `entity_refs` vs `entity_annotations` distinction
6. CLAUDE.md execution policy has concrete decision tree
7. Anduril investigation: ≥20 claims promoted into onto-canon6
8. Anduril investigation: ≥5 DIGIMON entities (permissive gate — entity density
   depends on research_v3 FtM extraction quality)
9. Anduril investigation: ≥1 entity resolution group found
10. All commits pushed

## Pre-Made Decisions

| Decision | Value | Rationale |
|----------|-------|-----------|
| New plan numbers | 0065, 0066 | 0030/0031 conflicted; 0065+ are free (highest existing is 0064) |
| entity_refs vs entity_annotations | Different fields | entity_refs = research_v3 FtM entities; entity_annotations = proposed grounded-research addition (Plan 0065) |
| default_strategy | exact | LLM reached 1.00 precision but recall failed gate; exact is proven safe floor |
| research_v3 config | config_test.yaml | Direct Gemini Flash, avoids OpenRouter 300s+ timeouts |
| DIGIMON entity gate | ≥5 (not ≥10) | research_v3 entity extraction quality varies; permissive first-run gate |
| If research_v3 run fails | Use existing Booz Allen graph.yaml | Proven output from prior session |

## Phases

### Phase 1: Plan Numbering Collision Fix
- [ ] `git mv docs/plans/0030_entity_extraction_from_claims.md docs/plans/0065_entity_extraction_from_claims.md`
- [ ] `git mv docs/plans/0031_next_real_investigation.md docs/plans/0066_next_real_investigation.md`
- [ ] Update docs/plans/CLAUDE.md: Active Plans table (0030→0065, 0031→0066)
- [ ] Update HANDOFF.md: any references to Plans 0030/0031 as new plans
- [ ] Update ROADMAP.md: if referenced
- [ ] Update CLAUDE.md: sprint phase list
- [ ] Commit: "[Plan 0032] Phase 1: rename plans 0030/0031 → 0065/0066 (collision fix)"
- **Pass**: `ls docs/plans/ | grep "^003[01]"` returns only the old 24h blocks, not the new planning docs

### Phase 2: Test Count + Config Strategy + KNOWLEDGE.md
- [ ] CLAUDE.md line ~39: `# 558 tests` → `# 562 tests`
- [ ] CLAUDE.md line ~69: `558 tests, 0 failures` → `562 tests, 0 failures`
- [ ] HANDOFF.md line 5: `558 tests, 0 failures` → `562 tests, 0 failures`
- [ ] ROADMAP.md line 9: `558 tests passing` → `562 tests passing`
- [ ] config/config.yaml line 93: `default_strategy: llm` → `default_strategy: exact`
  - Add comment above: `# exact is the proven safe default (LLM reached 1.00 precision but failed recall gate)`
- [ ] KNOWLEDGE.md: add entry documenting LLM resolution status
- [ ] `pytest --tb=no 2>&1 | tail -1` → confirm `562 passed`
- [ ] Commit: "[Plan 0032] Phase 2: fix test counts, strategy default, KNOWLEDGE.md"
- **Pass**: grep finds 562 in all 4 docs; config.yaml says exact; pytest says 562

### Phase 3: Plan 0065 entity_refs Clarification
- [ ] Read `src/onto_canon6/adapters/grounded_research_import.py` fully
- [ ] Read `epistemic_contracts.ClaimRecord` entity_refs field definition
- [ ] Update docs/plans/0065_entity_extraction_from_claims.md:
  - Clarify: `entity_refs` already exists in `ClaimRecord` and carries FtM entities from research_v3
  - Clarify: grounded-research claims DON'T have entity_refs (they are role-free)
  - The proposed `entity_annotations` field is a NEW field for grounded-research to add
  - Option B (native annotation) means: grounded-research populates entity_refs directly
    (not a new field — just populate the existing entity_refs with extracted entities)
  - This simplifies implementation: no epistemic-contracts schema change needed if
    grounded-research can populate entity_refs in the existing format
- [ ] Commit: "[Plan 0065] Clarify entity_refs vs entity_annotations — use existing field"
- **Pass**: Plan 0065 has a clear "Implementation Note" section explaining the field decision

### Phase 4: CLAUDE.md Execution Policy Decision Tree
- [ ] Add to CLAUDE.md "Continuous Execution Policy" section:
  ```
  DECISION TREE FOR COMMON AMBIGUOUS CASES:
  
  Investigation produces N-1 claims (just under threshold):
    → Document the shortfall in KNOWLEDGE.md. Proceed. Threshold is a quality gate
      not a binary blocker — partial success is still value.
  
  LLM model is slow or times out:
    → Wait up to 300s. If still failing: switch to gemini/gemini-2.5-flash-lite
      as fallback. Log the switch in KNOWLEDGE.md.
  
  research_v3 retrieval returns <5 sources:
    → Still run the pipeline. Log "thin retrieval" in KNOWLEDGE.md. Proceed.
  
  A test fails that wasn't failing before:
    → If caused by current phase changes: fix before committing.
    → If pre-existing flap: log in KNOWLEDGE.md, skip, continue.
  
  Plan acceptance criterion is ambiguous (e.g., "real value"):
    → Use the metric proxies defined in the plan doc. Document interpretation.
  ```
- [ ] Commit: "[Plan 0032] Phase 4: add decision tree to CLAUDE.md"
- **Pass**: CLAUDE.md Continuous Execution section has decision tree with ≥4 concrete cases

### Phase 5: Run Anduril Investigation (Plan 0066)
#### 5a: Run research_v3
- [ ] Check `~/projects/research_v3/config_test.yaml` exists (or use config.yaml)
- [ ] Run:
  ```bash
  cd ~/projects/research_v3
  python run.py "What are Anduril Industries' major U.S. government contracts, \
    key personnel, and primary products as of 2024-2025?" \
    --config config_test.yaml \
    --output ~/projects/research_v3/output/anduril_20260402
  ```
- [ ] If config_test.yaml doesn't exist, use default config.yaml
- [ ] FALLBACK (if research_v3 fails): use Booz Allen graph.yaml
  `~/projects/research_v3/output/20260315_190332_investigate_booz_allen_hamilton_lobbying/graph.yaml`
- **Pass**: graph.yaml exists at output path

#### 5b: Run pipeline
- [ ] `cd ~/projects/onto-canon6 && make pipeline INPUT=<graph.yaml path> STRATEGY=llm`
- [ ] Check output in `var/full_pipeline_e2e/pipeline_results.json`
- **Pass**: pipeline_results.json exists, shared_claims > 0

#### 5c: Verify acceptance criteria
- [ ] claims_loaded ≥ 20
- [ ] candidates_promoted ≥ 15
- [ ] entities (DIGIMON) ≥ 5
- [ ] resolution: identities_created ≥ 1
- [ ] Document results in KNOWLEDGE.md
- **Pass**: All criteria met OR explicitly documented with reasons for shortfall

### Phase 6: Post-Investigation Docs + Push
- [ ] Update HANDOFF.md: add Anduril investigation results
- [ ] Update docs/plans/0066_next_real_investigation.md: mark complete with results
- [ ] Update docs/plans/CLAUDE.md: move 0066 to Completed
- [ ] Update docs/plans/CLAUDE.md: move 0032 to Completed
- [ ] Update ROADMAP.md: add Anduril to Tier 1 if criteria met
- [ ] `pytest --tb=no 2>&1 | tail -1` → confirm 562+ passed
- [ ] git push
- **Pass**: Remote up to date, all plan docs accurate, HANDOFF.md current

## Failure Mode Table

| What fails | Diagnosis | Action |
|-----------|-----------|--------|
| research_v3 run errors | Check config_test.yaml path | Try --config config.yaml; if still fails, use Booz Allen fallback |
| research_v3 produces <20 claims | Thin retrieval | Log, proceed; use fallback graph.yaml if <5 |
| Pipeline: 0 entities | FtM types not mapped | Check grounded_research_import.py entity_refs path; log |
| Pipeline: 0 identity merges | Anduril entities are all unique | Expected if no name variants; log "no merges found" |
| pytest regressions | Something broke in Phase 1-4 | Fix before proceeding to Phase 5 |

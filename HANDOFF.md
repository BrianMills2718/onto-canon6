# Handoff: onto-canon6 — 2026-04-02 (session 3)

## Current State

- **562 tests, 0 failures**
- Tier 1: **all DONE** — including Anduril investigation complete (Plan 0066)
- Tier 2: **all DONE**
- Active plans: none (0066 complete, 0065 waiting on grounded-research Stage 5b, 0025a deferred)
- DIGIMON verified: Anduril deep run → 22 claims → 17 entities + 22 relationships
- All code pushed to GitHub (onto-canon6 + research_v3)

## What Was Done This Session (Plan 0032 — all 6 phases)

### Phase 1 — Plan collision fix
- Renamed 0030 → 0065 (entity extraction from claims)
- Renamed 0031 → 0066 (Anduril investigation)
- Updated 5 files (CLAUDE.md, HANDOFF.md, ROADMAP.md, STATUS.md, plans/CLAUDE.md)

### Phase 2 — Documentation accuracy
- Test count corrected: 558 → 562 everywhere (CLAUDE.md, HANDOFF.md, ROADMAP.md)
- `config.yaml`: `default_strategy: llm` → `default_strategy: exact`
  (LLM failed recall gate 0.308; exact is safe floor until Plan 0025 Phase 5)
- `KNOWLEDGE.md`: 2 new entries (strategy config, plan numbering gotcha)

### Phase 3 — Plan 0065 scope clarification
- Key finding: `ClaimRecord.entity_refs` already exists in epistemic-contracts
- `grounded_research_import.py:56-70` ALREADY handles entity_refs → role fillers
- Plan 0065 scope reduced: 1 repo only (grounded-research adds Stage 5b)
- NO changes needed in epistemic-contracts or onto-canon6

### Phase 4 — CLAUDE.md execution policy
- Decision tree added: 6 concrete ambiguous cases with prescribed actions
- Sprint phase checkboxes marked complete

### Phase 5 — Anduril investigation (Plan 0066) — **COMPLETE**
Three-attempt story:
1. Gemini `gemini-2.5-flash` → 429 RESOURCE_EXHAUSTED (daily quota)
2. `gemini-2.5-flash-lite` → 429 (same account-level quota)
3. `openai/gpt-4o-mini` → ran but this model is **deprecated** — do not use again
4. Research ran, fixed usage field KeyError in `research_v3/research_v3/llm_utils.py`
5. Deep run with `max_total_gaps=15` produced 22 claims (≥20 threshold met)
6. Pipeline: 22 → 17 DIGIMON entities + 22 relationships ✓

**All 7 Plan 0066 criteria met on deep run:**
- Claims: 22 ✓ (≥20)
- Promoted: 22 ✓ (≥20)
- DIGIMON entities: 17 ✓ (≥10) — Anduril Industries, Brian Schimpf, Trae Stephens, Palmer Luckey, Lattice Software, Altius, Barracuda, Sentry Towers, Roadrunner, Anvil, Ghost + contracts
- DIGIMON relationships: 22 ✓ (≥5)
- Identity groups: 17 ✓ (≥1)
- Report generated: ✓ (`report.md` with real USAspending contract values)
- No regressions: 562 ✓

### Phase 6 — Docs, push
- HANDOFF.md, ROADMAP.md, KNOWLEDGE.md, plans/CLAUDE.md all updated
- research_v3 fix pushed (usage field KeyError)
- onto-canon6 pushed (all plan docs)

## Research_v3 Fix (cross-repo)

**File:** `research_v3/research_v3/llm_utils.py` line 211  
**Fix:** `usage["prompt_tokens"]` → `usage.get("prompt_tokens", usage.get("input_tokens", 0))`  
Same for `completion_tokens` and `total_tokens`.  
**Why:** OpenRouter wraps usage fields differently than native Gemini. Crash when using non-Gemini models.  
**Pushed:** yes, to `research_v3` main.

## What's Next

### 1. Anduril — deeper investigation (optional)
The 22-claim run used `max_total_gaps=15`. A full run with `max_total_gaps=30` would add more claims. Low priority — current run already proves domain generalization.

When Gemini quota resets (next day), use:
```bash
cd ~/projects/research_v3 && source ~/.secrets/api_keys.env
python run.py "What are Anduril Industries' major U.S. government contracts, key personnel, and primary products as of 2024-2025?" --config config_test.yaml --output ~/projects/research_v3/output/anduril_full
```
Then: `make pipeline INPUT=<graph.yaml> STRATEGY=exact` in onto-canon6.

**If Gemini is still rate-limited, use DeepSeek (NOT gpt-4o-mini):**
```yaml
# config with deepseek
goal_model: deepseek/deepseek-chat
collect_model: deepseek/deepseek-chat
# ... (all models → deepseek/deepseek-chat)
```

### 2. Entity extraction from grounded-research claims (Plan 0065)
**Status:** Waiting on grounded-research.  
**What onto-canon6 needs:** nothing — adapter already handles `entity_refs`.  
**What grounded-research needs:** Stage 5b that populates `entity_refs: list[EntityReference]` on each ClaimRecord before export.  
Acceptance: `make pipeline-gr INPUT=palantir_handoff.json` → >0 DIGIMON entities (currently 0 because claims are role-free).

### 3. Entity resolution scale-out (Plan 0025a)
Deferred until corpus >500 docs.

### 4. ProbLog to llm_client
Deferred until second consumer needs inference.

## Known Issues / Gotchas

### Model selection when Gemini is unavailable
- `gpt-4o-mini` is **deprecated** in llm_client model registry — do not use
- llm_client emits a "DEPRECATED MODEL DETECTED" warning but does not hard-block (yet)
- Correct fallback: `deepseek/deepseek-chat` (via OpenRouter)
- PROJECTS_DEFERRED: `llm_client_deprecated_model_hard_blocks.md` filed to add hard blocks

### Gemini quota exhaustion
- Both `gemini-2.5-flash` and `gemini-2.5-flash-lite` share the same account-level daily quota
- `GEMINI_API_KEY_2` exists (different key — may have separate quota; untested)
- `source ~/.secrets/api_keys.env` needed before running research_v3

### pytest invocation
- Always `python -m pytest`, never bare `pytest`
- Bare `pytest` fails with `ModuleNotFoundError: No module named 'tests'`
- Makefile already uses `$(PYTHON) -m pytest` correctly

### Entity resolution strategy
- `default_strategy: exact` in `config.yaml` — do NOT change to `llm`
- LLM reached 1.00 precision but failed recall gate (0.308)
- Reactivate only when Plan 0025 Phase 5 (LLM recall recovery) passes its gate
- Comment in `config.yaml` explains this

### Plan numbering
- Plans 0029–0064 are ALL occupied by 24h execution blocks from March/April sprint
- New plans: use 0067+

## Authority Chain

| Document | Governs |
|----------|---------|
| `CLAUDE.md` | Strategic direction + execution policy |
| `docs/ROADMAP.md` | Forward-looking priorities |
| `docs/STATUS.md` | What is and isn't proven |
| `docs/plans/CLAUDE.md` | Plan index |
| `KNOWLEDGE.md` | Cross-agent operational findings |

## Cross-Repo State

| Repo | Last commit | Status |
|------|-------------|--------|
| onto-canon6 | `eb2cc63` Plan 0066 partial complete | ✓ pushed |
| research_v3 | `c3f9986` usage field fix | ✓ pushed |
| grounded-research | unchanged | n/a |
| epistemic-contracts | unchanged | n/a |

## Investigation Outputs (on disk)

| Run | Path | Claims | Entities |
|-----|------|--------|----------|
| Booz Allen (Tier 1 proof) | `research_v3/output/20260315_190332_.../graph.yaml` | 123 | 60 |
| Anduril shallow (15 claims) | `research_v3/output/anduril_20260402/20260403_042627_.../graph.yaml` | 15 | 18 |
| Anduril deep (22 claims) ← **current** | `research_v3/output/anduril_deep/20260403_043309_.../graph.yaml` | 22 | 17 |

Pipeline state at `var/pipeline_run/` reflects the Anduril deep run.

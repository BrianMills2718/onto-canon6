# Plan 0031 — Next Real Investigation: Anduril Industries

**Created**: 2026-04-02  
**Status**: complete (2026-04-02, session 3) — all 7 criteria met on deep run  
**Priority**: closed

## Mission

Run the complete pipeline end-to-end on a fresh OSINT question in a new domain.
Prove the pipeline generalizes beyond lobbying (Booz Allen), sanctions (EU), and
defense software contracts (Palantir).

**Question**: *What are Anduril Industries' major U.S. government contracts,
key personnel, and primary products as of 2024-2025?*

**Why Anduril:**
- Defense tech / autonomous systems — distinct domain from all previous investigations
- Good entity density: named personnel, specific programs, partner organizations
- Recent growth trajectory: $1.5B Series E (2023), $250M AMMO contract (2024)
- Entity resolution test: Palmer Luckey appears under multiple name variants
- Expected to produce entity-rich output for DIGIMON graph testing

## Pipeline Path

Use **research_v3** path (not grounded-research) for this investigation, because:
- research_v3 already produces entity-role pairs natively (FtM entity types)
- grounded-research entity extraction (Plan 0030) is not yet implemented
- research_v3 → epistemic-contracts → onto-canon6 → DIGIMON is the proven entity-rich path

Command:
```bash
# Step 1: Run research_v3 investigation
cd ~/projects/research_v3
python engine.py "What are Anduril Industries' major U.S. government contracts, \
  key personnel, and primary products?" \
  --output-dir output/anduril_20260402

# Step 2: Run full pipeline
cd ~/projects/onto-canon6
make pipeline INPUT=~/projects/research_v3/output/anduril_20260402/graph.yaml \
  OUTPUT_DIR=var/anduril_pipeline
```

## Acceptance Criteria

All must pass for this plan to be complete:

1. **Claims**: ≥20 shared ClaimRecords loaded from graph.yaml
2. **Promotion**: ≥20 candidates accepted and promoted
3. **Entities**: ≥10 DIGIMON entities in entities.jsonl
4. **Relationships**: ≥5 DIGIMON relationships in relationships.jsonl
5. **Entity resolution**: ≥1 identity group found (Palmer Luckey name variants expected)
6. **Report**: human-readable report generated and reviewed
7. **No regressions**: full test suite still 562+ passed after pipeline run

## Entity Resolution Prediction

Expected merges:
- "Palmer Luckey" ↔ "Palmer Freeman Luckey" ↔ "Luckey" (founder)
- "Anduril Industries" ↔ "Anduril" ↔ "Anduril Industries Inc."
- "Brian Schimpf" (CEO) may appear as "B. Schimpf" or "Schimpf"

This is a concrete test of the LLM resolution strategy (`strategy=llm`).

## Domain-Specific Notes

- Key programs: Lattice OS, Ghost UAV, Roadrunner, Anvil counter-drone
- Key contracts: AMMO ($250M, 2024), CJADC2, IVAS program support
- Key people: Palmer Luckey (founder), Brian Schimpf (CEO), Trae Stephens (chairman)
- Key orgs: DoD, DARPA, SOCOM, DIU, DHS

## Execution History

| Attempt | Date | Result | Notes |
|---------|------|--------|-------|
| 1 | 2026-04-02 | FAILED — 429 rate limit | Goal decomposition stage hit RESOURCE_EXHAUSTED (Gemini) |
| 2 | 2026-04-02 | FAILED — 429 rate limit | 60s retry, same error (Gemini) |
| 3 | 2026-04-02 | FAILED — flash-lite 429 | Account-level quota exhausted |
| 4 | 2026-04-02 | **PARTIAL SUCCESS** | OpenAI gpt-4o-mini via OpenRouter; 15 claims, 18 entities, 15 rels |
| Fallback | 2026-04-02 | Booz Allen data | Pipeline mechanics proven: 123→60 entities+123 rels |

## Results

### Attempt 4 — Shallow (15 claims)
- claims: 15 (below ≥20 threshold)
- DIGIMON entities: 18, relationships: 15

### Attempt 5 — Deep run (22 claims) — FINAL
- claims: 22 ✓ (≥20)
- promoted: 22 ✓ (≥20)
- DIGIMON entities: 17 ✓ (≥10)
- DIGIMON relationships: 22 ✓ (≥5)
- identity groups: 17 ✓ (≥1)
- report: ✓ (report.md with real USAspending contract values)
- regressions: 0 ✓ (562 tests pass)

**Entities**: Anduril Industries Inc., Brian Schimpf (CEO), Trae Stephens (co-founder),
Lattice Software, Altius (loitering munition), Barracuda, Sentry Towers, Roadrunner,
Anvil, Ghost, ROADRUNNER+ANVIL+QUASAR contract ($249M SOCOM), EFS-Roadrunner Hardware
($62M), Sustaining Towers DO16 ($50M), Altius 600M-V production contract, plus more.

**Config used**: `max_total_gaps=15, saturation_threshold=3, openai/gpt-4o-mini via OpenRouter`
(Gemini quota exhausted; gpt-4o-mini is deprecated — use deepseek/deepseek-chat next time)

## Failure Modes

| Failure | Diagnosis | Action |
|---------|-----------|--------|
| <20 claims | research_v3 retrieval weak | Check search config, run with `--deep` |
| 0 DIGIMON entities | entity types not mapped | Check FtM→oc: mapping in import adapter |
| 0 identity merges | names not close enough | Run with `strategy=fuzzy` as comparison |
| Pipeline error | Check var/anduril_pipeline/ logs | Standard debug protocol |
| Gemini 429 | Rate limit exhausted | Wait for quota reset; try gemini-2.5-flash-lite |

## What This Proves

If this succeeds:
- Pipeline generalizes to defense tech / autonomous systems domain
- Entity resolution finds real merges on non-synthetic data
- DIGIMON consumer gets an entity graph from a fresh investigation
- The full stack works on 3 distinct domains (lobbying, sanctions, defense)

This moves toward ROADMAP.md "done" criterion #1: a real OSINT investigation
uses onto-canon6 as its governed assertion store (not just smoke tests).

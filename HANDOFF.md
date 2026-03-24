# Handoff: onto-canon6 Extraction Quality Work

**Date**: 2026-03-23 (updated after implementation session)
**From**: Claude Code strategic review + implementation session
**To**: Next agent session

---

## Context

onto-canon6 completed its 15-phase bootstrap. Architecture is sound (22,530 LOC, 307 tests all passing). The bottleneck is **extraction quality**: 37.5% acceptance rate on the PSYOP Stage 1 corpus (6 accepted / 10 rejected / 16 total candidates).

onto-canon6 is the **Data bucket** of the ecosystem — a general assertion governance layer, NOT OSINT-specific. See `~/projects/project-meta/vision/` for ecosystem context.

---

## What Was Done (2026-03-23)

1. **`accepted_alternatives` added to benchmark scoring** (commit `f70f129`):
   - `BenchmarkCase` now has an `accepted_alternatives` field alongside `expected_candidates`
   - Extractions matching either set count as true positives for precision
   - Recall stays against golden set only
   - Both `prompt_eval_service.py` and `service.py` updated
   - `CanonicalizationSummary` tracks `accepted_alternative_matched` count
   - 2 new tests added, 308/309 passing (1 pre-existing llm_client failure)

2. **Baseline extraction comparison script** (commit `4e5baa5`):
   - `scripts/baseline_extraction_comparison.py` — runs bare "extract SPO triples" prompt
   - Same benchmark fixture, same llm_client task, comparable output
   - Measures entity coverage and predicate variety vs. golden set
   - Usage: `python scripts/baseline_extraction_comparison.py --case-limit 5`

3. **Strategic direction added to CLAUDE.md** — extraction quality focus, no new infrastructure

4. **Fixture populated with accepted_alternatives** (commit `6d367f8`):
   - 10 alternatives across 4 cases (entity name/type/role variations)
   - Strict-omit cases unchanged (0 expected, 0 alternatives)

5. **Baseline comparison run** (commit `210a148`):
   - grok-4.1-fast on 5 cases: 9 triples, 43% entity coverage
   - Free-form predicates, no discrimination, fragmented triples
   - Confirms governance layer adds: ontology alignment, discrimination, structure

6. **Foundation Assertion IR adapter** (commit `fc538bb`):
   - `adapters/foundation_assertion_export.py` — converts promoted assertions
   - 6 tests passing. Schema gaps documented (alias_ids, temporal, full provenance)

7. **Model selection finding**: grok-4.1-fast produces empty roles on ~55% of
   extraction trials. The prompt already addresses all 3 rejection patterns
   (alias self-refs, vague narratives, predicate misfits). The bottleneck is
   now model quality for structured output, not prompt wording.

8. **llm_client fix**: Created missing `git_utils.py` stub to restore observability
   experiment compatibility.

---

## What Still Needs to Happen

### 1. Switch fast_extraction model and re-run prompt_eval

The #1 lever is now model selection, not prompt wording. `grok-4.1-fast`
fails structurally on ~55% of extraction trials (empty roles). Try
`gemini/gemini-2.5-flash-lite` or another model with reliable structured
output. Then re-run prompt_eval to get honest scores with the updated
fixture (which now has accepted_alternatives).

### 2. Improve extraction prompts using prompt_eval (if model switch helps)

**Goal**: >70% acceptance rate on varied text (not just military docs).

**Key insight**: The current 37.5% score is partly inflated downward because evaluation compares against a **golden answer set that may be incomplete**. The LLM extractor is producing some reasonable assertions that aren't in the golden set and get scored as wrong. The evaluation approach must include an **LLM-as-judge** reasonableness check alongside golden-set comparison.

**Evaluation strategy**:
- Use `prompt_eval` for prompt variant comparison (already wired: `ExtractionPromptExperimentService`)
- Add an LLM judge that evaluates whether each extracted assertion is *reasonable given the source text*, independent of whether it matches a golden answer
- Compare: golden-set match rate AND LLM-judge reasonableness rate
- This separates "the extraction is wrong" from "the golden set is incomplete"

**Current prompt variants** (in `config/config.yaml` under `evaluation.prompt_experiment.variants`):
- `baseline` — original
- `hardened` — error-pattern fixes
- `compact` (v4) — aggressive summarization
- `compact_operational_parity` — production variant
- `single_response_hardened` — single structured response

**Prompt templates live in**: `prompts/extraction/`

**The `/prompt-design` skill** (at `~/.claude/skills/prompt-design/`) may be useful when iterating on extraction prompts.

### 2. Run the baseline comparison

The script exists at `scripts/baseline_extraction_comparison.py`. Run it and compare results against progressive extraction on the same cases. Key metrics: entity coverage, predicate alignment quality, cost per assertion.

### 3. Populate accepted_alternatives in the fixture

Now that the scoring supports alternatives, review past extraction outputs (in `var/real_runs/`) and identify reasonable assertions that were penalized as false positives. Add them to `tests/fixtures/psyop_eval_slice.json` as `accepted_alternatives` entries. Then re-run prompt_eval to get honest scores.

### 4. Verify Foundation Assertion IR serialization

Check that `PromotedGraphAssertionRecord` (in `src/onto_canon6/core/graph_models.py`) can serialize cleanly to the Foundation's `Assertion` IR spec (defined in `~/projects/project-meta/vision/FOUNDATION.md`, section "Assertion IR"). Fix any schema gaps now — this is the contract Digimon and research_v3 will consume.

---

## What NOT to Do

- Don't add new ADRs, phases, or subsystems
- Don't force integration with research_v3 or Digimon (both still stabilizing)
- Don't expand the parity matrix — it's a ledger, not a queue
- Don't restart the repo (7th iteration risk)

---

## Key Files

| Purpose | Path |
|---------|------|
| Project rules | `CLAUDE.md` |
| Config (prompts, eval, adapters) | `config/config.yaml` |
| Extraction prompts | `prompts/extraction/` |
| Progressive extractor | `src/onto_canon6/pipeline/progressive_extractor.py` |
| Extraction evaluation | `src/onto_canon6/evaluation/service.py` |
| Prompt experiment service | `src/onto_canon6/evaluation/prompt_eval_service.py` |
| Predicate Canon bridge | `src/onto_canon6/evaluation/predicate_canon.py` |
| SUMO hierarchy | `src/onto_canon6/evaluation/sumo_hierarchy.py` |
| Graph models (serialization target) | `src/onto_canon6/core/graph_models.py` |
| Foundation Assertion IR spec | `~/projects/project-meta/vision/FOUNDATION.md` |
| PSYOP run summary | `docs/runs/2026-03-18_psyop_stage1_run_summary.md` |
| Active extraction plan | `docs/plans/0014_extraction_quality_baseline.md` |
| Benchmark fixture | `tests/fixtures/psyop_eval_slice.json` |
| Run artifacts | `var/real_runs/` |
| Strategic review memory | `~/.claude/projects/-home-brian-projects/memory/onto_canon6_strategic_review.md` |

---

## Rejection Patterns from PSYOP Stage 1

These are what the prompts need to fix:
1. **Alias self-references** — e.g., `USAFRICOM -> U.S. Africa Command` (name variants, not assertions)
2. **Vague narrative claims** — structurally valid but not useful governed assertions
3. **Predicate misfits** — e.g., `use_organizational_form` or `hold_command_role` where text supports a different relation

---

## Dependencies

- `llm_client` — all LLM calls (mandatory kwargs: `task=`, `trace_id=`, `max_budget=`)
- `prompt_eval` — prompt variant comparison
- `../onto-canon/data/sumo_plus.db` — SUMO hierarchy for evaluation
- Predicate Canon: 4,669 predicates, 11,890 role slots, 78% single-sense lemma rate

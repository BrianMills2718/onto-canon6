# Friction Log: 2026-03-18 PSYOP Stage 1 Real Run

Use this log to record only observed workflow friction from the real run.
Keep it short and concrete.

## Format

- `timestamp`
- `step`
- `severity`
- `what happened`
- `workaround`
- `suggested fix`

## Entries

1. `2026-03-18T17:40-07:00` | `extract-text whole-report` | `high` | `The configured extraction task selected a long-thinking model path that repeatedly hit output-length limits on real report text.` | `Added deterministic chunking and ran bounded chunk files instead of whole reports.` | `Keep chunking first-class for real ingestion and prefer a budget extraction task for this workflow.`
2. `2026-03-18T17:55-07:00` | `llm runtime` | `medium` | `Workspace environment set LLM_CLIENT_TIMEOUT_POLICY=ban, which disabled the configured timeout behavior during the real run.` | `Explicitly ran the extraction commands with LLM_CLIENT_TIMEOUT_POLICY=allow.` | `Document and validate runtime-sensitive env overrides before live runs.`
3. `2026-03-18T18:20-07:00` | `extract-text contract` | `high` | `Live extraction often produced useful named entities without stable entity IDs, which the old extractor boundary rejected.` | `Allowed extraction outputs to provide reviewer-meaningful entity names and derived source-scoped local entity IDs deterministically.` | `Keep local source-scoped entity-id derivation in the extraction boundary until broader identity resolution takes over.`
4. `2026-03-18T18:35-07:00` | `extract-text evidence grounding` | `high` | `The model was much more reliable at quoting exact evidence text than at computing correct character offsets.` | `Treated quoted evidence text as primary and resolved offsets deterministically against the source text.` | `Keep evidence-span resolution text-first and fail loudly on ambiguous matches.`
5. `2026-03-18T18:50-07:00` | `extract-text prompt quality` | `medium` | `The prompt-facing predicate catalog was too thin, so the model produced structurally valid but semantically weak predicate choices.` | `Expanded the rendered predicate catalog to include role requirements, cardinality, and expected filler types.` | `Preserve ontology-aware role constraints in prompt rendering for all governed extraction paths.`
6. `2026-03-18T19:05-07:00` | `provider availability` | `medium` | `OpenRouter key rotation occurred during live extraction and some keys were over the total limit.` | `Allowed the llm_client retry/rotation path to recover and reran bounded chunk jobs.` | `Expect provider rotation during real runs and keep the friction visible instead of hiding retries.`
7. `2026-03-18T19:20-07:00` | `review quality` | `high` | `Several candidates from real narrative text were structurally valid but semantically weak or mapped to poor predicate choices.` | `Reviewed them explicitly and rejected the weak candidates instead of widening ontology or silently accepting them.` | `Use real-review rejection patterns to guide future prompt or ontology improvements, not parity pressure.`
8. `2026-03-18T19:35-07:00` | `graph promotion` | `high` | `Promotion failed for an accepted value-bearing assertion because the graph layer only understood manual value fillers under value=..., while live extraction persisted normalized literals under normalized=...` | `Patched canonical graph promotion to accept normalized-only value fillers and added a regression test.` | `Keep graph promotion aligned with the real extraction payload contract, not only the manual seed shape.`

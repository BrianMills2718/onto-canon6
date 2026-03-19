# prompt_eval Extraction Experiment

Status: implemented

## Purpose

Use `prompt_eval` and shared `llm_client` observability for extraction prompt
iteration instead of ad hoc local loops.

This is a supporting tool for `0012_extraction_quality_baseline.md`, not a new
architecture branch. The operational extraction service stays unchanged. The
experiment compares prompt variants over the same benchmark fixture and reloads
the result family from shared observability for comparison.

## Scope

The first slice is intentionally narrow:

1. use the existing `psyop_eval_slice.json` benchmark fixture;
2. require a single shared profile across all cases;
3. compare two extraction prompt variants:
   - `baseline`
   - `hardened`
4. score each trial deterministically using:
   - exact canonicalization F1
   - structural usable rate (`valid` + `needs_review`)
   - candidate-count alignment
5. compare variants through `prompt_eval.compare_variants(...)`

## Acceptance Criteria

1. experiment runs go through `prompt_eval.run_experiment(...)`, not a custom
   local trial loop;
2. extraction prompt variants carry explicit `prompt_ref` provenance on the
   underlying LLM calls;
3. the result family is reloadable through
   `prompt_eval.load_result_from_observability(...)`;
4. the experiment fails loudly if the fixture mixes profiles;
5. there is a thin CLI surface for running the experiment and inspecting the
   typed report;
6. tests cover:
   - deterministic trial scoring
   - mixed-profile failure
   - service-level wiring
   - CLI wiring

## Non-Goals

1. Do not replace the existing live benchmark service.
2. Do not introduce a second extraction runtime.
3. Do not add nested LLM judging inside `prompt_eval`.
4. Do not move repo-local prompt templates into `llm_client` shared prompt
   assets in this slice.

## Known Limits

1. The first slice uses repo-local prompt template paths plus explicit
   `prompt_ref` metadata. It does not yet render through `llm_client`
   `prompt_ref` asset resolution because these prompt templates are not part of
   the shared `llm_client` prompt asset root.

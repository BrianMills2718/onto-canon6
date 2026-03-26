# Plan 0013: LLM Observability and Prompt-Eval Adoption

Status: complete

## Purpose

Adopt the shared `llm_client` observability and `prompt_eval` experiment
surfaces where they immediately improve `onto-canon6`, without reopening the
broader roadmap.

## Acceptance Criteria

Pass:

1. the live benchmark path records stable prompt provenance for both extraction
   and reasonableness-judge calls;
2. one benchmark invocation emits shared experiment run, item, and aggregate
   records that can be queried outside the local report object;
3. benchmark outputs expose the experiment execution identifier and per-case
   run identifiers;
4. the repo docs say clearly that prompt/model iteration should prefer
   `llm_client` observability and `prompt_eval` when useful, rather than ad
   hoc local loops.

Fail:

1. prompt provenance remains missing from `llm_client` call logs;
2. the live benchmark still only produces local Python objects and notebooks;
3. the repo implies that `prompt_eval` adoption already exists when it is only
   planned.

## Chosen Slice

Implement now:

1. config-backed prompt refs for extraction and benchmark judging;
2. shared experiment logging around the existing Phase 5 benchmark loop;
3. a family-level benchmark aggregate over the emitted case runs;
4. explicit docs that mark `prompt_eval` as the next helpful layer for
   prompt/model comparison rather than pretending it is already wired.

Do not implement now:

1. a full migration of the benchmark onto `prompt_eval.run_experiment()`;
2. generalized prompt-asset resolution for repo-local prompt refs;
3. a larger benchmark-expansion phase.

## Outcome

All acceptance criteria are satisfied:

1. prompt provenance is config-backed (`extraction.prompt_ref`,
   `judge_prompt_ref` in `config/config.yaml`);
2. the live benchmark emits shared experiment runs, items, and aggregates
   through `llm_client.observability`;
3. benchmark outputs expose execution identifiers;
4. `CLAUDE.md` and plan 0015 document `prompt_eval` as the preferred
   layer for prompt/model iteration.

The direct `prompt_eval` integration was subsequently implemented in plan
0015 (`0015_prompt_eval_extraction_experiment.md`), which adds
`ExtractionPromptExperimentService` with 4 prompt variants, failure
taxonomy, and statistical comparison.

## Notes

- This slice improved observability and repeatability without changing the
  benchmark’s core semantics.
- Direct `prompt_eval` adoption is now live through plan 0015 and is the
  preferred approach for prompt/model comparison going forward.

# Extraction Quality Baseline

Status: active

Last updated: 2026-03-21
Workstream: post-bootstrap extraction R&D (ADR-0022)

## Purpose

Get extraction quality to a useful baseline before treating the newer
extraction architecture as ready for broader consumers.

This plan is driven by real friction from the Stage 1 PSYOP run and the later
bounded extraction experiments. It is not a new successor phase and it is not
parity-chasing. It is the active quality campaign for the post-bootstrap
extraction workstream.

## Acceptance Criteria

This plan is complete only when all of the following are true:

1. one prompt/model lane completes the current bounded benchmark sweep
   repeatably with no structural trial failures;
2. that same lane produces materially better semantic quality than the old
   baseline on the current extraction-boundary benchmark contract;
3. bounded real-document verification succeeds on at least two explicit chunks
   with reviewable output and no recurring structural breakage;
4. the remaining misses are clearly semantic/domain questions, not unresolved
   prompt-experiment or observability plumbing problems.

This plan fails if:

1. prompt experiments only expose transport or schema failures;
2. exact/count improvements are still dominated by reviewer-only IDs or
   downstream normalization differences;
3. real-document runs regress back into empty roles, invalid filler shape, or
   other structural failures as the main blocker.

## Current State

### Harness and Scoring

The extraction prompt-eval boundary is now usable on the explicit:

1. `--selection-task budget_extraction`
2. `--comparison-method bootstrap`
3. bounded `case-limit` / `n-runs` path

Phase A exact scoring is now aligned to extraction-boundary semantics rather
than reviewer-only canonical payload shape (ADR-0020). That means prompt-eval
now measures predicate/role/entity/value behavior honestly for this boundary.

### Best Confirmed Phase A Result

The strongest clean Phase A result so far came from the
`single_response_hardened` family after the split-multi-fact and
entity-type/filler-kind clarifications:

1. `mean_score = 0.63916`
2. `exact_f1 = 0.53333`
3. `structural_usable_rate = 0.9`
4. `count_alignment = 0.675`
5. `n_errors = 0`

That prompt state was promoted into the main live extraction prompt.

### Phase B Real-Chunk Checkpoint

The first bounded real Stage 1 chunk verification now proves:

1. `fast_extraction` can remain truthful but operationally impractical on this
   slice because it may sit in `waiting` too long;
2. the same bounded chunk completes successfully on
   `--selection-task budget_extraction`;
3. that run produced 10 valid candidates;
4. real review accepted 8 of the 10 candidates;
5. the two rejections were semantic support/predicate issues, not structural
   schema failures.

The two concrete semantic misses were:

1. unsupported context-only membership inference
   (`4th PSYOP Group -> belongs_to_organization -> USSOCOM`);
2. forcing JPOTF establishment text into `oc:use_organizational_form`.

ADR-0021 now locks the interpretation of those errors: chunk extraction stays
directly grounded to the current call input, and broader document-level
synthesis is explicitly deferred.

### New Discriminative Benchmark Cases

The benchmark fixture is now `psyop_eval_slice_v3` and includes explicit cases
for:

1. context-only membership strict omit;
2. named institutional concern;
3. JPOTF establishment not organizational-form.

Those cases proved that the earlier Phase A winner does not automatically
generalize. The next prompt iteration must target those cases explicitly rather
than assuming the earlier winner is the stable default.

## Current Evidence

Active run history and supporting evidence live here:

1. `docs/runs/2026-03-21_expanded_fixture_prompt_eval_baseline.md`
2. `docs/runs/2026-03-21_phase_a_prompt_eval_dry_review.md`
3. `docs/runs/2026-03-21_phase_b_chunk_verification.md`
4. `docs/runs/2026-03-21_phase_b_focus_prompt_eval.md`
5. `var/evaluation_runs/expanded_fixture_prompt_eval_2026-03-21_contract_aligned.json`
6. `var/evaluation_runs/psyop_eval_slice_phase_b_focus_prompt_eval.json`

This plan intentionally does not duplicate the dated campaign chronology. The
run notes are the history. This file is the active plan and current state.

## Active Next Slices

Build in this order:

1. add case-level diagnostics to the prompt-eval output so variant behavior is
   visible per benchmark case, not only in aggregates;
2. design one or two targeted prompt variants specifically against the v3
   cases (`006-008`) instead of another generic prompt rewrite;
3. rerun the bounded benchmark on the explicit `budget_extraction` lane;
4. rerun bounded real-chunk verification with the best surviving variant;
5. only then decide whether broader corpus verification or a larger extraction
   architecture change is justified.

## Known Risks and Uncertainties

1. The current prompt-eval winner may still be slice-specific and fail to
   generalize once more real-chunk-derived cases are added.
2. `budget_extraction` is the viable experiment lane right now, but that does
   not yet justify flipping the global repo default away from
   `fast_extraction`.
3. Whole-document inference remains valuable, but per ADR-0021 it must not be
   smuggled into the chunk-grounded extraction contract.
4. Some future gains may require model/task changes rather than prompt edits
   alone.

## Non-Goals

1. silently turning this workstream into a new canonical successor phase;
2. weakening extraction grounding to paper over document-level inference gaps;
3. adding new ontology/runtime features before the current extraction-quality
   questions are resolved.

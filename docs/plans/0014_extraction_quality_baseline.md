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

### Focused v3 Diagnostic Result

The focused diagnostic rerun over cases `006-008` now has two important
improvements:

1. case diagnostics include one representative successful output payload per
   case and variant, so semantic drift is visible without reopening the raw
   prompt-eval trial family;
2. the revised `compact@2` prompt is the first variant to handle all three
   focus cases correctly in one bounded run:
   - omit context-only membership inference;
   - keep the named institutional concern candidate; and
   - omit JPOTF-establishment over-extraction.

That does not make `compact@2` the global default yet. It does mean the next
quality step should expand outward from this focused win rather than keep doing
generic prompt rewrites.

### Broad v3 Benchmark Result

The broader v3 rerun now shows that `compact@2` is not only a focused-case
winner:

1. it materially outperformed `baseline` on the full v3 fixture;
2. that improvement was bootstrap-significant on the current bounded run; and
3. its remaining failures are now concentrated in a small number of structural
   drift cases rather than broad semantic collapse.

The lane is still not acceptance-complete because it had two structural trial
failures on the broader sweep. But the current question is no longer "does this
prompt work at all?" It is "can we verify it on another real chunk before
promoting it, and can we reduce the last structural drift cases without losing
the semantic gains?"

### Compact-v2 Operational Checkpoint

The bounded prompt-override path is now proved on the live `extract-text`
surface.

That checkpoint matters for two reasons:

1. it lets the repo test a candidate extraction prompt on a real chunk without
   mutating the repo-wide extraction default; and
2. it proves the operational path can consume a prompt asset shaped for live
   extraction, not only the prompt-eval experiment harness.

The first explicit compact-v2 operational verification used the same Stage 1
chunk that previously exposed the Phase B overbinding problems and produced:

1. `9` structurally valid candidates;
2. `8` accepted and `1` rejected after real review (`88.9%` acceptance);
3. no JPOTF over-extraction candidate on the live extraction path; and
4. the same remaining directly-grounded membership inference miss already known
   from the earlier chunk review.

This is the strongest current evidence that the extraction-quality campaign is
past pure harness work. The remaining question is prompt generalization across
more than one explicit real chunk, not whether the bounded operational
verification path exists.

## Current Evidence

Active run history and supporting evidence live here:

1. `docs/runs/2026-03-21_expanded_fixture_prompt_eval_baseline.md`
2. `docs/runs/2026-03-21_phase_a_prompt_eval_dry_review.md`
3. `docs/runs/2026-03-21_phase_b_chunk_verification.md`
4. `docs/runs/2026-03-21_phase_b_focus_prompt_eval.md`
5. `docs/runs/2026-03-21_phase_b_focus_prompt_eval_v2.md`
6. `var/evaluation_runs/expanded_fixture_prompt_eval_2026-03-21_contract_aligned.json`
7. `var/evaluation_runs/psyop_eval_slice_phase_b_focus_prompt_eval.json`
8. `var/evaluation_runs/psyop_eval_slice_phase_b_focus_prompt_eval_v2.json`
9. `docs/runs/2026-03-21_v3_broad_prompt_eval_compact2.md`
10. `var/evaluation_runs/psyop_eval_slice_v3_prompt_eval_compact2_broad.json`
11. `docs/runs/2026-03-21_compact2_real_chunk_verification.md`

This plan intentionally does not duplicate the dated campaign chronology. The
run notes are the history. This file is the active plan and current state.

## Active Next Slices

Build in this order:

1. use the new case-level diagnostics plus representative outputs to review the
   broader v3 benchmark case by case, not only through aggregate scores;
2. run a second explicit real chunk through the bounded compact-v2 operational
   override path;
3. if that second chunk is similarly strong, decide whether compact-v2 should
   replace the current repo-default live extraction prompt;
4. only after that decide whether broader corpus verification or a larger
   extraction architecture change is justified.

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
5. The bounded override path depends on extraction-compatible prompt assets;
   prompt-eval templates are similar but not directly interchangeable because
   the live extraction path and the experiment harness pass different input
   variables.

## Non-Goals

1. silently turning this workstream into a new canonical successor phase;
2. weakening extraction grounding to paper over document-level inference gaps;
3. adding new ontology/runtime features before the current extraction-quality
   questions are resolved.

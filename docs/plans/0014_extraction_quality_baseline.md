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

### Second Real-Chunk Generalization Check

The second explicit real chunk answered that question, and the answer is:
not yet.

The same bounded compact-v2 operational path ran successfully on the
analytical prose-heavy chunk `003`, but the semantic outcome was poor:

1. `5` structurally valid candidates;
2. `0` accepted and `5` rejected after real review;
3. four rejected `oc:express_concern` candidates that invented `USSOCOM` as a
   speaker where the narration named no speaker; and
4. one rejected `oc:limit_capability` candidate whose subject/capability
   anchoring was looser than the text justified.

That means the current blocker is no longer whether the operational override
path works on more than one chunk. It does. The blocker is that compact-v2
still overreaches on prose-heavy analysis sections and should not replace the
repo-default extraction prompt yet.

### v4 Prompt-Eval Recovery vs Operational Transfer Gap

The next bounded prompt-eval slice did recover the new prose-heavy benchmark
cases.

After adding two chunk-003-derived strict-omit cases and tightening the compact
prompt, the `v4` prompt-eval sweep showed:

1. `compact` as the clear winner on the updated fixture;
2. `compact` returning `candidates: []` on both new strict-omit cases; and
3. the other variants still over-extracting or failing structurally on at
   least one of those cases.

But the operational rerun on the same real chunk did not inherit that win. The
updated extraction-compatible compact prompt still produced `6` candidates and
all `6` were rejected for the same narrator/speaker and loose capability
anchoring problems.

That makes the current blocker more specific:

1. the benchmark is now discriminating the right failure mode;
2. the compact prompt can solve that failure mode in prompt_eval; but
3. the fix does not yet transfer to the full live extraction path.

Rendered prompt comparison narrowed that transfer gap further:

1. the compact prompt-eval and operational system messages now differ only
   modestly;
2. the much larger difference is the user payload, because prompt_eval is
   scoring isolated sentence-level cases while the operational path sees the
   full multi-paragraph chunk; and
3. the next useful question is therefore whether the benchmark needs an
   explicit chunk-level evaluation slice rather than more small prompt-only
   edits.

### Chunk-Level Transfer Gate

That explicit chunk-level gate now exists (ADR-0023, Plan 0019).

The new stable artifact is:

```bash
python -m onto_canon6 export-chunk-transfer-report ...
```

The first proof over the compact-v2 family now gives the exact contrast this
workstream needed:

1. `chunk_002` transfer report:
   - `8/9` accepted
   - verdict `positive`
2. `chunk_003` rerun transfer report:
   - `0/6` accepted
   - verdict `negative`

That means the current state is no longer ambiguous:

1. the repo can now distinguish sentence-level prompt-eval recovery from real
   chunk-level transfer;
2. compact-v2 is strong enough to succeed on at least one real chunk; but
3. compact-v2 still should not become the live default because its transfer is
   mixed, not broadly positive.

The later `compact3` benchmark improvement did not yet change that operational
conclusion on chunk 003:

1. the recovered `compact3` chunk-003 transfer report shows `0/4` accepted;
2. that is a smaller rejected set than the `compact2@2` rerun (`0/6`), but it
   is still a `negative` transfer result; and
3. the current bottleneck is now clearly live transfer on the full chunk, not
   sentence-level prompt-eval discrimination alone.

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
12. `docs/runs/2026-03-21_compact2_real_chunk_verification_chunk003.md`
13. `docs/runs/2026-03-21_v4_prompt_eval_compact3_none.md`
14. `docs/runs/2026-03-21_compact2_real_chunk_verification_chunk003_rerun.md`
15. `docs/runs/2026-03-21_chunk_transfer_gate_compact2.md`
16. `var/evaluation_runs/chunk_transfer_reports/2026-03-21_chunk_002_transfer_report.json`
17. `var/evaluation_runs/chunk_transfer_reports/2026-03-21_chunk_003_transfer_report.json`
18. `docs/runs/2026-03-22_compact3_chunk003_transfer_recovery.md`
19. `var/evaluation_runs/chunk_transfer_reports/2026-03-21_chunk_003_transfer_report_compact3.json`
20. `investigations/2026-03-22-compact2-vs-compact3-chunk003-transfer-gap.md`
21. `docs/runs/2026-03-22_chunk003_context_focus_prompt_eval.md`
22. `investigations/2026-03-22-full-chunk-compact-observability-reconstruction.md`

This plan intentionally does not duplicate the dated campaign chronology. The
run notes are the history. This file is the active plan and current state.

## Active Next Slices

Build in this order:

1. compare the live `compact2@2` and inferred `compact3@1` chunk-003 outputs
   directly, using persisted candidate payloads and review outcomes rather
   than only aggregate prompt-eval scores;
2. freeze the four surviving chunk-003 analytical-prose spans as new
   evaluation cases, ideally with sentence-only and short-local-context
   variants, so the repo can distinguish prompt weakness from longer-context
   transfer effects;
3. use those new results to separate local prompt quality from full-chunk
   operational behavior; current evidence now points more toward longer chunk
   context than local prompt wording;
4. reconstruct or compare the full operational prompt/render path on chunk 003
   before another broad prompt rewrite; this reconstruction is now complete and
   confirms the same chunk render with only a stronger system prompt;
5. treat chunking/render strategy and full-chunk operational context as the
   primary next extraction-quality lever, ahead of another broad prompt
   rewrite;
6. track the compact prompt-eval `multiple_tool_calls` failure as an
   experiment-reliability issue distinct from semantic extraction quality;
7. only after that decide whether another operational prompt revision is
   justified; and
8. only after that decide whether broader corpus verification or a larger
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
6. Prose-heavy analytical sections can still trigger narrator/speaker confusion
   even when chunk-grounding and structural validity are otherwise good.
7. Prompt-eval improvements can fail to transfer to the live extraction path
   when the operational asset or longer chunk context behaves differently from
   the sentence-level benchmark harness.
8. Current evidence suggests the longer chunk context is a bigger source of
   transfer failure than the remaining system-prompt wording differences.

## Non-Goals

1. silently turning this workstream into a new canonical successor phase;
2. weakening extraction grounding to paper over document-level inference gaps;
3. adding new ontology/runtime features before the current extraction-quality
   questions are resolved.

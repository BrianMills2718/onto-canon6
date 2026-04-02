# 2026-04-01 Wrapper Alignment Decision

## Scope

Closeout note for `docs/plans/0044_24h_wrapper_alignment_block.md`.

This note answers the bounded question left by Plan `0043`:

**If the live extraction surface is aligned more closely to the prompt-eval
wrapper, does the chunk-003 divergence narrow materially?**

## Canonical Artifacts

1. `docs/runs/2026-04-01_live_path_divergence_decision.md`
2. `docs/runs/2026-04-01_chunk003_prompt_surface_parity_v5.json`
3. `docs/runs/2026-04-01_chunk003_prompt_surface_parity_v6.json`
4. `var/real_runs/2026-04-01_compact6_wrapper_align_chunk003/outputs/extract_manifest.json`
5. `docs/runs/2026-04-01_chunk003_transfer_report_compact6_wrapper_align.json`
6. `docs/runs/2026-04-01_chunk003_semantic_transfer_diff_compact6_wrapper_align.json`

## What Changed

The aligned live candidate was:

1. prompt:
   `onto_canon6.extraction.text_to_candidate_assertions_compact_v6_wrapper_align@1`
2. system instructions:
   same as `compact_v5`
3. user-surface change:
   - `source material` wording
   - explicit `Case input:` wrapper
   - same source fields moved inside that wrapper

Compared with the prior `v5` artifact, the prompt-surface diff shrank to the
remaining `Case id:` line plus minor spacing noise.

## Live Result

Wrapper alignment did **not** narrow the divergence.

Compared with the prior live `compact_v5` rerun:

1. `compact_v5`:
   - `4` accepted candidates
   - `0` shared bodies with prompt-eval
2. `compact_v6_wrapper_align`:
   - `6` accepted candidates
   - `0` shared bodies with prompt-eval

The aligned wrapper actually widened the live-only family:

1. `4` `oc:limit_capability`
2. `1` `oc:express_concern`
3. `1` `oc:uses_designation_label`

## Decision

Plan `0044` is complete.

Wrapper alignment is **not** the main rescue lever for the current chunk-003
divergence.

The repo now knows:

1. reducing the user-surface gap does not bring the live extractor toward the
   prompt-eval result;
2. the live extraction path still diverges before review; and
3. the next blocker is therefore deeper than wrapper wording alone.

## Next Bounded Step

The next block should target the live extraction path itself:

1. compare the live extraction-service call path against the prompt-eval call
   path under the same prompt/model pair;
2. identify what live-only behavior remains after wrapper alignment is ruled
   out; and
3. keep review/judge behavior as a secondary check, not the first repair
   lever.

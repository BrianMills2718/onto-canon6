# 2026-04-02 Extraction-Path Decision

## Scope

Closeout note for `docs/plans/0045_24h_extraction_path_block.md`.

This note answers the bounded question left by Plan `0044`:

**What part of the live extraction path still causes chunk-003 divergence
after wrapper alignment is ruled out?**

## Canonical Artifacts

1. `docs/runs/2026-04-01_wrapper_alignment_decision.md`
2. `docs/runs/2026-04-02_chunk003_extraction_call_surface_diff.json`
3. `docs/runs/2026-04-02_chunk003_extraction_call_surface_diff_temp0_relref.json`
4. `docs/runs/2026-04-02_chunk003_semantic_transfer_diff_compact6_temp0_relref.json`
5. `var/real_runs/2026-04-02_compact6_temp0_relref_chunk003/outputs/extract_manifest.json`

## What Plan 0045 Proved

Plan `0045` localized the remaining live-vs-prompt_eval differences more
precisely than any earlier block:

1. the live `budget_extraction` call was omitting `temperature=0.0` while the
   prompt-eval call included it explicitly;
2. the live path was defaulting `source_ref` to an absolute path unless the CLI
   caller overrode it;
3. after aligning both `temperature=0.0` and the relative `source_ref`, the
   live chunk-003 rerun still produced `5` accepted candidates with `0`
   body-level overlap against the prompt-eval zero-candidate result.

This means the temperature omission was a real extraction-path difference, but
it was **not** the dominant rescue lever for chunk `003`.

## Current Fact Pattern

After the aligned `compact_v6_wrapper_align` rerun with deterministic
temperature and prompt-eval-matching `source_ref`, the remaining live-vs-prompt
surface differences were reduced to:

1. `public_api`
   - live: `call_llm_structured`
   - prompt-eval: `acall_llm_structured`
2. timeout control
   - live: `60`
   - prompt-eval: `0`
3. prompt-eval-only user metadata
   - `Case id: psyop_017_full_chunk003_analytical_context_strict_omit`
   - one blank line before `Source text:`

The semantically meaningful output still diverged completely:

1. prompt-eval: `{"candidates":[]}`
2. live temp0+relref rerun:
   - `3` `oc:limit_capability`
   - `1` `oc:express_concern`
   - `1` `oc:belongs_to_organization`
3. body overlap: `0`

## Decision

Plan `0045` is complete.

The dominant blocker family remains:

**live extraction-service behavior before review**

with a narrower residual than before:

1. missing temperature was a real live-path difference, but not the dominant
   root cause;
2. review/judge behavior remains secondary amplification, not the first blocker;
3. the remaining unresolved residual is now bounded to:
   - sync vs async `llm_client` structured-call behavior, and/or
   - the prompt_eval-only `Case id` metadata line.

## Next Bounded Step

The next block should not reopen broad prompt editing.

It should only answer:

1. does the residual survive when the same rendered prompt is replayed through
   the async structured-call path; and
2. does the residual survive when the prompt_eval-only `Case id` metadata is
   isolated as the last prompt-surface difference?

That next block is tracked as
`docs/plans/0046_24h_sync_async_and_caseid_residual_block.md`.

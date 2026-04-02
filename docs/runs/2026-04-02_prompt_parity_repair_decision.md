# 2026-04-02 Prompt Parity Repair Decision

## Scope

Closeout note for the prompt-side residual sequence:

1. `docs/plans/0046_24h_sync_async_and_caseid_residual_block.md`
2. `docs/plans/0047_24h_case_metadata_parity_block.md`
3. `docs/plans/0048_24h_prompt_wrapper_parity_block.md`
4. `docs/plans/0049_24h_post_repair_transfer_block.md`

The bounded question was:

**After wrapper alignment and extraction-path localization, what remaining
prompt-side differences still explain chunk-003 live vs prompt_eval drift, and
what remains once those differences are repaired?**

## Canonical Artifacts

1. `docs/runs/2026-04-02_chunk003_prompt_eval_replayed_via_sync.json`
2. `docs/runs/2026-04-02_chunk003_live_temp0_replayed_via_async.json`
3. `docs/runs/2026-04-02_chunk003_prompt_eval_replayed_async_without_case_id.json`
4. `docs/runs/2026-04-02_chunk003_prompt_eval_replayed_async_without_case_id_or_blank.json`
5. `docs/runs/2026-04-02_chunk003_prompt_eval_replayed_async_without_case_id_or_wrapper.json`
6. `docs/runs/2026-04-02_chunk003_prompt_surface_parity_without_case_id.json`
7. `docs/runs/2026-04-02_chunk003_prompt_surface_parity_without_case_id_or_wrapper.json`
8. `docs/runs/2026-04-02_chunk003_post_repair_prompt_eval_report.json`

## What The Residual Sequence Proved

### 1. Sync vs async public API was not the dominant blocker

The replay evidence ruled out the public API facade as the main explanation:

1. replaying the captured prompt_eval prompt through `call_llm_structured`
   still returned `0` candidates;
2. replaying the captured live temp0+relref prompt through
   `acall_llm_structured` still returned a non-empty candidate family.

That made `llm_client` public API parity secondary, not dominant.

### 2. `Case id:` was a real prompt-side blocker

Removing only the prompt_eval-only `Case id:` line changed the replay result
from `0` candidates to `5`.

This proved that benchmark-only case metadata was materially changing the model
behavior on chunk `003`.

### 3. The prompt_eval-only `Case input:` wrapper heading was also active

Removing `Case id:` plus the prompt_eval-only `Case input:` heading changed the
replay from `5` candidates to `4`.

That matched the live async candidate count and proved the wrapper heading was
also part of the remaining prompt-side residual.

### 4. The rendered operational-parity surface is now effectively aligned

After the case-id and wrapper repairs landed:

1. prompt_eval extraction input no longer includes `Case id:` by default;
2. extraction prompt_eval templates no longer prepend `Case input:` before
   `{input}`;
3. the real chunk-003 rendered prompt surface has no remaining content-line
   diff against the live user prompt;
4. the only residual rendered difference is one trailing newline.

### 5. The active blocker moved back to semantic extraction quality

The post-repair one-case prompt_eval rerun on
`psyop_017_full_chunk003_analytical_context_strict_omit` produced a real
compact operational-parity output again, but the case is still semantically
wrong:

1. `mean_score = 0.25`
2. `exact_f1 = 0.0`
3. `count_alignment = 0.0`
4. `structural_usable_rate = 1.0`

The repaired prompt_eval example output is now near the live family, not the
old zero-candidate prompt_eval failure:

1. both families contain the same three `oc:limit_capability` narratives;
2. both contain the same concern-family extraction instead of the old
   zero-candidate result;
3. the repaired prompt_eval output still differs semantically from live by
   splitting `Congressional oversight` and `public scrutiny` into two
   `oc:express_concern` candidates rather than one combined concern candidate.

## Decision

The prompt-parity repair sequence is complete.

It changed the active blocker honestly:

1. the repo is no longer blocked on sync-vs-async call-path speculation;
2. the repo is no longer blocked on prompt_eval-only `Case id:` metadata;
3. the repo is no longer blocked on the prompt_eval-only `Case input:` wrapper;
4. the active blocker is now semantic extraction quality on the repaired
   analytical chunk-003 path.

## Explicit Uncertainty

One replay remained runtime-unstable:

1. the fully aligned manual replay that also replaced the last opening wording
   line hung for minutes and was aborted without a result;
2. that instability was not needed for the decision because the rendered
   prompt-surface repair and the post-repair prompt_eval rerun already proved
   the blocker transition.

## Next Bounded Step

The next block should not reopen prompt-surface plumbing.

It should focus on one bounded semantic question:

**How do we recover strict-omit behavior on chunk `003` under the repaired
operational-parity prompt surface without reintroducing the old prompt-path
drift?**

That next block is tracked as
`docs/plans/0050_24h_post_parity_semantic_recovery_block.md`.

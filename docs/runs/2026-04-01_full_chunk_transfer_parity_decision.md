# 2026-04-01 Full-Chunk Transfer Parity Decision

## Scope

Closeout note for
`docs/plans/0041_24h_full_chunk_transfer_parity_block.md`.

This note answers the narrow question left open by Plan `0040`:

**Is the remaining full-chunk live vs prompt-eval disagreement mainly a
prompt/render contract problem, or is it still a semantic extraction
difference?**

## Canonical Artifacts

Prompt-surface artifacts:

1. `docs/runs/2026-04-01_chunk002_prompt_surface_parity.json`
2. `docs/runs/2026-04-01_chunk003_prompt_surface_parity.json`

Existing transfer-comparison artifacts:

1. `docs/runs/2026-04-01_chunk002_live_vs_parity_diff.json`
2. `docs/runs/2026-04-01_chunk003_live_vs_parity_diff.json`
3. `docs/runs/2026-04-01_chunk002_transfer_report_compact4.json`
4. `docs/runs/2026-04-01_extraction_transfer_certification.md`

## Prompt-Surface Result

The prompt-surface comparison helper now reconstructs three distinct surfaces
truthfully:

1. the live extraction messages;
2. the prompt-eval template messages before `{input}` substitution; and
3. the prompt-eval effective messages after the same substitution that
   `prompt_eval.runner._substitute_input()` performs at runtime.

For both canonical chunks, the result is the same:

1. system messages are identical;
2. the prompt-eval template still contains literal `{input}` until runtime;
3. the effective prompt-eval user message differs from the live user message
   in one stable wrapper family:
   - `"source material"` vs `"source text"` wording;
   - an explicit `Case input:` block with `Case id: ...`; and
   - otherwise the same core catalog/profile/source payload.

That means the repo no longer has an unknown "maybe the wrong prompt asset was
used" question. The render-path difference is now explicit and reproducible.

## Chunk 002 Result

Chunk `002` does **not** look like a pure prompt-surface failure.

Evidence:

1. live and prompt-eval both produce `10` candidates;
2. strict shared count is only `1`, but that is partly because the current
   transfer comparator includes `claim_text`;
3. comparing candidate bodies by predicate + roles yields:
   - `7` shared bodies
   - `3` live-only bodies
   - `3` prompt-eval-only bodies

The residual body-level differences are concrete:

Live-only:

1. `oc:belongs_to_organization`
   - `4th PSYOP Group -> Army`
2. `oc:limit_capability`
   - availability of PSYOP commander names limited by the sensitive nature of
     the work
3. `oc:use_organizational_form`
   - `Operation Iraqi Freedom -> Joint PSYOP Task Force`

Prompt-eval-only:

1. `oc:belongs_to_organization`
   - `4th PSYOP Group -> Army PSYOP unit`
2. `oc:operation_occurs_in_location`
   - `Operation Enduring Freedom -> Afghanistan`
3. `oc:operation_occurs_in_location`
   - `Operation Iraqi Freedom -> Iraq`

Interpretation:

1. the chunk-002 residual is mostly semantic body drift, not path confusion;
2. some of the strict mismatch is still claim-text wording noise, but not all
   of it;
3. the prompt-surface wrapper difference alone does not explain the residual.

## Chunk 003 Result

Chunk `003` is even clearer.

Prompt surface:

1. the same stable wrapper difference appears as chunk `002`;
2. system messages are still identical.

Output behavior:

1. prompt-eval parity emits `0` candidates;
2. the live path emits `3` candidates;
3. all `3` are live-only unsupported analytical overreach:
   - `oc:limit_capability`
   - `oc:express_concern`
   - `oc:hold_command_role`

Interpretation:

1. chunk `003` is not blocked by an unknown prompt/render-path mismatch;
2. it is blocked by semantic over-extraction on analytical narration.

## Decision

The dominant residual blocker is **semantic extraction behavior**, not prompt
asset confusion.

More precisely:

1. a stable prompt/render contract difference does exist;
2. that difference is generic and reproducible across both canonical chunks;
3. but the chunk-specific residuals are semantic:
   - chunk `002` mostly body-level candidate drift plus claim-text noise;
   - chunk `003` unsupported analytical overreach on the live path.

So Plan `0041` closes with this decision:

1. prompt-surface uncertainty is no longer the active blocker family;
2. the next bounded extraction block should target semantic transfer residuals,
   not more prompt-surface reconstruction.

## Next Bounded Step

The next block should:

1. freeze the semantic residual contract from chunk `002` and chunk `003`;
2. compare live vs prompt-eval candidates at the body level without letting
   `claim_text` dominate the signal;
3. make one bounded compact-prompt revision aimed at suppressing analytical
   narrator overreach while preserving chunk-002 positive control behavior; and
4. verify that revision first in prompt-eval, then on at least one live chunk
   rerun.

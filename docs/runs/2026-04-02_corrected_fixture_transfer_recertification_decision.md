# 2026-04-02 Corrected-Fixture Transfer Recertification Decision

## Decision

Plan `0057` does **not** certify the compact operational-parity lane for
promotion.

Chunk `002` remained a valid positive control, but chunk `003` produced a
false-positive transfer result under misaligned live review semantics.

## Evidence

### Positive control held

- `var/real_runs/2026-04-02_corrected_fixture_transfer_recertification/outputs/chunk_002_transfer_report.json`
- summary: `accepted=10/10`, `verdict=positive`

### Stress case result was overstated

- `var/real_runs/2026-04-02_corrected_fixture_transfer_recertification/outputs/chunk_003_transfer_report.json`
- summary: `accepted=5/5`, `verdict=positive`

That result does not survive comparison to corrected fixture `v6`:

1. chunk-003 candidate
   `“hearts and minds” campaigns ... were hampered ...`
   matches the same semantic family as
   `psyop_011_hearts_and_minds_narration_strict_omit`;
2. chunk-003 candidate
   `Bureaucratic friction ... impeded rapid decision-making ...`
   matches the same semantic family as
   `psyop_015_local_context_limit_capability_without_named_subject_strict_omit`;
3. chunk-003 candidate
   `Congressional oversight and public scrutiny increased regarding the ethical
   and legal questions ...`
   matches the same semantic family as
   `psyop_016_local_context_ethical_questions_with_following_scrutiny_strict_omit`;
4. the remaining chunk-003 `limit_capability` candidates are the same broader
   abstract evaluative family, not clean concrete operational assertions.

## Root Cause

The live transfer-report surface summarizes accepted/rejected review outcomes.
The current live `review_mode: llm` path is too permissive for the corrected
analytical-prose omit family:

1. implementation currently auto-accepts `partially_supported` candidates;
2. the judge prompt is still phrased as generic reasonableness review rather
   than corrected benchmark-boundary review for this omit family.

## Next Step

Activate Plan `0058`:

1. align live review behavior so only `supported` candidates auto-accept;
2. harden the judge prompt for the chunk-003 analytical-prose omit family; and
3. rerun chunk `002` and chunk `003` under the aligned contract.

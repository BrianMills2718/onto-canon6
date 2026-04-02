# Corrected-Fixture Semantic Recovery Decision

Date: 2026-04-02
Plan: `0056_24h_corrected_fixture_semantic_recovery_block.md`

## Decision

The bounded prompt revision should be kept.

It restored the compact operational-parity lane to the top score on the
corrected benchmark fixture without reopening the strict-omit regression guards.

## Artifacts

1. `docs/runs/2026-04-02_corrected_fixture_focus_report.json`
2. `docs/runs/2026-04-02_corrected_fixture_full_report.json`

## Results

Focused rerun (`case-limit 8`):

1. `compact_operational_parity = 0.7718`
2. `compact = 0.740625`
3. `psyop_008_jpotf_establishment_not_org_form = 1.0`
4. all variants completed with `n_errors = 0`

Full corrected-fixture rerun (`psyop_eval_slice_v6`):

1. `compact_operational_parity = 0.8859`
2. `compact = 0.8484375`
3. `baseline = 0.2947875`
4. all variants completed with `n_errors = 0`

Residual compact-operational-parity cases after the improvement:

1. `psyop_001_designation_change = 0.4744`
2. `psyop_002_concerns_about_truth_based_shift = 0.35`
3. `psyop_007_named_institutional_concern = 0.35`

Regression guard result:

1. `psyop_005`, `psyop_006`, and `psyop_008` through `psyop_016` all stayed
   clean at `1.0`.

## Interpretation

The benchmark-only question is no longer the blocker.

What is now true:

1. removing chunk `017` was the right contract change;
2. the bounded semantic prompt revision fixed `psyop_008`;
3. the compact operational-parity lane now beats the plain compact lane on the
   corrected fixture.

What is still not proved:

1. the improved prompt has not yet re-cleared the named real chunk-transfer
   gate from Plan `0014`;
2. chunk `003` remains the operational prose-heavy stress case until rerun;
3. benchmark improvement alone still cannot certify promotion.

## Next Step

The next blocker is now live transfer recertification on the two named chunks:

1. `chunk_002` positive control
2. `chunk_003` prose-heavy stress case

That work is activated as:

- `docs/plans/0057_24h_corrected_fixture_transfer_recertification_block.md`

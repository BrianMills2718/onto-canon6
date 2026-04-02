# 2026-04-02 Personnel-Membership Enforcement Decision

## Decision

Plan `0061` is complete and truthful. The named chunk-transfer blocker family
is no longer active.

## What Changed

Artifacts:

- `var/real_runs/2026-04-02_personnel_membership_enforcement/outputs/chunk_002_extract.json`
- `var/real_runs/2026-04-02_personnel_membership_enforcement/outputs/chunk_003_extract.json`
- `var/real_runs/2026-04-02_personnel_membership_enforcement/outputs/chunk_002_transfer_report.json`
- `var/real_runs/2026-04-02_personnel_membership_enforcement/outputs/chunk_003_transfer_report.json`

Results:

1. chunk `002` remained a positive control;
2. chunk `003` no longer accepted the staffing-summary
   `oc:belongs_to_organization` claim;
3. chunk `003` no longer accepted any spillover family at all; and
4. the only chunk-003 outputs that remained were two rejected abstract
   `oc:limit_capability` claims already governed by the corrected local
   benchmark omit controls.

## Interpretation

The compact operational-parity candidate now satisfies the currently named
real-chunk transfer gate:

1. chunk `002` transfers positively; and
2. chunk `003` transfers negatively under the corrected contract without any
   accepted spillover.

That means the remaining question is no longer chunk-transfer cleanup. It is
whether the proved candidate should now become the repo default.

## Conclusion

Plan `0061` is complete. Plan `0062` now owns promotion certification and
default cutover.

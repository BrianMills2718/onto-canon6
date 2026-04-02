# 2026-04-02 Limit-Capability Enforcement Decision

## Decision

Plan `0060` is complete and truthful. The compact operational-parity lane is
still not promotable, but the active blocker family changed cleanly.

## What Changed

Artifacts:

- `var/real_runs/2026-04-02_limit_capability_enforcement/outputs/chunk_002_extract.json`
- `var/real_runs/2026-04-02_limit_capability_enforcement/outputs/chunk_003_extract.json`
- `var/real_runs/2026-04-02_limit_capability_enforcement/outputs/chunk_002_transfer_report.json`
- `var/real_runs/2026-04-02_limit_capability_enforcement/outputs/chunk_003_transfer_report.json`

Results:

1. chunk `002` remained positive;
2. chunk `002` simplified from `10` accepted candidates to `2` accepted
   `oc:hold_command_role` claims, but it did not regress into a negative or
   mixed transfer result;
3. chunk `003` still transfers as `mixed`, not `positive`;
4. the owned abstract evaluative `oc:limit_capability` family is no longer
   accepted on the live path; and
5. the remaining chunk-003 acceptance is now one staffing-summary
   `oc:belongs_to_organization` claim.

## Remaining Residual

The only remaining accepted chunk-003 candidate is:

1. `A substantial proportion of personnel assigned to PSYOP units belonged to
   USSOCOM by 2013.`

That family is already represented by the corrected local benchmark contract
through `psyop_017_personnel_dedication_not_membership_strict_omit`.

## Conclusion

The bounded live-path enforcement seam worked. The active blocker is no longer
abstract `limit_capability`; it is now the smaller staffing-summary membership
family.

Plan `0061` now owns that work.

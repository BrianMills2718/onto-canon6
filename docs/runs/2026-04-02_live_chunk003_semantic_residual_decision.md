# 2026-04-02 Live Chunk-003 Semantic Residual Decision

## Decision

Plan `0059` is complete, but the compact operational-parity lane is still not
promotable.

## What Improved

Artifacts:
- `var/real_runs/2026-04-02_live_chunk003_semantic_residual/outputs/chunk_002_transfer_report.json`
- `var/real_runs/2026-04-02_live_chunk003_semantic_residual/outputs/chunk_003_transfer_report.json`

Results:

1. chunk `002` remained positive with `10/10` accepted candidates;
2. chunk `003` improved from `positive` to `mixed`;
3. the personnel-dedication-to-membership leak disappeared; and
4. the bogus chunk-003 `create_organizational_unit` candidate is now rejected.

## Remaining Residual

Chunk `003` still accepts three abstract evaluative `oc:limit_capability`
claims:

1. `effectiveness of PSYOP was limited ...`
2. `“hearts and minds” campaigns ... were hampered ...`
3. `digital media limited the impact of PSYOP messages`

Those are already represented by the local strict-omit benchmark contract
through cases `013` and `014`.

## Conclusion

Another prompt-only pass improved the live result but did not fully enforce the
documented boundary. The next best lever is one bounded enforcement seam for
the remaining abstract `limit_capability` family.

Plan `0060` now owns that work.

# 2026-04-01 Entity Resolution Alias-Family Completion

## Purpose

Record the fresh clean rerun after Plan 0035 repaired the three residual
alias-family misses from the clean-measurement baseline.

## Key Artifacts

Fixed-sample diagnostic rerun:

1. `docs/runs/scale_test_llm_2026-04-01_105502.json`
2. `var/scale_test_llm_alias_completion_v2/scale_test.sqlite3`

Fresh clean rerun:

1. `docs/runs/scale_test_llm_2026-04-01_110321.json`
2. `var/scale_test_llm_alias_completion_v3/scale_test.sqlite3`

## Verified Outcome

The original Plan 0035 residual families are now closed on the fresh clean
rerun:

1. `q02` closed:
   - `USSOCOM` and `U.S. Special Operations Command` now resolve together;
2. `q04` closed:
   - `Ft. Bragg` and `Fort Liberty` now resolve together;
3. `q08` closed:
   - `the Agency` now resolves to canonical entity `E006`.

The fresh clean rerun is measurement-valid:

1. all `25/25` source documents survived extraction;
2. extraction reported `96 extracted / 96 pending / 0 failed docs`;
3. `84` assertions were promoted;
4. `110` promoted entities were scanned;
5. `63` identity groups were formed with `47` alias attachments.

## Metrics

Fixed-sample diagnostic rerun (`105502`):

1. precision `1.00`
2. recall `0.8818`
3. false merges `0`
4. false splits `13`
5. answer rate `0.90`
6. accuracy over all questions `0.90`

Fresh clean rerun (`110321`):

1. precision `0.9316`
2. recall `1.00`
3. false merges `8`
4. false splits `0`
5. answer rate `0.90`
6. accuracy over all questions `0.80`

## Remaining Misses

The three original alias-family misses are no longer the blocker. The fresh
clean rerun exposed a different residual:

1. `q05` regressed to answered-but-wrong:
   - `General John Smith` and `James Smith` were incorrectly merged;
2. `q06` remained unanswered:
   - `Washington` and `George Washington University` still did not both resolve
     to unique predicted clusters.

False merges in `110321` are all the same family:

1. `John Smith` ↔ `James Smith`
2. `General John Smith` ↔ `James Smith`
3. `Gen. Smith` / `General Smith` / `Gen. J. Smith` ↔ `James Smith`

This shows the blocker has shifted from organization/installations to
same-surname person safety under the titled-person bridge path.

## Important Diagnostics

1. the corrected fixed-sample diagnostic artifact `105502` is useful for
   confirming that the intended Plan 0035 repairs worked without false merges;
2. the fresh clean rerun `110321` is the decision-grade artifact for the next
   block;
3. rerunning resolution on an already-resolved DB is not decision-grade and
   should not be used to close the block.

## Decision

Plan 0035 is complete under its own exit clause: the intended residual families
are closed, and the remaining blocker is now explicit and localized.

The next active block is:

1. `docs/plans/0036_24h_entity_resolution_negative_control_recovery_block.md`

That block owns restoration of same-surname person safety and the remaining
negative-control question behavior on a fresh clean rerun.

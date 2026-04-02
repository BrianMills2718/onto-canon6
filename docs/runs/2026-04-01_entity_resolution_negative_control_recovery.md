# 2026-04-01 Entity Resolution Negative-Control Recovery

## Purpose

Record the fresh rerun after Plan 0036 restored same-surname person safety and
recovered the remaining negative-control question behavior from the Plan 0035
fresh clean rerun.

## Key Artifacts

Aborted timeout-disabled rerun:

1. `var/scale_test_llm_negative_control_recovery/full_run.log`

Canonical timeout-enabled fresh rerun:

1. `docs/runs/scale_test_llm_2026-04-01_113959.json`
2. `var/scale_test_llm_negative_control_recovery_timeout/scale_test.sqlite3`
3. `var/scale_test_llm_negative_control_recovery_timeout/full_run.log`

## Verified Outcome

The timeout-enabled fresh rerun is measurement-valid:

1. all `25/25` source documents survived extraction;
2. extraction reported `104 extracted / 104 pending / 0 failed docs`;
3. `90` assertions were promoted;
4. `106` promoted entities were scanned;
5. `60` identity groups were formed with `46` alias attachments.

The Plan 0036 gate is now cleared on the canonical fresh rerun:

1. same-surname person safety is restored:
   - `John Smith` and `James Smith` are no longer falsely merged;
2. `q05` is answered and correct:
   - `General John Smith` and `James Smith` correctly resolve as different;
3. `q06` is answered and correct:
   - `Washington` and `George Washington University` correctly resolve as
     different entities;
4. previously closed questions remain green:
   - `q02`, `q04`, and `q08` stay answered and correct.

## Metrics

Canonical fresh rerun (`113959`):

1. precision `1.00`
2. recall `0.9417`
3. false merges `0`
4. false splits `6`
5. answer rate `1.00`
6. accuracy over all questions `1.00`

## Remaining Residuals

Plan 0036 removed the false-merge blocker entirely. The remaining quality gap
is now only false splits:

1. Rodriguez title-family split:
   - `James Rodriguez` / `Colonel Rodriguez` cluster separately from
     `Col. Rodriguez`;
2. Washington place-family split:
   - `Washington D.C.` / `D.C.` cluster separately from the `Washington`
     location cluster.

These residuals no longer block fixed-question correctness, but they keep
pairwise recall below `1.00`.

## Important Diagnostics

1. the first fresh rerun attempt is not decision-grade:
   - it hung because timeout handling was not enabled for the long-running
     LLM calls;
2. the canonical rerun for this block is the timeout-enabled artifact
   `113959`;
3. the next block should treat the remaining misses as false-split cleanup,
   not benchmark answerability recovery.

## Decision

Plan 0036 is complete. Its declared blocker is closed:

1. same-surname person safety is restored;
2. `q05` and `q06` are both answered and correct on a fresh rerun;
3. the remaining misses are narrower false splits only.

The next active block is:

1. `docs/plans/0037_24h_entity_resolution_false_split_cleanup_block.md`

That block owns the remaining Rodriguez and Washington place-family false
splits while preserving the zero-false-merge and `10/10` question-accuracy
floor from this rerun.

# 2026-04-02 Live Review Alignment Decision

## Decision

Plan `0058` is complete, but the compact operational-parity lane is still not
promotable.

## What Changed

1. `review_mode: llm` now auto-accepts only `supported` candidates;
2. `partially_supported` candidates now remain pending review;
3. the live judge prompt is now versioned as
   `onto_canon6.evaluation.judge_candidate_reasonableness@2`.

## Evidence

### Narrow judge replay

Artifact:
- `docs/runs/2026-04-02_live_review_alignment_judge_replay.json`

That replay showed the review alignment was directionally correct but not fully
stable on every local omit control.

### Fresh live reruns

Artifacts:
- `var/real_runs/2026-04-02_live_review_alignment/outputs/chunk_002_transfer_report.json`
- `var/real_runs/2026-04-02_live_review_alignment/outputs/chunk_003_transfer_report.json`

Results:

1. chunk `002` remained positive with `10/10` accepted candidates;
2. chunk `003` remained positive, but the accepted family shrank from `5`
   candidates to `4`.

## Remaining Residual

Chunk `003` still accepts:

1. three abstract evaluative `oc:limit_capability` claims; and
2. one `oc:belongs_to_organization` claim that converts personnel dedication
   prose into a membership assertion.

## Conclusion

The review-contract mismatch is no longer the dominant blocker. The next owned
problem is a smaller live extraction residual on chunk `003`, not another broad
review-policy question.

Plan `0059` now owns that residual.

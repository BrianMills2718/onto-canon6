# 2026-04-01 Entity Resolution Rerun Stability

## Scope

Decision-grade closeout note for
`docs/plans/0039_24h_entity_resolution_rerun_stability_block.md`.

This note answers one narrow question:

Can the best fresh rerun from Plan `0038` be reproduced on new databases
without reintroducing false merges or question-level instability?

## Incoming Contract

Plan `0038` ended with two fresh reruns that defined the problem:

1. `docs/runs/scale_test_llm_2026-04-01_131124.json`
   - precision `1.00`
   - recall `0.9756`
   - false merges `0`
   - false splits `2`
   - answer rate `0.80`
   - accuracy `0.80`
2. `docs/runs/scale_test_llm_2026-04-01_132119.json`
   - precision `1.00`
   - recall `0.9009`
   - false merges `0`
   - false splits `11`
   - answer rate `0.80`
   - accuracy `0.80`

The critical instability families were:

1. `D.C.` / `Washington D.C.` / `Washington`
2. `4th POG` / `4th PSYOP Group`
3. `the Agency` / `CIA` / `Central Intelligence Agency`
4. `GWU` / `George Washington University` / `researchers at GWU`

## Landed Repairs

Plan `0039` intentionally stayed narrow.

Landed runtime repair slice:

1. bounded district-place bridge for unknown `D.C.` mentions;
2. bounded military-unit alias signature for `4th POG` ↔ `4th PSYOP Group`;
3. no new broad descriptor-only cross-document merge heuristic for
   `the Agency`.

The plan also classified `GWU` honestly instead of assuming it still needed
resolution work.

## Fresh Rerun Artifacts

Two new fresh reruns on new DBs were executed with
`LLM_CLIENT_TIMEOUT_POLICY=allow`:

1. `docs/runs/scale_test_llm_2026-04-01_145141.json`
   - precision `1.00`
   - recall `0.9643`
   - false merges `0`
   - false splits `4`
   - answer rate `1.00`
   - accuracy `1.00`
2. `docs/runs/scale_test_llm_2026-04-01_152927.json`
   - precision `1.00`
   - recall `0.9346`
   - false merges `0`
   - false splits `7`
   - answer rate `1.00`
   - accuracy `1.00`

## What Held Stable

The rerun-stability gate is now satisfied at the question/safety level:

1. both fresh reruns kept false merges at `0`;
2. both fresh reruns kept precision at `1.00`;
3. both fresh reruns answered all `10/10` fixed questions correctly.

That is enough to close Plan `0039` under its declared gate.

## What Did Not Fully Stabilize

Pairwise recall still moves across fresh reruns:

1. `145141` had `4` false splits;
2. `152927` had `7` false splits.

The residuals are now narrower and better understood:

1. `the Agency` remains the dominant descriptor-only false-split family;
2. `Washington D.C.` / `Washington` / `D.C.` can still reopen at the pairwise
   level even when the fixed questions stay green;
3. `GWU` is no longer a question blocker in the successful reruns;
4. `4th POG` no longer reopens as a benchmark blocker on the successful reruns.

## Interpretation

The repo now has repeatable fresh-run evidence that the entity-resolution path
is stable enough for the current fixed-question gate and the zero-false-merge
floor.

It does **not** yet have a claim that pairwise false splits are fully stable
across extraction-shape drift. That stronger claim would require more hardening,
especially around descriptor-only organization mentions and place-family drift.

Those are now follow-on quality questions, not blockers for closing this
bounded rerun-stability block.

## Decision

1. close Plan `0039` as complete;
2. treat Plan `0025` Phase 4 value proof as complete enough on its declared
   acceptance criteria;
3. keep exact matching as the safe default floor and do not claim that LLM
   clustering is ready to become the repo default purely from these reruns;
4. treat remaining descriptor-only and place-family pairwise drift as future
   hardening work, not as unfinished `0039` scope.

## Next Step

Move the active frontier away from entity-resolution rerun triage and onto the
next explicit program gate, with extraction-transfer proof under Plan `0014`
as the highest-value next candidate.

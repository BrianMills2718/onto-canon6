# 2026-04-01 Entity Resolution Recall Recovery Rerun

Source artifact:
- `docs/runs/scale_test_llm_2026-04-01_083207.json`

State DB:
- `var/scale_test_llm_recovery/scale_test.sqlite3`

Plan context:
- `docs/plans/0032_24h_entity_resolution_recall_recovery_block.md`

## Decision

Plan 0032 succeeded on its declared gate.

The refreshed LLM run now clears all bounded recovery thresholds:

1. all `25` source documents survived extraction;
2. precision is `1.00` (gate: `>= 0.95`);
3. recall is `0.615` (gate: `>= 0.40`);
4. false merges are `0` (gate: `<= 2`);
5. fixed-question answer rate is `0.50` (gate: `>= 0.50`);
6. fixed-question accuracy over all questions is `0.40` (gate: `>= 0.30`).

This block therefore closes as a success.

## Before / After

Compared to the Plan 0031 hardened LLM rerun:

- precision: `1.00` -> `1.00`
- recall: `0.308` -> `0.615`
- false merges: `0` -> `0`
- answer rate: `0.20` -> `0.50`
- accuracy over all questions: `0.20` -> `0.40`

The recovery was real, not cosmetic:

1. response-level extraction salvage removed the prior document-loss failure;
2. deterministic post-LLM alias collapse materially improved org/person
   answerability;
3. the same-surname person safety floor from Plan 0031 stayed intact.

## What Passed

### Document survival

`candidate_assertions.source_ref` covered all `25` docs:

`doc_01` through `doc_25`

### Resolution summary

- entities scanned: `111`
- groups found: `77`
- identities created: `77`
- aliases attached: `34`

### Question results

Correctly answered:

1. `q02` — `USSOCOM` / `U.S. Special Operations Command`
2. `q03` — `Adm. Olson` / `Eric Olson`
3. `q07` — `Gen. J. Smith`
4. `q10` — `Lt. Gen. Michael Torres`

Incorrect or unanswered:

1. `q01` — `Gen. Smith` / `General John Smith`
2. `q04` — `Ft. Bragg` / `Fort Liberty`
3. `q05` — `General John Smith` / `James Smith`
4. `q06` — `Washington` / `George Washington University`
5. `q08` — `the Agency`
6. `q09` — `GWU`

## Remaining Failure Families

The remaining misses are now narrower than the Plan 0031 frontier.

### 1. Type-divergent mention surfaces

Two benchmark-critical aliases still fail because extraction emits different
semantic types for what should remain answerable through one real-world entity:

1. `Gen. Smith` appears both as:
   - `oc:person` (matched)
   - `oc:military_rank` (unmatched)
2. `Ft. Bragg` / `Fort Liberty` appear as:
   - `oc:location`
   - `oc:military_organization`

This is no longer a false-merge problem. It is a type-family consistency and
answerability problem.

### 2. Alias phrases absent from promoted observations

`the Agency` and `GWU` were not present as promoted observed names in the final
artifact. The question failures for `q08` and `q09` therefore remain upstream
of clustering. This is an extraction / canonical mention coverage problem, not
just a clustering problem.

### 3. Washington / university ambiguity

`Washington` still resolves only to a city observation in the current artifact,
while `George Washington University` never appears as a promoted matched
observation. The benchmark failure remains a missing university-side mention
surface, not an unsafe merge.

## Residual Caveats

The rerun still logged extraction validation errors from malformed candidate
payloads:

- unsupported filler kind: `event`
- malformed unknown filler requiring `raw`

These errors no longer caused document loss because the response-level salvage
path now preserves valid siblings. The error family is therefore downgraded
from gate blocker to ongoing extraction noise.

## Recommendation

Do not promote the LLM strategy as the unconditional default yet.

Plan 0032 proved that the LLM path can now be both safe and materially better
than the earlier hardened run, but the remaining misses are concentrated in a
small set of still-important answerability families:

1. typed mention-family divergence (`person` vs `rank`, `installation` vs
   `location` / `organization`);
2. alias coverage gaps for elided or abbreviated organization names;
3. university / place ambiguity.

The next bounded block should target those families directly rather than
broadening prompt churn or changing the evaluation rules.

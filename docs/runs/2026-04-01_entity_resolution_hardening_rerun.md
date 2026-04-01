# 2026-04-01 Entity Resolution Hardening Rerun

## Scope

Decision note for the post-Plan-0030 hardening reruns executed under
`docs/plans/0031_24h_entity_resolution_hardening_block.md`.

Compared surfaces:

1. previous exact run from Plan 0030
2. hardened exact rerun
3. previous LLM run from Plan 0030
4. hardened LLM rerun

## Artifacts

1. `docs/runs/2026-04-01_entity_resolution_value_proof.md`
2. `docs/runs/scale_test_exact_2026-04-01_073211.json`
3. `docs/runs/scale_test_llm_2026-04-01_074236.json`

## Commands

```bash
PYTHONPATH=src python scripts/run_scale_test.py \
  --strategy exact \
  --db-dir var/scale_test_exact_hardened \
  --model-override gemini/gemini-2.5-flash-lite \
  --judge-model-override gemini/gemini-2.5-flash-lite

PYTHONPATH=src python scripts/run_scale_test.py \
  --strategy llm \
  --db-dir var/scale_test_llm_hardened \
  --model-override gemini/gemini-2.5-flash-lite \
  --judge-model-override gemini/gemini-2.5-flash-lite \
  --resolution-model-override gemini/gemini-2.5-flash-lite
```

## Hardening Gate Result

Plan 0031 succeeded on safety hardening and failed on default-promotion
readiness.

Passed:

1. stale auto-review judge path fixed and rerun with explicit bounded judge
   override;
2. prior same-surname person false-merge family eliminated;
3. no new broad false-merge family replaced it;
4. LLM precision rose above the gate floor (`1.00` vs target `>= 0.93`);
5. false merges fell to zero (`0` vs target `<= 2`).

Failed:

1. LLM recall did not meet the promotion target (`0.308` vs target `>= 0.50`);
2. fixed-question answerability regressed sharply (`0.20` answer rate vs
   `0.50` in Plan 0030 and `0.80` for hardened exact);
3. one extraction/schema failure dropped `doc_06` from the LLM rerun entirely.

## Metric Comparison

| Strategy | Precision | Recall | False merges | False splits | Matched obs | Unmatched obs | Ambiguous obs | Answer rate | Accuracy (all) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| exact (Plan 0030) | 1.00 | 0.204 | 0 | 43 | 36 | 68 | 5 | 0.80 | 0.40 |
| exact (hardened) | 1.00 | 0.244 | 0 | 59 | 40 | 48 | 5 | 0.80 | 0.40 |
| llm (Plan 0030) | 0.85 | 0.500 | 6 | 34 | 56 | 56 | 2 | 0.50 | 0.30 |
| llm (hardened) | 1.00 | 0.308 | 0 | 92 | 47 | 58 | 6 | 0.20 | 0.20 |

## What Improved

### 1. Same-surname false merges are no longer the blocking failure family

The hardened LLM rerun produced `0` false merges. The prior `John Smith` /
`James Smith` overmerge family was eliminated, which is the main intended
effect of the new deterministic person-name postprocessing.

### 2. Exact remains a clean precision floor

The hardened exact rerun improved recall modestly (`0.204` -> `0.244`) while
keeping zero false merges and preserving the same fixed-question accuracy
(`0.40`).

### 3. Judge-path caveat is narrowed truthfully

The reruns were executed with explicit bounded judge overrides and no longer
depend on the stale `_judge_candidate()` path caveat that affected the Plan
0030 note.

## What Still Fails

### 1. Alias-heavy recall is still too weak for LLM default promotion

Representative surviving false-split families in the hardened LLM run:

1. `Special Operations Command` vs `USSOCOM`
2. `Special Operations Command` vs `U.S. Special Operations Command`
3. `Ft. Bragg` vs `Fort Liberty`
4. `Adm. Olson` vs `Eric Olson`
5. `GWU` vs `George Washington University`
6. `the Agency` vs the CIA family

The hardening block removed the unsafe merges, but the current system is still
too conservative to recover enough true aliases.

### 2. Question answerability regressed

In the hardened LLM run:

1. `q01`-`q06` all became unanswered because one or both mentions could not be
   mapped to a unique predicted cluster;
2. only the two canonical-entity lookup questions with already-clean mentions
   (`q07` and `q10`) still answered correctly.

This means pairwise precision alone is not enough. The strategy must also
produce stable unique-cluster outcomes for the benchmark questions.

### 3. One extraction/schema failure contaminated the LLM rerun

`make errors DAYS=1 LIMIT=5` showed one same-day extraction validation failure:

1. `unsupported filler kind: 'event'`
2. `unknown fillers require raw`

The hardened exact DB contains all `25` source documents, but the hardened LLM
DB contains only `24`; `doc_06` is missing from
`candidate_assertions.source_ref`. This is a real caveat and should be fixed,
but it does not explain the whole recall gap because the dominant remaining
failures are alias/unique-cluster splits across many other documents.

## Decision

LLM resolution is still **not promotable as the default strategy**.

Current strategy posture:

1. keep `exact` as the default precision floor;
2. keep the hardened LLM path available as an experimental strategy;
3. treat the next active work as recall/answerability hardening, not more
   false-merge blocking.

## Next Narrow Work

1. fix the extraction schema failure family that emitted `kind: "event"` and
   dropped `doc_06`;
2. improve alias recovery for the benchmark-critical organization and
   installation families;
3. improve unique-cluster resolution for abbreviated person mentions without
   reintroducing same-surname overmerges;
4. rerun the same fixed corpus only after those failure families change.

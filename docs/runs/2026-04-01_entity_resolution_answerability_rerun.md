# 2026-04-01 Entity Resolution Answerability Rerun

Artifact:
- `docs/runs/scale_test_llm_2026-04-01_092444.json`

State ref:
- `var/scale_test_llm_answerability/scale_test.sqlite3`

## Outcome

This rerun is decision-useful but not gate-valid.

It localized the remaining answerability work, but it did **not** satisfy the
Plan 0033 gate because the run lost 9 source documents to transient provider
connectivity failures during extraction.

Reported metrics from the artifact:

- precision: `1.00`
- recall: `0.6667`
- false merges: `0`
- false splits: `17`
- question answer rate: `0.60`
- question accuracy over all questions: `0.50`
- extraction summary: `71 extracted / 71 pending / 9 errors`

Observed surviving source refs:

- `doc_01` through `doc_13`
- `doc_23` through `doc_25`

Missing from the promoted surface because extraction failed mid-run:

- `doc_14`
- `doc_15`
- `doc_16`
- `doc_17`
- `doc_18`
- `doc_19`
- `doc_20`
- `doc_21`
- `doc_22`

## Why The Gate Did Not Clear

1. **Measurement invalidity**
   - The run did not satisfy the `25/25` document-survival requirement.
   - `make errors DAYS=1 LIMIT=20` showed repeated extraction failures with:
     `litellm.APIConnectionError: GeminiException - [Errno -3] Temporary failure in name resolution`
   - This was a provider/network failure family, not a schema-validation failure.

2. **Real surviving logic miss**
   - `q04` remained wrong:
     - prompt: `Do 'Ft. Bragg' and 'Fort Liberty' refer to the same installation?`
     - predicted answer: `False`
   - Because the run lost `doc_21`, this is still partially confounded. A clean
     rerun is needed before deciding whether this requires a new installation
     equivalence rule or just complete evidence.

3. **Real type-family miss**
   - `q09` remained unanswered:
     - prompt: `Which canonical entity does 'GWU' resolve to?`
   - The surviving promoted observation was `oc:university`, but the ground-truth
     fixture expects `oc:educational_institution`. This is a real family
     compatibility gap, not a measurement artifact.

## Question-Level Snapshot

Answered and correct:

- `q01`
- `q02`
- `q03`
- `q07`
- `q08`

Answered but incorrect:

- `q04`

Unanswered:

- `q05`
- `q06`
- `q09`
- `q10`

## Decision

Plan 0033 is complete in the sense required by its own exit clause: the
remaining miss is explicit and localized.

The next active block must do three things in order:

1. make the measurement harness resilient enough to recover from transient
   extraction failures without silently accepting partial corpora;
2. repair the institution-family compatibility gap (`oc:university` ↔
   `oc:educational_institution`);
3. rerun on a clean corpus and only then decide whether the installation rename
   family (`Ft. Bragg` / `Fort Liberty`) needs new merge logic.

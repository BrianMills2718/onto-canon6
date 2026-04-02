# 2026-04-01 Entity Resolution Clean Measurement

## Purpose

Record the first measurement-valid rerun after Plan 0034 repaired harness
resilience and institution-family compatibility.

## Command

```bash
PYTHONPATH=src python scripts/run_scale_test.py \
  --strategy llm \
  --db-dir var/scale_test_llm_clean_measurement \
  --model-override gemini/gemini-2.5-flash-lite \
  --judge-model-override gemini/gemini-2.5-flash-lite \
  --resolution-model-override gemini/gemini-2.5-flash-lite \
  --retry-failed-docs 2 \
  --retry-delay-seconds 10
```

## Artifact

1. `docs/runs/scale_test_llm_2026-04-01_100114.json`
2. `var/scale_test_llm_clean_measurement/scale_test.sqlite3`

## Verified Outcome

1. all `25/25` source documents survived extraction;
2. extraction reported `errors: 0`, `transient_failures: 0`,
   `failed_docs: []`, and `recovered_docs: []`;
3. `108` candidate assertions were extracted;
4. `97` assertions were promoted;
5. `100` promoted entities were scanned;
6. `60` identity groups were formed with `40` alias attachments.

## Metrics

Pairwise:

1. precision `1.00`
2. recall `0.746`
3. false merges `0`
4. false splits `32`
5. unmatched observations `44`
6. ambiguous observations `3`

Question summary:

1. answer rate `0.80`
2. accuracy over all questions `0.70`

## Remaining Misses

1. `q02` unanswered:
   - `USSOCOM` observations all landed in one predicted cluster;
   - one `U.S. Special Operations Command` observation still landed in a
     separate predicted cluster because it carried a generic / missing entity
     type and therefore never joined the organization family.
2. `q04` wrong:
   - `Ft. Bragg` matched ground-truth `E005`;
   - `Fort Liberty` also matched ground-truth `E005`;
   - the two mentions still remained in different predicted clusters, so this
     is now a pure installation rename / redesignation equivalence miss.
3. `q08` unanswered:
   - `the Agency` remained unmatched;
   - the observed type was `oc:government_agency`;
   - the ground-truth type is `oc:government_organization`;
   - this is now a conservative organization-family compatibility gap, not a
     corpus-loss or measurement-hygiene issue.

## Decision

Plan 0034 is complete: the rerun is now measurement-valid and the remaining
misses are explicit and localized.

The next bounded block is:

1. `docs/plans/0035_24h_entity_resolution_alias_family_completion_block.md`

That block owns only the three residual misses above.

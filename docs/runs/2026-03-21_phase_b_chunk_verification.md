# Run Summary: 2026-03-21 Phase B Chunk Verification

## Purpose

Verify that the winning Phase A prompt guidance helps on a real Stage 1
document slice through the operational `extract-text` CLI path, not just on
the prompt-eval fixture.

This was intentionally a bounded run:

1. one real Stage 1 report,
2. deterministic chunking,
3. one real chunk,
4. one live extraction call.

## Source Slice

Copied from the earlier `onto-canon` lineage:

- `../onto-canon/research_outputs/stage1/stage1_query2_20251118_122424.md`

Bounded live extraction target:

- `var/real_runs/2026-03-21_phase_b_prompt_verification/chunks/01_stage1_query2/01_stage1_query2__chunk_002.md`

The selected chunk includes:

1. the USSOCOM commanders table,
2. the PSYOP Group Commanders narrative,
3. Operation Enduring Freedom / Iraqi Freedom headings,
4. Joint PSYOP Task Force discussion,
5. one named concern-style sentence from the NDU review.

## Runtime

### Slow default lane

- project: `onto-canon6-phase-b-2026-03-21`
- task: `fast_extraction`
- prompt ref: `onto_canon6.extraction.text_to_candidate_assertions@1`
- timeout policy: `ban`

### Bounded operational lane

- project: `onto-canon6-phase-b-2026-03-21-budget`
- task: `budget_extraction`
- prompt ref: `onto_canon6.extraction.text_to_candidate_assertions@1`
- timeout policy: `ban`
- review db: `var/real_runs/2026-03-21_phase_b_prompt_verification/review_state_budget.sqlite3`
- overlay root: `var/real_runs/2026-03-21_phase_b_prompt_verification/overlays_budget`
- output artifact:
  `var/real_runs/2026-03-21_phase_b_prompt_verification/outputs/01_stage1_query2__chunk_002_budget_extract.json`

## What Happened

The first live run used the existing `extract-text` operational surface with
its config-default task. Observability showed:

- `activity_state="waiting"`
- `process_alive=True`
- repeated 15-second heartbeats
- no orphaning or false “progressing” claim

That part was healthy. But the call remained in that truthful waiting state
for more than five minutes on a single chunk and was not useful for bounded
verification.

This exposed an operational gap rather than a model-runtime failure: the CLI
did not previously allow a task override even though the prompt-eval lane was
already proving that `budget_extraction` was the viable bounded path.

After adding `--selection-task` to `extract-text`, the same real chunk was
rerun on `budget_extraction` and completed successfully.

## Results

The bounded rerun persisted `10` valid candidates and `0` proposals.

Predicate counts:

- `oc:hold_command_role`: `5`
- `oc:belongs_to_organization`: `1`
- `oc:operation_occurs_in_location`: `2`
- `oc:use_organizational_form`: `1`
- `oc:express_concern`: `1`

Good signs:

1. the commanders table produced clean `oc:hold_command_role` rows for all
   five commanders
2. the PSYOP Group narrative yielded one `oc:belongs_to_organization`
   candidate instead of the earlier role/predicate confusions
3. the operation headings produced two straightforward
   `oc:operation_occurs_in_location` candidates
4. every persisted candidate in the bounded lane was structurally valid

Remaining semantic review concerns:

1. `oc:use_organizational_form` for “the establishment of Joint PSYOP Task
   Forces (JPOTF)” is still likely a predicate misfit
2. `oc:express_concern` over the NDU review sentence may still be too loose a
   speaker/topic interpretation even though the speaker is now explicitly
   named

## Review Outcome

The bounded review pass accepted `8` of the `10` candidates and rejected `2`,
for an `80%` acceptance rate on this real chunk.

Accepted:

1. all five `oc:hold_command_role` commander-table rows
2. both `oc:operation_occurs_in_location` operation headings
3. the NDU-review `oc:express_concern` candidate

Rejected:

1. the `4th PSYOP Group -> USSOCOM` `oc:belongs_to_organization` candidate,
   because this chunk does not directly support the USSOCOM membership claim
2. the JPOTF `oc:use_organizational_form` candidate, because the cited text
   supports establishment/integration language rather than organizational-form
   usage

This is materially better than the broader first Stage 1 run's `6/16`
acceptance rate, though it is not directly comparable as a benchmark because
this is one bounded chunk and not the whole earlier corpus.

## Decision

Phase B real-document verification is now past the “can the operational path
run at all?” question.

The next useful question is narrower:

1. which of the `10` bounded candidates are actually review-worthy on a real
   analyst chunk, and
2. whether the remaining misses justify prompt iteration, stricter reviewer
   policy, or later filler/predicate changes.

Until there is stronger evidence to change the repo-wide default task,
bounded real-document verification should use:

```bash
./.venv/bin/python -m onto_canon6 extract-text ... --selection-task budget_extraction
```

instead of waiting on the slower `fast_extraction` default.

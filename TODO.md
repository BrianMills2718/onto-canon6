# TODO

## Current 24h Execution Block

Source of truth:
- `docs/plans/0037_24h_entity_resolution_false_split_cleanup_block.md`

### Phase 1 — Freeze The Residual False-Split Contract
- [x] Close Plan 0036 truthfully in the docs
- [x] Activate Plan 0037 and freeze the residual false-split families
- [x] Commit verified phase

### Phase 2 — Repair The Rodriguez Title Family
- [x] Localize exactly why `Col. Rodriguez` stays outside the current cluster
- [x] Land one conservative titled-surname bridge repair for the Rodriguez family
- [x] Add/update targeted regression tests
- [x] Commit verified phase

### Phase 3 — Repair The Washington Place Family
- [ ] Localize exactly why `Washington` still splits from `Washington D.C.` / `D.C.`
- [ ] Land one bounded place-family repair
- [ ] Add/update targeted regression tests
- [ ] Commit verified phase

### Phase 4 — Rerun The Value Proof
- [ ] Rerun LLM strategy on a fresh DB
- [ ] Verify 25/25 document survival from the DB
- [ ] Check the zero-false-split gate while preserving zero false merges and 10/10 question accuracy
- [ ] Commit verified phase

### Phase 5 — Closeout
- [ ] Refresh docs/status/handoff
- [ ] Mark execution block complete
- [ ] Commit verified phase

## Most Recent Completed 24h Execution Block

Source of truth:
- `docs/plans/0036_24h_entity_resolution_negative_control_recovery_block.md`

### Phase 1 — Freeze The Fresh-Run Residual Contract
- [x] Close Plan 0035 truthfully in the docs
- [x] Activate Plan 0036 and freeze the fresh-run residuals (`q05`, `q06`)
- [x] Commit verified phase

### Phase 2 — Restore Same-Surname Person Safety
- [x] Localize the fresh-run `John Smith` / `James Smith` overmerge precisely
- [x] Tighten titled-person bridge logic without undoing positive title/initial merges
- [x] Add/update targeted tests
- [x] Commit verified phase

### Phase 3 — Recover The Remaining Negative-Control Answerability
- [x] Localize the residual `q06` unmatched/ambiguous path after Phase 2
- [x] Land one bounded repair only if the residual is explicit
- [x] Add/update targeted regression tests
- [x] Commit verified phase

### Phase 4 — Rerun The Value Proof
- [x] Rerun LLM strategy on a fresh DB
- [x] Verify 25/25 document survival from the DB
- [x] Check the gate for `q05` and `q06` while preserving `q02` / `q04` / `q08`
- [x] Commit verified phase

### Phase 5 — Closeout
- [x] Refresh docs/status/handoff
- [x] Mark execution block complete
- [x] Commit verified phase

## Next Active Work

Source of truth:
- `docs/plans/0025_cross_document_entity_resolution.md`

- [x] Close the three residual misses from the clean-measurement baseline (`q02`, `q04`, `q08`)
- [x] Preserve the `25/25` extraction-survival baseline while rerunning
- [x] Restore fresh-run same-surname safety while preserving the `q02` / `q04` / `q08` wins
- [x] Get `q05` back to answered-and-correct and localize/fix `q06`
- [ ] Keep precision at or above `0.95` with zero false merges
- [ ] Clear the remaining Rodriguez and Washington false splits
- [ ] Refresh the decision note and close the active 24h block truthfully

## Longer-Term Queue

- [ ] Re-evaluate whether LLM clustering should replace exact strategy as default after the next answerability hardening pass
- [ ] Evaluate whether Plan 0028 should widen beyond the first five operations
- [ ] Revisit consumer-blocked richer DIGIMON interchange only through DIGIMON Plan 23
- [ ] Revisit trusted bulk ingestion only if a real workflow makes review the bottleneck

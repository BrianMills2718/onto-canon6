# TODO

## Current 24h Execution Block

Source of truth:
- `docs/plans/0034_24h_entity_resolution_clean_measurement_block.md`

### Phase 1 — Freeze The Clean-Measurement Contract
- [ ] Record the Plan 0033 outcome and activate Plan 0034
- [ ] Freeze the remaining failure classes and thresholds
- [ ] Commit verified phase

### Phase 2 — Harden Measurement Hygiene
- [ ] Localize run-scale extraction failure handling
- [ ] Add bounded failed-doc retry behavior
- [ ] Add/update focused tests
- [ ] Commit verified phase

### Phase 3 — Repair Institution-Family Compatibility
- [ ] Land the bounded `university` / institution family fix
- [ ] Add/update targeted tests
- [ ] Keep the existing safety families green
- [ ] Commit verified phase

### Phase 4 — Run One Clean Rerun
- [ ] Rerun LLM strategy on a fresh DB
- [ ] Verify 25/25 document survival from the DB
- [ ] Decide whether installation-equivalence work is still needed
- [ ] Commit verified phase

### Phase 5 — Conditional Installation-Equivalence Repair And Closeout
- [ ] If needed, add the bounded `Ft. Bragg` / `Fort Liberty` repair
- [ ] Rerun after the repair if Phase 4 still misses `q04`
- [ ] Refresh docs/status/handoff
- [ ] Mark execution block complete
- [ ] Commit verified phase

## Most Recent Completed 24h Execution Block

Source of truth:
- `docs/plans/0032_24h_entity_resolution_recall_recovery_block.md`

### Phase 1 — Freeze The Recovery Contract
- [x] Make Plan 0032 the active execution surface
- [x] Freeze the targeted failure families and thresholds
- [x] Commit verified phase

### Phase 2 — Remove Extraction Document Loss
- [x] Reproduce and localize the `event` / malformed-unknown extraction failure
- [x] Fix the boundary so one malformed candidate does not lose a whole doc
- [x] Add/update targeted tests
- [x] Commit verified phase

### Phase 3 — Recover Alias And Answerability Families
- [x] Improve org / installation alias handling
- [x] Improve abbreviated person unique-cluster handling
- [x] Keep the same-surname safety family green
- [x] Add/update targeted regression tests
- [x] Commit verified phase

### Phase 4 — Refresh The LLM Value Proof
- [x] Rerun LLM strategy on a fresh DB
- [x] Write refreshed decision-grade run note
- [x] Commit verified phase

### Phase 5 — Closeout
- [x] Refresh docs/status/handoff
- [x] Mark execution block complete
- [x] Commit verified phase

## Next Active Work

Source of truth:
- `docs/plans/0025_cross_document_entity_resolution.md`

- [ ] Make the value-proof harness robust against transient failed-doc runs
- [ ] Repair `oc:university` / educational-institution compatibility
- [ ] Get one clean 25/25 answerability rerun on the fixed corpus
- [ ] Decide whether bounded installation-equivalence work is still needed only
      after the clean rerun

## Longer-Term Queue

- [ ] Re-evaluate whether LLM clustering should replace exact strategy as default after the next answerability hardening pass
- [ ] Evaluate whether Plan 0028 should widen beyond the first five operations
- [ ] Revisit consumer-blocked richer DIGIMON interchange only through DIGIMON Plan 23
- [ ] Revisit trusted bulk ingestion only if a real workflow makes review the bottleneck

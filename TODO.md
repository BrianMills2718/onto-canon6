# TODO

## Current 24h Execution Block

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
- [ ] Commit verified phase

### Phase 3 — Recover Alias And Answerability Families
- [ ] Improve org / installation alias handling
- [ ] Improve abbreviated person unique-cluster handling
- [ ] Keep the same-surname safety family green
- [ ] Add/update targeted regression tests
- [ ] Commit verified phase

### Phase 4 — Refresh The LLM Value Proof
- [ ] Rerun LLM strategy on a fresh DB
- [ ] Write refreshed decision-grade run note
- [ ] Commit verified phase

### Phase 5 — Closeout
- [ ] Refresh docs/status/handoff
- [ ] Mark execution block complete
- [ ] Commit verified phase

## Most Recent Completed 24h Execution Block

Source of truth:
- `docs/plans/0031_24h_entity_resolution_hardening_block.md`

- [x] Judge-path parity fixed
- [x] Same-surname false-merge family removed
- [x] Fresh exact + LLM reruns recorded
- [x] Decision note written and block closed

## Next Active Work

Source of truth:
- `docs/plans/0025_cross_document_entity_resolution.md`

- [ ] Fix the extraction/schema failure family that emitted `kind: \"event\"`
- [ ] Improve alias recovery for benchmark-critical org / installation families
- [ ] Improve unique-cluster resolution for abbreviated people without
      reintroducing same-surname overmerges
- [ ] Decide the next bounded execution block only after the above frontier is
      written as an explicit phase plan

## Longer-Term Queue

- [ ] Re-evaluate whether LLM clustering should replace exact strategy as default after the next recall/answerability hardening pass
- [ ] Evaluate whether Plan 0028 should widen beyond the first five operations
- [ ] Revisit consumer-blocked richer DIGIMON interchange only through DIGIMON Plan 23
- [ ] Revisit trusted bulk ingestion only if a real workflow makes review the bottleneck

# TODO

## Current 24h Execution Block

Source of truth:
- `docs/plans/0035_24h_entity_resolution_alias_family_completion_block.md`

### Phase 1 — Freeze The Residual Failure Contract
- [ ] Record the Plan 0034 clean-measurement baseline and activate Plan 0035
- [ ] Freeze the three residual failure families and thresholds
- [ ] Commit verified phase

### Phase 2 — Repair Organization-Family Drift
- [ ] Add `government_agency` ↔ `government_organization` compatibility
- [ ] Add bounded name-aware organization-family inference for missing / generic entity types
- [ ] Add/update targeted tests
- [ ] Commit verified phase

### Phase 3 — Land The Bounded Installation-Equivalence Repair
- [ ] Localize the surviving `Ft. Bragg` / `Fort Liberty` split at the grouping level
- [ ] Add one bounded installation rename / redesignation repair
- [ ] Add/update targeted tests
- [ ] Commit verified phase

### Phase 4 — Rerun The Value Proof
- [ ] Rerun LLM strategy on a fresh DB
- [ ] Verify 25/25 document survival from the DB
- [ ] Check the gate for `q02`, `q04`, and `q08`
- [ ] Commit verified phase

### Phase 5 — Closeout
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

- [ ] Close the three residual misses from the clean-measurement baseline (`q02`, `q04`, `q08`)
- [ ] Preserve the `25/25` extraction-survival baseline while rerunning
- [ ] Keep precision at or above `0.95` with zero false merges
- [ ] Refresh the decision note and close the active 24h block truthfully

## Longer-Term Queue

- [ ] Re-evaluate whether LLM clustering should replace exact strategy as default after the next answerability hardening pass
- [ ] Evaluate whether Plan 0028 should widen beyond the first five operations
- [ ] Revisit consumer-blocked richer DIGIMON interchange only through DIGIMON Plan 23
- [ ] Revisit trusted bulk ingestion only if a real workflow makes review the bottleneck

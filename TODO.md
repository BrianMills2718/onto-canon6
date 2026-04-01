# TODO

## Current 24h Execution Block

Source of truth:
- `docs/plans/0033_24h_entity_resolution_answerability_block.md`

### Phase 1 — Freeze The Answerability Contract
- [x] Make Plan 0033 the active execution surface
- [x] Freeze the targeted failure families and thresholds
- [x] Commit verified phase

### Phase 2 — Repair Type-Divergent Mention Families
- [ ] Localize the benchmark-critical type drift
- [ ] Implement a bounded family-level fix
- [ ] Add/update targeted tests
- [ ] Commit verified phase

### Phase 3 — Recover Missing Alias Surfaces
- [ ] Localize why aliases like `the Agency` / `GWU` do not survive
- [ ] Implement a bounded family-level fix
- [ ] Add/update targeted tests
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
- [ ] Commit verified phase

## Next Active Work

Source of truth:
- `docs/plans/0025_cross_document_entity_resolution.md`

- [ ] Repair type-divergent mention families without weakening safety
- [ ] Recover missing alias surfaces for benchmark-critical abbreviations and
      elided references
- [ ] Refresh the fixed-question value proof after those families land
- [ ] Decide whether LLM is now a plausible default candidate only after the
      next bounded block

## Longer-Term Queue

- [ ] Re-evaluate whether LLM clustering should replace exact strategy as default after the next answerability hardening pass
- [ ] Evaluate whether Plan 0028 should widen beyond the first five operations
- [ ] Revisit consumer-blocked richer DIGIMON interchange only through DIGIMON Plan 23
- [ ] Revisit trusted bulk ingestion only if a real workflow makes review the bottleneck

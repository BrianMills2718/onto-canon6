# TODO

## Most Recent 24h Execution Block

Source of truth:
- `docs/plans/0031_24h_entity_resolution_hardening_block.md`

### Phase 1 — Freeze The Hardening Contract
- [x] Make Plan 0031 the active execution surface
- [x] Freeze the targeted failure families and thresholds
- [x] Commit verified phase

### Phase 2 — Fix Auto-Review Judge Parity
- [x] Remove or modernize the stale `_judge_candidate()` path
- [x] Ensure explicit `judge_model_override` is honored in auto-review
- [x] Add/update tests for the seam
- [x] Commit verified phase

### Phase 3 — Harden Resolution Decisions
- [x] Add deterministic same-surname person disambiguation
- [x] Make resolution type compatibility hierarchy-aware or override-aware
- [x] Strengthen prompt or post-LLM validation accordingly
- [x] Add targeted regression tests
- [x] Commit verified phase

### Phase 4 — Refresh The Value Proof
- [x] Rerun exact strategy on a fresh DB
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

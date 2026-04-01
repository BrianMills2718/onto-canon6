# TODO

## Current 24h Execution Block

Source of truth:
- `docs/plans/0031_24h_entity_resolution_hardening_block.md`

### Phase 1 — Freeze The Hardening Contract
- [ ] Make Plan 0031 the active execution surface
- [ ] Freeze the targeted failure families and thresholds
- [ ] Commit verified phase

### Phase 2 — Fix Auto-Review Judge Parity
- [ ] Remove or modernize the stale `_judge_candidate()` path
- [ ] Ensure explicit `judge_model_override` is honored in auto-review
- [ ] Add/update tests for the seam
- [ ] Commit verified phase

### Phase 3 — Harden Resolution Decisions
- [ ] Add deterministic same-surname person disambiguation
- [ ] Make resolution type compatibility hierarchy-aware or override-aware
- [ ] Strengthen prompt or post-LLM validation accordingly
- [ ] Add targeted regression tests
- [ ] Commit verified phase

### Phase 4 — Refresh The Value Proof
- [ ] Rerun exact strategy on a fresh DB
- [ ] Rerun LLM strategy on a fresh DB
- [ ] Write refreshed decision-grade run note
- [ ] Commit verified phase

### Phase 5 — Closeout
- [ ] Refresh docs/status/handoff
- [ ] Mark execution block complete
- [ ] Commit verified phase

## Longer-Term Queue

- [ ] Decide whether LLM clustering should replace exact strategy as default
- [ ] Evaluate whether Plan 0028 should widen beyond the first five operations
- [ ] Revisit consumer-blocked richer DIGIMON interchange only through DIGIMON Plan 23
- [ ] Revisit trusted bulk ingestion only if a real workflow makes review the bottleneck

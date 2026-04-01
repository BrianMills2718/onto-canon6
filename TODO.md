# TODO

## Current 24h Execution Block

Source of truth:
- `docs/plans/0030_24h_entity_resolution_value_proof_block.md`

### Phase 1 — Freeze Corpus And Evaluation Contracts
- [x] Add fixed cross-document question fixture
- [x] Make scoring rules explicit in code/docs
- [x] Define baseline report shape
- [x] Commit verified phase

### Phase 2 — Implement Decision-Grade Evaluator
- [x] Add typed evaluation models
- [x] Implement ground-truth matching
- [x] Implement precision/recall + false-merge/false-split reporting
- [x] Add evaluator tests
- [x] Commit verified phase

### Phase 3 — Upgrade Runners And Operator Surface
- [x] Upgrade `scripts/run_scale_test.py`
- [x] Add bare-baseline corpus runner
- [x] Add/refresh Make targets
- [ ] Commit verified phase

### Phase 4 — Execute The First Full Value-Proof Slice
- [x] Run exact-strategy report
- [x] Run bare baseline report
- [ ] Run LLM-strategy report if environment supports it cleanly
- [ ] Write run note with concrete findings
- [ ] Commit verified phase

### Phase 5 — Closeout
- [ ] Refresh docs/status/handoff
- [ ] Mark execution block complete
- [ ] Commit verified phase

## Longer-Term Queue

- [ ] Finish Plan 0025 value proof
- [ ] Decide whether LLM clustering should replace exact strategy as default
- [ ] Evaluate whether Plan 0028 should widen beyond the first five operations
- [ ] Revisit consumer-blocked richer DIGIMON interchange only through DIGIMON Plan 23
- [ ] Revisit trusted bulk ingestion only if a real workflow makes review the bottleneck

# TODO

## Current 24h Execution Block

Source of truth:
- `docs/plans/0060_24h_limit_capability_enforcement_block.md`

### Phase 1 — Freeze The Remaining Family
- [x] Close Plan `0059` truthfully
- [x] Freeze the exact remaining chunk-003 accepted claims
- [x] Record the governing local benchmark cases for this family
- [ ] Commit verified phase

### Phase 2 — Land One Bounded Enforcement Seam
- [ ] Add one deterministic guard for the remaining abstract `limit_capability` family
- [ ] Keep the rule family-level, not row-specific
- [ ] Commit verified phase

### Phase 3 — Verify The Enforcement Seam
- [ ] Add/update targeted tests for the enforcement seam
- [ ] Verify the family through the narrow test slice
- [ ] Commit verified phase

### Phase 4 — Rerun Chunk 002 And Chunk 003
- [ ] Rerun chunk `002` under the bounded enforcement seam
- [ ] Rerun chunk `003` under the bounded enforcement seam
- [ ] Export both reviewed chunk-transfer reports
- [ ] Commit verified phase

### Phase 5 — Closeout
- [ ] Write the limit-capability enforcement decision note
- [ ] Refresh docs/status/handoff/knowledge
- [ ] Mark the block complete and name the next blocker explicitly
- [ ] Commit verified phase

## Most Recent Completed 24h Execution Block

Source of truth:
- `docs/plans/0045_24h_extraction_path_block.md`

### Phase 1 — Freeze The Extraction-Path Contract
- [x] Restate the Plan 0044 decision as the incoming contract
- [x] Freeze the current aligned-wrapper failure artifacts
- [x] Record chunk `002` as the regression guard only
- [x] Record the execution caveats (`PYTHONPATH=src`, run-id mapping)
- [x] Commit verified phase

### Phase 2 — Compare Extraction-Service Behavior Directly
- [x] Identify the remaining path differences after wrapper alignment
- [x] Capture those differences in a reproducible artifact
- [x] Separate extraction-path behavior from review amplification
- [x] Commit verified phase

### Phase 3 — Land One Narrow Diagnostic Aid
- [x] Implement the smallest helper or instrumentation needed to replay or summarize the extraction-path divergence
- [x] Add verification for that aid
- [x] Keep it bounded to extraction-path behavior
- [x] Commit verified phase

### Phase 4 — Classify The Dominant Blocker
- [x] Decide whether the remaining blocker is extraction-service behavior or review/judge behavior
- [x] Record secondary caveats separately
- [x] Commit the classification with artifacts
- [x] Commit verified phase

### Phase 5 — Closeout
- [x] Write the decision-grade extraction-path note
- [x] Refresh docs/status/handoff
- [x] Mark execution block complete
- [x] Commit verified phase

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
- `docs/plans/0014_extraction_quality_baseline.md`

- [x] Turn the current compact operational-parity lane into one explicit certification decision
- [x] Keep chunk `002` as the positive control and chunk `003` as the prose-heavy stress case
- [x] Make the live-vs-parity gap reproducible instead of aggregate-only
- [x] Decide whether the current candidate is promotable or still transfer-blocked
- [x] Narrow the remaining full-chunk prompt-eval/live residual into one dominant blocker family
- [x] Reduce the remaining semantic transfer residual to one bounded prompt-revision target
- [x] Localize the remaining same-model live-path divergence to one dominant surface
- [x] Test whether wrapper alignment materially narrows the same-model live-path divergence
- [x] Localize the remaining post-wrapper extraction-path divergence to one dominant surface
- [x] Localize and repair the remaining prompt-side parity residual through Plans `0046`-`0049`
- [x] Run one bounded post-parity semantic recovery attempt and classify it honestly
- [ ] Eliminate the remaining abstract `limit_capability` family under Plan `0060`

## Longer-Term Queue

- [ ] Re-evaluate whether LLM clustering should replace exact strategy as default after the next answerability hardening pass
- [ ] Evaluate whether Plan 0028 should widen beyond the first five operations
- [ ] Revisit consumer-blocked richer DIGIMON interchange only through DIGIMON Plan 23
- [ ] Revisit trusted bulk ingestion only if a real workflow makes review the bottleneck

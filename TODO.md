# TODO

## Current 24h Execution Block

Source of truth:
- `docs/plans/0045_24h_extraction_path_block.md`

### Phase 1 — Freeze The Extraction-Path Contract
- [x] Restate the Plan 0044 decision as the incoming contract
- [x] Freeze the current aligned-wrapper failure artifacts
- [x] Record chunk `002` as the regression guard only
- [x] Record the execution caveats (`PYTHONPATH=src`, run-id mapping)
- [ ] Commit verified phase

### Phase 2 — Compare Extraction-Service Behavior Directly
- [ ] Identify the remaining path differences after wrapper alignment
- [ ] Capture those differences in a reproducible artifact
- [ ] Separate extraction-path behavior from review amplification
- [ ] Commit verified phase

### Phase 3 — Land One Narrow Diagnostic Aid
- [ ] Implement the smallest helper or instrumentation needed to replay or summarize the extraction-path divergence
- [ ] Add verification for that aid
- [ ] Keep it bounded to extraction-path behavior
- [ ] Commit verified phase

### Phase 4 — Classify The Dominant Blocker
- [ ] Decide whether the remaining blocker is extraction-service behavior or review/judge behavior
- [ ] Record secondary caveats separately
- [ ] Commit the classification with artifacts
- [ ] Commit verified phase

### Phase 5 — Closeout
- [ ] Write the decision-grade extraction-path note
- [ ] Refresh docs/status/handoff
- [ ] Mark execution block complete
- [ ] Commit verified phase

## Most Recent Completed 24h Execution Block

Source of truth:
- `docs/plans/0044_24h_wrapper_alignment_block.md`

### Phase 1 — Freeze The Wrapper-Alignment Contract
- [x] Restate the Plan 0043 decision as the incoming contract
- [x] Freeze the current wrapper-difference artifacts
- [x] Record chunk `002` as the regression guard only
- [x] Record the execution caveats (`PYTHONPATH=src`, run-id mapping)
- [x] Commit verified phase

### Phase 2 — Build One Aligned Surface Candidate
- [x] Define the narrowest live-prompt override that aligns the live user surface toward the prompt-eval wrapper
- [x] Keep system instructions and model selection fixed
- [x] Document exactly what changed
- [x] Commit verified phase

### Phase 3 — Verify The Aligned Surface
- [x] Run prompt-surface comparison for the aligned candidate
- [x] Run one live chunk-003 rerun with the aligned surface
- [x] Compare against prompt-eval and the prior live run
- [x] Commit verified phase

### Phase 4 — Classify The Result
- [x] Decide whether wrapper alignment materially reduced the divergence
- [x] If not, name the next blocker as extraction-path behavior or review/judge behavior
- [x] Commit the classification with artifacts
- [x] Commit verified phase

### Phase 5 — Closeout
- [x] Write the decision-grade wrapper-alignment note
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
- [ ] Localize the remaining post-wrapper extraction-path divergence to one dominant surface

## Longer-Term Queue

- [ ] Re-evaluate whether LLM clustering should replace exact strategy as default after the next answerability hardening pass
- [ ] Evaluate whether Plan 0028 should widen beyond the first five operations
- [ ] Revisit consumer-blocked richer DIGIMON interchange only through DIGIMON Plan 23
- [ ] Revisit trusted bulk ingestion only if a real workflow makes review the bottleneck

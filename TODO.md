# TODO

## Current 24h Execution Block

Source of truth:
- `docs/plans/0043_24h_live_path_divergence_block.md`

### Phase 1 — Freeze The Divergence Contract
- [x] Restate the Plan 0042 decision as the incoming contract
- [x] Freeze the same-model evidence on chunk `003`
- [x] Record chunk `002` as the regression guard only
- [x] Record the execution caveats (`PYTHONPATH=src`, run-id mapping)
- [ ] Commit verified phase

### Phase 2 — Compare Path Surfaces Directly
- [ ] Identify the remaining live-vs-prompt-eval path differences under the revised candidate pair
- [ ] Capture those differences in a reproducible artifact
- [ ] Separate prompt wrapper differences from extraction/review behavior
- [ ] Commit verified phase

### Phase 3 — Land One Narrow Diagnostic Or Repair Aid
- [ ] Implement the smallest honest aid for replaying the divergence
- [ ] Add verification for that aid
- [ ] Keep it bounded to the divergence family
- [ ] Commit verified phase

### Phase 4 — Classify The Dominant Live-Path Blocker
- [ ] Decide whether the divergence is dominated by prompt/render contract, extraction path behavior, or review/judge acceptance
- [ ] Record secondary caveats separately
- [ ] Commit the classification with artifacts
- [ ] Commit verified phase

### Phase 5 — Closeout
- [ ] Write the decision-grade live-path divergence note
- [ ] Refresh docs/status/handoff
- [ ] Mark execution block complete
- [ ] Commit verified phase

## Most Recent Completed 24h Execution Block

Source of truth:
- `docs/plans/0042_24h_semantic_transfer_residual_block.md`

### Phase 1 — Freeze The Semantic Residual Contract
- [x] Restate the Plan 0041 decision as the incoming contract
- [x] Enumerate the chunk `002` body-level residuals
- [x] Enumerate the chunk `003` live-only overreach families
- [x] Record the execution caveats (`PYTHONPATH=src`, run-id mapping)
- [x] Commit verified phase

### Phase 2 — Land A Body-Level Comparison Aid
- [x] Extend or add the narrowest helper for body-level comparison
- [x] Add targeted verification for that helper
- [x] Save semantic residual artifacts for chunks `002` and `003`
- [x] Commit verified phase

### Phase 3 — Make One Bounded Prompt Revision
- [x] Update the compact extraction prompt candidate only where the residual justifies it
- [x] Target analytical narrator overreach and unsupported subject/speaker invention
- [x] Keep the diff small and traceable
- [x] Commit verified phase

### Phase 4 — Verify The Revision
- [x] Rerun bounded prompt-eval verification on chunks `002` and `003`
- [x] Run at least one live chunk rerun
- [x] Decide whether the candidate advanced or stayed promotion-blocking
- [x] Commit verified phase

### Phase 5 — Closeout
- [x] Write the decision-grade semantic residual note
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
- [ ] Localize the remaining same-model live-path divergence to one dominant surface

## Longer-Term Queue

- [ ] Re-evaluate whether LLM clustering should replace exact strategy as default after the next answerability hardening pass
- [ ] Evaluate whether Plan 0028 should widen beyond the first five operations
- [ ] Revisit consumer-blocked richer DIGIMON interchange only through DIGIMON Plan 23
- [ ] Revisit trusted bulk ingestion only if a real workflow makes review the bottleneck

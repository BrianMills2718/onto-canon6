# TODO

## Current 24h Execution Block

Source of truth:
- `docs/plans/0041_24h_full_chunk_transfer_parity_block.md`

### Phase 1 — Freeze The Residual Contract
- [x] Restate the Plan 0040 result as the incoming contract
- [x] Enumerate the exact residual mismatches on chunks `002` and `003`
- [x] Record the execution caveats (`PYTHONPATH=src`, run-id mapping)
- [ ] Commit verified phase

### Phase 2 — Reconstruct Prompt Surfaces
- [ ] Reconstruct the live extraction prompt surface for a named chunk
- [ ] Reconstruct the prompt-eval parity prompt surface for the same chunk
- [ ] Save the exact message/context delta
- [ ] Commit verified phase

### Phase 3 — Land The Minimum Parity Aid
- [ ] Implement the narrowest reproducible prompt-surface comparison helper
- [ ] Add verification for the helper
- [ ] Commit verified phase

### Phase 4 — Classify The Dominant Residual
- [ ] Run the parity aid on chunks `002` and `003`
- [ ] Decide whether the dominant blocker is prompt/render contract or semantic extraction
- [ ] Commit verified phase

### Phase 5 — Closeout
- [ ] Write the decision-grade parity note
- [ ] Refresh docs/status/handoff
- [ ] Mark execution block complete
- [ ] Commit verified phase

## Most Recent Completed 24h Execution Block

Source of truth:
- `docs/plans/0040_24h_extraction_transfer_certification_block.md`

### Phase 1 — Freeze The Certification Contract
- [x] Name the exact compact candidate lane and prompt asset under test
- [x] Freeze the canonical chunk pair (`002`, `003`)
- [x] Freeze the incoming transfer artifacts from Plan 0014
- [x] Commit verified phase

### Phase 2 — Localize The Live-vs-Parity Gap
- [x] Compare current live output against prompt-eval parity output on chunk `003`
- [~] Compare the same surfaces on chunk `002`
- [x] Write down exact candidate/output differences plus review outcomes
- [x] Commit verified phase

### Phase 3 — Land The Minimum Certification Aid
- [x] Implement the narrowest reproducible live-vs-parity comparison helper
- [x] Add verification for the helper
- [x] Commit verified phase

### Phase 4 — Re-run The Certification Check
- [x] Build one current-generation full-chunk parity artifact for chunk `002`
- [x] Build or confirm one current-generation live compact-v4 reviewed chunk `002` artifact
- [x] Run the certification comparison on chunk `002`
- [x] Run the certification comparison on chunk `003`
- [x] Decide whether the candidate clears or fails the transfer gate
- [x] Commit verified phase

### Phase 5 — Closeout
- [x] Write the decision-grade certification note
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
- [ ] Narrow the remaining full-chunk prompt-eval/live residual into one dominant blocker family

## Longer-Term Queue

- [ ] Re-evaluate whether LLM clustering should replace exact strategy as default after the next answerability hardening pass
- [ ] Evaluate whether Plan 0028 should widen beyond the first five operations
- [ ] Revisit consumer-blocked richer DIGIMON interchange only through DIGIMON Plan 23
- [ ] Revisit trusted bulk ingestion only if a real workflow makes review the bottleneck

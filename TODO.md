# TODO

## Current 24h Execution Block

Source of truth:
- `docs/plans/0040_24h_extraction_transfer_certification_block.md`

### Phase 1 — Freeze The Certification Contract
- [ ] Name the exact compact candidate lane and prompt asset under test
- [ ] Freeze the canonical chunk pair (`002`, `003`)
- [ ] Freeze the incoming transfer artifacts from Plan 0014
- [ ] Commit verified phase

### Phase 2 — Localize The Live-vs-Parity Gap
- [ ] Compare current live output against prompt-eval parity output on chunk `003`
- [ ] Compare the same surfaces on chunk `002`
- [ ] Write down exact candidate/output differences plus review outcomes
- [ ] Commit verified phase

### Phase 3 — Land The Minimum Certification Aid
- [ ] Implement the narrowest reproducible live-vs-parity comparison helper
- [ ] Add verification for the helper
- [ ] Commit verified phase

### Phase 4 — Re-run The Certification Check
- [ ] Run the certification comparison on chunk `002`
- [ ] Run the certification comparison on chunk `003`
- [ ] Decide whether the candidate clears or fails the transfer gate
- [ ] Commit verified phase

### Phase 5 — Closeout
- [ ] Write the decision-grade certification note
- [ ] Refresh docs/status/handoff
- [ ] Mark execution block complete
- [ ] Commit verified phase

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

- [ ] Turn the current compact operational-parity lane into one explicit certification decision
- [ ] Keep chunk `002` as the positive control and chunk `003` as the prose-heavy stress case
- [ ] Make the live-vs-parity gap reproducible instead of aggregate-only
- [ ] Decide whether the current candidate is promotable or still transfer-blocked

## Longer-Term Queue

- [ ] Re-evaluate whether LLM clustering should replace exact strategy as default after the next answerability hardening pass
- [ ] Evaluate whether Plan 0028 should widen beyond the first five operations
- [ ] Revisit consumer-blocked richer DIGIMON interchange only through DIGIMON Plan 23
- [ ] Revisit trusted bulk ingestion only if a real workflow makes review the bottleneck

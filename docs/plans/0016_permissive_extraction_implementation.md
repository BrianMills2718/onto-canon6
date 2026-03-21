# Permissive Extraction Implementation

Status: complete

Updated: 2026-03-21

## Outcome (2026-03-21)

Implemented as part of the progressive extraction pipeline (Plan 0018).
`pipeline.permissive_review` config flag added, ReviewService passes it to
validation transition. When true, invalid candidates can be accepted
(annotation, not gate). All 3 passes of progressive extraction store
partial results permissively. 1 dedicated test + 8 e2e tests verify the
permissive path.

## Purpose

Implement ADR-0017: shift the pipeline from reject-at-ingest to
store-everything-score-downstream. Validation becomes annotation, not gate.
Promotion becomes the governance boundary.

Driven by the 37.5% acceptance rate on Stage 1 and the `roles: {}` structural
blocker that prompt hardening cannot fully resolve.

## Requirements

1. All extraction results persist as candidate assertions regardless of
   validation outcome.
2. Validation runs on every candidate and produces a `validation_outcome`
   annotation. It does not reject.
3. The existing review workflow (accept/reject) remains available.
4. Promotion checks configurable quality thresholds before allowing
   candidates into the canonical graph.
5. Deletion of stored candidates is never the default.
6. Existing tests that assert rejection on hard errors are updated to
   assert annotation instead.

## Design

### Current flow (reject-at-ingest)

```
extract → submit_candidate_import() → validate → hard_error? → REJECT
                                                → clean? → PERSIST
```

### New flow (permissive)

```
extract → submit_candidate_import() → validate → annotate → PERSIST always
                                                           ↓
review (human/LLM) or auto-promote policy → promote_candidate() → graph
```

### Key changes

1. **`ReviewService.submit_candidate_import()`**: Remove the early return on
   hard validation errors. Always persist. Attach validation outcome as a
   field on the candidate record.

2. **`CandidateAssertionRecord`**: Add `validation_outcome` field that stores
   the full `ValidationOutcome` (hard errors, soft violations, proposal
   requests). Currently this information is partially captured in
   `validation_status` but hard-error candidates are never persisted.

3. **`ReviewService.submit_candidate_assertion()`**: Same change — validate
   and annotate, do not reject.

4. **Promotion gate**: `CanonicalGraphService.promote_candidate()` already
   requires an accepted review decision. Add a configurable quality gate
   that checks `validation_outcome` before promotion. Default: reject
   promotion of candidates with hard validation errors (preserves current
   behavior at the promotion boundary).

5. **Config**: Add `pipeline.permissive_ingest: true` to `config.yaml`.
   When `false`, revert to reject-at-ingest behavior (backwards compat).
   Default: `true`.

## Files Affected

- `src/onto_canon6/pipeline/service.py` — submission path changes
- `src/onto_canon6/pipeline/models.py` — `CandidateAssertionRecord` field
- `src/onto_canon6/pipeline/store.py` — persist validation outcome
- `src/onto_canon6/core/graph_service.py` — promotion quality gate
- `config/config.yaml` — `permissive_ingest` setting
- `tests/pipeline/test_review_service.py` — update rejection assertions
- `tests/core/test_graph_service.py` — promotion gate tests

## Build Order

1. Add `validation_outcome` field to `CandidateAssertionRecord` and update
   store schema.
2. Change `submit_candidate_import()` to always persist, attaching
   validation outcome.
3. Change `submit_candidate_assertion()` similarly.
4. Add `permissive_ingest` config flag with default `true`.
5. Add promotion quality gate to `promote_candidate()`.
6. Update tests: existing rejection tests become annotation tests.
7. Add new tests for: promotion gate blocks hard-error candidates,
   config toggle reverts to strict behavior.
8. Verify all 124 existing tests pass.

## Acceptance Criteria

- [ ] Candidates with hard validation errors persist with full provenance
- [ ] `validation_outcome` is queryable on stored candidates
- [ ] Promotion rejects candidates with hard validation errors by default
- [ ] `permissive_ingest: false` reverts to reject-at-ingest behavior
- [ ] All existing tests pass (updated where needed)
- [ ] New tests cover permissive path, promotion gate, config toggle

## Non-Goals

1. Do not implement LLM-automated review in this plan.
2. Do not implement auto-promotion policies beyond the quality gate.
3. Do not change the extraction pipeline itself.

## Relationship to Prior Work

- Implements: ADR-0017
- Extends: Plan 0014 (extraction quality baseline) — permissive extraction
  changes what "baseline" means
- Enables: Plan 0017 (ancestor-aware evaluation needs stored partial candidates)
- Enables: Plan 0018 (progressive disclosure produces partial candidates)

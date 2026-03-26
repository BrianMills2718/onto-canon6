# Permissive Extraction Implementation

Status: complete

Updated: 2026-03-21
Implements: ADR-0017
Workstream: post-bootstrap extraction R&D (ADR-0022)

## Purpose

Implement the extraction-governance boundary from ADR-0017:

1. validation should remain visible;
2. extracted candidates should still be stored and reviewed;
3. graph promotion should remain governed by explicit acceptance rather than
   by silent ingest rejection.

The point of this plan was not to weaken governance. The point was to stop
losing potentially useful extraction output before review and downstream
evaluation can see it.

## Acceptance Criteria

This plan is complete when:

1. candidate submission persists candidates together with validation
   annotation instead of rejecting them at persistence time;
2. invalid candidates remain reviewable rather than being silently dropped;
3. acceptance of invalid candidates is explicit and configurable;
4. the canonical graph still only admits accepted candidates;
5. tests cover the permissive review path and the strict default path.

## Implemented Shape

The repo now implements the permissive boundary like this:

1. `ReviewService.submit_candidate_import()` and
   `ReviewService.submit_candidate_assertion()` persist candidates together
   with:
   - `validation_status`
   - `validation: PersistedValidationSnapshot`
   - full provenance
2. `CandidateAssertionRecord` did **not** gain a separate
   `validation_outcome` field. The persisted validation annotation lives in the
   existing `validation_status` and `validation` fields.
3. invalid candidates are therefore visible in the review store instead of
   disappearing at ingest time.
4. `pipeline.permissive_review` controls whether an invalid candidate may move
   from `pending_review` to `accepted`.
   - default: `false`
   - permissive mode: `true`
5. graph promotion remains governed by explicit accepted review state.
   - there is no separate extra promotion-quality gate in this slice;
   - the boundary is still “accepted candidate required”.

This is the truthful repo-local shape today. The earlier design sketch that
mentioned `permissive_ingest` and a new promotion gate is superseded by the
implemented form above.

## Evidence

Primary implementation and proof:

1. `src/onto_canon6/pipeline/service.py`
2. `src/onto_canon6/pipeline/models.py`
3. `config/config.yaml`
4. `tests/pipeline/test_review_service.py`
5. `tests/pipeline/test_progressive_extraction_e2e.py`
6. `tests/pipeline/test_progressive_extractor_pass1.py`
7. `tests/pipeline/test_progressive_extractor_pass2.py`
8. `tests/pipeline/test_progressive_extractor_pass3.py`

The dedicated permissive-review proof is the invalid-candidate acceptance test
in `tests/pipeline/test_review_service.py`.

## Consequences

Positive:

1. extraction errors are inspectable and reviewable instead of vanishing at
   ingest time;
2. downstream evaluation and progressive extraction can persist partial results
   honestly;
3. governance still stays explicit at the review and promotion boundaries.

Costs:

1. the review store now contains more low-quality or invalid candidate rows;
2. operators must interpret validation annotation rather than assuming
   persisted candidates are always clean;
3. review configuration matters more, because `permissive_review` changes what
   acceptance allows.

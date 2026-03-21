# ADR-0020: Align Phase A Prompt-Eval Exact Scoring to Extraction-Boundary Semantics

Status: Accepted

Date: 2026-03-21

## Context

The expanded PSYOP prompt-eval fixture exposed a measurement problem in
Phase A. The first two expanded sweeps were structurally usable, but every
variant still reported `exact_f1 = 0.0`. That looked like total semantic
failure, but the run details showed something narrower:

1. Some semantically correct prompt-eval outputs were failing exact match
   because the extraction boundary derives local `ent:auto:*` IDs while the
   fixture payloads were written in reviewer-style preferred IDs.
2. Value fillers could also fail exact match because later review-oriented
   payloads include richer normalized objects, while the extractor is only
   responsible for emitting a correct primary surface-form value.
3. Prompt experiments should evaluate what the extractor is supposed to do
   now, not what later identity or canonicalization stages may rewrite.

This was a recurring ambiguity, not a one-off bad run. Phase A prompt
experiments and later evaluation lanes serve different purposes and should
not share one exact-match contract blindly.

## Decision

1. `ExtractionPromptExperimentService` uses a local prompt-eval exact
   matcher that scores extraction-boundary semantics:
   - exact predicate choice
   - exact role-name structure
   - entity fillers by `kind`, `entity_type`, and `name`
   - value fillers by `kind`, `value_kind`, and primary value text
2. The prompt-eval exact matcher ignores reviewer-only identity details such
   as `entity_id` and `alias_ids`.
3. The prompt-eval exact matcher also ignores richer downstream
   value-normalization shape when the extraction boundary already matches on
   the primary value text.
4. `LiveExtractionEvaluationService` keeps the stricter reviewer-style exact
   canonicalization lane for later review-quality and fidelity checks.
5. Phase A prompt-eval exact scores and later canonicalization-fidelity
   scores are intentionally related but not identical. They answer
   different questions.

## Consequences

Positive:

1. Phase A prompt experiments now measure extractor behavior instead of
   downstream reviewer state.
2. `exact_f1` moving off zero becomes meaningful again for prompt
   iteration.
3. Remaining failures are now honest prompt/model failures, such as
   unnamed entity fillers or wrong predicate structure.
4. ADR-0005's lane-separation principle stays intact: reasonableness,
   structural validity, prompt-eval exactness, and downstream
   canonicalization fidelity remain distinct surfaces.

Tradeoffs:

1. Phase A exact scores are no longer directly comparable to later
   reviewer-style exact-fidelity scores.
2. The repo now has two exact-match contracts on purpose, which must stay
   documented to avoid confusion.
3. If the extraction boundary changes materially, this matcher may need to
   change with it.

## Dependencies

- ADR-0005, which established separate evaluation lanes.
- Plan 0014, which defines the extraction-quality baseline campaign.

## Implementation Notes

Key implementation lives in:

- `src/onto_canon6/evaluation/prompt_eval_service.py`
- `tests/evaluation/test_prompt_eval_service.py`

The benchmark-alignment regression test must keep proving that reviewer-only
IDs and downstream value-normalization objects do not penalize a prompt-eval
exact match when the extraction-boundary semantics are otherwise identical.

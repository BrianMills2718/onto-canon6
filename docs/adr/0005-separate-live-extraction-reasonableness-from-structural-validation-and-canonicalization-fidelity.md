# ADR-0005: Separate Live Extraction Reasonableness from Structural Validation and Canonicalization Fidelity

Status: Accepted

Date: 2026-03-17

## Context

The `onto-canon` lineage repeatedly blurred three different questions when
judging extraction quality:

1. Is the extracted candidate assertion actually supported by the source text?
2. Is the extracted candidate structurally usable by the local ontology
   runtime?
3. Did the extracted candidate reproduce one preferred canonical payload
   exactly?

Treating those as one score made the benchmark harder to interpret. A low
exact-match score could mean:

1. unsupported extraction;
2. structurally invalid extraction;
3. a noncanonical but still reasonable candidate assertion.

`onto-canon6` now has a real text-extraction boundary, so it also needs a real
evaluation boundary that does not collapse those questions back together.

## Decision

`onto-canon6` Phase 5 evaluates live extraction in three explicit lanes:

1. `reasonableness/support`
   Judged against the source text and the extracted candidate assertions,
   including their evidence spans.
2. `structural validation`
   Determined locally by the ontology runtime and validation pipeline.
3. `canonicalization fidelity`
   Scored separately as exact preferred-form agreement against the benchmark
   reference payloads.

This decision also fixes four narrower rules:

1. reasonableness is the primary headline metric for extraction usefulness;
2. structural validation remains deterministic and local;
3. canonicalization fidelity is reported explicitly but is not treated as the
   same thing as truth;
4. live benchmark reports must keep the source text, extracted candidates,
   evidence spans, and split evaluation labels inspectable together.

## Consequences

Positive:

1. evaluation reports become much easier to interpret honestly;
2. the project can improve extraction quality without pretending canonical ID
   disagreement is factual error;
3. benchmark regressions can distinguish extraction failure from ontology or
   canonicalization policy drift.

Tradeoffs:

1. evaluation becomes more verbose than a single headline F1;
2. reasonableness review now depends on a judge model and prompt contract;
3. benchmark maintenance still requires curated reference payloads for the
   canonicalization lane.

## Implementation Notes

This ADR is implemented by the Phase 5 slice:

1. `src/onto_canon6/evaluation/models.py`
2. `src/onto_canon6/evaluation/service.py`
3. `prompts/evaluation/judge_candidate_reasonableness.yaml`
4. `tests/evaluation/test_service.py`
5. `notebooks/10_live_extraction_evaluation.ipynb`

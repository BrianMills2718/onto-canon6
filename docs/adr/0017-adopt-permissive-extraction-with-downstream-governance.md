# ADR-0017: Adopt Permissive Extraction with Downstream Governance

Status: Accepted

Date: 2026-03-19

## Context

The current extraction pipeline validates candidate assertions at submission
time and rejects those with hard validation errors (unknown predicates, missing
roles, type mismatches). Two real non-fixture runs exposed the cost of this
approach:

1. PSYOP Stage 1 achieved 37.5% acceptance (6/16 candidates).
2. The dominant failure mode is `roles: {}` — the model detects a relationship
   but cannot fill role slots to schema compliance in a single pass.
3. Prompt hardening (baseline → hardened → compact → single_response_hardened)
   reduced empty-role failures from 3 to 1 but cannot eliminate them because
   the source text often does not contain enough information to fill all roles.

The fundamental tension: strict validation at ingest fights the nature of LLM
extraction, which is approximate and incremental. A candidate with
`predicate=belongs_to_organization` and `roles={}` is still a signal — the
relationship was detected, the role structure is incomplete. Rejecting it
discards the signal entirely.

Systems like Microsoft GraphRAG handle this by being permissive at extraction
time and using graph algorithms to clean up downstream. The governance happens
on the output (what gets promoted), not the input (what gets stored).

## Decision

1. The pipeline stores all extraction results as candidate assertions
   regardless of validation outcome. No candidate is rejected at submission
   time.
2. Ontology validation runs on every candidate but produces annotations (a
   `validation_outcome` record attached to the candidate), not gate decisions.
3. A candidate can have `validation_status=hard_error` and still persist with
   full provenance.
4. The governance boundary moves to **promotion**: only candidates that meet
   configurable quality thresholds (validation status, reasonableness score,
   confidence) get promoted to the canonical graph.
5. The existing review workflow (accept/reject) remains available as an
   explicit human or LLM-automated decision surface. Policy-driven automatic
   promotion is a future possibility that will require its own plan and ADR
   when pursued. For now, promotion requires explicit review decisions.
6. Deletion of stored candidates is never the default. A configurable
   retention policy may archive low-quality candidates, but the default is
   to keep everything.

## Consequences

Positive:

1. No extraction signal is lost. Partial extractions (detected relationship,
   missing roles) persist as enrichment targets.
2. Downstream enrichment steps can fill missing roles on stored candidates
   without re-extracting from source text.
3. Evaluation becomes fairer: the system's recall is no longer artificially
   deflated by premature rejection.
4. The governance boundary (promotion) can use richer signals than validation
   alone — reasonableness scores, graph context, confidence, corroboration.

Tradeoffs:

1. Storage grows: every extraction persists, including low-quality candidates.
2. The promotion policy must be explicitly designed — without it, the graph
   fills with noise.
3. Existing tests that assert rejection on hard errors will need updating.

## Supersedes

This ADR modifies the behavior assumed by ADR-0002 (validation as gate) and
ADR-0004 (extraction grounding). Those ADRs remain valid for their core
principles (mixed-mode governance, evidence grounding) but the pipeline
no longer rejects at submission time.

## Implementation Notes

See Plan 0016 for the detailed implementation steps.

Key files:
- `src/onto_canon6/pipeline/service.py` (ReviewService submission path)
- `src/onto_canon6/pipeline/models.py` (CandidateAssertionRecord)
- `src/onto_canon6/pipeline/store.py` (persistence)

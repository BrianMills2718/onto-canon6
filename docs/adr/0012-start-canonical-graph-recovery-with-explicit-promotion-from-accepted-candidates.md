# ADR-0012: Start canonical graph recovery with explicit promotion from accepted candidates

Status: Accepted  
Date: 2026-03-18

## Context

After the Phase 10 bootstrap, the main remaining product gap versus
`onto-canon` is the missing canonical graph layer.

`onto-canon6` currently proves:

1. candidate assertions with review, proposal, overlay, artifact, and
   extension-local epistemic state;
2. a governed bundle export over accepted candidates.

But it does not yet prove:

1. durable promoted graph assertions;
2. first-class graph entities/concepts;
3. inspection of promoted graph state independent of the candidate-review
   tables.

The next slice needs to recover that value without repeating the old fused
runtime shape.

## Decision

Phase 11 starts canonical graph recovery with a narrow explicit promotion path:

1. only accepted candidates may be promoted;
2. one accepted candidate promotes to one durable promoted assertion record in
   the first slice;
3. entity fillers that already carry explicit `ent:*` ids are materialized as
   promoted graph-entity records;
4. the promoted assertion stores the normalized assertion body and keeps an
   explicit back-link to its source candidate;
5. proposal, overlay, artifact, evidence, and extension-local epistemic state
   are not duplicated into new storage tables in this slice; they are surfaced
   by traversal from the source candidate link.

The first operational surface for this slice is:

1. explicit promotion command;
2. typed graph report over promoted assertions and promoted entities.

## Why

This is the smallest slice that honestly recovers a graph layer:

1. it creates durable graph state rather than only export artifacts;
2. it preserves the review/governance workflow as the promotion source of truth;
3. it does not force identity resolution, semantic-stack recovery, or richer
   surfaces into the same phase;
4. it keeps promotion explicit and auditable rather than hidden inside review.

## Consequences

Positive:

1. `onto-canon6` regains the first real piece of the v1 graph model;
2. later phases can layer identity, semantic canonicalization, and richer
   epistemics onto promoted state instead of candidate-only state;
3. the promoted graph remains traceable back to the governed workflow.

Negative:

1. the first graph slice will still be narrower than the v1 concept/belief
   system;
2. repeated promotions stay one-to-one with accepted candidates in this slice;
3. promoted entity records will only be as stable as the incoming `entity_id`
   values until Phase 12 recovers richer identity handling.

## Non-Goals

This decision does not:

1. recover full v1 system-belief behavior in the same phase;
2. solve external identity resolution;
3. recover the full AMR/PropBank/SUMO/FrameNet/Wikidata stack;
4. add MCP or adapter surfaces in the same phase.

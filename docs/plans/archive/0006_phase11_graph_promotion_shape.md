# Phase 11 Graph Promotion Shape

Status: Complete (bootstrap phase)


Updated: 2026-03-18

## Purpose

This note locks the first promotable graph target for Phase 11 before broader
identity or semantic-stack work lands.

## Requirements

The first slice must:

1. promote only accepted candidates;
2. create durable promoted assertion records;
3. materialize explicit graph-entity records only when a filler already carries
   a concrete `entity_id`;
4. preserve explicit traceability back to the source candidate and, through that
   seam, to evidence, proposals, overlays, artifacts, and extension-local
   epistemic state;
5. fail loudly on invalid promotion attempts.

The first slice must not:

1. solve external identity resolution;
2. infer new graph entities from raw strings;
3. duplicate candidate-linked governance and provenance state into a second set
   of storage tables without proof that duplication is needed.

## Minimal Data Shape

The Phase 11 promotion target is:

1. `promoted_graph_entities`
   - one row per explicit `entity_id` encountered in promoted assertions
   - carries the first seen `entity_type` when present
2. `promoted_graph_assertions`
   - one row per promoted accepted candidate
   - stores predicate, normalized body, profile reference, source candidate id,
     promoter id, and timestamps
3. `promoted_graph_role_fillers`
   - typed role-filler rows for each promoted assertion
   - supports entity and literal/value fillers without flattening the payload

## Back-Link Rule

`promoted_graph_assertions.source_candidate_id` is the explicit provenance seam.

That seam is sufficient for Phase 11 because it allows reports to compose:

1. candidate provenance and evidence spans;
2. linked proposals and overlay applications;
3. candidate-centered artifact lineage;
4. extension-local epistemic state.

Phase 11 should traverse those relationships, not duplicate them.

## Surface

The first operational surface should be:

1. `promote-candidate`
   - explicit promotion command
2. `list-promoted-assertions`
   - inspect promoted assertion rows
3. one typed report service
   - bundles promoted graph records with the candidate-backed context

## Acceptance Criteria

Phase 11 counts as successful if:

1. promoting an accepted candidate creates deterministic graph records;
2. promoting a non-accepted candidate fails loudly;
3. repeated promotion of the same accepted candidate is deterministic and
   inspectable;
4. users can inspect promoted assertions and promoted entities without reading
   candidate tables directly;
5. one notebook proves promotion plus contextual back-links live.

## Open Questions For Later Phases

These remain intentionally deferred:

1. whether promoted system facts should become separate graph assertions or
   typed entity attributes;
2. whether one accepted candidate should later be able to promote into more than
   one graph assertion;
3. how external identity providers attach to promoted graph entities;
4. how much of the v1 concept system should return unchanged.

# ADR-0008: Start artifact lineage with a narrow three-kind model and candidate-centered links

Status: accepted

## Context

Phase 8 recovers one of the strongest donor ideas from `onto-canon` v1:
artifact-backed provenance. The successor needs that capability, but it should
not reintroduce a fused runtime or a large artifact subsystem before the core
review workflow proves it needs more breadth.

The main design questions were:

1. which artifact kinds are essential for the first slice;
2. whether lineage links should terminate at candidate assertions only or also
   be copied onto later accepted-assertion projections;
3. how much deduplication is worth doing before real pressure exists.

## Decision

Phase 8 starts with:

1. three artifact kinds:
   - `source`
   - `derived_dataset`
   - `analysis_result`
2. artifact links terminating at `candidate_assertion` records first;
3. accepted-assertion lineage exposed through traversal/reporting rather than
   by copying artifact links into a second storage layer;
4. exact-only deduplication at most, preferably through an optional
   fingerprint field rather than aggressive semantic merging.

## Why

This is the smallest slice that still proves the core donor idea:

1. raw source support remains visible;
2. derived transformations can be represented explicitly;
3. analysis-backed support becomes first-class rather than being hidden in free
   text or metadata blobs.

It also keeps the storage center of gravity in the current review pipeline.
The candidate assertion remains the first durable review subject, so artifact
links should attach there before the system grows additional assertion
projections.

## Expansion Path

This narrow slice is not the final artifact model. The intended path to a
broader version is:

1. Phase 8:
   - three artifact kinds
   - candidate-centered links
   - lineage report traversal
2. Later broadening when real workflows justify it:
   - add more artifact kinds such as `graph`, `query_result`, `embedding_index`,
     or `model`
   - add additional link subjects only if accepted-assertion or extension-local
     queries become awkward through traversal alone
   - add stronger exact deduplication and registry ergonomics once repeated
     duplicate registration becomes a demonstrated problem

The broad version should still preserve the same architectural rule: artifact
logic remains a bounded subsystem and does not become a new central workflow
object.

## Consequences

Positive:

1. Phase 8 remains small and independently verifiable.
2. The system regains a meaningful v1 capability without wholesale donor import.
3. The path to a fuller lineage model remains explicit.

Negative:

1. The first slice will not cover the full v1 artifact taxonomy.
2. Accepted-assertion lineage queries will initially rely on traversal rather
   than direct copied links.
3. Artifact deduplication will remain intentionally conservative.

## Related

1. `docs/plans/0001_successor_roadmap.md`
2. `docs/plans/0002_phase8_artifact_lineage_shape.md`
3. `../onto-canon/onto_canon/artifact_registry.py`

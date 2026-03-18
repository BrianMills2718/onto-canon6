# Phase 13 Semantic Canonicalization Shape

Updated: 2026-03-18

## Purpose

This note locks the first semantic canonicalization and repair slice before the
successor broadens into richer agent surfaces or deeper epistemic recovery.

## Requirements

The first slice must:

1. explicitly record what happened to the main v1 semantic layers:
   - AMR
   - PropBank
   - SUMO
   - FrameNet
   - Wikidata/Q-codes
2. canonicalize promoted assertion predicates and role ids through ontology-pack
   metadata rather than hidden code maps;
3. support explicit repair of already-promoted graph state;
4. revalidate rewritten promoted assertions against the current effective
   profile before saving them;
5. persist an auditable repair event with actor, timestamps, and before/after
   snapshots;
6. fail loudly when an assertion cannot be mapped cleanly to a canonical form.

The first slice must not:

1. reintroduce the full v1 AMR/PropBank/SUMO/FrameNet stack as a mandatory
   runtime dependency;
2. mix identity repair into the same phase;
3. silently rewrite promoted graph state without an explicit event trail;
4. treat notebook-only inspection as sufficient proof.

## Minimal Data Shape

The Phase 13 target is:

1. ontology-pack alias metadata
   - predicate aliases
   - role aliases
   - optional source-system predicate mappings usable as canonicalization input
2. `promoted_graph_recanonicalization_events`
   - one explicit event per applied rewrite
   - stable event id
   - promoted assertion id
   - actor id
   - optional reason
   - before predicate/body snapshot
   - after predicate/body snapshot
   - timestamp
3. one typed recanonicalization result object
   - updated promoted assertion
   - rewritten role fillers
   - persisted event, if any

## Rules

1. Scope
   - Phase 13 acts on promoted assertions only, not candidate assertions.
2. Canonicalization source
   - canonical ids come from the effective pack/profile, not from ad hoc code
     maps.
3. Predicate mapping
   - predicates may canonicalize through:
     - exact canonical id
     - declared alias
     - declared source mapping
4. Role mapping
   - roles may canonicalize through:
     - exact canonical runtime name
     - declared alias
5. Persistence
   - rewritten graph state must pass current validation before it replaces the
     prior promoted assertion body.
6. Repair trail
   - every rewrite must create an explicit persisted event.
7. No-op behavior
   - already-canonical assertions should return a typed no-op result without
     inventing a fake repair event.

## Surface

The first operational surface should be:

1. `recanonicalize-promoted-assertion`
   - rewrite one promoted assertion through the pack-driven canonicalization
     path
2. `list-recanonicalization-events`
   - inspect the persisted repair trail
3. one typed report service
   - bundle current promoted assertion state with any recanonicalization events

## Acceptance Criteria

Phase 13 counts as successful if:

1. the repo has an explicit semantic-stack disposition record for the v1 stack;
2. one promoted assertion with noncanonical predicate and/or role ids is
   rewritten deterministically to the pack-canonical form;
3. rewritten assertions are revalidated before persistence;
4. persisted repair events are inspectable and auditable;
5. one notebook proves measurable before/after canonicalization improvement on
   a real local slice.

## Open Questions For Later Phases

These remain intentionally deferred:

1. whether AMR/PropBank returns as an optional producer adapter package;
2. whether pack metadata should later represent frame families or external
   ontology lineage explicitly;
3. how much automatic repair should remain deterministic versus reviewed or
   model-assisted;
4. whether identity changes should later trigger automatic semantic
   recanonicalization.

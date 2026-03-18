# ADR-0013: Start Stable Identity with Promoted-Entity Identities, Alias Membership, and Explicit External Reference State

Date: 2026-03-18

## Status

Accepted

## Context

Phase 11 recovered the first durable graph slice, but promoted graph entities
are still only explicit `entity_id` rows. The successor does not yet have a
stable identity layer that can:

1. keep the same entity stable across repeated ingestions;
2. merge multiple promoted entity ids under one reviewed identity;
3. attach external references explicitly rather than hiding them in strings;
4. represent unresolved external-reference work without pretending it is
   already solved.

The Phase 12 roadmap requires stable identity plus external references, but the
repo does not yet need a broad entity-linking or enrichment platform.

## Decision

Phase 12 starts with a narrow identity subsystem over promoted graph entities
only.

The first slice will:

1. create stable local identity records that group one or more promoted entity
   ids;
2. keep identity membership explicit and auditable;
3. support one canonical membership plus zero or more alias memberships;
4. support explicit external-reference records with a typed state:
   `attached` or `unresolved`;
5. keep the external-reference provider model generic, with `wikidata` as one
   possible provider rather than the only built-in concept;
6. stay explicit and review-like rather than inventing automatic linking.

The first slice will not:

1. infer identity equivalence automatically from raw text;
2. solve concept identity in the same phase;
3. implement broad web enrichment or large-scale resolution;
4. recover the full v1 Q-code stack in one move.

## Consequences

Positive:

1. repeated promotion of the same promoted entity can resolve to the same local
   identity;
2. alias/merge decisions become explicit state instead of informal naming
   conventions;
3. external references become a first-class, auditable attachment rather than a
   string hidden in labels or metadata;
4. unresolved external-reference work can be persisted honestly.

Negative:

1. this is only the first identity slice, not the full v1 identity story;
2. concept identity and richer provider workflows remain deferred;
3. identity quality still depends on explicit reviewer actions rather than
   automatic linking.

## Follow-On

Later phases may extend this slice with:

1. concept-centric identity records;
2. richer review state over merges and splits;
3. broader provider-specific resolution workflows;
4. semantic recanonicalization tied to identity changes.

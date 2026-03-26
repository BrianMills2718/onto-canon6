# Phase 12 Identity Shape

Status: Complete (bootstrap phase)


Updated: 2026-03-18

## Purpose

This note locks the first stable-identity target for Phase 12 before broader
concept identity or semantic-stack work lands.

## Requirements

The first slice must:

1. create stable local identity records for promoted graph entities;
2. keep repeated ingestion stable by reusing the same identity for the same
   promoted `entity_id`;
3. support explicit alias membership so multiple promoted entity ids can map to
   one stable identity;
4. persist explicit external references as either:
   - `attached`
   - `unresolved`
5. fail loudly on conflicting identity membership or conflicting external
   reference content.

The first slice must not:

1. infer new merges automatically from strings or embeddings;
2. add concept identity in the same phase;
3. rebuild the v1 Q-code stack wholesale;
4. add broad enrichment or crawling.

## Minimal Data Shape

The Phase 12 identity target is:

1. `graph_identities`
   - one local stable identity id
   - identity kind for the first slice: `entity`
   - optional display label
   - actor and timestamps
2. `graph_identity_memberships`
   - map promoted `entity_id` rows into one identity
   - membership kind:
     - `canonical`
     - `alias`
   - actor and timestamps
3. `graph_external_references`
   - one explicit external-reference record attached to one identity
   - provider name
   - state:
     - `attached`
     - `unresolved`
   - attached records keep a concrete external id
   - unresolved records keep a query or note explaining what is missing

## Rules

1. Identity scope
   - Phase 12 identities are only for promoted graph entities, not promoted
     assertions and not yet concepts.
2. Repeated-ingestion stability
   - if the same promoted `entity_id` is seen again, the same identity must be
     reused.
3. Membership conflict
   - one `entity_id` may not silently belong to two different identities.
4. Canonical membership
   - each identity must have exactly one canonical membership in the first
     slice.
5. External references
   - `attached` requires a provider and external id
   - `unresolved` requires a provider and unresolved note/query

## Surface

The first operational surface should be:

1. `create-identity-for-entity`
   - create or reuse the stable identity for one promoted entity
2. `attach-identity-alias`
   - attach another promoted entity to an existing identity explicitly
3. `attach-external-ref`
   - attach one concrete external reference
4. `record-unresolved-external-ref`
   - persist unresolved reference work explicitly
5. `list-identities`
   - inspect stable identity rows
6. one typed report service
   - bundle identity, memberships, external refs, and linked promoted entities

## Acceptance Criteria

Phase 12 counts as successful if:

1. creating an identity for one promoted entity is deterministic and reusable;
2. repeated ingestion of the same promoted entity reuses the same local
   identity;
3. alias membership is explicit and auditable;
4. external references are stored as explicit attached or unresolved records;
5. one notebook proves repeated-ingestion stability and identity attachment
   live.

## Open Questions For Later Phases

These remain intentionally deferred:

1. whether concept identities should share the same table family or use a
   parallel shape;
2. whether provider-specific review workflows should live in a dedicated
   extension package;
3. how much of the old Q-code model should return unchanged;
4. whether identity changes should trigger automatic graph recanonicalization or
   only later repair workflows.

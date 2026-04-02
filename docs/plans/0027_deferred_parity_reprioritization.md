# Deferred Parity Reprioritization

Status: active

Last updated: 2026-03-31
Workstream: Lane 5 of the post-cutover program

## Purpose

Turn the preserved parity ledger in
[0005_v1_capability_parity_matrix.md](0005_v1_capability_parity_matrix.md)
into an ordered post-cutover backlog.

This plan does not redefine successor scope. It decides:

1. which deferred or narrowed capabilities should become next-active;
2. which should remain protected but deferred;
3. which are blocked on specific consumer pressure; and
4. which need their own future execution plans before implementation starts.

## Why Now

The program is no longer blocked on runtime cutover or vague schema promises:

1. Lane 2 has a real first consumer (DIGIMON) on the supported v1 seam;
2. Lane 3 is complete and the contract policy is now explicit;
3. Lane 4 has an explicit promotion gate, even though extraction transfer proof
   is still open.

That is enough evidence to stop treating the parity matrix as a flat preserved
ledger. It now needs an execution order.

## Non-Goals

This plan does not:

1. remove capabilities from the parity matrix without explicit rationale;
2. start implementation of a deferred capability by itself;
3. re-open completed bootstrap lanes;
4. decide benchmark-lane convergence work that belongs in DIGIMON Plan 23.

## Pre-Made Decisions

1. [0005_v1_capability_parity_matrix.md](0005_v1_capability_parity_matrix.md)
   remains the authoritative scope ledger.
2. Lane 5 classifies capabilities into exactly four buckets:
   - `next-active`
   - `protected-deferred`
   - `consumer-blocked`
   - `abandoned-with-rationale`
3. No capability becomes `next-active` unless there is a clear owner and a
   plausible acceptance surface.
4. DIGIMON as first consumer increases the priority of queryability and
   canonicalization, not of immediately widening the DIGIMON seam.
5. No row is marked `abandoned-with-rationale` in this pass unless there is a
   clear replacement thesis already supported by current repo direction.

## Classification Rules

### next-active

Use when a capability should plausibly become one of the next implementation
tracks after the current active gates.

### protected-deferred

Use when the capability remains part of successor scope but has no current
consumer or gate pressure justifying activation.

### consumer-blocked

Use when the capability should not activate until a named consumer or workflow
needs it.

### abandoned-with-rationale

Use only when the user-visible value is intentionally being replaced elsewhere
and the replacement path is explicit.

## Current Ordered Classification

### next-active

1. **Cross-document entity resolution value proof**
   - parity rows: concept dedup and merge tools; cross-investigation entity
     resolution at scale
   - owner: [0025_cross_document_entity_resolution.md](0025_cross_document_entity_resolution.md)
     and [0025a_entity_resolution_scale_out.md](0025a_entity_resolution_scale_out.md)
   - rationale: this directly improves canonical state quality and is already
     the strongest active value-multiplier for both DIGIMON and future query
     surfaces
2. **Concept/entity browsing and search**
   - parity row: concept/entity browsing and search
   - owner: needs a dedicated future execution plan
   - rationale: `onto-canon6` is now self-contained and has a consumer, but it
     still lacks a first-class query/browse surface for agents and operators.
     That limits its value as a governed knowledge base.

### protected-deferred

1. **Canonical concept/belief graph broadening**
   - parity row: canonical concept/belief graph with system beliefs
   - rationale: the narrowed promoted-graph slice is enough for current
     consumers; broader system-belief recovery is not yet consumer-driven
2. **Stable identity and external references beyond current alias/identity slice**
   - parity row: stable identity and external references, including Q-code-like
     cross-investigation identity
   - rationale: current identity slice is usable; broader external-reference
     work can wait until a real consumer needs it
3. **Direct concept/belief CRUD**
   - parity row: direct concept/belief CRUD
   - rationale: governed review remains the right default until trusted bulk
     ingestion is a real bottleneck
4. **Frame ontology interactive browsing**
   - parity row: frame ontology interactive browsing
   - rationale: low leverage compared with general browse/search
5. **Temporal inference**
   - parity row: temporal extraction and inference integration
   - rationale: temporal qualifiers exist; inference remains deferred until
     consumer pressure appears
6. **Streaming/incremental ingestion**
   - parity row: streaming/incremental ingestion
   - rationale: architecture should not block it, but there is no immediate
     proof need
7. **Multi-consumer query federation**
   - parity row: multi-consumer query federation
   - rationale: valuable long-term, but premature before a stronger single-repo
     query surface exists

### consumer-blocked

1. **Richer DIGIMON interchange / import direction**
   - parity row: DIGIMON bidirectional adapter
   - rationale: the current thin v1 seam is supported; richer interchange
     should move only with DIGIMON Plan 23 evidence, not as a default `onto-canon6`
     expansion
2. **Trusted-source bulk ingestion fast path**
   - parity row: direct concept/belief CRUD
   - rationale: only activate if governed review becomes the blocking cost for
     a real trusted-source workflow such as large `research_v3` imports
3. **Lead/investigation management**
   - parity row: lead/investigation management
   - rationale: likely belongs in a consumer such as `research_v3` unless
     `onto-canon6` itself becomes the place where investigations are managed

### abandoned-with-rationale

None in this pass.

## Immediate Execution Order After Current Active Gates

Assuming Lane 4 remains the active extraction gate, the next deferred-capability
order is:

1. finish the value-proof stage of [0025_cross_document_entity_resolution.md](0025_cross_document_entity_resolution.md);
2. execute the browse/search execution plan in [0028_query_browse_surface.md](0028_query_browse_surface.md);
3. keep richer DIGIMON interchange experimental and consumer-blocked under
   DIGIMON Plan 23;
4. revisit direct CRUD / trusted fast-path ingestion only if a real bulk-source
   workflow makes governed review the bottleneck.

## Future Plan Requirements

The following future execution plans are now justified when bandwidth allows:

1. **Trusted bulk ingestion plan**
   - should only activate if a real consumer forces it
   - must preserve fail-loud governance and provenance semantics
2. **Richer DIGIMON interchange plan**
   - remains downstream of DIGIMON Plan 23 experiment evidence
   - should be versioned as a new seam, not a silent mutation of v1

## Acceptance

This plan is complete enough for Lane 5 when:

1. each major deferred/narrowed parity area has one of the four classifications
   above;
2. the next-active order is explicit;
3. any capability that needs its own execution plan is named;
4. no current deferred capability remains implicitly important but operationally
   ownerless.

## Failure Modes

1. the parity matrix stays preserved but unusable as a priority tool;
2. new capability work starts from intuition instead of consumer/gate evidence;
3. DIGIMON convergence pressure causes silent widening of the v1 seam instead
   of explicit versioning;
4. low-leverage interactive surfaces crowd out higher-value canonicalization or
   queryability work.

## Open Questions / Uncertainty Tracking

### Q1: Is browse/search really the right next-active capability after entity-resolution proof?
**Status:** Open
**Why it matters:** If a stronger consumer case appears for bulk ingestion or a
specific adapter, the next-active order may need to change.

### Q2: Does lead/investigation management belong in onto-canon6 or should it be replaced by consumer-side workflows?
**Status:** Open
**Why it matters:** This is the one deferred row most likely to move to
`abandoned-with-rationale`, but there is not enough evidence yet.

### Q3: Should external-reference / Q-code-like identity work be promoted sooner if DIGIMON or research_v3 needs stable cross-investigation identities?
**Status:** Open
**Why it matters:** Current alias/identity infrastructure may be enough, but
real consumer pressure could move this from protected-deferred to next-active.

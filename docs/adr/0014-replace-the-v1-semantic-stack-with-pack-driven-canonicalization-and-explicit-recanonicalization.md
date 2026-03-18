# ADR-0014: Replace the v1 Semantic Stack with Pack-Driven Canonicalization and Explicit Recanonicalization

Date: 2026-03-18

## Status

Accepted

## Context

`onto-canon` v1 derived much of its value from a semantic stack built around:

1. AMR extraction and PropBank predicate senses;
2. SUMO-backed type and role validation;
3. FrameNet role naming and enrichment;
4. Wikidata/Q-code-linked external identity.

`onto-canon6` has already recovered:

1. governed text-to-candidate extraction;
2. pack/profile validation;
3. explicit promotion into a durable canonical graph;
4. explicit identity and external-reference state.

What it does not yet have is an explicit answer to two successor questions:

1. which parts of the old semantic stack are still core requirements;
2. how bad or noncanonical promoted graph state is repaired without reviving
   the v1 monolith.

Phase 13 needs a narrow answer that restores semantic canonicalization value
without making AMR/PropBank/SUMO/FrameNet hard runtime dependencies again.

## Decision

Phase 13 adopts a replacement thesis rather than a mechanical v1 import.

The successor semantic stack will start with:

1. pack-driven canonical predicate and role identifiers as the durable core;
2. explicit alias and source-mapping metadata loaded from ontology packs;
3. deterministic recanonicalization over promoted assertions;
4. explicit persisted repair events when promoted graph state is rewritten.

Disposition of the main v1 layers:

1. AMR
   - Replaced as a producer-side extraction strategy, not a core graph
     dependency.
2. PropBank
   - Replaced as an optional upstream predicate vocabulary and mapping source,
     not the required successor runtime vocabulary.
3. SUMO
   - Replaced in the core with pack/profile validation and explicit type rules.
     A SUMO-backed pack or adapter may return later, but SUMO is not a hard
     dependency of the successor runtime.
4. FrameNet
   - Replaced as optional ontology-pack enrichment metadata rather than a core
     runtime requirement.
5. Wikidata/Q-codes
   - Replaced in the core by the explicit identity and external-reference
     subsystem added in Phase 12.

The first successor semantic slice will:

1. canonicalize promoted assertion predicates through pack aliases and source
   mappings;
2. canonicalize promoted assertion role ids through pack aliases;
3. revalidate the rewritten promoted assertion against the current effective
   profile before persisting it;
4. persist an auditable recanonicalization event containing before/after
   snapshots and the actor who applied the rewrite.

The first slice will not:

1. recover AMR/PropBank/FrameNet/SUMO as mandatory runtime services;
2. perform semantic repair over entity identity in the same phase;
3. apply opaque LLM rewrites directly to promoted graph state;
4. claim that every v1 semantic capability has already returned.

## Consequences

Positive:

1. the successor gains a deterministic semantic repair seam over durable graph
   state;
2. ontology-pack authors can declare canonicalization knowledge directly in
   pack content;
3. the runtime no longer depends on a single semantic stack thesis to remain
   useful;
4. v1 semantic layers can still return later as optional adapters or pack
   compilers instead of hard runtime dependencies.

Negative:

1. the first slice is narrower than the v1 AMR/PropBank/SUMO stack;
2. quality depends on pack-declared alias/source metadata being present and
   accurate;
3. semantic canonicalization coverage will initially be limited to promoted
   assertions whose pack/profile is known.

## Follow-On

Later phases may extend this decision with:

1. optional producer-side adapters that emit pack-canonical predicate ids from
   AMR/PropBank or other semantic analyzers;
2. richer pack metadata for frame families, external ontologies, or semantic
   role equivalence;
3. broader repair flows over identity, corroboration, temporal, or inference
   state.

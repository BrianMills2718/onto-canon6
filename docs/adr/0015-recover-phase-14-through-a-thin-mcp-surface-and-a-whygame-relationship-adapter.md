# ADR-0015: Recover Phase 14 through a Thin MCP Surface and a WhyGame Relationship Adapter

Date: 2026-03-18

## Status

Accepted

## Context

By the end of Phase 13, `onto-canon6` had recovered:

1. the governed candidate-review flow;
2. overlay-aware ontology growth;
3. bounded graph, identity, artifact, and semantic-repair slices;
4. a CLI-first operational surface.

What it still lacked from v1 was:

1. a richer agent-facing boundary than the CLI;
2. one real recovered adapter path instead of notebook-local inputs only.

The v1 donor offered both a broad MCP server and WhyGame/DIGIMON adapters, but
that combination also embodied the old fused runtime. Phase 14 needs to recover
useful agent leverage without recreating that shape.

## Decision

Phase 14 will recover:

1. one thin FastMCP server over already-proved successor services; and
2. one narrow WhyGame relationship adapter that imports RELATIONSHIP facts into
   reviewable candidate assertions.

The chosen adapter and surface shape are:

1. WhyGame first, not DIGIMON
   - WhyGame relationship facts are the smaller, clearer donor path for a
     one-way adapter recovery.
2. FastMCP first, not a second custom runtime
   - the richer surface should expose existing services directly rather than
     duplicate CLI logic in another orchestration layer.
3. one local `whygame_minimal` pack and one strict profile
   - the adapter should import into an explicit, typed successor vocabulary
     rather than sneaking facts through the open profile.
4. relationship-only scope
   - the first slice accepts WhyGame `RELATIONSHIP` facts only and fails loudly
     on other fact types.
5. candidate-centered provenance
   - imported facts become candidate assertions first, with optional artifact
     registration and artifact links visible through the existing governed
     bundle/export surfaces.

The first MCP tool set is intentionally small:

1. import WhyGame relationships;
2. list candidates;
3. list proposals;
4. review candidates;
5. review proposals;
6. apply overlays;
7. promote accepted candidates;
8. export the governed bundle.

## Consequences

Positive:

1. the successor regains an actual agent-facing boundary without reviving the
   v1 monolith;
2. one real adapter now terminates in the governed review path instead of a
   separate importer runtime;
3. WhyGame provenance becomes visible through the same bundle and artifact
   surfaces as other successor inputs.

Negative:

1. the Phase 14 MCP slice is much smaller than the v1 35-tool server;
2. DIGIMON remains deferred;
3. the WhyGame adapter currently covers only relationship facts, not the full
   WhyGame graph model.

## Follow-On

Later phases may broaden this decision with:

1. a DIGIMON adapter over an equally explicit contract;
2. more MCP tools only when a real consumer forces them;
3. richer multi-fact WhyGame import if the narrow relationship slice proves
   insufficient.

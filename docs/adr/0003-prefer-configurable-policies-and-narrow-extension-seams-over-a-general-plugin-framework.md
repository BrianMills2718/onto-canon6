# ADR-0003: Prefer configurable policies and narrow extension seams over a general plugin framework

Status: Accepted  
Date: 2026-03-17

## Context

The successor is intended to support variation across:

1. ontology packs;
2. ontology profiles and modes;
3. mixed-mode governance behavior;
4. future domain packs such as DoDAF;
5. future external producers and importers;
6. future extensions and surfaces.

That creates a predictable temptation to build a broad plugin framework early.

The lineage review showed that the project's larger failure mode has not been
"too little framework." It has been drift toward oversized runtime centers,
speculative abstraction, and architecture that outruns the thin slice actually
proved.

The successor therefore needs a more disciplined distinction between:

1. configurable behavior;
2. explicit extension seams;
3. a full plugin platform.

## Decision

`onto-canon6` distinguishes these three concerns explicitly.

### 1. Configurable behavior

Configuration is preferred when the mechanism stays the same and only policy or
selection changes.

Current and expected examples:

1. which ontology pack or packs are active;
2. which profile is active;
3. `open|closed|mixed` ontology mode;
4. unknown-item routing behavior;
5. proposal acceptance application behavior.

### 2. Narrow extension seams

Typed extension seams are preferred when the system needs different
implementations behind a stable contract.

Expected seams include:

1. domain pack loading;
2. external producer importers;
3. extension packages such as epistemic reasoning;
4. surfaces such as CLI, report, MCP, or UI.

These seams should be:

1. explicit;
2. typed;
3. small enough to test independently;
4. owned by a specific subsystem boundary.

### 3. General plugin framework

A broad runtime-discovered plugin framework is explicitly deferred.

That includes things such as:

1. generic plugin registries for every subsystem;
2. entry-point discovery as a primary extension mechanism;
3. plugin-first architecture before at least two real consumers demand the same
   abstraction.

The default rule is:

1. choose configuration first;
2. choose a narrow typed seam second;
3. introduce a broader plugin mechanism only after repeated real pressure.

## Consequences

### Positive

- The successor stays extensible without turning into framework engineering.
- Subsystem boundaries remain visible because extension points are explicit.
- The project can support multiple ontology/domain shapes without treating every
  variation as a plugin problem.

### Negative

- Some later extension mechanisms may need refactoring once more real consumers
  exist.
- Early extension points must be chosen carefully rather than hidden behind a
  generic plugin abstraction.

### Neutral

- This ADR does not reject extensibility.
- It rejects speculative, platform-style plugin infrastructure before there is
  evidence that it is needed.

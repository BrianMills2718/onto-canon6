# ADR-0010: Choose CLI-driven governed bundle export as the first product-facing workflow

Status: Accepted  
Date: 2026-03-18

## Context

By the end of Phase 9, `onto-canon6` already proved:

1. text-grounded candidate extraction through `llm_client`;
2. candidate and proposal review with explicit overlay application;
3. candidate-centered artifact lineage;
4. extension-local epistemic state;
5. a thin operational CLI.

What remained unproved was the first real product-facing workflow. The open
questions were:

1. which single workflow best demonstrates user-visible leverage;
2. whether the first outward-facing boundary after the CLI should be MCP or
   something narrower;
3. how much provenance depth is needed before the workflow feels credibly
   useful.

The main risk was repeating an old lineage failure mode: adding a bigger new
surface that quietly becomes a second workflow runtime.

## Decision

The first product-facing workflow is:

1. start from one real source text file;
2. extract candidate assertions through the existing CLI;
3. review candidates and ontology proposals through the existing CLI;
4. apply accepted ontology growth through the existing CLI;
5. export one governed JSON bundle over the accepted reviewed state.

The outward-facing boundary for this first workflow is a thin CLI export
command, not MCP.

The exported governed bundle must include:

1. the accepted candidate assertions;
2. source provenance and evidence spans already attached to those candidates;
3. linked ontology proposals and any overlay applications;
4. candidate-centered artifact lineage when it exists;
5. extension-local epistemic state when it exists;
6. an explicit summary suitable for downstream inspection or later adapter
   work.

## Why

This is the smallest slice that demonstrates real leverage without changing the
architecture:

1. it is usable without ad hoc Python editing;
2. it produces one downstream-friendly artifact rather than only raw lists;
3. it reuses the proved services instead of introducing a new orchestrator;
4. it keeps MCP deferred until there is real consumer pressure.

MCP remains a likely later boundary, but it is not the simplest correct first
product-facing proof.

## Consequences

Positive:

1. the repo now has a concrete exportable workflow artifact, not just
   infrastructure slices;
2. the first product-facing proof stays thin and CLI-backed;
3. downstream consumers can inspect one JSON bundle with provenance, ontology
   governance state, and optional epistemic/artifact state;
4. MCP can later wrap the same surface rather than becoming a new workflow
   runtime.

Negative:

1. the first product-facing slice is still less interactive than a true MCP or
   UI surface;
2. the exported bundle is a bounded JSON artifact, not a general research
   platform;
3. artifact enrichment and epistemic enrichment remain optional rather than
   required inputs to the first workflow.

## Non-Goals

This decision does not:

1. add MCP in the same phase;
2. create a new central workflow controller;
3. require artifact lineage or epistemic state to be present for every
   candidate before export succeeds;
4. define multiple workflow variants at once.

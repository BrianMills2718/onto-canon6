# Phase 10 Governed Bundle Shape

Status: Complete (bootstrap phase)


This note locks the first product-facing workflow before or alongside
implementation.

## Goal

Recover one real user-facing workflow that ends in an exportable governed
artifact rather than only notebook outputs or raw CLI lists.

## Chosen Workflow

The first workflow is:

1. input source text;
2. extract candidate assertions through the existing CLI;
3. review candidates and ontology proposals;
4. apply accepted ontology additions;
5. export one governed bundle over the accepted candidate assertions.

## Chosen Boundary

The first outward-facing boundary is:

1. a thin CLI export command;
2. JSON-first output;
3. no MCP yet.

## Export Shape

The governed bundle should expose:

1. accepted candidate assertions;
2. linked proposal and overlay-application records;
3. source provenance and evidence spans from the candidate records;
4. candidate artifact links and lineage when present;
5. candidate epistemic state when present;
6. summary counts over the exported scope.

## Acceptance Criteria

Phase 10 counts as successful if:

1. a user can run the end-to-end workflow without direct module-level Python
   calls;
2. the resulting exported bundle includes clear source provenance and ontology
   governance state;
3. the export surface remains a thin adapter over existing services;
4. the canonical journey notebook runs the workflow live rather than emitting a
   provisional plan artifact.

## Acceptance Evidence

The acceptance evidence should be:

1. one integration test covering extract -> review -> overlay -> export;
2. one deep-dive notebook proving the exported bundle shape;
3. one canonical journey phase promoted from `planned/stub` to `proven/live`;
4. one ADR explaining why this boundary was chosen instead of MCP.

## Non-Goals

This phase does not:

1. add MCP in the same slice;
2. create a second workflow runtime;
3. require artifact or epistemic enrichment before export can succeed;
4. define multiple product workflows.

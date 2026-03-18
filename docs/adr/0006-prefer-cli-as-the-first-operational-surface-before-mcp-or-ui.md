# ADR-0006: Prefer CLI as the first operational surface before MCP or UI

Status: Accepted  
Date: 2026-03-17

## Context

By the end of Phase 5, `onto-canon6` already had:

1. ontology-aware validation;
2. candidate and proposal persistence;
3. review state transitions;
4. overlay application;
5. text-grounded extraction through `llm_client`;
6. live extraction evaluation.

What it still lacked was a narrow operational surface that let a user drive
the proved workflow without direct Python calls or notebook editing.

At this point there were three obvious directions:

1. add a CLI first;
2. add an MCP surface first;
3. add a richer UI first.

The risk was repeating a lineage pattern where a new surface quietly became a
new workflow runtime instead of staying a thin adapter over existing services.

## Decision

`onto-canon6` will use a thin CLI as its first operational surface.

That CLI must:

1. stay narrow and delegate to existing services;
2. prefer JSON-first output for scripting, notebooks, and shell inspection;
3. cover only the proved actions needed for the current slice:
   extraction, listing, review, and overlay application.

MCP and UI surfaces are deferred until after the CLI proves that the current
service boundaries are operationally credible.

## Consequences

Positive:

1. the first operational proof stays simple and local;
2. command handlers can be integration-tested without adding tool-runtime
   complexity;
3. the CLI becomes a stable inspection/debug surface for later MCP or UI work;
4. the project avoids building a second runtime around the services.

Negative:

1. the first surface is less user-friendly than a polished UI;
2. external tool integration still remains future work;
3. some ergonomics tradeoffs stay intentionally unresolved until real users
   push on the CLI shape.

## Notes

This decision is intentionally narrow. It does not say the CLI is the final
surface. It says the CLI is the simplest correct first proof that the current
stack can be operated without notebook-only glue.

# ADR-0002: Set the next proving slice and keep mixed-mode governance configurable

Status: Accepted  
Date: 2026-03-17

## Context

`onto-canon6` has now proved the first ontology-runtime slice:

1. donor profile and pack loading;
2. explicit `open|closed|mixed` policy semantics;
3. local assertion validation against donor rules.

The main remaining ambiguity was what should come next and which strategic
choices still require direct user input.

The user explicitly resolved the open questions as follows:

1. the next proving slice can follow the assistant's recommendation;
2. the first regained user-visible capability can follow the assistant's
   recommendation;
3. DoDAF should be deferred until later and treated as an exemplar of a
   different ontology/project shape the system should support;
4. mixed mode should remain configurable, including how acceptance is handled.

## Decision

The next proving slice is a narrow pipeline/review slice built on top of the
current ontology-runtime validation surface.

That slice should prove:

1. validation outcomes can be persisted as reviewable records;
2. unknown-item proposals can be persisted without importing the old monolithic
   workflow runtime;
3. mixed-mode governance behavior is configurable rather than hardcoded;
4. a user can inspect accepted, rejected, and pending ontology additions.

The first regained user-visible capability is:

1. governed review of candidate assertions, not domain-specific modeling and
   not a full extraction stack.

DoDAF is explicitly deferred:

1. it remains a useful donor/example domain pack;
2. it is not a near-term driver of the proving sequence.

Mixed-mode policy remains split across two distinct configuration concerns:

1. unknown-item routing policy:
   - allow
   - reject
   - propose
2. proposal acceptance application policy:
   - record accepted governance decisions without applying them
   - apply accepted decisions to an overlay target

The successor should not collapse those into one hidden runtime behavior.

## Consequences

### Positive

- The next build step is now explicit and no longer depends on conversational
  memory.
- The system keeps mixed-mode governance extensible without prebuilding a large
  plugin framework.
- DoDAF stays in the architecture as a supported future domain shape without
  distorting early implementation priorities.

### Negative

- Query/UI/MCP surfaces remain deferred until the pipeline/review slice is
  proven.
- Overlay writeback is still not a day-one assumption and will need a later
  proving step.

### Neutral

- This ADR does not force one specific consumer integration before the review
  slice is proven.
- It does require later work to make mixed-mode acceptance policy explicit in
  config and runtime contracts.

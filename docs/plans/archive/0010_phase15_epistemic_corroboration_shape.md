# Phase 15 Shape: Promoted-Assertion Epistemics, Corroboration, and Tension

Status: Complete (bootstrap phase)


Updated: 2026-03-18

## Purpose

Lock the narrowest honest Phase 15 slice before implementation.

The goal is to recover the remaining v1 epistemic value that still serves the
successor:

1. broader status transitions on promoted assertions;
2. corroboration reporting over promoted graph state;
3. tension reporting over promoted graph state;
4. explicit disposition for temporal/inference work instead of leaving it
   ambiguous.

## Acceptance Criteria

Phase 15 passes only if all of the following are true:

1. promoted assertions can move through explicit extension-local state beyond
   `active` and `superseded`;
2. invalid state transitions fail loudly;
3. corroboration groups are inspectable through a typed report surface;
4. tension pairs are inspectable through a typed report surface;
5. the canonical journey notebook includes one live Phase 15 proof;
6. the repo states clearly that temporal/inference recovery is deferred from
   the current successor scope.

Phase 15 fails if any of the following occur:

1. the implementation mutates the graph tables to store epistemic status;
2. `superseded` becomes a second manual state path separate from the
   candidate-level supersession seam;
3. corroboration or tension depend on hidden notebook state or opaque LLM
   judgment;
4. temporal/inference behavior is quietly omitted without an explicit
   disposition.

## Narrow Design

### 1. Manual promoted-assertion dispositions

Persist one auditable event stream over promoted assertions with manual target
statuses:

1. `active`
2. `weakened`
3. `retracted`

The extension derives current state from the event history plus existing
candidate-backed supersession:

1. `retracted` is terminal;
2. `superseded` is derived when a promoted assertion's source candidate has a
   supersession whose replacement candidate also has a promoted assertion;
3. `weakened` is reversible back to `active`;
4. `superseded` is not manually authored in this phase.

### 2. Corroboration

Corroboration groups are derived, not persisted.

Heuristic:

1. consider only currently non-terminal promoted assertions (`active` or
   `weakened`);
2. group assertions by canonical normalized assertion body;
3. emit a corroboration group when the same canonical body appears in two or
   more promoted assertions.

This keeps corroboration grounded in the proved canonicalization and graph
promotion layers.

### 3. Tension

Tension pairs are derived, not persisted.

Heuristic:

1. consider only currently non-terminal promoted assertions (`active` or
   `weakened`);
2. require the same predicate;
3. require at least one matching entity-bearing role anchor;
4. require at least one differing role filler;
5. skip exact canonical matches, because those are corroborations instead.

This is intentionally narrower than a general contradiction engine, but it
recovers useful deterministic signals over the current promoted graph.

## Interfaces

Phase 15 should add:

1. extension-local models for promoted-assertion disposition events,
   corroboration groups, tension pairs, and assertion-level epistemic reports;
2. service methods to:
   - record a promoted-assertion disposition;
   - build one promoted-assertion report;
   - build one collection report over promoted assertions;
3. one thin CLI surface for:
   - recording assertion disposition;
   - exporting the promoted-assertion epistemic report.

## Explicit Deferral

Temporal reasoning and inference are deferred, not proven, in Phase 15.

Rationale:

1. the successor already recovered the graph, identity, semantic, MCP, and
   adapter seams that matter more to current product value;
2. the present graph model does not yet justify broad temporal or inference
   infrastructure;
3. forcing them into this phase would create speculative complexity and weaken
   the extension boundary.

## Proof Artifacts

Implementation must be backed by:

1. unit tests over disposition transitions and derived status;
2. tests over corroboration and tension derivation;
3. one CLI or report integration test;
4. one live notebook proof.

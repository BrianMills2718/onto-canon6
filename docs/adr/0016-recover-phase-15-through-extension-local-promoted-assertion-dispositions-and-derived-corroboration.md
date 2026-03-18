# ADR-0016: Recover Phase 15 through extension-local promoted-assertion dispositions and derived corroboration

Status: Accepted  
Date: 2026-03-18

## Context

Phase 9 intentionally started the successor epistemic subsystem with the
smallest proved slice:

1. confidence assessments over accepted candidate assertions;
2. explicit supersession between accepted candidate assertions.

That slice preserved clean subsystem boundaries, but it did not recover the
remaining v1 belief-management behaviors that still matter to the successor:

1. broader assertion-level epistemic state transitions such as weakening or
   retraction;
2. explicit corroboration signals over the recovered graph layer;
3. explicit tension signals over the recovered graph layer.

At the same time, `onto-canon6` already proved:

1. accepted candidates promote into durable graph assertions;
2. proposal, overlay, artifact, and candidate-level epistemic context remain
   candidate-backed rather than duplicated into graph tables;
3. the successor avoids recreating a fused truth-maintenance runtime.

Phase 15 therefore needs to recover more epistemic value without collapsing
the extension boundary or silently reviving v1's broader monolith.

## Decision

Phase 15 will recover broader epistemics through one narrow extension-local
slice:

1. add explicit promoted-assertion disposition events with manual target
   statuses `active`, `weakened`, and `retracted`;
2. derive promoted-assertion `superseded` state from the existing
   candidate-level supersession seam when both candidates have promoted graph
   assertions;
3. compute corroboration groups dynamically from promoted assertions that share
   the same canonical normalized assertion body;
4. compute tension pairs dynamically from promoted assertions that share a
   stable entity-role anchor but differ in one or more role fillers;
5. keep all of that behavior inside the epistemic extension and its report
   surfaces rather than moving it into the graph store or the core workflow.

Temporal and inference behavior are explicitly deferred from the current
successor scope. They are not silently forgotten; they are intentionally not
part of the Phase 15 proof unless later workflow pressure justifies a narrower
re-entry.

## Consequences

Positive:

1. promoted assertions can now carry broader state transitions than
   supersession alone;
2. corroboration and tension become inspectable over graph state without
   mutating graph tables;
3. the successor regains meaningful v1 epistemic value without rebuilding a
   general truth-maintenance engine;
4. `superseded` remains grounded in the already-proved candidate review seam
   instead of becoming a second inconsistent manual mechanism.

Negative:

1. temporal reasoning and inference are still not recovered;
2. corroboration and tension remain deterministic heuristics over the current
   promoted graph shape, not general semantic contradiction detection;
3. the epistemic story remains split between candidate-backed confidence /
   supersession records and promoted-assertion disposition/report state.

## Guardrails

1. manual promoted-assertion state must fail loudly on invalid transitions;
2. `superseded` remains derived rather than manually authored in this phase;
3. corroboration and tension signals must be reproducible from persisted graph
   state, not opaque runtime guesses;
4. temporal or inference logic must not sneak back in under a generic
   "epistemic" label without a new ADR and a workflow-driven reason.

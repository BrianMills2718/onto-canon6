# ADR-0007: Adopt canonical journey notebooks with an explicit registry

Status: Accepted  
Date: 2026-03-18

## Context

`onto-canon6` already had many useful notebooks, but they were drifting toward
two bad states at once:

1. phase or subsystem probes looked like peer artifacts to actual end-to-end
   journeys;
2. notebook phase contracts lived mostly in prose and notebook cells instead of
   one explicit machine-readable surface.

The short-term notebook rules adopted across the workspace require a narrower
shape:

1. one canonical notebook per end-to-end journey;
2. explicit phase contracts outside the notebook;
3. explicit phase `status` and `execution_mode`;
4. later planned phases runnable only through explicit provisional artifacts;
5. clear separation between journey notebooks and deep-dive/planning notebooks.

## Decision

`onto-canon6` will implement the notebook process locally with four concrete
artifacts:

1. one canonical journey notebook for the current user-visible workflow;
2. `notebooks/notebook_registry.yaml` as the machine-readable notebook
   registry;
3. a typed validator in `src/onto_canon6/notebook_process.py`;
4. classified auxiliary notebooks for deep dives and planning companions.

The canonical journey notebook must:

1. run top-to-bottom in planning mode;
2. declare each phase explicitly through the registry contract;
3. use explicit provisional artifacts for unfinished later phases;
4. fail loudly in proof mode if a proof-critical phase is not `live`.

Auxiliary notebooks remain allowed, but they are not separate journeys unless
the registry says so.

## Consequences

Positive:

1. notebook drift becomes mechanically visible;
2. the main user journey has one obvious entry point;
3. existing phase notebooks can stay useful without pretending to be separate
   end-to-end workflows;
4. future deeper `project-meta` integration has a concrete local target to
   build on.

Negative:

1. the repo now carries a registry that must be maintained alongside docs and
   notebooks;
2. auxiliary notebooks need explicit classification work instead of being left
   informal;
3. notebook validation is still local to `onto-canon6`, not yet integrated
   into the wider workspace hooks.

## Notes

This decision is deliberately short-term and local. It does not claim the full
workspace notebook process is already integrated into the global graph or hook
system. It makes the local notebook practice explicit and testable now.

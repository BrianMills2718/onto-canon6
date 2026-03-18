# ADR-0011: Treat Phase 10 as bootstrap completion and track v1 capability parity explicitly

Status: Accepted  
Date: 2026-03-18

## Context

`onto-canon6` completed the initial successor bootstrap through Phase 10:

1. typed ontology/runtime contracts;
2. governed candidate and proposal review;
3. text-grounded extraction through `llm_client`;
4. overlay application;
5. a CLI operational surface;
6. a second-pack proof;
7. narrow artifact lineage;
8. narrow extension-local epistemics;
9. a product-facing governed-bundle export.

That bootstrap proved the restart rationale: cleaner subsystem boundaries,
better review/governance discipline, and a credible user-visible workflow.

But a rereview against `onto-canon` showed a strategic ambiguity:

1. the charter still says `onto-canon6` is a capability-preserving refactor;
2. the earlier roadmap language implied the project was effectively complete
   after Phase 10;
3. several major `onto-canon` capabilities are still not recovered or formally
   replaced:
   - the canonical concept/belief graph and system-belief model;
   - stable identity plus external reference handling;
   - the broader semantic canonicalization stack;
   - MCP and adapter surfaces;
   - broader epistemic, corroboration, and temporal/inference behavior.

Without an explicit rule, the repo can drift into claiming successor completion
while still carrying silent feature omissions.

## Decision

Phase 10 is now treated as:

1. completion of the initial successor bootstrap roadmap;
2. not completion of the broader successor goal.

From this point forward:

1. every major `onto-canon` capability must appear in an explicit parity record;
2. each capability must be marked as one of:
   - retained;
   - expanded;
   - replaced;
   - deferred;
   - abandoned;
3. every deferred or replaced capability must map to a concrete next phase or
   design note;
4. the successor is not considered strategically complete until every major v1
   capability has an explicit disposition and every retained/replaced capability
   has proof evidence.

The parity source of truth is:

1. `docs/plans/0005_v1_capability_parity_matrix.md`
2. the extended roadmap in `docs/plans/0001_successor_roadmap.md`

## Why

This is the simplest way to preserve the real restart thesis:

1. it keeps the good part of the bootstrap story;
2. it prevents “Phase 10 complete” from being misread as “v1 successor done”;
3. it allows v1 features to be intentionally replaced rather than rebuilt
   mechanically;
4. it forces silent omissions to become explicit product decisions.

## Consequences

Positive:

1. the repo now has a formal distinction between bootstrap completion and
   successor completion;
2. future roadmap extensions can be justified against explicit missing
   capabilities instead of vague momentum;
3. feature recovery can stay architectural rather than devolving into wholesale
   v1 porting.

Negative:

1. the project now carries a longer strategic plan than the original bootstrap
   roadmap;
2. some later phases remain intentionally uncertain until narrow design notes
   lock them down;
3. the repo can no longer honestly describe itself as “done” just because the
   bootstrap workflow exists.

## Non-Goals

This decision does not:

1. require one-to-one reimplementation of every v1 module;
2. force retention of every v1 design choice;
3. immediately lock all later implementation details before thin-slice planning
   happens for each new phase.

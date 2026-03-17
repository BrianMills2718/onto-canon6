# onto-canon6 Successor Roadmap

Status: Active  
Updated: 2026-03-17

## Purpose

This roadmap turns the accepted successor direction into a local phased plan for
`onto-canon6`.

It is intentionally narrow. Each phase must produce a real, inspectable slice
before the next phase expands the system.

## Phase Exit Rule

A phase is complete only when all three of these are true:

1. the build items for the phase exist in the repo;
2. the phase acceptance criteria are satisfied;
3. the acceptance evidence named for the phase exists and passes.

If any one of those is missing, the phase remains in progress even if some
supporting code already exists.

## Phase 0: Ontology Runtime Slice [completed]

Proved:

1. policy contracts;
2. donor profile/pack loading;
3. `open|closed|mixed`;
4. local assertion validation;
5. notebook probes and tests.

Acceptance evidence:

1. `tests/ontology_runtime/`
2. `notebooks/01_policy_contracts.ipynb`
3. `notebooks/02_donor_profile_loading.ipynb`
4. `notebooks/03_validation_slice.ipynb`

## Phase 1: Pipeline Review Slice [completed]

Goal:

1. turn local validation into persisted, reviewable workflow state.

Built:

1. validation record model;
2. proposal record model;
3. configurable proposal acceptance policy;
4. notebook-driven review/decision flow.

Acceptance evidence:

1. `tests/pipeline/test_review_service.py`
2. `notebooks/04_review_slice.ipynb`

Proved:

1. candidate assertions can persist validation outcomes;
2. mixed mode can persist proposal records without old workflow imports;
3. accepted and rejected proposal states are inspectable;
4. acceptance application policy is explicit in config and runtime behavior.

## Phase 2: First User-Visible Capability [completed]

Goal:

1. recover a concrete user-facing payoff from the lineage.

Chosen capability:

1. governed review of candidate assertions.

This is narrower than a full extraction product and more useful than staying at
policy-only infrastructure.

Built:

1. candidate-level review state model and transitions;
2. stronger provenance attached to candidate assertions;
3. a small query/report surface for pending, accepted, and rejected items;
4. notebook and test coverage for the review path.

Acceptance criteria:

1. a user can inspect candidate assertions by candidate status, proposal
   status, and profile;
2. each candidate assertion exposes provenance fields that identify who
   submitted it and what source it came from;
3. a user can record candidate-level accept or reject decisions without
   mutating ontology packs implicitly;
4. accepted and rejected candidates become visible in the query/report surface;
5. the review state machine fails loudly on invalid transitions.

Acceptance evidence:

1. a test module covering candidate review state transitions and invalid
   transition failures;
2. a notebook showing candidate submission, review, and reporting end to end;
3. one repo-local query/report entry point that can be executed against the
   persisted review store.

Proved:

1. candidate assertions can move through an explicit review state machine
   separate from validation outcome;
2. candidate submissions now retain stronger provenance fields;
3. the report surface exposes filtered candidates and proposals by status and
   profile;
4. invalid candidate-review transitions fail loudly;
5. accepted and rejected candidate states are visible through the report
   surface.

## Phase 3: Overlay Application and Query Surface [completed]

Goal:

1. make accepted governance decisions operational.

Built:

1. overlay-target write path;
2. overlay-aware pack loading;
3. provenance on overlay-applied additions;
4. simple query surface over accepted assertions and active ontology additions.

Acceptance criteria:

1. accepted overlay additions can be applied deterministically and idempotently;
2. `record_only` and `apply_to_overlay` remain observably different behaviors;
3. query behavior can distinguish base-pack and overlay-sourced content;
4. overlay application records what was written, where it was written, and from
   which accepted proposal;
5. overlay writeback is explicit and testable rather than hidden inside review
   actions.

Acceptance evidence:

1. tests proving deterministic overlay application and idempotent re-apply
   behavior;
2. a notebook showing base-pack plus overlay behavior before and after
   application;
3. one query/report example that shows overlay provenance explicitly.

Proved:

1. accepted predicate proposals can be applied into explicit local overlays;
2. overlay writeback is deterministic and idempotent by proposal identifier;
3. validation becomes overlay-aware after accepted additions are applied;
4. the report surface can distinguish overlay-sourced additions explicitly;
5. `record_only` and `apply_to_overlay` remain observably different paths.

## Phase 4: Text-Grounded Producer Integration [completed]

Goal:

1. wire one real raw-text producer into the review/governance flow.

Chosen producer for this phase:

1. a narrow `llm_client`-backed raw-text extraction path that produces
   candidate assertion payloads grounded in source evidence.

Built so far:

1. one typed raw-text import contract;
2. one first-class evidence-span model for candidate assertions;
3. persistence for optional source text, optional claim text, and exact
   evidence spans;
4. deterministic evidence-span verification before persistence;
5. one `llm_client`-backed text extraction service;
6. one prompt template stored under `prompts/`;
7. end-to-end notebook and tests for the selected producer boundary.

Build:

1. one importer that maps extractor output into candidate assertions,
   provenance, and evidence records;
2. one `llm_client`-backed extraction path with prompt templates stored under
   `prompts/`;
3. failure semantics for malformed payloads and unresolved evidence spans;
4. end-to-end notebook and tests for the selected producer.

Acceptance criteria:

1. the selected producer is named in this roadmap and its input contract is
   typed and documented;
2. raw text or another source artifact remains the primary input and provenance
   reference;
3. each imported candidate assertion carries first-class evidence spans and may
   also carry an optional natural-language gloss;
4. malformed producer payloads and unresolved evidence spans fail loudly with
   actionable errors;
5. any LLM-backed extraction call routes through `llm_client`;
6. prompt templates explain the downstream review goal and use an explicit
   structured output schema without adding unapproved examples;
7. imported candidate assertions drive the same review, proposal, and overlay
   workflow as local notebook examples;
8. no producer-specific logic leaks into `core` or `ontology_runtime`.

Acceptance evidence:

1. tests for the importer contract, span verification, and failure cases;
2. one notebook or small script showing end-to-end import from the chosen
   producer;
3. documentation for the producer payload contract, evidence model, and
   provenance mapping;
4. the prompt template and structured output contract used by the extraction
   path.

Proved:

1. raw text can flow through a narrow `llm_client`-backed extraction service
   into candidate assertions without bypassing the review pipeline;
2. the extractor prompt now lives as data under `prompts/` and is rendered
   through `llm_client`;
3. extracted candidate assertions retain source text, optional claim text, and
   first-class evidence spans;
4. malformed spans fail loudly before persistence;
5. producer-specific logic remains in the pipeline boundary rather than
   leaking into `core` or `ontology_runtime`.

## Phase 5: Additional Domain Packs and Extensions

Goal:

1. prove the architecture generalizes without collapsing boundaries.

Deferred areas:

1. DoDAF as exemplar domain pack;
2. epistemic extension;
3. richer surfaces such as MCP/UI.

Build:

1. one additional domain pack integrated without moving domain logic into core;
2. one extension package integrated through explicit extension seams;
3. one richer surface only if it can be built on the already-proven query and
   pipeline contracts.

Acceptance criteria:

1. the additional domain pack loads through the same pack/profile machinery as
   existing packs;
2. the extension package depends only on explicit extension seams rather than
   a central workflow object;
3. no broad plugin framework is introduced without real proven consumers;
4. adding the new pack or extension does not require domain-specific changes in
   `core`;
5. any new surface keeps business logic outside tool handlers.

Acceptance evidence:

1. tests proving the new pack and extension load through existing boundaries;
2. one notebook or integration test showing the exemplar domain pack in use;
3. one brief design note explaining why the new work did not require boundary
   violations.

## Standing Priorities

Always prefer:

1. explicit contracts over implied runtime behavior;
2. notebook-visible proof before larger rewrites;
3. configuration for mixed-mode routing and acceptance policy;
4. donor borrowing by subsystem, not by wholesale runtime import;
5. configuration first, narrow typed extension seams second, general plugin
   infrastructure only after repeated real need.
6. raw text remains primary for text-derived assertions; candidate assertions
   do not replace the underlying evidence.

## Current Explicit Unknowns

These are unresolved on purpose and should be resolved explicitly before the
relevant phase begins:

1. how live extraction quality should be evaluated once real model outputs are
   enabled beyond deterministic notebook proofs;
2. whether the first richer surface after the report view should be CLI, MCP,
   or something else.

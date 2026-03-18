# onto-canon6 Successor Roadmap

Status: Active  
Updated: 2026-03-18

## Purpose

This roadmap turns the accepted successor direction into a local phased plan for
`onto-canon6`.

It is intentionally narrow. Each phase must produce a real, inspectable slice
before the next phase expands the system.

The notebook companion at `notebooks/09_successor_long_term_plan.ipynb`
renders the same phase sequence as executable planning output with design
sketches for later phases.

The canonical end-to-end workflow notebook now lives in
`notebooks/00_master_governed_text_to_reviewed_assertions.ipynb`, with phase
contracts kept in `notebooks/notebook_registry.yaml`.

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

## Phase 5: Live Extraction Evaluation and Quality Harness [complete]

Goal:

1. move from structurally proved extraction to measured extraction quality on
   real model outputs.

Why this phase comes next:

1. the extraction boundary now exists, but its real-world usefulness is still
   unmeasured;
2. more extraction features would be premature before evaluation is explicit;
3. this phase resolves the known ambiguity between reasonableness and
   canonicalization fidelity before the workflow expands further.

Build:

1. one typed evaluation record that separates support/reasonableness from
   canonicalization fidelity;
2. one small benchmark corpus with source text, evidence expectations, and
   adjudicated reference outputs;
3. one `llm_client`-backed live extraction runner that records model
   selection, trace ID, and budget/cost context;
4. one notebook or report surface that shows per-sample and aggregate results.

Acceptance criteria:

1. at least one real model can be run end to end through the live extraction
   path;
2. evaluation outputs distinguish extraction reasonableness from
   canonicalization fidelity;
3. source text, extracted candidate assertions, evidence spans, and evaluation
   labels are inspectable together;
4. benchmark runs are reproducible enough for regression comparison;
5. the evaluation docs no longer present exact-match agreement as the primary
   truth metric.

Acceptance evidence:

1. tests for evaluation models and aggregate result computation;
2. one notebook showing a live or recorded extraction-evaluation run;
3. one short design note documenting the evaluation rubric and why it is split.

Proved:

1. `onto-canon6` now has typed evaluation models and a live evaluation service
   under `src/onto_canon6/evaluation/`;
2. the benchmark fixture, judge prompt, and aggregate scoring keep
   reasonableness, structural validation, and canonicalization fidelity
   separate;
3. at least one real model can run end to end through the extraction and judge
   path on the local PSYOP slice;
4. the live proof is inspectable through
   `notebooks/10_live_extraction_evaluation.ipynb`;
5. the local rationale is now recorded in
   `docs/adr/0005-separate-live-extraction-reasonableness-from-structural-validation-and-canonicalization-fidelity.md`.

## Phase 6: First Operational Surface [completed]

Goal:

1. make the proved workflow usable without direct Python or notebook editing.

Chosen first surface:

1. CLI first, because it is the simplest operational surface that can exercise
   the existing service boundaries without dragging in broader tool-runtime
   concerns.

Build:

1. one thin CLI surface over extraction, review, proposal, and overlay actions;
2. JSON output mode for scripting and inspection;
3. minimal command coverage for extract, list, review, and apply actions.

Acceptance criteria:

1. a user can go from raw text to persisted candidate assertions through the
   CLI;
2. a user can inspect candidates and proposals, record review decisions, and
   apply overlays through the CLI;
3. CLI handlers delegate to existing services rather than owning business
   logic;
4. JSON output is stable enough for scripted use in notebooks or shell flows.

Acceptance evidence:

1. CLI integration tests that exercise the end-to-end happy path and one loud
   failure path;
2. one notebook or shell transcript showing the workflow entirely through the
   CLI;
3. one brief design note explaining why CLI came before MCP/UI.

Build order:

1. define the CLI command surface and argument contract before wiring handlers;
2. implement thin handlers for extract, list, review, and apply actions;
3. add JSON output first, then human-readable output on top of the same data;
4. add integration tests and one notebook or shell transcript last.

Non-goals:

1. MCP or UI surfaces;
2. background jobs, daemons, or remote service deployment;
3. direct database manipulation from CLI handlers.

Explicit uncertainties:

1. whether the first extract command should accept file input only, or also
   raw stdin/text literals;
2. whether human-readable output should be table-first or JSON-first;
3. whether the first review commands should stay separate by object type
   (`candidate`, `proposal`) or share one higher-level command group.

Proved:

1. `onto-canon6` now exposes a thin operational CLI through
   `src/onto_canon6/cli.py` and `python -m onto_canon6`;
2. the first command surface covers extract, list, review, and overlay actions
   without moving business logic into CLI handlers;
3. JSON-first output is stable enough for scripted notebook and shell use,
   while a lighter text view reuses the same underlying data;
4. the end-to-end happy path plus a loud invalid-review failure are covered by
   `tests/integration/test_cli_flow.py`;
5. the local proof and rationale now live in
   `notebooks/12_cli_surface.ipynb` and
   `docs/adr/0006-prefer-cli-as-the-first-operational-surface-before-mcp-or-ui.md`.

## Phase 7: Domain Pack Generalization [completed]

Goal:

1. prove that the architecture supports a second real domain pack without core
   changes.

Chosen exemplar:

1. DoDAF remains the preferred late exemplar for this phase, not an earlier
   bootstrap dependency.

Build:

1. one second domain pack with at least one strict profile and one mixed
   profile;
2. pack-local notebook proof covering validation, proposal routing, and
   overlays;
3. any pack-specific extraction context needed to support the second pack,
   without adding domain branches to core modules.

Acceptance criteria:

1. the second pack loads through the same pack/profile machinery as the donor
   packs;
2. the same review and overlay workflow works for the second pack;
3. mixed-mode proposal routing remains configurable for the second pack;
4. no domain-specific logic is added to `core` or `ontology_runtime`.

Acceptance evidence:

1. tests proving second-pack loading and validation through existing
   boundaries;
2. one notebook showing second-pack review and overlay behavior;
3. one short design note describing what had to vary and what stayed shared.

Build order:

1. choose the minimal second-pack scope before importing or rewriting any
   ontology material;
2. define one strict profile and one mixed profile for that pack;
3. prove validation, proposal routing, and overlay behavior locally;
4. add pack-specific extraction context only if the existing extraction
   prompts are insufficient.

Non-goals:

1. full DoDAF coverage;
2. cross-pack inference or ontology merging as a separate subsystem;
3. domain-specific branches in `core` or `ontology_runtime`.

Explicit uncertainties:

1. which exact DoDAF subset is the right first proof surface;
2. whether the second pack should be imported from donor material or authored
   locally from a reduced subset;
3. whether a shared base vocabulary layer is needed before the second pack can
   stay clean.

Proved:

1. `onto-canon6` now has a local `dodaf_minimal` ontology pack plus two
   profiles over the same starting vocabulary:
   `dodaf_minimal_strict` and `dodaf_minimal_mixed`;
2. the local loader/runtime can discover repo-local profiles and ontology
   packs without changing the external pack/profile format;
3. strict and mixed remain profile/policy differences over the same pack,
   rather than separate ontology definitions;
4. the same validation, proposal, overlay, and CLI surfaces work for the
   second pack without core branching;
5. the deep-dive proof and canonical journey phase are now live in
   `notebooks/13_dodaf_minimal_second_pack.ipynb` and
   `notebooks/00_master_governed_text_to_reviewed_assertions.ipynb`.

## Phase 8: Artifact Lineage Recovery [completed]

Goal:

1. recover artifact-backed provenance from `onto-canon` v1 without rebuilding a
   fused runtime.

Build:

1. one typed artifact reference model for `source`, `derived_dataset`, and
   `analysis_result` artifacts;
2. links from candidate assertions to artifacts first, with accepted-assertion
   lineage exposed by traversal/reporting rather than copied storage;
3. one small lineage report surface that makes those links inspectable.

Acceptance criteria:

1. assertions can reference both raw sources and derived analysis artifacts;
2. lineage queries do not require moving artifact logic into `core`;
3. provenance remains explicit and inspectable rather than hidden in metadata
   blobs.

Acceptance evidence:

1. tests for artifact reference persistence and retrieval;
2. one notebook showing an assertion linked to both a source and a derived
   artifact;
3. one brief design note mapping the recovered lineage model back to the donor
   idea from `onto-canon` v1.

Build order:

1. define the minimal typed artifact model and persistence boundary;
2. link artifacts to candidate assertions first;
3. add derived-artifact support and lineage reporting second;
4. prove one small workflow where a claim is supported by an analysis artifact
   rather than only raw text.

Non-goals:

1. a full artifact warehouse or blob store;
2. workflow scheduling or orchestration;
3. a generalized research-platform artifact system.

Chosen first-slice shape:

1. artifact kinds: `source`, `derived_dataset`, `analysis_result`;
2. link target: `candidate_assertion` first;
3. accepted-assertion lineage: derived by traversal/reporting, not copied;
4. deduplication: none or exact-only through an optional fingerprint field.

Path to the fuller version:

1. add more artifact kinds only when real workflows need them;
2. add additional link subjects only if accepted-assertion or extension-local
   queries become awkward through traversal alone;
3. add stronger exact deduplication and registry ergonomics only after repeated
   duplicate registration becomes a demonstrated problem.

Proved:

1. `onto-canon6` now has a bounded `artifacts` subsystem with typed artifact
   records, lineage edges, and candidate-centered support links;
2. the first slice persists `source`, `derived_dataset`, and
   `analysis_result` artifacts without moving artifact logic into `core`;
3. accepted-assertion lineage remains derived by traversal/reporting rather
   than copied into a second storage path;
4. the typed lineage report surface now exposes direct links and ancestor
   artifacts explicitly;
5. the deep-dive proof and canonical journey phase are now live in
   `notebooks/14_artifact_lineage_slice.ipynb` and
   `notebooks/00_master_governed_text_to_reviewed_assertions.ipynb`.

## Phase 9: Epistemic Extension [planned]

Goal:

1. add optional epistemic reasoning without collapsing the current subsystem
   boundaries.

Build:

1. one extension package for confidence, tension, supersession, or related
   epistemic operations;
2. typed storage and operators owned by the extension rather than by the core
   review pipeline;
3. one inspectable report or notebook showing the extension in use.

Acceptance criteria:

1. epistemic data stays optional and does not become a hidden requirement for
   the base workflow;
2. the extension depends only on explicit seams and existing persisted records;
3. no central workflow object is reintroduced to host epistemic behavior.

Acceptance evidence:

1. tests for the extension's storage and operators;
2. one notebook demonstrating the extension against accepted assertions;
3. one short design note showing why the extension stayed out of core.

Build order:

1. choose the smallest useful epistemic operator set before defining storage;
2. implement extension-local models and operators;
3. wire them through explicit seams from the existing review/provenance
   records;
4. prove that the base workflow still functions unchanged when the extension is
   disabled.

Non-goals:

1. a full truth-maintenance system;
2. automatic contradiction resolution across the whole graph;
3. recentering the runtime around an epistemic controller.

Explicit uncertainties:

1. whether the first extension slice should start with confidence, tension,
   supersession, or contradiction;
2. whether epistemic state should attach only to accepted assertions or also to
   candidate assertions under review;
3. whether confidence values are user-entered, model-derived, or both.

## Phase 10: Product-Facing Workflow Integration [planned]

Goal:

1. connect the proved stack into one real end-to-end workflow that is useful
   beyond notebooks and local probes.

Build:

1. one end-to-end flow that starts from real source material and ends in
   reviewed, queryable, or exportable governed assertions;
2. one outward-facing integration surface, such as MCP or another research
   workflow boundary, built on the already-proven services;
3. enough artifact/provenance support to explain where the resulting assertions
   came from.

Acceptance criteria:

1. the workflow is usable without direct module-level Python calls;
2. the integration surface stays thin and keeps business logic out of handlers;
3. the system exposes clear provenance from source material through review and
   any overlay-applied ontology growth;
4. the workflow demonstrates actual user-visible leverage rather than only
   infrastructure correctness.

Acceptance evidence:

1. one integration test or scripted demo covering the end-to-end path;
2. one notebook or operator guide showing the workflow from input to output;
3. one short design note explaining why this is the first credible
   product-facing slice.

Build order:

1. choose one workflow and one integration boundary explicitly before building
   anything around it;
2. reuse the proved CLI/review/extraction/overlay/artifact services rather
   than creating a new workflow runtime;
3. add only the minimal outward-facing adapter needed for that workflow;
4. prove the workflow with real inputs and explicit provenance traces.

Non-goals:

1. multiple product workflows at once;
2. a generalized platform or multi-tenant service;
3. new architecture layers that exist only for hypothetical later products.

Explicit uncertainties:

1. which single workflow best demonstrates real user-visible leverage;
2. whether the first outward-facing boundary after CLI should be MCP or
   something narrower;
3. what minimum level of artifact/provenance depth is required before the
   workflow feels credibly useful.

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

1. how much broader benchmark coverage is needed before Phase 5 results should
   be treated as stronger quality evidence;
2. whether the first operational surface after CLI should be MCP, UI, or
   something else;
3. which single workflow should be the first product-facing integration slice.

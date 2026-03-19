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

## Phase 9: Epistemic Extension [completed]

Goal:

1. add optional epistemic reasoning without collapsing the current subsystem
   boundaries.

Build:

1. one extension package for confidence and supersession over accepted
   candidate assertions;
2. typed storage and operators owned by the extension rather than by the core
   review pipeline;
3. one inspectable report and notebook showing the extension in use.

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

Proved:

1. `onto-canon6` now has an extension-local epistemic package under
   `src/onto_canon6/extensions/epistemic/` with typed confidence assessments
   and supersession records;
2. the first epistemic slice attaches only to accepted candidate assertions
   and fails loudly if used on pending or rejected candidates;
3. the epistemic slice depends on the existing review store through explicit
   seams rather than mutating the base review schema;
4. the typed epistemic report surface now exposes current confidence,
   supersession state, and derived status without introducing a new central
   workflow object;
5. the deep-dive proof and canonical journey phase are now live in
   `notebooks/15_epistemic_extension_slice.ipynb` and
   `notebooks/00_master_governed_text_to_reviewed_assertions.ipynb`;
6. the local rationale is now recorded in
   `docs/adr/0009-start-epistemic-extension-with-confidence-and-supersession-over-accepted-candidates.md`
   and `docs/plans/0003_phase9_epistemic_shape.md`.

## Phase 10: Product-Facing Workflow Integration [completed]

Goal:

1. connect the proved stack into one real end-to-end workflow that is useful
   beyond notebooks and local probes.

Build:

1. one end-to-end flow that starts from real source material and ends in an
   exportable governed bundle over accepted reviewed assertions;
2. one outward-facing integration surface in the form of a thin CLI export
   command built on the already-proven services;
3. enough provenance, ontology-governance state, and optional
   artifact/epistemic state to explain where the resulting assertions came
   from.

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
2. reuse the proved CLI/review/extraction/overlay/artifact/epistemic services
   rather than creating a new workflow runtime;
3. add only the minimal outward-facing adapter needed for that workflow;
4. prove the workflow with real inputs and explicit provenance traces.

Non-goals:

1. multiple product workflows at once;
2. a generalized platform or multi-tenant service;
3. new architecture layers that exist only for hypothetical later products.

Proved:

1. the first product-facing workflow is now a CLI-driven governed-bundle
   export over accepted reviewed assertions;
2. the outward-facing boundary stays thin and service-backed through
   `src/onto_canon6/cli.py` and `src/onto_canon6/surfaces/governed_bundle.py`;
3. the exported bundle includes accepted candidates, linked proposal and
   overlay state, source provenance/evidence, candidate artifact lineage when
   present, and extension-local epistemic state when present;
4. the product-facing slice is covered by
   `tests/surfaces/test_governed_bundle.py`,
   `tests/integration/test_cli_flow.py`, and
   `notebooks/16_governed_bundle_workflow.ipynb`;
5. the canonical journey now ends in a live governed export artifact rather
   than a provisional workflow plan;
6. the local rationale is now recorded in
   `docs/adr/0010-choose-cli-driven-governed-bundle-export-as-the-first-product-facing-workflow.md`
   and `docs/plans/0004_phase10_governed_bundle_shape.md`.

## Bootstrap Completion Rule

Phase 10 completes the initial successor bootstrap roadmap.

It does not, by itself, complete the broader successor goal. The strategic
completion rule from this point forward is:

1. every major `onto-canon` capability must have an explicit disposition in
   `docs/plans/0005_v1_capability_parity_matrix.md`;
2. any capability still marked `deferred` must map to an explicit later phase
   or be intentionally abandoned with rationale;
3. the successor is not considered complete until every retained or replaced
   capability has real proof evidence.

## Post-Phase-15 Adoption Gate

After Phase 15, the default next step is not another automatic implementation
phase.

Before opening a new roadmap extension, the repo should:

1. run at least one real non-fixture investigation or external consumer
   workflow through the proved extract -> review -> promote -> export path;
2. record the observed friction, breakage, and missing user-visible value from
   that run;
3. use that evidence to justify the smallest next slice, whether that slice is
   parity-closing, ergonomics-driven, or consumer-specific.

This gate has now been satisfied once through the local PSYOP Stage 1 run
documented in:

1. `docs/plans/0011_first_real_run_psyop_stage1.md`
2. `docs/runs/2026-03-18_psyop_stage1_run_summary.md`
3. `docs/runs/2026-03-18_psyop_stage1_friction_log.md`

This keeps the parity matrix as a decision aid rather than a mandate to rebuild
every earlier capability before the successor is used.

## Phase 11: Canonical Graph Recovery [completed]

Goal:

1. recover the durable graph layer that made `onto-canon` more than a review
   inbox.

Build:

1. define a canonical promotion target for accepted candidate assertions;
2. recover the first durable entity/assertion graph records;
3. preserve explicit links from promoted graph state back to accepted
   candidates, evidence spans, proposals, overlays, artifacts, and extension
   state;
4. keep promotion explicit and auditable rather than hidden inside review
   actions.

Acceptance criteria:

1. accepted candidates can be promoted into deterministic durable graph records;
2. promoted records preserve provenance back to the review workflow and source
   evidence;
3. users can inspect or query promoted graph state without reading candidate
   tables directly;
4. the implementation does not introduce a new fused workflow runtime.

Acceptance evidence:

1. one design note for the promotion target and failure semantics;
2. unit and integration tests over promotion and provenance links;
3. one notebook proof over the smallest real promoted graph slice.

Build order:

1. lock the graph record shape first;
2. implement explicit promotion from accepted candidates second;
3. expose one thin report or query path over promoted state third.

Non-goals:

1. full external identity resolution;
2. broad semantic-stack recovery in the same phase;
3. all v1 graph ergonomics at once.

Explicit uncertainties:

1. whether promoted system facts remain separate beliefs or become typed
   attributes with explicit provenance;
2. whether promotion is one-to-one from candidate to assertion or may split one
   candidate into multiple graph records.

Proved:

1. accepted candidates now promote explicitly into durable graph assertions and
   materialized graph entities through `src/onto_canon6/core/graph_service.py`
   and `src/onto_canon6/core/graph_store.py`;
2. the graph slice remains candidate-backed: proposal, overlay, artifact, and
   epistemic context are traversed through `source_candidate_id` rather than
   duplicated into graph tables;
3. the promoted graph state is inspectable through a thin CLI-backed surface in
   `src/onto_canon6/cli.py` and `src/onto_canon6/surfaces/graph_report.py`;
4. the slice is covered by `tests/core/test_graph_service.py`,
   `tests/integration/test_graph_cli.py`, and
   `notebooks/17_canonical_graph_recovery_slice.ipynb`;
5. the canonical journey notebook now includes a live graph-promotion phase in
   `notebooks/00_master_governed_text_to_reviewed_assertions.ipynb`;
6. the local rationale is now recorded in
   `docs/adr/0012-start-canonical-graph-recovery-with-explicit-promotion-from-accepted-candidates.md`
   and `docs/plans/0006_phase11_graph_promotion_shape.md`.

## Phase 12: Stable Identity and External References [completed]

Goal:

1. recover cross-ingestion identity and explicit external references.

Build:

1. define successor-local stable identities for promoted entities/concepts;
2. add explicit alias, merge, and unresolved-state handling;
3. define whether v1-style Wikidata/Q-code behavior is retained directly or
   replaced by a broader external-reference model with Wikidata as one provider.

Acceptance criteria:

1. promoted identities remain stable across repeated ingestions;
2. external references are explicit attachments or explicit unresolved state,
   not hidden strings;
3. merge and alias decisions are reviewable and auditable;
4. the repo states clearly whether Q-code behavior is retained, optional, or
   replaced.

Acceptance evidence:

1. one identity-model design note;
2. unit and integration tests over identity attachment and merge behavior;
3. one notebook proof over repeated-ingestion identity stability.

Build order:

1. lock the identity model;
2. wire one reviewed merge/alias path;
3. add one external-reference provider or explicit unresolved-state path.

Non-goals:

1. broad web enrichment;
2. large-scale entity linking optimization;
3. support for many external sources at once.

Explicit uncertainties:

1. whether Wikidata stays the default first provider;
2. whether local stable ids should be concept-centric, entity-centric, or both.

Proved:

1. promoted entities now map into stable local identities through
   `src/onto_canon6/core/identity_service.py` and
   `src/onto_canon6/core/identity_store.py`;
2. repeated identity creation for the same promoted `entity_id` deterministically
   reuses the same local identity;
3. alias membership is explicit and auditable instead of inferred silently;
4. external references are now explicit attached or unresolved records through
   `src/onto_canon6/surfaces/identity_report.py` and the CLI identity commands;
5. the slice is covered by `tests/core/test_identity_service.py`,
   `tests/integration/test_identity_cli.py`, and
   `notebooks/18_stable_identity_slice.ipynb`;
6. the canonical journey notebook now includes a live stable-identity phase in
   `notebooks/00_master_governed_text_to_reviewed_assertions.ipynb`;
7. the local rationale is now recorded in
   `docs/adr/0013-start-stable-identity-with-promoted-entity-identities-alias-membership-and-explicit-external-reference-state.md`
   and `docs/plans/0007_phase12_identity_shape.md`.

## Phase 13: Semantic Canonicalization Stack Recovery Or Replacement [complete]

Goal:

1. recover or explicitly replace the major semantic layers that made v1 useful
   beyond generic extraction.

Build:

1. write one explicit semantic-stack decision record covering AMR, PropBank,
   SUMO, FrameNet, and related validation layers;
2. implement one credible canonicalization path over promoted assertions;
3. recover explicit repair or recanonicalization behavior for bad promoted graph
   state.

Acceptance criteria:

1. every major v1 semantic layer is explicitly marked retained, replaced, or
   abandoned with rationale;
2. one production path canonicalizes predicates and roles with measurable
   quality evidence;
3. structurally invalid or rejected promoted assertions can be revalidated or
   repaired through explicit tools;
4. the replacement thesis, if chosen, is benchmarked against real corpus
   slices.

Acceptance evidence:

1. one semantic-stack ADR or design note;
2. tests over canonicalization and repair flows;
3. one benchmark or notebook slice comparing the retained/replacement path to
   the predecessor expectations.

Build order:

1. lock the stack disposition first;
2. implement the minimal canonicalization path second;
3. add repair and recanonicalization third.

Non-goals:

1. importing the whole v1 ontology stack mechanically;
2. supporting every ontology pack equally in the first semantic slice.

Explicit uncertainties:

1. whether AMR/PropBank returns later as one optional producer adapter among
   several;
2. how much richer pack metadata should later represent SUMO/FrameNet lineage
   explicitly.

Proved:

1. the v1 AMR/PropBank/SUMO/FrameNet/Wikidata stack is now explicitly marked
   as replaced or deferred by layer through
   `docs/adr/0014-replace-the-v1-semantic-stack-with-pack-driven-canonicalization-and-explicit-recanonicalization.md`;
2. the first successor semantic slice now canonicalizes promoted assertion
   predicates and role ids through ontology-pack alias and source-mapping
   metadata loaded in `src/onto_canon6/ontology_runtime/loaders.py`;
3. bad promoted graph state can now be explicitly repaired and revalidated
   through `src/onto_canon6/core/semantic_service.py` and
   `src/onto_canon6/core/semantic_store.py`;
4. persisted recanonicalization events are now inspectable through
   `src/onto_canon6/surfaces/semantic_report.py` and the new CLI commands;
5. the slice is covered by `tests/core/test_semantic_service.py`,
   `tests/integration/test_semantic_cli.py`, and the local pack-loading proof
   in `tests/ontology_runtime/test_dodaf_minimal.py`;
6. the live proof artifact is
   `notebooks/19_semantic_canonicalization_slice.ipynb`, and the canonical
   journey notebook now includes the semantic recanonicalization phase in
   `notebooks/00_master_governed_text_to_reviewed_assertions.ipynb`;
7. the phase shape is locked locally in
   `docs/plans/0008_phase13_semantic_canonicalization_shape.md`.

## Phase 14: Agent Surface And Adapter Recovery [complete]

Goal:

1. recover one richer surface and one real adapter without recreating the v1
   monolith.

Build:

1. choose the next outward-facing boundary based on real consumer need;
2. if MCP is chosen, wrap the proved services thinly rather than reintroducing a
   new tool runtime;
3. define an explicit adapter contract and recover one real adapter such as
   WhyGame or DIGIMON.

Acceptance criteria:

1. the richer surface stays thin and service-backed;
2. one real adapter imports or exports through an explicit contract;
3. adapter provenance remains visible through the existing governance and bundle
   surfaces;
4. the new surface provides user-visible leverage beyond CLI-only export.

Acceptance evidence:

1. one design note for the chosen surface and adapter contract;
2. integration tests over the richer surface or adapter path;
3. one notebook or scripted operator proof using the new boundary.

Build order:

1. choose the next surface and adapter explicitly;
2. add the adapter contract second;
3. implement one adapter and one surface proof third.

Non-goals:

1. all v1 adapters at once;
2. a large new MCP surface just because v1 had one.

Proved:

1. the richer agent-facing boundary is now a thin FastMCP surface in
   `src/onto_canon6/mcp_server.py` rather than a second workflow runtime;
2. the first recovered adapter is now a successor-local WhyGame relationship
   adapter in `src/onto_canon6/adapters/whygame_service.py`;
3. the adapter imports WhyGame `RELATIONSHIP` facts through an explicit typed
   contract in `src/onto_canon6/adapters/whygame_models.py`;
4. imported WhyGame provenance now remains visible through the existing review,
   artifact, and governed-bundle surfaces;
5. the local WhyGame adapter vocabulary is now declared through
   `ontology_packs/whygame_minimal/0.1.0/manifest.yaml` and
   `profiles/whygame_minimal_strict/0.1.0/manifest.yaml`;
6. the slice is covered by `tests/adapters/test_whygame_service.py`,
   `tests/integration/test_mcp_server.py`, and
   `tests/ontology_runtime/test_whygame_minimal.py`;
7. the phase shape is locked locally in
   `docs/adr/0015-recover-phase-14-through-a-thin-mcp-surface-and-a-whygame-relationship-adapter.md`
   and `docs/plans/0009_phase14_agent_surface_and_adapter_shape.md`;
8. the live proof artifact is `notebooks/20_whygame_mcp_slice.ipynb`.

## Phase 15: Broader Epistemics, Corroboration, And Temporal/Inference Recovery [complete]

Goal:

1. recover the remaining v1 belief-management capabilities that the narrow
   Phase 9 slice intentionally deferred.

Build:

1. extend epistemics beyond confidence and supersession where justified;
2. add explicit corroboration and tension signals over promoted graph state;
3. recover temporal or inference behavior only if it still serves the current
   successor thesis.

Acceptance criteria:

1. promoted assertions can carry broader state transitions than supersession
   alone;
2. the system can surface corroborations or tensions over graph state through
   explicit reports or tools;
3. temporal/inference behavior is either proved or explicitly abandoned with
   rationale;
4. epistemic behavior remains extension-local where possible.

Acceptance evidence:

1. one design note over the broadened epistemic model;
2. tests over state transitions, corroboration, and tension behavior;
3. one notebook proof over a small but real conflict/corroboration slice.

Build order:

1. lock the broadened epistemic contract first;
2. wire corroboration and tension signals second;
3. add temporal or inference work only if the earlier slices justify it.

Non-goals:

1. a full truth-maintenance platform in one phase;
2. speculative inference features without a real workflow.

Proved:

1. the broadened successor epistemic slice now stays extension-local under
   `src/onto_canon6/extensions/epistemic/` instead of relocating epistemic
   policy into the graph store or a new workflow runtime;
2. promoted assertions can now carry explicit `active`, `weakened`, and
   `retracted` disposition history, while `superseded` remains derived from
   the existing candidate-level supersession seam;
3. corroboration groups are now derived deterministically from non-terminal
   promoted assertions that share the same canonical normalized assertion body;
4. tension pairs are now derived deterministically from non-terminal promoted
   assertions that share entity-role anchors but differ in one or more role
   fillers;
5. the new assertion-level epistemic report is exposed through
   `src/onto_canon6/surfaces/epistemic_report.py` and the CLI commands
   `record-assertion-disposition` and `export-assertion-epistemic-report`;
6. the slice is covered by `tests/extensions/test_epistemic_service.py`,
   `tests/integration/test_epistemic_cli.py`, and the live proof notebook
   `notebooks/21_phase15_epistemic_corroboration_slice.ipynb`;
7. temporal/inference recovery is now explicitly deferred rather than left
   ambiguous, with the local rationale locked in
   `docs/adr/0016-recover-phase-15-through-extension-local-promoted-assertion-dispositions-and-derived-corroboration.md`
   and `docs/plans/0010_phase15_epistemic_corroboration_shape.md`.

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

These are the remaining open questions for the successor beyond the bootstrap:

1. what exact promotion target should define the recovered canonical graph;
2. whether external identity should remain Wikidata-first or become a broader
   external-reference model;
3. how much of the v1 semantic stack should be retained versus intentionally
   replaced;
4. which richer surface or adapter should recover first after the CLI;
5. whether temporal or inference behavior ever deserves re-entry into the
   successor after the explicit Phase 15 deferral;
6. how much broader benchmark coverage is needed before Phase 5 results should
   be treated as stronger quality evidence.

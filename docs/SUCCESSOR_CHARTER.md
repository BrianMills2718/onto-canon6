# onto-canon6 Successor Charter

Updated: 2026-03-18

## Purpose

This document is the local strategic anchor for `onto-canon6`.

It exists to keep the project from repeating the drift that happened across
`onto-canon` through `onto-canon5`. It consolidates, in one place:

1. why `onto-canon6` exists;
2. why the project is not continuing any previous repo directly;
3. what each prior repo should donate;
4. what the long-term plan is;
5. what now counts as drift.

This charter summarizes the accepted ADR direction. The detailed supporting ADR
record still exists in `onto-canon5/docs/adr/` and the active implementation
plan lives in this repo's roadmap plus the explicit v1 capability parity
matrix.

## The Successor Goal

`onto-canon6` is a capability-preserving refactor of the `onto-canon` lineage.

That means the project is trying to recover and extend the useful capabilities
proven in earlier repos while enforcing clear subsystem boundaries that earlier
iterations did not hold.

Phase 10 completed the initial bootstrap roadmap for that goal. It did not, by
itself, finish the broader successor-parity work. The explicit parity ledger now
lives in `docs/plans/0005_v1_capability_parity_matrix.md`.

The intended architecture is:

1. `core`
2. `ontology_runtime`
3. `pipeline`
4. `extensions`
5. `domain_packs`
6. `surfaces`

The project is not trying to become:

1. one dominant workflow service with many concerns braided together;
2. a kernel-only library with no credible path back to user-visible leverage;
3. a runtime centered on one ontology, one domain, or one hardcoded policy;
4. a generic plugin platform before real consumers prove the need.

The local notebook process follows the same discipline:

1. one canonical notebook per end-to-end journey;
2. auxiliary notebooks explicitly classified as deep dives or planning
   companions;
3. phase contracts kept outside the notebook in a machine-readable registry.

Variation in the system should default to one of two forms:

1. configuration when the mechanism stays the same and policy changes;
2. narrow typed extension seams when different implementations are needed.

That distinction is formalized in `docs/adr/0003-prefer-configurable-policies-and-narrow-extension-seams-over-a-general-plugin-framework.md`.

## Candidate Assertions and Source Text

`onto-canon6` treats candidate assertions as reviewable ontology-shaped
proposals, not as replacements for the source text that justified them.

For text-derived flows, this means:

1. raw text or another source artifact remains the primary input and reference;
2. candidate assertions should carry first-class evidence spans grounding them
   in the source;
3. candidate assertions may also carry an optional natural-language gloss for
   review ergonomics;
4. candidate assertions remain reviewable and are not auto-approved merely
   because an extractor produced them.

If an LLM is used in that flow:

1. it must route through `llm_client`;
2. prompts should follow the "goals over rules" principle;
3. prompt templates should live in `prompts/`;
4. the structured output schema remains part of the contract and is not the
   kind of worked example forbidden by the "no examples without approval" rule.

This design decision is formalized in
`docs/adr/0004-keep-text-derived-candidate-assertions-grounded-in-source-evidence-and-route-llm-work-through-llm_client.md`.

## Why onto-canon6 Exists Instead of Continuing an Older Repo

The restart is justified because no prior repo achieved all three of these at
once:

1. preserved user-visible leverage;
2. clean subsystem boundaries;
3. extensible multi-pack and multi-policy runtime behavior.

Each earlier repo got part of the picture right and part wrong.

### Why Not Continue `onto-canon` Directly

`onto-canon` has the richest product leverage in the lineage:

1. extraction;
2. epistemic operations;
3. artifact lineage;
4. adapters;
5. MCP surfaces.

But it is not the right structural base for the successor because too much is
fused together. Product ideas and leaf subsystems should be borrowed, but the
repo shape should not be preserved.

### Why Not Continue `onto-canon2` Directly

`onto-canon2` improved architecture thinking and subsystem boundaries, but it
leaned too far toward architecture-first delivery. It is a donor for
boundaries, contracts, and split thinking, not the direct successor base.

### Why Not Continue `onto-canon3` Directly

`onto-canon3` recovered runtime simplicity and a smaller, more readable style,
but still recenters too much behavior around a small number of strong runtime
objects. It is a donor for ergonomics and simplicity, not the final shape.

### Why Not Continue `onto-canon4` Directly

`onto-canon4` improved contract discipline, profiles, registries, and interop
thinking, but it again drifted toward a central workflow object and let domain
concerns leak inward. It is a donor for contracts and registries, not the repo
to keep extending.

### Why Not Continue `onto-canon5` Directly

`onto-canon5` clarified ontology packs, profiles, and `open|closed|mixed`, but
it also narrowed too far toward a kernel-first restart. Continuing there would
mean unbraiding a repo that is already centered on the wrong strategic thesis
for the successor.

## What We Borrow From Each Prior Repo

Borrowing is by subsystem, not by wholesale port.

### `onto-canon`

Primary donors:

1. user-visible leverage;
2. artifact lineage concepts and registry patterns;
3. epistemic operator ideas;
4. ontology and extraction donor material;
5. MCP and adapter use cases.

Do not inherit:

1. monolithic runtime shape;
2. fused storage, workflow, and tool-handler logic;
3. autonomous governance behavior where human review is actually required.

### `onto-canon2`

Primary donors:

1. subsystem boundaries;
2. kernel versus extension split;
3. migration and contract discipline;
4. traversal and projection thinking.

Do not inherit:

1. architecture-heavy delivery before thin proof;
2. unnecessary day-one module weight;
3. a runtime centered on heavyweight standards before the simpler slice is
   proven.

### `onto-canon3`

Primary donors:

1. runtime simplicity;
2. readable storage and service ergonomics;
3. understandable test style;
4. thin surface patterns.

Do not inherit:

1. one dominant database or service object;
2. blurred ownership between core and extension concerns.

### `onto-canon4`

Primary donors:

1. contract discipline;
2. profile-driven validation posture;
3. extractor registry ideas;
4. deterministic interop contracts;
5. early DoDAF seed material.

Do not inherit:

1. expanding central workflow service;
2. domain logic in core workflow code;
3. speculative plugin/process weight.

### `onto-canon5`

Primary donors:

1. ontology packs;
2. profiles;
3. `open|closed|mixed` semantics;
4. proposal routing and governance ideas;
5. validation and pack-loading donor material.

Do not inherit:

1. kernel-only strategic narrowing;
2. central workflow and ingestion shape;
3. benchmark interpretation that confuses extraction quality with
   canonicalization fidelity.

## Long-Term Plan

The long-term plan is phased and thin-slice driven.

The roadmap in `docs/plans/0001_successor_roadmap.md` is the authoritative
phase document for:

1. build items;
2. success criteria;
3. required acceptance evidence;
4. explicit unresolved questions.

The parity matrix in `docs/plans/0005_v1_capability_parity_matrix.md` is the
authoritative companion for:

1. which major `onto-canon` capabilities are already recovered;
2. which are intentionally narrowed or replaced;
3. which are still deferred.

### Phase 0

Prove ontology runtime contracts, donor loading, policy semantics, and local
validation.

Status: complete

### Phase 1

Persist reviewable candidate and proposal workflow state with configurable
mixed-mode acceptance behavior.

Status: complete

### Phase 2

Recover the first user-visible capability:

1. ingest candidate assertions;
2. attach stronger provenance;
3. support candidate review state transitions;
4. expose a small query and report surface.

Status: complete

### Phase 3

Make accepted governance decisions operational:

1. apply accepted ontology additions into explicit local overlays;
2. keep overlay writeback separate from review actions;
3. make validation and reporting overlay-aware.

Status: complete

### Phase 4

Prove one text-grounded producer integration through `llm_client`:

1. keep raw text primary;
2. extract reviewable candidate assertions;
3. ground them in first-class evidence spans;
4. route them through the same review workflow rather than a side path.

Status: complete

### Phase 5

Measure live extraction quality without conflating support and canonical form:

1. run the text extractor against a small local benchmark slice;
2. judge candidate-assertion reasonableness separately from structural
   validation and exact preferred-form agreement;
3. keep the resulting evidence inspectable through a local notebook proof.

Status: complete

### Phase 6

Expose the proved workflow through a thin operational CLI:

1. keep handlers narrow and service-backed;
2. prefer JSON-first output for scripting and notebook inspection;
3. prove the happy path and one loud failure path end to end.

Status: complete

### Phase 7

Prove a second real pack without changing the core boundaries:

1. keep the ontology pack separate from the profile/policy choice;
2. use one reduced local `dodaf_minimal` pack plus strict and mixed profiles
   over the same vocabulary;
3. prove that the same validation, review, overlay, and CLI surfaces still
   work.

Status: complete

### Phase 8

Recover artifact-backed provenance through a narrow bounded subsystem:

1. start with `source`, `derived_dataset`, and `analysis_result` artifacts;
2. keep artifact links candidate-centered first;
3. expose accepted-assertion lineage by traversal/reporting rather than copied
   storage;
4. keep the path to a broader registry model explicit.

Status: complete

### Phase 9

Recover the first optional epistemic slice without moving epistemic policy into
the base review runtime:

1. keep epistemic state in an extension-local package;
2. start with confidence and supersession over accepted candidate assertions;
3. expose current epistemic status through a typed report surface;
4. keep the path to broader contradiction and tension handling explicit.

Status: complete

### Phase 10

Deliver the first real product-facing workflow without adding a second runtime:

1. keep the outward-facing boundary CLI-backed for the first proof;
2. export one governed JSON bundle over accepted reviewed assertions;
3. include provenance, ontology-governance state, and optional artifact and
   epistemic state in that bundle;
4. keep MCP deferred until a concrete consumer pressures it.

Status: complete

### Phase 11

Recover the canonical graph layer that existed in v1, but without rebuilding
the old fused runtime:

1. promote accepted candidate assertions into durable graph records;
2. recover the first durable entity/assertion graph records without attempting
   the full v1 concept/system-belief layer in the same slice;
3. preserve traceability from promoted graph state back to candidates,
   evidence, proposals, overlays, artifacts, and extension state.

Status: complete

### Phase 12

Recover stable identity and external reference handling:

1. define successor-local stable identity records;
2. add explicit alias, merge, and unresolved-state handling;
3. decide whether v1-style Q-code linkage is retained directly or replaced by a
   broader external-reference model with Wikidata as one provider.

Status: planned

### Phase 13

Recover or explicitly replace the semantic canonicalization stack:

1. make the v1 AMR/PropBank/SUMO/FrameNet/Wikidata stack explicit as retained,
   replaced, or abandoned by layer;
2. implement one credible canonicalization path over promoted assertions;
3. recover explicit repair and recanonicalization behavior for bad graph state.

Status: planned

### Phase 14

Recover one richer external surface and one real adapter:

1. add an agent-facing boundary only if it stays thin and service-backed;
2. recover one real adapter such as WhyGame or DIGIMON through an explicit
   contract;
3. prove user-visible leverage beyond CLI-only governed-bundle export.

Status: planned

### Phase 15

Recover the broader v1 belief-management behaviors:

1. extend epistemics beyond confidence and supersession where justified;
2. add corroboration, tension, and related graph-wide review signals;
3. recover temporal/inference behavior only if it still serves the successor
   thesis.

Status: planned

### Bootstrap Completion vs Successor Completion

The bootstrap roadmap is complete through Phase 10.

The broader successor is not complete until every major v1 capability is
explicitly marked as retained, expanded, replaced, deferred, or abandoned in
`docs/plans/0005_v1_capability_parity_matrix.md`, and every retained/replaced
capability has real proof artifacts.

## Drift Conditions

The following now count as drift and should not happen casually:

1. rebuilding one dominant workflow or service object as the center of the
   system;
2. recentering the project as kernel-only infrastructure with no path back to
   product leverage;
3. moving domain-specific logic into core;
4. collapsing packs, profiles, and policy into one hidden config surface;
5. importing older repos wholesale because they are convenient;
6. treating notebook-free architectural speculation as proof;
7. using notebooks as unstructured scratchpads instead of the canonical
   journey notebook plus explicit registry.

## Authoritative Local Reading Order

If someone needs the local strategic picture in `onto-canon6`, start with:

1. this document;
2. `docs/adr/README.md`;
3. `docs/STATUS.md`;
4. `docs/plans/0001_successor_roadmap.md`;
5. `docs/plans/0005_v1_capability_parity_matrix.md`;
6. `notebooks/README.md`.

If someone needs the deeper donor rationale behind this charter, then read the
supporting donor record in `onto-canon5`:

1. `docs/adr/0001-restart-successor-repo-instead-of-continuing-onto-canon5.md`
2. `docs/adr/0009-borrow-from-the-lineage-by-subsystem-not-by-version.md`
3. `docs/adr/0010-realign-the-successor-with-the-original-refactor-intent.md`
4. `docs/plans/015_lineage_final_synthesis.md`

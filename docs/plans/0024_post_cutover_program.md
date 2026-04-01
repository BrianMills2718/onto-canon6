# Post-Cutover Program

Status: active

Last updated: 2026-03-31
Workstream: successor completion after runtime ownership cutover

## Purpose

Define the authoritative ordered execution program for `onto-canon6` after the
runtime-critical donor cutover.

This plan answers a different question than the other top-level plans:

1. `0001` explains how the bootstrap was completed;
2. `0005` records the full preserved capability vision;
3. `0020` tracks gap-by-gap closure against the broader ecosystem vision;
4. this plan decides what should be worked next, in what order, and what counts
   as completion.

## Program Goal

Move from "self-contained successor runtime with real proofs" to
"stable, adopted, and strategically legible successor."

The program is complete only when all of the following are true:

1. at least one downstream consumer uses `onto-canon6` outputs in a real
   supported workflow rather than only repo-local proofs;
2. the promoted-graph and export contracts have explicit schema-stability rules
   and pass their defined compatibility gate;
3. extraction-quality promotion decisions are governed by measured transfer
   evidence rather than ad hoc prompt churn;
4. deferred parity items are explicitly prioritized, deferred, or abandoned
   based on consumer evidence and written rationale;
5. the repo's top-level docs describe one coherent current program without
   broken navigation or competing authority.

This plan fails if any of the following become true:

1. the repo resumes broad subsystem expansion without clearing the gates below;
2. "adapter exists" is treated as equivalent to "consumer adoption complete";
3. extraction prompt changes are promoted without transfer evidence;
4. deferred parity items drift silently because no document owns the execution
   order after cutover.

## Pre-Made Decisions

These decisions are fixed for this program unless a later ADR changes them:

1. `onto-canon6` remains the owner of the governed-assertion runtime and the
   successor-local ontology/runtime assets it now carries.
2. The full long-term scope remains defined by the parity matrix, not by the
   narrower current implementation frontier.
3. New broad capability tracks do not start by default. Work must advance one
   of the ordered lanes below or it should be deferred.
4. The chunk-level transfer evaluation requirement from ADR 0023 remains real,
   but it is now executed inside this program and Plan 0014 rather than through
   a separate standalone plan file.
5. Optional external consumers such as `research_v3` remain external. Their
   adoption matters, but they are not vendored into this repo.
6. Documentation cleanup should make authority clearer, not create a second
   documentation migration project.

## Ordered Execution Lanes

The program is intentionally ordered. Later lanes may be prepared in parallel,
but they should not be treated as complete or promoted ahead of earlier gates.

### Lane 1. Documentation Authority And Program Integrity

#### Goal

Keep the repo's active contract legible after the cutover.

#### Tasks

1. remove broken "read this next" references from top-level docs;
2. mark completed plans as completed or historical rather than active;
3. keep one current program plan that names the ordered work after cutover;
4. ensure `README.md`, `CLAUDE.md`, `STATUS.md`, and the charter point to the
   same current plan surface.

#### Acceptance

1. top-level reading-order docs do not reference missing local plan files;
2. completed plans no longer masquerade as active work;
3. this plan is cited as the current post-cutover execution authority.

#### Failure Modes

1. stale plan state causes agents to reopen completed work;
2. missing references break the doc graph for new operators;
3. historical records are rewritten so aggressively that provenance is lost.

#### Status

Completed in the current cleanup pass. Broken current-plan references and stale
active-plan labels are now baseline doc defects for future changes, not
acceptable repo drift.

### Lane 2. Consumer Adoption Proof

#### Goal

Convert repo-local adapter proofs into at least one real downstream supported
workflow.

#### Pre-Made Decisions

1. "consumer adoption" means the consuming repo or workflow actually uses the
   outputs, not merely that `onto-canon6` can export them.
2. DIGIMON is the first supported consumer for Lane 2. Foundation Assertion IR
   and `research_v3` remain valid secondary consumers but no longer compete for
   the first proof slot.
3. One adopted workflow is worth more than another new adapter.

#### Decision Update (2026-03-31)

The first supported consumer is now DIGIMON. The current supported workflow is
the thin v1 export/import seam:

1. from the `onto-canon6` repo root, run:
   `.venv/bin/onto-canon6 export-digimon --review-db-path var/progressive_review_v2.sqlite3 --output-dir <export_dir>`
2. from the DIGIMON repo root, run:
   `.venv/bin/python scripts/import_onto_canon_jsonl.py --entities <export_dir>/entities.jsonl --relationships <export_dir>/relationships.jsonl --working-dir <artifact_root> --dataset-name <dataset_name> --force`
3. consume the resulting GraphML artifact through DIGIMON's existing
   entity/relationship retrieval surfaces.

Verified on 2026-03-31 against the real Shield AI review DB:

- export wrote `110` entities and `99` relationships from
  `var/progressive_review_v2.sqlite3`
- DIGIMON imported them into GraphML as `110` nodes and `78` edges
- `16` single-endpoint relationships were skipped by the importer, and the
  remaining delta came from DIGIMON's duplicate-endpoint merge semantics

#### Remaining Gaps Captured By Lane 2

1. DIGIMON's importer must currently be invoked from the DIGIMON repo root
   because `Option/Config2.yaml` is loaded via a relative path.
2. The v1 seam is still flat and lossy: alias memberships, role structure,
   passages, evidence refs, and richer provenance are not exported.
3. The current supported consumer proof is graph materialization plus
   downstream queryability, not a richer passage-aware retrieval contract.
4. DIGIMON's default benchmark lane remains DIGIMON-native. The richer
   convergence experiment still lives under DIGIMON Plan 23.

#### Tasks

1. keep the DIGIMON consumer workflow explicit and truthful;
2. define the exact handoff artifact, invocation path, and success criteria;
3. prove the workflow in the consumer context, not only inside this repo;
4. capture friction: dependency shape, schema mismatches, confidence semantics,
   operator ergonomics, and missing metadata.

#### Acceptance

1. one consumer workflow is documented as supported end to end;
2. the consumer-side invocation path is verified with real data;
3. remaining integration gaps are concrete and prioritized, not speculative.

#### Failure Modes

1. adapter-level export is mistaken for adoption;
2. consumer proof depends on one-off local patching not reflected in docs/code;
3. the workflow proves only happy-path format exchange and not actual use.

#### Exit Artifact

A short consumer integration note or plan update naming:

1. consumer;
2. supported entrypoint;
3. verified dataset/artifact;
4. remaining gaps;
5. owner of the next integration step.

### Lane 3. Schema Stability Gate

#### Goal

Define when the successor contracts are stable enough for other projects to rely
on them.

#### Execution Surface

This lane now executes through
[0026_schema_stability_gate.md](0026_schema_stability_gate.md).

#### Current State

The minimum in-repo compatibility gate is now landed for the four named Lane 3
surfaces, the change-classification policy is written down, and the DIGIMON
consumer-proof question is resolved. Lane 3 is complete; any future richer
DIGIMON automation is follow-on hardening, not part of this lane's closure
criteria.

#### Tasks

1. choose the contract surfaces that matter:
   promoted graph, governed bundle, Foundation IR export, and any live consumer
   boundary adopted in Lane 2;
2. define what counts as a breaking change for each surface;
3. define the evidence required before declaring a surface stable;
4. decide where compatibility checks live: tests, fixtures, snapshot exports, or
   consumer integration verification.

#### Acceptance

1. each named surface has explicit compatibility rules;
2. the repo has at least one reproducible compatibility check for each named
   surface;
3. docs stop using vague phrases such as "schema stabilization" without naming
   the gate.

#### Failure Modes

1. downstream projects consume unstable contracts without warning;
2. changes land that silently reshape exported artifacts;
3. "stable" is declared without any compatibility evidence.

### Lane 4. Extraction Quality Promotion Gate

#### Goal

Make extraction changes evidence-driven enough that prompt/model iteration does
not become undirected churn.

#### Pre-Made Decisions

1. Plan 0014 remains the extraction-quality execution surface.
2. ADR 0023's chunk-level transfer requirement is mandatory before promoting a
   new operational prompt/model pair.
3. Golden-set exact match is necessary but insufficient; reasonableness and
   transfer matter too.

#### Current State

Plan 0014 now carries the explicit promotion policy for this lane. The current
state remains: no compact-family candidate is eligible to replace the live
default yet because prose-heavy chunk transfer is still negative or mixed.

#### Tasks

1. keep the canonical corpora explicit;
2. define the promotion gate for prompt/model changes:
   structural validity, reasonableness, exact-match deltas, and transfer slice
   behavior;
3. run chunk-level transfer evaluation on a held-out slice before live prompt
   promotion;
4. record why a prompt/model is promoted, not only that it won one local run.

#### Acceptance

1. prompt/model promotions cite a reproducible benchmark result;
2. transfer evaluation is part of the promotion record;
3. extraction work can explain whether a regression is in extraction,
   canonicalization, or evaluation.

#### Failure Modes

1. prompt churn without durable evidence;
2. promotion based on one slice that does not transfer;
3. benchmark results that collapse different failure classes into one score.

### Lane 5. Deferred Parity Reprioritization

#### Goal

Turn the parity matrix from a preserved vision ledger into a better-ordered
backlog after the first consumer and stability gates are real.

#### Execution Surface

This lane now executes through
[0027_deferred_parity_reprioritization.md](0027_deferred_parity_reprioritization.md).

#### Pre-Made Decisions

1. Deferred capabilities remain visible unless explicitly abandoned with
   rationale.
2. Reprioritization happens after consumer and schema evidence improves, not
   before.
3. The output should be a tighter order, not a narrower vision.

#### Tasks

1. review parity items against real consumer friction and extraction findings;
2. classify each major deferred area as:
   next-active, protected-deferred, consumer-blocked, or abandoned-with-rationale;
3. identify which parity items need their own execution plans.

#### Acceptance

1. the parity matrix stays authoritative for scope;
2. the next-active deferred items are explicitly named;
3. low-value or obsolete parity ideas are abandoned explicitly rather than left
   ambiguous.

#### Failure Modes

1. the parity matrix becomes an archival wishlist instead of a planning tool;
2. new work starts from intuition rather than the consumer/stability evidence;
3. important deferred capabilities remain architecturally visible but
   operationally unowned forever.

#### Current State

Lane 5 now has an explicit classification surface. The current next-active
order after the active gates is:

1. finish the entity-resolution value proof under Plan 0025;
2. activate [0028_query_browse_surface.md](0028_query_browse_surface.md) for a
   first browse/search surface over promoted knowledge;
3. keep richer DIGIMON interchange consumer-blocked rather than silently
   widening the supported v1 seam.

## Program Order

The default execution order is:

1. Lane 1: documentation authority and program integrity;
2. Lane 2: first consumer adoption proof;
3. Lane 3: schema stability gate;
4. Lane 4: extraction quality promotion gate hardening;
5. Lane 5: deferred parity reprioritization.

Lane 4 may continue in parallel with Lane 2 when it is directly supporting the
chosen consumer workflow, but Lane 5 should not be treated as the next major
implementation frontier until Lanes 2 and 3 have materially advanced.

## Current Recommendations

The highest-value next actions are:

1. finish the documentation authority cleanup and remove broken current-plan
   references;
2. choose the first consumer workflow explicitly and define its end-to-end
   success criteria;
3. write the schema-stability gate in concrete terms instead of leaving it as a
   broad aspiration;
4. keep extraction-quality work under Plan 0014 aligned to the consumer and
   transfer-evidence gates above.

## Relationship To Other Plans

1. `0001_successor_roadmap.md`
   completed historical bootstrap baseline;
2. `0005_v1_capability_parity_matrix.md`
   full preserved scope and capability ledger;
3. `0014_extraction_quality_baseline.md`
   extraction-quality execution surface;
4. `0020_vision_gap_closure.md`
   ecosystem-vision gap tracker;
5. `0021_repo_honesty_and_reproducibility_cleanup.md`
   completed operational hardening plan;
6. `0022_donor_absorption_and_archive_readiness.md`
   mostly completed ownership-transfer plan with residual historical labeling;
7. `0023_24h_successor_ownership_execution_block.md`
   completed execution record for the donor-ownership cutover.

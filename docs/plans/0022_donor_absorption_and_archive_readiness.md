# Donor Absorption And Archive Readiness

Status: active

Last updated: 2026-03-28
Workstream: post-bootstrap reproducibility / successor ownership transfer

## Purpose

Prepare `onto-canon6` to become the stable successor repository before older
`onto-canon` repos are archived.

The goal is not to copy whole donor repos. The goal is to make
`onto-canon6` own every runtime-critical donor asset and code slice it still
depends on, while keeping provenance explicit and avoiding a second round of
lineage sprawl.

This plan converts "bootstrap against donor repos" into
"successor owns the required slice locally."

## Why This Plan Exists

`onto-canon6` has already proved a real workflow, but the repo still assumes:

1. `../onto-canon5` for configured donor profile and ontology-pack roots;
2. `../onto-canon` for `data/sumo_plus.db`;
3. donor profile ids such as `default`, `dodaf`, and `psyop_seed` across tests,
   notebooks, fixtures, and some default workflows.

If older repos are meant to be archived after stabilization, these sibling-repo
dependencies cannot remain part of the canonical runtime contract.

## Acceptance Criteria

This plan is complete only when all of the following are true:

1. The canonical runtime and verification path do not require sibling
   `../onto-canon5` or `../onto-canon` checkouts.
2. Every runtime-critical donor profile, ontology pack, and evaluation asset
   still needed by `onto-canon6` exists locally in this repo or is rebuilt
   locally by a documented command.
3. `config/config.yaml`, `make verify-setup`, and the README describe the same
   local-first ownership model.
4. Tests that are part of the supported verification envelope no longer encode
   sibling-repo paths as the default contract.
5. Imported donor material carries explicit provenance notes: source repo, source
   path, import date, and ownership status.
6. Historical docs and notebooks that still mention donor loading are either:
   updated to the new successor-local contract, or clearly labeled historical.
7. Optional external inputs remain optional. The canonical runtime may skip
   `research_v3`-specific integration when `../research_v3` is absent, but that
   absence must not make the base repo incomplete.

This plan fails if any of the following remain true at stabilization time:

1. a fresh checkout still needs `../onto-canon5` or `../onto-canon` to run the
   canonical runtime;
2. the repo has copied donor material locally, but no one can tell what is now
   owned here versus what is still expected to refresh externally;
3. the migration copies whole donor subsystems whose purpose inside
   `onto-canon6` is still unclear.

## Pre-Made Decisions

These decisions are part of the plan and should not be reopened casually during
execution.

1. `onto-canon6` is the long-term owner of the successor runtime.
2. Donor absorption will be selective, not wholesale. Copy only the required
   assets and narrow code slices that the successor is prepared to maintain.
3. Profile ids and pack ids that appear in proof artifacts, tests, fixtures, and
   notebooks should remain stable during the first absorption pass unless there
   is a clear migration need. Compatibility is more important than cleanup in
   this pass.
4. `research_v3` remains an external consumer/integration surface, not a donor
   runtime dependency to be vendored into this repo.
5. Historical artifacts may remain historically accurate. They do not all need
   rewriting immediately, but they must stop masquerading as the current
   canonical contract.
6. `sumo_plus.db` is the only currently known donor data asset that may justify
   a separate build-or-vendor decision. That decision must be made explicitly,
   not drift in accidentally.

## Current State

### Already Local

The repo already owns several important successor-local assets:

1. local ontology packs:
   - `ontology_packs/dodaf_minimal/0.1.0`
   - `ontology_packs/general_purpose/0.1.0`
   - `ontology_packs/whygame_minimal/0.1.0`
2. local profiles:
   - `profiles/dodaf_minimal_strict/0.1.0`
   - `profiles/dodaf_minimal_mixed/0.1.0`
   - `profiles/general_purpose_open/0.1.0`
   - `profiles/progressive_permissive/0.1.0`
   - `profiles/research_v3_integration/0.1.0`
   - `profiles/whygame_minimal_strict/0.1.0`
3. canonical proof artifacts and smoke path already live inside this repo.

### Still External By Default

The repo still defaults to external donor paths in `config/config.yaml`:

1. `paths.donor_profiles_root: ../onto-canon5/profiles`
2. `paths.donor_ontology_packs_root: ../onto-canon5/ontology_packs`
3. `evaluation.sumo_db_path: ../onto-canon/data/sumo_plus.db`

The setup contract, tests, and docs still encode those sibling-repo
assumptions in multiple places.

### Remaining Donor Surface Before Classification

The following donor material is still reachable through current config and
bootstrap-era fallback paths, but not all of it is equally live:

1. donor profiles in `../onto-canon5/profiles`:
   - `default/1.0.0`
   - `strict/1.0.0`
   - `dodaf/0.1.0`
   - `psyop_seed/0.1.0`
   - `sumo/0.1.0`
   - `contract_influence_seed/0.1.0`
2. donor ontology packs in `../onto-canon5/ontology_packs`:
   - `onto_canon_psyop_seed/0.1.0`
   - `onto_canon_contract_influence_seed/0.1.0`
3. donor evaluation asset in `../onto-canon/data/`:
   - `sumo_plus.db`

Phase 1 inventory is now captured in
`docs/plans/0022a_donor_dependency_inventory.md`. That inventory narrows the
required-now donor set to:

1. `default@1.0.0`
2. `dodaf@0.1.0`
3. `psyop_seed@0.1.0`
4. `onto_canon_psyop_seed@0.1.0`
5. `sumo_plus.db`

The remaining donor profiles and packs are currently classified as historical
or deferred unless a supported workflow reactivates them.

### Confirmed Current References

The current repo still uses donor assumptions in at least these areas:

1. runtime config and setup verification;
2. ontology loader tests that assert donor roots under `onto-canon5`;
3. config tests that assert `../onto-canon/data/sumo_plus.db` as the default;
4. pipeline/review/runtime tests that still exercise `default`, `dodaf`,
   and `psyop_seed`;
5. notebooks and status docs that still describe donor loading as a current
   proved behavior;
6. the default `PROFILE_ID` in the Makefile currently points at `psyop_seed`.

## Scope

### In Scope

1. selective migration of donor profiles that are still part of the successor
   contract;
2. selective migration of donor ontology packs that those profiles still need;
3. an explicit strategy for `sumo_plus.db`;
4. config, docs, tests, Make targets, and setup verification changes needed to
   make the local ownership model true;
5. provenance notes for imported material;
6. historical labeling where older docs/notebooks still describe donor-era
   behavior.

### Out Of Scope

1. wholesale copying of earlier `onto-canon` repos;
2. redesigning the ontology/runtime contracts during migration;
3. new capability tracks unrelated to ownership transfer;
4. vendoring external consumer repos such as `research_v3`;
5. deleting historical archives merely because they still mention donor roots.

## Work Breakdown

### Phase 1. Inventory And Classification

#### Goal

Freeze the actual donor surface before changing it.

Inventory artifact:

- `docs/plans/0022a_donor_dependency_inventory.md`

#### Tasks

1. Build a donor dependency table with one row per item:
   - item type: profile, pack, data asset, code utility, doc-only reference;
   - current source path;
   - current local usage sites;
   - required for canonical runtime yes/no;
   - required for supported tests yes/no;
   - required only for historical proof yes/no;
   - planned disposition: vendor, rebuild, archive-only, or delete reference.
2. Distinguish runtime dependencies from historical references.
3. Distinguish required successor assets from optional parity-preservation assets.

#### Acceptance

The table exists in the repo and is precise enough that an agent could execute
the migration without rediscovering what matters.

#### Concerns

1. It is easy to over-classify historical references as runtime requirements.
2. It is also easy to under-classify a test-only asset that still protects a
   meaningful capability.

### Phase 2. Localize Required Donor Profiles

#### Goal

Move still-required donor profiles under `onto-canon6/profiles/` with explicit
ownership.

#### Planned Profile Tiers

Tier A: absorb first because they are visibly active in runtime/tests/fixtures:

1. `default@1.0.0`
2. `dodaf@0.1.0`
3. `psyop_seed@0.1.0`

Tier B: absorb if they remain part of supported tests, planned parity recovery,
or operator workflow after Phase 2 review:

4. `strict@1.0.0`
5. `sumo@0.1.0`
6. `contract_influence_seed@0.1.0`

#### Tasks

1. Copy each approved donor profile into a successor-local path without changing
   its id/version on the first pass.
2. Add provenance notes adjacent to each imported profile or in a single
   registry file under `profiles/`.
3. Update tests and docs to treat the local copy as canonical.
4. Keep donor-root fallback only if needed temporarily during migration, not as
   the target end state.

#### Acceptance

1. `load_profile()` resolves the absorbed profiles locally by default.
2. Supported tests that use those profiles pass without `../onto-canon5`.
3. The repo can explain where each local profile came from.

#### Concerns

1. `dodaf@0.1.0` is conceptually close to local `dodaf_minimal_*` profiles but
   is not the same thing. Absorbing it preserves compatibility but may increase
   naming clutter.
2. `psyop_seed` is central to proof artifacts and fixtures. Renaming it during
   migration would create avoidable churn.

### Phase 3. Localize Required Donor Packs

#### Goal

Bring in the packs still required by absorbed profiles.

#### Likely Required Packs

1. `onto_canon_psyop_seed@0.1.0`
2. `onto_canon_contract_influence_seed@0.1.0` if `contract_influence_seed`
   remains supported after Phase 2 review

#### Tasks

1. Copy each approved donor pack into `ontology_packs/`.
2. Add provenance notes for each imported pack.
3. Verify that absorbed profiles resolve against successor-local packs.
4. Confirm overlay behavior still works with preserved pack ids.

#### Acceptance

1. `load_ontology_pack()` resolves the absorbed packs locally by default.
2. Overlay pack derivation and existing proof DBs remain compatible.

#### Concerns

1. Overlay naming depends on base pack ids. Any id change would ripple into
   overlay pack references and proof artifacts.
2. Some donor packs may preserve legacy modeling choices that are no longer
   desirable, but the first absorption pass should prioritize ownership and
   compatibility over ontology cleanup.

### Phase 4. Resolve `sumo_plus.db` Ownership

#### Goal

Make `sumo_plus.db` local, reproducible, and explicitly owned.

#### Decision Required

Choose exactly one of the following:

1. vendor the current `sumo_plus.db` into `onto-canon6/data/`;
2. build `sumo_plus.db` locally from source inputs via a documented command;
3. vendor a reduced successor-local subset if the full DB is not actually
   required.

#### Decision Criteria

1. reproducibility;
2. maintenance burden;
3. provenance clarity;
4. ability to support Predicate Canon and ancestor-aware evaluation without
   hidden donor repos;
5. avoidance of accidental silent divergence between multiple DB copies.

#### Tasks

1. Measure which tables and rows are actually used by:
   - `SUMOHierarchy`
   - `PredicateCanon`
   - fidelity / ancestor evaluation
   - progressive extraction passes
2. Pick one ownership model.
3. Update config defaults, tests, scripts, and README to match that choice.
4. If build-based, add a deterministic build target and provenance note.
5. If vendored, add integrity metadata such as source hash or import note.

#### Acceptance

1. supported evaluation/progressive tests run without `../onto-canon/data`;
2. the repo has one documented canonical `sumo_plus.db` path and ownership model.

#### Concerns

1. This is the highest-risk migration item because it is both large and central.
2. A local copy without provenance will become a silent fork.
3. A build pipeline may be cleaner architecturally but can be higher effort than
   the rest of the absorption plan combined.

### Phase 5. Cut Over Config, Tests, And Setup

#### Goal

Make the local-first ownership model operationally true.

#### Tasks

1. Change `config/config.yaml` so local assets are canonical defaults.
2. Update loader tests to assert local ownership, not donor-root location.
3. Update config tests to assert the chosen local `sumo_plus.db` contract.
4. Update `make verify-setup` to stop requiring donor repos once migration is
   complete.
5. Update `README.md`, `docs/STATUS.md`, and relevant plans to describe the new
   contract.
6. Reclassify donor-root notebooks and docs as historical where appropriate.

#### Acceptance

1. `make verify-setup`, `make smoke`, and `make check` pass without donor repos.
2. README and tests describe the same runtime contract.

#### Concerns

1. Docs can lag the code and leave the repo internally contradictory.
2. Some archive plans and historical notebooks should not be rewritten as if
   they were never donor-based; they should be labeled, not falsified.

### Phase 6. Archive Readiness Review

#### Goal

Prove that archiving donor repos will not break the successor.

#### Tasks

1. Run the supported verification surface in an environment where donor repos
   are absent or ignored.
2. Record what still fails.
3. Classify each failure as:
   - real remaining successor dependency;
   - unsupported historical artifact;
   - optional external consumer path.
4. Close the real dependencies before declaring archive readiness.

#### Acceptance

A human can remove or archive `../onto-canon5` and `../onto-canon` without
breaking the canonical runtime of `onto-canon6`.

## Verification Plan

Minimum required verification before closing this plan:

1. `make verify-setup`
2. `make smoke`
3. `make check`
4. targeted loader/runtime tests for each absorbed profile and pack
5. targeted evaluation/progressive tests for the chosen `sumo_plus.db` strategy
6. one explicit "no donor repos present" verification run or equivalent
   simulated isolation run

## Failure Modes And Diagnostics

### Failure Mode 1. Hidden Donor Dependency Still Exists

Symptoms:

1. tests pass only when sibling repos exist;
2. a loader or script resolves donor roots unexpectedly.

Diagnostics:

1. search for `../onto-canon5`, `../onto-canon`, and `sumo_plus.db` path
   assumptions;
2. run setup and verification in an environment without donor repos.

### Failure Mode 2. Local Copy Exists But Ownership Is Unclear

Symptoms:

1. an imported asset exists locally but no one knows whether it is canonical;
2. multiple copies drift quietly.

Diagnostics:

1. inspect provenance notes;
2. compare config defaults with README and tests.

### Failure Mode 3. Compatibility Break During Absorption

Symptoms:

1. proof artifacts or tests using `psyop_seed`, `dodaf`, or overlay packs break;
2. renamed ids ripple through fixtures and notebooks.

Diagnostics:

1. compare profile ids, pack ids, and overlay targets before/after migration;
2. run targeted regression tests around loader and review behavior.

### Failure Mode 4. `sumo_plus.db` Becomes A Silent Fork

Symptoms:

1. two DB copies exist and scripts update one but not the other;
2. evaluation results vary by local path.

Diagnostics:

1. enforce one canonical configured path;
2. record import/build provenance;
3. search scripts for dual-path update logic.

## Uncertainties Requiring Explicit Resolution

These are real open questions, not loose brainstorming.

1. Which donor profiles beyond `default`, `dodaf`, and `psyop_seed` truly belong
   in the supported successor contract?
2. Should `sumo_plus.db` be vendored, rebuilt, or subsetted?
3. Is any donor utility code still needed beyond raw assets, or can the current
   successor runtime already own the whole required behavior?
4. Which historical notebooks should be updated versus labeled archive-only?
5. Do we want a provenance registry file for imported donor assets, or
   per-directory import notes?

No implementation phase should close without writing down the answer to any
uncertainty it resolves.

## Recommended Execution Order

1. complete the dependency table from Phase 1;
2. absorb Tier A donor profiles locally;
3. absorb the packs those profiles require;
4. make the `sumo_plus.db` ownership decision;
5. cut over config, tests, and setup verification;
6. run archive-readiness verification without donor repos;
7. only then decide whether Tier B donor material still needs to move.

## Non-Goals

This plan is not permission to:

1. copy all of `onto-canon5` or `onto-canon`;
2. rewrite the ontology model while migrating it;
3. prune deferred capabilities from the parity ledger;
4. collapse historical run evidence just because it came from the donor era.

## Notes

Archive readiness is a successor milestone, not a cleanup nicety. If
`onto-canon6` is meant to replace older `onto-canon` repos, then selective
donor absorption is part of shipping the successor, not optional polish.

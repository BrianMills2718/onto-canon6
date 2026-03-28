# Donor Dependency Inventory

Status: active snapshot

Last updated: 2026-03-28
Parent plan: `docs/plans/0022_donor_absorption_and_archive_readiness.md`

## Purpose

This document is the Phase 1 dependency table for Plan 0022.

It records the donor-era material that `onto-canon6` still references, how that
material is used today, and the planned disposition for each item. The point is
to remove ambiguity before migration work starts.

## Classification Rules

Each item is classified using these labels:

- `required-now`: needed by the canonical runtime, supported tests, or current
  proof workflow
- `optional-external`: may stay outside this repo because it is an external
  consumer/input, not a donor runtime dependency
- `historical-only`: appears only in archive-era docs/notebooks or parity
  discussion, not in supported runtime/test behavior

Disposition labels:

- `vendor-now`: copy into `onto-canon6` during the first absorption pass
- `decide`: explicit design decision still required before migration
- `keep-external`: leave outside this repo intentionally
- `label-historical`: keep the reference, but stop treating it as current
- `defer`: do not move now; revisit only if the capability becomes active again

## Inventory Summary

The current donor surface is smaller than a wholesale repo copy would imply.

What is clearly live now:

1. donor-root path assumptions in config, setup verification, and loader tests;
2. donor profiles `default@1.0.0`, `dodaf@0.1.0`, and `psyop_seed@0.1.0`;
3. donor pack `onto_canon_psyop_seed@0.1.0`, because `psyop_seed` depends on it;
4. donor data asset `sumo_plus.db`.

What is not clearly live now:

1. donor profiles `strict@1.0.0`, `sumo@0.1.0`, and
   `contract_influence_seed@0.1.0`;
2. donor pack `onto_canon_contract_influence_seed@0.1.0`.

Those items may still matter to long-term parity, but they are not part of the
currently supported successor contract based on the code/tests/docs surveyed
below.

## Root Path Dependencies

| Item | Current source | Current usage sites | Class | Disposition | Notes / concerns |
|---|---|---|---|---|---|
| donor profiles root | `../onto-canon5/profiles` | `config/config.yaml`, `src/onto_canon6/config.py`, `src/onto_canon6/ontology_runtime/loaders.py`, `tests/ontology_runtime/test_loaders.py`, `scripts/verify_setup.py`, `README.md` | required-now | vendor-now | This is still treated as a canonical setup requirement even though local-first search roots already exist. |
| donor ontology packs root | `../onto-canon5/ontology_packs` | `config/config.yaml`, `src/onto_canon6/config.py`, `src/onto_canon6/ontology_runtime/loaders.py`, `tests/ontology_runtime/test_loaders.py`, `scripts/verify_setup.py`, `README.md` | required-now | vendor-now | Only clearly needed today because `psyop_seed` still points at a donor pack. |
| SUMO DB path | `../onto-canon/data/sumo_plus.db` | `config/config.yaml`, `tests/test_config.py`, progressive/evaluation tests, `README.md`, CLI `--sumo-db-path` surfaces, `scripts/fix_over_deepened_constraints.py` | required-now | decide | Highest-risk item. Needs an explicit owner model: vendor, rebuild, or subset. |
| research_v3 output root | `../research_v3/output` | `scripts/verify_setup.py`, `scripts/e2e_integration_test.py`, `README.md` | optional-external | keep-external | This is an external consumer/input path, not donor runtime state. Canonical smoke already degrades gracefully when absent. |

## Donor Profiles

| Profile | Source path | Key usage sites | Class | Disposition | Notes / concerns |
|---|---|---|---|---|---|
| `default@1.0.0` | `../onto-canon5/profiles/default/1.0.0/` | heavily used in `tests/pipeline/test_text_extraction.py`, `tests/pipeline/test_review_service.py`, `tests/ontology_runtime/test_loaders.py`, `tests/ontology_runtime/test_validation.py`, governed-bundle/identity/epistemic tests | required-now | vendor-now | Standalone open baseline profile. No donor pack dependency. Low-risk migration. |
| `dodaf@0.1.0` | `../onto-canon5/profiles/dodaf/0.1.0/` | `tests/pipeline/test_review_service.py`, `tests/ontology_runtime/test_loaders.py`, `tests/ontology_runtime/test_validation.py` | required-now | vendor-now | Inline DM2 rules, not pack-based in the current donor form. Should be absorbed without renaming in first pass. |
| `psyop_seed@0.1.0` | `../onto-canon5/profiles/psyop_seed/0.1.0/` | `Makefile` default `PROFILE_ID`, `tests/pipeline/test_review_service.py`, `tests/ontology_runtime/test_loaders.py`, `tests/ontology_runtime/test_validation.py`, `tests/evaluation/test_prompt_eval_service.py`, `tests/adapters/test_foundation_assertion_export.py`, `tests/fixtures/psyop_eval_slice.json` | required-now | vendor-now | Central proof/profile compatibility anchor. Do not rename on first pass. Depends on donor pack `onto_canon_psyop_seed`. |
| `strict@1.0.0` | `../onto-canon5/profiles/strict/1.0.0/` | no live `load_profile(\"strict\")` or `profile_id=\"strict\"` usage found in `src/`, `tests/`, or `Makefile`; appears in docs/history | historical-only | defer | Do not absorb in Tier A. Revisit only if a supported workflow actually uses it. |
| `sumo@0.1.0` | `../onto-canon5/profiles/sumo/0.1.0/` | no live `load_profile(\"sumo\")` or `profile_id=\"sumo\"` usage found in `src/`, `tests/`, or `Makefile` | historical-only | defer | The repo has many `sumo:` type references, but that is not evidence that the donor `sumo` profile is live. |
| `contract_influence_seed@0.1.0` | `../onto-canon5/profiles/contract_influence_seed/0.1.0/` | no live reference found outside Plan 0022 | historical-only | defer | Preserve in parity discussion only unless the capability is reactivated. |

## Donor Packs

| Pack | Source path | Key usage sites | Class | Disposition | Notes / concerns |
|---|---|---|---|---|---|
| `onto_canon_psyop_seed@0.1.0` | `../onto-canon5/ontology_packs/onto_canon_psyop_seed/0.1.0/` | required indirectly by `psyop_seed`; directly exercised in `tests/ontology_runtime/test_loaders.py`; referenced in proof notebooks via overlay pack ids | required-now | vendor-now | Pack id should remain stable initially because overlay ids derive from it. |
| `onto_canon_contract_influence_seed@0.1.0` | `../onto-canon5/ontology_packs/onto_canon_contract_influence_seed/0.1.0/` | no live reference found in `src/`, `tests/`, `Makefile`, or current README | historical-only | defer | Do not absorb unless `contract_influence_seed` is promoted back into active use. |

## Supporting Files Inside Donor Profile Directories

| Item | Source path | Class | Disposition | Notes / concerns |
|---|---|---|---|---|
| `severity.yaml` for each live donor profile | profile-local alongside each donor manifest | required-now | vendor-now with its profile | Severity policy is part of the profile contract and must travel with the profile. |
| `dm2_crosswalk.yaml` under donor `dodaf` | `../onto-canon5/profiles/dodaf/0.1.0/dm2_crosswalk.yaml` | historical-only | defer | No live reference found in `onto-canon6`. Do not absorb by reflex. |

## Code And Test Surfaces To Cut Over

| Surface | Current dependency | Class | Planned change | Notes / concerns |
|---|---|---|---|---|
| `config/config.yaml` | donor roots + donor `sumo_plus.db` default | required-now | cut over after local assets exist | Config should stop encoding sibling repos as the default contract. |
| `src/onto_canon6/config.py` and `src/onto_canon6/ontology_runtime/loaders.py` | donor-root fields and helpers remain first-class | required-now | keep temporarily, then downgrade donor roots to optional fallback or remove from canonical path | Search order is already local-first; migration is mostly about eliminating the donor-required contract. |
| `tests/ontology_runtime/test_loaders.py` | asserts donor roots under `onto-canon5`; loads donor-only profiles/packs | required-now | rewrite to assert local ownership after absorption | This test currently protects the bootstrap contract, not the intended stable successor contract. |
| `tests/test_config.py` | asserts donor `sumo_plus.db` path as default | required-now | rewrite after `sumo_plus.db` decision | Must change in lockstep with config. |
| progressive/evaluation tests | require donor `sumo_plus.db` path today | required-now | update after `sumo_plus.db` decision | These are real runtime checks, not just doc drift. |
| `scripts/verify_setup.py` | requires `../onto-canon5` and `../onto-canon` | required-now | stop requiring donor repos after migration | Should continue to check optional `research_v3` separately. |
| `Makefile` default `PROFILE_ID ?= psyop_seed` | depends on donor profile today | required-now | keep id, change backing ownership | The id can remain stable while the asset moves local. |
| `scripts/fix_over_deepened_constraints.py` | updates both local and donor `sumo_plus.db` copies | required-now | collapse to one owned DB path | This is a concrete silent-fork risk. |

## Documentation And Notebook Surfaces

| Surface | Current dependency | Class | Planned change | Notes / concerns |
|---|---|---|---|---|
| `README.md` setup section | names donor repos as required siblings | required-now | update after migration | Must stay aligned with `make verify-setup`. |
| `docs/STATUS.md` | still says donor profile/pack loading is a currently proved capability | required-now | rewrite to successor-local ownership wording | The repo has moved beyond pure donor-loading bootstrap. |
| `docs/adr/README.md` | points to `../onto-canon5/docs/adr/` | historical-only | label-historical | This is documentation lineage, not runtime dependency. |
| notebooks such as `02_donor_profile_loading.ipynb` | donor-loading bootstrap narrative | historical-only | label-historical | Keep as historically accurate bootstrap evidence unless a successor-local replacement is needed. |
| archive plans and run notes | donor-era assumptions | historical-only | label-historical | Do not rewrite archival records into fiction. |

## Immediate Conclusions

1. The first absorption pass should be narrower than previously assumed:
   `default`, `dodaf`, `psyop_seed`, `onto_canon_psyop_seed`, and the
   `sumo_plus.db` decision are the real blockers.
2. `strict`, `sumo`, `contract_influence_seed`, and
   `onto_canon_contract_influence_seed` do not currently justify first-pass
   migration.
3. The runtime already has the right structural seam for migration because the
   search order is local-first. The main work is asset ownership transfer and
   contract cleanup, not a loader redesign.
4. `sumo_plus.db` is still the dominant uncertainty. It should be handled as a
   separate decision gate, not folded casually into profile/pack copying.

## Open Questions Carried Forward

1. Should donor-root config fields remain as an optional fallback after archive
   readiness, or should they be removed entirely from the canonical runtime?
2. What provenance format should imported donor assets use:
   one central registry file or per-directory import notes?
3. Is there any supported workflow that truly still needs `strict`, `sumo`, or
   `contract_influence_seed`, or are they parity-only backlog items now?

These questions should be answered explicitly during later phases of Plan 0022.

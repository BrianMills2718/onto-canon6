# Notebook Process

`onto-canon6` now uses a local notebook registry and one canonical journey
notebook.

## Canonical Journey

The main end-to-end user journey is:

- [00_master_governed_text_to_reviewed_assertions.ipynb](00_master_governed_text_to_reviewed_assertions.ipynb)

That notebook is the primary notebook entry point for the current workflow and
now ends in live governed-bundle export, canonical graph promotion, stable
identity, semantic recanonicalization, and broadened promoted-assertion
epistemic reporting rather than a provisional workflow plan.

One important qualification:

1. the canonical journey is mostly live, but its extraction phase is
   intentionally `fixture`-backed;
2. that phase uses a deterministic stand-in that emits the same
   contract-shaped artifact as the real extraction boundary;
3. the live extraction proof remains in
   [08_text_extraction_slice.ipynb](08_text_extraction_slice.ipynb) and
   [10_live_extraction_evaluation.ipynb](10_live_extraction_evaluation.ipynb).

The current Phase 15 auxiliary proof is:

- [21_phase15_epistemic_corroboration_slice.ipynb](21_phase15_epistemic_corroboration_slice.ipynb)

## Registry

The machine-readable notebook contract lives in:

- [notebook_registry.yaml](notebook_registry.yaml)

The typed local validator lives in:

- [`src/onto_canon6/notebook_process.py`](../src/onto_canon6/notebook_process.py)

## Auxiliary Notebook Kinds

Auxiliary notebooks are allowed, but they must be classified in the registry as
one of:

1. `deep_dive`
2. `planning_companion`

They are supporting artifacts, not separate end-to-end journeys, unless the
registry declares them as such.

## Local Rule

If notebook process work changes:

1. update the canonical journey notebook if the main workflow changed;
2. update `notebook_registry.yaml` if phase contracts or notebook roles changed;
3. keep the linked docs/tests/evidence paths aligned;
4. run the local notebook-process validation and notebook execution proof.

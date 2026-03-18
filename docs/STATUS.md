# onto-canon6 Status

Updated: 2026-03-18

## What Is Proven

`onto-canon6` currently proves a narrow review-and-governance slice built on a
typed ontology runtime:

1. typed ontology policy contracts;
2. deterministic `open|closed|mixed` unknown-item handling;
3. donor profile and ontology-pack loading from `onto-canon5`;
4. local assertion validation against donor predicate rules;
5. persisted candidate assertion records;
6. persisted ontology proposal records with deduplicated links from candidates;
7. explicit proposal review decisions with configurable acceptance policy;
8. candidate-level review decisions with loud transition rules;
9. provenance-aware candidate submissions;
10. a typed report surface for filtered candidate and proposal views;
11. explicit overlay application records with deterministic idempotent writeback;
12. overlay-aware validation after accepted predicate additions are applied;
13. typed text-grounded candidate-import contracts;
14. persisted optional source text, optional claim text, and first-class
    evidence spans on candidate assertions;
15. deterministic evidence-span verification before persistence;
16. one `llm_client`-backed raw-text extraction service that uses a prompt
    asset plus structured output to produce candidate assertions;
17. deterministic end-to-end extraction into the existing review workflow
    without bypassing proposal or overlay logic;
18. notebook probes that make the current behavior inspectable;
19. a typed live extraction-evaluation harness that separates reasonableness,
    structural validation, and exact canonicalization fidelity;
20. a first real-model benchmark proof over the local PSYOP evaluation slice;
21. a thin operational CLI over extraction, review, proposal, and overlay
    actions;
22. JSON-first CLI output suitable for scripting and notebook inspection;
23. loud end-to-end CLI proof for both the happy path and a review-transition
    failure path;
24. one canonical journey notebook for the current user-visible workflow;
25. a machine-readable notebook registry that keeps phase contracts outside the
    notebook;
26. a local notebook-process validator plus notebook execution proof;
27. one local second-pack proof with `dodaf_minimal` strict and mixed profiles
    over the same pack vocabulary;
28. proof that the second pack uses the same runtime, review, overlay, and CLI
    surfaces without core branching;
29. one bounded artifact subsystem with typed `source`, `derived_dataset`, and
    `analysis_result` records;
30. candidate-centered artifact support links plus recursive lineage edges over
    persisted artifacts;
31. one typed lineage report surface that exposes direct links and ancestor
    artifacts without hidden metadata blobs;
32. live notebook proof for the narrow Phase 8 artifact-lineage slice;
33. one extension-local epistemic subsystem with typed confidence and
    supersession records over accepted candidate assertions;
34. one typed epistemic report surface that derives current candidate status
    without mutating the base review schema;
35. loud failures when epistemic state is attempted on candidates that are not
    accepted;
36. live notebook proof for the narrow Phase 9 epistemic-extension slice;
37. one typed governed-bundle export surface that composes accepted candidate
    assertions, linked governance state, candidate provenance, artifact
    lineage, and extension-local epistemic state;
38. one CLI command that exports the governed bundle without direct
    module-level Python calls;
39. one live notebook proof for the first product-facing governed-bundle
    workflow;
40. one canonical journey notebook that now ends in a real governed export
    artifact rather than a provisional workflow plan.

Concrete assets:

1. `notebooks/01_policy_contracts.ipynb`
2. `notebooks/02_donor_profile_loading.ipynb`
3. `notebooks/03_validation_slice.ipynb`
4. `notebooks/04_review_slice.ipynb`
5. `notebooks/05_review_reporting_slice.ipynb`
6. `notebooks/06_overlay_application_slice.ipynb`
7. `notebooks/07_text_grounded_import_contract.ipynb`
8. `notebooks/08_text_extraction_slice.ipynb`
9. `notebooks/10_live_extraction_evaluation.ipynb`
10. `notebooks/12_cli_surface.ipynb`
11. `notebooks/00_master_governed_text_to_reviewed_assertions.ipynb`
12. `notebooks/notebook_registry.yaml`
13. `notebooks/README.md`
14. `notebooks/13_dodaf_minimal_second_pack.ipynb`
15. `notebooks/14_artifact_lineage_slice.ipynb`
16. `notebooks/15_epistemic_extension_slice.ipynb`
17. `notebooks/16_governed_bundle_workflow.ipynb`
18. `prompts/extraction/text_to_candidate_assertions.yaml`
19. `prompts/evaluation/judge_candidate_reasonableness.yaml`
20. `src/onto_canon6/pipeline/text_extraction.py`
21. `src/onto_canon6/evaluation/`
22. `src/onto_canon6/cli.py`
23. `src/onto_canon6/__main__.py`
24. `src/onto_canon6/notebook_process.py`
25. `src/onto_canon6/artifacts/`
26. `src/onto_canon6/extensions/epistemic/`
27. `src/onto_canon6/surfaces/lineage_report.py`
28. `src/onto_canon6/surfaces/epistemic_report.py`
29. `src/onto_canon6/surfaces/governed_bundle.py`
30. `ontology_packs/dodaf_minimal/0.1.0/manifest.yaml`
31. `profiles/dodaf_minimal_strict/0.1.0/manifest.yaml`
32. `profiles/dodaf_minimal_mixed/0.1.0/manifest.yaml`
33. tests in `tests/ontology_runtime/`
34. tests in `tests/pipeline/`
35. tests in `tests/evaluation/`
36. tests in `tests/artifacts/`
37. tests in `tests/extensions/`
38. tests in `tests/surfaces/`
39. `tests/integration/test_cli_flow.py`
40. `tests/integration/test_notebook_process.py`
41. `tests/integration/test_dodaf_minimal_cli.py`
42. `src/onto_canon6/surfaces/review_report.py`
43. `src/onto_canon6/pipeline/overlay_service.py`
44. `src/onto_canon6/ontology_runtime/overlays.py`

Planning companion:

1. `notebooks/09_successor_long_term_plan.ipynb`
2. `notebooks/11_future_phase_breakdown.ipynb`

## What Is Not Proven Yet

Still missing:

1. broader benchmark coverage and calibration beyond the first local live slice;
2. any post-Phase-10 outward-facing boundary beyond the governed-bundle CLI
   export, such as MCP or a richer UI.

## Current Donor Dependencies

`onto-canon6` still depends on donor material from `onto-canon5` for:

1. detailed successor ADR source records;
2. first-slice planning history;
3. donor validation profiles;
4. donor ontology packs.

This is acceptable for bootstrap, but it should shrink over time.

The local strategic summary now lives in `docs/SUCCESSOR_CHARTER.md`, so the
repo no longer depends on donor docs for the basic explanation of why the
successor exists and what it is trying to preserve.

## Current Architectural Guardrails

The current direction is:

1. capability-preserving refactor, not kernel-only restart;
2. explicit subsystem boundaries;
3. packs separate from profiles;
4. domain packages outside core;
5. thin-slice proof before broader expansion.
6. one canonical journey notebook per end-to-end workflow, with auxiliary
   notebooks explicitly classified rather than treated as peer journeys.

The current locked strategic decisions are:

1. the first regained user-visible capability is governed review of candidate
   assertions;
2. live extraction evaluation is now explicit and the first operational
   surface is a thin CLI;
3. text-derived candidate assertions should carry first-class evidence spans
   and may also carry an optional natural-language gloss;
4. any LLM-backed extraction path must route through `llm_client` with
   goal-oriented prompts and schema-enforced structured output;
5. the second-pack proof uses a reduced local `dodaf_minimal` pack rather than
   a large donor import;
6. mixed-mode routing and proposal acceptance policy must stay configurable;
7. artifact lineage starts with a narrow three-kind model and
   candidate-centered links before broader registry ergonomics are added;
8. the first epistemic slice stays extension-local and starts with confidence
   plus supersession over accepted candidates only;
9. the first product-facing workflow is a CLI-driven governed-bundle export,
   with MCP deferred until real consumer pressure exists.

The authoritative phase exit criteria and remaining explicit unknowns now live
in `docs/plans/0001_successor_roadmap.md`.

## Current Risks

1. Detailed donor evidence still lives partly in `onto-canon5`.
2. `onto-canon6` now has a real product-facing export workflow, but it still
   exposes that workflow through a bounded CLI artifact rather than a richer
   interactive surface.
3. The extraction boundary now has a real live benchmark slice, but the
   benchmark corpus is still small and not yet calibrated for broader claims.
4. Notebook process validation is local to `onto-canon6`; it is not yet wired
   into the wider workspace hook and graph system.
5. The artifact-lineage slice is intentionally narrow and does not yet answer
   how broad the later artifact taxonomy or deduplication ergonomics should
   become.
6. The second-pack proof is intentionally small and does not yet answer how
   broad a future DoDAF vocabulary should become.
7. The epistemic slice is intentionally narrow and does not yet answer how
   broader contradiction, tension, or graph-wide truth-maintenance behavior
   should be modeled.
8. The roadmap is complete through Phase 10, so any next expansion now needs
   explicit new consumer pressure instead of momentum alone.

## Immediate Next Step

Hold the line after Phase 10 unless a real next consumer or boundary justifies
expanding the roadmap:

1. expand benchmark coverage only if it changes real confidence in the current
   workflow;
2. add MCP only if a concrete consumer needs it over the governed-bundle
   export;
3. extend the roadmap only when a new workflow or integration pressure is
   explicit.

The locked decisions for the latest slices are already explicit
in:

1. `docs/adr/0008-start-artifact-lineage-with-a-narrow-three-kind-model-and-candidate-centered-links.md`
2. `docs/plans/0002_phase8_artifact_lineage_shape.md`
3. `docs/adr/0009-start-epistemic-extension-with-confidence-and-supersession-over-accepted-candidates.md`
4. `docs/plans/0003_phase9_epistemic_shape.md`
5. `docs/adr/0010-choose-cli-driven-governed-bundle-export-as-the-first-product-facing-workflow.md`
6. `docs/plans/0004_phase10_governed_bundle_shape.md`

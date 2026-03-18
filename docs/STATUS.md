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
    surfaces without core branching.

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
15. `prompts/extraction/text_to_candidate_assertions.yaml`
16. `prompts/evaluation/judge_candidate_reasonableness.yaml`
17. `src/onto_canon6/pipeline/text_extraction.py`
18. `src/onto_canon6/evaluation/`
19. `src/onto_canon6/cli.py`
20. `src/onto_canon6/__main__.py`
21. `src/onto_canon6/notebook_process.py`
22. `ontology_packs/dodaf_minimal/0.1.0/manifest.yaml`
23. `profiles/dodaf_minimal_strict/0.1.0/manifest.yaml`
24. `profiles/dodaf_minimal_mixed/0.1.0/manifest.yaml`
25. tests in `tests/ontology_runtime/`
26. tests in `tests/pipeline/`
27. tests in `tests/evaluation/`
28. `tests/integration/test_cli_flow.py`
29. `tests/integration/test_notebook_process.py`
30. `tests/integration/test_dodaf_minimal_cli.py`
31. `src/onto_canon6/surfaces/review_report.py`
32. `src/onto_canon6/pipeline/overlay_service.py`
33. `src/onto_canon6/ontology_runtime/overlays.py`

Planning companion:

1. `notebooks/09_successor_long_term_plan.ipynb`
2. `notebooks/11_future_phase_breakdown.ipynb`

## What Is Not Proven Yet

Still missing:

1. broader benchmark coverage and calibration beyond the first local live slice;
2. artifact-lineage recovery;
3. epistemic extension;
4. product-facing end-to-end workflow beyond CLI, notebooks, and Python API
   use.

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
6. mixed-mode routing and proposal acceptance policy must stay configurable.

The authoritative phase exit criteria and remaining explicit unknowns now live
in `docs/plans/0001_successor_roadmap.md`.

## Current Risks

1. Detailed donor evidence still lives partly in `onto-canon5`.
2. `onto-canon6` now proves a text-grounded import workflow structurally, but
   it still exposes that workflow only through notebooks, Python APIs, and the
   narrow first CLI.
3. The extraction boundary now has a real live benchmark slice, but the
   benchmark corpus is still small and not yet calibrated for broader claims.
4. Notebook process validation is local to `onto-canon6`; it is not yet wired
   into the wider workspace hook and graph system.
5. The second-pack proof is intentionally small and does not yet answer how
   broad a future DoDAF vocabulary should become.

## Immediate Next Step

Start Phase 8 with one narrow artifact-lineage proof that recovers one of the
strongest v1 donor capabilities without rebuilding a fused runtime:

1. define the minimal typed artifact reference model and persistence boundary;
2. start with `source`, `derived_dataset`, and `analysis_result` artifact kinds;
3. link artifacts to candidate assertions first and derive accepted-assertion
   lineage by traversal/reporting rather than copied storage;
4. prove one workflow where a claim is supported by an analysis artifact rather
   than only raw text.

The path to a broader lineage model is now explicit in:

1. `docs/adr/0008-start-artifact-lineage-with-a-narrow-three-kind-model-and-candidate-centered-links.md`
2. `docs/plans/0002_phase8_artifact_lineage_shape.md`

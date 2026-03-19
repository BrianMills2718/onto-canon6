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
41. one narrow canonical-graph subsystem with durable promoted assertion,
    promoted entity, and promoted role-filler tables;
42. explicit promotion from accepted candidates into deterministic durable
    graph records;
43. one typed promoted-graph report surface that traverses candidate-backed
    proposal, overlay, artifact, and epistemic context without duplicating it
    into the graph tables;
44. thin CLI commands for promotion, promoted-assertion listing, and promoted
    graph report export;
45. one live notebook proof for the first canonical-graph recovery slice;
46. one canonical journey notebook phase that now continues from governed
    bundle export into explicit graph promotion.
47. one bounded stable-identity subsystem with explicit local identity rows,
    identity memberships, and external-reference records over promoted
    entities;
48. deterministic identity reuse for repeated promoted entity ids;
49. explicit alias membership and explicit attached or unresolved external
    reference state;
50. thin CLI commands for identity creation, alias attachment, external
    reference recording, identity listing, and identity report export;
51. one live notebook proof for the first stable-identity slice;
52. one canonical journey notebook phase that now continues from graph
    promotion into stable identity creation and external-reference state.
53. one bounded semantic canonicalization subsystem that explicitly replaces
    the v1 hard semantic stack with pack-driven predicate and role
    canonicalization over promoted assertions;
54. explicit persisted recanonicalization events over promoted graph state,
    with revalidation before repaired state is written;
55. thin CLI commands for promoted-assertion recanonicalization, repair-event
    listing, and semantic repair report export;
56. one live notebook proof for the first semantic canonicalization slice, and
    a canonical journey notebook phase that now continues from stable identity
    into explicit semantic repair.
57. one thin FastMCP server over the proved successor services rather than a
    second workflow runtime;
58. one explicit successor-local WhyGame relationship adapter that imports
    WhyGame `RELATIONSHIP` facts into candidate assertions;
59. one local `whygame_minimal` pack and strict profile that give the adapter a
    typed successor-local ontology target;
60. optional WhyGame artifact registration and candidate-to-artifact links that
    keep imported provenance visible through governed bundles;
61. integration proof that the MCP surface can import WhyGame facts, review
    candidates, promote candidates, and export a governed bundle.
62. one broadened extension-local promoted-assertion epistemic slice with
    explicit `active`, `weakened`, and `retracted` disposition events;
63. derived promoted-assertion `superseded` state that still stays grounded in
    candidate-level supersession rather than a second manual path;
64. deterministic corroboration groups and deterministic role-filler tension
    pairs over promoted graph state;
65. thin CLI commands for promoted-assertion disposition recording and
    assertion-level epistemic report export;
66. one live notebook proof for the Phase 15 promoted-assertion epistemic
    slice.

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
18. `notebooks/17_canonical_graph_recovery_slice.ipynb`
19. `notebooks/18_stable_identity_slice.ipynb`
20. `notebooks/19_semantic_canonicalization_slice.ipynb`
21. `notebooks/20_whygame_mcp_slice.ipynb`
22. `notebooks/21_phase15_epistemic_corroboration_slice.ipynb`
23. `prompts/extraction/text_to_candidate_assertions.yaml`
24. `prompts/evaluation/judge_candidate_reasonableness.yaml`
25. `src/onto_canon6/pipeline/text_extraction.py`
26. `src/onto_canon6/evaluation/`
27. `src/onto_canon6/cli.py`
28. `src/onto_canon6/__main__.py`
29. `src/onto_canon6/notebook_process.py`
30. `src/onto_canon6/artifacts/`
31. `src/onto_canon6/core/`
32. `src/onto_canon6/extensions/epistemic/`
33. `src/onto_canon6/surfaces/lineage_report.py`
34. `src/onto_canon6/surfaces/epistemic_report.py`
35. `src/onto_canon6/surfaces/governed_bundle.py`
36. `src/onto_canon6/surfaces/graph_report.py`
37. `src/onto_canon6/surfaces/identity_report.py`
38. `src/onto_canon6/surfaces/semantic_report.py`
39. `src/onto_canon6/mcp_server.py`
40. `src/onto_canon6/adapters/`
41. `ontology_packs/dodaf_minimal/0.1.0/manifest.yaml`
42. `profiles/dodaf_minimal_strict/0.1.0/manifest.yaml`
43. `profiles/dodaf_minimal_mixed/0.1.0/manifest.yaml`
44. `ontology_packs/whygame_minimal/0.1.0/manifest.yaml`
45. `profiles/whygame_minimal_strict/0.1.0/manifest.yaml`
46. tests in `tests/ontology_runtime/`
47. tests in `tests/pipeline/`
48. tests in `tests/evaluation/`
49. tests in `tests/artifacts/`
50. tests in `tests/core/`
51. tests in `tests/extensions/`
52. tests in `tests/surfaces/`
53. tests in `tests/adapters/`
54. `tests/integration/test_cli_flow.py`
55. `tests/integration/test_graph_cli.py`
56. `tests/integration/test_identity_cli.py`
57. `tests/integration/test_semantic_cli.py`
58. `tests/integration/test_epistemic_cli.py`
59. `tests/integration/test_notebook_process.py`
60. `tests/integration/test_dodaf_minimal_cli.py`
61. `tests/integration/test_mcp_server.py`
62. `src/onto_canon6/surfaces/review_report.py`
63. `src/onto_canon6/pipeline/overlay_service.py`
64. `src/onto_canon6/ontology_runtime/overlays.py`

Planning companion:

1. `notebooks/09_successor_long_term_plan.ipynb`
2. `notebooks/11_future_phase_breakdown.ipynb`

## What Is Not Proven Yet

Still missing:

1. broader benchmark coverage and calibration beyond the first local live slice;
2. the broader v1 concept/belief graph and system-belief layer beyond the
   first promoted-assertion/entity slice;
3. broader identity recovery beyond the first promoted-entity identity slice;
4. broader producer-side semantic adapters beyond the first pack-driven
   canonicalization replacement slice;
5. any richer interactive surface beyond the new thin MCP slice, such as a UI
   or a broader MCP tool set;
6. any recovered DIGIMON adapter path;
7. temporal/inference recovery and any broader truth-maintenance behavior
   beyond the explicit Phase 15 slice.

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
8. epistemic behavior stays extension-local: candidate confidence/supersession
   remain separate from promoted-assertion dispositions and derived
   corroboration/tension reporting;
9. the first product-facing workflow is still the governed-bundle export, and
   the first richer agent boundary is now a thin FastMCP wrapper over proved
   services rather than a second runtime.
10. canonical graph recovery stays explicit and bounded: accepted candidates
    promote into durable graph records, while governance and provenance
    context is traversed through the source candidate rather than duplicated.
11. stable identity also stays explicit and bounded: promoted entities map into
    local identities through reviewed membership rather than automatic linking.
12. semantic canonicalization also stays explicit and bounded: promoted graph
    state is repaired through pack-declared aliases and auditable
    recanonicalization events rather than a hidden hard-wired semantic stack.

The authoritative phase exit criteria and remaining explicit unknowns now live
in `docs/plans/0001_successor_roadmap.md`.

The authoritative parity ledger for the broader successor now lives in
`docs/plans/0005_v1_capability_parity_matrix.md`.

## Current Risks

1. Detailed donor evidence still lives partly in `onto-canon5`.
2. `onto-canon6` now has a thin MCP surface and a recovered WhyGame adapter,
   but the richer surface is still intentionally much smaller than the v1 MCP
   server.
3. The extraction boundary now has a real live benchmark slice, but the
   benchmark corpus is still small and not yet calibrated for broader claims.
4. Notebook process validation is local to `onto-canon6`; it is not yet wired
   into the wider workspace hook and graph system.
5. The artifact-lineage slice is intentionally narrow and does not yet answer
   how broad the later artifact taxonomy or deduplication ergonomics should
   become.
6. The second-pack proof is intentionally small and does not yet answer how
   broad a future DoDAF vocabulary should become.
7. The epistemic slice is now broader over promoted assertions, but it still
   intentionally defers temporal/inference recovery and broader
   truth-maintenance machinery.
8. Phase 10 completed the bootstrap roadmap, but the successor still has
   explicit parity gaps against `onto-canon`.
9. Phase 12 recovered the first stable-identity slice, but broader identity
   and DIGIMON-style adapter recovery are still not implemented.
10. Phase 13 replaced the first semantic-stack slice, but broader producer-side
   semantic adapters and richer pack metadata are still not implemented.
11. Phase 15 recovered promoted-assertion corroboration/tension and broader
   disposition state, but temporal/inference are still explicitly deferred.

## Immediate Next Step

The current roadmap is now proved through Phase 15.

There is no automatic “Phase 16” until a new roadmap extension is justified.
The repo should now:

1. use `docs/plans/0005_v1_capability_parity_matrix.md` as the feature ledger;
2. treat the current roadmap as the proved bounded successor core, not as full
   v1 parity;
3. run at least one real non-fixture investigation or consumer workflow through
   extract -> review -> promote -> export before opening a new broad parity
   phase;
4. capture the friction, breakage, and missing value from that real run as the
   justification record for any later roadmap extension;
5. require explicit workflow pressure before reopening temporal/inference work
   or another broad parity-recovery phase;
6. prefer the smallest next product-facing or parity-closing slice if a new
   roadmap extension is needed.

The locked decisions for the latest slices are already explicit
in:

1. `docs/adr/0008-start-artifact-lineage-with-a-narrow-three-kind-model-and-candidate-centered-links.md`
2. `docs/plans/0002_phase8_artifact_lineage_shape.md`
3. `docs/adr/0009-start-epistemic-extension-with-confidence-and-supersession-over-accepted-candidates.md`
4. `docs/plans/0003_phase9_epistemic_shape.md`
5. `docs/adr/0010-choose-cli-driven-governed-bundle-export-as-the-first-product-facing-workflow.md`
6. `docs/plans/0004_phase10_governed_bundle_shape.md`
7. `docs/adr/0011-treat-phase-10-as-bootstrap-completion-and-track-v1-capability-parity-explicitly.md`
8. `docs/plans/0005_v1_capability_parity_matrix.md`
9. `docs/adr/0012-start-canonical-graph-recovery-with-explicit-promotion-from-accepted-candidates.md`
10. `docs/plans/0006_phase11_graph_promotion_shape.md`
11. `docs/adr/0013-start-stable-identity-with-promoted-entity-identities-alias-membership-and-explicit-external-reference-state.md`
12. `docs/plans/0007_phase12_identity_shape.md`
13. `docs/adr/0014-replace-the-v1-semantic-stack-with-pack-driven-canonicalization-and-explicit-recanonicalization.md`
14. `docs/plans/0008_phase13_semantic_canonicalization_shape.md`
15. `docs/adr/0016-recover-phase-15-through-extension-local-promoted-assertion-dispositions-and-derived-corroboration.md`
16. `docs/plans/0010_phase15_epistemic_corroboration_shape.md`

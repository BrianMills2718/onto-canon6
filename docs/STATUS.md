# onto-canon6 Status

Updated: 2026-04-02

## Current Program

The current long-term execution authority is split deliberately:

1. `docs/plans/0005_v1_capability_parity_matrix.md`
   preserved full capability vision;
2. `docs/plans/0024_post_cutover_program.md`
   current ordered execution program and gates;
3. `docs/plans/0020_vision_gap_closure.md`
   gap-by-gap closure tracking against the broader ecosystem vision.

This status page is intentionally narrower: it records what is already proved
and where the repo still has real operational risk.

Current post-cutover program state:

1. Lane 2 consumer adoption is satisfied for the current thin DIGIMON v1 seam;
2. Lane 3 schema stability is closed through
   `docs/plans/0026_schema_stability_gate.md`;
3. Lane 4 now has an explicit promotion policy in
   `docs/plans/0014_extraction_quality_baseline.md`;
4. the first read-only query surface is now landed and proved through
   `docs/plans/0028_query_browse_surface.md` and
   `docs/plans/0029_24h_query_surface_execution_block.md`;
5. Plan 0025 is now complete at the Phase 4 value-proof level;
6. Plan 0039 proved rerun stability at the question/safety gate with two fresh
   reruns (`145141`, `152927`) that both held `10/10` question accuracy,
   precision `1.00`, and false merges `0`;
7. Plan `0040` is now complete and decided the compact operational-parity lane
   is not yet promotable;
8. Plan `0041` is now complete and proved the remaining prompt-surface delta is
   stable and bounded, not the dominant blocker family;
9. Plan `0042` is now complete and proved that one more narrow semantic prompt
   revision was not enough to recover live chunk transfer;
10. Plan `0043` is now complete and proved the remaining same-model divergence
    begins before review and is then amplified by review/judge acceptance;
11. Plan `0044` is now complete and proved wrapper alignment did not narrow
    the chunk-003 divergence;
12. Plan `0045` is now complete and proved live had omitted `temperature=0.0`,
    but temperature/source-ref alignment still did not recover chunk-003
    transfer;
13. Plans `0046` through `0049` are now complete: sync/async path speculation,
    `Case id` metadata, and prompt_eval wrapper drift are no longer the active
    blockers on chunk `003`;
14. Plan `0051` is now complete and proved that section-level analytical
    suppression did not shrink the repaired chunk-003 spillover family;
15. Plan `0052` is now complete and proved predicate-local gating can shrink
    the spillover family, but not close it;
16. Plan `0053` is now complete and proved that even stronger hard-negative
    prompt rules did not close the full chunk-003 residual;
17. Plan `0054` is now complete and proved the remaining blocker is a
    benchmark-contract question, not another prompt-wording diagnosis block;
18. the chunk-017 contract cutover is complete under Plan `0055`;
19. the next extraction-quality blocker is the corrected-fixture semantic
    family `001`, `002`, `007`, and `008`, now owned by Plan `0056`.

## What Is Proven

`onto-canon6` currently proves a narrow review-and-governance slice built on a
typed ontology runtime:

1. typed ontology policy contracts;
2. deterministic `open|closed|mixed` unknown-item handling;
3. successor-local profile and ontology-pack loading from this repo;
4. local assertion validation against explicit local predicate rules;
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
21. config-backed prompt provenance on both extraction and benchmark-judge
    calls;
22. shared experiment run, item, and aggregate logging for the live benchmark
    path;
23. a thin operational CLI over extraction, review, proposal, and overlay
    actions;
24. JSON-first CLI output suitable for scripting and notebook inspection;
25. loud end-to-end CLI proof for both the happy path and a review-transition
    failure path;
26. one canonical journey notebook for the current user-visible workflow;
27. a machine-readable notebook registry that keeps phase contracts outside the
    notebook;
28. a local notebook-process validator plus notebook execution proof;
29. one local second-pack proof with `dodaf_minimal` strict and mixed profiles
    over the same pack vocabulary;
30. proof that the second pack uses the same runtime, review, overlay, and CLI
    surfaces without core branching;
31. one bounded artifact subsystem with typed `source`, `derived_dataset`, and
    `analysis_result` records;
32. candidate-centered artifact support links plus recursive lineage edges over
    persisted artifacts;
33. one typed lineage report surface that exposes direct links and ancestor
    artifacts without hidden metadata blobs;
34. live notebook proof for the narrow Phase 8 artifact-lineage slice;
35. one extension-local epistemic subsystem with typed confidence and
    supersession records over accepted candidate assertions;
36. one typed epistemic report surface that derives current candidate status
    without mutating the base review schema;
37. loud failures when epistemic state is attempted on candidates that are not
    accepted;
38. live notebook proof for the narrow Phase 9 epistemic-extension slice;
39. one typed governed-bundle export surface that composes accepted candidate
    assertions, linked governance state, candidate provenance, artifact
    lineage, and extension-local epistemic state;
40. one CLI command that exports the governed bundle without direct
    module-level Python calls;
41. one live notebook proof for the first product-facing governed-bundle
    workflow;
42. one canonical journey notebook that now ends in a real governed export
    artifact rather than a provisional workflow plan;
43. one narrow canonical-graph subsystem with durable promoted assertion,
    promoted entity, and promoted role-filler tables;
44. explicit promotion from accepted candidates into deterministic durable
    graph records;
45. one typed promoted-graph report surface that traverses candidate-backed
    proposal, overlay, artifact, and epistemic context without duplicating it
    into the graph tables;
46. thin CLI commands for promotion, promoted-assertion listing, and promoted
    graph report export;
47. one live notebook proof for the first canonical-graph recovery slice;
48. one canonical journey notebook phase that now continues from governed
    bundle export into explicit graph promotion;
49. one bounded stable-identity subsystem with explicit local identity rows,
    identity memberships, and external-reference records over promoted
    entities;
50. deterministic identity reuse for repeated promoted entity ids;
51. explicit alias membership and explicit attached or unresolved external
    reference state;
52. thin CLI commands for identity creation, alias attachment, external
    reference recording, identity listing, and identity report export;
53. one live notebook proof for the first stable-identity slice;
54. one canonical journey notebook phase that now continues from graph
    promotion into stable identity creation and external-reference state;
55. one bounded semantic canonicalization subsystem that explicitly replaces
    the v1 hard semantic stack with pack-driven predicate and role
    canonicalization over promoted assertions;
56. explicit persisted recanonicalization events over promoted graph state,
    with revalidation before repaired state is written;
57. thin CLI commands for promoted-assertion recanonicalization, repair-event
    listing, and semantic repair report export;
58. one live notebook proof for the first semantic canonicalization slice, and
    a canonical journey notebook phase that now continues from stable identity
    into explicit semantic repair;
59. one thin FastMCP server over the proved successor services rather than a
    second workflow runtime;
60. one explicit successor-local WhyGame relationship adapter that imports
    WhyGame `RELATIONSHIP` facts into candidate assertions;
61. one local `whygame_minimal` pack and strict profile that give the adapter a
    typed successor-local ontology target;
62. optional WhyGame artifact registration and candidate-to-artifact links that
    keep imported provenance visible through governed bundles;
63. integration proof that the MCP surface can import WhyGame facts, review
    candidates, promote candidates, and export a governed bundle;
64. one broadened extension-local promoted-assertion epistemic slice with
    explicit `active`, `weakened`, and `retracted` disposition events;
65. derived promoted-assertion `superseded` state that still stays grounded in
    candidate-level supersession rather than a second manual path;
66. deterministic corroboration groups and deterministic role-filler tension
    pairs over promoted graph state;
67. thin CLI commands for promoted-assertion disposition recording and
    assertion-level epistemic report export;
68. one live notebook proof for the Phase 15 promoted-assertion epistemic
    slice.

Representative proof assets:

1. `notebooks/01_policy_contracts.ipynb`
2. `notebooks/02_donor_profile_loading.ipynb` (historical bootstrap proof)
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

65. a 3-pass progressive disclosure extraction pipeline (Plan 0018): open
    extraction with top-level SUMO seeding → predicate mapping with 78%
    single-sense early exit → entity refinement with narrowed subtree typing;
66. 87.8% predicate resolution on real text (Shield AI findings, 348 lines,
    337 triples, $0.07 total cost);
67. ancestor-aware evaluator with SUMO hierarchy integration (Plan 0017);
68. Predicate Canon bridge: read-only interface to 4,669 predicates and
    11,890 role slots with 78.1% single-sense lemma rate;
69. fidelity experiments proving top-level seeding (50 types, 87.5% ancestor
    match) outperforms mid-level (62.5%) and full-subtree (50%);
70. json_schema response_format with field-level descriptions as a prompting
    surface (18.8% → 87.8% resolution via schema + prompt alone);

## Post-Bootstrap Extraction Quality Work (2026-03-24)

71. discriminated union filler types enforce entity_type and name at JSON
    Schema decode time — LLMs cannot produce null entity_type on entity
    fillers. Three concrete models: ExtractedEntityFiller,
    ExtractedValueFiller, ExtractedUnknownFiller;
72. goal-conditioned extraction: extraction_goal is required on every run,
    narrow goals improve discrimination (3/3 strict-omit cases correct with
    targeted goal);
73. accepted_alternatives in benchmark scoring: precision no longer penalizes
    reasonable extractions not in the golden set;
74. Foundation Assertion IR export adapter with identity subsystem wiring for
    alias_ids;
75. baseline comparison script proves governance layer value (bare SPO-triple
    extraction: 43% entity coverage, no discrimination, fragmented triples);
76. model_override config for pinning specific models (currently
    `gemini/gemini-2.5-flash` after `gemini-3-flash-preview` regressed);
77. single_response_hardened promoted as operational prompt (4/4 structural
    on gpt-5.4-mini, 0 errors);
78. composability principle documented: vocabulary, extensions, extraction
    strategy, and resolution strategies are pluggable;
79. second vocabulary proof: `dodaf_minimal` pack with `dm2:OperationalNode`
    and `dm2:InformationElement` entity types, 7 candidates extracted with
    100% validation using the same runtime and review pipeline (Plan 0020
    Gap 9);
80. non-military domain testing: financial (SEC/crypto, 82% structural
    validity) and academic (climate research) text extraction with psyop_seed
    and general_purpose_open profiles (Plan 0020 Gap 2);
81. automated entity resolution: `auto_resolution.py` groups promoted entities
    by normalized display name, creates identities with canonical/alias
    memberships, proven on USSOCOM across 2 source chunks (Plan 0020 Gap 3);
82. temporal qualifiers: `valid_from` and `valid_to` as optional ISO 8601
    fields in extraction, payload storage, and Foundation IR export
    (`sys:valid_from`, `sys:valid_to`). Proven: SEC complaint 2023-06-05,
    Zhao tenure end 2023-11 (Plan 0020 Gap 4);
83. DIGIMON supported v1 consumer proof: 110 entities + 99 relationships from
    the real Shield AI promoted graph exported as JSONL and imported into
    DIGIMON GraphML as 110 nodes + 78 edges. 16 single-endpoint relationships
    were skipped by the importer; the remaining relationship delta came from
    DIGIMON duplicate-endpoint merge semantics (Plan 0020 Gap 5);
84. research_v3 import adapter: FtM entity types mapped to onto-canon6 types
    (15 schemas), corroboration status to confidence scores. 48 claims from
    real Booz Allen lobbying investigation imported into review pipeline
    (Plan 0020 Gap 6);
85. epistemic engine on real data: 16 assertions scored with varying
    confidence (0.65-0.95), 1 supersession recorded, 19 tension pairs
    detected (5 USSOCOM commanders → role_filler_conflict), 1 assertion
    weakened (Plan 0020 Gap 7);
86. ProbLog rule evaluation: 16 facts from onto-canon6 SQLite → 45 derived
    facts with probability propagation. Product semantics: P(authority_over)
    = P(commands) × P(belongs_to). Decision: use ProbLog (Plan 0020 Gap 8);
87. repo-local OpenClaw mission artifacts drafted: `.openclaw/success-criteria.yaml`
    with measurable criteria and `.openclaw/mission-spec.yaml` with a
    Makefile-oriented execution contract. This proves the repo-side
    specification exists, not yet that the OpenClaw runner consumes it
    correctly (Plan 0020 Gap 10);
88. general-purpose ontology pack: 15 entity types (person, organization,
    company, government_org, legal_entity, location, event, etc.) and 10
    generic predicates with open profile (general_purpose_open);
89. enhanced observability: `make summary` reports identity resolution stats
    (total, multi-member, auto-resolved) and epistemic stats (confidence
    scores, averages);
90. consumer-path building blocks proven separately: extraction → review →
    promotion → DIGIMON export/import/query; research_v3 graph.yaml →
    onto-canon6 candidate import; Foundation IR export over promoted
    assertions. Full consumer-side adoption is still pending.

## What Is Not Proven Yet

Still missing:

1. extraction quality improvement — API reliability (55% timeout rate in
   experiment) and empty-roles issue are the primary bottlenecks, not prompt
   quality. Operational prompt works; experiment variants need rework;
2. one-command consumer-side adoption flow; the stitched proof exists, but no
   consumer currently runs the full path as part of its own normal workflow;
3. entity resolution across 2+ independent extraction runs with fuzzy or
   external-reference strategies; exact-name auto-resolution is proven, broader
   resolution is not;
4. cross-investigation conflict detection on real data; single-run tension
   detection is proven, but contradiction policy across multiple investigations
   is not;
5. broader benchmark coverage beyond 17 PSYOP military cases;
6. the broader v1 concept/belief graph and system-belief layer beyond the
   first promoted-assertion/entity slice;
7. broader producer-side semantic adapters beyond pack-driven canonicalization;
8. any richer interactive surface beyond the thin MCP slice;
9. OpenClaw mission-runner consumption of repo-local `.openclaw` contracts;
10. temporal/inference recovery (deferred by ADR).

## Current Donor Dependencies

`onto-canon6` no longer depends on sibling donor repos for its canonical
runtime. Remaining donor-era dependency is now primarily historical:

1. detailed successor ADR source records;
2. first-slice planning history;
3. archived bootstrap notebooks and run records.

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
   It now emits shared experiment records, but `prompt_eval`-driven
   prompt/model iteration is still optional rather than wired by default.
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
8. Phases 0-15 completed the current bootstrap roadmap, but the successor still has
   explicit parity gaps against `onto-canon`.
9. Phase 12 recovered the first stable-identity slice, but broader identity
   and DIGIMON-style adapter recovery are still not implemented.
10. Phase 13 replaced the first semantic-stack slice, but broader producer-side
   semantic adapters and richer pack metadata are still not implemented.
11. Phase 15 recovered promoted-assertion corroboration/tension and broader
   disposition state, but temporal/inference are still explicitly deferred.
12. First-pass extraction quality is below baseline: 37.5% acceptance rate
   on Stage 1 corpus, with distinct failure modes (alias self-references,
   wrong predicate choices, unattributed opinion claims). Active plan:
   `docs/plans/0014_extraction_quality_baseline.md`.

## Immediate Next Step

The current roadmap is now proved through Phase 15.

The first real non-fixture workflow run has now been completed over local PSYOP
research outputs. See:

1. `docs/plans/0011_first_real_run_psyop_stage1.md`
2. `docs/runs/2026-03-18_psyop_stage1_run_summary.md`
3. `docs/runs/2026-03-18_psyop_stage1_friction_log.md`

A second real cross-project consumer run has also been completed over local
`research-agent` Shield AI relationship output. See:

1. `docs/plans/0012_research_agent_shield_ai_whygame_run.md`
2. `docs/runs/2026-03-18_research_agent_shield_ai_whygame_run_summary.md`
3. `docs/runs/2026-03-18_research_agent_shield_ai_whygame_friction_log.md`

The immediate next step is the **extraction quality baseline** work described
in `docs/plans/0014_extraction_quality_baseline.md`. This is driven by
Stage 1 friction log entries 5 and 7:

1. prompt hardening for observed error patterns (alias self-references,
   predicate disambiguation, entity type boundaries);
2. typed-but-unidentified entity fillers at the extraction boundary so the
   model can express “I know this is a person but I can't name them”;
3. profile-level policy for whether unidentified entity fillers pass
   validation — strict profiles reject them, permissive profiles let them
   through to review;
4. prompt rendering of the active unidentified-filler policy.

The target is >50% acceptance rate on the Stage 1 corpus, not perfection.
The review workflow exists precisely because first-pass extraction will
never be perfect.

Broader roadmap rules remain:

1. use `docs/plans/0005_v1_capability_parity_matrix.md` as the feature ledger;
2. treat the current roadmap as the proved bounded successor core, not as full
   v1 parity;
3. require any later roadmap extension to point to concrete friction, breakage,
   or missing value observed in a real run;
4. require explicit workflow pressure before reopening temporal/inference work
   or another broad parity-recovery phase;
5. prefer the smallest next product-facing or parity-closing slice if a new
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

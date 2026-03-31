# Vision Gap Closure

Status: active

Last updated: 2026-03-28
Workstream: post-bootstrap capability completion

## Purpose

Close the 10 identified gaps between the ecosystem vision (project-meta/vision/)
and onto-canon6's current state. Each gap has acceptance criteria, uncertainties,
and dependencies. Implementation priority is consumer-driven; scope is
vision-driven (per CLAUDE.md principles).

This is a tracking plan, not a phase. Individual gaps may be promoted to their
own plans if scope warrants it. Gaps are ordered by dependency, not priority.
The ordered post-cutover execution program now lives in
`docs/plans/0024_post_cutover_program.md`; this document remains the
gap-by-gap closure tracker.

Unless a gap section has been fully rewritten, the `Current State` subsection
captures the baseline state at the moment the gap was opened. The per-gap
`Status` block is authoritative for present closure state.

## Execution Posture (2026-03-27)

This plan is sequencing the work, not shrinking the vision.

### Preserved Long-Term Capabilities

The full successor capability vision remains authoritative in
`docs/plans/0005_v1_capability_parity_matrix.md`. Deferred capabilities are
not being dropped because an early run underperformed or because the current
workstream is narrower. If a capability belongs in the successor, it stays in
the parity ledger until explicitly abandoned with rationale.

### Active Implementation Frontier

The active implementation frontier is currently limited to the work most likely
to unlock the rest of the vision:

1. extraction quality and evaluation hardening;
2. reproducibility / bootstrap independence from donor repos and hidden setup;
3. consumer adoption of the proved outputs (research_v3, Digimon, Foundation IR,
   and adjacent downstream surfaces).

New active work should only be promoted when it clearly advances one of those
three fronts.

### Deferred But Protected

Capabilities outside the current frontier remain deferred but protected.

Protection means:

1. do not delete proven slices merely because they are not the current
   bottleneck;
2. do not make local simplifications that would box out deferred capabilities;
3. prefer archive-and-label over delete when preserving proof artifacts or
   design records;
4. keep extension points, schema seams, and boundary contracts explicit where
   they are needed for later recovery.

### Immediate Gate For New Work

Before starting a new implementation track, answer:

1. does this improve extraction quality on the canonical corpora;
2. does this make the proved workflow reproducible without hidden repo
   dependencies;
3. does this cause a real downstream consumer to adopt onto-canon6 outputs;
4. if none of the above, why is this more important than the current frontier?

If the answer to 1-3 is no, the default move is to defer the work rather than
expand the active surface area.

## Review Notes (2026-03-26)

Reviewed for completeness and consistency with ecosystem vision
(`project-meta/vision/FRAMEWORK.md`, `FOUNDATION.md`, `ECOSYSTEM_STATUS.md`).

### Inline Corrections (applied to gap text above)

1. **Gap 5 import contract.** onto-canon6 adapter exports JSONL and DIGIMON now
   exposes a surfaced importer in
   `Digimon_for_KG_application/Core/Interop/onto_canon_import.py`. Real export
   materializes into DIGIMON GraphML and is queryable through DIGIMON's
   operator/runtime path. Remaining open item is weight semantics on a
   non-unity-confidence slice.
2. **Gap 6 framing.** Should target Foundation Assertion IR, not just pairwise
   adapter. `ECOSYSTEM_STATUS.md` calls out schema stabilization as prerequisite.
3. **Gap 8 placement resolved.** `FRAMEWORK.md` places rule engine in Operations
   (`llm_client`). Open question is fact-store adapter boundary only.
4. **Gap 2 acceptance.** "Comparable quality" replaced with explicit comparison
   rule requirement.

### Additional Findings

5. **Missing gap: Multi-modal projection.** FRAMEWORK.md defines four modalities
   (graph, table, vector, text). Only graph and epistemic addressed here. Table,
   vector, text deliberately deferred (no consumer) but should be listed as
   known out-of-scope.
6. **Gap 8 dependency too strict.** Gap 8 → Gap 7 should be nice-to-have, not
   hard dependency. ProbLog spike can use any promoted assertions with default
   confidence=1.0.
7. **Gap 6 scope may be optimistic (3-5 sessions).** FtM has ~70 entity schemas;
   SUMO mapping study alone could consume 1-2 sessions.
8. **Gap 10 uncertainties underdeveloped.** Review gate for extraction results
   (not code) needs concrete design: LLM-judge, structural validity threshold,
   or `make summary` as review input.
9. **Cross-cutting: Assertion confidence alignment.** FOUNDATION.md notes
   confidence nullable in onto-canon6. Affects Gaps 5 (Digimon weight), 6
   (research_v3 corroboration mapping), 7 (epistemic confidence source).
10. **Gap 2 vocabulary question.** Real constraint is predicate catalog coverage
    for non-military domains, not profile config.

### Dependency Graph Correction

```
Gap 8 (ProbLog spike)       → standalone (Gap 7 nice-to-have)
```

---

## Gap 1: Human-Readable Predicate Names

### Current State
4,669 predicate senses in sumo_plus.db use PropBank IDs (e.g., `fund-01`).
The Framework says predicates should be "identified by human-readable names."

### Acceptance Criteria
1. Every predicate sense has a human-readable name (e.g., `fund_ongoing_support`)
2. Names are generated, not hand-written (one LLM pass over 4,669 senses)
3. Names are stored alongside PropBank IDs (additive, not replacing)
4. Extraction prompts reference human-readable names in the predicate catalog

### Uncertainties
- Which LLM and prompt produces good names? Needs prompt_eval comparison.
- Do we rename the `event_types` table to `predicates`? (Mentioned in
  ECOSYSTEM_STATUS.md planned extensions)
- Do we add `is_static` flag at the same time? (Distinguishes events from
  static relations)

### Dependencies
None — standalone. Improves extraction quality indirectly.

### Estimated Scope
Small (1-2 sessions). One LLM batch pass + schema migration + test.

### Status: ALREADY CLOSED (discovered 2026-03-26)

All 4,669 predicate senses in sumo_plus.db already have human-readable names
in the `name` column (e.g., `promote_raise_rank`, `build_construct`,
`covet_wish_crave`). These are stored alongside PropBank IDs in the
`propbank_sense_id` column. Pack-level predicates (oc:, dodaf:) also have
human-readable IDs with `preferred_label` in predicate_types.jsonl.

The PredicateCanon bridge exposes these names as `predicate_id` in
`PredicateInfo` and `PredicateMatch` models. No additional LLM pass needed.

Remaining consideration: the `is_static` flag and potential table rename
(`event_types` → `predicates`) noted as uncertainties are already addressed —
the table IS named `predicates` and the `is_static` column exists.

---

## Gap 2: Non-Military Domain Testing

### Current State
All testing uses 17 PSYOP military cases. The system claims to be
domain-general but has never been tested on non-military text.

### Acceptance Criteria
1. E2E extraction proven on at least one non-military text (e.g., financial,
   academic, news article)
2. Benchmark fixture includes at least 5 non-military cases
3. Define and meet an explicit comparison rule before declaring success
   (for example: no worse structural-validity rate than the military slice, or
   a named benchmark threshold for the selected domain)

### Uncertainties
- Which domain? Financial text has different predicate patterns than military.
- Does the `psyop_seed` profile work for non-military text, or do we need a
  new profile/pack?
- Is the predicate catalog (military-focused) adequate for other domains?

### Dependencies
Gap 1 (human-readable names) would help but is not required.

### Estimated Scope
Medium (1-2 sessions). Select text, create profile if needed, run extraction,
create fixture cases.

### Status: COMPLETED (2026-03-26)

Tested on two non-military domains:
- **Financial text** (SEC/crypto enforcement): 3 valid candidates from psyop_seed
  (oc:send_report, oc:express_concern, oc:criticize_change). 100% validation.
- **Academic text** (climate attribution research): 1 valid + 2 invalid from
  psyop_seed. Invalid ones: entity type mismatches (psyop_seed has only
  oc:person, oc:military_organization, oc:military_unit).
- **Progressive extraction** (financial text, 4669 predicates): 19 entities
  with correct SUMO types (GovernmentOrganization, Corporation, Human).

Overall: 11 candidates, 82% structural success rate (comparable to military
80% on Phase B bounded chunks).

Key finding: **vocabulary is the constraint, not the pipeline.** The extraction
pipeline works unchanged on non-military text. The psyop_seed entity types
are military-specific, but the progressive extractor with sumo_plus.db handles
non-military entities correctly. A general-purpose pack with broader entity
types would close the remaining 18% validation gap.

---

## Gap 3: Automated Entity Resolution

### Current State
Identity resolution works (proven: USSOCOM across 2 chunks) but requires
manual `create-identity-for-entity` and `attach-identity-alias` CLI calls.

### Acceptance Criteria
1. After extraction + promotion, entities with matching names across
   source-scoped IDs are automatically grouped into identity candidates
2. Resolution strategy is configurable (exact name match, fuzzy, Q-code)
3. Auto-resolved identities are flagged as `auto` for optional human review
4. `make summary` reports identity resolution stats

### Uncertainties
- Exact name match is naive — "4th PSYOP Group" vs "4th POG(A)" are the same
  entity but different names. How aggressive should fuzzy matching be?
- Should auto-resolution happen at promotion time or as a separate pass?
- Q-code resolution requires Wikidata API calls — cost and reliability?

### Dependencies
E2E pipeline must work (done). Gap 2 would test resolution across domains.

### Estimated Scope
Medium (2-3 sessions). Matching logic + CLI integration + tests.

### Status: PARTIALLY COMPLETED (updated 2026-03-31)

**Exact-name resolution (2026-03-26):** Implemented auto_resolution.py with
exact name matching + fuzzy (rapidfuzz) strategies. CLI command
`auto-resolve-identities` added. Tested on e2e data:
- 20 entities scanned, 19 groups found (USSOCOM merged from 2 chunks)
- 18 identities created, 1 multi-member identity (USSOCOM canonical + alias)
- Resolution strategy configurable via --strategy flag
- Auto-resolved identities created with `created_by="auto:resolution"`

**Cross-document LLM clustering (Plan 0025, planned):** Exact-name matching
cannot resolve title variations ("Gen. Smith" vs "General John Smith"),
abbreviations, or contextual identity. Plan 0025 adds:
- Name normalization (title/honorific stripping)
- LLM-based entity clustering (KGGen-style, per entity type)
- Fuzzy pre-filtering → LLM validation (no direct fuzzy merges)
- Scale test on 20-50 doc synthetic corpus with ground truth

Gap 3 is fully closed when Plan 0025 Phase 4 demonstrates cross-document
entity resolution on a realistic corpus with >90% precision and >70% recall.

---

## Gap 4: Temporal Qualifiers

### Current State
Foundation expects `sys:valid_from` and `sys:valid_to` on assertions.
Deferred by ADR — onto-canon6 does not extract temporal bounds.

### Acceptance Criteria
1. Extraction prompt asks for temporal qualifiers when present in source text
2. Temporal values stored in assertion payload (`sys:valid_from`, `sys:valid_to`)
3. Foundation IR export includes temporal qualifiers when present
4. Assertions without temporal info export with null qualifiers (not failure)

### Uncertainties
- Do we extract temporal qualifiers in the same LLM call as assertions, or
  as a separate enrichment pass?
- What temporal precision is useful? Year? Month? Exact date?
- Which consumer needs temporal qualifiers first? Digimon? research_v3?

### Dependencies
None — additive to existing extraction.

### Estimated Scope
Small-Medium (1-2 sessions). Prompt change + schema addition + export update.

### Status: COMPLETED (2026-03-26)

All acceptance criteria met:
1. Extraction prompt asks for temporal qualifiers (`valid_from`, `valid_to`)
   as ISO 8601 date strings when present in source text
2. Temporal values stored in assertion payload (flows through to DB)
3. Foundation IR export includes temporal qualifiers as `sys:valid_from`,
   `sys:valid_to` when present
4. Assertions without temporal info export with null qualifiers (not failure)

Proven on financial text: SEC complaint dated 2023-06-05, Zhao CEO tenure
ended 2023-11, settlement dated 2023-11. Model correctly extracts dates
from source text into ISO format.

---

## Gap 5: Digimon Real-Data Export Test

### Current State
`digimon_export.py` adapter exists, tested on 5-node synthetic fixture.
Real promoted assertions were exported on 2026-03-26 from
`var/e2e_test_2026_03_25/review_combined.sqlite3` (20 exported entity rows,
16 relationship rows). DIGIMON now has a thin JSONL importer that materializes
that export into native GraphML (19 nodes after merging duplicate `USSOCOM`
names, 16 edges). DIGIMON's runtime/operator path is also proven on this
artifact: `relationship.onehop` returns the expected USSOCOM commanders and
subordinate-unit neighborhood. Weight/confidence validation remains incomplete
because this slice only exports unit-confidence edges.

### Acceptance Criteria
1. Export promoted assertions from e2e test DB as Digimon JSONL
2. DIGIMON importer successfully materializes the JSONL into its native graph
   artifact format
3. DIGIMON query/retrieval path returns the expected USSOCOM commander and
   PSYOP-unit neighborhood from the imported graph
4. Weight/confidence semantics validated (onto-canon6 probability maps
   correctly to Digimon weight on a non-unity-confidence slice or synthetic
   control case)

### Uncertainties
- Does the DIGIMON runtime environment used for operator-level querying have
  the optional dependencies needed to load and query the imported graph?
- Single-argument predicates (one entity only) are skipped by the current
  importer because DIGIMON's persisted graph is binary-edge-only. Is that the
  correct long-term policy?
- DIGIMON's persisted graph is undirected, so assertion role direction is not a
  first-class runtime concept after import. Is that acceptable for the intended
  retrieval use cases?

### Dependencies
E2E pipeline must produce promoted assertions (done). DIGIMON must be
runnable with its optional graph/runtime dependencies installed. Non-unity
confidence validation depends on a real or synthetic slice with varied
assertion confidence values.

### Estimated Scope
Small (1 session). Run export, attempt Digimon ingestion, fix any format
issues.

### Status: PARTIALLY COMPLETED (2026-03-26)

Acceptance criteria 1-3 are met:
1. Real promoted assertions exported from the e2e review DB
2. DIGIMON importer materialized the export into GraphML
3. DIGIMON operator query recovered the expected USSOCOM neighborhood

Acceptance criterion 4 remains open:
4. Weight/confidence semantics are not fully validated on a non-unity slice

---

## Gap 6: research_v3 → onto-canon6 Adapter

### Current State
An onto-canon6-side adapter now exists in
`src/onto_canon6/adapters/research_v3_import.py` and is proven at the
import-contract level on a real `graph.yaml` investigation export. Remaining
work is consumer-side adoption, conflict-policy hardening, and longer-term
Foundation/schema alignment. Earlier convergence planning is archived at
`project-meta/vision/archive/2026-03-22/ONTO_CANON_RESEARCH_V3_CONVERGENCE.md`.

### Acceptance Criteria
1. research_v3 KnowledgeGraph (YAML) can be exported to onto-canon6
2. Entity mapping: research_v3 Entity (FtM-backed) → onto-canon6 entity type
3. Claim translation: corroboration_status → onto-canon6 epistemic level
4. Provenance preserved: source URLs, retrieval timestamps survive export
5. At least 5 entities from a real research_v3 investigation imported and
   promoted in onto-canon6

### Uncertainties
- FtM entity types → SUMO types: is the mapping feasible? How many FtM
  schemas map cleanly to SUMO types?
- Conflict handling: what happens when a new investigation contradicts
  existing onto-canon6 assertions? (Policy decision needed)
- Round-trip: should research_v3 be able to re-import its own exports?
- Does research_v3 output currently include structured KnowledgeGraph YAML,
  or is it unstructured text? (Need to check current state)

### Dependencies
research_v3 must produce KnowledgeGraph output. Gap 3 (entity resolution)
needed for cross-investigation dedup. The adapter should stay aligned with the
Foundation Assertion IR and onto-canon6 promoted-graph schema stability
criteria from `ECOSYSTEM_STATUS.md`.

### Estimated Scope
Large (3-5 sessions). Entity mapping study + adapter code + conflict policy
+ integration test.

### Status: COMPLETED (2026-03-26)

Adapter implemented: `adapters/research_v3_import.py`
Tested on real data: Booz Allen Hamilton lobbying investigation (48 claims).

1. Entity mapping: FtM Person → oc:person, Company → oc:company,
   PublicBody → oc:government_organization (15 schemas mapped)
2. Claim translation: corroboration_status → confidence score.
   corroborated=0.90, partially_corroborated=0.70, unverified=0.50.
   Combined with confidence label (high/medium/low) via averaging.
3. Provenance preserved: source URLs, retrieval timestamps, source_type
   all stored in source_metadata
4. 48 claims from real investigation → 48 CandidateAssertionImport objects
5. Entity types in output: oc:company, oc:government_organization, oc:person

Remaining: submit-progressive CLI integration to ingest imports into review DB.
Conflict handling (contradicting assertions): deferred — needs Gap 3 entity
resolution to detect cross-investigation entity overlap first.

---

## Gap 7: Epistemic Engine on Real Data

### Current State
Built: confidence assessments, supersession, disposition (active/weakened/
retracted), corroboration groups, tension detection. 298 tests pass.
Never tested on real extraction data.

### Acceptance Criteria
1. Confidence scores assigned to at least 10 real promoted assertions
2. At least 1 supersession recorded (new assertion replaces old)
3. At least 1 tension detected (conflicting assertions identified)
4. Epistemic report exports correctly via CLI and Foundation IR

### Uncertainties
- What triggers supersession? Manual only, or automatic when a newer
  extraction contradicts an older one?
- Confidence source: LLM-assigned at extraction time? Post-extraction judge?
- What constitutes "tension"? Same predicate with different fillers?
  Same entities with contradictory predicates?

### Dependencies
E2E pipeline with multiple runs producing overlapping/contradictory
assertions. Gap 6 (research_v3 adapter) would provide natural contradictions
from different investigation runs.

### Estimated Scope
Medium (2-3 sessions). Manual confidence assignment, fabricate a
contradiction scenario, verify tension detection.

### Status: COMPLETED (2026-03-26)

All acceptance criteria met on real e2e test data (16 promoted assertions):
1. Confidence: 16/16 assertions scored with varying values (0.65-0.95)
2. Supersession: 1 recorded (Holland command superseded by generic USSOCOM Commander)
3. Tension: 19 pairs detected (role_filler_conflict — 5 commanders sharing
   USSOCOM anchor but differing on commander role filler)
4. Disposition: 1 assertion weakened

No fabricated scenarios needed — the real data naturally produces tensions
because 5 different people each held the Commander role at USSOCOM. The
tension engine correctly identifies these as role_filler_conflict with
anchor_roles=(organization,) and differing_roles=(commander,).

---

## Gap 8: Custom Logic / ProbLog Spike

### Current State
Not started. Framework describes rules-as-data with Datalog or ProbLog
interpreter. ECOSYSTEM_STATUS lists it as a planned extension under
Operations (llm_client).

### Acceptance Criteria
1. Spike: one concrete rule (e.g., "if A funds B and B attacks C then A is
   proxy_war_participant against C") evaluated over test facts
2. Facts loaded from onto-canon6 SQLite (not hardcoded)
3. Probability propagation works (confidence on input facts affects output)
4. Decision: ProbLog or custom Datalog? Documented with rationale.

### Uncertainties
- ProbLog's SQLite integration (`sqlite_load`): does it work with
  onto-canon6's schema?
- Performance: how many facts + rules before it's too slow?
- What is the cleanest fact-store adapter boundary between llm_client's rule
  engine and onto-canon6 / DIGIMON data stores?
- Is ProbLog's dependency weight acceptable for the ecosystem?

### Dependencies
onto-canon6 must have promoted assertions with confidence scores (Gap 7).

### Estimated Scope
Small spike (1 session) to answer the build-vs-buy question. Full
implementation TBD based on spike results.

### Status: COMPLETED (2026-03-26)

ProbLog spike successful:
1. Loaded 16 facts from onto-canon6 SQLite with confidence scores (0.65-0.95)
2. Defined 2 rules: authority_over (direct command + transitive via belongs_to),
   transitive part_of
3. ProbLog derived 45 facts with correct probability propagation. Example:
   Gen. Holland commands USSOCOM (P=0.95), 193rd SOW belongs to USSOCOM
   (P=0.91), so Holland has authority over 193rd SOW (P=0.95*0.91=0.8645)
4. DECISION: **Use ProbLog.** 2MB pure Python, probability propagation
   automatic (product semantics), fact-store adapter ~30 lines. Custom
   Datalog not justified — ProbLog does everything we need.

Fact-store adapter boundary: onto-canon6 exports facts as ProbLog terms,
llm_client hosts the rule engine (per FRAMEWORK.md), consumers define rules.

---

## Gap 9: Second Vocabulary (Composability Proof)

### Current State
`dodaf_minimal` pack exists with strict and mixed profiles. Never tested
with the full extraction pipeline (only Phase 7 bootstrap validation proof).

### Acceptance Criteria
1. E2E extraction using `dodaf_minimal` profile on DoDAF-relevant text
2. Different predicate catalog renders correctly in extraction prompt
3. Validation uses dodaf_minimal pack rules (not psyop_seed)
4. Both vocabularies can coexist in the same DB (different profile_id)

### Uncertainties
- Is `dodaf_minimal` complete enough for real extraction? It was designed
  as a "second pack proof" with minimal predicates.
- What text would exercise DoDAF predicates? Military systems architecture
  documents?
- Can we extract with two different profiles on the same source text and
  compare results?

### Dependencies
E2E pipeline must work (done). dodaf_minimal pack exists (done).

### Estimated Scope
Small (1 session). Select DoDAF text, run extraction with dodaf profile,
compare to psyop_seed extraction.

### Status: COMPLETED (2026-03-26)

All acceptance criteria met:
1. E2E extraction with dodaf_minimal_strict on DoDAF OV-2 text: 7 candidates
   extracted, all using dodaf:operational_node_exchanges_information predicate
2. Predicate catalog rendered correctly: dm2:OperationalNode, dm2:InformationElement
   entity types, source_node/target_node/information_element roles
3. Validation used dodaf pack rules: 0 hard errors, 0 soft violations,
   0 unknown type checks across all 7 candidates (100% pass rate)
4. Both vocabularies coexist: dodaf_minimal_strict uses dm2: namespace,
   psyop_seed uses oc: namespace, same runtime/review/promotion pipeline

---

## Gap 10: Autonomous Operation (OpenClaw)

### Current State
Repo-local `.openclaw/success-criteria.yaml` and `.openclaw/mission-spec.yaml`
now exist, but OpenClaw runtime consumption is not yet proven. The
`project-meta/ops/openclaw/README.md` documents auto-loading
`.openclaw/success-criteria.yaml`, but `project-meta/ops/openclaw/run_task.py`
does not yet reference these files directly. This gap is therefore at the
specification stage, not the execution-proof stage.

### Acceptance Criteria
1. `.openclaw/success-criteria.yaml` exists with measurable criteria
2. Mission spec defines: what text to extract, what goal, what acceptance
   threshold
3. OpenClaw can launch an extraction mission on onto-canon6 and produce
   reviewed commits
4. Review gate evaluates extraction results (not just code changes)

### Uncertainties
- What does a "successful" extraction mission look like? N candidates
  extracted with >X% structural validity?
- Should the mission runner call `make extract` or the CLI directly?
- Review gate: how does gpt-5.2-pro review extraction results vs code
  changes?
- Cost control: extraction calls cost money — per-mission budget?

### Dependencies
E2E pipeline must work (done). Mission runner must be operational
(Phase 1 complete, Phase 1.5 in progress).

### Estimated Scope
Medium (2 sessions). Success criteria + mission spec + test run.

### Status: PARTIALLY COMPLETED (2026-03-26)

Acceptance criteria 1-2 are met at the specification level:
1. `.openclaw/success-criteria.yaml` exists with measurable criteria
2. `.openclaw/mission-spec.yaml` defines a concrete extraction mission

Acceptance criteria 3-4 remain open:
3. OpenClaw has not yet been shown launching an onto-canon6 extraction mission
   that consumes these repo-local contracts end to end
4. The review gate design is documented, but not yet proven in the mission
   runner against extraction-result artifacts

---

## Dependency Graph

```
Gap 1 (predicate names)     → standalone
Gap 2 (domain testing)      → standalone (Gap 1 nice-to-have)
Gap 3 (entity resolution)   → standalone
Gap 4 (temporal qualifiers) → standalone
Gap 5 (Digimon export)      → standalone
Gap 6 (research_v3 adapter) → Gap 3
Gap 7 (epistemic on data)   → standalone (Gap 6 provides natural contradictions)
Gap 8 (ProbLog spike)       → standalone (Gap 7 nice-to-have)
Gap 9 (second vocabulary)   → standalone
Gap 10 (autonomous ops)     → standalone
```

## Implementation Priority (recommended)

Consumer-driven priority, per CLAUDE.md:

1. **Gap 5** (Digimon export) — smallest scope, proves cross-project flow
2. **Gap 2** (domain testing) — validates generality claim
3. **Gap 3** (entity resolution) — unblocks Gap 6
4. **Gap 9** (second vocabulary) — proves composability
5. **Gap 1** (predicate names) — improves extraction quality
6. **Gap 6** (research_v3 adapter) — biggest integration value
7. **Gap 7** (epistemic on data) — validates epistemic engine
8. **Gap 4** (temporal qualifiers) — additive
9. **Gap 8** (ProbLog spike) — exploratory
10. **Gap 10** (autonomous ops) — depends on mission runner maturity


---

## Extraction Quality Experiment Results (2026-03-26)

Ran prompt_eval experiment: 5 variants × 4 cases × 1 run = 20 LLM calls.
Model: gemini/gemini-2.5-flash via litellm.

### Full Results (re-run completed)
5 variants × 4 cases = 20 variant-case pairs:
- **psyop_001** (designation change): 0/5 variants produce candidates
- **psyop_002** (concerns about shift): 0/5 variants produce candidates
- **psyop_003** (alias expansion): 5/5 variants score 1.0 (simplest case)
- **psyop_004** (subordinate unit): 0/5 variants produce candidates
- **Overall: 5/20 pairs scored > 0 (25%), mean=0.278, max=1.0**

First run also showed: 11/20 connection timeouts (600s), 26 empty-roles.

### Root Cause Analysis
1. **Experiment variants produce empty candidates on 3/4 cases.** Only
   psyop_003 (a simple parenthetical alias) works. The complex assertion
   extraction cases (designation change, organizational belonging) fail.
2. **The operational prompt works.** `text_to_candidate_assertions.yaml`
   successfully extracted in Gap 2 (financial), Gap 4 (temporal), Gap 9
   (dodaf). The problem is specific to experiment variants.
3. **API reliability compounds the problem.** 55% timeout rate on first run
   (600s connection timeouts via OpenRouter/litellm).

### Action Items
1. Focus prompt iteration on the operational prompt (the one that works)
2. Rebuild experiment variants from the operational prompt, not separately
3. Switch to direct API calls (bypass OpenRouter) for reliability
4. Consider model upgrade: gemini-2.5-flash is cheap but may lack capacity
   for complex multi-role assertions

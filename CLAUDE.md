# onto-canon6

`onto-canon6` is the successor bootstrap for the `onto-canon` lineage. It
starts from a proved slice instead of trying to port the entire previous
runtime.

## Read First

1. `README.md`
2. `docs/SUCCESSOR_CHARTER.md`
3. `docs/STATUS.md`
4. `docs/plans/0025_cross_document_entity_resolution.md` (current active work)
5. `docs/plans/0024_post_cutover_program.md`
6. `docs/plans/0005_v1_capability_parity_matrix.md`
7. `docs/plans/0001_successor_roadmap.md`

## Commands

```bash
pytest -q
onto-canon6 --help
onto-canon6-mcp
```

## Layout

```text
src/onto_canon6/
  adapters/
  artifacts/
  core/
  extensions/
  ontology_runtime/
  pipeline/
  domain_packs/
  surfaces/
tests/
docs/
config/
```

## Current State

- Phases 0-15 completed the bootstrap roadmap, not full successor parity.
- The explicit parity ledger is `docs/plans/0005_v1_capability_parity_matrix.md`.
- Two real non-fixture runs completed (PSYOP Stage 1 + Shield AI WhyGame).
- **Progressive extraction pipeline** (Plan 0018) is complete and proven on real
  text. 3-pass architecture: open extraction → predicate mapping (78% early exit)
  → entity refinement. 87.8% predicate resolution on Shield AI findings.
- ADRs 0017-0023 adopted (permissive extraction, progressive disclosure,
  ancestor-aware evaluation, scoring alignment, chunk grounding, workstream
  classification, chunk-level transfer evaluation).
- Predicate Canon bridge, ancestor-aware evaluator, and Digimon export
  adapter operational.
- **Active work**: extraction quality hardening (Plan 0014), vision-gap closure
  tracking (Plan 0020), the post-cutover execution program (Plan 0024), and
  the explicit schema-stability gate (Plan 0026). The chunk-level transfer
  evaluation requirement remains active through ADR 0023 and Plans 0024/0014
  even though there is no standalone Plan 0019 file.

## Strategic Direction (2026-03-31)

- **Architecture is sound. Current priority: cross-document entity resolution
  and scale test.** Plan 0025 implements KGGen-style LLM clustering over
  promoted entities, then tests on a 20-50 document corpus to prove onto-canon6's
  value proposition (cross-doc entity resolution, contradiction detection, typed
  reasoning). This is the prerequisite for consumer adoption (Plan 0024 Lane 2).
- **Default operating mode is `review_mode: llm` with `enable_judge_filter: true`.**
  Human review is for debugging, not production. Auto-accept is for bulk
  throughput when you trust the schema. LLM-judge is the standard mode.
- **Extraction quality at 88% structural validity on bounded chunks** (progressive
  extraction + improved prompts). The 37.5% PSYOP Stage 1 number was from an
  early run before progressive extraction and prompt hardening.
- **Entity resolution is the scale bottleneck, not extraction quality.** Without
  cross-document resolution, every document produces isolated entity islands.
  The value proposition (accumulation, contradiction detection, cross-doc
  reasoning) cannot be demonstrated.
- **Flat filler model with strong descriptions** — discriminated unions (oneOf)
  are architecturally correct but no current model can navigate them (all produce
  empty roles). Reverted to flat model with `Field(description=...)` enforcing
  kind-specific requirements + post-parse validator. `minProperties` removed from
  roles (providers don't enforce it; post-parse validator catches empty roles).
- **E2E pipeline proven (2026-03-25).** Text → extraction → validation → review
  → promotion → durable graph. 5 USSOCOM commanders extracted with correct
  ontology types, 100% acceptance. Model: `gemini/gemini-3-flash-preview`
  (best tested — 100% precision/recall on scale test). The earlier empty-roles
  regression was caused by `additionalProperties` in the JSON schema, not the
  model. Fixed by replacing `dict[str, list[Filler]]` with `list[RoleEntry]`
  (standard Gemini workaround). See KNOWLEDGE.md for details.
- **Observability gap closed**: llm_client now stores the raw model response on
  validation failure (not just the error message). Query with:
  `SELECT response, error FROM llm_calls WHERE error IS NOT NULL AND task='fast_extraction'`
  to diagnose whether the model or our processing caused failures.
- **Shared evidence span resolver** in `llm_client/utils/evidence_spans.py`.
  Handles whitespace normalization, ambiguous matches (disambiguation via hints),
  markdown table formatting. Used by onto-canon6, available to all projects.
- **No LLM provider enforces value-level JSON Schema constraints** (minProperties,
  minLength, pattern, minimum) at decode time. Only structural constraints (type,
  required, enum) are enforced. llm_client now has post-generation validation
  and observability columns for `schema_hash`, `response_format_type`, and
  `validation_errors`; the current repo should assume those fields exist on
  llm_client `main`.
- **extraction_goal is now required** — every run must specify what assertions
  are relevant. Broad default: "Extract all factual assertions directly supported
  by the source text." Narrow goals (e.g., "extract organizational command
  relationships") improve discrimination. The schema rejects extractions that
  can't fill entity_type (psyop_005 correctly rejected). Alias expansions
  (psyop_003) still over-extract with broad goals — caller must narrow.
- **onto-canon is NOT OSINT-specific** — it's the Data bucket of the ecosystem
  (general assertion governance layer). OSINT is one consumer.
- **Extraction evaluation must use LLM-as-judge**, not just golden-set
  comparison. The golden set is incomplete — the extractor produces reasonable
  assertions that aren't in the golden set and get scored as wrong. Always
  report both: golden-set match rate AND LLM-judge reasonableness rate.
- **Benchmark against a simple baseline** — compare progressive extraction vs
  bare "extract SPO triples" prompt on same corpus to prove governance value.
- **Integration adapters are built and proven** — research_v3 import (48 claims),
  Digimon export/import/query (19 merged nodes, operator query proven), and
  Foundation IR (16 assertions). Next step is consumer-side adoption and
  long-tail hardening, not more net-new adapter surfaces.
- **DIGIMON is now the first chosen Lane 2 consumer.** The currently supported
  downstream workflow is the thin v1 seam: `onto-canon6` exports flat
  `entities.jsonl` / `relationships.jsonl` via the `onto-canon6` console
  script, then DIGIMON imports them into GraphML via
  `scripts/import_onto_canon_jsonl.py` from the DIGIMON repo root. Keep this
  workflow truthful: it proves downstream materialization and graph reuse, not
  richer alias/passage/provenance interchange yet.
- **Preserve the full capability vision; narrow the active frontier.**
  onto-canon6 is not retreating from deferred capabilities and is not judging
  the thesis by one early extraction run. The parity matrix remains the full
  successor capability ledger, and deferred capabilities remain mandatory to
  preserve architecturally even when they are not the current implementation
  focus.
- **No capability deletion; no casual new implementation tracks.** The
  bootstrap roadmap is done. New active work must be justified by one of:
  extraction-quality friction, reproducibility / bootstrap-independence,
  or concrete consumer adoption needs. Do not start net-new surfaces,
  adapters, epistemic concepts, or internal subsystems unless they unblock one
  of those three fronts.
- **Donor repos are transitional, not permanent runtime dependencies.** The
  older `onto-canon` repos are expected to be archived once `onto-canon6` is
  stable. Stabilization therefore means `onto-canon6` must absorb the donor
  assets and code slices it truly needs, rather than requiring sibling repos
  forever.
- **Absorb selectively, not by wholesale copy.** Migrate required donor
  profiles, packs, data assets, and narrow utility code as explicit ownership
  transfers with provenance notes. Do not bulk-copy whole repos and sort them
  out later.
- **Foundation Assertion IR adapter operational** (`adapters/foundation_assertion_export.py`).
  Entity alias_ids and temporal qualifiers are wired from the promoted-graph /
  identity stack. Remaining alignment work is mainly confidence semantics and
  provenance envelope shape; onto-canon6 does NOT adopt the Foundation event log
  internally.
- **Baseline comparison done**: bare SPO-triple extraction (no ontology) gets 43%
  entity coverage with free-form predicates, no discrimination, and fragmented
  triples. Confirms governance layer adds: ontology alignment, discrimination,
  structured multi-role assertions. Script: `scripts/baseline_extraction_comparison.py`.

## Composability Principle

onto-canon6 is a composable toolkit, not a monolithic application:

- **Vocabulary is pluggable.** The SUMO/PropBank/FrameNet synthesis (`oc:` prefix,
  sumo_plus.db) is ONE vocabulary, not THE vocabulary. Packs and profiles are the
  mechanism for plugging in different vocabularies. Don't hardcode assumptions
  about specific predicates or entity types outside of pack-specific code.
- **Extensions are pluggable.** The epistemic engine (confidence, supersession,
  tension) is ONE extension, not the only use case. A financial signals extension
  or a temporal reasoning extension would use the same governed assertion
  lifecycle with different extension-local models. Keep extensions in
  `extensions/`, not in core.
- **Extraction is a producer, not core.** The text extraction pipeline is one way
  to produce candidate assertions. An API import adapter, a manual entry form,
  or a structured data ingestion pipeline are other producers. Don't couple core
  governance logic to extraction-specific assumptions.
- **Resolution strategies are consumer-chosen.** Entity identity, dedup, conflict
  handling — onto-canon6 provides the infrastructure, consumers choose the
  strategy (exact match, Q-code, never merge, LLM-assisted).

Don't refactor into separate packages until a second vocabulary/extension/producer
exists. But don't deepen coupling either — keep boundaries clean so extraction
happens.

## Integration Decisions (2026-03-24)

1. **Entity type CURIE namespacing** — RESOLVED. Extraction already uses `oc:`
   prefix (e.g., `oc:person`, `oc:military_organization`). Progressive extractor
   uses `sumo:` for SUMO types. Both are valid CURIE namespaces per Foundation.

2. **Provenance model** — DECIDED. onto-canon6 exposes its own provenance
   (candidate → evidence spans → source artifact → lineage edges). The data
   is already in the DB. A wrapper maps this to Foundation `provenance_refs`
   at export time. onto-canon6 does NOT adopt the Foundation event log format
   internally — it's a tool, not an orchestrator.

3. **Entity ID + dedup** — DECIDED. onto-canon6 owns entity identity
   infrastructure (the identity subsystem: `GraphIdentityRecord`,
   memberships, external references). Consumers choose their resolution
   *strategy* (exact name, Q-code, never merge); onto-canon6 provides the
   resolution *infrastructure*. Export adapters wire the identity subsystem.
   Consumers should not have to reimplement dedup.

## Active Execution Block (2026-04-01 afternoon)

**CONTINUOUS AUTONOMOUS EXECUTION. DO NOT STOP.**

Execute the phases below in order. When one phase completes, immediately start
the next. Log uncertainties and continue — do not stop to ask. Commit after
every verified phase as a rollback point. Use tasks to track progress.

The ONLY valid stop conditions are:
1. All phases complete
2. A real blocker that requires Brian's input AND cannot be worked around
3. LLM API is down for >10 minutes (log it and try the next phase)

### Phase J: Plan 0026 Phase 4 — Change classification policy
**Goal**: Define release-note expectations for breaking/compatible/non-breaking
changes. Require plan or ADR updates for intentional breaking changes. Require
consumer coordination before breaking Surface C or D.
**Success**: Future agents can classify a change without reopening architecture
debate. Consumer-facing exports cannot change casually.
**Approach**: Add a "Change Classification" section to Plan 0026 with concrete
rules and examples. This is documentation, not code.

### Phase K: Plan 0024 Lane 5 — Deferred parity reprioritization
**Goal**: Review the parity matrix (Plan 0005) against real consumer friction
and extraction findings. Classify each major deferred area as next-active,
protected-deferred, consumer-blocked, or abandoned-with-rationale.
**Success**: Parity matrix has updated dispositions. Next-active items named.
**Approach**: Read Plan 0005, check each deferred row against what we learned
from Plans 0025/0026/0014. Update dispositions. No code — planning only.

### Phase L: Full 25-doc scale test with gemini-3-flash-preview
**Goal**: Complete the partial scale test (previously 20/25 docs due to timeout).
**Success**: All 25 docs extracted, resolution run, scored. Results in docs/runs/.
**Approach**: Run scripts/run_scale_test.py with gemini-3-flash-preview. May need
to run in background with longer timeout.

### Phase M: require_llm_review integration test
**Goal**: Test the `require_llm_review=true` flag with real data.
**Success**: Run exact strategy with LLM validation on scale test DB. Verify
LLM confirms correct merges and rejects false merges. Document results.
**Approach**: Run auto_resolve_identities(strategy="exact", require_llm_review=True)
on scale test data. Check that merges match ground truth.

### Phase N: Data Contracts compliance (Q6)
**Goal**: Add `extra="forbid"` to DIGIMON export adapter producer models per
root CLAUDE.md Data Contracts rule.
**Success**: DigimonEntityRecord and DigimonRelationshipRecord use extra="forbid".
Tests pass.

### Phase O: Module entrypoint fix (Plan 0014 known issue)
**Goal**: Make `python -m onto_canon6.cli` work.
**Success**: `python -m onto_canon6.cli --help` produces help text.
**Approach**: Add `src/onto_canon6/__main__.py`.

### Phase P: Update all plans and HANDOFF with final results
**Goal**: All docs current after Phases J-O.
**Success**: Plans 0005, 0024, 0026, 0014 updated. HANDOFF current.

**Pre-made decisions (apply to all phases):**
- Model: `gemini/gemini-3-flash-preview` (best tested)
- Config: `review_mode: llm`, `enable_judge_filter: true`, `require_llm_review: true`
- All LLM calls through llm_client with task/trace_id/max_budget
- Commit each verified phase immediately
- Log uncertainties in plan docs and continue — do not stop
- If LLM quota hits: switch to gemini-2.5-flash-lite as fallback

## Principles

- **Autonomy is the default operating mode.** When there is an active plan or
  clearly bounded workstream, continue executing it end to end without waiting
  for incremental permission after each slice. Do not stop at "plan written",
  "first file migrated", or "one test passed". Continue until the active plan
  is fully implemented, a real blocker is hit, or a concrete unresolved
  uncertainty appears.
- **Do not pause for routine next-step confirmation.** Once the repo has an
  adopted execution plan, treat "what next?" as already answered by that plan.
  Keep moving through the phases in order, commit verified increments, and only
  surface to the user when:
  1. the current plan is complete;
  2. a real blocker or risk requires a decision;
  3. a material new uncertainty changes the plan.
- **For active implementation blocks, stopping early is a failure mode.** The
  expected behavior is continuous execution across planning, migration,
  verification, cleanup, and documentation updates in one sustained pass.
- The parity matrix is the capability vision ledger. Every capability the system
  should eventually have must appear there, even if deferred. Deferred
  capabilities must not be silently dropped. Uncertainties must be documented
  explicitly in the parity matrix and the charter.
- Deferred does not mean abandoned. Protect future capabilities with extension
  points and clean boundaries even when implementation priority is elsewhere.
- Architectural decisions must not box out the long-term vision. If a design
  choice prevents a deferred capability from being added later, add an
  extension point now.
- Implementation priority is driven by consumer need and extraction quality
  friction. But the scope of what will eventually be built is defined by the
  vision, not by current friction alone.
- Active implementation priority is currently limited to:
  extraction quality, reproducibility / bootstrap independence, and
  consumer adoption of the proved outputs. All other work must clear a higher
  bar.
- Bootstrap independence means the canonical runtime must eventually stop
  requiring sibling `../onto-canon5` or `../onto-canon` checkouts. Optional
  external consumers such as `research_v3` may remain outside this repo, but
  required donor runtime assets must not.
- Keep the current scope narrow and explicit: reviewed assertions, overlays,
  promoted graph state, stable identity, semantic canonicalization, and the thin
  CLI/MCP surfaces that prove those slices.
- If the next change cannot be justified against the adopted ADR set, it should
  not land as casual repo drift.

## Workflow

- All significant work follows plans in `docs/plans/`
- Commit verified increments with `[Plan #N]` prefix
- Use `[Trivial]` for <20 line changes

## References

| Doc | Purpose |
|-----|---------|
| `docs/plans/CLAUDE.md` | Plan index |
| `config/config.yaml` | Extraction and prompt configuration |
| `evaluation/` | Evaluation harness and prompt experiment service |

## LLM Integration

- All LLM calls route through `llm_client` with mandatory `task=`, `trace_id=`,
  `max_budget=` kwargs.
- Prompts are YAML/Jinja2 templates in `prompts/`, loaded via
  `llm_client.render_prompt()`. No f-string prompts in Python.
- Prompt/model iteration should use `ExtractionPromptExperimentService`
  (`evaluation/prompt_eval_service.py`) backed by `prompt_eval`, not ad hoc
  local loops. Results log to llm_client observability (SQLite + JSONL).
- Extraction config, prompt refs, and variant definitions are in
  `config/config.yaml`.
- No examples in prompts without approval. Rules and goal-oriented guidance
  are fine.

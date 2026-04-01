# onto-canon6

`onto-canon6` is the successor bootstrap for the `onto-canon` lineage. It
starts from a proved slice instead of trying to port the entire previous
runtime.

## Read First

1. `README.md`
2. `docs/SUCCESSOR_CHARTER.md`
3. `docs/STATUS.md`
4. `docs/plans/0024_post_cutover_program.md`
5. `docs/plans/0025_cross_document_entity_resolution.md` (current active implementation work)
6. `docs/plans/0026_schema_stability_gate.md` (completed Lane 3 contract policy)
7. `docs/plans/0014_extraction_quality_baseline.md` (active Lane 4 promotion gate)
8. `docs/plans/0027_deferred_parity_reprioritization.md`
9. `docs/plans/0028_query_browse_surface.md`
10. `docs/plans/0005_v1_capability_parity_matrix.md`
11. `docs/plans/0001_successor_roadmap.md`

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
- **Active work**: cross-document entity resolution value proof (Plan 0025),
  extraction quality hardening under an explicit promotion gate (Plan 0014),
  vision-gap closure tracking (Plan 0020), the post-cutover execution program
  (Plan 0024), and deferred parity ordering / queryability planning
  (Plans 0027-0028). Lane 3 schema stability is no longer just planned:
  Plan 0026 is now the completed contract-policy surface, and the first
  read-only query surface is now implemented end to end through Plan 0029.
  The chunk-level transfer evaluation requirement remains active through
  ADR 0023 and Plans 0024/0014 even though there is no standalone Plan 0019
  file.

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
- **After the current value-proof work, the next-active deferred capability is
  queryability.** Plan 0027 now fixes the deferred-capability order, and Plan
  0028 now has a landed first read-only browse/search surface over promoted
  knowledge. Do not widen the DIGIMON seam or start broad new capability tracks
  before Plan 0025 and the first query surface are settled.
- **Flat filler model with strong descriptions** — discriminated unions (oneOf)
  are architecturally correct but no current model can navigate them (all produce
  empty roles). Reverted to flat model with `Field(description=...)` enforcing
  kind-specific requirements + post-parse validator. `minProperties` removed from
  roles (providers don't enforce it; post-parse validator catches empty roles).
- **E2E pipeline proven (2026-03-25).** Text → extraction → validation → review
  → promotion → durable graph. 5 USSOCOM commanders extracted with correct
  ontology types, 100% acceptance. Model: `gemini/gemini-2.5-flash` (stable).
  Root cause of prior empty-roles failures: `gemini-3-flash-preview` regressed
  on structured output between 2026-03-21 and 2026-03-25. OpenRouter routing
  models (gpt-5.4-mini) also failed. Stable Gemini model works.
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
  DIGIMON thin v1 export/import proof (110 exported entities, 99 exported
  relationships, 110 imported nodes, 78 imported edges on the 2026-03-31
  Shield AI proof), and Foundation IR (16 assertions). Next step is
  consumer-side depth and long-tail hardening, not more net-new adapter
  surfaces.
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

## Active Execution Block (2026-04-01)

**Plan 0030: 24h Entity Resolution Value-Proof Block — active until fully closed.**

Execute continuously and do not pause between phases. Finish the current
phase, update the plan/TODO surfaces, commit the verified increment, and move
immediately to the next phase. Never stop at "the harness exists" or "one run
completed." The block is not done until all required phases, run artifacts,
and closeout docs are finished.

The only valid stop conditions are:
1. All 5 phases in `docs/plans/0030_24h_entity_resolution_value_proof_block.md`
   complete and are committed
2. A real blocker that cannot be resolved from repo context or the plan
3. A material uncertainty not covered by the pre-made decisions below

If a sub-phase is blocked, log the blocker in the active plan, `TODO.md`, and
the run note, then continue with the next unblocked phase. Do not silently
abandon a phase. Do not ask what to do next while the active block still has
unfinished phases.

Pre-made decisions (do not ask about these):
- Config defaults: `review_mode: llm`, `enable_judge_filter: true`
- Fuzzy matching is a pre-filter for LLM validation, not an independent merge strategy
- Synthetic corpus for Phase 4 (controlled ground truth)
- Single LLM call per entity type; batch if token count exceeds threshold
- All LLM calls through llm_client with `task`, `trace_id`, and `max_budget`
- Prompt templates in `prompts/resolution/` as YAML/Jinja2
- Commit each verified phase immediately
- Work stays in the isolated `codex/onto-canon6-integration-planning` worktree

## Completed 24h Execution Block (2026-03-31)

**Plan 0029: First Query Surface — complete.**

The bounded execution block landed:

1. shared read-only query service;
2. thin CLI commands for the first five browse/search operations;
3. thin MCP tools over the same service contracts;
4. real-proof verification against the canonical proof DB;
5. doc/status/closeout updates.

`TODO.md` remains the live execution tracker pattern for future bounded blocks,
but Plan 0029 itself is no longer active.

## Active 24h Execution Block (2026-03-31)

**Plan 0030: Entity resolution value proof — execute continuously until complete.**

This is a bounded 24-hour implementation block, not an open-ended "work a bit"
instruction. The required behavior is:

1. finish one phase;
2. verify it;
3. commit it immediately; then
4. continue directly to the next phase without waiting for another prompt.

The only valid stop conditions are:

1. all Plan 0030 phases are complete;
2. a real blocker makes safe implementation impossible;
3. a material uncertainty appears that is not already covered by Plan 0025,
   Plan 0030, or `TODO.md`.

Do **not** stop because:

1. fixtures are written but metrics are not yet implemented;
2. the evaluator is done but the runner/baseline path is not;
3. the runner is done but the real corpus runs are not;
4. exact results exist but the run note/docs are not updated;
5. you have to record a new uncertainty — log it and continue.

`TODO.md` is the live execution tracker for this block. Keep it current as
phases land. Long-term planning stays in the plan docs; immediate execution
state lives in `TODO.md`.

## Working Rules

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

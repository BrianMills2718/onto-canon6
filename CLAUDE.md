# onto-canon6

`onto-canon6` is the successor bootstrap for the `onto-canon` lineage. It
starts from a proved slice instead of trying to port the entire previous
runtime.

## Read First

1. `README.md`
2. `docs/SUCCESSOR_CHARTER.md`
3. `docs/STATUS.md`
4. `docs/plans/0001_successor_roadmap.md`
5. `docs/plans/0005_v1_capability_parity_matrix.md`

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
- **Active work**: chunk-level transfer evaluation (Plan 0019), extraction
  quality Phase B (Plan 0014).

## Strategic Direction (2026-03-23)

- **Architecture is sound. Bottleneck is extraction quality** (37.5% acceptance
  on PSYOP Stage 1, 80% on Phase B bounded chunks). Focus on prompt iteration
  with `prompt_eval`, not new infrastructure.
- **Discriminated union schema enforces entity_type at decode time** (commit
  `534a52c`). `single_response_hardened` + gpt-5.4-mini: 13/17 cases pass
  (76%), 1.0 structural rate, f1=0.077 (up from 0.0). Schema errors are now
  legitimate rejections. Promoted as operational prompt.
- **No LLM provider enforces value-level JSON Schema constraints** (minProperties,
  minLength, pattern, minimum) at decode time. Only structural constraints (type,
  required, enum) are enforced. Fix applied to llm_client:
  `litellm.enable_json_schema_validation = True` + `JSONSchemaValidationError`
  retryable + repair prompt on retry. Changes pending commit (hook issue in
  llm_client, see llm_client/BACKLOG.md).
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
- **Don't force integration yet** — research_v3 and Digimon are stabilizing.
  Verify Foundation Assertion IR serialization path (see
  `~/projects/project-meta/vision/FOUNDATION.md`), don't wire the pipeline.
- **No more phases/ADRs/subsystems** unless justified by extraction quality
  friction. The 15-phase bootstrap is done. Parity matrix is a ledger, not a queue.
- **Foundation Assertion IR adapter exists** (`adapters/foundation_assertion_export.py`).
  Schema gaps documented: alias_ids, temporal qualifiers, full provenance_refs.
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

## Working Rules

- Use the recorded friction from real runs before reopening broad parity chasing
  or another roadmap extension.
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

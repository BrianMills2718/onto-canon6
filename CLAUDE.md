# onto-canon6

`onto-canon6` is the successor bootstrap for the `onto-canon` lineage. It
starts from a proved slice instead of trying to port the entire previous
runtime.

## Read First

1. `README.md`
2. `docs/SUCCESSOR_CHARTER.md`
3. `docs/STATUS.md`
4. `docs/plans/0024_post_cutover_program.md`
5. `docs/plans/0025_cross_document_entity_resolution.md` (completed Phase 4 value proof)
6. `docs/plans/0031_24h_entity_resolution_hardening_block.md` (completed hardening block)
7. `docs/plans/0032_24h_entity_resolution_recall_recovery_block.md` (completed recall-recovery block)
8. `docs/plans/0033_24h_entity_resolution_answerability_block.md` (completed answerability block)
9. `docs/plans/0034_24h_entity_resolution_clean_measurement_block.md` (completed clean-measurement block)
10. `docs/plans/0035_24h_entity_resolution_alias_family_completion_block.md` (completed alias-family closure block)
11. `docs/plans/0036_24h_entity_resolution_negative_control_recovery_block.md` (completed negative-control recovery block)
12. `docs/plans/0037_24h_entity_resolution_false_split_cleanup_block.md` (completed Rodriguez/Washington cleanup block)
13. `docs/plans/0038_24h_entity_resolution_surface_stability_block.md` (completed surface-stability block)
14. `docs/plans/0039_24h_entity_resolution_rerun_stability_block.md` (completed rerun-stability block)
15. `docs/plans/0040_24h_extraction_transfer_certification_block.md` (completed certification decision block)
16. `docs/plans/0041_24h_full_chunk_transfer_parity_block.md` (completed parity-localization block)
17. `docs/plans/0042_24h_semantic_transfer_residual_block.md` (completed semantic-residual block)
18. `docs/plans/0043_24h_live_path_divergence_block.md` (completed live-path divergence block)
19. `docs/plans/0044_24h_wrapper_alignment_block.md` (completed wrapper-alignment block)
20. `docs/plans/0045_24h_extraction_path_block.md` (completed extraction-path localization block)
21. `docs/plans/0046_24h_sync_async_and_caseid_residual_block.md` (completed prompt-side residual localization block)
22. `docs/plans/0047_24h_case_metadata_parity_block.md` (completed case-id repair block)
23. `docs/plans/0048_24h_prompt_wrapper_parity_block.md` (completed wrapper repair block)
24. `docs/plans/0049_24h_post_repair_transfer_block.md` (completed post-repair chunk-003 rerun block)
25. `docs/plans/0050_24h_post_parity_semantic_recovery_block.md` (completed failed bounded semantic attempt)
26. `docs/plans/0051_24h_analytical_section_suppression_block.md` (completed failed section-level suppression attempt)
27. `docs/plans/0052_24h_predicate_locality_gate_block.md` (completed narrowing block)
28. `docs/plans/0053_24h_abstract_result_and_citation_block.md` (completed failed hard-negative attempt)
29. `docs/plans/0054_24h_full_chunk_strict_omit_contract_audit.md` (completed audit block)
30. `docs/plans/0055_24h_chunk017_contract_cutover_and_rebaseline_block.md` (completed cutover block)
31. `docs/plans/0056_24h_corrected_fixture_semantic_recovery_block.md` (completed corrected-fixture recovery block)
32. `docs/plans/0057_24h_corrected_fixture_transfer_recertification_block.md` (completed false-positive transfer audit)
33. `docs/plans/0058_24h_live_review_alignment_block.md` (completed review-alignment block)
34. `docs/plans/0059_24h_live_chunk003_semantic_residual_block.md` (completed semantic-reduction block)
35. `docs/plans/0060_24h_limit_capability_enforcement_block.md` (completed abstract limit-capability enforcement block)
36. `docs/plans/0061_24h_personnel_membership_enforcement_block.md` (completed staffing-membership enforcement block)
37. `docs/plans/0062_24h_default_extraction_cutover_block.md` (completed default extraction cutover block)
38. `docs/plans/0026_schema_stability_gate.md` (completed Lane 3 contract policy)
39. `docs/plans/0014_extraction_quality_baseline.md` (Lane 4 policy reference; no active transfer-rescue block)
40. `docs/plans/0027_deferred_parity_reprioritization.md`
41. `docs/plans/0028_query_browse_surface.md`
42. `docs/plans/0063_24h_query_browse_widening_block.md` (completed browse widening block)
43. `docs/plans/0064_24h_identity_external_reference_browse_block.md` (completed browse widening block)
44. `docs/plans/0005_v1_capability_parity_matrix.md`
45. `docs/plans/0001_successor_roadmap.md`

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
- **Active work**: extraction quality hardening under an explicit promotion
  gate (Plan 0014),
  vision-gap closure tracking (Plan 0020), the post-cutover execution program
  (Plan 0024), and deferred parity ordering / queryability planning
  (Plans 0027-0028). Lane 3 schema stability is no longer just planned:
  Plan 0026 is now the completed contract-policy surface, and the first
  read-only query surface is now implemented end to end through Plan 0029.
  Plan 0030 is now complete and gives the first decision-grade comparison
  between exact, bare-baseline, and LLM entity-resolution strategies. Plan
  0031 is also now complete: it fixed the stale auto-review judge seam,
  removed the known same-surname false-merge family, and reran the value
  proof. Plan 0032 is now also complete: it removed the document-loss failure,
  materially improved recall and answerability, and cleared its declared gate
  with precision `1.00`, recall `0.615`, false merges `0`, answer rate `0.50`,
  and accuracy `0.40`. Plan 0033 is now complete: it recovered alias-surface
  coverage, localized the remaining miss, and showed that the next blocker was
  a clean measurement run rather than broad new clustering churn. Plan 0034 is
  now also complete: it restored a valid `25/25` clean rerun, improved recall
  to `0.746`, and narrowed the remaining work to three residual alias families.
  Plan 0035 is now also complete: it closed `q02`, `q04`, and `q08`, and the
  fresh clean rerun proved that those alias families are no longer the blocker.
  Plan 0036 is now also complete: it restored same-surname person safety and
  recovered `q05` / `q06` on a fresh rerun. Plan 0037 is now also complete:
  it closed the Rodriguez and Washington residual families truthfully. Plan
  0038 is now also complete under its explicit exit clause: it materially
  improved the acronym/descriptor/evaluator blocker family and produced the
  near-gate `131124` fresh rerun, but the follow-on `132119` rerun proved that
  the next blocker was rerun stability under extraction-shape drift. Plan
  0039 is now also complete: fresh reruns `145141` and `152927` both restored
  `10/10` question accuracy while keeping precision `1.00` and false merges
  `0`, which is enough to close the rerun-stability gate. Plan 0025 is now
  complete at its Phase 4 value-proof level. Plan `0063` is now complete: it
  widened the landed first query surface into a real browse surface with
  source-centric provenance entrypoints and proved that widened surface on the
  real Booz Allen promoted DB. Plans `0040` through `0045`
  completed the chunk-transfer certification and localization sequence:
  chunk `002` stayed a real positive control, chunk `003` remained the only
  meaningful residual, and prompt-surface / wrapper / live-path differences
  were narrowed to a bounded family instead of left speculative. There was no
  further truthful autonomous prompt-only rescue block after Plan `0054`.
  Plans `0046` through
  `0049` are now complete and proved that sync/async API speculation,
  prompt_eval-only `Case id` metadata, and the prompt_eval `Case input:`
  wrapper were all real prompt-path issues but are no longer the active
  blocker. Plan `0050` then proved that one bounded semantic revision changed
  the chunk-003 family without improving the score gate, and Plan `0051`
  proved that another section-level suppression pass made the compact
  operational-parity spillover family worse rather than better. Plan `0052`
  then narrowed the family from `6` candidates to `5`, but left the core
  abstract-result and citation/report spillovers intact. Plan `0053` then
  proved that even stronger hard-negative prompt wording still widened the
  family again. Plan `0054` then answered the next question: chunk `017` is a
  mixed-content benchmark-contract problem, not a clean prompt hardening
  target. The user approved the recommended removal/demotion, and Plan `0055`
  completed the fixture cutover plus one corrected-fixture rerun. Plan `0056`
  then restored the compact operational-parity benchmark lead on corrected
  fixture `v6`. Plan `0057` then reran the named transfer chunks and proved
  that the first chunk-003 positive transfer result was overstated by live
  review-contract drift. Plan `0058` then fixed that contract and reduced the
  chunk-003 false-positive family. Plan `0059` then removed the staffing leak
  and downgraded chunk `003` from `positive` to `mixed`. Plan `0060` then
  removed the remaining abstract `limit_capability` spillover family, Plan
  `0061` removed the staffing-summary membership spillover family, and Plan
  `0062` completed the repo-default extraction cutover onto the proved compact
  operational-parity lane. There is no active extraction-transfer cleanup
  block now; any future extraction-quality work must start from the promoted
  default surface instead of reopening Plans `0057` through `0062`.
  The chunk-level transfer evaluation requirement remains active through
  ADR 0023 and Plans 0024/0014 even though there is no standalone Plan 0019
  file.

## Strategic Direction (2026-03-31)

- **Architecture is sound. Current priority: queryability hardening over the landed promoted-state surface.**
  Plan `0064` is now complete: browse/search can find entities through identity
  and external-reference state without dropping back to maintenance-only
  identity commands. The next narrowed queryability choice is first-class
  source-artifact query unless later evidence changes the order. Cross-document
  entity-resolution proof remains complete at the Phase 4 gate; any next entity
  resolution work is scale-out under `0025a`, not the repo-default active lane.
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
- **24h execution rule: do not stop between bounded phases.** When a 24h
  execution block is active, continue through its declared phase order
  autonomously until the block is truthfully complete or a blocker/uncertainty
  is explicit in the docs. Log uncertainties in the active plan, `TODO.md`,
  and `KNOWLEDGE.md`, then keep moving on the next bounded task instead of
  pausing for conversational check-ins. Treat this as a hard operating rule,
  not a suggestion: keep executing, keep rerunning, keep committing, and only
  stop when the active block is either complete or explicitly narrowed to a new
  documented blocker.
- **Current extraction-quality execution rule:** Plans `0056`, `0057`,
  `0058`, `0059`, `0060`, `0061`, and `0062` are complete. There is no active
  extraction-transfer cleanup block now that the compact operational-parity
  candidate is the repo-default extraction surface.
- **Continuous execution rule is hard, not advisory.** When a 24h block is
  active, keep executing until the approved contract is implemented, the
  bounded rerun is recorded, the next blocker is written down, and the block is
  truthfully closed. If a new uncertainty appears, log it in the active plan,
  `TODO.md`, and `KNOWLEDGE.md`, then continue on the next bounded task unless
  the uncertainty changes the contract itself.
- **Default execution mode for substantial autonomous work is an isolated
  worktree plus explicit merge-back.** When an agent is going to run a
  multi-phase implementation block, use a dedicated worktree/branch by default
  so the main checkout stays readable and rollback stays cheap. Keep commits
  small and verified, then merge the worktree branch back into `main` only
  after the block is truthfully complete. Only stay in the main checkout by
  default for tiny edits or when a worktree would create a bigger risk than it
  removes.
- **Queryability is the active deferred-capability lane now.** Plan 0027 fixed
  the ordering, Plan 0028 landed the first read-only slice, Plan `0063`
  completed the first widening block, and Plan `0064` completed the next
  identity/external-reference-aware widening step. Do not reopen
  extraction-transfer rescue work or widen the DIGIMON seam as a substitute for
  the next narrowed queryability choice.
- **24h execution in this repo is mandatory, not aspirational.** When a block like Plan `0064` is active, agents must keep working through every declared phase in the isolated worktree until the block is truthfully complete. Once the block is closed, update `CLAUDE.md`, `TODO.md`, and the active plans immediately so the next agent does not continue from stale authority text.
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

**Plan 0054: 24h Full-Chunk Strict-Omit Contract Audit — complete.**

Within an active 24h execution block, the default operating mode is continuous
execution: finish the current phase, verify it, commit it, update the active
plan / TODO surface, then continue immediately into the next declared phase.
Do not stop because a smaller slice is complete. If a real uncertainty remains,
log it in the active plan, decision note, TODO, or KNOWLEDGE file and continue
unless it creates a genuine blocker.

Execute continuously and do not pause between phases. Finish the current
phase, update the plan/TODO surfaces, commit the verified increment, and move
immediately to the next phase. Never stop at "one extraction fix landed" or
"one alias family improved." The block is not done until all required phases,
rerun artifacts, and closeout docs are finished.

Treat premature stopping as a repo-level failure mode. While a bounded block is
active, the required behavior is: plan the next concrete phase, execute it,
verify it, commit it, log any uncertainty, and continue. Do not wait for
"what next?" confirmation mid-block.

The current valid stop condition is no longer the `0062`
default-cutover boundary.

1. Plans `0056`, `0057`, `0058`, `0059`, `0060`, `0061`, and `0062` are
   complete and committed.
2. The benchmark lead is restored on corrected fixture `v6`, the review
   contract is aligned, the named chunk-transfer blocker families are closed,
   and the proved compact operational-parity candidate is now the repo default.
3. Any future extraction-quality work must start from that promoted default
   rather than reopening the previous transfer-hardening chain.

Pre-made decisions (do not ask about these):
- Work stays in the isolated `codex/onto-canon6-integration-planning` worktree
- chunk `002` and chunk `003` remain the canonical transfer chunks
- the current compact operational-parity lane is the only candidate under test
- no prompt-surface parity work reopens before the repaired chunk-003 semantic
  family is re-evaluated
- the next lever after 0054 is a user benchmark-contract decision, not another
  prompt-wording pass
- Commit each verified phase immediately

## Most Recent Execution Block (2026-04-01)

**Plan 0045: 24h Extraction-Path Block — complete.**

The extraction-path block now has:

1. one bounded extraction-call comparator over `llm_calls.call_snapshot`;
2. explicit proof that live extraction had been omitting `temperature=0.0`;
3. one live temperature/source-ref aligned chunk-003 rerun;
4. semantic comparison evidence showing the aligned rerun still had `0`
   shared bodies with prompt-eval; and
5. a decision note proving the next blocker is narrower than generic
   extraction-path behavior: sync/async call-path residual plus prompt_eval-only
   `Case id` metadata.

Decision from the block:

1. exact remains the default precision floor;
2. hardened LLM now has zero false merges on the synthetic value-proof corpus;
3. hardened LLM is still not promotable as default because recall and
   fixed-question answerability remain too weak, and one extraction/schema
   failure dropped `doc_06` from the rerun.

Active work therefore returns to Plan 0014's next narrow frontier:
certification-grade extraction transfer evidence on the current compact
operational-parity lane.

## Completed Execution Block (2026-04-01)

**Plan 0030: 24h Entity Resolution Value-Proof Block — complete.**

The value-proof block now has:

1. a frozen corpus and question set;
2. exact, bare-baseline, and LLM strategy run artifacts;
3. a written decision note in
   `docs/runs/2026-04-01_entity_resolution_value_proof.md`.

Decision from the block:

1. exact matching remains the high-precision floor;
2. the bare baseline is not competitive;
3. LLM clustering improves recall materially but is not ready for default
   promotion because false merges and question regressions remain.

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

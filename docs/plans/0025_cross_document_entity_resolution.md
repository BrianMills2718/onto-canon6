# Cross-Document Entity Resolution

Status: planned

Last updated: 2026-03-31
Workstream: entity resolution for scale test (20-500 documents)

## Purpose

Enable onto-canon6 to resolve the same real-world entity mentioned differently
across documents ("Gen. Smith" in Document A, "General John Smith" in Document B)
into a single identity. This is a prerequisite for the cross-document scale test
that proves onto-canon6's value proposition.

Without this, every document produces isolated entity islands. The scale value
(cross-document entity resolution, contradiction detection, typed reasoning)
cannot be demonstrated.

## What Exists Today

| Capability | Status | Limitation |
|---|---|---|
| Exact-name grouping | Working | "Gen. Smith" ≠ "General John Smith" |
| Fuzzy matching (rapidfuzz token_sort_ratio) | Working | Catches some variations, misses abbreviations/titles |
| Entity-type guard | Working | Prevents cross-type false merges |
| Within-doc coreference (LLM) | Working | Resolves mentions within one extraction only |
| Identity infrastructure | Working | Canonical + alias memberships, external refs |
| **Cross-document resolution** | **Missing** | New extractions never compared to existing entities |
| **Name normalization** | **Missing** | No title/honorific stripping |
| **LLM-based entity clustering** | **Missing** | No "are these the same entity?" LLM calls |

## Approach

**KGGen-style LLM clustering**, chosen for simplicity at investigation scale.

At 20-500 documents, entity counts are hundreds to low thousands — small enough
to pass to an LLM per type. No blocking or embedding infrastructure needed.
This is the approach validated by KGGen (NeurIPS 2025, 66% MINE benchmark).

Design for single LLM call per type; add batching when a type's entity list
exceeds a configurable token threshold. Frontier models have 1M token context
windows, but quality likely degrades as entity lists grow. Monitor empirically:
log entity count and token count per clustering call, correlate with merge
quality in Phase 4.

**Fuzzy matching is a pre-filter, not an independent strategy.** Fuzzy matching
(rapidfuzz) generates candidate clusters cheaply, but these candidates MUST go
through LLM review because fuzzy matching produces false dedup (e.g., "USSOCOM"
matching "USSOCOM Commander" even with type guards). The pipeline is:
normalize → fuzzy candidate clusters → LLM validates/rejects each cluster.

**Why not the full tiered pipeline (normalize → fuzzy → embed → LLM adjudicate)?**
That's the right approach at 500+ documents where entity lists don't fit in LLM
context. Documented in deferred plan (Plan 0025a). For now, the simpler approach
gets us to the scale test faster.

## Pre-Made Decisions

1. Resolution runs AFTER promotion, over promoted entities (not raw candidates).
   Identities are over stable entities, not draft candidates.
2. Resolution is type-blocked: only compare Person-to-Person, Org-to-Org, etc.
   The entity-type guard already exists and is proven.
3. All LLM calls go through llm_client with mandatory task/trace_id/max_budget.
4. Resolution results wire into the existing identity subsystem (canonical + alias
   memberships). No new identity infrastructure needed.
5. `review_mode: llm` and `enable_judge_filter: true` become the config defaults.
6. The `llm` resolution strategy is additive — exact and fuzzy strategies remain
   available. Config selects which to use.
7. Prompt template for clustering lives in `prompts/resolution/` as YAML/Jinja2.

## Phases

### Phase 1: Config Defaults & Name Normalization

**Goal**: Fix operating defaults and add title/honorific normalization.

**Tasks**:
1. Change config.yaml: `review_mode: llm`, `enable_judge_filter: true`
2. Add name normalization to `auto_resolution.py`:
   - Title/honorific stripping: Gen., General, Dr., Mr., Mrs., Col., Colonel,
     Sgt., Sergeant, Lt., Lieutenant, Maj., Major, Capt., Captain, Adm.,
     Admiral, Cmdr., Commander, Pvt., Private, Cpl., Corporal, etc.
   - Abbreviation expansion: common military/government abbreviations
   - Punctuation normalization (strip periods from abbreviations)
   - Wire into `_normalize_name()` as a preprocessing step
3. Tests for normalization: "Gen. Smith" normalizes to same key as "General Smith"

**Acceptance**:
- `_normalize_name("Gen. John Smith")` == `_normalize_name("General John Smith")`
- Existing exact/fuzzy tests still pass
- Config defaults changed

**Estimate**: ~2 hours

### Phase 2: LLM Entity Clustering

**Goal**: Add LLM-based entity clustering with fuzzy pre-filtering.

**Design**: Two-stage pipeline per entity type:
1. **Fuzzy candidate generation**: rapidfuzz token_sort_ratio generates candidate
   clusters (cheap, fast, noisy). These are PROPOSALS, not final merges.
2. **LLM validation**: Each fuzzy-proposed cluster (and any remaining unclustered
   entities) goes to the LLM for validation. The LLM can: confirm a cluster,
   split it, merge additional entities into it, or reject it entirely.
   For types with few entities (<50), skip fuzzy and send all directly to LLM.

This prevents fuzzy false dedup while keeping LLM costs low (fuzzy narrows
the search space so the LLM doesn't need to evaluate all n² pairs).

**Tasks**:
1. Create prompt template `prompts/resolution/cluster_entities.yaml`:
   - Input: list of entities with names, types, and context snippets
   - Optionally include fuzzy-proposed clusters as hints for LLM to validate
   - Instruction: identify groups of entities that refer to the same real-world entity
   - Output schema: list of clusters, each with canonical name + member entity IDs + reasoning
2. Add `_group_by_llm()` to `auto_resolution.py`:
   - Collect all promoted entities with names, types, context (from assertion claim_text)
   - Group by entity_type
   - For types with >50 entities: run fuzzy pre-filter first, send proposals to LLM
   - For types with ≤50 entities: send all directly to LLM
   - If entity list exceeds token threshold: batch into chunks, merge clusters across batches
   - Log entity count + token count per LLM call (quality monitoring)
   - Parse cluster assignments
   - Return groups in same format as `_group_by_name()` / `_group_by_fuzzy()`
3. Add `strategy="llm"` to `ResolutionStrategy` type and `auto_resolve_identities()`
4. Add `resolution` section to config.yaml with model, max_budget, prompt_template,
   fuzzy_pre_filter_threshold, batch_token_limit
5. Tests: mock LLM for unit tests; one integration test with real LLM call

**Structured output schema** (Pydantic):
```python
class EntityCluster(BaseModel):
    canonical_name: str = Field(description="Best full canonical name for this entity")
    entity_ids: list[str] = Field(description="Entity IDs that refer to this same entity")
    reasoning: str = Field(description="Why these are the same entity, citing evidence")

class ClusteringResult(BaseModel):
    clusters: list[EntityCluster]
```

**Acceptance**:
- `auto_resolve_identities(strategy="llm")` produces cluster assignments
- Fuzzy-proposed clusters go through LLM validation (no direct fuzzy merges)
- LLM calls go through llm_client with task/trace_id/max_budget
- Clusters wire into identity subsystem (canonical + alias memberships)
- Entity-type blocking works (only compares within type)
- Batching works when entity list exceeds token threshold
- Entity count + token count logged per LLM call
- Unit tests with mocked LLM pass
- One real LLM test demonstrates "Gen. Smith" + "General John Smith" merge

**Estimate**: ~6-8 hours

### Phase 3: Pipeline Integration

**Goal**: Make resolution a natural step in the extract → govern → resolve → export pipeline.

**Tasks**:
1. Add `make resolve` target (runs auto_resolve_identities with configured strategy)
2. Add `make govern` update: include resolution step after promote-all
   (current: accept-all + promote-all + auto-resolve; add: identity resolution)
3. Wire coreference module output into resolution input:
   - Within-doc coreference (existing) resolves surface forms at extraction time
   - Cross-doc resolution (new) merges identities at promotion time
   - These are complementary, not competing
4. Add resolution strategy to config.yaml extraction section
5. Update CLI: `onto-canon6 auto-resolve-identities --strategy llm`
6. Update identity report to show resolution provenance (which strategy merged which)

**Acceptance**:
- `make extract INPUT=... && make govern` runs full pipeline including resolution
- Identity report shows cross-document merges with strategy attribution
- Digimon export uses resolved identities (merged entities, not duplicates)

**Estimate**: ~3-4 hours

### Phase 4: Scale Test

**Goal**: Prove onto-canon6's value on a real multi-document corpus.

**Tasks**:

**4a. Design synthetic corpus with ground truth:**
- Generate 20-50 documents about a realistic scenario with overlapping entities
- The corpus MUST have known ground truth for entity resolution:
  - Entity registry: list of real-world entities with all name variants used
  - Cross-document ground truth: which entities appear in which documents
  - Expected merges: which extracted entities should resolve to the same identity
  - Expected non-merges: entities with similar names that are different people/orgs
- Include deliberate challenges:
  - Title variations ("Gen. Smith", "General John Smith", "Smith")
  - Abbreviations ("USSOCOM" vs "United States Special Operations Command")
  - Ambiguous names ("Washington" the person vs "Washington" the location — type guard test)
  - Partial overlaps (some entities unique to one doc, some span 5+ docs)
- Domain: military/OSINT (matches existing ontology packs) or general-purpose

**4b. Run full pipeline:**
- Extract all documents with LLM review mode (`review_mode: llm`, judge filter on)
- Promote all accepted
- Run LLM entity resolution (strategy="llm")
- Export to Digimon

**4c. Measure entity resolution quality:**
- Entity count before vs after resolution (dedup ratio)
- Precision: fraction of merges that are correct (compare against ground truth)
- Recall: fraction of ground-truth merges that were found
- False merges (merged entities that shouldn't be)
- False splits (entities that should have merged but didn't)
- Cross-document connections found (relationships spanning documents)
- Resolution quality vs entity list length (empirical context window monitoring)

**4d. Compare against bare extraction:**
- Same corpus, simple "extract entities and relationships as JSON" prompt
- No ontology, no governance, no resolution
- Feed to Digimon, ask same queries

**4e. Cross-document synthesis evaluation:**
- Ask 10-20 questions that REQUIRE cross-document synthesis
  ("what entities appear in both funding and operational networks?")
- Score answers with LLM-judge
- Compare onto-canon6 pipeline vs bare extraction

**Acceptance**:
- Entity resolution precision >90% (few false merges)
- Entity resolution recall >70% (finds most real matches)
- Cross-document questions answered measurably better than bare extraction
- Resolution quality vs. entity count diagnostic logged and analyzed
- Results documented in `docs/runs/`

**Estimate**: ~2-3 days (including corpus design)

### Phase 5: Deferred — Scale-Out (500+ Documents)

See `docs/plans/0025a_entity_resolution_scale_out.md`.

Not started until Phase 4 proves the approach works at 20-500 scale.

## Failure Modes

1. **LLM over-merges**: Clusters unrelated entities with similar names.
   Mitigation: entity-type guard + context snippets in prompt + reasoning field
   for auditability.
2. **LLM under-merges**: Misses obvious matches.
   Mitigation: run fuzzy matching first, then LLM clustering. Fuzzy catches
   the easy cases; LLM handles the hard ones.
3. **Context window overflow**: Too many entities of one type for LLM context.
   Mitigation: at investigation scale this shouldn't happen. If it does,
   batch entities and merge clusters across batches (simple extension).
4. **Extraction quality too low**: Pipeline produces too much noise for
   resolution to work on.
   Mitigation: LLM judge filter removes unfaithful extractions before
   promotion. Resolution operates on judge-approved entities only.

## Relationship to Other Plans

- **Plan 0024 Lane 2 (Consumer Adoption)**: Phase 4 is the value proof that
  enables consumer adoption.
- **Plan 0024 Lane 4 (Extraction Quality)**: LLM judge mode makes extraction
  quality evidence-driven.
- **Plan 0014 (Extraction Quality Baseline)**: Resolution quality depends on
  extraction quality. The two are complementary.
- **Plan 0020 Gap 3 (Cross-Investigation Entity Resolution)**: This plan
  partially closes Gap 3. Full closure requires the scale-out deferred work.
- **STRUCTURED_OUTPUT_QUALITY.md** (project-meta/vision): Entity clustering
  prompt is itself a structured output quality problem — the clustering prompt
  should eventually be optimizable via prompt_eval.

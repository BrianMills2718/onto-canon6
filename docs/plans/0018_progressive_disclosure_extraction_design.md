# Progressive Disclosure Extraction Design

Status: complete
Updated: 2026-03-21
Implements: ADR-0018
Blocked by: ~~Plan 0017 empirical results~~ (unblocked — data collected)
Depends on: Plan 0016 (permissive extraction), v1 Predicate Canon data

## Empirical Results (Plan 0017, 2026-03-21)

Model: `gemini/gemini-2.5-flash-lite`. 8 entity fixtures, 3 fidelity levels.

| Metric               | top_level (50 types) | mid_level (~30/branch) | full_subtree |
|----------------------|---------------------|----------------------|--------------|
| Exact match          | **62.5%**           | 25.0%                | 25.0%        |
| Ancestor match       | **87.5%**           | 62.5%                | 50.0%        |
| Mean specificity     | 0.836               | 0.875                | 0.708        |
| Wrong branch         | **12.5%**           | 37.5%                | 50.0%        |
| Cost                 | $0.0003             | $0.0006              | $0.0009      |

### Resolved Questions

1. **Ancestor match rate on coarse picks**: 87.5% at top_level. Strong enough
   for Pass 1 to serve as a reliable branch selector.

2. **Wrong-branch rate**: 12.5% at top_level, escalating to 50% at full_subtree.
   More types = more confusion. Long type lists actively hurt.

3. **Fidelity cost-accuracy tradeoff**: More types degrade performance. The
   "show full subtree" strategy is the worst performer. Mid-level is only useful
   when constrained to the correct subtree (which requires Pass 1 first).

4. **Model variation**: Not yet tested (single model so far). This is a
   follow-up question, not a blocker.

### Design Implications

- **Top-level seeding is the right starting point.** 87.5% ancestor match at
  50 types beats 62.5% at ~30 and 50% at full subtree.
- **The wrong-branch problem is the primary failure mode**, not lack of
  specificity. Pass 2/3 must constrain to the correct subtree, not just
  add more types.
- **Specificity > 1.0 is valid.** The LLM sometimes picks a *more specific*
  descendant than the reference type (e.g. Human → HumanAdult). This is
  a feature, not a bug — the ancestor evaluator scores it correctly.

---

## Finalized Pass Structure

### Pass 1: Entity Extraction + Coarse Typing (top_level seeding)

- **Input**: Raw text chunk + ~50 top-level SUMO types (the curated
  `TOP_LEVEL_TYPES` from `fidelity_experiment.py`)
- **Prompt**: "Extract entities and relationships. For each entity, pick the
  best SUMO type from this list. For relationships, identify the verb/action
  and which entities are involved."
- **Output**: `list[Pass1Triple]` — each has `entity_a`, `entity_b`,
  `relationship_verb`, coarse types for each entity, evidence span
- **Model**: `gemini/gemini-2.5-flash-lite` (cheap bulk)
- **Contract**: No strict schema. Partial results valid (ADR-0017).
- **Expected accuracy**: ~87% of entity types land in the correct SUMO branch

### Pass 2: Predicate Mapping (lemma lookup + disambiguation)

- **Input**: Pass 1 triples
- **For each triple**: Normalize `relationship_verb` to lemma, look up in
  `predicates` table by lemma
- **Early exit (78.1% of cases)**: If lemma maps to exactly one PropBank
  sense, assign it deterministically. No LLM call.
- **LLM disambiguation (21.9%)**: Show the 2-10 candidate predicates with
  descriptions and role schemas. LLM picks the best match.
- **Output**: `list[Pass2MappedAssertion]` — each has predicate ID, role
  schema, mapped roles from the triple
- **Model**: Same as Pass 1 for disambiguation calls
- **Contract**: Predicate must exist in Predicate Canon. Unknown lemmas
  are stored as unresolved candidates (permissive).

### Pass 3: Entity Refinement (narrowed subtree typing)

- **Input**: Pass 2 mapped assertions
- **For each role filler**:
  1. Get the role's `type_constraint` from `role_slots` table
  2. Get the entity's Pass 1 coarse type
  3. Find the **intersection**: the narrowest SUMO type that is an ancestor
     of both the role constraint and the coarse pick (or descendants of
     the coarse pick that satisfy the constraint)
  4. Show the subtree under that intersection point (~10-30 types)
- **LLM call**: "Given entity X in context Y, pick the most specific SUMO
  type from this narrowed list"
- **Early exit**: If coarse type already satisfies the role constraint and
  is a leaf, no refinement needed
- **Output**: `list[Pass3TypedAssertion]` — fully typed assertions
- **Model**: Same as Pass 1, or configurable per-pass

### Pass 4+: Optional Enrichment (future, not in scope)

- FrameNet frame enrichment (deterministic via SemLink where available)
- Wikidata entity linking
- Cross-source corroboration
- Role-filling enrichment on stored partial candidates

---

## Data Models

```python
class Pass1Triple(BaseModel):
    """Raw extraction from Pass 1."""
    entity_a: str
    entity_a_type: str          # Coarse SUMO type from top_level list
    entity_b: str
    entity_b_type: str
    relationship_verb: str      # Raw verb/action phrase
    evidence_span: str          # Source text excerpt
    confidence: float           # LLM self-assessed confidence

class Pass2MappedAssertion(BaseModel):
    """Predicate-mapped assertion from Pass 2."""
    triple: Pass1Triple
    predicate_id: str           # e.g. "abandon_leave_behind"
    propbank_sense_id: str      # e.g. "abandon-01"
    process_type: str           # SUMO process type
    mapped_roles: dict[str, str]  # ARG0 → entity_a, ARG1 → entity_b, etc.
    disambiguation_method: str  # "single_sense" | "llm_pick"

class Pass3TypedAssertion(BaseModel):
    """Fully typed assertion from Pass 3."""
    assertion: Pass2MappedAssertion
    entity_types: dict[str, str]  # entity_name → refined SUMO type
    type_evidence: dict[str, str]  # entity_name → reasoning
```

## Build Order

### Slice A: Predicate Canon Bridge (no LLM calls)

**Files:**
- `src/onto_canon6/evaluation/predicate_canon.py` — read-only interface to
  `predicates`, `role_slots`, and `type_ancestors` tables in sumo_plus.db.
  Lemma lookup, single-sense detection, candidate listing, role constraint
  resolution.
- `tests/evaluation/test_predicate_canon.py` — deterministic tests against
  real DB

**Acceptance criteria:**
- [x] `lookup_by_lemma("abandon")` returns 3 candidates with role schemas
- [x] `is_single_sense("abate")` returns True
- [x] `get_role_constraints("abandon_leave_behind")` returns
  `{ARG0: "AutonomousAgent", ARG1: "Entity", ARG2: "Object"}`
- [x] Context manager protocol (same pattern as SUMOHierarchy)

### Slice B: Pass 1 — Open Extraction Prompt

**Files:**
- `prompts/extraction/pass1_open_extraction.yaml` — Jinja2 template
- `src/onto_canon6/pipeline/progressive_extractor.py` — `run_pass1()`
- `tests/pipeline/test_progressive_extractor_pass1.py` — mocked LLM tests

**Acceptance criteria:**
- [x] Prompt renders with entity list and top_level types
- [x] LLM output parses into `list[Pass1Triple]`
- [x] Partial results (missing entity_b, missing type) are accepted
- [x] Results stored as permissive candidates (ADR-0017)

### Slice C: Pass 2 — Predicate Mapping

**Files:**
- `prompts/extraction/pass2_predicate_disambiguation.yaml` — Jinja2 template
- `src/onto_canon6/pipeline/progressive_extractor.py` — `run_pass2()`
- `tests/pipeline/test_progressive_extractor_pass2.py`

**Acceptance criteria:**
- [x] Single-sense lemmas (78%) bypass LLM
- [x] Multi-sense lemmas show only matching candidates
- [x] Unknown lemmas stored as unresolved (permissive)
- [x] Mapped roles match predicate schema

### Slice D: Pass 3 — Entity Refinement

**Files:**
- `prompts/extraction/pass3_entity_refinement.yaml` — Jinja2 template
- `src/onto_canon6/pipeline/progressive_extractor.py` — `run_pass3()`
- `tests/pipeline/test_progressive_extractor_pass3.py`

**Acceptance criteria:**
- [x] Subtree narrowing uses role constraint + Pass 1 coarse type
- [x] Leaf types bypass refinement
- [x] Refined types exist in SUMO hierarchy
- [x] Ancestor evaluator confirms improvement over Pass 1 types

### Slice E: Pipeline Orchestrator

**Files:**
- `src/onto_canon6/pipeline/progressive_extractor.py` — `run_progressive_extraction()`
- `tests/pipeline/test_progressive_extraction_e2e.py`
- CLI command: `onto-canon6 extract-progressive`

**Acceptance criteria:**
- [x] Full pipeline: text → Pass 1 → Pass 2 → Pass 3 → typed assertions
- [x] Each pass stores intermediate candidates (permissive)
- [x] Pass provenance tracked on each candidate
- [x] Cost reported per pass
- [x] At least one real text produces correct assertions end-to-end

---

## Risk Register

1. **Wrong-branch propagation**: If Pass 1 puts an entity in the wrong branch
   (12.5% rate), Pass 3 will refine within the wrong subtree. Mitigation:
   permissive storage means the wrong-branch result is still a candidate.
   A future "re-route" pass could detect and correct these using the
   predicate's role constraint as a cross-check.

2. **Lemma normalization**: The relationship verb from Pass 1 may not
   exactly match lemmas in the Predicate Canon. Mitigation: use a lemmatizer
   (spaCy or similar) to normalize. Fuzzy matching as fallback.

3. **Predicate Canon coverage**: Not all verbs/relationships will have
   Predicate Canon entries. Mitigation: unresolved predicates are stored
   as permissive candidates. This is expected and handled by design.

4. **Role mapping ambiguity**: Which entity fills which role may be ambiguous
   from the triple alone. Mitigation: Pass 2 shows role descriptions and
   constraints alongside the triple for LLM disambiguation.

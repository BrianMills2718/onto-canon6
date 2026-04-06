# Plan 0072 — Entity Normalization Pass (Anaphor Resolution + Deduplication)

**Status:** Draft  
**Created:** 2026-04-06  
**Priority:** High — fundamental KG quality gate before any downstream use

---

## Problem Statement

Two structural defects degrade graph quality in every pipeline run:

1. **Anaphors**: entity names that refer to a real entity but don't name it —
   "the group", "the attackers", "the conspirators", "they". These create false
   nodes and dilute the graph's signal. Pass 1 prompt v2.2 reduced them from
   69 → 7 per run, but can't eliminate them because some cases are genuinely
   ambiguous from the LLM's view of a single chunk.

2. **Near-duplicates**: multiple names for the same real-world entity —
   "IRGC" / "Islamic Revolutionary Guard Corps Intelligence Organization (IRGC-IO)" /
   "The IRGC's Shahid Kaveh Group". These fragment the graph: edges that should
   converge on one node are spread across several. Downstream consumers (the
   browser, Digimon) cannot aggregate facts about an entity they don't know is
   one entity.

Both are **entity identity problems**: the question in each case is "what is
the canonical name for the real-world thing this string refers to?"

The resolution pattern used across onto-canon6 (flag → LLM attempt → review →
apply) fits both problems exactly.

---

## Design

### Where it lives

A new **Pass 4: Entity Normalization** in the progressive extractor, running
after Pass 3 entity typing but before `submit-progressive`. It operates on the
full entity list from all events in the report, has access to the source text,
and emits a `normalization_map: dict[str, str]` — a mapping from raw entity
name to canonical name. Events are rewritten using the map before submission.

Running before submission is preferred over a post-DB pass because:
- The graph never contains dirty data
- No merge/split operations needed on already-promoted records
- Simpler rollback (just re-run the extractor)

A post-DB normalization service is deferred (Plan 007x+1) for cases where
coreferent entities surface across *multiple* documents.

### Sub-pass 4a: Anaphor Resolution

**Detection (rule-based, zero cost):**
- Entity name is a pronoun or pronoun phrase: "they", "it", "this"
- Entity name matches `(the|a|an)\s+(group|actors|attackers|conspirators|target|organization|unit|team|regime|company|network|adversary|gang|collective|entity)$` (case-insensitive)
- Entity name is a descriptor clause > 60 chars that contains no proper noun (heuristic: no capitalized word other than first word)

**Resolution (LLM, bounded):**
Input:
- The flagged entity name
- The full entity list from the run (candidate referents)
- The evidence_span(s) from assertions where the anaphor appears
- A short excerpt of source text around each evidence_span

Prompt: "Given this list of named entities and the source text below, what
named entity does '{anaphor}' refer to? Return the exact name from the entity
list, or UNRESOLVABLE if it cannot be determined."

Output:
- `resolved_to: str | None` — matched name from entity list
- `confidence: float`
- `evidence: str` — one-sentence justification

**Apply:**
- confidence ≥ 0.85: auto-apply (rewrite anaphor → resolved_to in all events)
- 0.5 ≤ confidence < 0.85: flag with `resolution_status="uncertain"`, include
  in report but mark in graph node for human review
- confidence < 0.5 or UNRESOLVABLE: omit participant from event (current behavior)

### Sub-pass 4b: Near-Duplicate Detection + Merging

**Detection (two tiers):**

Tier 1 — String heuristics (zero LLM cost):
- Substring containment: "IRGC" ⊂ "Islamic Revolutionary Guard Corps (IRGC)" → candidate pair
- Edit distance < 3 on normalized forms (lowercase, strip punctuation)
- One name is a known abbreviation/acronym of the other (acronym check: first-letter match)

Tier 2 — Embedding similarity (optional, flag with `--embed-dedup`):
- Compute embeddings for all entity names
- Cosine similarity > 0.92 → candidate pair
- Only run if total unique entities > 50 (below that, string heuristics suffice)

**Critical guard — type-based rejection:**
Before sending a candidate pair to LLM resolution, check SUMO types:
- If one entity is `Organization`/`Agent` subtype and the other is `Process`/
  `Attribute`/`Proposition`, they are NOT duplicates — reject without LLM call.
  ("APT42" vs "APT42 operations": Organization ≠ Process)
- Only send pairs with compatible SUMO types to the LLM.

**Resolution (LLM, per surviving candidate pair):**
Input:
- Entity A: name + SUMO type + sample evidence spans
- Entity B: name + SUMO type + sample evidence spans
- Source text excerpt

Prompt: "Are these two entity names referring to the same real-world entity?
If yes, which name is the canonical form? If no, are they related (e.g. part/
whole) or entirely distinct?"

Output:
- `verdict: "same" | "related" | "distinct"`
- `canonical: str` — the preferred name if same
- `confidence: float`
- `relation: str` — brief description if related

**Apply:**
- verdict="same", confidence ≥ 0.85: merge (rewrite B → A canonical in all events)
- verdict="same", confidence < 0.85: flag as `merge_candidate` in graph node
- verdict="related": add a `related_to` edge in the graph (not a merge)
- verdict="distinct": no action

---

## Data Model Changes

New fields on `Pass1Event.participants[*]`:

```python
class Pass1Participant(BaseModel):
    proto_role: str
    entity: Pass1Entity
    resolution_status: Literal["canonical", "resolved", "uncertain", "unresolvable"] = "canonical"
    resolved_from: str | None = None  # original anaphor text if resolved
```

New top-level field on `ProgressiveExtractionReport`:

```python
class ProgressiveExtractionReport(BaseModel):
    ...
    pass4: Pass4NormalizationResult | None = None
```

```python
class Pass4NormalizationResult(BaseModel):
    anaphor_resolutions: list[AnaphorResolution]
    merge_decisions: list[MergeDecision]
    normalization_map: dict[str, str]  # raw_name → canonical_name
    cost_usd: float
    model: str
```

---

## Acceptance Criteria

1. **Anaphor rate**: After Pass 4, entities with `resolution_status != "canonical"` 
   account for < 2% of total participants in the v3 corpus run.

2. **No valid entity loss**: Known canonical entities (APT42, IRGC-IO, Iran,
   Microsoft, Google) must appear in the final graph with the same assertion
   count ± 10% vs the Pass 3 output.

3. **Type-guard works**: "APT42 operations" and "APT42" must NOT be merged.
   Verified by asserting distinct nodes for both in the output graph.

4. **IRGC deduplication**: "IRGC", "IRGC-IO", "Islamic Revolutionary Guard Corps"
   should be candidates; the canonical form should be the longest/most specific
   one. Verify at least two of these collapse to one node.

5. **Cost**: Pass 4 should not exceed 20% of total extraction budget (i.e., ≤
   10% of max_budget for a typical run).

6. **All existing tests still pass** (21/21 — counts will update after v4 run).

---

## Failure Modes

| Failure | Diagnosis |
|---------|-----------|
| Over-merging (valid entities collapsed) | Check type-guard logic; expand SUMO type rejection list |
| Under-merging (obvious duplicates missed) | Lower string heuristic thresholds; check acronym detection |
| Anaphor resolved to wrong entity | Check evidence spans sent to LLM; may need wider context window |
| Budget exceeded | Pass 4 budget cap kicks in; uncertain cases flagged rather than resolved |
| LLM returns entity not in list | Strict validation: only accept names present in entity list |

---

## Implementation Phases

| Phase | Task | Acceptance |
|-------|------|-----------|
| 1 | Data model: add Pass4 types to `progressive_types.py`; all tests still pass | green tests |
| 2 | Sub-pass 4a: detection (rule-based) + resolution LLM call + normalization map | anaphor rate < 2% on v3 corpus |
| 3 | Sub-pass 4b: Tier 1 string heuristics + type-guard + merge LLM call | IRGC dedup AC passes |
| 4 | Rewrite events using normalization_map before submission | full pipeline run produces clean v4 dataset |
| 5 | Update browser backend tests for v4 counts | 21/21 pass |
| 6 | Sub-pass 4b Tier 2: embedding similarity (optional, behind flag) | deferred |

---

## Deferred

- **Cross-document normalization**: entities that are coreferent across
  multiple source documents. This requires a post-DB normalization service
  that can see all runs, not just one. Deferred to Plan 0073.
- **Embedding-based dedup** (Tier 2): deferred to Phase 6 above; string
  heuristics + type-guard cover the clear cases first.
- **Interactive review surface**: flagged `merge_candidate` and `uncertain`
  nodes are currently visible in the browser as low-confidence markers.
  A dedicated review UI is deferred to the investigation browser plan.

# Entity Resolution Scale-Out (500+ Documents)

Status: deferred

Last updated: 2026-03-31
Workstream: entity resolution beyond investigation scale
Depends on: Plan 0025 Phase 4 results

## Purpose

Document the approach for entity resolution at larger scale (500-10K+ documents)
where the KGGen-style "dump all entities to LLM" approach breaks down. This plan
activates only after Plan 0025 Phase 4 proves the value at 20-500 scale.

## Why Deferred

At 20-500 documents, entity counts are hundreds to low thousands — fits in LLM
context. At 500+ documents, entity counts reach tens of thousands. The full
entity list no longer fits in a single LLM call. Different infrastructure is
needed.

## Approach: Tiered Pipeline

The SOTA for large-scale entity resolution is a tiered pipeline that progresses
from cheap/fast/approximate to expensive/slow/accurate:

### Tier 1: Deterministic Normalization (free, instant)
- Title/honorific stripping (from Plan 0025 Phase 1)
- Abbreviation expansion
- Punctuation normalization
- Case normalization

### Tier 2: Fuzzy Matching (nearly free, very fast)
- rapidfuzz token_sort_ratio (from existing `auto_resolution.py`)
- Entity-type guard (from existing code)
- Auto-merge above high threshold (e.g., >95)

### Tier 3: Embedding-Based Candidate Generation (cheap, fast)
- Embed (entity name + type + context snippet) with sentence-transformer
- Index with FAISS or Annoy for nearest-neighbor search
- Find candidate pairs with cosine similarity > configurable threshold
- This is the BLOCKING step — reduces O(n²) comparisons to O(n log n)
- New dependencies: sentence-transformers, faiss-cpu (or annoy)

### Tier 4: LLM Adjudication (expensive, accurate)
- For candidate pairs from Tier 3 that score between thresholds
  (not confident enough to auto-merge, not dissimilar enough to skip)
- Send both entity profiles + source contexts for yes/no merge decision
- ~$0.001-0.01 per comparison with fast model (gemini-flash-lite)

### Tier 5: Role-Constraint Resolution (unique to onto-canon6)
- If both entities fill the same role for the same organization in the
  same time period, strong positive evidence for merge
- If both fill the same unique role (e.g., "commander") for the same org
  at the same time, near-certain match
- Requires temporal qualifier extraction to be working
- This is an untapped signal that no existing system exploits

### Transitive Closure
- Union-Find (already implemented in `auto_resolution.py`)
- After all tiers, compute transitive closure
- Select canonical name (fullest form) for each cluster

## Infrastructure Needed

| Component | Dependency | Where it lives |
|---|---|---|
| Name normalization | None (stdlib) | onto-canon6 auto_resolution.py |
| Fuzzy matching | rapidfuzz (existing) | onto-canon6 auto_resolution.py |
| Embedding similarity | sentence-transformers, faiss-cpu | New: shared infra or onto-canon6 |
| LLM adjudication | llm_client (existing) | onto-canon6 auto_resolution.py |
| Role-constraint matching | onto-canon6 ontology runtime | onto-canon6 auto_resolution.py |

## Decision: Shared Infra vs. onto-canon6-Local?

**Undecided.** The resolution ALGORITHM (tiers 1-4) is general-purpose — any KG
project needs entity resolution. The identity STORAGE (canonical/alias memberships,
external refs) is onto-canon6-local.

Options:
1. Build everything in onto-canon6, extract to shared infra when a second consumer needs it
2. Build the algorithm as a shared library from the start, have onto-canon6 call it

Recommendation: Option 1. Don't premature-abstract. Extract when there's a real
second consumer.

## Incremental/Streaming Resolution

At scale, new documents arrive continuously. Resolution must be incremental:
- New entities compared against existing identity clusters (not full re-resolution)
- FAISS index updated incrementally
- Tier 4 LLM adjudication only for new entities vs. existing clusters

This is a significant architectural change from the current batch-only approach.
Design it when the batch approach proves insufficient.

## External Validation

| System | Scale | Approach | Precision |
|---|---|---|---|
| Apple ODKE+ | 9M pages | Deterministic URL linking + ML entity linking | 98.8% |
| KGGen | Research papers | LLM clustering (full list) | 66% MINE |
| GraphRAG | Arbitrary | Exact name match only | (known gap) |
| LINK-KG | Medium | Type-specific prompt cache | 45% dedup improvement |
| Splink | 100M+ records | Fellegi-Sunter probabilistic | Production-grade |

## Activation Criteria

This plan activates when ALL of:
1. Plan 0025 Phase 4 proves value at 20-500 scale
2. A real use case requires >500 documents
3. LLM clustering approach demonstrably fails (context window, cost, or quality)

## References

- KGGen: https://github.com/stair-lab/kg-gen (clustering algorithm)
- LINK-KG: https://arxiv.org/abs/2510.26486 (type-specific prompt cache)
- Apple ODKE+: https://arxiv.org/abs/2509.04696 (production entity linking)
- sift-kg: https://github.com/juanceresa/sift-kg (KG-specific dedup with HITL)
- Splink: https://github.com/moj-analytical-services/splink (large-scale ER)
- pyJedAI: https://github.com/AI-team-UoA/pyJedAI (full ER pipeline)

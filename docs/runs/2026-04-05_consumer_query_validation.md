# Consumer Query Validation — Iran DIGIMON Graph

Date: 2026-04-05
Plan: `docs/plans/0071_consumer_value_validation_block.md`
Graph source: `var/iran_pipeline_run/` (63 entities, 62 relationships)
Graph file: `Digimon_for_KG_application/results/iran_disinformation/er_graph/nx_data.graphml`
Script: `scripts/digimon_query.py`

## Scoring Rubric

| Score | Meaning |
|-------|---------|
| 2 | Answer contains relevant entities + relationship context with source URLs |
| 1 | Answer contains relevant entities but no relationship structure |
| 0 | Answer returns irrelevant or empty results |

Threshold: mean score ≥ 1.0 → "sufficient for current phase"

## Q1: IRGC Influence Operations

Query: `"Iran Islamic Revolutionary Guard Corps influence operations and proxies"`

Results:
- 7 keyword-matched entities including IRGC, IRIB, Iran, CISA, NewsGuard, US Central Command
- 15 PPR-expanded nodes including Twitter, Instagram, Qassem Soleimani, Graphika, Russia, Treasury
- 37 relationships with descriptions and source URLs including:
  - Iran → US DoJ: IRGC cyber actors indicted for hack-and-leak, 2024 election (DOJ source)
  - Iran → IRIB: broadcaster inauthentic behavior (Graphika report)
  - Iran → Russia: Twitter data trove of Russian IRA + Iranian accounts
  - Iran → US Treasury: sanctions for election interference, 2020
  - IRGC: explicitly named and typed as `oc:government_organization` with primary source URL
- 37/37 relationships have source URLs

**Score: 2** — relevant entities + relationship context + provenance

## Q2: Iran Social Media Disinformation

Query: `"Iran disinformation campaigns targeting United States social media"`

Results:
- 5 keyword-matched entities (Iran, Twitter, Instagram, Facebook, IRIB)
- 15 PPR-expanded nodes overlapping heavily with Q1 (same graph neighborhood)
- 37 sourced relationships (identical to Q1 — Iran node is the hub)
- Key relationships: Facebook/Instagram account removals for CIB, coordinated narratives
- Specific operations named: "Unheard Voice," "Endless Mayfly" typosquatting campaign

**Score: 2** — same relationship subgraph, different keyword matches confirm different
entry points both navigate to the same well-sourced subgraph

## Q3: APT42 Cyber Operations

Query: `"APT42 cyber operations phishing Iran hacking"`

Results:
- 4 keyword-matched entities including APT42 (typed as `oc:program`, 2 source URLs)
- PPR-expanded: Charming Kitten as top neighbor (ppr=0.0718), correctly identified as related program
- 38 sourced relationships including:
  - Iran → US DoJ: IRGC hack-and-leak indictment (directly relevant to APT42's operation)
  - Iran → Kazemi/Kashian: cyber-enabled disinformation campaign charges
- APT42 and Charming Kitten correctly co-surface, showing the graph captured entity relationships
  between the two aliases/programs

**Score: 2** — APT42 entity directly matched, alias relationship surfaced via PPR, operations
linked to cyber-legal context with DOJ sources

## Summary

| Query | Score | Entities matched | Rels returned | Provenance |
|-------|-------|-----------------|---------------|------------|
| Q1: IRGC influence operations | 2 | 7 keyword + 15 PPR | 37 | 100% |
| Q2: Iran social media disinformation | 2 | 5 keyword + 15 PPR | 37 | 100% |
| Q3: APT42 cyber operations | 2 | 4 keyword + 15 PPR | 38 | 100% |
| **Mean** | **2.0** | — | — | **100%** |

Mean score 2.0 ≥ threshold 1.0. **Verdict: sufficient for current phase.**

## Observations

**What works well:**
1. Entity-level matching is accurate — IRGC, APT42, CISA all return with correct types and sources
2. PPR correctly surfaces related entities — Charming Kitten appears near APT42, Russia appears near Iran
3. Relationship descriptions are substantive (not just entity pairs) — each edge carries a
   text summary of the actual claim
4. 100% provenance — every relationship carries at least one source URL, most carry two
5. Source diversity — DOJ, Graphika, Atlantic Council, IranIntl, Google Cloud TI, CISA

**Limitations confirmed but not blocking:**
1. All edges use `shared:assertion` — the query cannot filter to "find only contract relationships"
   or "find only indictments." Currently an OSINT analyst reads the relationship description text.
2. Graph neighborhood is Iran-centric — Q1 and Q2 return the same subgraph because Iran is the hub.
   This reflects the actual investigation corpus, not a retrieval failure.
3. PPR returns the same top nodes across queries because the graph has one dominant connected
   component. Queries on less-connected entities would return smaller subgraphs.

**Thin semantics are sufficient for the current use case:**
- An analyst asking "tell me what you know about IRGC influence operations" receives relevant
  entities, substantive relationship descriptions, and primary sources to follow.
- The lack of typed predicates does not prevent useful answers — the text content of each
  edge is informative.
- Option A (predicate enrichment) remains the right enrichment path but is not urgent.

## Verdict

**Thin semantics are sufficient for the current phase.** The DIGIMON graph answers
real OSINT queries with relevant entities, sourced relationship descriptions, and full
provenance. The consumer value goal in the ROADMAP is satisfied at the current
investigation scale.

The "consumer is blocked" trigger for Option A was not met. Defer as documented in
`docs/assertion_semantics_evaluation.md`.

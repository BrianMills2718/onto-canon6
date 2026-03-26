# Consumer Integration Notes (2026-03-25)

Notes from cross-project strategic review for agents working on onto-canon6.

## First Consumer: research_v3

research_v3 (`~/projects/research_v3/`) produces `InvestigationMemo` with
`Finding` objects. Each Finding has:
- `claim`: str — factual assertion text
- `source_urls`: list[str] — provenance URLs
- `confidence`: float (0-1)
- `corroborated`: bool
- `tags`: list[str]

### Integration Path (simplest)

Feed each Finding.claim as evidence text through the extraction pipeline:
1. Create evidence record with source_url provenance
2. Run extraction on the claim text (canon6_commit_canonicalization or equivalent)
3. Map Finding.confidence → belief probability
4. Map Finding.corroborated → epistemic_level (observed/inferred)

onto-canon6's extraction pipeline handles entity extraction, SUMO typing,
and predicate canonicalization. The adapter does NOT need to do entity work.

### Integration Prerequisite (ROADMAP 2.0)

Feed 5 research_v3 findings into onto-canon6, verify:
- Entities extracted correctly from claim text
- Beliefs stored with correct provenance (source_urls)
- Confidence/epistemic_level mapped correctly

### Open Questions for Integration

1. **Bulk ingestion**: Can the governed review workflow handle 61 findings
   from one investigation without manual review of each? May need a
   trusted-source fast path (see Open Uncertainties in parity matrix).

2. **Confidence mapping**: research_v3 confidence (0-1 float) maps directly
   to onto-canon6 probability. But should low-confidence findings (< 0.3)
   be treated differently (e.g., skip promotion)?

3. **Tags → vocabulary**: research_v3 Finding.tags are free-text categories.
   Should these map to onto-canon6 domain pack concepts, or stay as metadata?

4. **Batch vs streaming**: Should the adapter feed all findings from one
   investigation as a batch (with cross-finding context), or one at a time?

## Second Consumer: DIGIMON (deferred)

DIGIMON adapter is deferred in the parity matrix. Build after research_v3
integration is proven. Key uncertainty: DIGIMON edge weights are TF-IDF
(can exceed 1.0), not probabilities. The adapter must define the mapping.

## Consumer-Ready MCP Surface Gap

Current 8-tool MCP surface is extraction/review focused. For agents to use
onto-canon6 as a queryable knowledge base, need at minimum:
- list/search entities
- get beliefs for entity
- add evidence (direct)

These are documented as deferred in the parity matrix.

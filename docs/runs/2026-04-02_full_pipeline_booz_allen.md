# Full Pipeline E2E: Booz Allen Lobbying Investigation

Date: 2026-04-02
Source: research_v3 graph.yaml (Booz Allen Hamilton lobbying, 2026-03-15)
Script: `scripts/full_pipeline_e2e.py`

## Pipeline

1. research_v3 graph.yaml → shared ClaimRecords (epistemic-contracts)
2. shared ClaimRecords → onto-canon6 CandidateAssertionImport
3. Submit to review pipeline (shared_import_permissive profile)
4. Accept all candidates
5. Promote to graph
6. Entity resolution (exact strategy)
7. Export to DIGIMON (entities.jsonl + relationships.jsonl)

## Results

| Metric | Count |
|--------|-------|
| Source claims | 123 |
| Candidates submitted | 123 |
| Candidates accepted | 123 |
| Candidates promoted | 123 |
| Promoted entities | 60 |
| Identity groups | 60 |
| Identities created | 60 |
| Aliases attached | 0 |
| DIGIMON entities | 60 |
| DIGIMON relationships | 123 |

## Key Observations

1. **All 123 claims flowed through** — zero data loss from research_v3 to DIGIMON
2. **60 unique entities** extracted from entity_refs in claims
3. **0 aliases** — exact-name resolution found no matches because each entity
   has a unique name in the corpus (no abbreviation/title variations)
4. **Validation status: needs_review** — shared_import_permissive profile
   correctly allows all imported claims through with soft violations only
5. **Entity IDs preserved**: `rv3:` prefix with FtM IDs (e.g., `rv3:cb462e9d6f6afe9f`)

## Artifacts

- Review DB: `var/full_pipeline_e2e/pipeline_review.sqlite3`
- Results JSON: `var/full_pipeline_e2e/pipeline_results.json`
- DIGIMON entities: `var/full_pipeline_e2e/entities.jsonl`
- DIGIMON relationships: `var/full_pipeline_e2e/relationships.jsonl`

## Claim Type Distribution

From the source graph.yaml:
- financial_claim (lobbying expenditures, contract values)
- relationship_claim (lobbying firms, government relationships)
- fact_claim (organizational structure, personnel)
- temporal_claim (date-bounded assertions)

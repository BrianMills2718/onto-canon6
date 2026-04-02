# 2026-04-02 Identity / External-Reference Browse Real Proof

## Purpose

Prove the Plan `0064` browse widening slice against a copy of a real promoted
DB.

## Source Artifact

Base promoted DB:
- `var/full_pipeline_e2e/pipeline_review.sqlite3`

Proof DB copy:
- `/tmp/onto-canon6-query-refs-proof.sqlite3`

Why a copy was required:
- the source DB is real promoted state, but `graph_external_references` had
  zero rows at the start of this proof
- Plan `0064` explicitly allows seeding identity/external-reference state on a
  copy so the browse/search contract can be proved honestly without pretending
  the source artifact already carried that state

## Selected Real Entity

Seed target from the real promoted DB:
- `rv3:acd3e2794e736cd1`
- display label: `Andrew Howell`
- entity type: `oc:person`

## Commands And Results

### 1. Copy the real promoted DB

```bash
cp var/full_pipeline_e2e/pipeline_review.sqlite3 /tmp/onto-canon6-query-refs-proof.sqlite3
```

### 2. Seed one identity on the copy

Executed through worktree code with `PYTHONPATH=src` and the repo `.venv`:

```text
create-identity-for-entity --entity-id rv3:acd3e2794e736cd1 --actor-id analyst:proof --display-label Andrew Howell --review-db-path /tmp/onto-canon6-query-refs-proof.sqlite3 --output json
```

Observed result:
- created identity `gid_b3ef63e10838e44dfb4e0693`
- canonical member remained `rv3:acd3e2794e736cd1`

### 3. Seed one attached and one unresolved external reference on the copy

```text
attach-external-ref --identity-id gid_b3ef63e10838e44dfb4e0693 --provider analyst_registry --external-id andrew-howell-profile --reference-label Andrew Howell --actor-id analyst:proof --review-db-path /tmp/onto-canon6-query-refs-proof.sqlite3 --output json
```

Result:
- `reference_status: attached`
- `provider: analyst_registry`
- `external_id: andrew-howell-profile`

```text
record-unresolved-external-ref --identity-id gid_b3ef63e10838e44dfb4e0693 --provider wikidata --unresolved-note "Need canonical Q-code for Andrew Howell" --actor-id analyst:proof --review-db-path /tmp/onto-canon6-query-refs-proof.sqlite3 --output json
```

Result:
- `reference_status: unresolved`
- `provider: wikidata`

### 4. Prove widened CLI browse/search behavior on the seeded real DB copy

```text
list-entities --provider analyst_registry --review-db-path /tmp/onto-canon6-query-refs-proof.sqlite3 --output json
```

Observed result:
- returned exactly `Andrew Howell`
- `attached_external_reference_count: 1`
- `unresolved_external_reference_count: 1`
- `external_reference_providers: ["analyst_registry", "wikidata"]`

```text
list-entities --reference-status unresolved --review-db-path /tmp/onto-canon6-query-refs-proof.sqlite3 --output json
```

Observed result:
- returned exactly `Andrew Howell`

```text
search-entities --query andrew-howell-profile --provider analyst_registry --review-db-path /tmp/onto-canon6-query-refs-proof.sqlite3 --output json
```

Observed result:
- returned exactly `Andrew Howell`
- `match_reason: external_id_exact`

### 5. Prove matching MCP behavior on the same seeded real DB copy

Python call over the worktree code:

```python
from onto_canon6 import mcp_server
mcp_server.canon6_search_entities(
    query="andrew-howell-profile",
    provider="analyst_registry",
    review_db_path="/tmp/onto-canon6-query-refs-proof.sqlite3",
)
```

Observed result:
- returned the same `Andrew Howell` entity
- `match_reason: external_id_exact`

## Conclusion

Plan `0064` is proved at the operational level:

1. entity browse can filter on external-reference provider;
2. entity browse can filter on attached/unresolved external-reference status;
3. entity search can match on attached external ids;
4. the widened summary fields remain truthful on a real promoted DB copy; and
5. the MCP layer mirrors the widened entity-search behavior.

## Caveat

This is a real promoted DB proof, but not a naturally occurring external-
reference proof. The external-reference rows were seeded on the copy because the
source artifact carried zero `graph_external_references` rows. The proof is
still valid for the query-surface contract, and the caveat should remain
explicit in all summaries.

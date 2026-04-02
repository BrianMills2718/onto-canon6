# Query Surface Real-Proof Verification

Date: 2026-03-31
Worktree: `codex/onto-canon6-integration-planning`
Plan: [0029_24h_query_surface_execution_block.md](../plans/0029_24h_query_surface_execution_block.md)

## Goal

Verify the first read-only query surface against the canonical local proof DB
on real promoted data, not only seeded test fixtures.

## Proof DB

The isolated worktree does not carry the heavy proof artifact under `var/`, so
Phase 4 used the canonical proof DB from the main repo checkout in read-only
fashion:

- `/home/brian/projects/onto-canon6/var/e2e_test_2026_03_25/review_combined.sqlite3`

This was safe because the new surface is read-only.

## Commands

The worktree implementation was exercised through the operator-facing CLI
entrypoint by calling `onto_canon6.cli.main()` under the worktree `src/`
binding:

```bash
PYTHONPATH=/home/brian/projects/.worktrees/onto-canon6-integration-planning/src \
python - <<'PY'
from onto_canon6 import cli
raise SystemExit(cli.main([
    "get-entity",
    "--entity-id", "ent:auto:9efd089a:oc_military_organization:ussocom",
    "--review-db-path", "/home/brian/projects/onto-canon6/var/e2e_test_2026_03_25/review_combined.sqlite3",
    "--output", "json",
]))
PY
```

```bash
PYTHONPATH=/home/brian/projects/.worktrees/onto-canon6-integration-planning/src \
python - <<'PY'
from onto_canon6 import cli
raise SystemExit(cli.main([
    "get-promoted-assertion",
    "--assertion-id", "gassert_c15127de58634b164b06dec0",
    "--review-db-path", "/home/brian/projects/onto-canon6/var/e2e_test_2026_03_25/review_combined.sqlite3",
    "--output", "json",
]))
PY
```

```bash
PYTHONPATH=/home/brian/projects/.worktrees/onto-canon6-integration-planning/src \
python - <<'PY'
from onto_canon6 import cli
raise SystemExit(cli.main([
    "get-evidence",
    "--assertion-id", "gassert_c15127de58634b164b06dec0",
    "--review-db-path", "/home/brian/projects/onto-canon6/var/e2e_test_2026_03_25/review_combined.sqlite3",
    "--output", "json",
]))
PY
```

## Verified Outcomes

### 1. Real entity/alias lookup

`get-entity` on canonical USSOCOM entity
`ent:auto:9efd089a:oc_military_organization:ussocom` returned:

- identity bundle `gid_c6476dce9dc695a18946e484`
- canonical membership:
  `ent:auto:9efd089a:oc_military_organization:ussocom`
- alias membership:
  `ent:auto:f82d1997:oc_military_organization:ussocom`
- 11 linked promoted assertions across the identity cluster

This proves the read surface can expose real alias-cluster state and aggregate
linked promoted assertions across the cluster.

### 2. Real promoted assertion lookup

`get-promoted-assertion` on
`gassert_c15127de58634b164b06dec0` returned:

- claim text:
  `Adm. Eric T. Olson held the role of Commander for USSOCOM.`
- predicate:
  `oc:hold_command_role`
- source candidate:
  `cand_0e373c3bfbc34658bcbdafdd`
- epistemic status:
  `active`
- source artifact ref:
  `var/real_runs/2026-03-21_phase_b_prompt_verification/chunks/01_stage1_query2/01_stage1_query2__chunk_002.md`

This proves the surface can resolve a real promoted assertion into promotion,
candidate, epistemic, and evidence-backed context.

### 3. Real evidence/provenance lookup

`get-evidence` on `gassert_c15127de58634b164b06dec0` returned:

- evidence spans:
  - `Adm. Eric T. Olson`
  - `Commander`
  - `USSOCOM`
- source artifact label:
  `01_stage1_query2__chunk_002.md`
- source artifact kind:
  `text_file`

This proves the surface can return the original promoted candidate, direct
evidence spans, and the source artifact payload on real data.

## Observed Constraints

1. The worktree-local `verify_setup.py` currently reports the proof DB missing,
   because worktrees do not automatically carry the heavy `var/` proof
   artifacts. Real-proof verification therefore needs an explicit proof DB
   path when run from lightweight worktrees.
2. The verified assertion had populated source artifact and evidence spans, but
   empty `artifact_links`, `artifacts`, and `lineage_edges`. That is not a
   query-surface failure; it reflects the stored provenance shape for this
   proof DB slice.
3. Exact search on `USSOCOM` returns both canonical and alias members because
   the observed labels are identical. The trustworthy identity proof for this
   slice is `get-entity`, not search-result ordering alone.

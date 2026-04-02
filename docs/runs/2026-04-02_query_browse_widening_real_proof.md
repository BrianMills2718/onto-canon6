# Query Browse Widening Real Proof

Date: 2026-04-02
Plan: `0063_24h_query_browse_widening_block.md`
Dataset: full Booz Allen pipeline artifact from `2026-04-02_full_pipeline_booz_allen.md`
Review DB: `/home/brian/projects/onto-canon6/var/full_pipeline_e2e/pipeline_review.sqlite3`

## Why This DB

The default config-backed review DB in `var/review_state.sqlite3` was not a
useful proof target for this block because it was empty at verification time.
The widened browse surface was therefore proved against the real promoted DB
already produced by the full `research_v3 -> onto-canon6 -> DIGIMON` pipeline
run on the Booz Allen lobbying investigation.

## Entry Point Note

For this worktree, the truthful reproducible command path was:

- `PYTHONPATH=src python - <<'PY' ... from onto_canon6 import cli; cli.main([...])`

The repo already records that `python -m onto_canon6.cli ...` can exit cleanly
without emitting the expected stdout artifact. The proof below therefore uses
explicit Python invocations of `cli.main([...])` in the worktree instead of the
module entrypoint.

## Proof 1: Entity Browse

Command:

```bash
PYTHONPATH=src python - <<'PY'
from io import StringIO
from contextlib import redirect_stdout
from onto_canon6 import cli
buf = StringIO()
with redirect_stdout(buf):
    code = cli.main([
        'list-entities',
        '--review-db-path','/home/brian/projects/onto-canon6/var/full_pipeline_e2e/pipeline_review.sqlite3',
        '--limit','5',
        '--output','json',
    ])
print('code', code)
print(buf.getvalue())
PY
```

Observed output excerpt:

```json
[
  {
    "display_label": "Akin Gump Strauss Hauer & Feld",
    "entity_id": "rv3:f16b059a44dcffb6",
    "entity_type": "oc:company",
    "identity_id": "gid_1afc462e5d9000dc766a1031",
    "linked_assertion_count": 6
  },
  {
    "display_label": "Andrew Howell",
    "entity_id": "rv3:acd3e2794e736cd1",
    "entity_type": "oc:person",
    "identity_id": "gid_b3ef63e10838e44dfb4e0693",
    "linked_assertion_count": 1
  },
  {
    "display_label": "Booz Allen Hamilton Holding Corporation",
    "entity_id": "rv3:cb462e9d6f6afe9f",
    "entity_type": "oc:company",
    "identity_id": "gid_263279148fcebb18b43f7257",
    "linked_assertion_count": 105
  }
]
```

What this proves:

1. the widened `list-entities` CLI works on real promoted state, not only on
   fixture DBs;
2. browse results expose identity ids, promoted entity ids, and linked
   assertion counts in deterministic order; and
3. the surface is immediately useful for operator/agent inspection of the
   promoted graph.

## Proof 2: Source-Centric Assertion Browse

Command:

```bash
PYTHONPATH=src python - <<'PY'
from io import StringIO
from contextlib import redirect_stdout
from onto_canon6 import cli
buf = StringIO()
with redirect_stdout(buf):
    code = cli.main([
        'list-promoted-assertions',
        '--review-db-path','/home/brian/projects/onto-canon6/var/full_pipeline_e2e/pipeline_review.sqlite3',
        '--source-ref','198e18e4f7351b2b',
        '--source-kind','research_v3_claim',
        '--limit','10',
        '--output','json',
    ])
print('code', code)
print(buf.getvalue())
PY
```

Observed output excerpt:

```json
[
  {
    "assertion_id": "gassert_564173a2d2fb9b6048fba350",
    "predicate": "shared:fact_claim",
    "source_candidate_id": "cand_ed4a0dc8c61b47a18276d71b",
    "source_kind": "research_v3_claim",
    "source_ref": "198e18e4f7351b2b"
  },
  {
    "assertion_id": "gassert_ccf4d40a6cb7611011615f89",
    "predicate": "shared:fact_claim",
    "source_candidate_id": "cand_dc80c2ead19b494ca11a7898",
    "source_kind": "research_v3_claim",
    "source_ref": "198e18e4f7351b2b"
  }
]
```

What this proves:

1. `list-promoted-assertions` is now query-surface-backed on real promoted
   data, not a separate raw graph read;
2. `source_ref` and `source_kind` work as first-class provenance entrypoints;
3. one source artifact can now be used to recover the exact promoted assertion
   subset it produced without raw SQLite inspection.

## Conclusion

Plan `0063` cleared its real-proof requirement. The widened browse surface now
works on:

1. service fixtures;
2. CLI integration tests;
3. MCP integration tests; and
4. the real Booz Allen promoted DB.

The next query-surface question should no longer be “does browse widening work
at all?” It should be one of the explicitly narrowed follow-ons documented in
Plan `0063` closeout:

1. identity/external-reference-aware browse and filters; or
2. first-class source-artifact query beyond source-centric assertion filters.

# Run: research_v3 memo -> onto-canon6 -> DIGIMON

Date: 2026-04-02
Plan: `0068`

## Goal

Prove the active-loop `research_v3` memo path end to end through shared
contracts and the governed `onto-canon6` review/promotion flow, with real
graph structure reaching DIGIMON.

## Input Artifact

- `~/projects/research_v3/output/20260323_082242_What_federal_contracts_has_Palantir_Tech/memo.yaml`

Baseline before this block:

- the same artifact previously promoted `61` assertions but produced `0`
  canonical entities and `0` DIGIMON rows because the completed memo did not
  persist resolved entities

## Command

```bash
cd ~/projects/research_v3
./.venv/bin/python loop.py \
  --enrich-entities output/20260323_082242_What_federal_contracts_has_Palantir_Tech/memo.yaml \
  --config config_loop_entity_backfill.yaml

cd ~/projects/onto-canon6
make pipeline-rv3-memo \
  INPUT=/home/brian/projects/research_v3/output/20260323_082242_What_federal_contracts_has_Palantir_Tech/memo.yaml
```

## Result

The run completed successfully and wrote:

- [pipeline_results.json](/home/brian/projects/onto-canon6/var/pipeline_memo_run/pipeline_results.json)
- [entities.jsonl](/home/brian/projects/onto-canon6/var/pipeline_memo_run/entities.jsonl)
- [relationships.jsonl](/home/brian/projects/onto-canon6/var/pipeline_memo_run/relationships.jsonl)

Summary:

- shared claims loaded: `61`
- candidates submitted: `61`
- candidates accepted: `61`
- candidates promoted: `61`
- entities scanned for resolution: `40`
- identity groups: `40`
- identities created: `40`
- DIGIMON entities exported: `40`
- DIGIMON relationships exported: `61`

## Concern Encountered

The first live enrichment attempt on the existing memo artifact failed with a
real Gemini quota error (`429 RESOURCE_EXHAUSTED`). The proof therefore used
`research_v3/config_loop_entity_backfill.yaml` to switch the enrichment call to
`claude-sonnet-4-6` for this backfill run.

## Interpretation

This closes the first semantic-value gap for the memo path:

- `research_v3` can now export active-loop memo findings through shared
  contracts
- existing completed memos can be repaired in place through
  `loop.py --enrich-entities`
- `onto-canon6` can import, review, accept, promote, resolve, and export the
  real memo artifact as a non-empty DIGIMON graph

This does **not** fully close end-goal consumer adoption:

- the exported relation semantics are still generic `shared:assertion` edges
  derived from memo entity refs, not graph-native typed relations
- this proof used an explicit model override during backfill because the
  default Gemini entity-resolution call hit quota
- a fresh live investigation still needs to be rerun end to end under the
  landed final-memo persistence logic

## Decision

Treat the memo path as value-producing but not yet fully hardened.

The next implementation step should prove a fresh live investigation under the
default runtime and then decide whether memo exports should remain thin
entity-ref transport or grow richer relation semantics.

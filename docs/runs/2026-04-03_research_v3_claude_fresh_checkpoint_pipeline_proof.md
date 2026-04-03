# Run: research_v3 fresh Claude checkpoint -> onto-canon6 -> DIGIMON

Date: 2026-04-03
Plan: `0069`

## Goal

Prove that a fresh live `research_v3` memo artifact can produce graph value
through `onto-canon6` under a non-Gemini runtime, without any post-hoc
entity-enrichment repair step.

## Input Artifact

- live run directory:
  `~/projects/research_v3/output/20260403_062500_palantir_claude_fresh/`
- proof snapshot:
  `~/projects/research_v3/output/20260403_062500_palantir_claude_fresh/memo.proof_0069_round4.yaml`

## Commands

```bash
cd ~/projects/research_v3
./.venv/bin/python loop.py \
  "What federal contracts has Palantir Technologies been awarded in the last 2 years, and which agencies awarded them?" \
  --config config_loop_claude_runtime.yaml

cp output/20260403_062500_palantir_claude_fresh/memo.yaml \
  output/20260403_062500_palantir_claude_fresh/memo.proof_0069_round4.yaml

cd ~/projects/onto-canon6
make pipeline-rv3-memo \
  INPUT=/home/brian/projects/research_v3/output/20260403_062500_palantir_claude_fresh/memo.proof_0069_round4.yaml
```

## Fresh Live Memo Checkpoint

The stable round-4 live checkpoint already contained:

- round number: `4`
- findings: `34`
- persisted entities: `34`
- total observed cost: `$0.158579`
- reflect confidence: `0.35`

`load_memo_claims()` on the snapshot exported:

- shared claims: `34`
- claims with non-empty `entity_refs`: `30`

## Downstream Result

`make pipeline-rv3-memo` on the snapshot produced:

- shared claims loaded: `34`
- candidates submitted: `34`
- candidates accepted: `34`
- candidates promoted: `34`
- entities scanned for resolution: `34`
- identity groups: `34`
- identities created: `34`
- DIGIMON entities exported: `34`
- DIGIMON relationships exported: `30`

Artifacts:

- [pipeline_results.json](/home/brian/projects/onto-canon6/var/pipeline_memo_run/pipeline_results.json)
- [entities.jsonl](/home/brian/projects/onto-canon6/var/pipeline_memo_run/entities.jsonl)
- [relationships.jsonl](/home/brian/projects/onto-canon6/var/pipeline_memo_run/relationships.jsonl)

## Interpretation

This closes the fresh-live memo proof gap under a different model runtime:

- fresh live memo artifacts can now persist entities without repair
- the shared-contract export carries enough structure for downstream graph
  promotion
- `onto-canon6` can turn that fresh memo snapshot into a non-empty DIGIMON
  graph

This does **not** close all remaining runtime/product questions:

- the proof artifact is a stable live checkpoint snapshot, not a completed
  final report, because the loop continued under low confidence
- the Claude runtime is operationally slower than the earlier repaired memo
  path
- the relation layer is still generic `shared:assertion` transport, not
  graph-native relation typing

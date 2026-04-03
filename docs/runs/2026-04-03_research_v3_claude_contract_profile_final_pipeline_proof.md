# Run: research_v3 contract-profile final memo -> onto-canon6 -> DIGIMON

Date: 2026-04-03
Plan: `0070`

## Goal

Prove that a fresh live `research_v3` contract investigation can stop
naturally on graph readiness under the promoted Claude contract profile and
still produce a non-empty downstream graph through `onto-canon6`.

## Input Artifact

- run directory:
  `~/projects/research_v3/output/20260403_134331_What_federal_contracts_has_Palantir_Tech/`
- final memo:
  `~/projects/research_v3/output/20260403_134331_What_federal_contracts_has_Palantir_Tech/memo.yaml`
- final report:
  `~/projects/research_v3/output/20260403_134331_What_federal_contracts_has_Palantir_Tech/report.md`

## Commands

```bash
cd ~/projects/research_v3
./.venv/bin/python loop.py \
  "What federal contracts has Palantir Technologies been awarded in the last 2 years, and which agencies awarded them?" \
  --config config_loop_claude_runtime.yaml

cd ~/projects/onto-canon6
make pipeline-rv3-memo \
  INPUT=/home/brian/projects/research_v3/output/20260403_134331_What_federal_contracts_has_Palantir_Tech/memo.yaml
```

## Live Result

The fresh run completed normally with final artifacts:

- rounds: `3`
- findings: `23`
- searches: `22/22`
- pages: `52/53`
- total observed cost: `$0.14`
- final memo graph metrics:
  - findings: `23`
  - sourced findings: `23`
  - corroborated findings: `13`
  - entities: `28`
  - entity-backed findings: `23`

Reflect still wanted to continue at `32%` confidence, but the run stopped on
the explicit graph-value gate once the memo was already export-ready.

## Downstream Result

`make pipeline-rv3-memo` on the final memo produced:

- shared claims loaded: `23`
- candidates submitted: `23`
- candidates accepted: `23`
- candidates promoted: `23`
- entities scanned for resolution: `28`
- identity groups: `28`
- identities created: `28`
- DIGIMON entities exported: `28`
- DIGIMON relationships exported: `23`

Artifacts:

- [memo.yaml](/home/brian/projects/research_v3/output/20260403_134331_What_federal_contracts_has_Palantir_Tech/memo.yaml)
- [report.md](/home/brian/projects/research_v3/output/20260403_134331_What_federal_contracts_has_Palantir_Tech/report.md)
- [pipeline_results.json](/home/brian/projects/onto-canon6/var/pipeline_memo_run/pipeline_results.json)

## Interpretation

This closes the stop-policy and runtime-promotion uncertainty for
contract-style investigations:

- the promoted Claude contract profile now produces a fresh final memo and
  final report, not only a proof checkpoint
- the loop can stop on graph readiness even when confidence is still below the
  generic deep-research stop threshold
- the final memo still produces governed graph state and a non-empty DIGIMON
  export downstream

Residual concern:

- the memo transport remains semantically thin because downstream edges are
  still generic `shared:assertion` relationships rather than graph-native
  relation typing

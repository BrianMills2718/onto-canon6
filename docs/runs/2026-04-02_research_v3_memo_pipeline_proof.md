# Run: research_v3 memo -> onto-canon6 -> DIGIMON

Date: 2026-04-02
Plan: `0067`

## Goal

Prove the active-loop `research_v3` memo path end to end through shared
contracts and the governed `onto-canon6` review/promotion flow.

## Input Artifact

- `~/projects/research_v3/output/20260323_082242_What_federal_contracts_has_Palantir_Tech/memo.yaml`

## Command

```bash
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
- entities scanned for resolution: `0`
- identity groups: `0`
- identities created: `0`
- DIGIMON entities exported: `0`
- DIGIMON relationships exported: `0`

## Interpretation

This closes the transport and reproducibility gap for the memo path:

- `research_v3` can now export active-loop memo findings through shared
  contracts
- `onto-canon6` can import, review, accept, and promote them without hidden
  workstation assumptions
- the one-command memo path is now real (`make pipeline-rv3-memo`)

This does **not** close the end-goal consumer-value gap:

- the memo-derived `ClaimRecord`s still arrive as free-text assertions
- the current shared-claim import path does not recover canonical entities or
  role fillers from those claims
- DIGIMON therefore receives an empty graph from this run

## Decision

Do not treat memo-path consumer adoption as complete.

The next implementation step must add structured entity / role information to
the active-loop export path, or add an explicit downstream extraction stage
before DIGIMON export.

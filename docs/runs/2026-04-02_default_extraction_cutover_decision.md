# 2026-04-02 Default Extraction Cutover Decision

## Decision

Plan `0062` is complete and truthful. The proved compact operational-parity
lane is now the repo-default extraction surface.

## What Changed

Default extraction config now points to:

1. `selection_task: budget_extraction`
2. `prompt_template: prompts/extraction/text_to_candidate_assertions_compact_v5.yaml`
3. `prompt_ref: onto_canon6.extraction.text_to_candidate_assertions_compact_v5@3`

Verification:

1. targeted config/pipeline tests passed after the default cutover; and
2. a fresh no-override live rerun proved the repo-default path still holds the
   current transfer posture.

Artifacts:

- `var/real_runs/2026-04-02_default_extraction_cutover/outputs/chunk_002_extract.json`
- `var/real_runs/2026-04-02_default_extraction_cutover/outputs/chunk_003_extract.json`
- `var/real_runs/2026-04-02_default_extraction_cutover/outputs/chunk_002_transfer_report.json`
- `var/real_runs/2026-04-02_default_extraction_cutover/outputs/chunk_003_transfer_report.json`

Results:

1. chunk `002` remained positive under the no-override default path;
2. chunk `003` remained free of accepted spillover under the no-override
   default path; and
3. the exact candidate mix changed slightly from the override-based proof, but
   the transfer verdicts did not regress.

## Conclusion

The compact operational-parity candidate is no longer only a proved
experimental lane. It is now the repo-default extraction surface.

No active chunk-transfer cleanup block remains under Plan `0014`. Future
extraction-quality work should start from this promoted default rather than
reopening the previous transfer-hardening chain.

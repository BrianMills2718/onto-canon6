# Chunk-017 Contract Cutover Decision

Date: 2026-04-02
Plan: `0055_24h_chunk017_contract_cutover_and_rebaseline_block.md`

## Decision

The approved chunk-017 contract cutover is now implemented.

1. `psyop_017_full_chunk003_analytical_context_strict_omit` has been removed
   from the strict-omit benchmark fixture.
2. the fixture is now `psyop_eval_slice_v6`.
3. the authoritative negative controls for this family are now the cleaner
   local cases `008` through `016`.

## Corrected-Fixture Rerun

Command used:

```bash
PYTHONPATH=src /home/brian/projects/onto-canon6/.venv/bin/python -m onto_canon6 \
  run-extraction-prompt-experiment \
  --case-limit 16 \
  --n-runs 1 \
  --comparison-method none \
  --selection-task budget_extraction \
  --output json \
  > docs/runs/2026-04-02_chunk017_cutover_prompt_eval_report.json
```

Primary artifact:

- `docs/runs/2026-04-02_chunk017_cutover_prompt_eval_report.json`

Aggregate means on the corrected fixture:

1. `baseline = 0.2791625`
2. `compact = 0.8484375`
3. `compact_operational_parity = 0.8416625`
4. `hardened = 0.5604125`
5. `single_response_hardened = 0.6072875`

All variants completed with `n_errors = 0`.

## What Changed

The cutover removed a benchmark-contract distortion, but it did not rescue the
compact operational-parity lane.

What is now clean:

1. strict-omit controls `005`, `006`, and `009` through `016` all scored `1.0`
   under `compact_operational_parity`;
2. the repo no longer depends on a mixed-content full-chunk zero-output case to
   define this failure family;
3. the corrected benchmark surface is structurally stable (`n_errors = 0`).

What still fails under `compact_operational_parity`:

1. `psyop_001_designation_change` — score `0.5166`
2. `psyop_002_concerns_about_truth_based_shift` — score `0.35`
3. `psyop_007_named_institutional_concern` — score `0.35`
4. `psyop_008_jpotf_establishment_not_org_form` — score `0.25`

The most important residual facts are:

1. `compact_operational_parity` still emits an incorrect
   `oc:create_organizational_unit` candidate on case `008`;
2. `compact_operational_parity` still under-specifies or over-extracts the
   positive concern/designation cases `001`, `002`, and `007`;
3. `compact_operational_parity` still trails `compact` overall on the corrected
   fixture, so the lane remains non-promotable.

## Conclusion

The next blocker is no longer "what should chunk 017 mean?" The next blocker is
a narrower semantic recovery family over cases `001`, `002`, `007`, and `008`
on the corrected fixture.

That work is activated as:

- `docs/plans/0056_24h_corrected_fixture_semantic_recovery_block.md`

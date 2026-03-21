# Extraction Experiment Runbook

This note captures the smallest live extraction-prompt workflow that is useful
for `onto-canon6` right now.

## Purpose

Use the shared `llm_client` and `prompt_eval` stack to run a bounded live
extraction prompt experiment, then inspect the active-call view while it is in
flight.

This is the right path when you want to answer:

1. is the extraction experiment actually still running,
2. which prompt variant is active right now,
3. which model/task/prompt_ref is in flight,
4. did the process die locally or is it still alive.

## Environment

Inside the project `.venv`, keep both shared libraries installed editable:

```bash
cd ~/projects/onto-canon6
./.venv/bin/pip install -e ~/projects/llm_client
./.venv/bin/pip install -e ~/projects/prompt_eval
```

## Recommended Live Slice

Use a bounded one-case run first, but give bootstrap enough scored trials to
compare variants honestly.

```bash
cd ~/projects/onto-canon6
env \
  LLM_CLIENT_PROJECT=onto-canon6-extraction-sweep \
  LLM_CLIENT_TIMEOUT_POLICY=ban \
  ./.venv/bin/python -m onto_canon6 run-extraction-prompt-experiment \
  --case-limit 1 \
  --n-runs 2 \
  --comparison-method bootstrap \
  --selection-task budget_extraction \
  --output json
```

Why these defaults:

1. `LLM_CLIENT_TIMEOUT_POLICY=ban` keeps provider wall-clock timeouts from
   killing a slow-but-healthy call.
2. `LLM_CLIENT_PROJECT=...` gives the run an isolated observability filter.
3. `--case-limit 1 --n-runs 2` is the smallest shape that still gives the
   SciPy bootstrap comparison path two scored trials per variant.
4. `--selection-task budget_extraction` is the current viable prompt-eval lane
   on the tiny PSYOP slice. `fast_extraction` remains useful for operational
   extraction, but it has been much slower and less practical for prompt
   iteration on this slice.
5. `--comparison-method bootstrap` avoids Welch assumptions when live failures
   leave just enough scored trials to compare.

If you only want a smoke test of liveness rather than a real comparison, you
can still use `--n-runs 1`, but `onto-canon6` will now fail loudly if you ask
for a bootstrap or Welch comparison with too few planned scored trials.

## Bounded Real-Chunk Prompt Verification

If you want to test a candidate extraction prompt on the real operational path
without mutating the repo-wide live extraction default, use `extract-text`
with an explicit prompt override pair.

Important constraint:

1. prompt-eval templates are experiment assets and are not automatically
   extraction-compatible;
2. the live extraction path passes `source_text` and related source metadata,
   while the prompt-eval harness passes its own experiment input variables; and
3. bounded operational checks therefore need an extraction-compatible prompt
   asset plus an explicit `prompt_ref`.

Current working example:

```bash
cd ~/projects/onto-canon6
env \
  LLM_CLIENT_PROJECT=onto-canon6-compact2-real-chunk-max10 \
  LLM_CLIENT_TIMEOUT_POLICY=ban \
  ./.venv/bin/python -m onto_canon6 extract-text \
  --input var/real_runs/2026-03-21_phase_b_prompt_verification/chunks/01_stage1_query2/01_stage1_query2__chunk_002.md \
  --profile-id psyop_seed \
  --profile-version 0.1.0 \
  --submitted-by analyst:compact2-run \
  --review-db-path var/real_runs/2026-03-21_compact2_real_chunk_verification/review_state_max10.sqlite3 \
  --overlay-root var/real_runs/2026-03-21_compact2_real_chunk_verification/overlays_max10 \
  --selection-task budget_extraction \
  --prompt-template prompts/extraction/text_to_candidate_assertions_compact_v2.yaml \
  --prompt-ref onto_canon6.extraction.text_to_candidate_assertions_compact_v2@1 \
  --max-candidates-per-call 10 \
  --max-evidence-spans-per-candidate 1 \
  --output json
```

Use this path when you need to answer:

1. does the prompt variant still behave on the real extraction service,
2. does it stay structurally valid outside the prompt-eval harness, and
3. is it strong enough on a real chunk to justify broader verification or
   promotion into the repo default.

## Active-Call Query

In a second shell, inspect the active-call state while the command runs:

```bash
cd ~/projects/onto-canon6
./.venv/bin/python - <<'PY'
from pprint import pprint
from llm_client import get_active_llm_calls

pprint(get_active_llm_calls(project="onto-canon6-extraction-sweep", limit=20))
PY
```

For current non-streaming structured extraction calls, the expected truthful
state is usually:

- `activity_state="waiting"`
- `progress_observable=False`
- `process_alive=True` while the process is still running

That means the call is still live, but the provider path does not expose real
progress signals. This is not the same thing as a hang.

## Interpreting Results

### Healthy long-running opaque call

- `phase` moves from `started` to `heartbeat`
- `activity_state="waiting"`
- `process_alive=True`
- `prompt_ref`, `task`, and `requested_model_id` are populated

### Local process interrupted or dead

- the run disappears from `get_active_llm_calls(...)`
- same-host orphaned rows should not linger as active after a local interrupt

### Quality failure, not liveness failure

Typical current prompt-experiment failures are structural, for example:

- candidates with `roles: {}`
- candidates whose role fillers are not wrapped in role arrays
- `kind: value` fillers missing `value_kind`
- schema-invalid candidate payloads
- multiple tool-call envelopes when the prompt should return one `candidates`
  array
- zero scored trials after all variants fail deterministically

Those are extraction-quality problems. They should be fixed in prompt/config or
evaluation logic, not by adding more timeout machinery.

## Current Limits

1. Opaque non-streaming structured calls do not expose truthful progress
   events, so they stay in `waiting` rather than `progressing`.
2. The active-call query is most useful when filtered by `project=...`; the
   shared observability database may contain unrelated live calls from other
   repos.
3. This runbook does not replace the benchmark/evaluation docs. It is only the
   shortest operational path for a real live prompt-experiment check.

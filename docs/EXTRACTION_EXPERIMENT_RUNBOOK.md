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

Use a bounded one-case run first.

```bash
cd ~/projects/onto-canon6
env \
  LLM_CLIENT_PROJECT=onto-canon6-extraction-sweep \
  LLM_CLIENT_TIMEOUT_POLICY=ban \
  ./.venv/bin/python -m onto_canon6 run-extraction-prompt-experiment \
  --case-limit 1 \
  --n-runs 1 \
  --comparison-method bootstrap \
  --selection-task fast_extraction \
  --output json
```

Why these defaults:

1. `LLM_CLIENT_TIMEOUT_POLICY=ban` keeps provider wall-clock timeouts from
   killing a slow-but-healthy call.
2. `LLM_CLIENT_PROJECT=...` gives the run an isolated observability filter.
3. `--case-limit 1 --n-runs 1` keeps cost and latency bounded while still
   surfacing structural extraction failures.
4. `--comparison-method bootstrap` avoids Welch assumptions when live failures
   leave too few scored trials.

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
- schema-invalid candidate payloads
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

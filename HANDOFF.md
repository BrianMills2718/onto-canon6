# Handoff: onto-canon6 — 2026-04-03 (session 7)

## Current State

- Plan `0070` is complete
- `research_v3` now has a config-driven graph-value stop gate
- `config_loop_claude_runtime.yaml` is now the promoted runtime profile for
  contract-style investigations
- fresh live Palantir contract-profile proof is complete:
  final run with `3` rounds, `23` findings, `28` persisted entities, and cost
  `$0.14`
- `onto-canon6` consumer proof on that final memo is complete:
  `23` shared claims -> `23` promoted assertions -> `28` canonical entities ->
  `23` DIGIMON relationships

## What Was Done This Session

### 1. Opened and executed Plan `0070`
- added:
  `docs/plans/0070_24h_graph_value_stop_gate.md`
- added progress anchor:
  `var/progress/0070_graph_value_stop_gate.md`
- updated `CLAUDE.md`, `docs/plans/CLAUDE.md`, and `TODO.md`

### 2. Landed graph-value stop gating in `research_v3`
- `shared_export.py`
  now computes export-aligned memo graph metrics
- `loop.py`
  now stops contract-style runs on explicit graph readiness when enabled by
  profile
- `research_v3/config_manager.py`
  now ships graph-value gate defaults with the gate off by default
- `config_loop_claude_runtime.yaml`
  now enables the stop gate and is documented as the promoted contract profile
- added deterministic tests covering:
  - graph-value metrics
  - gate-enabled vs gate-disabled stop behavior
  - full loop stop-on-graph-readiness flow

### 3. Re-verified both repos before the fresh proof
- `research_v3` targeted gate tests:
  `40 passed`
- `research_v3` full suite:
  `251 passed, 3 skipped, 1 warning`
- `onto-canon6` memo-import + cross-project integration tests:
  `7 passed`

### 4. Proved the fresh live contract-profile path
- ran the Palantir federal-contracts question under
  `config_loop_claude_runtime.yaml`
- wrote a fresh run directory:
  `research_v3/output/20260403_134331_What_federal_contracts_has_Palantir_Tech/`
- the completed run stopped naturally at round `3` even though reflect still
  wanted to continue at `32%` confidence
- stop reason:
  graph-value gate met (`23` findings, `23` sourced, `13` corroborated,
  `28` entities, `23` entity-backed findings)
- final artifacts written by the run itself:
  `memo.yaml` and `report.md`

### 5. Proved the consumer path on the final memo
- `load_memo_claims()` on the final memo exported:
  - `23` shared claims
  - `23` claims with non-empty `entity_refs`
- `make pipeline-rv3-memo INPUT=.../memo.yaml` produced:
  - `23` promoted assertions
  - `28` canonical entities
  - `23` DIGIMON relationships

## Verification

- `research_v3` targeted gate tests:
  `40 passed`
- `research_v3` full suite:
  `251 passed, 3 skipped, 1 warning`
- fresh live final memo:
  `3` rounds, `23` findings, `28` entities, final `report.md` written
- downstream pipeline proof:
  `23` promoted assertions, `28` entities, `23` relationships

## Highest-Signal Finding

The runtime/stop-policy uncertainty is closed.

The promoted Claude contract profile now does three things on a fresh live run:

- persists entities directly into the final memo
- stops naturally once the memo is already downstream-graph-ready
- writes final memo/report artifacts that flow through `onto-canon6` into a
  non-empty DIGIMON graph

## Known Concerns / Uncertainties

### Runtime tradeoff
- the Claude contract profile is still operationally slower than the raw
  Gemini-default path
- the fresh final proof cost remained low (`$0.14`), but wall-clock latency is
  still noticeable because search, corroboration, entity resolution, report,
  and leads all route through Claude

### Runtime decision is now closed
- `config_loop_claude_runtime.yaml` is now the promoted runtime profile for
  contract-style investigations
- graph-value stopping is now the accepted stop policy for that profile
- repo-default depth-biased behavior remains unchanged outside that profile

### FARA live tests remain external-network sensitive
- the final `research_v3` suite passed only after broadening the FARA skip
  policy from just upstream `5xx` to the full `httpx.RequestError` family
- this is still the same external-outage class, not a regression in the loop
  or memo-export path

### Memo relation semantics are still thin
- the fresh memo path now yields a non-empty DIGIMON graph through final
  artifacts, not just checkpoints
- relationship labels remain generic `shared:assertion` edges derived from
  memo entity refs, not graph-native typed relations

## Next Phases

1. Decide whether the memo path should stay thin or emit richer relation
   semantics before claiming broader consumer adoption
2. Prove richer relation semantics only if they materially improve a real
   consumer outcome
3. Revisit broader consumer adoption after the semantic seam is honest

## Authority Chain

| Document | Governs |
|----------|---------|
| `CLAUDE.md` | Strategic direction + execution policy |
| `docs/plans/0070_24h_graph_value_stop_gate.md` | Completed 24h block and verification record |
| `docs/ROADMAP.md` | Forward-looking priorities |
| `docs/STATUS.md` | What is and isn't proven |
| `docs/plans/CLAUDE.md` | Plan index |
| `KNOWLEDGE.md` | Cross-agent runtime findings |

# Handoff: onto-canon6 — 2026-04-03 (session 6)

## Current State

- Plan `0069` is complete
- `research_v3` now supports `loop.py --config` for fresh and resumed runs
- `research_v3` now ships a dedicated proof profile:
  `config_loop_claude_runtime.yaml`
- `research_v3` package metadata now declares `open-web-retrieval`
- fresh live Palantir memo checkpoint proof is complete:
  round-4 snapshot with `34` findings, `34` persisted entities, and cost
  `$0.158579`
- `onto-canon6` consumer proof on that snapshot is complete:
  `34` shared claims -> `34` promoted assertions -> `34` canonical entities ->
  `30` DIGIMON relationships

## What Was Done This Session

### 1. Opened and executed Plan `0069`
- added:
  `docs/plans/0069_24h_non_gemini_fresh_memo_proof.md`
- added progress anchor:
  `var/progress/0069_non_gemini_fresh_proof.md`
- updated `CLAUDE.md`, `docs/plans/CLAUDE.md`, and `TODO.md`

### 2. Landed non-Gemini fresh-run support in `research_v3`
- `loop.py`
  now accepts `config_path` for fresh and resumed runs
- `loop.py --config`
  now applies to live investigations, not just `--enrich-entities`
- added:
  `config_loop_claude_runtime.yaml`
- added targeted tests covering:
  - config override plumbing
  - CLI forwarding for fresh runs

### 3. Fixed runtime packaging drift
- the fresh live proof initially failed because the local `research_v3` `.venv`
  did not have `open_web_retrieval`
- root cause: `research_v3/pyproject.toml` had not declared
  `open-web-retrieval`
- fixed by adding the dependency and verifying:
  `./.venv/bin/python -m pip install -e .`

### 4. Proved the fresh live memo path under a different model
- ran the Palantir federal-contracts question under
  `config_loop_claude_runtime.yaml`
- wrote a fresh run directory:
  `research_v3/output/20260403_062500_palantir_claude_fresh/`
- the live checkpoint at round 4 already contained:
  - `34` findings
  - `34` persisted entities
  - cost `$0.158579`
  - confidence `0.35`
- froze the proof artifact as:
  `memo.proof_0069_round4.yaml`

### 5. Proved the consumer path on the fresh checkpoint
- `load_memo_claims()` on the snapshot exported:
  - `34` shared claims
  - `30` claims with non-empty `entity_refs`
- `make pipeline-rv3-memo INPUT=.../memo.proof_0069_round4.yaml` produced:
  - `34` promoted assertions
  - `34` canonical entities
  - `30` DIGIMON relationships

## Verification

- `research_v3` targeted loop tests:
  `19 passed`
- `research_v3` full suite:
  `247 passed, 2 skipped, 1 warning`
- `research_v3` editable install from `pyproject.toml`:
  succeeded
- fresh live memo checkpoint:
  round 4, `34` findings, `34` entities, no repair step
- downstream pipeline proof:
  `34` promoted assertions, `34` entities, `30` relationships

## Highest-Signal Finding

Using a different model solved the freshness problem.

The fresh live memo path no longer depends on post-hoc enrichment:

- a brand-new Palantir run under the Claude runtime profile persisted entities
  directly into the memo checkpoint
- that fresh memo snapshot flowed through `onto-canon6` into a non-empty
  DIGIMON graph

The remaining gap is not "can a fresh memo work?" It is:

- should the Claude runtime profile be promoted beyond proof use, and
- should the loop stop earlier on contract-style investigations once graph
  value is already present

## Known Concerns / Uncertainties

### Fresh proof artifact is a stable checkpoint snapshot
- the live run kept extending because reflect confidence remained `0.35`
- the proof uses the stable round-4 memo snapshot
  `memo.proof_0069_round4.yaml`
  rather than a completed final report
- this is truthful and sufficient for the consumer proof because
  `onto-canon6` imports `memo.yaml`, not `report.md`

### Runtime tradeoff
- the Claude runtime path is operationally slower than the earlier repaired
  memo proof, even though the observed checkpoint cost remained low
- that tradeoff is now real evidence, not speculation

### FARA live tests remain external-network sensitive
- the final `research_v3` suite passed only after broadening the FARA skip
  policy from just upstream `5xx` to the full `httpx.RequestError` family
- this is still the same external-outage class, not a regression in the loop
  or memo-export path

### Memo relation semantics are still thin
- the fresh memo path now yields a non-empty DIGIMON graph
- relationship labels remain generic `shared:assertion` edges derived from
  memo entity refs, not graph-native typed relations

## Next Phases

1. Decide whether `config_loop_claude_runtime.yaml` should stay proof-only or
   become the promoted runtime for contract investigations
2. Tighten loop stop behavior so a proof-worthy contract memo does not keep
   extending after graph value is already present
3. Decide whether the memo path should stay thin or emit richer relation
   semantics before claiming broader consumer adoption

## Authority Chain

| Document | Governs |
|----------|---------|
| `CLAUDE.md` | Strategic direction + execution policy |
| `docs/plans/0069_24h_non_gemini_fresh_memo_proof.md` | Completed 24h block and verification record |
| `docs/ROADMAP.md` | Forward-looking priorities |
| `docs/STATUS.md` | What is and isn't proven |
| `docs/plans/CLAUDE.md` | Plan index |
| `KNOWLEDGE.md` | Cross-agent runtime findings |

# Handoff: onto-canon6 — 2026-04-02 (session 4)

## Current State

- `onto-canon6` full suite passes locally: `562` collected tests, `0` failures
- Active authority block: Plan `0067`
- `research_v3` now exports active-loop memo findings through shared contracts
  via `load_memo_claims()` / `load_memo_sources()`
- `full_pipeline_e2e.py` now supports explicit `--memo`, fails loud, and no
  longer depends on hidden workstation defaults for the memo path
- Real Palantir memo proof is recorded:
  `61` findings -> `61` candidates submitted -> `61` accepted -> `61`
  promoted -> `0` canonical entities -> `0` DIGIMON rows
- Graph-backed consumer proofs remain healthy:
  - Booz Allen: `123` claims -> `60` entities + `123` relationships
  - Anduril: `22` claims -> `17` entities + `22` relationships

## What Was Done This Session

### 1. Plan / execution authority
- Added Plan `0067`:
  `docs/plans/0067_24h_end_goal_convergence_block.md`
- Added progress anchor:
  `var/progress/0067_end_goal_convergence.md`
- Updated `CLAUDE.md`, `docs/plans/CLAUDE.md`, and `TODO.md`
- Strengthened the execution policy in `CLAUDE.md` so that:
  - stopping early is explicitly treated as failure
  - plan completion is not a stop condition
  - one green test is not a stop condition
  - one commit is not a stop condition

### 2. Shared-contract memo export
- `research_v3/shared_export.py`
  now provides:
  - `load_memo_claims(memo_path)`
  - `load_memo_sources(memo_path)`
- Added deterministic ids for memo-derived claims/sources
- Added targeted tests in
  `research_v3/tests/test_shared_export.py`

### 3. Pipeline reproducibility / fail-loud cleanup
- `scripts/full_pipeline_e2e.py` now:
  - supports `--memo`
  - requires exactly one explicit input (`--graph`, `--memo`, or `--handoff`)
  - removes the hidden default Booz Allen fallback
  - resolves sibling repo roots explicitly instead of assuming one workstation path
  - fails loud on accept/promote failures
- `Makefile` now:
  - runs the real full suite from `make test`
  - adds `make pipeline-rv3-memo INPUT=...`

### 4. Verification
- Green targeted tests:
  - `research_v3/tests/test_shared_export.py`
  - `onto-canon6/tests/integration/test_cli_research_v3_import.py`
  - `onto-canon6/tests/adapters/test_research_v3_import.py`
  - `onto-canon6/tests/adapters/test_research_v3_memo_import.py`
- Green full suite:
  - `cd ~/projects/onto-canon6 && ./.venv/bin/python -m pytest -q`
- Real proof:
  - `cd ~/projects/onto-canon6 && make pipeline-rv3-memo INPUT=/home/brian/projects/research_v3/output/20260323_082242_What_federal_contracts_has_Palantir_Tech/memo.yaml`
- `research_v3` broad suite needed one stabilization:
  live DOJ FARA endpoint returned HTTP `500`; `tests/test_tools.py::test_search_fara`
  now skips on upstream `5xx` instead of failing the entire suite

## Highest-Signal Finding

The transport path is no longer the blocker.

The blocker is semantic value:

- memo findings can now move from `research_v3` into `onto-canon6`
- they survive review and promotion
- but they still do not yield graph objects for DIGIMON because the memo path
  exports free-text claims without reusable entity / role structure

If the end goal is shared memory that powers graph consumers, the next work
must make the active-loop export structured enough to produce canonical
entities, not just durable assertions.

## Next Phases

### 1. Close the memo-path semantic gap
Choose one explicit strategy and execute it:

- enrich `Finding` export with entity / role structure (`entity_refs` or an
  equivalent contract), or
- route active-loop outputs through a graph-derived export instead of raw memo
  claim text, or
- add a deliberate downstream extraction stage before DIGIMON export

Acceptance gate:

- real memo / loop artifact -> `onto-canon6` -> `>0` canonical entities ->
  `>0` DIGIMON rows without manual editing

### 2. Keep repo truth strict
- keep `README`, `STATUS`, `ROADMAP`, and `HANDOFF` aligned to the proof state
- do not mark consumer adoption complete until the memo/loop path yields graph
  value, not just storage

### 3. Optional follow-on hardening
- add a script-backed proof artifact for the Palantir memo run under `docs/runs/`
- consider whether the DIGIMON import seam should preserve more structure than
  flat entity-name / endpoint-pair merging

## Known Concerns / Uncertainties

### Shared-claim semantic thinness
- The Palantir memo proof promoted `61` assertions but created `0` entities.
- This is documented in:
  `docs/runs/2026-04-02_research_v3_memo_pipeline_proof.md`

### research_v3 live-network tests
- DOJ FARA foreign-principal endpoint returned HTTP `500` during verification.
- The suite now skips that case as an external outage.
- This does not affect the new memo export path.

## Authority Chain

| Document | Governs |
|----------|---------|
| `CLAUDE.md` | Strategic direction + execution policy |
| `docs/plans/0067_24h_end_goal_convergence_block.md` | Active 24h execution block |
| `docs/ROADMAP.md` | Forward-looking priorities |
| `docs/STATUS.md` | What is and isn't proven |
| `docs/plans/CLAUDE.md` | Plan index |
| `KNOWLEDGE.md` | Cross-agent runtime findings |

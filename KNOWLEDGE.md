### 2026-03-28 — codex — integration-issue
`onto-canon6/data/sumo_plus.db` already existed locally before the ownership
cutover and matched the donor `onto-canon/data/sumo_plus.db` byte-for-byte
(SHA-256 `9a6da4825eb9e4f4d81d1263e5c2ee6847bb85a1b899727e6be929658e1da0f6`).
That made the SUMO migration a contract cutover, not a rebuild project.

### 2026-03-28 — codex — best-practice
Archive-readiness should be verified from an isolated temp copy of the repo,
not inferred from the main workspace. `make verify-setup`, `make smoke`, and
`make check` all passed from `/tmp/onto-canon6-isolation.*` with no sibling
`onto-canon5` or `onto-canon` repos present.

### 2026-03-31 — codex — integration-issue
The supported DIGIMON export entrypoint is the installed `onto-canon6` console
script, not `python -m onto_canon6.cli`. `src/onto_canon6/cli.py` exposes
`main()` but does not execute it as a module entrypoint, so `python -m
onto_canon6.cli export-digimon ...` exits without writing JSONL. Use the
console script in docs and verification commands until the module entrypoint is
made explicit.

# Imported Profile Provenance

These profiles were imported into `onto-canon6` on 2026-03-28 as part of the
successor-ownership cutover.

They are now owned locally by this repo and are part of the canonical runtime
contract.

Imported profiles:

- `profiles/default/1.0.0`
  source repo: `onto-canon5`
  source path: `profiles/default/1.0.0`
- `profiles/dodaf/0.1.0`
  source repo: `onto-canon5`
  source path: `profiles/dodaf/0.1.0`
- `profiles/psyop_seed/0.1.0`
  source repo: `onto-canon5`
  source path: `profiles/psyop_seed/0.1.0`

Notes:

- Profile ids and versions were preserved intentionally for compatibility with
  proof artifacts, fixtures, and tests.
- `dm2_crosswalk.yaml` under `profiles/dodaf/0.1.0` was imported with the
  profile directory even though it is not part of the current runtime surface.

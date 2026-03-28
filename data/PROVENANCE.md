# Data Asset Provenance

Canonical data assets owned by `onto-canon6`.

## `sumo_plus.db`

- local path: `data/sumo_plus.db`
- became the canonical repo-owned path on 2026-03-28
- source repo: `onto-canon`
- original source path: `data/sumo_plus.db`
- SHA-256 at cutover:
  `9a6da4825eb9e4f4d81d1263e5c2ee6847bb85a1b899727e6be929658e1da0f6`

Notes:

- The local DB matched the donor DB byte-for-byte at cutover time.
- Scripts and tests should now treat this local path as authoritative.

# Compatibility Fixtures

This directory is reserved for Lane 3 compatibility artifacts from
`docs/plans/0026_schema_stability_gate.md`.

The goal is narrow: give each gated surface one deterministic local artifact so
schema-stability checks do not depend only on memory of a past run.

## Layout

- `promoted_graph/`
  - `minimal_promotion_result.json`
- `governed_bundle/`
  - `minimal_governed_bundle.json`
- `foundation_ir/`
  - `minimal_foundation_assertion.json`
- `digimon_v1/`
  - `minimal_entities.jsonl`
  - `minimal_relationships.jsonl`

## Ownership

| Surface | Primary owner check |
|---------|---------------------|
| Promoted graph typed surface | `tests/core/test_graph_service.py` |
| Governed bundle surface | `tests/surfaces/test_governed_bundle.py` |
| Foundation Assertion IR export | `tests/adapters/test_foundation_assertion_export.py` |
| DIGIMON v1 export seam | `tests/adapters/test_digimon_export.py` |

Secondary checks still matter:

- `tests/integration/test_mcp_server.py` for governed bundle export paths
- `tests/pipeline/test_temporal_qualifiers.py` for Foundation temporal fields
- DIGIMON `tests/unit/test_onto_canon_import.py` for the consumer-side import
  side of the v1 seam

## Normalization Rules

1. Normalize generated ids and timestamps when they are implementation details,
   not contract fields.
2. Preserve ids that are explicitly part of the contract under test.
3. Strip temp paths from snapshots.
4. Sort unordered collections before writing snapshots when order is not part
   of the surface contract.
5. Keep JSONL row ordering stable when the consumer currently relies on
   deterministic export order.

## Status

The directory layout is planned and reserved. The concrete fixture files are
not all implemented yet.

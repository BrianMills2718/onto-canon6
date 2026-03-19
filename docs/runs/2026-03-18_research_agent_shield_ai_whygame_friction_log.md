# Friction Log: 2026-03-18 research-agent Shield AI WhyGame Run

Use this log to record only observed workflow friction from the real cross-project run.
Keep it short and concrete.

## Format

- `timestamp`
- `step`
- `severity`
- `what happened`
- `workaround`
- `suggested fix`

## Entries

1. `2026-03-18T20:04-07:00` | `consumer import surface` | `medium` | `The existing WhyGame adapter worked, but there was no thin CLI command for importing a JSON file of relationship facts, so the first real cross-project import required ad hoc Python.` | `Implemented and then used a thin CLI command: import-whygame-relationships.` | `Keep real consumer adapters reachable from the CLI when the workflow is operational, not only from MCP or Python.`
2. `2026-03-18T20:03-07:00` | `producer contract shape` | `medium` | `research-agent entities.json is not a WhyGame-native contract. A narrow transformation step was needed to map source entity relationships into WhyGame RELATIONSHIP facts.` | `Generated a run-local WhyGame fact file from the real producer artifact.` | `If this producer path recurs, add a narrow research-agent-to-WhyGame conversion helper instead of repeating ad hoc transformation code.`
3. `2026-03-18T20:05-07:00` | `provenance richness` | `medium` | `The cross-project import preserved source metadata and artifact lineage, but not direct source text or evidence spans, because the producer artifact did not carry span-level evidence.` | `Accepted the relationship import as analysis-backed rather than text-grounded and preserved the upstream detail in source metadata.` | `If research-agent becomes a regular producer, decide whether it should emit span-bearing evidence objects instead of only relationship summaries.`

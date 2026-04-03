# TODO

## Current State

Most recently completed block:
- `docs/plans/0070_24h_graph_value_stop_gate.md`
- `docs/plans/0069_24h_non_gemini_fresh_memo_proof.md`
- `docs/plans/0068_24h_memo_semantic_lift_block.md`

## Current Priorities

1. Decide whether the memo path should stay on thin `shared:assertion` edges
   or grow richer graph-native relation semantics
2. Prove richer relation semantics only if they materially improve a real
   consumer outcome
3. Revisit broader consumer adoption after the semantic seam is honest

## Most Recently Closed

- Plan `0070` closed the contract-runtime promotion and stop-policy decision
- `config_loop_claude_runtime.yaml` is now the promoted profile for
  contract-style investigations
- fresh live contract-profile Palantir run:
  `23` promoted assertions -> `28` canonical entities -> `23` DIGIMON
  relationships

## Longer-Term Queue

- [ ] Revisit first-class source-artifact query after Plan `0068`
- [ ] Revisit richer DIGIMON interchange only through DIGIMON Plan 23
- [ ] Revisit trusted bulk ingestion only if a real workflow makes review the bottleneck

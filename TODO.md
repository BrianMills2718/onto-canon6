# TODO

## Current State

Most recently completed block:
- `docs/plans/0069_24h_non_gemini_fresh_memo_proof.md`
- `docs/plans/0068_24h_memo_semantic_lift_block.md`
- `docs/plans/0067_24h_end_goal_convergence_block.md`

## Current Priorities

1. Decide whether `config_loop_claude_runtime.yaml` should stay a proof-only
   profile or become the promoted runtime for contract-style investigations
2. Tighten loop stop behavior so proof-worthy contract investigations do not
   keep extending after graph value is already present
3. Decide whether the memo path should stay on thin `shared:assertion` edges
   or grow richer graph-native relation semantics

## Longer-Term Queue

- [ ] Revisit first-class source-artifact query after Plan `0068`
- [ ] Revisit richer DIGIMON interchange only through DIGIMON Plan 23
- [ ] Revisit trusted bulk ingestion only if a real workflow makes review the bottleneck

# TODO

## Current 24h Execution Block

Source of truth:
- `docs/plans/0063_24h_query_browse_widening_block.md`

### Phase 1 — Freeze Post-Merge Queryability Contract
- [ ] Create and activate Plan `0063`
- [ ] Align `CLAUDE.md`, `docs/plans/CLAUDE.md`, `TODO.md`, and active plan docs
- [ ] Restate Plan `0014` as a policy reference rather than an active transfer-hardening block
- [ ] Commit verified phase

### Phase 2 — Add Typed Browse Contracts And Service Support
- [ ] Add typed entity-browse and promoted-assertion-browse contracts
- [ ] Add `source_ref` / `source_kind` promoted-assertion filters
- [ ] Implement deterministic browse semantics in `QuerySurfaceService`
- [ ] Add/update service-level tests
- [ ] Commit verified phase

### Phase 3 — CLI And MCP Widening
- [ ] Add `list-entities` to the CLI
- [ ] Route `list-promoted-assertions` through the query surface and add source filters
- [ ] Add matching MCP browse tools
- [ ] Add/update CLI/MCP tests
- [ ] Commit verified phase

### Phase 4 — Real-Proof Verification
- [ ] Run the widened browse surface on a real promoted DB
- [ ] Record one entity-browse proof and one source-centric assertion proof
- [ ] Commit verified phase

### Phase 5 — Closeout
- [ ] Refresh `README.md`, `docs/STATUS.md`, `HANDOFF.md`, and Plan `0028`
- [ ] Mark Plan `0063` complete truthfully
- [ ] Record the next narrowed query-surface question
- [ ] Commit verified phase

## Longer-Term Queue

- [ ] Decide whether identity browse/list should fold into the query surface after Plan `0063`
- [ ] Decide whether source-artifact search needs its own future execution plan
- [ ] Revisit richer DIGIMON interchange only through DIGIMON Plan 23
- [ ] Revisit trusted bulk ingestion only if a real workflow makes review the bottleneck

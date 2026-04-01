# TODO

## Current 24h Execution Block

Source of truth:
- `docs/plans/0029_24h_query_surface_execution_block.md`

### Phase 1 — Shared Read Service
- [ ] Add typed query request/response models
- [ ] Implement read-only query service
- [ ] Add service-level tests
- [ ] Commit verified phase

### Phase 2 — CLI Surface
- [ ] Add `search-entities`
- [ ] Add `get-entity`
- [ ] Add `search-promoted-assertions`
- [ ] Add `get-promoted-assertion`
- [ ] Add `get-evidence`
- [ ] Add CLI tests
- [ ] Commit verified phase

### Phase 3 — MCP Surface
- [ ] Add thin MCP tools for the five operations
- [ ] Add integration coverage
- [ ] Commit verified phase

### Phase 4 — Real-Proof Verification
- [ ] Verify entity/alias lookup on real promoted data
- [ ] Verify promoted assertion lookup on real promoted data
- [ ] Verify evidence/provenance lookup on real promoted data
- [ ] Commit verified phase

### Phase 5 — Closeout
- [ ] Refresh docs/status/handoff
- [ ] Mark execution block complete
- [ ] Commit verified phase

## Longer-Term Queue

- [ ] Finish Plan 0025 value proof
- [ ] Evaluate whether Plan 0028 should widen beyond the first five operations
- [ ] Revisit consumer-blocked richer DIGIMON interchange only through DIGIMON Plan 23
- [ ] Revisit trusted bulk ingestion only if a real workflow makes review the bottleneck

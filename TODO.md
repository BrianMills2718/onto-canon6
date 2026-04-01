# TODO

## Current 24h Execution Block

Source of truth:
- `docs/plans/0029_24h_query_surface_execution_block.md`

### Phase 1 — Shared Read Service
- [x] Add typed query request/response models
- [x] Implement read-only query service
- [x] Add service-level tests
- [x] Commit verified phase

### Phase 2 — CLI Surface
- [x] Add `search-entities`
- [x] Add `get-entity`
- [x] Add `search-promoted-assertions`
- [x] Add `get-promoted-assertion`
- [x] Add `get-evidence`
- [x] Add CLI tests
- [x] Commit verified phase

### Phase 3 — MCP Surface
- [x] Add thin MCP tools for the five operations
- [x] Add integration coverage
- [x] Commit verified phase

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

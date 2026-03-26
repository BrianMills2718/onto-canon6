# onto-canon v1 Capability Parity Matrix

Updated: 2026-03-26

## Purpose

This document is the explicit parity ledger for the successor.

It answers one question that the Phase 10 bootstrap did not close:

What happened to the major capabilities that existed in `onto-canon`?

From this point forward:

1. no major v1 capability should remain implicit;
2. every capability must be marked as retained, expanded, replaced, deferred,
   or abandoned;
3. every deferred or replaced capability must map to a concrete roadmap phase
   or design note;
4. successor completion requires this matrix to have no ambiguous rows.

## Completion Gate

`onto-canon6` should not be treated as the full successor until:

1. every row below has an explicit disposition;
2. every `retained`, `expanded`, or `replaced` row has proof artifacts;
3. every `deferred` row either lands or is intentionally reclassified as
   `abandoned` with rationale.

## Matrix

| v1 capability | v1 evidence | onto-canon6 status | disposition | Planned closure |
|---|---|---|---|---|
| Packs, profiles, and explicit ontology policy | `onto-canon5` donor idea used to recover successor runtime shape | Proved in the runtime, validation, and overlay workflow | Expanded | Closed in bootstrap |
| Governed review over extracted assertions and ontology growth | `predicate_governance.py`, review flow in v1 | Proved through candidate review, proposal review, and overlays | Replaced and expanded | Closed in bootstrap |
| Text-grounded extraction with provenance | `amr_claim_extractor.py`, extraction pipeline | Proved through `llm_client`, evidence spans, and reviewable candidate assertions | Replaced and expanded | Closed in bootstrap |
| Live evaluation of extraction quality | v1 had extraction validation and benchmark-like checks | Proved with separated reasonableness, structural validation, and canonicalization fidelity lanes | Expanded | Closed in bootstrap |
| Canonical concept/belief graph with system beliefs | `concept_storage.py`, `beliefs`/`concepts` schema, `sys:*` beliefs | Narrow first slice recovered through promoted assertions/entities and explicit promotion from accepted candidates; full concept/system-belief layer still not recovered | Narrowed | Phase 11 |
| Stable identity and external references, including Q-code-like cross-investigation identity | Wikidata/Q-code flow in v1 | Narrow first slice recovered through promoted-entity identities, explicit alias membership, and explicit attached or unresolved external-reference state; broader v1 identity/Q-code behavior still not recovered | Narrowed | Phase 12 |
| Semantic canonicalization stack over predicates and roles | AMR/PropBank/SUMO/FrameNet/Wikidata stack in v1 | Narrow replacement slice recovered through explicit semantic-stack disposition, pack-driven predicate/role canonicalization, and persisted recanonicalization over promoted assertions; broader producer-side semantic adapters are still deferred | Replaced, narrowed | Phase 13 |
| Artifact lineage registry | `artifact_registry.py` and related MCP surface | Recovered as a bounded three-kind subsystem with candidate-centered links | Retained, narrowed | Broaden only if later phases need it |
| Epistemic engine | `belief_ops.py`, tension handling, updates, status transitions | Recovered through candidate confidence/supersession plus promoted-assertion `weakened`/`retracted` dispositions and derived corroboration/tension reports; broader temporal/inference behavior remains intentionally deferred | Retained, narrowed | Phase 15 complete; temporal/inference deferred unless later workflow pressure justifies return |
| Agent-facing operational surface | `canon_mcp_server.py`, 35 MCP tools | Narrow FastMCP surface recovered as a thin wrapper over successor services; broad v1 tool coverage remains intentionally unrecovered | Retained, narrowed | Phase 14 |
| External adapters | DIGIMON and WhyGame adapters in v1 | Narrow WhyGame relationship adapter recovered through an explicit successor-local contract; DIGIMON still deferred | Retained, narrowed | Phase 14 for WhyGame, Phase 15+ or later extension for DIGIMON |
| Cross-channel corroboration | Planned `canon_find_corroborations` in v1 status doc | Narrow deterministic corroboration groups recovered over promoted assertions | Retained, narrowed | Phase 15 complete |
| Temporal extraction and inference integration | Phase 4 plan in v1 status doc | Temporal qualifiers (valid_from/valid_to) implemented in extraction, payload storage, and Foundation IR export. Temporal inference remains deferred. | Partially recovered | Plan 0020 Gap 4. Inference deferred. |
| Repair and recanonicalization flows over bad stored assertions | v1 repair pipeline and SUMO repair tools | Narrow promoted-assertion repair flow recovered through explicit recanonicalization events and revalidation before persistence; broader graph-wide repair remains deferred | Retained, narrowed | Phase 13 and Phase 15 |
| Direct concept/belief CRUD (add, update, query) | `canon_add_concept`, `canon_add_belief`, `canon_add_evidence`, `canon_update_belief`, `canon_get_beliefs` | Not yet recovered; governed review workflow is the only ingestion path | Deferred | Extension point exists (services layer); add when consumer integration requires escape hatch or bulk ingestion. **Uncertainty**: will the governed workflow be usable for bulk ingestion (e.g., 10K research_v3 findings), or will a fast path be required? |
| Concept/entity browsing and search | `canon_list_concepts`, `canon_search_concepts`, `canon_get_evidence_for_concept`, `canon_search_evidence` | Not yet recovered; only candidate/proposal listing exists | Deferred | Required for any agent to use onto-canon6 as a queryable knowledge base. **Uncertainty**: should browsing surface be MCP-only, or also CLI? |
| DIGIMON bidirectional adapter | `canon_import_digimon_graph`, `canon_export_digimon_graph` | Export adapter operational (`digimon_export.py`), tested on real data (20 entities, 16 relationships → 19 merged nodes in GraphML). DIGIMON-side importer also built. Import adapter not yet built. | Retained, narrowed (export only) | Plan 0020 Gap 5 complete. Import adapter deferred. |
| Lead/investigation management | `canon_create_lead`, `canon_list_leads` | Not recovered; not in original parity matrix (silently dropped) | Deferred | Lightweight investigation tracking. May be replaced by a richer consumer-side concept. **Uncertainty**: does this belong in onto-canon6 or in research_v3? |
| Concept dedup and merge tools | `canon_merge_concepts`, `canon_prune_orphans` | Automated entity resolution by exact name match (`auto_resolution.py`). CLI: `auto-resolve-identities`. Proven: USSOCOM merged across 2 chunks. Fuzzy matching deferred. | Partially recovered | Plan 0020 Gap 3. Fuzzy matching and manual merge surface deferred. |
| Frame ontology interactive browsing | `canon_frame_lookup`, `canon_compress_predicates`, `canon_list_proposed_frames`, `canon_review_proposed_frame` | Not recovered; Predicate Canon bridge reads data but no interactive surface | Deferred | Low priority unless consumers need interactive frame exploration. |
| Multi-consumer query federation | Not in v1 | Not started | Vision (beyond v1) | Multiple consumers querying the same assertion store with different resolution strategies. **Uncertainty**: requires multi-tenant identity model not yet designed. |
| Cross-investigation entity resolution at scale | Not in v1 (Q-codes were partial) | Exact-name auto-resolution works across source chunks. Q-code and fuzzy matching not started. | Vision (beyond v1), partially started | Exact-name proven. Q-code/fuzzy/LLM-assisted strategies deferred. |
| Streaming/incremental ingestion | Not in v1 | Not started | Vision (beyond v1) | Real-time assertion ingestion from continuous sources. Architecture must not prevent this. **Uncertainty**: requires async pipeline design not yet specified. |

## Open Uncertainties

Uncertainties documented here are design questions that are explicitly unresolved.
They must be revisited when the relevant capability moves from deferred to active.

1. **Bulk ingestion vs governed review.** The governed workflow (candidate →
   review → promotion) is the right default. But will it scale to bulk
   ingestion (10K+ assertions from a research_v3 run)? If not, a trusted-source
   fast path is needed. The architecture must not prevent adding one.

2. **Entity resolution strategy.** The identity subsystem provides infrastructure
   (aliases, merges, external refs) but no default resolution strategy. Each
   consumer chooses their own. This is architecturally clean but means no
   cross-consumer entity resolution exists by default. Undecided: should there
   be a default strategy?

3. **Extraction packaging boundary.** The current extraction pipeline lives in
   onto-canon6 and is an active, first-class producer. No move is planned
   until a concrete shared producer boundary exists and a real consumer or
   maintenance burden justifies the split. If extraction ever moves, the target
   package and trigger condition should be decided explicitly rather than
   implied.

4. **DIGIMON weight semantics.** The export adapter maps onto-canon6
   confidence (0-1 probability) directly to DIGIMON edge weight. Default
   confidence=1.0 maps to weight=1.0. Non-unity confidence propagates
   correctly. Import direction not yet built.

5. **Temporal extraction and inference.** Explicitly deferred from current scope.
   The architecture (extension-based epistemics) does not prevent adding it later,
   but no design exists. If a consumer needs temporal reasoning, this is the
   largest unresolved design question.

6. **Schema stability definition.** The convergence plan with research_v3 lists
   "onto-canon6 schema stabilization" as a prerequisite. No criteria define what
   "stable enough" means. Propose: stable = no breaking changes to the promoted
   graph schema (entities, assertions, identity records) for 30 days.

## Notes

1. `retained` means the core capability exists again, even if the exact v1
   shape is cleaner or narrower.
2. `expanded` means the successor has a stronger or more explicit form than v1.
3. `replaced` means the user-visible capability returns through a different
   architecture.
4. `deferred` means the capability is still part of the successor goal and must
   not be silently forgotten.
5. `abandoned` should be used only with an explicit rationale and replacement
   thesis if user-visible value is still needed.

## Immediate Use

Before adding new code after Phase 10, check:

1. which row is being advanced;
2. whether the next change is recovering, replacing, or intentionally dropping
   a v1 capability;
3. whether the roadmap phase and acceptance evidence match that row.

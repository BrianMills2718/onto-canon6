# onto-canon v1 Capability Parity Matrix

Updated: 2026-03-18

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
| Semantic canonicalization stack over predicates and roles | AMR/PropBank/SUMO/FrameNet/Wikidata stack in v1 | Not yet recovered or explicitly replaced end to end | Deferred | Phase 13 |
| Artifact lineage registry | `artifact_registry.py` and related MCP surface | Recovered as a bounded three-kind subsystem with candidate-centered links | Retained, narrowed | Broaden only if later phases need it |
| Epistemic engine | `belief_ops.py`, tension handling, updates, status transitions | Recovered only as confidence plus supersession over accepted candidates | Retained, narrowed | Phase 15 for broader recovery |
| Agent-facing operational surface | `canon_mcp_server.py`, 35 MCP tools | CLI proved; MCP and richer agent boundary still absent | Deferred | Phase 14 |
| External adapters | DIGIMON and WhyGame adapters in v1 | Not yet recovered in successor-local form | Deferred | Phase 14 |
| Cross-channel corroboration | Planned `canon_find_corroborations` in v1 status doc | Not present in successor | Deferred | Phase 15 |
| Temporal extraction and inference integration | Phase 4 plan in v1 status doc | Not present in successor | Deferred | Phase 15 |
| Repair and recanonicalization flows over bad stored assertions | v1 repair pipeline and SUMO repair tools | Not yet recovered for successor-local canonical graph state | Deferred | Phase 13 and Phase 15 |

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

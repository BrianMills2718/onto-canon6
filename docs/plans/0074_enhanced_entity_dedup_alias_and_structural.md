# Plan 0074 — Enhanced Entity Deduplication: Alias Extraction, Structural Fingerprinting, and Profile-Aware Merge Verification

**Status:** Draft
**Type:** implementation
**Priority:** High — closes recall gap in Pass 4b that misses semantic-equivalence duplicates with no string overlap
**Blocked By:** #0072 complete (Pass 4 entity normalization — done)

---

## Gap

**Current:** Pass 4b generates candidate duplicate pairs using only string heuristics (substring containment, acronym first-letter match, Levenshtein distance ≤ 1), then sends candidates to an LLM merge verifier with entity name + SUMO type + one evidence span. This misses two large classes of duplicates:

1. Alias pairs that are declared in the source text using parenthetical patterns ("Islamic Revolutionary Guard Corps (IRGC)") but where the naive acronym heuristic fails because the string forms don't share enough overlap.
2. Entities that are structurally the same real-world actor — appearing together in the same set of predicate roles across multiple assertions — but whose names share zero string similarity (e.g., "Charming Kitten" / "APT42").

The merge verifier also has no access to structural evidence (what predicates an entity participates in, co-participants), so even when a candidate pair is correctly surfaced, the verifier prompt cannot use the strongest available signal.

**Target:** Pass 4b detects alias pairs deterministically from text-declared parenthetical patterns, generates structurally-informed candidate pairs from predicate-role overlap (Jaccard ≥ 0.35 on the predicate-role profile), and the merge verifier prompt is enhanced to pass per-entity top-3 assertions plus alias and co-participant signals. Dense embedding-based candidate detection is deferred.

**Why:** "Charming Kitten / APT42"-class misses are the most damaging to graph quality — they produce systematically split entity nodes that downstream consumers (the browser, Digimon) cannot aggregate. Every fact about APT42 that arrives under "Charming Kitten" is invisible to queries against APT42. Alias extraction from text is zero-cost and eliminates an entire class of false-splits where the text itself declares the equivalence.

---

## References Reviewed

- `src/onto_canon6/pipeline/progressive_extractor.py:1295–2038` — full Pass 4 implementation including `_collect_entity_infos`, `detect_near_duplicate_pairs`, `_are_types_compatible`, `run_pass4_normalization`, `_apply_normalization_to_pass3`
- `src/onto_canon6/pipeline/progressive_types.py` — `Pass4NormalizationResult`, `MergeDecision`, `AnaphorResolution`, `Pass3TypedAssertion`, `Pass2MappedAssertion`
- `prompts/extraction/pass4_merge_duplicates.yaml` — current merge verifier prompt; takes `candidate_groups[].entities[]{name, sumo_type, evidence_span}`
- `prompts/extraction/pass4_entity_normalization.yaml` — anaphor resolution prompt
- `tests/pipeline/test_progressive_extractor_pass4.py` — 53 test functions covering detection + normalization; regression gate
- `docs/plans/0072_entity_normalization_pass.md` — plan that established Pass 4

## Research Basis

The Grale system (Google, KDD 2020) establishes the following blocking pipeline for entity deduplication at scale:
1. LSH blocking on string tokens (our Tier 1 heuristics)
2. Type constraints to reject cross-type candidates (our `_are_types_compatible`)
3. **Determinative predicate fingerprints:** entities sharing multiple (predicate_id, role_label) tuples are strong merge candidates regardless of name
4. **Alias table from text:** parenthetical patterns in prose are treated as declared equivalences
5. Collective coherence via LLM (our merge verifier call)
6. Dense embeddings for recall at large scale (deferred)

This plan adds capabilities 3 and 4, and upgrades capability 5.

---

## Design Decisions (Pre-Made)

All decisions are resolved so an implementing agent can proceed without design review.

### Capability 1: Alias Extraction from Source Text

**D1.1 — Where in the pipeline:**
Alias extraction runs as a new sub-step within `run_pass4_normalization`, before `detect_near_duplicate_pairs`. It takes the raw source text (new optional `source_text: str = ""` parameter on `run_pass4_normalization`). Alias pairs are injected into `normalization_map` before near-duplicate detection so string heuristics do not re-examine already-resolved aliases.

**D1.2 — Regex patterns:**
```python
import re

# Pattern A: "Full Name (ACRONYM)" — full form declared, abbreviation follows
ALIAS_PAREN_DEFINE = re.compile(
    r'\b([A-Z][^\(\)\n]{4,80}?)\s+\(([A-Z][A-Z0-9\-]{1,15})\)',
    re.UNICODE,
)

# Pattern B: "ACRONYM (Full Name)" — abbreviation declared first, expansion follows
ALIAS_PAREN_EXPAND = re.compile(
    r'\b([A-Z][A-Z0-9\-]{1,15})\s+\(([A-Z][^\(\)\n]{4,80}?)\)',
    re.UNICODE,
)
```

Short form: ALL-CAPS, length 2–16, may contain digits/hyphens. Long form: starts capital, 5–80 chars. Article-led phrases ("the Group") are excluded by the `[A-Z]` anchor.

**D1.3 — Canonical form:**
The longer form is canonical. `canonical = max(short_form, long_form, key=len)`. Consistent with the merge verifier guidance ("prefer longer, more descriptive canonical forms").

**D1.4 — LLM verification required?**
No. Text-declared parenthetical aliases are accepted deterministically without LLM verification. This is both the most important correctness property and the zero-cost path.

**D1.5 — Source text threading:**
`run_pass4_normalization` gains `source_text: str = ""` keyword argument (non-breaking — default is empty string). The orchestrator `run_progressive_extraction` passes `source_text="\n\n".join(chunks)`.

**D1.6 — Data type:**
New `AliasPair` model (see Data Model Changes). Stored in `Pass4NormalizationResult.alias_pairs`. The `normalization_map` is also updated (short_form → long_form). Alias pairs are NOT `MergeDecision` records — they are a separate provenance trail for zero-LLM-cost rewrites.

**D1.7 — Interaction with near-duplicate detection:**
After alias pairs are registered in `normalization_map`, non-canonical forms (short forms) are excluded from `detect_near_duplicate_pairs` input to avoid sending already-resolved pairs to the LLM verifier.

**D1.8 — Guard against false alias pairs:**
Only register an alias pair if both forms appear as entity names in `entity_infos` (the Pass 3 entity list). Regex matches that don't correspond to actual extracted entities are ignored.

---

### Capability 2: Structural Fingerprint Deduplication

**D2.1 — Profile definition:**
For each entity, compute its predicate-role profile as a `frozenset` of `(predicate_id, role_label)` tuples. `role_label` comes from `mapped_roles` keys in `Pass2MappedAssertion`. `predicate_id` comes from the same assertion. Both are available by iterating `pass3_result.typed_assertions`.

Example — entity "IRGC":
```
frozenset({("target_attack", "Agent"), ("deploy_use", "Agent"), ("fund_sponsor", "Agent")})
```

**D2.2 — Jaccard threshold: 0.35**
Rationale: at 4 pairs each with 2 shared → Jaccard = 2/(4+4-2) = 0.333 → NOT a candidate. At 3 shared → 0.600 → candidate. Lower than 0.30 produces spurious pairs from generic roles. Higher than 0.40 misses the target use case.

**D2.3 — Minimum assertion count: 2**
Entities with profile size < 2 are excluded. A single-assertion entity has insufficient signal — any two single-assertion entities sharing one predicate would be spurious candidates.

**D2.4 — Set vs multiset: frozenset (set)**
Frequency does not add meaningful signal. An entity appearing three times as Agent in `target_attack` is not "more" of a target-attack agent. Set formulation matches the Grale determinative fingerprint step exactly.

**D2.5 — Integration: union, not replace**
Both string heuristics and structural fingerprints generate candidate pairs. The union is deduplicated before the LLM verifier call. Existing string recall is preserved.

**D2.6 — Type guard: still applies**
`_are_types_compatible` is checked for structurally-detected pairs before LLM verification.

**D2.7 — Co-participant signal: in verifier prompt only**
Co-participant overlap (entities A and B both appearing with entity C) is a noisy candidate-generation signal. It is included in the LLM verifier prompt as secondary evidence (Capability 3), not used for candidate generation.

**D2.8 — New function signatures:**
```python
def compute_entity_profiles(
    pass3_result: Pass3Result,
    entity_names: set[str],
) -> dict[str, frozenset[tuple[str, str]]]:
    """Return mapping from entity name → (predicate_id, role_label) profile."""

def detect_structural_duplicate_pairs(
    entity_infos: list[dict[str, str]],
    profiles: dict[str, frozenset[tuple[str, str]]],
    *,
    jaccard_threshold: float = 0.35,
    min_profile_size: int = 2,
) -> list[tuple[dict[str, str], dict[str, str]]]:
    """Return structurally-similar entity pairs by Jaccard on predicate-role profiles."""
```

---

### Capability 3: Profile-Aware LLM Merge Verifier

**D3.1 — Evidence per entity in a candidate pair:**
- Name + SUMO type (existing)
- Evidence span truncated to 150 chars (existing)
- Top-3 assertions: `predicate_id` + `mapped_roles` values (entity names) + `evidence_span` truncated to 100 chars
- Any alias pairs already detected for this entity
- Co-participant overlap: entity names appearing with BOTH entities across their assertions (up to 5 names)

**D3.2 — Token budget per entity-pair: ~600 tokens maximum**
Enforcement: top-3 assertions capped at 3 items, evidence spans to 100 chars, co-participant list to 5 names.

**D3.3 — Single prompt, not separate:**
`pass4_merge_duplicates.yaml` is updated in place. New template fields (`assertions`, `alias_hints`, `co_participants`, `detection_method`) are optional — when empty, the prompt degrades to current format.

**D3.4 — Detection method label:**
Each candidate group includes `detection_method: "string_heuristic" | "structural_fingerprint"`. The system section includes: "For structural fingerprint pairs, weight the assertion evidence heavily — name similarity may be zero."

**D3.5 — Response schema unchanged:**
`verdict`, `canonical`, `confidence`, `evidence` remain the same. `_parse_merge_response` is unchanged.

---

### Capability 4: Embedding-Based Candidate Detection (Deferred)

Explicitly deferred. Implement only after Capabilities 1-3 are proven. Design when needed: embed profile string `"[name] [type]. [top predicates]. [co-participants]."`, cosine > 0.85 → candidate pair → existing LLM verifier.

---

## Data Model Changes

### New type: `AliasPair` (in `progressive_types.py`)

```python
class AliasPair(BaseModel):
    """A text-declared alias relationship between two entity name forms.

    Extracted from parenthetical patterns in source text ("Full Name (ABBREV)").
    No LLM verification is required — text-declared equivalences are accepted
    deterministically.
    """
    model_config = ConfigDict(extra="forbid", frozen=True)

    short_form: str = Field(description="The abbreviated or acronym form.")
    long_form: str = Field(description="The expanded or full form (canonical).")
    source_pattern: str = Field(
        description="The raw text span that contained the alias declaration."
    )
```

### Modified type: `Pass4NormalizationResult`

Add one new field:
```python
alias_pairs: list[AliasPair] = Field(
    default_factory=list,
    description=(
        "Alias pairs extracted deterministically from source text parenthetical patterns. "
        "Short forms are rewritten to long forms in the normalization_map without LLM verification."
    ),
)
```

`default_factory=list` ensures existing instantiation sites remain valid. No other types change.

---

## Files Affected

| File | Change |
|------|--------|
| `src/onto_canon6/pipeline/progressive_types.py` | Add `AliasPair`; add `alias_pairs` field to `Pass4NormalizationResult` |
| `src/onto_canon6/pipeline/progressive_extractor.py` | Add `extract_alias_pairs`, `compute_entity_profiles`, `detect_structural_duplicate_pairs`; update `run_pass4_normalization` signature and body; update `_collect_entity_infos` to also build profiles |
| `prompts/extraction/pass4_merge_duplicates.yaml` | Add `detection_method`, `assertions`, `alias_hints`, `co_participants` fields to user template |
| `tests/pipeline/test_progressive_extractor_pass4.py` | Add new test classes; existing 53 tests must still pass |

---

## Implementation Phases

| Phase | Task | Verification Gate |
|-------|------|-------------------|
| 1 | Add `AliasPair` to `progressive_types.py`; add `alias_pairs: list[AliasPair] = Field(default_factory=list)` to `Pass4NormalizationResult` | `pyright` passes; all 53 existing pass4 tests still pass (no instantiation breakage) |
| 2 | Implement `extract_alias_pairs(source_text: str, entity_names: set[str]) -> list[AliasPair]` with both regex patterns and entity-presence guard | Unit tests: "Islamic Revolutionary Guard Corps (IRGC)" with both names in entity list → `AliasPair` produced; reversed pattern works; non-entity matches produce nothing |
| 3 | Wire alias extraction into `run_pass4_normalization`: add `source_text: str = ""` param; call `extract_alias_pairs` before `detect_near_duplicate_pairs`; exclude alias non-canonicals from near-dup input; populate `result.alias_pairs` | Integration test: mock pass3 with "IRGC" + "Islamic Revolutionary Guard Corps" entities, source_text with parenthetical → `normalization_map["IRGC"] = "Islamic Revolutionary Guard Corps (IRGC)"` with zero LLM cost increase |
| 4 | Implement `compute_entity_profiles` and `detect_structural_duplicate_pairs` | Unit tests: Jaccard at/above threshold → candidate; < 2 assertions → excluded; type-incompatible pairs → rejected; combined pairs list has no duplicates |
| 5 | Wire structural fingerprinting into `run_pass4_normalization`: call after string heuristics, union pairs, deduplicate, annotate each pair with `detection_method` | Integration test: mock pass3 where two entities share 2+ predicate-role pairs → structurally-detected pair appears in combined `dup_pairs` |
| 6 | Update `pass4_merge_duplicates.yaml`; update `run_pass4_normalization` to build richer `candidate_groups` dict | Prompt renders correctly with and without new optional fields; a structural pair's rendered prompt includes predicate evidence |
| 7 | Smoke test on real corpus: source text containing "Islamic Revolutionary Guard Corps (IRGC)" | Alias pair detected; "IRGC" rewrites to long form in normalization_map; no LLM cost for alias |
| 8 | Update `tests/pipeline/test_progressive_extractor_pass4.py` with new test classes | All 53 existing tests pass; all new tests pass |

---

## Acceptance Criteria

### Capability 1 (Alias Extraction)
- [ ] "Islamic Revolutionary Guard Corps (IRGC)" with both names in entity list → `AliasPair(short_form="IRGC", long_form="Islamic Revolutionary Guard Corps (IRGC)")`
- [ ] Reversed pattern "IRGC (Islamic Revolutionary Guard Corps)" → same `AliasPair`
- [ ] Alias pairs applied to `normalization_map` without LLM call — `cost_usd` unchanged when only alias pairs detected
- [ ] Regex match where neither form is in entity list → no `AliasPair` (guard works)
- [ ] `Pass4NormalizationResult.alias_pairs` populated with detected pairs
- [ ] Non-canonical form excluded from `detect_near_duplicate_pairs` input

### Capability 2 (Structural Fingerprinting)
- [ ] Two entities with 4 assertions each, 2 shared pairs → Jaccard 0.333 → NOT candidate at 0.35 threshold
- [ ] Two entities with 4 assertions each, 3 shared pairs → Jaccard 0.600 → IS candidate
- [ ] Entity with only 1 assertion → excluded from structural comparison
- [ ] Structurally-detected pair with incompatible SUMO types → rejected by type guard
- [ ] Combined pairs list (string ∪ structural) has no duplicate (A, B) pairs
- [ ] `detect_structural_duplicate_pairs` on 10-entity set runs in < 100 ms (pure Python)

### Capability 3 (Profile-Aware Merge Verifier)
- [ ] Rendered prompt for structural pair includes `detection_method: "structural_fingerprint"`
- [ ] Rendered prompt includes at least 1 assertion per entity (predicate + roles + evidence)
- [ ] Rendered prompt for entity with alias hint includes that hint
- [ ] LLM response schema unchanged; `_parse_merge_response` parses enhanced prompts correctly
- [ ] Empty `assertions`/`alias_hints`/`co_participants` → prompt renders without error

### Regression
- [ ] All 53 existing pass4 tests pass
- [ ] `pyright` passes on all modified files
- [ ] `run_pass4_normalization` with `source_text=""` (default) behaves identically to current behavior

---

## Failure Modes and Diagnostics

| Failure Mode | Symptom | Diagnosis / Fix |
|---|---|---|
| Alias regex over-matches | Common noun phrases registered as aliases ("United States (US)") | Check entity-presence guard; add min long-form length guard (> 15 chars) |
| Alias regex under-matches | Known alias pair not detected | Source uses non-standard parenthetical (em-dash, brackets); extend pattern |
| Structural pairs explode | Hundreds of pairs for 50-entity run | Threshold too low; raise to 0.40; or raise min_profile_size to 3 |
| Structural false positive to LLM | Two unrelated orgs share generic (target_attack, Agent) pair | Filter the top-5 most common (predicate, role) pairs from profiles before Jaccard |
| Profile-aware prompt too large | LLM context-length error | Reduce top-3 to top-2; tighten evidence spans from 100 to 60 chars |
| Alias overrides valid distinct entities | "US" resolves to "United States" when both are separate actors | Add SUMO-type compatibility check for alias pairs too |
| Existing tests fail on `Pass4NormalizationResult` | `alias_pairs` field missing in test fixtures | All test fixtures constructing `Pass4NormalizationResult` must add `alias_pairs=[]` |

---

## Required New Tests

| Test Class | Test Function | What It Verifies |
|---|---|---|
| `TestExtractAliasPairs` | `test_paren_define_pattern` | Pattern A detected, both names in entity list |
| `TestExtractAliasPairs` | `test_paren_expand_pattern` | Pattern B (reversed) detected |
| `TestExtractAliasPairs` | `test_entity_presence_guard` | No alias pair when forms not in entity_infos |
| `TestExtractAliasPairs` | `test_longer_form_is_canonical` | Long form is canonical regardless of pattern order |
| `TestComputeEntityProfiles` | `test_profile_built_from_assertions` | Correct (predicate_id, role_label) pairs |
| `TestComputeEntityProfiles` | `test_entity_not_in_assertions_empty_profile` | Entity with no assertions → empty frozenset |
| `TestDetectStructuralPairs` | `test_jaccard_above_threshold` | Pair detected at Jaccard ≥ 0.35 |
| `TestDetectStructuralPairs` | `test_jaccard_below_threshold` | Pair NOT detected at Jaccard < 0.35 |
| `TestDetectStructuralPairs` | `test_min_profile_size_excluded` | 1-assertion entity excluded |
| `TestDetectStructuralPairs` | `test_type_guard_still_applies` | Incompatible SUMO types rejected |
| `TestDetectStructuralPairs` | `test_union_no_duplicates` | String ∪ structural pairs has no duplicate (A,B) |
| `TestRunPass4WithAlias` | `test_alias_registered_without_llm_cost` | `cost_usd` unchanged when only alias pairs fire |
| `TestRunPass4WithAlias` | `test_alias_form_excluded_from_near_dup_detection` | Non-canonical form absent from near-dup input |
| `TestRunPass4WithAlias` | `test_alias_pairs_in_result` | `Pass4NormalizationResult.alias_pairs` populated |
| `TestRunPass4WithAlias` | `test_source_text_empty_no_alias_pairs` | Empty `source_text` → no alias pairs |

---

## Execution Order Within `run_pass4_normalization` After This Plan

```
1.  collect entity infos              (_collect_entity_infos)          existing
2.  detect anaphors                   (_is_anaphor)                    existing
3.  extract alias pairs from text     (extract_alias_pairs)            NEW
4.  apply alias pairs to norm_map                                      NEW
5.  compute entity profiles           (compute_entity_profiles)        NEW
6.  string heuristic near-dup detect  (detect_near_duplicate_pairs)    existing
    [excluding alias non-canonicals]                                   NEW
7.  structural fingerprint near-dup   (detect_structural_duplicate_pairs) NEW
8.  union + deduplicate candidate pairs                                NEW
9.  LLM anaphor resolution call                                        existing
10. LLM merge verification call       (enhanced prompt)                modified
11. build consolidated norm_map       (_build_normalization_map)       existing
12. apply normalization to Pass 3     (_apply_normalization_to_pass3)  existing
```

---

## Notes

**Why frozenset for profiles, not Counter?**
The structural fingerprint answers "does this entity participate in these types of events?" — not "how often?". A Counter would give extra weight to entities that appeared in many chunks, which is an artifact of document structure rather than entity identity. The frozenset formulation matches the Grale paper exactly.

**Why longest form as canonical for alias pairs?**
The merge verifier prompt already says "prefer longer, more descriptive canonical forms." Making alias extraction consistent means norm_map entries from both alias pairs and LLM merge decisions point in the same direction, avoiding conflicts.

**Why separate `alias_pairs` from `normalization_map`?**
The `normalization_map` is a `dict[str, str | None]` used for both anaphors and merges. Adding alias pairs there is correct for rewriting, but provenance (why was this entry added?) would be lost. The separate `alias_pairs` list preserves the audit trail: an operator can see which rewrites came from text-declared equivalences (zero-cost, high-confidence) vs LLM decisions.

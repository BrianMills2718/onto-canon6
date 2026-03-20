# Ancestor-Aware Evaluator and Fidelity Experiments

Status: planned

Updated: 2026-03-19

## Purpose

Build the evaluation infrastructure needed to measure progressive disclosure
extraction accuracy and determine optimal fidelity levels. This plan produces
the empirical data that ADR-0018 (progressive disclosure) depends on before
its pass structure can be finalized.

Implements ADR-0019 (ancestor-aware evaluation with growing acceptable sets).

## Requirements

1. An ancestor-aware evaluator that scores type picks against the SUMO
   hierarchy from v1's `sumo_plus.db`.
2. Integration with `prompt_eval`'s `GoldenSetManager` (Plan 07) for the
   growing acceptable set.
3. A fidelity experiment comparing top-level, mid-level, and full-subtree
   SUMO seeding.
4. Baseline measurement: how accurate are coarse LLM picks with top-level
   SUMO seeding only?

## Design

### Component 1: Ancestor-aware evaluator

A custom `prompt_eval` evaluator that lives in onto-canon6.

```python
# src/onto_canon6/evaluation/ancestor_evaluator.py

def make_ancestor_evaluator(
    sumo_db_path: Path,
) -> Callable[[str, str], EvalScore]:
    """Build an evaluator that checks ancestor-or-equal in SUMO hierarchy.

    Returns EvalScore with dimensions:
    - exact: 1.0 if pick == reference, else 0.0
    - ancestor_match: 1.0 if pick is ancestor-or-equal, else 0.0
    - specificity: depth(pick) / depth(reference) when ancestor match
    """
```

**Data source**: v1's `sumo_plus.db` contains:
- `type_ancestors` table: 73,730 materialized closure records
- `types` table: 7,894 types with hierarchy depth

**Query**: `SELECT 1 FROM type_ancestors WHERE type_name = ? AND ancestor_name = ?`
→ O(1) ancestor check.

For specificity: `depth(pick) / depth(reference)` where depth is the longest
path from root. If pick == reference, specificity = 1.0. If pick is a
direct ancestor, specificity < 1.0 proportional to how much coarser it is.

### Component 2: SUMO hierarchy utilities

```python
# src/onto_canon6/evaluation/sumo_hierarchy.py

class SUMOHierarchy:
    """Read-only interface to v1's SUMO type hierarchy."""

    def __init__(self, db_path: Path) -> None: ...
    def is_ancestor_or_equal(self, candidate: str, reference: str) -> bool: ...
    def depth(self, type_name: str) -> int: ...
    def subtypes(self, type_name: str, max_depth: int | None = None) -> list[str]: ...
    def ancestors(self, type_name: str) -> list[str]: ...
    def subtree_at_depth(self, root: str, target_depth: int) -> list[str]: ...
```

This wraps v1's `sumo_plus.db` as a read-only dependency. The DB file is
referenced by path in `config.yaml`, not copied into onto-canon6.

### Component 3: Fidelity experiment

Three conditions, same extraction corpus:

| Condition | SUMO context in prompt | Expected tokens |
|-----------|----------------------|-----------------|
| `top_level` | ~50 types (Entity, Process, CognitiveAgent, ...) | ~500 |
| `mid_level` | ~30 types per relevant branch | ~1500 |
| `full_subtree` | All descendants of constraint type | variable |

**Experiment design**:
1. Select 10-20 entities from Stage 1 + Shield AI runs with known reference
   types.
2. For each entity, construct prompts with each fidelity level's type list.
3. Ask the LLM to pick the best SUMO type.
4. Score with the ancestor-aware evaluator.
5. Compare conditions with `prompt_eval` statistical comparison.

**Metrics per condition**:
- `ancestor_match_rate`: fraction where pick is ancestor-or-equal
- `exact_match_rate`: fraction where pick == reference
- `mean_specificity`: average depth ratio
- `wrong_branch_rate`: fraction where pick is neither ancestor nor descendant
- `cost_per_item`: average cost per entity typing call
- `latency_per_item`: average latency

### Component 4: Growing acceptable set integration

Uses `prompt_eval`'s `GoldenSetManager` (Plan 07). The evaluator pipeline:

```
pick == reference?
  → yes: score 1.0

pick is ancestor-or-equal of reference?
  → yes: score by specificity

pick in acceptable_alternatives[reference]?
  → yes: return cached score

LLM judge: "Is pick a reasonable type for this entity given the source text?"
  → reasonable: add to acceptable set, score as alternative match
  → unreasonable: add to rejected set, score 0.0
```

**If Plan 07 is not yet implemented**: the evaluator works without it — the
growing acceptable set is an enhancement, not a prerequisite. Without it,
non-ancestor picks always go to the LLM judge (higher cost, same accuracy).

### Component 5: Baseline measurement

Before the fidelity experiment, measure: what do LLMs already know about
SUMO types without any ontology context?

1. Same entity set as the fidelity experiment.
2. Prompt: "What SUMO type best describes [entity]?" with NO type list.
3. Score with ancestor-aware evaluator.
4. This establishes the LLM's baseline training knowledge and tells us how
   much ontology seeding actually helps.

v1 already has `eval_llm_ontology_knowledge_*.json` files that may provide
partial data for this.

## Files Affected

New files:
- `src/onto_canon6/evaluation/ancestor_evaluator.py`
- `src/onto_canon6/evaluation/sumo_hierarchy.py`
- `tests/evaluation/test_ancestor_evaluator.py`
- `tests/evaluation/test_sumo_hierarchy.py`

Modified files:
- `config/config.yaml` — add `sumo_db_path` and fidelity experiment config

## Build Order

1. **SUMO hierarchy utilities**: `SUMOHierarchy` class wrapping v1's DB.
   Tests: ancestor checks, depth queries, subtree enumeration.
2. **Ancestor-aware evaluator**: Custom evaluator returning `EvalScore`.
   Tests: exact match, ancestor match with specificity, wrong branch.
3. **Config**: Add `sumo_db_path` pointing to v1's `sumo_plus.db`.
4. **Baseline measurement**: Run zero-context SUMO type assignment on
   10-20 entities. Record results.
5. **Fidelity experiment**: Three conditions over the same entity set.
   Run via `prompt_eval`. Compare with statistical tests.
6. **Growing acceptable set**: Wire `GoldenSetManager` into the evaluator
   (after Plan 07 ships). This step is optional and can be deferred.

Steps 1-3 are immediately implementable. Steps 4-5 require LLM calls and
cost money. Step 6 depends on prompt_eval Plan 07.

## Acceptance Criteria

- [ ] `SUMOHierarchy` correctly queries v1's `sumo_plus.db` ancestor closure
- [ ] Ancestor-aware evaluator returns correct scores for exact, ancestor,
      wrong-branch cases
- [ ] Baseline measurement produces ancestor_match_rate for zero-context picks
- [ ] Fidelity experiment compares 3 conditions with statistical significance
- [ ] Results inform ADR-0018 pass structure decisions
- [ ] All existing tests pass

## Known Risks

1. v1's `sumo_plus.db` may have stale or incomplete data. Validate a sample
   of ancestor queries against known SUMO relationships.
2. The entity set for experiments must be representative. Using only military
   domain entities may not generalize. Include at least 2-3 non-military
   entities from the WhyGame run.
3. LLM baseline SUMO knowledge may vary by model. Run baseline on at least
   2 models (gemini-2.5-flash, claude-sonnet).

## Relationship to Prior Work

- Implements: ADR-0019 (ancestor-aware evaluation)
- Depends on: v1's `sumo_plus.db` (read-only)
- Integrates with: prompt_eval Plan 07 (growing acceptable set, optional)
- Informs: Plan 0018 (progressive disclosure pass structure)
- Extends: Plan 0014 (extraction quality baseline) with type-accuracy metrics

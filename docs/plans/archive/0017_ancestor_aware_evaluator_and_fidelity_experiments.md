# Ancestor-Aware Evaluator and Fidelity Experiments

Status: complete

Updated: 2026-03-21
Implements: ADR-0019
Workstream: post-bootstrap extraction R&D (ADR-0022)

## Purpose

Build the evaluator and experiment surfaces needed to measure type fidelity for
the progressive extraction workstream.

This plan exists to answer a narrow but important question before scaling the
new extractor: when an LLM is choosing SUMO types, what prompt context level is
actually helpful, and how should those choices be scored truthfully?

## Acceptance Criteria

This plan is complete when:

1. the repo has a local SUMO hierarchy utility that can score ancestor and
   descendant relationships deterministically;
2. the repo has a local ancestor-aware evaluator that returns more signal than
   exact-match-only scoring;
3. fidelity experiments can run through `prompt_eval` and produce aggregate
   reports;
4. the repo has a deterministic Predicate Canon bridge for lemma and role-slot
   lookups;
5. the empirical results are strong enough to inform Plan 0018 pass design.

## Implemented Shape

The repo-local implementation now consists of:

1. `src/onto_canon6/evaluation/sumo_hierarchy.py`
   - read-only access to v1's `sumo_plus.db`
   - ancestor, descendant, depth, and subtree queries
2. `src/onto_canon6/evaluation/ancestor_evaluator.py`
   - exact, ancestor-branch, and specificity-aware scoring
3. `src/onto_canon6/evaluation/predicate_canon.py`
   - read-only Predicate Canon bridge over predicates and role slots
4. `src/onto_canon6/evaluation/fidelity_experiment.py`
   - typed experiment-item preparation
5. `src/onto_canon6/evaluation/fidelity_runner.py`
   - `prompt_eval` execution bridge plus aggregate reporting

## Empirical Result

The key fidelity result that informed Plan 0018 was:

1. top-level seeding: `87.5%` ancestor match
2. mid-level seeding: `62.5%`
3. full-subtree seeding: `50.0%`

The main conclusion is that showing more ontology types by default made the
model worse, not better. That result is why Plan 0018 starts with coarse
top-level typing and only narrows later.

## Shared vs Local Responsibility

One earlier design sketch overstated the local outcome by listing
`GoldenSetManager` as if it were a new onto-canon6-owned subsystem.

The truthful boundary is:

1. `onto-canon6` owns the hierarchy utility, evaluator, Predicate Canon
   bridge, experiment preparation, and report interpretation;
2. `prompt_eval` remains the shared experiment runner and the place where
   growing acceptable-set support belongs;
3. this repo may depend on that shared capability, but it does not need to
   pretend it re-implemented it locally.

## Evidence

Primary proof surfaces:

1. `tests/evaluation/test_sumo_hierarchy.py`
2. `tests/evaluation/test_ancestor_evaluator.py`
3. `tests/evaluation/test_predicate_canon.py`
4. `tests/evaluation/test_fidelity_experiment.py`
5. `tests/evaluation/test_fidelity_runner.py`
6. CLI surfaces in `src/onto_canon6/cli.py`

## Consequences

Positive:

1. the extraction workstream now has a truthful type-fidelity scoring surface;
2. Plan 0018 no longer relies on intuition alone for its coarse-to-fine pass
   structure;
3. ontology seeding decisions can be judged by measured branch accuracy rather
   than by “more ontology must be better”.

Costs:

1. the evaluator depends on donor SUMO data from v1;
2. experiment interpretation is now a real maintenance surface, not just an
   ad hoc notebook exercise;
3. some advanced acceptable-set behavior still lives upstream in `prompt_eval`
   rather than entirely inside this repo.

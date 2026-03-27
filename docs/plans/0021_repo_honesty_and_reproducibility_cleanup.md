# Repo Honesty And Reproducibility Cleanup

Status: active

Last updated: 2026-03-27
Workstream: post-bootstrap operational hardening

## Purpose

Make the proved onto-canon6 workflow operationally honest and reproducible
without changing the long-term capability vision.

This plan is not a new capability track. It is cleanup on the active frontier:

1. repo-command honesty;
2. static-check honesty;
3. reproducible bootstrap setup;
4. canonical proof-artifact clarity.

The goal is that a fresh agent or human can understand what is proved, run the
supported checks, and reproduce the canonical workflow without hidden local
assumptions.

## Acceptance Criteria

This plan is complete only when all of the following are true:

1. `make check` truthfully runs the repo's supported verification surface;
2. shared Make targets match their labels and behavior;
3. repo-local setup does not depend on undocumented sibling-repo assumptions;
4. the canonical proof artifacts are named and documented explicitly;
5. README and plan docs point to the same current execution posture;
6. a fresh operator can run one documented canonical smoke path end to end.

This plan fails if:

1. commands still overclaim what they verify;
2. the repo still requires hidden local environment knowledge to reproduce the
   proved path;
3. proof artifacts remain discoverable only by reading old run notes or
   exploring `var/` manually.

## Current State

The repo already has real proof artifacts, real tests, and clear strategic
docs, but there are still avoidable trust gaps:

1. the Makefile currently hardcodes a workspace interpreter path;
2. `make check` is labeled as test + type check but only runs pytest;
3. `make errors` does not match its help text;
4. static-check expectations are stronger in docs than in the current local
   verification envelope;
5. canonical proof artifacts exist, but the repo does not yet foreground them
   consistently;
6. reproducibility still depends on donor-repo assets and local context that
   should be made explicit.

## Scope

### In Scope

1. Makefile honesty and portability
2. mypy / lint configuration honesty
3. README and plan alignment
4. canonical proof-artifact labeling
5. reproducibility documentation and setup guidance
6. one canonical smoke workflow

### Out Of Scope

1. new extraction capabilities
2. new ontology/runtime capabilities
3. new adapters or consumer surfaces
4. parity-matrix changes beyond wording/alignment

## Work Items

### 1. Makefile Honesty

Fix the shared and domain targets so they do what they say:

1. remove hardcoded home-directory assumptions where possible;
2. make `check` reflect the actual supported verification surface;
3. make `errors` reflect actual error-report behavior;
4. add a setup/bootstrap target if the repo needs one.

### 2. Static-Check Honesty

Resolve the mismatch between declared strictness and the supported local
verification path:

1. either make the current mypy scope pass;
2. or narrow/document the enforced scope explicitly;
3. ensure lint tooling is part of the supported dev setup if it is part of the
   repo contract.

### 3. Reproducibility / Bootstrap Independence

Make donor-repo dependencies explicit and reproducible:

1. document required donor assets and how they are materialized locally;
2. decide which assets are vendored, synced, or operator-provided;
3. ensure the canonical proof path can be followed from a documented setup.

### 4. Canonical Proof Artifacts

Reduce ambiguity about what counts as proof:

1. name the highest-signal DBs / run directories explicitly;
2. document what each artifact proves;
3. prefer archive-and-label over leaving equivalent artifacts mixed together.

### 5. Canonical Smoke Path

Define one operator-facing smoke workflow:

1. input;
2. command(s);
3. expected output;
4. expected summary metrics;
5. where the resulting artifact lives.

## Immediate Priority

The recommended execution order is:

1. README alignment;
2. Makefile honesty;
3. static-check honesty;
4. reproducibility documentation / setup;
5. canonical proof-artifact labeling;
6. canonical smoke path.

## Notes

This plan does not reduce scope. It raises the floor on trust so the preserved
long-term vision rests on a workflow that other agents and consumers can
actually reproduce.

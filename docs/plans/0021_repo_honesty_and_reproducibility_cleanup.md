# Repo Honesty And Reproducibility Cleanup

Status: completed

Last updated: 2026-03-28
Workstream: post-bootstrap operational hardening

## Implementation Outcome (2026-03-28)

This plan is complete.

Delivered:

1. `Makefile` now matches the supported verification surface;
2. `make check`, `make verify-setup`, and `make smoke` are real operator-facing
   entry points;
3. static-check expectations were brought back into alignment with the repo
   contract;
4. canonical proof artifacts are named in `README.md`;
5. setup and smoke-path documentation now match the repo's actual behavior.

Residual work from this area now belongs elsewhere:

1. donor-ownership completion and archive readiness live in Plan 0022 / 0023;
2. ongoing documentation authority and long-term sequencing live in Plan 0024.

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

## Historical Baseline

When this plan opened, the repo already had real proof artifacts, real tests,
and clear strategic docs, but it still had avoidable trust gaps:

1. the Makefile hardcoded a workspace interpreter path;
2. `make check` overclaimed what it verified;
3. `make errors` did not match its help text;
4. static-check expectations were stronger in docs than in the supported local
   verification envelope;
5. canonical proof artifacts existed, but the repo did not foreground them
   consistently;
6. reproducibility still depended on donor-repo assets and hidden local
   context.

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

## Notes

This plan did not reduce scope. It raised the floor on trust so the preserved
long-term vision now rests on a workflow that other agents and consumers can
actually reproduce.

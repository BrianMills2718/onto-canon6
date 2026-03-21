# 0022 - Classify post-bootstrap extraction work as an explicit R&D workstream

## Status

Accepted.

## Context

`onto-canon6` now has two different kinds of work in the repo:

1. the canonical successor core proved through Phases 0-15;
2. newer extraction-focused work around permissive review, ancestor-aware
   evaluation, progressive disclosure extraction, and extraction-quality
   iteration.

That newer work is real. It has code, tests, prompt assets, run logs, and
benchmark results. But it does not yet have the same status as the canonical
successor phase chain:

1. the charter and roadmap still describe Phases 0-15 as the completed
   successor-core path;
2. the canonical notebook journey still keeps extraction fixture-backed for
   stability and proof clarity;
3. the extraction work is moving faster than the stable successor-core story.

Without an explicit classification, the docs drift in an unhelpful way:

1. some surfaces imply a new implicit Phase 16+ chain;
2. other surfaces still describe the repo as Phase-15-complete plus
   adoption-first;
3. readers cannot tell whether extraction R&D is canonical, provisional, or
   simply undocumented drift.

The problem is not that the extraction work exists. The problem is that the
repo needs one truthful way to describe how it fits into the broader plan.

## Decision

`onto-canon6` will classify the current extraction-focused work as an explicit
**post-bootstrap R&D workstream**, not as an automatic continuation of the
successor phase chain.

That means:

1. **Phases 0-15 remain the canonical successor-core roadmap.**
   - Those phases are still the authoritative story for the proved successor
     bootstrap and the conservative notebook journey.
2. **Plans 0014, 0016, 0017, and 0018 form one active post-bootstrap
   extraction workstream.**
   - ADRs 0017, 0018, 0019, 0020, 0021, and this ADR describe that workstream.
   - The workstream is real and active, but it is not silently promoted to a
     new successor phase sequence.
3. **Canonical notebook proof stays conservative until this workstream
   stabilizes more.**
   - Code-and-test proof, run logs, and bounded deep dives are enough to mark
     workstream progress.
   - The canonical journey notebook should only absorb this work after an
     explicit later decision.
4. **Top-level docs must distinguish three things clearly.**
   - successor-core roadmap;
   - active extraction R&D workstream;
   - dated run history / experiment evidence.

## Consequences

Positive:

1. The repo gets one truthful strategic story instead of silently growing a
   second implicit phase ladder.
2. New readers can tell which parts are stable successor core versus active
   extraction iteration.
3. The canonical notebook can remain a conservative proof surface without
   denying that extraction R&D is real.
4. Extraction iteration can move quickly without forcing every result into the
   canonical successor narrative immediately.

Costs:

1. The docs need to carry one more explicit classification layer.
2. Some readers may initially expect the extraction workstream to become a
   formal Phase 16+, and the docs now have to say why it does not.
3. Workstream proof will remain partly code/test/run based rather than folded
   into the canonical notebook story.

## Follow-Up

If the extraction workstream later stabilizes into a durable default workflow,
the next step should be an explicit follow-up ADR that decides one or more of:

1. promote part of the workstream into the canonical notebook journey;
2. treat the workstream as a new successor-roadmap extension;
3. keep it as an ongoing experimental branch intentionally.

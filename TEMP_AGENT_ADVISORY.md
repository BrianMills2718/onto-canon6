# Temporary Agent Advisory (2026-03-25)

> **Delete this file when addressed.** It contains findings from a cross-project
> strategic review that the agent working on onto-canon6 should be aware of.

## Context

A cross-project documentation audit and integration planning session was
completed on 2026-03-25. Several changes were committed to this repo.

## Changes Already Committed

1. **SUCCESSOR_CHARTER.md** — Updated with 4 new guiding principles replacing
   the friction-only philosophy. Key change: document full vision even if
   deferred, never box out long-term architecturally, document uncertainties
   explicitly.

2. **Parity matrix (0005)** — 9 new rows added (6 silently-missing v1
   capabilities + 3 beyond-v1 vision). New "Open Uncertainties" section with
   6 named design questions.

3. **CLAUDE.md Working Rules** — Updated to reflect vision-driven principles.

4. **docs/CONSUMER_INTEGRATION_NOTES.md** — New file documenting research_v3
   as first consumer, integration path, and open questions.

## Things to Know

1. **research_v3 is your first consumer.** It produces Finding objects
   (claim, source_urls, confidence, corroborated, tags). Your extraction
   pipeline will process Finding.claim as evidence text. See
   `docs/CONSUMER_INTEGRATION_NOTES.md`.

2. **A 5-finding integration proof is coming** (ROADMAP step 2.0). After
   both repos stabilize, someone will feed 5 research_v3 findings into
   onto-canon6 and verify the output. Design your extraction pipeline to
   handle short factual claim sentences (1-3 sentences), not just long
   paragraphs.

3. **The parity matrix is now the capability vision ledger.** If you add
   or remove a capability, update the matrix. If you encounter a design
   uncertainty, add it to the Open Uncertainties section.

4. **CLAUDE.md exceeds its own 600-line limit** (currently ~783 lines).
   The "What Was Just Completed" section has ~200 lines of historical
   detail that should be moved to docs/STATUS.md or an archive doc.
   Consider trimming when you have a natural break point.

5. **Extraction quality is the #1 priority.** The 37.5% PSYOP acceptance
   rate is the honest benchmark. The 100% on 5 USSOCOM commanders (n=5)
   is encouraging but not statistically meaningful. Get a corpus-wide
   number on a larger set.

6. **No more phases/ADRs** unless justified by extraction quality friction
   or consumer integration needs.

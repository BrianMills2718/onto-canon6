# Audit Note: 2026-04-02 full chunk-003 strict-omit contract

## Question

Should `psyop_017_full_chunk003_analytical_context_strict_omit` remain a
zero-candidate benchmark case under the current broad extraction goal?

## Evidence

### 1. Repeated prompt-only suppression failed

Plans `0051` through `0053` tried three increasingly narrow prompt-only
approaches:

1. section-level analytical suppression
2. predicate-local gating
3. hard-negative abstract-result and citation suppression

None of them recovered the `expected_candidates=[]` contract for the compact
operational-parity lane. The latest compact-operational-parity execution
(`81cffac9c8df`) still produced six candidates:

1. `oc:limit_capability`
2. `oc:limit_capability`
3. `oc:limit_capability`
4. `oc:create_organizational_unit`
5. `oc:express_concern`
6. `oc:send_report`

### 2. The full chunk aggregates already-modeled local strict-omit families

The fixture already contains narrower local controls for the same residual
families:

1. `psyop_008_jpotf_establishment_not_org_form`
2. `psyop_009_report_narration_without_named_speaker_strict_omit`
3. `psyop_010_limit_capability_without_named_subject_strict_omit`
4. `psyop_011_hearts_and_minds_narration_strict_omit`
5. `psyop_012_ethical_legal_questions_without_local_speaker_strict_omit`
6. `psyop_013_local_context_report_narration_without_named_speaker_strict_omit`
7. `psyop_014_local_context_hearts_and_minds_narration_strict_omit`
8. `psyop_015_local_context_limit_capability_without_named_subject_strict_omit`
9. `psyop_016_local_context_ethical_questions_with_following_scrutiny_strict_omit`

Chunk `017` is not introducing a clean new failure family. It is mainly
re-aggregating several families already represented explicitly elsewhere.

### 3. The full chunk also contains explicit factual content outside the local negatives

Chunk `017` is not pure narration or pure analytical wrap-up. It also contains
sentences like:

1. `the integration of PSYOP into joint and coalition operations allowed for
   unprecedented reach and flexibility`
2. `the use of airborne broadcasting platforms ... contributed to tactical and
   operational successes`
3. `the establishment of USSOCOM and the JPOTF model improved unity of effort`

Those may still be bad fits for the current predicate catalog or current
extraction policy, but they are not obviously "should always yield zero
candidates" prose under a broad extraction goal.

## Audit Result

`psyop_017_full_chunk003_analytical_context_strict_omit` is **not** a clean
negative control anymore. It is a mixed-content aggregate case.

More specifically, it is:

1. a bundle of several already-modeled local strict-omit families; plus
2. additional explicit factual sentences that are not obviously strict omit
   under the broad extraction goal.

So the repo should stop treating the problem as "prompt wording is still not
good enough." The benchmark contract itself is the active blocker.

## Allowed Next Moves

There are four coherent options:

1. **Keep chunk `017` as strict omit and continue hardening the extractor.**
   This is the most conservative benchmark stance, but it keeps forcing the
   model to return zero from a mixed-content full chunk.
2. **Remove or demote chunk `017` as a strict-omit gate and rely on the local
   strict-omit controls (`008`-`016`).**
   This is the cleanest benchmark-design option if the goal is to test the
   negative families directly.
3. **Keep chunk `017`, but convert it from strict omit to an
   `accepted_alternatives` or mixed-allow case.**
   This preserves the full chunk as a stress test without pretending the only
   acceptable answer is zero candidates.
4. **Keep strict omit, but narrow the extraction goal specifically for this
   evaluation lane.**
   This is the most contract-heavy option and should be chosen only if you want
   the benchmark to represent a narrower extraction policy than the current
   broad goal.

## Recommendation

Recommended option: **Option 2 or Option 3**, not more prompt churn.

1. Option 2 if you want the benchmark to stay clean and highly interpretable.
2. Option 3 if you want to preserve full-chunk stress behavior while staying
   truthful about mixed-content text.

## User Decision Boundary

Changing the benchmark contract for chunk `017` requires user sign-off because
it changes what counts as success for the current extraction-quality lane.

The narrow decision needed is:

1. keep `017` as strict omit;
2. remove/demote `017` and rely on `008`-`016`;
3. or convert `017` to a mixed-allow / accepted-alternatives case.

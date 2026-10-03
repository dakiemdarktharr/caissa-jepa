# METHOD SPEC V2.12-05 — root-sampling replacement draft

**Status: unreviewed proposal.** This document proposes a replacement for
§7 of `METHOD_SPEC_V212.md` v04. Read §§1–6 and §8 of v04 unchanged, together
with this replacement §7. This file does not supersede the reviewed v04, does
not freeze a schedule, and does not authorize synthetic calibration, root
generation, scoring, fitting, matches, or outcome access. Independent method
and statistical review is required before any such gate can advance.

## 7. Development estimand, metrics, and nomination gate

### Target population and sampling unit

For each held-out-size variant, Connect Four 8×8/k4 and Reversi8, target the
distribution of the first eligible nonterminal root reached by a pinned
policy-mixture rollout from the exact initial state, conditional on that
candidate slot reaching its assigned occupancy band at or after four legal
plies. The three fixed bands are `[0,1/3)`, `[1/3,2/3)`, and `[2/3,1)` of
occupied board cells divided by board area; Reversi's four initial discs count
as occupied. A forced pass is a legal ply and leaves occupancy unchanged.

This is a success-conditional first-passage target. It is not uniform over all
reachable states, unique boards, or natural game occupancy. The sampling unit
is a candidate-slot ID. Repeated raw or symmetry-canonical states remain
separate draws. The proposed interpretation of v04's minimum of 40
independently generated situations is 48 slot observations per variant, 16
within each band; independent review must accept this interpretation.

### Frozen candidate schedule

Before any candidate state is generated, freeze 64 candidate slots for each
variant × band (192 per variant). Each slot has a unique ID and deterministic,
independent policy-draw and action RNG streams derived from the protocol seed,
variant, band, and slot ID using the pinned NumPy `SeedSequence` version. Pin
the rules, adapters, four policy implementations/configurations, protocol,
RNG implementation, and source hashes. For each slot, draw an ordered policy
pair uniformly from the 16 ordered pairs of the four pinned policies and keep
it fixed through the rollout. Replay exact legal actions from the initial
state and stop at the first eligible root. Record terminal-before-band,
invalid transition, and no-eligible-root slots with a reason.

Within each band, accept the first 16 valid slots in slot-ID order, regardless
of repeated board identity. Do not deduplicate, reweight, adapt, replace, or
top up. If any band has fewer than 16 valid slots among its 64 candidates,
this draft proposes failing the complete two-variant schedule before any
scoring. This global stop is a fail-closed proposal, not an accepted rule;
independent reviewers must reconcile it with design 02's earlier
variant-schedule wording. Report the candidate and accepted policy-pair/prefix
mix, raw and symmetry-canonical multiplicity, and every rejection reason
without changing the target after inspection.
Before scoring, freeze and hash every accepted root receipt, the full
rejection ledger, and the paired seat-assignment schedule. Receipts retain
the exact state, player to move, prefix actions including pass 64, slot ID and
seed derivation, policy pair, occupancy, prefix length, and source/rules/
protocol fingerprints.

The IID argument applies only if slots are IID within variant × band,
eligibility depends only on that slot's frozen criteria, and no adaptive retry
or rejection depends on prior slots, board identity, scores, or outcomes.
Deterministic stream splitting is a reproducible PRNG approximation to this
assumption, not proof of physical independence. Report the realized
success-conditional policy/prefix mixture; do not reweight it to the nominal
policy-pair probabilities.

### Primary metric and resampling proposal

Retain the v04 primary outcome: paired candidate-minus-control head-to-head
game score, averaged over both seat assignments within each seed/slot cell,
for every candidate and each of the five controls. The proposed variant
contrast is the fixed equal-weight mean of its three occupancy-band
contrasts. The macro contrast is the equal-weight mean of the two variant
contrasts. This explicitly targets an equal occupancy-band mixture and equal
variant macro; it does not estimate natural occupancy-frequency performance.

Retain 20 model seeds, the 15 candidate-versus-control contrasts, 10,000
bootstrap replicates, familywise 95% max-|T| intervals, centered one-sided
tests, and Holm adjustment, subject to independent review of this changed
design. In every replicate, draw one model-seed multiset jointly across arms,
variants, and bands. Separately resample the 16 slot IDs with replacement
within each variant × band, preserving candidate/control pairing and both
seat assignments. Combine band contrasts with fixed one-third weights and
variant contrasts with fixed one-half weights. Freeze the public bootstrap
seed and implementation hash before scores are read.

For contrast `i`, let `delta_i` be the observed paired contrast and
`delta_i^b` its value in bootstrap replicate `b`; let `SE_i` be the bootstrap
standard deviation. Compute
`T_b = max_i |(delta_i^b - delta_i) / SE_i|`, and use the 95th percentile
`q` of `T_b` for simultaneous intervals `delta_i ± q SE_i`. Also report
ordinary percentile intervals as descriptive only. For each positive-effect
test, compute the centered one-sided value
`p_i = (1 + count(delta_i^b - delta_i >= delta_i)) / (B + 1)`
and apply Holm step-down across all 15 tests. A zero `SE_i`, incomplete cell,
nonfinite replicate/statistic, or failed yield invalidates the complete
inferential gate; no contrast may be dropped or regularized after outcomes.

The proposed intervals and p-values are not calibrated by the cited sources
for this small crossed, stratified design. An independent statistical
reviewer must decide whether design-matched synthetic calibration is required
and, if so, freeze scenarios, numerical acceptance tolerances, Monte Carlo
precision, and failure consequences before any simulation. This draft does
not authorize such a simulation.

Any root-yield failure, incomplete cell, zero bootstrap SD, or nonfinite
replicate/statistic invalidates the inferential gate and stops nomination;
never drop or regularize a contrast after seeing scores. If accepted, retain
the v04 nomination margins and conditions unchanged: paired mean at least
+0.05 per variant and macro against every control, every familywise interval
wholly positive, every Holm-adjusted one-sided p-value below 0.05, complete
comparisons, no forfeits, and all compute caps passed. Report every comparison
and failed observation. A failed gate stops this objective family; do not
alter the metric, schedule, budget, or exclusion rules after outcomes.

Retain v04's secondary metrics, opponent-suite reporting, and all §8 pre-fit
gates. Development outcomes remain non-confirmatory. If a candidate is
nominated, locked confirmation must use fresh situations and generation
seeds disjoint from development, with its own preregistered schedule. Preserve
v04's rule that timeouts and invalid moves are losses/forfeits, never replaced
or censored; any forfeit blocks nomination. This proposal does not establish
performance, superiority, equilibrium, exploitability, transfer, novelty, or
Q1 readiness.

## Open review disposition

Before root generation, independent reviewers must accept the target and
minimum-sample interpretation, policy/RNG and eligibility contract, fixed
yield/failure semantics, seat and bootstrap pairing, and all familywise
failure rules. The independent statistical reviewer must explicitly decide
whether the design-matched calibration is required. The current review record
and unresolved items are in `docs/V212_ROOT_SAMPLING_REVIEW_01.md`.

# V2.12 root-sampling and inference design review 01

**Disposition: coherent proposal only as a versioned estimand/method change.
Not compatible with the currently reviewed v04, not a statistical calibration
result, and not authorization to generate roots, score models, simulate
coverage, fit, or run matches.** This static review compared `METHOD_SPEC_V212.md`
§§7–8 with the root-sampling amendment, design 02, and the inference audit on
2026-10-04. No simulations, roots, scores, or outcomes were produced or read.

## Findings

The first-valid-slot argument has no identified mathematical flaw under its
stated assumptions: slots are IID within variant × occupancy band; eligibility
uses only that slot's frozen rules and root criteria; and there is no adaptive
retry or rejection by board identity, prior slots, scores, or outcomes. Under
those assumptions, the first 16 valid receipts, conditional on at least 16
valid slots among the fixed 64, are IID draws from the slot-level
success-conditional distribution. Repeated boards therefore remain distinct
sampling units. Deterministic per-slot PRNG streams make the design reproducible
but only operationally approximate independent random draws.

The proposal changes v04 §7 in material ways. It replaces the broadly stated
reachable-situation target with first-passage roots conditional on reaching an
occupancy band after four legal plies; replaces situation IDs with candidate
slot IDs; introduces 16 slots per band and equal occupancy-band weights; and
changes the bootstrap to resample slots separately within variant × band.
The resulting target is neither uniform over reachable states nor over unique
boards, and equal occupancy-band weighting is not natural game occupancy
frequency. Describe it as an **equal occupancy-band mixture**, not an equal
phase mixture, unless cross-game phase comparability is separately justified.

The stratified crossed bootstrap preserves the proposed seed/root pairing,
seat assignments, and fixed weights. That structural alignment does not
establish finite-sample coverage, familywise error control, or calibration of
the max-|T| intervals and centered one-sided p-values with 20 seed clusters
and 16 slots per band. Ten thousand replicates address only Monte Carlo error
in the bootstrap approximation. The reviewed sources do not validate this
procedure for the proposed outcome distribution; Holm adjustment cannot
repair invalid input p-values.

## Decisions required in a v05 proposal

Before any root generation, a versioned method draft must explicitly replace
v04 §7 and freeze:

1. The success-conditional first-passage target; 16 candidate-slot observations
   per occupancy band; the meaning of the ≥40 independent-situation minimum
   when repeated states are separate slot draws; fixed equal occupancy-band
   weights and equal variant macro weights; policy-mixture and seat semantics;
   minimum ply, terminal and forced-pass rules; and whether any failed band
   invalidates the entire schedule without replacement or top-up. V05 currently
   proposes a global stop across both variants, stricter than design 02's
   original per-variant stop; reconcile and explicitly accept or revise that
   choice.
2. The four pinned policies and all ordered-pair probabilities; rules,
   adapter, policy, configuration, and protocol fingerprints; PRNG algorithm
   and version; deterministic independent per-slot stream derivation; the
   exact 64-slot bound; accept-first-16-valid ordering; full rejection ledger;
   and pre-score freeze of the accepted schedule and seat assignments. Any
   adaptive retry or state-identity/outcome rejection invalidates the IID
   argument.
3. Whether a design-matched synthetic calibration is required. If required,
   freeze its data-generating scenarios and numerical acceptance tolerances
   before simulation, covering global and partial nulls, simultaneous
   interval coverage, seed/root effects and seed × root interactions,
   discrete/tied outcomes, slot-yield conditioning, cross-contrast dependence,
   power/width near the +0.05 nomination boundary, and Monte Carlo precision.
   State what failure means for the method or sample size. A/A-only checks are
   insufficient.
4. All 15 contrasts, pairing, bootstrap weights, familywise procedure, and
   fail-closed rules for root-yield failure, missing cells, zero bootstrap SD,
   or nonfinite replicates. Carry forward v04's non-confirmatory development
   status, fresh/disjoint locked-confirmation situations and seeds, and
   no-replacement/no-censoring loss treatment of timeouts and invalid moves.
   Review the exact implementation hash after these choices are frozen.

Until a qualified independent statistical review accepts the versioned
method and disposes the calibration question, v04 remains the current method
and no root or score may be produced under the draft proposal. The separate
v04 §8 novelty, trajectory/split, compute, and pre-fit gates remain unchanged.
Any new OOM fault injection remains subject to separate explicit
authorization.

## Sources reviewed

- `METHOD_SPEC_V212.md` §§7–8.
- `docs/METHOD_SPEC_V212_ROOT_SAMPLING_AMENDMENT_DRAFT_01.md`.
- `docs/V212_DEV_ROOT_SCHEDULE_DESIGN_02.md`.
- `docs/V212_ROOT_SAMPLING_INFERENCE_AUDIT_01_DRAFT.md`.

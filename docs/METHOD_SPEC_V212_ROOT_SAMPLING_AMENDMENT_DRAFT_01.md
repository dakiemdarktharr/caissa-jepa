# V2.12 root-sampling and bootstrap amendment — draft 01

**Status: proposal for independent review only.** This document proposes
changes to the held-out development-root schedule and its resampling rule. It
does not amend `METHOD_SPEC_V212.md`, replace root schedule design 01, freeze
an evaluation schedule, or authorize root generation, scoring, fitting, match
play, or outcome access.

## Motivation

`METHOD_SPEC_V212.md` §7 describes at least 40 independently generated
reachable situations per held-out variant and resamples situation ids in its
crossed bootstrap. `V212_DEV_ROOT_SCHEDULE_DESIGN_01.md` instead proposes 64
candidate slots per occupancy band and keeps the first 16 symmetry-unique
roots. Rejection based on previously accepted state identity makes the
accepted set dependent and changes the induced policy/prefix mixture. The
development estimand and bootstrap unit therefore need to be stated together.

## Proposed target population and sampling unit

For each held-out variant (Connect Four 8x8/k4 and Reversi8), define three
fixed occupancy strata `[0,1/3)`, `[1/3,2/3)`, and `[2/3,1)`. Within a stratum,
the target is the distribution of the first eligible root reached by a
predeclared policy-mixture rollout from `game.initial()`, conditional on the
candidate slot producing a nonterminal root in that stratum at or after four
legal plies. It is a policy-induced first-passage distribution, not a uniform
sample of all reachable states or a uniform sample of unique board positions.

The independent sampling unit is a candidate-slot id, not a unique board
identity. A slot has its own predeclared policy-draw and action RNG streams,
derived from the frozen protocol seed, variant, occupancy band, and slot id.
The ordered policy pair is drawn independently and uniformly from the four
pinned families for each slot and remains fixed through that rollout. Its
validity predicate depends only on exact rules and the declared root criteria,
never on a model score or outcome.

## Proposed bounded schedule

1. Freeze 64 candidate slots per variant and band, with the exact RNG version,
   seed derivation, game/policy source hashes, and slot IDs, before generating
   any candidate state.
2. In each slot, stop at the first nonterminal state at ply four or later whose
   occupancy lies in that slot's assigned band. Record terminal-before-band,
   invalid transition, or no-eligible-root as an invalid slot with its reason.
3. Accept the first 16 valid slots in schedule order within each band,
   regardless of repeated raw or canonical board states. Keep slot IDs distinct
   and report raw/canonical state multiplicities by band, policy pair, and
   prefix length; do not deduplicate, reweight, or top up.
4. If any band has fewer than 16 valid slots among its fixed 64, fail the
   schedule before model scoring. Do not add seeds, slots, or replacement roots.
5. Freeze and hash all 48 accepted slot receipts, the complete rejection
   ledger, and the seat-assignment schedule before scoring. Receipts retain
   exact state, player to move, prefix actions (including pass 64), slot seed,
   policy pair, occupancy, prefix length, and rules/protocol/source hashes.

### Conditional-IID argument and assumptions

Within one variant and occupancy stratum, let candidate slots be independent
and identically distributed draws. For slot i, let V_i indicate that its
predeclared rollout produces an eligible root, and let X_i be the resulting
root receipt when V_i=1. The validity rule may use only the frozen rules and
root criteria; it must not depend on board identity relative to other slots,
model scores, or outcomes.

Conditional on a slot being valid, its receipt has distribution
P(X_i | V_i=1). The sequence of valid receipts in schedule order has this same
distribution independently slot by slot: the validity indicators determine
which slot indices are selected, while each selected receipt is drawn from
the same conditional law. Conditioning on at least 16 valid slots among the
fixed 64 changes the chance that the stratum passes the yield gate, but does
not change the conditional law of those first 16 valid receipts, because that
gate depends only on validity indicators. Thus the accepted 16 are IID draws
from P(X | V=1), conditional on passing the predeclared stratum yield gate.

This conclusion requires independent slot-level random streams and an
identical candidate-generation law within each stratum. In implementation,
freeze and record the RNG algorithm/version, root seed, deterministic
variant/stratum/slot seed derivation, and source hashes; deterministic
SeedSequence streams make the procedure reproducible but are an operational
pseudo-random approximation to the independent-draw model, not a proof of
physical randomness. A shared or stateful stream, adaptive retry, rejection
based on duplicate identity, scores, outcomes, or earlier accepted states, or
post hoc changes to the validity rule breaks the stated sampling argument.
The argument is within-stratum: it does not make the three occupancy strata
interchangeable or imply uniformity over reachable or unique boards.

Repeated states are repeated draws and remain separate sampling units. Because
policy family can affect whether and when a slot reaches its band, the
accepted policy-pair mixture may differ from the nominal uniform draw; report
that induced mix without reweighting. Condition inference on the predeclared
bounded schedule and its all-strata yield rule. This is a design argument for
review, not empirical verification of a generator or approval to run it.

## Proposed estimand and crossed bootstrap

For each held-out variant, the primary contrast is the equal-weight mean of
the three occupancy-stratum contrasts. The macro contrast remains the
equal-weight mean of the two variant contrasts. This deliberately targets an
equal phase mixture; it does not estimate performance under the natural
occupancy frequency of complete games or under a named opponent.

Retain METHOD_SPEC §7's 20 model seeds, five controls, paired seat assignments,
15 candidate-control contrasts, 10,000 bootstrap replicates, max-|T| familywise
intervals, centered one-sided tests, and Holm adjustment, subject to review of
this amendment. Change the situation resampling step as follows:

- Draw one resampled multiset of model-seed ids and share it across both
  variants, all strata, and all paired arms.
- Separately within each variant and occupancy stratum, resample the 16
  accepted candidate-slot ids with replacement. Retain every candidate/control
  and seat-assignment pairing within each seed/slot cell.
- Compute each variant contrast as the fixed one-third weighted mean of its
  three stratum contrasts, then macro as the fixed one-half weighted mean of
  the variants. Calculate all familywise statistics and p-values over the
  existing 15 contrasts without dropping a stratum or an incomplete cell.

The exact public bootstrap seed and implementation hash must be frozen before
scores are read. Any zero-variance contrast, missing cell, nonfinite replicate,
or failed root-yield stratum invalidates nomination, as in §7. The original
unstratified situation-id bootstrap is not interchangeable with this
stratified estimand.

## Statistical-method references and scope

Owen's pigeonhole bootstrap separately resamples row and column units for
crossed data and establishes a mean-consistency result under heteroscedastic
crossed random-effects models. This is a method analogue for paired model-seed
and root-slot dimensions; it does not validate the proposed finite-sample
coverage, max-|T| intervals, centered p-values, or Holm family for this
20-seed/16-slot-per-stratum design. See [Owen (2007)](https://arxiv.org/abs/0712.1111).

Preston develops a rescaled bootstrap for stratified multistage survey designs
and emphasizes reproducing the sampling structure within strata. That work
uses finite-population sampling without replacement and is not the procedure
proposed here; it supports preserving the fixed occupancy strata as a design
feature, not direct transplantation of its weights or validity results. See
[Preston (2009)](https://www150.statcan.gc.ca/n1/pub/12-001-x/2009002/article/11044-eng.pdf).

MacKinnon, Nielsen, and Webb derive conditions for asymptotic t-statistic
validity under two-way cluster-robust variance estimation in regression
models. Those conditions are a reminder that crossed resampling validity is
design- and dependence-specific; their results do not establish this
candidate/control score bootstrap. See [MacKinnon, Nielsen, and Webb
(2021)](https://doi.org/10.1080/07350015.2019.1677473). MacKinnon and Webb
document few-treated-cluster problems for cluster-robust and wild-bootstrap
inference in linear treatment models. This is a different setting, so it is
cautionary context rather than a direct result about the CAISSA design. See
[MacKinnon and Webb (2018)](https://doi.org/10.1111/ectj.12107).

Neither source establishes coverage for CAISSA-JEPA's paired outcomes,
conditional first-passage slot distribution, small number of model seeds,
familywise max statistic, or nomination thresholds. Those remain open for
independent statistical review. Increasing to 10,000 bootstrap replicates
reduces Monte Carlo error in the estimated resampling distribution; it does
not increase the number of independent seed/root sampling units or by itself
establish finite-sample coverage.

## Required review and limits

Independent statistical and method review must decide whether the
success-conditional first-passage population and equal-band weighting answer
the intended development question; whether retaining duplicate states as
independent slot draws is acceptable; whether 64 fixed slots have sufficient
yield; and whether the proposed stratified crossed bootstrap is valid for the
paired design. If any choice changes, issue a new version before root
generation. The existing root schedule and METHOD_SPEC v04 remain unchanged
until that review and all other gates pass.

Even if accepted and executed, this is an exploratory development screen. It
does not support confirmatory inference, superiority, generalization outside
the declared game/variant/sampling distributions, or Q1-readiness claims.

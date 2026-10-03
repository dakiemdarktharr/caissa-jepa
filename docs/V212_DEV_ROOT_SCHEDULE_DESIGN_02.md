# V2.12 held-out development root schedule — design 02

**Status: proposal for independent review only.** This draft supersedes
`V212_DEV_ROOT_SCHEDULE_DESIGN_01.md` as the candidate schedule, but does not
freeze a protocol or authorize root generation, scoring, matches, outcome
access, or training. Design 01 remains in the repository as the record of the
earlier unique-root proposal.

## Target and estimand

Use 48 accepted slot observations per held-out-size variant: Connect Four
8x8/k4 and Reversi8. Generate a fixed 192-candidate schedule per variant
(64 slots in each band), accepting 16 valid slots from each of three fixed
board occupancy bands: `[0,1/3)`, `[1/3,2/3)`, and `[2/3,1)`. Occupancy is occupied
board cells divided by board area; Reversi's four initial discs count as
occupied. A forced pass advances the legal-ply count but leaves occupancy
unchanged.

Within a variant and band, the target is the distribution of the first
eligible root reached by a predeclared policy-mixture rollout from
`game.initial()`, conditional on that slot reaching a nonterminal state in
the assigned band at or after four legal plies. This is the
success-conditional first-passage distribution described in
`METHOD_SPEC_V212_ROOT_SAMPLING_AMENDMENT_DRAFT_01.md`. It is not uniform over
all reachable states or over unique board positions. The 48 observations meet
the method's minimum of 40 situations only if independent review accepts
candidate-slot independence and this conditional target as the meaning of
independently generated situations.

## Fixed candidate schedule

For each variant and occupancy band, predeclare exactly 64 slots. Each slot
has a unique ID and independent deterministic policy-draw and action RNG
streams derived from a frozen protocol seed, variant, band, slot ID, and the
pinned NumPy `SeedSequence` version. Freeze source hashes for rules, adapters,
policies, protocol, and RNG implementation before generation.

For each slot, draw an ordered pair of policy families independently and
uniformly from the four pinned families; hold that pair fixed through the
rollout. Replay legal actions from the initial state and stop at the first
nonterminal state at ply four or later in the assigned occupancy band. Do not
continue the rollout to a terminal outcome or create an outcome label. Record
terminal-before-band, illegal/invalid transition, and no-eligible-root as
invalid-slot reasons. Pass action 64 is a legal ply when the Reversi rules
require it.

Within each band, accept the first 16 valid slots in slot-ID order,
irrespective of repeated raw or symmetry-canonical board states. A repeated
board is a repeated draw, not a rejected slot. Do not deduplicate, reweight,
top up, adapt the policy mixture, widen bands, or replace roots. If any band
has fewer than 16 valid slots among its fixed 64, fail the entire variant
schedule before scoring and preserve the complete candidate/rejection ledger.

The schedule therefore yields 48 accepted slot IDs per variant, or 96 across
both variants. Before scoring, freeze and hash all candidate outcomes, invalid
reasons, accepted root receipts, seat assignments, and source/protocol
fingerprints. Each receipt records exact board and player to move, occupancy,
prefix actions and legal-ply length, policy pair, slot seed identifiers, and
the rules/code/policy/protocol hashes. Replaying each prefix must reproduce
the exact nonterminal root.

## Sampling argument and reporting

Under the idealized model of IID candidate slots within a variant/band, slot
validity depends only on that slot's frozen root criteria, and selected root
receipts are IID from the success-conditional distribution. Requiring at least
16 valid slots among 64 is a yield gate based only on validity indicators; it
does not alter the conditional receipt law of the first 16 valid slots.
Independent slot RNG streams and an identical candidate-generation law within
each stratum are required. Deterministic PRNG stream splitting is a reproducible
operational approximation to independent draws, not a proof of physical
randomness. Adaptive retries or rejection based on earlier states, duplicate
identity, scores, or outcomes invalidate this argument.

Report raw repeated-state multiplicities by variant, band, policy pair, and
prefix length; keep every slot ID distinct. Report symmetry-canonical
multiplicities only after adapter property checks prove that each declared
mapping gives a legal-action bijection and commutes with exact transitions.
Canonical uniqueness is diagnostic here and never an acceptance rule. Report
the realized policy-pair and prefix-length mix among all 64 candidates and
among the first 16 valid slots. Because policy family can affect validity and
first-passage time, the accepted policy-pair mix can differ from the nominal
uniform draw; do not reweight it.

## Scoring and inference alignment

Pair every accepted slot with every model seed and each candidate/control
comparison under both seat assignments, retaining the same slot identity and
all paired cells. The proposed variant contrast is the fixed equal-weight
mean of the three occupancy-band contrasts; the macro contrast is the
equal-weight mean of the two variant contrasts. The matching bootstrap proposal
resamples model seeds jointly across arms/variants and slot IDs with
replacement separately within each variant/band, retaining all pairing.

This is a review proposal to align the schedule with the estimand and bootstrap
in Amendment Draft 01. It does not establish finite-sample coverage, power,
max-T/Holm validity, or nomination thresholds. Missing cells, nonfinite
statistics, failed yield, and other failure rules must be resolved in the
versioned method/protocol review before scoring.

## Required independent review and limits

Reviewers must decide whether:

1. the success-conditional first-passage population and IID slot IDs satisfy
   the method's minimum of 40 independently generated situations;
2. the fixed 16-per-band allocation and equal one-third band weights match the
   intended development estimand;
3. independent deterministic SeedSequence streams adequately instantiate the
   slot-independence assumption, with exact seed derivation and source hashes;
4. retaining repeated board states is preferable to a unique-state estimand and
   which canonical multiplicity checks are valid after adapter property tests;
5. the 64-slot yield rule, candidate failure taxonomy, and pre-score receipt
   freeze are complete and fail closed; and
6. the proposed crossed, stratified resampling and all failure rules are
   compatible with the frozen method.

Until those questions are accepted in a versioned independent protocol review,
design 02 remains unapproved, design 01's unique-root rule is not operative as a
replacement, and no roots may be generated. Passing this design review would
permit only the separately reviewed implementation work specified by the
generation protocol. It would not establish feasibility, statistical power,
performance, superiority, confirmatory readiness, or permission to fit.

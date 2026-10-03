# V2.12 held-out development root schedule — design 01

**Status: proposal for review only.** This schedule is not frozen and does not
authorize root generation, scoring, matches, or outcome access.

## Proposed evaluation bank

Use 48 unique nonterminal root situations per held-out-size variant: Connect
Four 8x8/k4 and Reversi 8x8. Allocate 16 roots to each of three occupancy
bands so early, middle, and late states are represented before any model score
is observed. This is a development screen under METHOD_SPEC_V212 §7, not a
power calculation or a confirmatory sample.

Define occupancy as the count of occupied board cells divided by board area;
Reversi's four initial discs count as occupied. Bands are `[0,1/3)`, `[1/3,2/3)`,
and `[2/3,1)`. Root phases are based on the reached board state, so a forced
pass advances the exact legal trajectory but does not change its occupancy
band. A root must be nonterminal, exactly reachable from `game.initial()`, and
at least four legal plies from the initial state. The minimum-ply rule excludes
the identical initial position from every early-band slot while preserving
early reachable situations.

## Candidate proposal schedule

For each variant and occupancy band, predeclare 64 candidate rollout slots.
Derive independent deterministic policy-draw and action RNG streams from a
versioned protocol seed, variant id, band id, and slot id using the pinned
NumPy `SeedSequence` implementation. For each slot, draw an ordered pair
independently and uniformly from the four pinned policy families, keep the pair
fixed for that rollout, and replay exact legal actions from the initial state.
The candidate root is the first nonterminal state at ply four or later whose
occupancy is in the assigned band. Stop that rollout at the candidate root; do
not continue to a terminal result or create an outcome label.

Accept the first 16 unique candidate roots in schedule order within each band.
Root identity is the game/rules-bound, side-to-move-normalized key modulo all
declared spatial symmetries. A terminal-before-band, invalid transition, or
duplicate canonical root is rejected and counted with its candidate slot and
reason. Do not choose based on a model score. If any band has fewer than 16
unique roots among its 64 fixed slots, fail the schedule and review a new
version; do not add seeds or widen bands after seeing scores.

Because acceptance is first-in-schedule among valid unique states, it can
change the realized policy-pair and prefix-length mix relative to the proposal
draws. Report candidate and accepted/rejected counts by ordered policy pair,
band, source-prefix length, root player, and rejection reason. Freeze and hash
these summaries before scoring; do not reweight accepted roots to equalize the
realized mixture after inspection.

Each accepted root receipt stores its exact board, player to move, source seed,
ordered policy pair, prefix actions (including Reversi pass action 64), prefix
length, occupancy, canonical key, rejection accounting for earlier slots, and
the rules/code/policy/protocol hashes. Replaying the prefix must reproduce the
state exactly and verify that it is nonterminal and legal. Freeze and hash the
48-root schedule and the paired seat-assignment table before evaluation.

## Pairing and use

For every model seed, root situation, and each of the five controls, evaluate
both candidate/control seat assignments using the exact same root state and
search budget. The side to move and absolute board colors remain fixed; the
seat assignment swaps which agent controls each absolute player. Retain every
forfeit, timeout, and invalid action under METHOD_SPEC §7. These roots are used
only for development/model selection on held-out sizes. They are not fit data
and cannot be reused in locked confirmation.

## Review questions and failure semantics

Review whether the fixed 48-root bank and three equal occupancy bands provide
the intended development coverage, and whether 64 candidate slots per band
are an acceptable no-outcome generation bound. Confirm whether Reversi phase
should use occupancy rather than ply, whether role-normalized symmetry is the
right uniqueness key, and whether stopping at the first state in a band is a
defensible root distribution. If any choice changes, version this proposal
before generating roots.

Passing root generation would establish only a reproducible reachable-root
schedule. It would not establish training-data sufficiency, performance,
statistical power, superiority, or confirmatory readiness. Locked-confirmatory
root generation remains a separate post-nomination gate.

Independent review accepted the four-ply minimum as removing the identical
initial-root failure and accepted pre-score reporting of the induced policy and
prefix mix. Review disposition is design-only: whether 64 slots yield 16 unique
roots in every band, the band definitions, and the symmetry key remain
unverified. Do not freeze or generate from this proposal until those choices
are resolved in the protocol review.

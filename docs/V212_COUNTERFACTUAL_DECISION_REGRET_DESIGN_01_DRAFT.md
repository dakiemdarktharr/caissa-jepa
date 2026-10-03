# V2.12 counterfactual decision-regret design 01 — draft

**Status: protocol design proposal for independent review only.** This draft
makes the action-score and regret terms operationally explicit. It does not
amend METHOD_SPEC_V212-04, freeze an estimand, authorize model scoring, data
or root generation, training, matches, or outcome access. The reference depth,
leaf evaluator, sampling schedule, and compute allocation remain unselected.

## Question and interpretation

For a prehashed set of reachable roots, does an arm's action chosen from its
complete legal root set retain value under one common, exact-rule bounded
max-min reference? This is a decision diagnostic, separate from game score,
playing strength, or representation similarity. “Regret” below means regret
against the declared reference only. Call it exact game-theoretic decision
regret only on positions solved to terminal under exact minimax. A depth-limited
reference with a heuristic is not optimal play and must be named
**bounded-reference regret**.

## Scores and primary diagnostic

For root state s, root player p, legal root action a, and fixed reference
configuration c, define Q_ref(s,a;c) as the root-perspective value after
playing a and then applying deterministic max/min backup under exact rules
through the declared reference horizon. Terminal values use the absolute
winner exactly. A nonterminal horizon leaf uses the pinned reference evaluator
h_ref(s_leaf,p) with its exact player-perspective conversion. Configuration c
binds the horizon, evaluator source hash and settings, action order,
terminal/pass treatment, and exact or bounded-search label.

For model arm m, define Q_m(s,a) under the frozen method's own four-ply
planner, model and leaf head. For every legal root action, search that action
independently with a full window (or use a separately verified equivalent
that returns an exact fixed-depth value). Do not carry an incumbent root alpha
from a previous root action into this diagnostic and then treat a fail-low
upper bound as a point score. The selected model action is
a_m(s)=argmax over a in Legal(s) of Q_m(s,a), using the spec's predeclared
legal action order for ties.

When all reference root-action values are exact under configuration c,
report per-root

    R_m(s;c) = max_{a in Legal(s)} Q_ref(s,a;c)
               - Q_ref(s,a_m(s);c).

The reference values are in root-player utility, so this quantity is
nonnegative and bounded by the reference value range. Also report reference
action-ranking agreement across the complete legal set, with ties handled by
Kendall's tau-b or another metric selected before scoring. Keep raw regret and
ranking separate; neither can be inferred from latent distance or factual
prediction error. Aggregate per root first, then by predeclared variant and
seat with the locked weighting. Do not pool root actions as if they were
independent root observations.

## Completeness, alpha-beta bounds, and failures

Every legal root action belongs in the denominator. The score ledger contains
one row per protocol, root, arm, and root action with root fingerprint, actor,
legal-set fingerprint, model/reference config hashes, score, score status,
search window/bound provenance, completed depth, node visits, exact transition
calls, model calls, elapsed time, and stop reason. Allowed statuses are
exact, upper_bound, lower_bound, and missing. Full-window completed fixed-depth
alpha-beta yields an exact score for that root action under the specified leaf
evaluator; a bound or missing score must never be converted to a point estimate.

A root's regret is not_estimable if any legal action needed for the model's
selected action or the reference maximum lacks a point-exact value. Pairwise
ranking is reported only when bounds establish the order; otherwise it is
unresolved. If any arm stops before scoring every required root action, retain
the failure row and do not shrink the denominator or substitute an easier
root. Report coverage and missing reasons next to every aggregate. Any
cap-stressed diagnostic needs its own predeclared compute allocation; it may
not silently borrow or alter the frozen head-to-head budget.

## Reference construction and leakage boundary

Use exact terminal minimax only on a declared tractable subset. For other
positions, a fixed bounded-depth reference must pin h_ref, source hash,
search depth, rules, tie-breaking, root-player conversion, and any pruning
settings before models are scored. Keep exact-solved and bounded-reference
results in separate strata and do not label the latter optimal, ground truth,
or full-game value. If a common reference cannot score the full legal root
set within its frozen procedure, mark that root not estimable for regret;
do not tune depth per root after seeing predictions.

Reference values are evaluation-only. Do not use them as training labels,
select support buckets, choose checkpoints, or tune the method. Any training
use requires a new method version, a provenance/split audit, and separate
independent review. Held-out board-size roots remain structurally
not-comparable for exact state-action fit support; retain that label.

## Current implementation audit and non-retroactivity

The current compute-only run_root_arm in
[two_player/v212_pilot.py](https://github.com/dakiemdarktharr/caissa-jepa/blob/main/two_player/v212_pilot.py)
uses a shared incumbent alpha across root actions, retains an
iteration_values map only for action selection, and does not put root action
values in its return record. Later root-action values can therefore be
fail-low bounds rather than exact scores. The v02 random-weight pilot also
explicitly records no selected actions or values. Its frozen receipt cannot be
used retroactively to calculate action regret; do not edit or rerun that
hash-bound pilot to manufacture these diagnostics.

A future diagnostic implementation must be separately versioned, preserve
the existing compute-only receipt contract, and receive protocol and
implementation review before any model scoring. It must test terminal roots,
forced Reversi passes, ties, full-window exactness versus a tiny exhaustive
oracle, bound/missing handling, and per-action cap interruption using
synthetic in-memory fixtures only. These are proposed checks, not tests run by
this draft.

## Open decisions before freeze

Independent review must resolve the reference depth and heuristic, whether any
positions can be exactly solved within the declared compute allocation, the
relationship between this diagnostic cap and the primary match cap, root/seat
weighting, ranking metric and tie tolerance, and whether this is secondary or
co-primary. Then version the method/protocol and freeze code/config hashes and
analysis before scoring. No metric threshold or nomination rule is supplied
here, and this draft does not establish that the remaining benchmark question
is novel or that any JEPA arm will perform better.


## Existing exact-regret precedent and scope

The repository's older exploratory evaluator provides a bounded-scope
implementation precedent. In two_player/evaluate.py, plan() enumerates every
legal root action, computes a two-ply max-min score, retains a completion
status, and reports regret only when the decision is complete. Its separate
reference values come from two_player/games.py::exact_value: a memoized,
full-game terminal minimax solver. That module's registered GAMES are
tic-tac-toe, 4x4 connect3, 4x4 reversi, and a held-out 3x4 connect3. The
exact_value docstring explicitly calls it an unbudgeted tiny-game oracle and
requires callers to restrict state-space size.

This is useful as a semantic/test precedent for complete legal-action
denominators, root-player value conversion, and withholding regret for
incomplete planning. It is not a ready oracle for V2.12's Connect Four 6x7,
Connect Four 8x8, Reversi6, or Reversi8 variants. The V2.12 random-weight
runner instantiates those four larger games separately and does not return
root-action scores. No V2.12 bounded reference heuristic or source/config hash
was found in the inspected runner/game path. Do not call the unbudgeted
exact_value solver on large variants without a separately reviewed,
fail-bounded feasibility design.

A defensible reference plan may retain full-game exact values only for a
predeclared tractable-position stratum and keep it separate from any bounded
reference on larger positions. The latter still requires choosing and pinning
a game-aware leaf evaluator, depth, transition/node cap, action order, and
incomplete-search policy before model scoring. The existing toy-game
evaluator does not settle those choices or authorize swapping V2.12's game
scope to smaller games.

## External exact-solver candidate: standard Connect Four (2026-10-03)

A read-only source audit found Markus Thill's MIT-licensed
[Connect-Four framework](https://github.com/MarkusThill/Connect-Four), pinned
for this audit to commit
[`2a58844594ac022846385dd3ddc8bbbf0a26eae5`](https://github.com/MarkusThill/Connect-Four/tree/2a58844594ac022846385dd3ddc8bbbf0a26eae5).
Its README claims exact game-theoretic state and state-action values for
arbitrary positions. The inspected source exposes
[`AlphaBetaAgent.getNextVTable`](https://github.com/MarkusThill/Connect-Four/blob/2a58844594ac022846385dd3ddc8bbbf0a26eae5/CFour/src/c4/AlphaBetaAgent.java):
for each non-full column it applies the move and calls a fresh
`rootNode(true)`, which initializes a full alpha-beta window. The configured
search depth is 100 while the implementation's board has at most 42 cells;
with `books=null`, opening-book branches are disabled. This is a plausible
route to complete terminal-minimax action values for valid, reachable,
nonterminal standard 7x6 positions. Returned values use the implementation's
Player-1 sign convention and encode win/loss distance; an adapter would need
to normalize them to root-player win/draw/loss utility and validate every
legal action and turn convention.

Scope is strictly the hard-coded 7-column by 6-row board. It does not cover
Connect Four 8x8 or either Reversi variant. This is a source-level candidate,
not an independently verified oracle: no code was run, no score was used, and
no compatibility, correctness, or resource test was performed. Before use,
pin and review an adapter, license/provenance handling, reachable-state and
terminal/pass/action-set contracts, value normalization, and bounded runtime;
keep exact-solved values separate from any bounded reference. Preserve the
upstream [MIT license](https://github.com/MarkusThill/Connect-Four/blob/2a58844594ac022846385dd3ddc8bbbf0a26eae5/LICENSE)
notice if code is ever copied. This does not close the overall V2.12 oracle
gap or authorize scoring, root generation, data generation, or training.


## Exact-reference candidate comparison and utility semantics (2026-10-03)

A follow-up primary-source audit found a more direct standard-board API than
the Java candidate above. At pinned commit
[`benjaminrall/connect-four-ai@28a112adaf3ff89ee23fb09411fa592b6597010e`](https://github.com/benjaminrall/connect-four-ai/tree/28a112adaf3ff89ee23fb09411fa592b6597010e),
the Rust MIT-licensed core exposes `Solver::get_all_move_scores`: it returns
one exact remoteness score for each playable column and `None` for full
columns, after solving each successor. The source assumes a valid, non-won
position. Its repository describes the standard 7x6 board and publishes
author-run benchmarks, including a 5.09 s average for its `begin-hard`
no-book position set; this is not a CAISSA measurement and is not independent
verification. The API has no per-call deadline. Its exact solver is therefore
a plausible evaluation-only candidate for reachable Connect Four 6x7 roots,
subject to adapter, correctness, and resource review. The output is from the
side-to-move perspective and folds win/loss remoteness into signed values; the
frozen diagnostic must decide whether the primary exact-regret utility is
W/D/L only, with remoteness secondary, before reading scores.

Pascal Pons's pinned [Connect4 Game Solver](https://github.com/PascalPons/connect4/tree/d6ba50d8aaf2308c769d9bf2abd42d90f34baf41)
also exposes per-column exact scores through `Solver::analyze(P, false)`
and `main -a`, but is AGPL-3.0-or-later; do not copy or integrate it without
separate license/provenance review. Both search sources are fixed to standard
7x6 Connect Four and do not cover the 8x8 variant or Reversi. The 2025
preprint [Strongly Solving 7x6 Connect-Four on Consumer Grade Hardware](https://arxiv.org/abs/2507.05267)
reports an exact W/D/L BDD table of 89.6 GB, produced in 47 hours on one CPU
core with 128 GB RAM; its [author repository](https://github.com/markus7800/Connect4-Strong-Solver)
describes querying W/D/L and remoteness separately. The repository has no
license file in the inspected tree; do not reuse its code or large artifact
until provenance, license, and storage are resolved.

This materially narrows the exact-oracle source gap for one training-size
variant, but it does not establish an integrated or cap-compatible oracle.
The Rust solver's internal node accounting is not the V2.12 planner's 10,000
search-node budget, and no request-to-reference latency, resource containment,
value normalization, or adapter test was run. Keep this separate from the
5-second candidate planner budget, exact-solved from bounded-reference
strata, and all score/generation/training gates. No external engine was
installed or run.

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

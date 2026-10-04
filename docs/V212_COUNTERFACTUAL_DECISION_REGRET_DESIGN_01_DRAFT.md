# V2.12 counterfactual decision-regret design 01 — draft

**Status: draft; prior formulation and both amendments independently reviewed; interval-reference tests/configuration pending; protocol not frozen.**
This proposal makes the action-score and regret terms operationally explicit.
It does not
amend METHOD_SPEC_V212-04, freeze an estimand, authorize model scoring, data
or root generation, training, matches, or outcome access. The reference depth,
leaf evaluator, sampling schedule, and compute allocation remain unselected.

**Independent static review of the prior formulation (2026-10-04): no remaining blocker within that scope.** The review
confirmed that regret must use the action returned under the frozen planner
caps, kept separate from any extra-compute full-window score-ranking
diagnostic. For the Reversi6 semi-strong artifact lead, it required
orientation-specific `R_P` membership with the free-agent role in that same
orientation; union-only `R` membership is insufficient. The artifact remains
unadopted, and no gate advanced.

**Independent review of the 2026-10-04 source-code amendment: no blocking issue.**
The review confirmed that the legacy heuristic creates a plausible source-policy
alignment risk, and that primary executed-action regret can use an exact
bounded-reference root maximum plus independent full-window values for each
executed action. The all-action table remains optional for ranking diagnostics.
The root schedule is retained. Tiny-oracle implementation checks, reference
configuration, and protocol freeze remain pending; no gate advanced.

**Independent review of the 2026-10-04 interval-reference option: no blocking issue in the derivation.**
The review confirmed soundness under the requirement that every expanded node
enumerate all legal successors or retain unexpanded actions as unresolved
`[-1,+1]` children. It confirmed the regret interval is valid but may be
conservative. Tiny-game containment tests, compute-cap feasibility, and
configuration remain pending; this interval estimand is distinct from scalar
bounded-`h_ref` regret and must not be pooled with it.

## Source-code audit: evaluator provenance and minimum regret queries (2026-10-04)

This is a design amendment proposal based on the repository source, not a
frozen protocol or independent acceptance. It does not change the method,
authorize root generation or scoring, or advance any gate.

The legacy `two_player/v28_data.py::_line_score` is not a neutral reference
candidate as currently used: `_bounded_search` calls it at depth/node-cap
leaves, and `choose_action(..., "positional", ...)` also ranks actions with
the policy heuristic built from it. A reference using the same implementation
on roots drawn from those synthetic policies could favor the data-generating
policy by construction. Pinning its source hash would make that dependency
reproducible, but would not remove the estimand's alignment. Keep this
heuristic excluded from the reference unless a separately reviewed protocol
explicitly wants that policy-aligned comparison. This is a source-level
confound audit; no roots or scores were inspected.

The primary executed-action regret does not mathematically require a point
score for every root action. For a fixed reference search `Q_ref`, it requires
the exact fixed-horizon root maximum `V_ref(s) = max_a Q_ref(s,a)` over the
complete legal set and an exact fixed-horizon value `Q_ref(s,a_m^exec)` for
the action returned by each arm. The latter must be an independent full-window
query (or a separately verified equivalent); a fail-low bound from a shared
incumbent window is insufficient. Then regret is
`V_ref(s) - Q_ref(s,a_m^exec)` for that declared bounded reference. One
action-independent `V_ref` can be shared across arms, while action-value
queries may be cached by root fingerprint and action.

Proposed protocol split: keep a complete legal-action fingerprint and prove
the reference maximization covered every legal action, but record exact
per-action Q rows only for distinct executed actions in the primary regret
table. Retain a separate optional all-legal-action full-window table for
reference/model ranking agreement; it has its own compute allocation and
completeness status. A root is not estimable for an arm if either `V_ref` or
that arm's selected-action value is missing, bounded, or interrupted. This
reduces redundant oracle work without dropping roots or changing the
estimand; it does not make the bounded reference full-game ground truth.

Before adoption, an independent implementation review must verify root-value
exactness, selected-action full-window semantics, ties, terminals and forced
passes under both game adapters, and prove against a tiny exhaustive oracle
that the new query path returns the same per-root regrets as a complete
all-action table. These are proposed checks only; no implementation or tests
were run.

## Deep-search update: sound minimax-regret intervals (2026-10-04)

The scalar fixed-depth `h_ref` proposal is not the only reference design. A
less heuristic-dependent candidate is to maintain sound lower/upper bounds on
the full-game minimax values while expanding only a frozen portion of the
tree. The primary source on optimistic minimax search by Busoniu, Munos and
Pall describes lower/upper bounds at partial-tree leaves, max/min propagation,
and anytime termination whose remaining value gap bounds the unresolved
optimality ([paper](https://busoniu.net/files/papers/adprl14-minimax.pdf)).
This is a general adversarial-search precedent, not a drop-in CAISSA algorithm;
its convergence guarantees rely on assumptions that must not be transferred
without proof. Pascal Pons's Connect Four solver likewise explicitly
distinguishes exact, upper-bound, and lower-bound alpha-beta returns
([pinned `Solver.cpp`](https://github.com/PascalPons/connect4/blob/d6ba50d8aaf2308c769d9bf2abd42d90f34baf41/Solver.cpp)); it illustrates why cutoffs must remain bounds rather than point values, but its AGPL code is not proposed for integration. The exact Othello study further distinguishes
positions whose game-theoretic value was solved from those only estimated
([Takizawa, 2024](https://arxiv.org/html/2310.19387v3)).

For CAISSA's W/D/L utility in `[-1,+1]`, initialize each unexpanded
nonterminal frontier leaf to the conservative interval `[-1,+1]`; terminal
nodes take their exact root-perspective outcome. On expansion, propagate
intervals monotonically: at a root-player MAX node use
`[max_i L_i, max_i U_i]`; at an opponent MIN node use
`[min_i L_i, min_i U_i]`. Enumerate the full legal root set. If action `a`
has interval `[L_a,U_a]`, then the exact full-game root value is enclosed by
`[max_a L_a, max_a U_a]`. For an executed action with interval
`[L_e,U_e]`, a sound regret interval is
`[max(0, max_a L_a - U_e), min(2, max_a U_a - L_e)]`.
This interval follows from the declared W/D/L utility range and bound
propagation; it is a derivation, not an empirical result. A zero-width regret
interval identifies a point value; otherwise report the interval and its
width, never its midpoint as a point estimate.

For soundness, every expanded internal node must either enumerate its full
legal successor set or retain each unexpanded legal action as an unresolved
`[-1,+1]` child interval. Propagating only visited children would silently
turn a partial search into a false exact value. A forced Reversi pass is its
own legal transition and must remain in this accounting.

This option avoids reusing the positional/bounded-search data heuristic and
can retain the full predeclared root schedule even when exact solving is
infeasible. It trades scalar coverage for honest uncertainty: many intervals
may remain wide under realistic caps. Freeze the deterministic expansion
policy, per-variant/per-root node or transition budget, tie ordering, cache
semantics, pass/terminal handling, and failure rules in advance. Report
interval widths and point-identification coverage alongside the separate
root-sampling uncertainty. The game-tree budget is a separately declared
evaluation allocation; it does not borrow from or alter the arm's inference
cap. The scalar `h_ref` regime may remain a labeled sensitivity analysis, but
must not be pooled with these game-theoretic bounds.

Before preferring this option, independently verify the interval recursion
against exhaustive tiny-game values at every partial-tree shape, including
forced Reversi passes, terminal wins/draws, and unseen legal children; check
the regret interval contains exact regret and collapses when bounds resolve.
Then assess cap feasibility using synthetic in-memory fixtures only. These
checks have not run, the interval option is not accepted or frozen, and no
root generation, model scoring, or gate advancement is authorized.

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

Let a_m^exec(s) be the action actually returned by arm m's frozen evaluation
planner under its shared node/time/memory limits, including a declared legal
fallback if a full iteration did not complete. Regret below evaluates this
deployed action. It must not silently replace it with the argmax of a separate
unbudgeted score pass.

Optionally, define Q_m(s,a) as arm m's fixed-depth, model-based root-action
score for a separate ranking diagnostic. Score every legal root action
independently with a full window (or use a separately verified equivalent
that returns an exact fixed-depth value). Do not carry an incumbent root
alpha from a previous action and treat a fail-low upper bound as a point
score. Report these model-score rankings only when all required rows complete;
their additional compute needs a separate frozen allocation. They do not
replace a_m^exec(s), and they do not enter the primary head-to-head metric.

When the exact fixed-horizon reference root maximum and selected-action
reference values are available under configuration c, report per-root

    R_m^exec(s;c) = max_{a in Legal(s)} Q_ref(s,a;c)
                    - Q_ref(s,a_m^exec(s);c).

The reference values are in root-player utility, so this quantity is
nonnegative and bounded by the reference value range. Also report ranking
agreement between complete Q_m and Q_ref rows only in their separately
completed diagnostic stratum, with ties handled by Kendall's tau-b or another
metric selected before scoring. Keep deployed-action regret, model-score
ranking and raw latent error separate; none can be inferred from another.
Aggregate per root first, then by predeclared variant and seat with the locked
weighting. Do not pool root actions as if they were independent root
observations.

## Completeness, alpha-beta bounds, and failures

The legal-action set is always fingerprinted, and the reference root search
must establish an exact maximum over that complete set. The primary regret
ledger needs one root-value record per protocol/root/reference configuration
and one independently exact selected-action reference value per distinct
executed action, arm, and root; repeated actions may share a cached value.
Record root fingerprint, actor, legal-set fingerprint, model/reference config
hashes, score/status, search window/bound provenance, completed depth, node
visits, exact transition calls, model calls, elapsed time, and stop reason.
Allowed statuses are exact, upper_bound, lower_bound, and missing. A bounded
action score must never be converted to a point estimate. A separate optional
all-legal-action ranking table requires a row for every legal action and its
own completeness status.

A root's regret is not_estimable if the exact root maximum or that arm's
selected-action value is missing, bounded, or interrupted. Pairwise ranking
is reported only when bounds establish the order; otherwise it is unresolved.
If any arm stops before the required root and selected-action values complete,
retain the failure row and do not shrink the root denominator or substitute an
easier root. Report coverage and missing reasons next to every aggregate. Any
cap-stressed or all-action ranking diagnostic needs its own predeclared
compute allocation; it may not silently borrow or alter the frozen
head-to-head budget.

## Reference construction and leakage boundary

Use exact terminal minimax only on a declared tractable subset. For other
positions, a fixed bounded-depth reference must pin h_ref, source hash,
search depth, rules, tie-breaking, root-player conversion, and any pruning
settings before models are scored. Keep exact-solved and bounded-reference
results in separate strata and do not label the latter optimal, ground truth,
or full-game value. If a common reference cannot establish the exact root
maximum and selected-action values within its frozen procedure, mark that
root/arm not estimable for regret; do not tune depth per root after seeing
predictions.

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


## New exact-reference lead: 6x6 Reversi semi-strong tablebase (2026-10-04)

Takizawa's primary paper defines a **semi-strong** solution region `R` for
6x6 Othello/Reversi and reports exact value queries within that region, not a
strong solution over every rule-reachable state. `R` contains positions
reachable when one designated player follows a fixed canonical optimal
policy while the other may choose any legal move. At a certified free-agent
decision node for a declared orientation, every legal successor remains in
that orientation's certified region; at an optimal-agent node for that
orientation, the artifact supports the canonical optimal move, not arbitrary
alternatives. The paper's public Zenodo release describes a
queryable solution artifact plus a proof certificate and totals 138.4 GB.
Sources: [paper v2](https://arxiv.org/abs/2411.01029v2), [full text v2](https://arxiv.org/html/2411.01029v2),
[Zenodo artifact](https://zenodo.org/records/18843225).

There is a utility mismatch that is tractable in principle. The artifact uses
exact terminal disc-margin utility, including award of empty squares to the
winner, while V2.12 uses winner/draw utility. Under the ordinary Reversi
terminal rule, the sign of the exact margin equals the winner utility; because
sign is monotone, applying it to every terminal value commutes with recursive
max/min. Thus a certified exact score value can yield an exact W/D/L value
for V2.12. This inference does not turn the artifact into a strong solve and
does not extend its region `R`.

**Potential use:** a separately labelled exact-reference stratum could score
every legal root action only when (i) the prehashed root is certified in the
orientation-specific region `R_P`, (ii) the side to move is the free player
for that same orientation `P`, and (iii) every legal successor value is
returned and verified by the artifact. Membership in the union
`R = R_first ∪ R_second` alone is insufficient.
Each child query must be converted from the next side-to-move perspective to
the root perspective before forming `Q_ref(s,a)`.
All other roots/actions remain uncovered; optimal-agent decision points do
not support an all-legal-action denominator from this artifact alone. The
normal v04 root schedule is generated from a policy mixture, so membership in
`R` cannot be assumed. Do not select roots after model scoring to improve
coverage.

This is a **source lead, not an adopted oracle**. The Zenodo record has no
license value in its rights metadata, and the full release is very large; no
files were downloaded. Before any use, resolve permission/license and storage,
pin artifact and query-script hashes, verify the query contract and proof
scope, and quantify root/action coverage on an independently frozen schedule.
Even if adopted, it only creates an exact Reversi6 stratum and cannot replace
the still-unselected bounded reference for the other variants or roots outside
`R`. No code, roots, artifact, score, or outcome was produced in this audit.


## Decision-metric alignment and action-conditioned objectives prior art

A close 2026 preprint, Wang et al., *Decision-Metric Alignment in Latent
World Models* ([arXiv:2608.18746v1](https://arxiv.org/abs/2608.18746)), introduces Plan-Real Spearman
and CEM-stage Spearman for latent-cost versus environment-cost ordering and
DA-LeWM, which adds inverse-dynamics and demonstration-conditioned
goal-action heads to an action-conditioned JEPA-style predictor. It establishes
that action-conditioned JEPA planning, these auxiliary objectives, and
planner-rank diagnostics are not independently novel claims. Its single-agent
Euclidean-goal CEM setup differs from this draft's complete legal root-action
scores and root-perspective max/min decision regret in deterministic
two-player games; the empirical gap remains a hypothesis, not a novelty
finding.

A reported negative is relevant to metric design: CEM-stage rank correlation
is near zero or below at the elite stage for every variant, including the
action-supervised DA-LeWM, despite positive random-stage gains. Global
candidate ranking can therefore hide failure in the planner's selected
neighborhood. The paper has one training run per configuration and three
evaluation seeds and is not independently reproduced here. Before scoring or
fitting, independent review should determine whether a board-game inverse
action head is an appropriate control and specify any behavior-derived
goal-action targets so they do not get misrepresented as adversarially optimal.
No new control is added to V2.12 by this note; doing so requires a versioned
method amendment and review.


## Possible inverse-action auxiliary control

A separate review proposal,
[V2.12 inverse-action control design 01](V212_INVERSE_ACTION_CONTROL_DESIGN_01_DRAFT.md),
considers crossing the frozen v04 arms with a training-only inverse-action
loss over exact observed transitions. The current predictor already receives
actions, and every arm has a behavior-policy action head; therefore this would
test incremental representation pressure rather than establish action
conditioning. The proposed all-arm factorial preserves compute matching and
reports the inverse-loss main effect and interaction with JEPA family. It does
not yet pass independent review or authorize an objective change. Goal-action
targets from policy-mixture trajectories remain behavior labels, not minimax
targets. Training and outcome gates remain closed.

# Method V2.8-P V02 amendment: supervised reply-set JEPA prototype

**Status: implementation-aligned prefit amendment; implementation/objective
consistency independently reviewed with no P1 finding; not frozen and not
trained.** V01 remains unchanged and frozen as a different development
candidate. This amendment documents the actual V02 prototype so no run can be
mislabeled as V01. Fitting remains closed until the implementation, data,
measured-compute, schedule-power, and independent-review gates pass.

## Research question and claim boundary

For the admitted finite, deterministic, two-player, alternating-turn,
fully-observed, zero-sum games, does adding complete legal-reply-set latent
prediction improve the paired color-swapped match score of the same shallow
max-min planner over (a) a task-value dynamics control and (b) a direct encoded
leaf-value control, under the fixed V08 schedule and measured compute budget?
The opponent in the planner is a worst-case legal reply in the enumerated
two-ply tree. This is not prediction of one opponent's behavior, expectation
under an uncalibrated policy distribution, full-game minimax, equilibrium, or
exploitability. A positive result applies only to the tested rules, generated
trajectory distribution, proxy/reference opponents, search budget, and frozen
model-selection procedure. It is not evidence of general JEPA superiority,
method novelty, broad game transfer, or Q1 acceptance.

V02 is deliberately distinct from frozen V01. V01 requires a KLENT-style
policy-improvement/Q objective and alternating lambda returns. V02 is a small
supervised implementation candidate using recorded behavior actions and
terminal self-play outcomes. V02 does **not** implement KLENT or lambda-return
training. KLENT's direct policy/Q learner may appear only as a secondary
policy-only reference in this version. Making it co-primary or comparing it
under the V08 confirmatory schedule requires a new schedule, multiplicity,
power, and independent-review amendment before training.

## State, perspective, and targets

For game `g`, let `s` be an exact nonterminal state, `p(s) in {-1,+1}` the
player to move, `A_g(s)` its exact legal actions, `T_g(s,a)` the deterministic
successor, and `u_g(s_T) in {-1,0,+1}` the terminal outcome from absolute player
`+1`'s perspective. A trajectory terminal label `U` defines the root target
`y(s)=p(s) U`, in the root player's perspective. Since two alternating actions
return the turn to the root player, an observed H2 leaf uses the same `y(s)`.
The record's observed action and opponent reply must replay exactly through
`T_g`; an observed H1/H2 state mismatch is an error, not a masked sample.

The exact adapter generates the complete legal two-ply closure
`C_2(s)={(a,b,s_ab): a in A_g(s), b in A_g(T_g(s,a)),
s_ab=T_g(T_g(s,a),b)}`. If the root action itself ends the game, it is scored
with exact utility and contributes no latent branch. A terminal H2 leaf is
also scored with exact root-perspective utility during planning, but it is
excluded from learned H2 value regression and from JEPA latent matching. Counts
of terminal masks are reported. Nonterminal leaves have target-latent and
value targets only where their source trajectory supplies those labels;
counterfactual branches never receive invented outcome labels.

The online encoder `f_theta(x)` maps the documented 198-feature rule-aware
state to a `d`-dimensional latent. The target encoder is an EMA copy
`bar(theta) <- tau bar(theta) + (1-tau) theta`. The predictor
`g_phi(z,e(a),e(b),r_g)` receives ordered one-hot action IDs for both players
and the six rule descriptors. `v_omega` returns a bounded score from the root
player's perspective. Exact game code remains authoritative for legality,
transitions, and terminal utility.

## Objective and matched arms

All primary learned arms receive identical train trajectories, root records,
legal branch closure, sampled behavior-action labels, terminal root outcomes,
observed H2 records, minibatch/update schedule, seeds, and planner. Their shared
supervision is

`L_shared = L_policy + L_root`,

where `L_policy` is legal-action-masked cross-entropy for the one recorded
behavior action at each root, and `L_root = mean((v(f(x_s))-y(s))^2)` is root
terminal-outcome regression. The policy target describes the data-collection
policy; it is not a best response, minimax policy, KLENT improvement target, or
opponent response model.

For nonterminal observed H2 records only, the learned leaf score receives
`L_H2 = mean((v(z_hat_ab)-y(s))^2)`. The `task-value-dynamics` arm trains the
same encoder, predictor and value head on `L_shared + L_H2 + L_collapse`, with
no latent target loss. `direct-leaf` uses the exact encoded observed leaf for
`L_H2` and exact encoded counterfactual leaves at inference; its predictor is
inactive. All allocated/active parameters and actual costs are reported.

The candidate `reply-jepa` arm adds the root-balanced latent loss

`L_reply = mean_roots[ mean_{(a,b,s_ab) in C_2(s), nonterminal}
||g_phi(f_theta(x_s),e(a),e(b),r_g) - stopgrad(f_bar_theta(x_s_ab))||_2^2 ]`.

Roots, rather than individual branches, receive equal weight. The full candidate
objective is `L_shared + L_H2 + lambda_J L_reply + L_collapse`, where
`lambda_J=1`; terminal and missing branches are masked and counted. The initial
`L_collapse` combines the declared online latent variance floor (`std>=0.1`,
weight 0.1) and off-diagonal covariance penalty (weight 0.01). These constants,
EMA coefficient 0.99, Adam settings, batch size 64, clipping threshold 5, model
seeds and epoch/update schedule must be frozen in the run config before any
fit. The implementation prototype uses float64 NumPy and a single hidden-free
linear/tanh encoder/predictor; this is a feasibility model, not a scale claim.

At planning time, the exact adapter enumerates each own action and legal reply.
Terminal leaves return exact utility; otherwise `reply-jepa` evaluates
`v(g_phi(f(x_s),e(a),e(b),r_g))`, `task-value-dynamics` uses the same learned
latent predictor, and `direct-leaf` evaluates `v(f(x_s_ab))`. Each arm selects
`argmax_a min_b Q(s,a,b)`. Search algorithm, root/action ordering, timeout,
matched budget, opening/root schedule, and censor policy must be identical.
Report actual model calls, transitions, wall/CPU time, memory, and censored
roots so an implementation-cost difference is visible.

## Data, evaluation, and stop rules

Only the audited project-generated DEV09 train split may be considered for a
development fit. Validation and selection are used only for model selection;
locked-final and the V08 match schedule remain unopened. No third-party data is
admitted. Dataset and audit SHA-256, code/config/objective hashes, trajectory
identity, checkpoint hash, seed, sample/mask/error counts, and measured resource
use are required in every receipt. No fit may begin until the current
nonlearned V08 complete-game run finishes within its declared local CPU cap,
all transcript/replay checks pass, paired variance/power gates pass, and an
independent prefit review approves the frozen artifact set.

The V08 primary contrast is paired color-swapped complete-game score for the
candidate against **each** of the two primary controls, with its locked block
schedule, practical margin, multiplicity correction, uncertainty bounds,
timeouts, and failures unchanged. Supporting only one contrast does not pass.
Any power or endpoint alteration requires a new prefit amendment. Mechanistic
latent error, policy metrics, root-value error, collapse diagnostics, and
compute curves are secondary; lower latent error alone is not evidence of
improved planning.

If the candidate does not beat both controls at the predeclared practical
margin and same measured budget, retain the negative result and do not tune on
locked outcomes. Tuning is limited to a small, explicitly versioned set on
development/selection data; each recipe and failed seed remains in the ledger.
If no recipe survives model selection without opening confirmation data, pivot
to a methods/benchmark or negative-results submission. Failure of support,
replay, runtime, power, or independent review blocks training rather than
loosening the gates.

## Version history

- **V01** (`docs/METHOD_V28_PLANNER_V01.md`): frozen development candidate with
  KLENT-style policy/Q and alternating lambda-return objectives. No fit was
  made under it.
- **V02 prototype** (`two_player/v28_model.py`): implementation-aligned
  supervised objective above. Separate, pending independent review and all
  prefit gates. No fit, checkpoint, or learned result exists.

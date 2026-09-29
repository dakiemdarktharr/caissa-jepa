# V2.6 method proposal — sequential JEPA transfer on held-out variants

**Status: design proposal, not yet frozen, not implemented, and not an experiment
result.** This document is a gate for a bounded feasibility implementation. A
reviewed/frozen version and immutable data plan must precede any predictive-model
training. V2.5 remains immutable and negative.

**Current feasibility disposition (2026-09-29): not cleared for fitting.** Small
Connect4-4x5 roots are often exactly solvable but early-ply coverage is weak;
late Reversi roots are cheap for exact search; Connect4-gravity-8x8 roots are
meaningfully harder but exact labels time out under the measured local budget.
See the `V26_ORACLE_FEASIBILITY_01` through `_05` receipts. No model-independent
balanced root bank has passed the pre-fit gate. Any shift to self-play/outcome
training and paired match evaluation requires a separately versioned method and
cannot be called a completion of this exact-minimax-regret proposal.

## Question and scope

Test whether action-conditioned latent prediction helps a shared model transfer
decision quality to whole held-out rule variants under a bounded planning
budget. This is distinct from predicting a particular opponent's behavior.
The environment is a two-player, alternating, fully observed, deterministic,
zero-sum game with explicit legal actions and terminal utility. State must
include all rule-relevant history to be Markov. The initial feasibility cap is
the existing repo-owned padded board/action interface (boards up to 8x8); any
broader game family requires a new versioned representation audit.

Falsifiable hypothesis: at the same training wall-clock cap and fixed matched
inference/search budget, a shared JEPA model trained on future states reached after the learner's legal
move and the opponent's legal reply achieves lower exact minimax regret on
complete held-out variants than matched policy/value-only, task-prediction,
and explicit state-feature-prediction controls. This is a hypothesis, not a
novelty or performance claim. If only transition-count matched results improve,
the claim is limited to sample efficiency.

## State, actions, and values

For the initial capped adapter set, state is \(s=(B,p,g)\), where \(B\) is
the board, \(p\in\{-1,+1\}\) is player to move, and \(g\) contains only
compositional, public fields already represented in the encoder: rows/8,
columns/8, connect target/8, gravity, and Reversi flags. The encoder receives
the actual feature tensor from `BoardGame.features`; it receives no opaque
variant/game ID. These games have no additional repetition/counter history; if
any new rule needs history, it is out of scope until an explicit feature and
Markov audit is added. The adapter supplies \(A_g(s)\), deterministic
transition \(T_g(s,a)\), terminal predicate, and terminal-only utility
\(u_{abs}(s)\in\{-1,0,+1\}\) from the fixed absolute +1-player perspective.
The encoder input is role-relative to player to move, with a tested role-swap
transform. Action IDs 0–63 use the padded board grid and 64 is forced pass;
padding slots are never legal actions. Illegal action logits are masked before
normalization and planning.

Let \(U^*_{abs}(s)\) be the exact minimax outcome from the fixed absolute
\(+1\)-player perspective for every state, with terminal boundary
\(U^*_{abs}(s)=u_{abs}(s)\). Define player-to-move value as
\(V^*(s)=p(s)U^*_{abs}(s)\). Then
\(Q^*(s,a)=-V^*(T_g(s,a))\) and
\(V^*(s)=\max_{a\in A_g(s)}Q^*(s,a)\). At terminal nodes use the exact
utility override; the planner never queries a learned terminal latent/value.
Role-swap, pass, terminal and symmetry tests must check this sign convention
and action mapping before training. For a symmetry map \(m\), transform the
board, legal-action mask, policy target, selected action and every transition
together, then re-encode; verify that minimax values are invariant and action
IDs follow \(m\). Role swap must negate player-to-move value and preserve the
mapped optimal-action set.

The repo's existing `two_player/games.py` uses 198 padded features and a
65-slot legal-action interface for supported boards through 8x8. Each V2.5 fit
used both Connect4-4x5 and Reversi6 through shared weights. This is a candidate
for finite transfer within the declared rule channels; it does not prove
transfer to held-out rules or general games. A held-out configuration must be
represented compositionally by those public fields; unique IDs are forbidden.
For broader or unseen rule semantics, add explicit feature channels and
re-audit before making a transfer claim.

## Model separation

All learned controls share the same encoder family, latent/hidden widths,
policy/value heads, training-root schedule, role/symmetry augmentation and
legal-action interface. No model receives test-variant training labels.

- **Direct PV:** shared state encoder with policy and player-to-move value
  heads; no predictive state model.
- **Recurrent PV:** action-conditioned recurrent state transitions, with
  policy/value heads at each unrolled step.
- **Task-prediction (MuZero-style) control:** recurrent latent dynamics with
  policy, value and reward/outcome prediction losses; use the same search and
  same exact game adapters as JEPA. This is a scoped MuZero-style offline
  control, not a reproduction of MuZero's self-play/search training pipeline.
- **Explicit state-feature prediction:** action-conditioned predictor decodes
  the future adapter feature vector. This controls for predictive auxiliary
  training without a JEPA target space.
- **JEPA:** online encoder \(f_\theta\), EMA target encoder \(f_{\bar\theta}\),
  and predictor \(q_\psi\). Given \(z_t=f_\theta(s_t)\), encode the learner's
  action \(a_t\) and the next player's reply \(b_t\) with shared action
  embeddings. Predict each future latent:
  \[
    \hat z_{t+1}=q_\psi(z_t,e(a_t),\mathrm{role}_t),\qquad
    \hat z_{t+2}=q_\psi(\hat z_{t+1},e(b_t),\mathrm{role}_{t+1}),
  \]
  and compare to stop-gradient target embeddings of the exact successor
  states. For prediction \(x\) and target \(y\), let
  \(\bar x=x/\sqrt{\|x\|_2^2+10^{-6}}\) and similarly for \(\bar y\); use
  \(\|\bar x-\mathrm{stopgrad}(\bar y)\|_2^2\), averaged separately over
  valid H1/H2 targets. The mask is false only for absent states or a terminal
  successor; terminal outcomes remain in exact value supervision and planner
  terminal override, while policy loss applies only to nonterminal states.
  Forced pass is a legal action with a real
  successor and perspective change, not a missing target. Online/target
  encoders receive the same role transform. EMA decay and any
  variance/covariance anti-collapse regularizer are fixed in the pre-fit
  configuration; no post-result tuning.
- **EMA scalar-value control:** same target encoder schedule, but predict
  future scalar minimax value only. This controls for target-network
  self-distillation without vector future-state prediction.
- **Untrained and random legal policy:** correctness references only, never the
  primary learned baselines.

The supervised loss is \(L_{PV}=L_{policy}+L_{value}\): policy uses masked
cross-entropy against the same exact minimax action distribution for every
family (uniform over exact optimal ties), while value uses squared error for the
same player-to-move oracle value, including exact terminal outcome labels.
Policy loss is normalized over valid nonterminal states; value loss is
normalized over valid states including terminal states. The planner still uses
exact terminal override and never calls a learned value at a terminal leaf.
JEPA adds
\(L_{pred}=\lambda_1L_{H1}+\lambda_2L_{H2}\); explicit-feature and
task-prediction controls use their corresponding target losses. Objective
weights, EMA, regularizer, optimizer (candidate Adam), learning-rate schedule,
batch size, number of updates, initialization seeds, and checkpoint schedule
remain to be frozen from a finite development-only configuration table before
any fit. Each family receives the same tuning cells and stopping/checkpoint
opportunity. Dynamics objectives are averaged by valid target count, never by
padded tensor size. A shared variant-balanced minibatch schedule gives every
game/variant equal exposure.

Every training root contributes its complete legal own-action × legal-reply
closure, not merely trajectory-selected replies. If future scale requires
subsampling, freeze inclusion probabilities and inverse-probability weights
before labels and prove coverage of every legal reply stratum. Reply \(b\)
means an action taken by the next player under the rules, not an action sampled
from a named opponent policy. Report closure/branching coverage and
terminal/nonterminal H1/H2 counts by variant and tactic stratum.
Use the same initialization for encoder/policy/value tensors where shapes
match across families; disclose separately initialized or unused heads and
trainable parameter counts. If compute limits prevent exact parameter equality,
include a parameter-matched sensitivity model. Report latent
variance, covariance/effective rank, target-online alignment, per-horizon error,
gradient norms, and nonfinite/collapse status by variant and seed.

## Planner and evaluation estimands

The behavioral opponent, worst-case opponent, and equilibrium concepts remain
separate. This method does **not** predict how a named opponent behaves. At
each search node, the exact adapter enumerates legal actions and transitions;
the learned model does not define game rules. The shared same-search comparison
uses identical roots, expanded branches, depth, legal masks, terminal override,
leaf budget, value perspective, and failure policy. Direct PV encodes the exact
state at a leaf; recurrent PV, task-prediction, and JEPA controls roll latent
states forward from the root actions. This compares learned evaluations under
shared exact rules; it does not show that JEPA is a standalone learned
simulator. Exact-rule solver cost and full system comparisons are reported
separately. Per-decision wall time, node expansions, model calls and estimated
FLOPs are recorded; timeouts are failures and cannot be dropped. Do not describe
decision regret as Elo, match win rate, or exploitability.

Run two comparison tracks:

1. **Objective-isolation track:** same labeled transitions, number of optimizer
   updates, architecture capacity, initialization seeds, batch order, and
   evaluator/search budget. Record the extra actual training time/FLOPs each
   objective incurs.
2. **Bounded-compute track:** each method receives the same measured local
   training wall-clock (and FLOP budget if reliable), then the same fixed
   inference search/time budget. This is the primary system-relevant
   comparison; updates and examples achieved under the cap may differ and must
   be reported.

For chosen root action \(\hat a\), define exact regret as
\(R(s,\hat a)=\max_{a\in A_g(s)}Q^*(s,a)-Q^*(s,\hat a)\); ties have zero
regret. Candidate primary endpoint: on selection variants, average per-root
regret within variant, average variants equally within each held-out rule
family, then average rule families equally. Integrate the resulting curve
against cumulative training-process wall-clock seconds from zero to a
predeclared common cap. Measure on one pinned local machine/process/thread
configuration. The timer includes minibatch construction/sampling,
augmentation, forward/backward, optimizer and EMA updates, logging, and
checkpoint writes. It excludes one-time data/oracle generation and offline
evaluation; report those costs separately. Use common predeclared checkpoint
targets. Timestamp each checkpoint after its atomic write completes and score
the saved weights offline on identical roots with fixed per-decision
search/time. Set \(t=0\) immediately before the first training batch and score
the initialized model there. Treat the curve as right-continuous stepwise and
hold each completed checkpoint's score until the next checkpoint and through
the cap. Let (t_0=0), let completed checkpoint times be
(0<t_1<\cdots<t_m<C), and explicitly set (t_{m+1}=C). Compute
\[\mathrm{AULC}=C^{-1}\sum_{i=0}^{m}y_i(t_{i+1}-t_i),\]
where (y_i) is the score available at (t_i); thus the final term is
(y_m(C-t_m)). No discretization grid or extrapolation is used. At the common
cap use the last checkpoint completed at or before the cap. Before the run,
measure the conservative runtime reserve in a separate development-only warm-up
and freeze it as the maximum observed duration of one complete optimizer update
plus atomic checkpoint and log write, multiplied by a fixed safety factor of
2. The runner starts an update/checkpoint only when this reserve fits the
remaining budget; otherwise it ends at the cap with the latest complete
checkpoint. Any update/checkpoint exceeding the frozen reserve is a budget
failure and makes the run inconclusive. Numerical, audit, process, or budget
overrun failures make a run inconclusive, while fewer updates within the same
cap are an outcome, not a censor. Lower normalized AULC is better.
Confirmatory AULC uses locked variants only after method selection and protocol
freeze. Report paired-seed/variant uncertainty, with bootstrap clusters at
configuration/trajectory rather than treating correlated positions as
independent. Three seeds support development screening only. Predefine
integration range and practical margin using development variance before
fitting.
Secondary endpoints: regret versus labeled transition exposures; fixed-budget
endpoint regret by variant/seed; zero-shot and few-shot adaptation reported
separately; all-legal policy ranking/NLL and value calibration; latent
prediction error by horizon; solver cost, wall time, memory, and latency.
Compute- and sample-efficiency claims require improvement on their own axes.

## Data and split plan

Generate project-owned deterministic game data locally. The configuration list,
generator/version, seeds, source hashes, and variant grouping rules must be
frozen before labels. Split entire rule configurations and all derived
trajectories, canonical symmetry orbits, and root closures before oracle labels
are computed. For a cross-family claim, the frozen grouping algorithm must put
all variants differing only by board dimension/connect target in one split;
otherwise label results within-family transfer. No family of near-duplicate
configurations may straddle splits.
Use distinct train, development, selection, and locked-confirmation variants.
The first 2–3 configuration feasibility pilot is exposed development only and
cannot support cross-game generalization or confirmation. A board-size-only
holdout supports only within-family variant transfer; cross-game language
requires held-out rule families.

Each dataset manifest must contain SHA-256, rules and generator fingerprints,
oracle implementation/version, counts, exclusions, exact-label provenance,
transition/parser version, and split assignment. Audit every transition and
legal set; duplicate states/trajectories and symmetry overlap; train/dev/test
closure overlap; terminal/perspective labels; per-variant hard-root coverage;
and oracle nodes/time. Production fitting is forbidden until these checks pass.
No third-party game code/data is included unless official licensing explicitly
permits the intended training and redistribution.

## Pre-fit gates and stopping rules

Before any model fit: (1) complete and independently review primary-source
positioning; (2) show adequate nonterminal two-ply held-out roots with unequal
exact action values under model-blind admission criteria; (3) measure exact
solver costs and reject a domain where exact search already dominates the
intended budget; (4) validate adapters against independent rules where a
permissively licensed source exists; (5) freeze baseline tuning opportunity,
primary metric, compute caps, seeds, root schedule, and exclusions; (6) run an
independent leakage/fairness review. Root candidates and strata are fixed from
public rule/state features and seeded generation before oracle queries; never
replace a difficult or timed-out root after observing its exact-solver cost or
labels. Exact-label timeouts count against the predeclared coverage gate. If
the gate fails, reduce the declared domain or change the oracle with a new
method version before producing training labels; do not silently condition the
test population on solver completion.

Stop or narrow the positive claim if the hard-root gate fails, a rules/oracle
disagreement or leakage occurs, exact search is cheaper throughout the target
regime, any learned family receives less tuning opportunity, JEPA fails the
predeclared held-out compute-curve margin against any strong learned control,
or the benefit is confined to one family/seed. A positive development result
only nominates a new locked confirmation; it does not establish Q1 readiness.

No confirmatory sample size or practical margin is assigned in this proposal.
Derive them from independent development variance and a documented power/
precision calculation before opening selection/final variants.

## Related-work boundary

The nearest game-transfer baseline is Soemers et al.'s AlphaZero-style
policy/value transfer among game variants and distinct games
([arXiv:2102.12375](https://arxiv.org/abs/2102.12375)); multi-game shared
interfaces were also studied with Ludii/Polygames ([arXiv:2101.09562](https://arxiv.org/abs/2101.09562)).
MuZero already performs successive action-conditioned latent rollouts for
planning ([arXiv:1911.08265](https://arxiv.org/abs/1911.08265)); SPR and
EfficientZero use multi-step latent consistency/prediction
([arXiv:2007.05929](https://arxiv.org/abs/2007.05929),
[arXiv:2111.00210](https://arxiv.org/abs/2111.00210)); and board-game state
consistency has been studied on Go and Gomoku ([arXiv:2411.04580](https://arxiv.org/abs/2411.04580)).
TD-JEPA adds multi-policy, action-conditioned long-horizon latent prediction
for zero-shot RL ([arXiv:2510.00739](https://arxiv.org/abs/2510.00739)), while
V-JEPA 2-AC demonstrates action-conditioned JEPA planning in robotics
([arXiv:2506.09985](https://arxiv.org/abs/2506.09985)). These works make broad
claims such as first action-conditioned JEPA, first multi-step latent game
planning, or first game-variant transfer untenable. The only candidate
incremental result is a controlled effect of JEPA targets versus matched
task/feature-prediction objectives in this bounded held-out-variant,
minimax-regret regime. This finite review has not established uniqueness.

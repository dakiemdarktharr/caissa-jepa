# Clean-room KLENT-style baseline specification

**Version:** K0.1, proposed for implementation checks only, 2026-09-30.
**Status:** equation-level adaptation; not a reproduction of the authors' code
or full-scale results. No model/data/training run yet. This document freezes
the baseline semantics needed for implementation and may not be changed to
improve observed candidate outcomes; corrections require a versioned amendment.

## Source and scope

Primary source: Ota et al., “Revisiting Regularized Policy Optimization for
Stable and Efficient Reinforcement Learning in Two-Player Games,” ICML 2026,
[paper](https://arxiv.org/html/2602.10894), especially equations (2)–(4) and
Appendix F. The authors' [supplementary repository](https://github.com/KazukiOhta/klent)
was inspected read-only. Its code license was not established, and its source
is not used here. This is a clean-room adaptation from the published equations.

The baseline applies to deterministic, finite, fully observed, alternating,
two-player zero-sum games with legal-action masks and terminal outcomes. It
learns a regularized self-play policy and return-Q; it is **not** a minimax
teacher, opponent-specific behavior model, or equilibrium certificate. The
implementation must call this “KLENT-style” until fidelity and external
replication are established.

## State, actions and perspective

At ply (t), (s_t) is the complete Markov state and (p_t\in\{+1,-1\}) is
the player to move. (A_t=A(s_t)) is the legal action set. The deterministic
transition is (s_{t+1}=T(s_t,a_t)), and a nonterminal transition changes
player. Terminal game outcome is (u\in\{-1,0,+1\}) from player (+1)'s
perspective. The training network sees player-relative features: the acting
player's pieces/role are canonicalized as “self”; thus the learned policy and
Q output are always from the current player-to-move perspective.

The action-value head (Q_\theta(s,a)) predicts the expected terminal return
for the player to move at (s), following the shared self-play policy after
the first action. Legal actions are masked before every probability
normalization, sampling step, policy loss and metric. A terminal state has no
action and is never passed through policy softmax.

For intermediate transitions the reward is zero. On the final action, reward
is the game result from the actor's perspective: +1 for a win, 0 for a draw,
and -1 for a loss. If a return target bootstraps at the next state, its
player-to-move value has the opposite perspective to the current actor. This
zero-sum sign convention is an explicit CAISSA adaptation and must pass
synthetic alternating-game tests before self-play.

## Policy-improvement target

The network emits legal policy \(\pi_\theta(a\mid s)\) and action values
\(Q_\theta(s,a)\). Given \(\alpha>0\) for entropy regularization and
\(\beta\geq0\) for reverse-KL regularization, define the target on legal actions
as

\[
\pi'_\theta(a\mid s)=\frac{\exp\{[Q_\theta(s,a)+\beta\log\pi_\theta(a\mid s)]/(\alpha+\beta)\}}{\sum_{b\in A(s)}\exp\{[Q_\theta(s,b)+\beta\log\pi_\theta(b\mid s)]/(\alpha+\beta)\}}.
\]

The target is detached from gradients. During self-play, sample from \(\pi'\);
the replay item stores the state, selected action, full legal target
distribution \(\pi'\), terminal return target and behavior-policy/version
identity. The policy loss is legal-action cross entropy
\(L_\pi=-\sum_{a\in A(s)}\pi'(a\mid s)\log\pi_\theta(a\mid s)\).

The paper's shared-backbone/separate-head design is the intended architecture.
The local CPU implementation uses a single affine-tanh shared encoder and
separate linear policy/Q heads; this is a feasibility adaptation, and it must
be matched across baseline and JEPA arms. The baseline code does not apply
gradient clipping because the paper's published implementation description
does not specify it; any later optimizer change requires a versioned amendment.
The published 6-block 128-channel ResNet, batch size 4096, and learning rate
0.001 are contextual target settings, not assumptions that local hardware can
replicate its scale.

## Lambda-return target

The paper defines its loss using a lambda-return but the finite-game experiment
uses one MDP perspective. To adapt the return to one shared policy controlling
alternating seats, define the bootstrap value
\(\bar V_\theta(s)=\sum_{a\in A(s)}\pi'_\theta(a\mid s)Q_\theta(s,a)\)
in the player-to-move perspective. For a recorded episode, compute backward
from the terminal reward. For nonterminal ply (t), use

\[
G_t^\lambda=r_t-\gamma\left[(1-\lambda)\bar V_\theta(s_{t+1})+
\lambda G_{t+1}^\lambda\right],
\]

because both next-state bootstrap and next-ply return are from the opponent's
perspective. At a terminal successor, \(G_t^\lambda=r_t\) with no bootstrap.
For the initial implementation use \(\gamma=1\), finite complete episodes,
and detached return targets. This recurrence is a documented adaptation; the
source paper's exact implementation details should be checked against its
published algorithm description before claiming reproduction. Synthetic
tests must compare it with explicit enumeration in small alternating trees.

The sampled action-value loss is
\(L_Q=(Q_\theta(s_t,a_t)-G_t^\lambda)^2\). Total fitting loss is
\(L=L_\pi+L_Q\), averaged over replay positions with each loss's own valid
count. The K0.1 code uses Adam with \(\beta_1=.9,\beta_2=.999,\epsilon=10^{-8}\)
and learning rate \(.001\), without gradient clipping. There is no JEPA,
state-transition predictor, minimax action-order loss,
search-generated target, or EMA in K0.1.

## Local implementation parameters and training exposure

For a first model-free pilot config, initialize
\((\alpha,\beta,\lambda)=(0.03,0.1,e^{-1/8})\), the paper's shared default.
No hyperparameter search occurs in fidelity tests. The paper used parallel
self-play across 1024 workers, up to 2048 transitions per worker, 6-block
ResNetV2 with 128 channels, batch 4096, Adam at 0.001; these settings and the
paper's reported compute scale cannot be reproduced by the local small NumPy
model. Any local pilot must disclose its deviations and match the *same local*
architecture, data opportunities, seeds, optimizer schedule and measured CPU
time between direct and JEPA variants.

To prevent target-policy leakage, collect \(\pi'\) and its generating
\((\pi,Q,\text{version})\) from the exact acting checkpoint. A replay window
may be reused only under a declared off-policy contract. K0.1 uses fresh
on-policy collection batches; it does not silently relabel old actions with a
new \(\pi'\). Generate each episode to terminal, then compute return targets.
Store seeds and player roles. Independent train/development/locked-final splits
are by whole game/trajectory before any window extraction.

## Required synthetic checks before game training

1. **Policy target algebra:** compare the numerically stable masked implementation
   against direct enumeration of the optimization objective on tiny legal-action
   sets; verify probabilities sum to one, illegal probability is exactly zero,
   and invariance to adding a constant to every legal Q value.
2. **Mask safety:** terminal/no-legal-action input is rejected; illegal logits
   never affect normalization or gradient; singleton legal action has
   probability one.
3. **Perspective/return:** enumerate short alternating zero-sum game trees,
   hand-calculate outcome returns, and verify player-role swap negates the
   perspective and leaves the self-canonical policy target invariant.
4. **Lambda endpoints:** \(\lambda=0\) uses one-step bootstrap; \(\lambda=1\)
   equals terminal Monte Carlo return (with signs); intermediate values match
   a direct weighted sum over n-step returns on a finite synthetic trajectory.
5. **Finite numerics:** extreme legal Q/log-policy values produce finite
   softmax targets and losses; empty/invalid episode and malformed mask fail
   explicitly.
6. **Small-game sanity:** on a deterministic count-up/alternating toy game,
   report policy and Q convergence against exact backward-induction values for
   several seeds. This is implementation validation only, never game-strength
   evidence.

## Baseline fidelity and claim limits

Before comparing with JEPA, an independent reviewer should inspect the equations,
target generation, perspective convention, action masking, replay identity,
and tests. Report any adaptation from the paper. A local small network or
single-game run is not a reproduction of the paper's results. The relevant
comparison is the incremental effect of adding JEPA to this same local baseline
under matched training-data exposure and measured compute. Simulator calls,
CPU wall time, parameter/update counts, prediction/backprop compute and
test-time inference costs are separate reported axes.

The primary KLENT-style policy/Q objective optimizes regularized expected
self-play returns. It is not a worst-case objective. Direct minimax-Q remains a
separate baseline; fixed-opponent match results remain separate from exact
small-game minimax regret/NashConv. Do not use the word “equilibrium” for a
finite-run win rate without an appropriate exploitability or gap calculation.

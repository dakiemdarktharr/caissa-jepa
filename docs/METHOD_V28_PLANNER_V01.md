# Method V2.8-P v0.1 - reply-set latent minimax planner

**Status: frozen development candidate; not novelty-certified, implemented, or trained.** This freezes the candidate and proposed planner-level estimand for the next model-blind gate. The locked-final sample size and confirmation schedule remain open until that gate passes. Do not change this version after looking at learned development results; any tuning requires a separately versioned candidate and a full development ledger.

## Scope and question

The target family is two-player, alternating-turn, fully observed, deterministic, zero-sum games with a finite legal-action list, known transition rule, explicit terminal condition, and player-relative outcome. Hidden information, simultaneous moves, stochastic transitions, and general-sum utilities are out of scope.

The falsifiable question is whether a JEPA-predicted latent for every legal own-action/opponent-reply branch improves fixed-budget depth-two max-min decisions over direct encoded-leaf value and matched non-JEPA dynamics. The opponent is treated as choosing a worst-case legal reply inside the search tree. This is not a behavioral opponent-response model, an expectation over a policy distribution, or an equilibrium guarantee. Exact root minimax regret is primary; fixed-suite win rate is secondary.

## State, actions, transition, and perspective

Let `s_t` denote the exact state of game `g`, `p_t` the player to move, `A_g(s_t)` the nonempty legal-action set in nonterminal states, `T_g(s_t,a_t)` the deterministic successor, and `u_g(s_T)` the terminal outcome from the absolute `+1` player perspective. Outcomes are in {-1, 0, +1}; the side-to-move target is `y_t = p_t * u_g(s_T)`. Training examples retain the exact serialized state, player-to-move, legal mask, game/rules version, trajectory ID, behavior policy identity/hash, actions, terminal outcome, and provenance.

The current shared board contract pads observations to an 8x8 grid with three side-to-move-relative feature planes and explicit board/rule descriptors; action IDs use `row*8+column`, with action 64 reserved for a forced Reversi pass. `GameSpec` remains the only authority for legality, transitions, and terminal states. A game unsupported by that feature/action contract needs a separately versioned adapter. The encoder is shared across admitted variants; no per-game encoder or checkpoint may be described as transfer. Only rule descriptors, not a learned game-ID embedding, are used for a prospective held-out-variant test.

## Model and planner

The online encoder `f_theta(x_t) = z_t in R^d` reads exact side-to-move-relative features. The target encoder `f_bar_theta` is an EMA copy updated after each optimizer step using `bar_theta <- tau*bar_theta + (1-tau)*theta`. The two-step predictor `g_phi(z_t, e(a_t), e(a_{t+1}), r_g)` receives separate one-hot action tokens for the current player and next opponent, rule descriptors `r_g`, and an explicit horizon/role marker. It predicts `z_hat_{t+2}`, the latent for the state after the opponent reply, when the original player is to move again. The value head `v_omega(z) in [-1,1]` uses the current/root player perspective. The learned model never proposes illegal moves: the exact adapter supplies legal actions and terminal outcomes at each enumerated node.

At a nonterminal root `s`, enumerate every legal `a in A_g(s)`, then every legal reply `b in A_g(T_g(s,a))`. For `s_ab = T_g(T_g(s,a),b)`, define

\[
\hat Q(s,a)=\min_{b\in A_g(T_g(s,a))}\begin{cases}
u(s_{ab})p_s,&s_{ab}\text{ terminal},\\
v_\omega(g_\phi(f_\theta(x_s),e(a),e(b),r_g)),&\text{otherwise},
\end{cases}\quad \hat a=\arg\max_{a\in A_g(s)}\hat Q(s,a).
\]

The terminal perspective and forced-pass case are unit-tested. This is a two-ply max-min cutoff planner; it does not solve the full game and does not estimate Nash equilibrium or exploitability. An inference decision is censored if any root action/reply branch required for comparison is not evaluated before budget expiration; do not score a fallback action as completed.

## Losses and optimization

Training begins only after the data, rules, split, opponent, compute, and power gates pass. For each sampled root, form the complete legal two-ply closure. The principal loss is

\[
L=L_{\mathrm{return}}+L_{\mathrm{policy/Q}}+\lambda_{J}L_{\mathrm{reply\text{-}JEPA}}+\lambda_{R}L_{\mathrm{collapse}}.
\]

`L_return` is squared error for bounded terminal/self-play lambda-return value targets, always converted to the target state's side-to-move perspective; it uses only observed trajectory targets and exact terminal labels. Use discount `gamma=1` and alternating lambda-return `lambda=exp(-1/8)`. `L_policy/Q` is legal-action-masked cross-entropy to the KLENT reverse-KL/entropy policy-improvement target plus unit-weight Q regression on the same observed training positions for every learned arm; use `alpha=0.03, beta=0.1`. It does not turn a sampled opponent action into a worst-case label. `L_reply-JEPA` is the root-balanced mean squared error between predictor output and a stop-gradient EMA target latent for every nonterminal legal `(a,b)` branch, with weight `lambda_J=1.0`. First average over branches within root, then over roots, so roots with high branching do not dominate. Terminal branches skip latent loss and retain their exact outcome. Missing targets are masked, counted, and never replaced by zero-valued latents.

The initial regularizer is a VICReg-style variance floor (target standard deviation 0.1, coefficient 0.1) plus off-diagonal covariance penalty (coefficient 0.01) on online and target latents. Report per-dimension standard deviation, covariance spectrum, effective rank, and collapse rate. A separately versioned development ablation will compare LeJEPA/SIGReg; SIGReg is prior art, not a claimed contribution, and its published guarantees are not assumed to transfer to correlated game trajectories. Predictor and target latent use the existing tanh-bounded convention and unnormalized MSE. Optimizer: Adam, beta=(0.9,0.999), epsilon=1e-8, gradient norm cap 5.0, initial learning rate 1e-3, batch size 64, target EMA tau=0.99, three deterministic seeds 17/29/43 for the pilot. Collect one on-policy batch under a fixed checkpoint, detach its KLENT policy/return targets, and perform exactly one epoch of shuffled minibatches; do not reuse stale targets across epochs. Any change is a new version with a recorded rationale and complete retained prior runs.

## Matched controls and ablations

The planner-level primary comparisons use identical trajectory IDs, complete legal-reply exposure, terminal outcomes, rule adapter, root schedule, value/policy target schedule, planner, inference budget, and optimizer-update schedule:

1. Direct encoded-leaf minimax value: encode exact (s_{ab}) and score with the same value head; no learned transition predictor.
2. Reply-set JEPA (candidate): predict EMA-target leaf latents from the root and both ordered actions; use those latents in the max-min planner.
3. Decoded-state dynamics: predict the fixed board/rule feature vector and apply a matched value head/planner.
4. Task-value latent dynamics: use the same predictor/planner but train only reward/value/policy targets, without latent-state matching (MuZero-style control).
5. JEPA-trained/no-JEPA-at-inference: identify representation-regularization effects separately from predicted-latent planning.
6. KLENT-style direct policy/Q: separate no-search learning baseline; include its same-search direct-Q variant only as an additional planner control after a fidelity review.

Predictor/decoder branches are not free extra labels: all arms receive the same complete branch states. Report both equal optimizer updates and equal measured compute, including CPU/wall time, model parameters, encoded leaves, predictor/value calls, legal transition generation, peak memory, training examples, and censored decisions. A win only on environment calls or only on the JEPA training loss is not a planning advantage. Exact rule search is an external reference and may demonstrate that learning is unnecessary at a given budget.

## Data splits, metrics, and stopping

Split full game trajectories and opponent families before making windows or counterfactual branches. Put all seat swaps, symmetric transforms, roots, H1/H2 targets, and legal counterfactual leaves from one connected source trajectory into one group. Hash both raw states and role-/symmetry-normalized states. Require zero overlap between train, development, model selection, and locked-final for every root/context/target/branch key. Do not reuse model-exposed V2 survey/pilot data as locked confirmation. Record all rejected, duplicate, terminal, and solver-timeout roots against the frozen quota.

Before training, require at least 100 symmetry-unique admitted roots and 50 beyond-depth roots per scientific game, then estimate paired clustered power from a frozen model-blind schedule. These are support floors, not a power result. The review's provisional 80% power / family-wise α=.05 target and five-point score margin apply only if the study justifies the practical meaning and defines how it maps to normalized exact regret; otherwise predeclare a scientifically justified regret margin before outcomes.

Primary metric: per-root minimax regret (V^*(s)-V^*(s,\hat a)), with exact complete root action values, role/seat pairing, and uncertainty clustered by trajectory, game, and training seed. Secondary metrics include exact action-ranking accuracy, latent horizon prediction error, value error, collapse/effective-rank diagnostics, compute curves, and paired fixed-opponent score by frozen opponent family. Report independent games separately and use a preweighted aggregate only if weights are fixed before outcomes. No post-hoc root removal, game weighting, opponent substitution, timeout recoding, seed selection, or locked-final opening is allowed.

Kill or narrow the claim if any game fails rule/runtime validation; the fresh bank lacks support/power; held-out groups overlap; exact root values are too often censored; reference matchups saturate or seat effects persist; the candidate fails against either direct encoded-leaf value or matched task-value dynamics at the same measured budget; or cross-game transfer does not survive held-out-family tests. A negative result is retained. A positive result supports only the tested games, budget, root distribution, and controls, not general JEPA superiority or Q1 acceptance.

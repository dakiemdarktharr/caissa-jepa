# Method V2.8-P v0.2 amendment: terminal branches, fair oracle coverage, and supervision contract

**Status: frozen design amendment for the development candidate; not novelty-certified, implemented, or trained.** Read this with `METHOD_V28_PLANNER_V01.md`. This amendment supersedes the affected v0.1 clauses. The next changes require v0.3 and a new review; do not tune this version against learned development results.

## 1. Immediate terminal after the root action

Let `p_s` be the absolute player to move at root `s`, and let `u(s')` be terminal utility from absolute player `+1`'s perspective. For each legal root action `a`, first form `s_a=T(s,a)`. Define the action score as

```text
Q_hat(s,a) = p_s * u(s_a)                                      if s_a is terminal
             min over b in A(s_a) of branch_score(s,a,b)        otherwise
branch_score(s,a,b) = p_s * u(s_ab)                             if s_ab=T(s_a,b) is terminal
                      v_omega(g_phi(f_theta(x_s),e(a),e(b),r_g)) otherwise
a_hat = argmax over legal a of Q_hat(s,a)
```

The `s_a` terminal branch is scored before any reply-set reduction; the minimization is defined only when `s_a` is nonterminal. Forced pass is an ordinary legal action token and is included in the reply set. Exact game rules provide terminal status and legal actions. The value head always predicts the original root player's perspective for planner branches, including after two plies; observed return/Q targets elsewhere retain the explicitly declared side-to-move perspective below.

## 2. Oracle coverage and estimand

The model-blind gate fixes the complete scheduled root population before running exact solvers. **Every scheduled nonterminal root stays in the denominator.** Solver timeouts, crashes, and malformed states are reported separately and never silently removed or replaced. Before a game can pass to locked-bank construction, the exact oracle must return every legal root-action value for 100% of its fixed development-gate roots within one common, predeclared node/time/cache budget. If coverage is below 100%, the game fails that gate; it may be reconsidered only in a separately versioned gate with a uniformly increased budget set without inspecting model outcomes. No metric is estimated on the solver-complete subset when the full scheduled population is incomplete.

The 100 symmetry-unique-root and 50 beyond-depth-root figures in v0.1 are minimum support floors, not the gate's entire scheduled population and not power evidence. The gate must schedule at least those counts in advance, then apply the all-roots oracle-coverage rule. An exact solver pass establishes oracle feasibility for that schedule only; it does not establish statistical power. The final sample size and paired clustered power calculation remain open until an independent model-blind audit freezes root, trajectory, opponent-family, game, seed, and seat grouping plus the practical regret margin. If the required support/power cannot be reached under permitted local compute, narrow the claim or pivot; do not filter roots by solvability.

## 3. Branch exposure and target contract across arms

For each accepted training trajectory/root ID, all learned arms receive the same exact state, player-to-move, legal action/reply masks, game/rules metadata, observed behavior actions, and terminal labels. The complete legal two-ply closure is generated once by the exact adapter and referenced by stable branch IDs. It is not expanded selectively for one arm. The generation record includes all root actions, all legal replies, immediate terminal-after-own-action branches, terminal-after-reply branches, nonterminal leaves, and any invalid/missing target count.

Targets differ by arm only where the objective requires it:

- **Reply-set JEPA:** each nonterminal branch targets the frozen EMA encoder's stop-gradient latent computed from that exact leaf state; terminal branches have no latent target and retain their exact utility. Training trajectory return and KLENT policy/Q targets are identical to other arms.
- **Decoded-state dynamics:** each nonterminal branch targets the same leaf's canonical fixed board/rule feature vector; terminal branches retain exact utility. The decoder output dimensionality and update budget are recorded.
- **Task-value latent dynamics:** receives the same branch IDs and exact terminal flags/utilities; it predicts the return/value target defined for the branch's player perspective from observed terminal/self-play lambda returns. It receives no latent or board reconstruction target. It receives no additional exact full-game root-action minimax label unavailable to other learned arms.
- **Direct encoded-leaf minimax value:** reads the exact leaf state through the shared encoder and applies the same value head; no transition predictor or latent branch target is used. It receives the same trajectory return/KLENT targets and branch-state exposure.
- **JEPA-disabled-at-inference and policy/Q arms:** use the same fitted training data and target schedule as their declared parent objective; inference disabling is the only change for the JEPA-disabled arm. Policy/Q remains a distinct no-search comparison.

The transition-supervision comparison is therefore explicit: the decoded control gets endpoint state features, JEPA gets endpoint EMA latents, and task-value dynamics gets task return targets. None gets extra branches, trajectory outcomes, exact minimax labels, optimizer updates, or planner calls. Report supervised scalar/vector dimensions, loss evaluations, and total target bytes per arm alongside measured FLOPs/time; equal states and steps alone do not imply equal information content. If that imbalance makes the claim uninterpretable in pilot, narrow the primary claim to predictive-target representation versus task-value dynamics and retain the decoded/direct controls as distinct architectural ablations, rather than relabeling the objectives as fully information-matched.

## 4. Alternating-player target equations

For state `s_t` with player `p_t`, trajectory outcome `u_T` is absolute-player utility. A side-to-move return target is `G_t = p_t * u_T` at terminal; for a bootstrapped continuation it is

```text
G_t^(lambda) = (1-lambda) * (-V_{t+1}) + lambda * (-G_{t+1}^(lambda))
```

with the return recursion initialized at the observed terminal utility from the corresponding side-to-move perspective; equivalently compute on absolute utility and multiply by `p_t` once. Use `gamma=1`; this recursion is over alternating turns and must flip sign exactly once per ply. Implementations must unit-test a forced win, forced loss, draw, pass, and a two-ply trajectory against the absolute-utility formulation.

For each observed training decision `(s_t,a_t)`, the Q regression target is the one-step backed-up value in the side-to-move perspective of `s_t`: `q_target(s_t,a_t) = -G_{t+1}^(lambda)`. The KLENT improvement target uses the Q values in that same side-to-move perspective, with legal-action masking, `alpha=0.03`, `beta=0.1`; it is a policy improvement distribution over observed legal actions, not a model of an optimal or adversarial opponent. The planner branch value separately uses root-player perspective as specified in section 1. Configs and output records must state which perspective each tensor uses; mixed-perspective batching is rejected.

## 5. Frozen sampler and behavior population required before fitting

No production fit begins until a versioned manifest pins: trajectory/root IDs and hashes; per-game and per-opponent-family quotas; the deterministic hash-based train/dev/model-selection grouping; seat/role swap schedule; legal-random and named project-owned search/self-play behavior policies with source/config hashes; checkpoint identity for any learned behavior policy; root sampling weights (uniform across groups first, then uniform within a group unless another rule is frozen); one-epoch batch order seed; and the exact target-generation and terminal-label source. Candidate model hyperparameter tuning can use only the development/model-selection groups. The locked-final groups remain unopened until the protocol, code, configs, analysis script, and confirmatory sample size are hashed and signed off by independent review.

## Acceptance impact

This amendment resolves the four critical ambiguities and the incomplete sampler flagged in `V28_SPLIT_PROTOCOL_REVIEW_01.md`: immediate root-action termination, selective solver coverage, branch supervision source, value/Q perspective, and frozen sampling inputs. It does not supply fresh data, prove support/power, show implementation correctness, establish JEPA superiority, or certify novelty. Before fitting, independent review must validate a passing fresh model-blind gate and confirm all locked-protocol fields. Any failure remains a stop condition.

# Research positioning: complete-reply latent consistency

Draft for discussion with the supervising professor, 2026-09-29. Prepared before
the complete V2.5 result was available, without inspecting partial scores.
Method/source reference: `METHOD_V25.md`, commit
`5102ea0588198f993874a495d18bfef1e868e2ec`. This document interprets the research
question; it does not amend the frozen experiment or report new results.

## Research question and possible contribution

Can allocating part of a predictive representation loss to the largest error
among all legal opponent replies improve bounded two-ply decisions, beyond
strong recurrent policy/value supervision and equally structured non-JEPA
controls? The prespecified candidate is `raw-tail`. Its auxiliary combines
the mean and maximum squared latent residual within a complete reply group.
The prediction targets are detached EMA representations of actual successors.

This is a proposed adaptation of established ideas, with priority unestablished.
The defensible contribution would be controlled evidence about **when this
specific allocation helps adversarial planning**, including negative outcomes.
The elementary bound below motivates measurement; it is not a new general
theory of games or proof that training will improve decisions.

The scope is deterministic, fully observed, alternating, zero-sum two-player
games with exact legal actions and terminal rules. Supplied own/opponent
actions condition transitions. There is no model of a particular opponent's
behavior, no expectation over an uncalibrated policy, and no claim of equilibrium
computation. The planner takes a worst-reply minimum over an exact finite tree.

## Established ingredients and remaining distinction

| Primary work | What is already established | Boundary for this project |
| --- | --- | --- |
| [MuZero](https://arxiv.org/abs/1911.08265) | Learned latent dynamics with recurrent task predictions and search across board games and Atari. | Multiple games and latent planning alone are not novelty. Our matched recurrent control is not a faithful MuZero reproduction. |
| [SPR](https://arxiv.org/pdf/2007.05929) and [EfficientZero](https://proceedings.neurips.cc/paper/2021/file/d5eca8dc3820cad9fe56a3bafda65ca1-Paper.pdf) | Predictive representation consistency; EfficientZero combines consistency with a planning system. | Calling recurrent latent consistency JEPA does not establish a new algorithm. Atari evidence does not establish a board-game gain. |
| [TD-JEPA](https://arxiv.org/html/2510.00739v1) | Temporal-difference latent prediction, policy conditioning and successor-feature connections for zero-shot RL. | Bellman/TD prediction and JEPA successor representations are existing work. V2.5 does not implement their zero-shot objective. |
| [Iterative VAML](https://proceedings.neurips.cc/paper_files/paper/2018/file/7a2347d96752880e3d58d72e9813cc14-Paper.pdf) and [VaGraM](https://arxiv.org/pdf/2204.01464) | Task/value-aware model objectives and value-gradient-weighted prediction errors. | Decision-aware prediction is established; scalar consistency must be a strong control. |
| [TEMPO](https://papers.nips.cc/paper_files/paper/2023/file/a995960dd0193654d6b18eca4ac5b936-Paper-Conference.pdf) | Metaweights world-model samples through latent value mismatch while retaining reconstruction. | Task-important sample weighting is not new. V2.5 uses fixed group aggregation rather than a learned metaweighter. |
| [WAKER](https://arxiv.org/html/2306.09205) | Connects worst-case model error and regret, prioritizing environment instances through error estimates. | Robust model-error allocation is prior art. V2.5's unit is a fixed own-action legal reply set, not an environment curriculum. |
| [Minimax Model Learning](https://proceedings.mlr.press/v130/voloshin21a.html) | Adversarial value/importance-weight classes for offline model evaluation and optimization. | Its model-learning adversary differs from a game's legal opposing player. Neither use of “minimax” proves algorithmic equivalence. |

The bounded search in `V25_ROBUST_PREDICTION_RESEARCH.md` did not establish an
exact predecessor for this complete-reply auxiliary. That is not evidence of
absence. A paper must position any positive result as a measured incremental
effect, pending broader priority review.

## Conditional relationship to decisions

Fix one root and own action a. For each nonterminal legal reply b, let u_ab be
the predicted latent, t_ab the EMA target, and d the latent dimension. Define

`ell_ab = ||u_ab - t_ab||² / d`,
`J_a = 0.5 mean_b(ell_ab) + 0.5 max_b(ell_ab)`.

Use the same value head v on both latent spaces. If v is L-Lipschitz, define
`epsilon_a = max_b |v(t_ab) - V*(s_ab)|`. Then the predicted own-action backup
error is at most `delta_a = L sqrt(2d J_a) + epsilon_a`. Minimum is nonexpansive
in the maximum norm; the maximum residual is at most `2d J_a` in squared norm.
With all own actions included, selecting the largest predicted backup gives
root regret at most `2 max_a delta_a`.

Exact terminal values enter both backups identically. Empty nonterminal subsets
contribute zero error; a terminal H1 branch uses its exact, sign-corrected
utility. The bound assumes a complete identical legal tree, consistent oracle
perspectives, and fixed evaluated parameters. Here `L <= ||w_value||₂` for the
tanh linear value head. Target oracle error is indispensable: accurate prediction
of an uninformative representation does not imply useful decisions.

This finite-tree inequality neither certifies unseen roots nor follows from a
small average training loss. Learned coordinates can rescale, the head norm can
grow, and a maximum residual may emphasize irrelevant dimensions. The reply
with maximum error also need not be the reply with lowest utility. We therefore
measure target error, head norms and backed-up oracle error, not latent MSE alone.

## Matched experiment and controls

All families share encoded policy/value supervision, initialization of matching
tensors, grouped data/symmetries and tuning opportunity. Recurrent families share
the same two-layer transition, recurrent policy/value losses and variance penalty.

| Family | Additional role |
| --- | --- |
| `direct` | Encoded policy/value reference; recurrent module unused. |
| `recurrent-pv` | Strong task-supervised recurrent control, without auxiliary. |
| `decoded-tail` | Same reply-tail aggregation on feature reconstruction. |
| `scalar-tail` | Same aggregation on value consistency, using the online head on detached EMA-encoded targets. |
| `raw-mean` | Uniform latent matching; isolates tail allocation. |
| `raw-scaled` | Uniform residual gradients with detached group scaling; same forward auxiliary scalar as tail at the same parameters. |
| `raw-tail` | Sole candidate: half mean, half maximum latent residual. |

The scaled control does not match gradient norms or evolving model trajectories.
H1 auxiliary counts once per eligible group. H2 auxiliary averages eligible
groups after excluding exact-terminal leaves. Common supervised weights retain
the original complete-group denominator. Complete replies are never pruned by
outcome or prediction error. The auxiliary itself uses no oracle importance
weights, but the overall pipeline is fully supervised.

The finite screen contains 42 cells: seven families, two rates and three paired
seeds, at one shared capacity and 160 epochs. No ablation can replace the
candidate, and no extension until a favorable result is part of this protocol.

## Evaluation and permissible conclusions

The original primary metric remains equal-game **exact-state action regret**.
It chooses one global learning rate per family, carried unchanged into hybrid
evaluation. Exact-state evaluation re-encodes real successors and bypasses learned
dynamics; improvement there supports representation regularization, not improved
latent simulation. Hybrid evaluation uses recurrent H2 latents while receiving
exact legality and terminal facts.

Both tracks require at least 0.05 regret-unit improvement over the strongest
control, improvement in both games against each control, and favorable paired
seed effects in at least two of three seeds. The mechanism also requires hybrid
improvement over uniform/scaled latent controls and lower backed-up oracle MSE
than every non-JEPA recurrent control. These are development gates, not significance
tests. Root bootstrap intervals condition on the three seeds and reused roots.

| Complete outcome | Permissible interpretation |
| --- | --- |
| All project and mechanism gates pass | An exploratory candidate merits independent selection and replication. |
| Hybrid mechanism passes; exact gate fails | A narrow hybrid-development finding; original project screen failed. |
| Exact improves; hybrid mechanism fails | No demonstrated improvement in learned-transition planning. |
| Scalar/decoded/scaled controls explain the gain | No supported JEPA-tail-specific mechanism. |
| Valid negative screen | Reject this specified recipe under the tested conditions; preserve the result. |
| Failure, censoring or collapse | Inconclusive grid, not evidence for superiority or inferiority. |

The benchmark uses full-oracle endgame closures in Connect4 4x5 and Reversi6:
509 training roots and 209 repeatedly used development roots. One shared model
over these two trained games does not establish unseen-game transfer, general
opening/middlegame play, engine strength or exploitability. Exact enumeration,
legality and terminal overrides materially assist every planner. Equal trees,
updates and data are not equal wall time/FLOPs; bounded CPU resource limits are
not evidence of computational advantage.

Any surviving result still needs independent selection, protected confirmation,
held-out game/variant transfer, broader positions, reference opponents and compute
accounting. Earlier negative grids remain part of the evidence. Publication
quality, including a Q1 target, requires that larger research case; acceptance
is not promised.

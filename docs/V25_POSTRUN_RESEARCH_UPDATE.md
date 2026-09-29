# V2.5 post-run research and next-question audit

Updated 2026-09-29 after the complete V2.5 result and independent rule audit.
This note is design research. It does not amend METHOD_V25, promote an ablation,
or authorize a confirmatory claim.

## What the new result changes

V2.5 raw-tail failed both its exact-state promotion screen and its hybrid
latent-planning mechanism screen. The candidate's exact-state regret point
difference versus direct was 0.001329 with an interval spanning zero; hybrid
regret was worse by 0.064565. The scalar-tail control also had lower backed-up
oracle MSE. Thus neither worst-reply latent allocation nor learned H2 transitions
show a current advantage on these small, exact-rule endgame banks. See
`V25_GRID05_RESULTS.md`.

The independent third-party Reversi audit passed on 100 seeded trajectories
each for board sizes4 and6, plus separate fixtures. It compared legal sets,
all legal successors, flips, counts, pass, terminal status, perspective and
invalid-action handling. This upgrades confidence in tested Reversi rule
compatibility only. It did not validate the project minimax solver, labels,
optimal actions, or neural performance. A compact public receipt is
`validation/REVERSI_REFERENCE_AUDIT01.json`; the hash-bound full receipt and
trajectory hashes remain in ignored local artifacts.

## Novelty update from primary sources

| Work | Direct overlap / implication | Remaining possible distinction |
| --- | --- | --- |
| [MuZero](https://arxiv.org/abs/1911.08265) | Action-conditioned latent dynamics, reward/value/policy prediction, and planning already span board games. Multi-game operation alone is not a novelty claim. | A specific JEPA contribution needs a controlled outcome MuZero-style task losses and search do not explain. |
| [Interpreting the Learned Model in MuZero Planning](https://arxiv.org/abs/2411.04580) | Adds observation reconstruction and state consistency to MuZero, with analysis on 9x9 Go and Outer-Open Gomoku. State consistency on board games is already directly studied. | A carefully isolated effect of JEPA target/predictor training under matched compute and game-held-out transfer could be incremental evidence, not a broad first. |
| [Transfer of Fully Convolutional Policy-Value Networks Between Games and Game Variants](https://arxiv.org/abs/2102.12375) | Directly studies parameter transfer between board-game variants and distinct games. Variant transfer by itself is not new. | A possible JEPA-specific question is whether action-pair latent prediction improves sample efficiency on genuinely held-out variants over shared policy/value and MuZero-style controls. |
| [Policy-Aware Simulator Learning](https://arxiv.org/abs/2605.29032) | 2026 work frames model learning as a zero-sum game against an exploiting policy, derives error-MDP active sampling, and argues for strategic robustness over average prediction error. It substantially overlaps any generic adversarial/world-model-robustness claim. | Our alternating perfect-information game player is conceptually different from an adversarial simulator, but that distinction alone is not a contribution. A joint formulation would need explicit theory and direct baselines. |
| [RAMBO-RL](https://arxiv.org/abs/2204.12581) and [A Game Theoretic Framework for Model Based RL](https://arxiv.org/abs/2004.07804) | Model-vs-policy adversarial learning is established in offline/model-based RL. “Adversarial JEPA” or worst-case prediction is not novel by label. | Different observations, action structure, or measurable theorem may motivate a scoped adaptation only after a complete related-work search. |
| [AlphaZero](https://arxiv.org/abs/1712.01815) and [MuZero](https://arxiv.org/abs/1911.08265) | Strong game-specific self-play/search systems already use exact rules or learned planning; a tiny solved benchmark risks making neural planning unnecessary. | A JEPA advantage must be measured in a regime where reusable learned state prediction has a defensible cost/coverage benefit. |

This is a focused update, not a systematic review or priority search. The
existing `RELATED_WORK.md`, `V2_PREDICTIVE_RESEARCH.md`,
`V2_GAME_EVALUATION_RESEARCH.md`, `V25_ROBUST_PREDICTION_RESEARCH.md`, and
their citations remain necessary. Exact uniqueness is unverified.

## Candidate next question, not yet a frozen method

The most defensible next direction from current evidence is **predictive
representation transfer across held-out deterministic game variants**, rather
than another loss-weight sweep on the same two adapters:

> Does action-conditioned JEPA pretraining on a family of deterministic,
> alternating, fully observed, zero-sum game variants reduce the number of
> labeled transitions or optimizer updates needed to reach a fixed minimax-regret
> threshold on held-out variants, relative to equally sized policy/value-only,
> MuZero-style task-prediction, and transition-supervised representation
> controls, at matched total training and inference compute?

This is only a research hypothesis. Cross-variant policy/value transfer is
already prior art. The JEPA-specific claim would have to be the incremental
sample-efficiency curve from future-state representation prediction, with
transfer measured on whole held-out rule variants, not another train/test
split of the same game roots. The present fixed 198-feature MLP and 65-action
head do not provide a sound variable-size game interface; a successor design
would need a shared spatial/token encoder, explicit game/action metadata, and
symmetry equivariance, with game-specific adapters/weights disclosed.

### Feasibility gates before code or training

1. Finish a primary-source related-work matrix covering general-game systems,
   transfer across board variants, predictive/state abstraction methods,
   successor features, and MuZero/SPR/JEPA variants; record dataset/code
   licenses at official sources.
2. Define a nontrivial procedurally generated game-variant family with one
   licensed reference implementation per rule family, finite exact oracle
   labels, and predeclared train/development/selection/final partitions grouped
   by game instance. No variant, seed, or symmetry-equivalent instance may cross
   partitions.
3. Prove that current exact solvers are not a cheaper complete answer for the
   intended difficulty range. Compare rule-aware search, direct value/policy,
   MuZero-style task prediction, JEPA, and random/untrained controls under the
   same state bank, train transitions, seeds, wall-clock and measured FLOPs.
4. Freeze a single primary sample-efficiency endpoint, e.g. training
   transitions to a preregistered equal-game regret threshold; also report full
   learning curves, area under the regret-versus-compute curve, zero-shot/few-
   shot transfer, per-variant effects, memory and inference latency. Candidate
   wins must replicate across seeds and improve on each held-out game family
   without selecting variants after seeing scores.
5. Develop on an openly declared development family. Lock all selection/final
   variants and their labels; do not adapt thresholds, rule generator or
   curriculum after seeing locked results. Only a passed selection study can
   justify a predeclared confirmatory run.

**Kill criteria:** stop or narrow the JEPA claim if (a) rule-based planning
dominates at equal practical cost; (b) JEPA does not improve the transition-
budget curve over the equally tuned task-prediction model; (c) gains disappear
on held-out variants or against per-family baselines; (d) performance depends
on train/test variant leakage; or (e) a finite novelty search finds the same
objective/protocol with no defensible incremental contribution. Negative
results can support a benchmark/measurement paper, but do not establish a
positive JEPA method.

## Literature sources inspected in this update

- Dann, Mansour & Mohri (2026), *Theoretical Foundations and Effective
  Algorithms for Policy-Aware Simulator Learning*, arXiv:2605.29032.
- Guei et al. (2024), *Interpreting the Learned Model in MuZero Planning*,
  arXiv:2411.04580.
- Soemers et al. (2021), *Transfer of Fully Convolutional Policy-Value Networks
  Between Games and Game Variants*, arXiv:2102.12375.
- Schrittwieser et al. (2020), *Mastering Atari, Go, Chess and Shogi by Planning
  with a Learned Model*, Nature; arXiv:1911.08265.
- Rigter, Lacerda & Hawes (2022), *RAMBO-RL: Robust Adversarial Model-Based
  Offline Reinforcement Learning*, arXiv:2204.12581.
- Lu et al. (2020), *A Game Theoretic Framework for Model Based Reinforcement
  Learning*, arXiv:2004.07804.

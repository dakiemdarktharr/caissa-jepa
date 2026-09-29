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
| [Dream with Abstractions (Dr. Abs)](https://doi.org/10.3233/FAIA251203) | ECAI 2025 proceedings, published online Aug. 2026; it pretrains a JEPA representation then regularizes DreamerV3/RSSM and reports out-of-distribution gains on ProcGen level seeds and distracting-control tasks. JEPA aiding zero-shot RL is already reported. | Its evaluated tasks use single-agent visual control with fixed rules/objectives; this is not evidence for adversarial two-player search or changed game rules. Any distinction needs a direct controlled comparison in that setting. |
| [V-JEPA 2 / V-JEPA 2-AC](https://arxiv.org/abs/2506.09985) | Video JEPA pretraining followed by action-conditioned latent-world-model post-training; reports zero-shot robot planning from image goals in new labs using robot interaction data. Action-conditioned JEPA planning is already demonstrated outside games. | It studies physical robot dynamics and goal-reaching, not sequential zero-sum decisions, adversarial replies, or minimax regret. A JEPA world-model novelty claim in general is untenable. |
| [TD-JEPA](https://arxiv.org/abs/2510.00739) | Policy-conditioned multi-step latent prediction from offline reward-free transitions for zero-shot RL across locomotion, navigation, and manipulation; the paper reports successor-feature connections and 13 datasets. Multi-policy predictive representation and zero-shot adaptation are direct neighboring prior art. | Its control tasks do not use two-player perfect-information zero-sum minimax; any game-specific claim must isolate the incremental role of legal alternating action sequences under matched game-planning controls. |
| [Transfer of Fully Convolutional Policy-Value Networks Between Games and Game Variants](https://arxiv.org/abs/2102.12375) | Directly studies parameter transfer between board-game variants and distinct games. Variant transfer by itself is not new. | A possible JEPA-specific question is whether action-pair latent prediction improves sample efficiency on genuinely held-out variants over shared policy/value and MuZero-style controls. |
| [Deep Learning for General Game Playing with Ludii and Polygames](https://arxiv.org/abs/2101.09562) | Reports a game-agnostic AlphaZero-style learning/search pipeline across hundreds of games using shared game/state/action interfaces. Shared encoders and multi-game board play are established precedent. | CAISSA can only distinguish itself through a measured JEPA-specific gain beyond such task-driven policy/value learning, not through adapter count. |
| [EfficientZero](https://arxiv.org/abs/2111.00210) and [SPR](https://arxiv.org/abs/2007.05929) | EfficientZero combines MuZero-style planning with SimSiam-like temporal consistency; SPR uses EMA targets and action-conditioned multi-step latent predictions. Both overlap the proposed mechanics of recurrent future-latent targets. | Their main benchmarks are Atari/visual RL rather than held-out deterministic board-rule variants. The proposed contribution, if any, is only a scoped controlled transfer result, not a first sequential JEPA or first latent rollout. |
| [Policy-Aware Simulator Learning](https://arxiv.org/abs/2605.29032) | 2026 work frames model learning as a zero-sum game against an exploiting policy, derives error-MDP active sampling, and argues for strategic robustness over average prediction error. It substantially overlaps any generic adversarial/world-model-robustness claim. | Our alternating perfect-information game player is conceptually different from an adversarial simulator, but that distinction alone is not a contribution. A joint formulation would need explicit theory and direct baselines. |
| [Learning to Play Sequential Games versus Unknown Opponents](https://proceedings.neurips.cc/paper/2020/hash/65cf25ef90de99d93fa96dc49d0d8b3c-Abstract.html) | Studies repeated sequential/Stackelberg games with unknown opponent response functions and adversarial sequences of opponent types, with regret guarantees. This is direct prior art for opponent-behavior adaptation, though not for JEPA or symmetric perfect-information minimax board play. | If CAISSA claims adaptation to a particular behavioral opponent, it must compare with response-function/policy-representation methods and use held-out opponent types; minimax regret cannot support that claim. |
| [Metric Policy Representations for Opponent Modeling](https://arxiv.org/abs/2106.05802) | Learns embeddings of other agents' policies from joint-action samples and reports generalization to unseen agents in three multi-agent tasks. Opponent-policy representation is established independently of JEPA. | A latent state transition conditioned on legal actions is not automatically an opponent-policy representation; keep state prediction and behavior prediction as separate modules and claims. |
| [RAMBO-RL](https://arxiv.org/abs/2204.12581) and [A Game Theoretic Framework for Model Based RL](https://arxiv.org/abs/2004.07804) | Model-vs-policy adversarial learning is established in offline/model-based RL. “Adversarial JEPA” or worst-case prediction is not novel by label. | Different observations, action structure, or measurable theorem may motivate a scoped adaptation only after a complete related-work search. |
| [AlphaZero](https://arxiv.org/abs/1712.01815) and [MuZero](https://arxiv.org/abs/1911.08265) | Strong game-specific self-play/search systems already use exact rules or learned planning; a tiny solved benchmark risks making neural planning unnecessary. | A JEPA advantage must be measured in a regime where reusable learned state prediction has a defensible cost/coverage benefit. |

This is a focused update, not a systematic review or priority search. The
existing `RELATED_WORK.md`, `V2_PREDICTIVE_RESEARCH.md`,
`V2_GAME_EVALUATION_RESEARCH.md`, `V25_ROBUST_PREDICTION_RESEARCH.md`, and
their citations remain necessary. Exact uniqueness is unverified.

The Soemers et al. preprint is especially close to the proposed next benchmark:
it studies fully-convolutional policy/value transfer among nine Ludii game
families, including board-size and win-condition variants, and reports zero-shot
and fine-tuned outcomes. Most cross-game zero-shot transfers were near zero,
while some same-family and selected cross-game transfers worked; negative
transfer also occurred. Runs used 20 hours, 8 GPUs and 80 CPUs per model, which
is outside this project's current local-compute scope. Therefore a game-variant
test is useful for falsifying transfer, but is not a new benchmark claim by
itself.

The Dr. Abs paper reports ProcGen returns of6.3±0.4 aggregate against CTRL
5.5±0.7, but its Dr. Abs figure uses3 seeds while most comparison figures use
10, and many baselines are taken from CTRL rather than rerun. It also reports
that JEPA's indirect target-encoder supervision takes more training steps before
the downstream dynamics/policy become useful. Treat this as published evidence
for a nearby visual-RL problem, not a directly comparable result for our game
class or a proof that JEPA improves compute efficiency.

The official [Ludii source repository](https://github.com/Ludeme/Ludii) currently
identifies its license as CC BY-NC-ND 4.0. That license contains non-commercial
and no-derivatives terms. We have not downloaded or executed Ludii, accepted
terms, generated data from it, or included its code/game files. It is excluded
as a default data/engine dependency. Any successor should use independently
implemented, project-owned procedural rules or another source with explicit
training and redistribution rights; a compatibility claim about the published
Ludii benchmark is not necessary to test the narrower JEPA hypothesis.

## V2.6 candidate question, not yet a frozen method

The broad question of policy/value transfer across game variants is already
prior art, and JEPA-based visual zero-shot generalization is also reported.
In a fully observed deterministic game, the complete Markov state already
contains all rule-relevant history; minimax explicitly searches both players'
successive actions. A model predicting the next two plies is therefore not an
opponent-behavior model. V2.6 must not conflate those problems. Its candidate
question is whether a shared JEPA representation trained on sequential own-move
and reply transitions improves adaptation and bounded minimax decision quality
on complete held-out rule variants. This remains a falsifiable transfer study,
not a novelty claim:

> At matched total training and inference compute, does training on sequential
> own-move/reply latent targets improve the held-out-variant exact minimax-regret
> versus compute curve, compared with the same shared encoder trained by
> policy/value-only, task-prediction, or explicit state-feature-prediction
> objectives?

This remains a research hypothesis. Split whole rule configurations,
trajectory families, and symmetry-equivalent instances before generating any
labels. A mere board-size holdout within the same rule family supports only a
within-family variant-transfer claim. Opponent-policy adaptation and response
distribution shift, if studied, require a separately identified behavioral
model, held-out opponent policies, and a metric distinct from minimax regret.
The repository already has a shared padded 198-feature encoder input and
65-slot legal-action interface for its project-owned board adapters up to 8x8;
V2.5 trains each run on both Connect4-4x5 and Reversi6. That finite interface
could support a first held-out-variant feasibility study, but V2.5 did not test
whole-rule-variant transfer, and no claim beyond those encoded rules is
supported. Larger boards or new rule families may require an explicit spatial/
token interface and new action semantics. Any per-game adapter or weight must
be disclosed.
Renderer-style OOD is not the main V2.6 question: Dr. Abs already studies visual
OOD in single-agent fixed-rule tasks, and adding pixels would confound this
symbolic transfer test.

### Feasibility gates before code or training

1. Complete the primary-source matrix for opponent-conditioned world models,
   minimax/model-based planning, transfer across board variants, and JEPA
   predictive objectives. The finite search must explicitly include policy-
   aware simulator learning, board-game state-consistency work, Dr. Abs, and
   general-game transfer. Record licenses only from official source pages.
2. As a bounded feasibility stage, specify and implement a project-owned
   deterministic variant generator with an exact minimax oracle and at least
   two distinct rule families before claiming cross-game transfer. Start with
   two or three configurations only to test interface and root coverage; this
   pilot cannot support generalization claims. Generate local data only; freeze
   variant-level partitions before labels, and keep locked-final labels out of
   model selection. Reject the design if exact search is already cheaper at the
   target decision quality.
3. Before fitting, freeze a shared encoder and action interface for the declared
   board-size/rule cap, and verify paired sequential transitions across both roles, legal masks,
   pass/terminal cases, value perspective, and symmetry transforms. Require
   baselines with the same encoder, parameter count, labels, schedules and
   training/inference budgets: policy/value-only, task-prediction (MuZero-style),
   explicit state-feature prediction, and JEPA. Use per-variant models only as
   an additional control.
4. Declare one primary endpoint on held-out variants before fitting (candidate:
   equal-variant macro AULC of exact minimax regret versus cumulative measured
   training compute, with matched fixed inference search/time). Add a separate
   equal-transition/update track to isolate objective effects, and report its
   AULC versus labeled exposures as a secondary sample-efficiency endpoint.
   Report per-variant curves, zero/few-shot transfer separately, paired seeds,
   exact-oracle cost, active FLOPs where measurable, wall time, memory, and
   all-legal policy/value diagnostics. Do not call regret or match score
   exploitability. Keep behavioral opponent adaptation as a separate future
   study.
5. Tune all families on a declared development split with the same finite
   opportunity. Selection and locked-final variants remain untouched until
   their access gates are met. A candidate advances only if JEPA beats each
   matched learned baseline by the predeclared practical margin, with the
   improvement replicated across seeds and both game families, and no per-game
   regression hidden by pooling. A positive development result only nominates
   an independent confirmation.

**Independent protocol review (2026-09-29):** the initial review correctly
identified that the V2.5 representation was not validated for held-out
variants, but source inspection shows its padded input/action interface already
supports project-owned board adapters through 8x8; V2.5 mixes Connect4-4x5 and
Reversi6 examples in each model fit. Reuse is therefore plausible for a bounded
feasibility study, not yet established as a general-game interface. Minimum
serious learned controls include direct
and recurrent policy/value, MuZero-style task-prediction/recurrent control, and
explicit state-feature prediction with the same encoder/capacity. Rule-aware
exact search is a separate system-level baseline; random/untrained models are
correctness references, not learned controls. All get matched data, labels,
parameter budget, optimizer updates and tuning opportunity; additionally show
wall-time/compute because equal node counts or updates alone are insufficient.
The suggested single development metric is held-out equal-variant macro AULC
of exact minimax regret versus cumulative measured training compute, with fixed
matched inference search/time. This directly addresses bounded-compute planning.
An equal-transition/update track and AULC versus labeled exposures are secondary
and help isolate sample efficiency from per-update cost.
Any practical margin and final sample size need a pre-run variance/power plan,
not an arbitrary reuse of the V2.5 0.05 threshold. Begin with 2–3 variants only
as an interface/coverage pilot, at least three seeds and a few fixed training
budgets; this is development evidence only, not confirmation.

**Kill criteria:** stop or narrow the positive-method claim if (a) exact
rule-based search dominates at equal practical cost; (b) JEPA does not improve
the compute-matched curve over task-prediction and feature-prediction controls;
(c) a recurrent policy/value, explicit transition, or ordinary transfer control
matches the effect; (d) a per-game model is stronger; (e) results depend on leakage or
selection; or (f) the finite novelty search finds the same sequential
action-pair objective and evaluation with no defensible added contribution.
Repeatedly tuning on exposed development roots is not evidence. A negative
result may support a benchmark/measurement paper, but cannot be called a JEPA
win.

## Literature sources inspected in this update

- Assran et al. (2025), *V-JEPA 2: Self-Supervised Video Models Enable
  Understanding, Prediction and Planning*, arXiv:2506.09985.
- Bagatella et al. (2025; ICLR 2026), *TD-JEPA: Latent-Predictive
  Representations for Zero-Shot Reinforcement Learning*, arXiv:2510.00739.
- Assran et al. (2023), *Self-Supervised Learning from Images with a
  Joint-Embedding Predictive Architecture*, CVPR 2023, arXiv:2301.08243.
- Dann, Mansour & Mohri (2026), *Theoretical Foundations and Effective
  Algorithms for Policy-Aware Simulator Learning*, arXiv:2605.29032.
- Sessa et al. (2020), *Learning to Play Sequential Games versus Unknown
  Opponents*, NeurIPS 2020, arXiv:2007.05271.
- Liu et al. (2021), *Metric Policy Representations for Opponent Modeling*,
  arXiv:2106.05802.
- Guei et al. (2024), *Interpreting the Learned Model in MuZero Planning*,
  arXiv:2411.04580.
- Soemers et al. (2021), *Deep Learning for General Game Playing with Ludii and
  Polygames*, arXiv:2101.09562.
- Ye et al. (2021), *Mastering Atari Games with Limited Data*, EfficientZero,
  arXiv:2111.00210.
- Schwarzer et al. (2020), *Data-Efficient Reinforcement Learning with
  Self-Predictive Representations*, arXiv:2007.05929.
- Soemers et al. (2021), *Transfer of Fully Convolutional Policy-Value Networks
  Between Games and Game Variants*, arXiv:2102.12375.
- Schrittwieser et al. (2020), *Mastering Atari, Go, Chess and Shogi by Planning
  with a Learned Model*, Nature; arXiv:1911.08265.
- Rigter, Lacerda & Hawes (2022), *RAMBO-RL: Robust Adversarial Model-Based
  Offline Reinforcement Learning*, arXiv:2204.12581.
- Lu et al. (2020), *A Game Theoretic Framework for Model Based Reinforcement
  Learning*, arXiv:2004.07804.

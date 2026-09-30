# V2.7 prior-art re-audit — 2026-09-30

This is a targeted primary-source re-audit, not a systematic review. It revises
the novelty assessment before any V2.7 model implementation or training. Search
scope: JEPA and action-conditioned representation learning, learned board-game
planning, competitive multi-agent latent world models, minimax/value-equivalent
model learning, and game-variant transfer. The reviewed work does not establish
that the candidate in this repository is novel. Search failure is not evidence
of novelty.

## Work-by-work comparison

| Work and source | Research question and method | Domain, data, baselines, and reported result | Relevance and remaining difference |
|---|---|---|---|
| **Deep Latent Competition (DLC)**, Schwarting et al., CoRL 2020 / PMLR 2021. [Proceedings](https://proceedings.mlr.press/v155/schwarting21a.html), [paper PDF](https://proceedings.mlr.press/v155/schwarting21a/schwarting21a.pdf), [arXiv](https://arxiv.org/abs/2102.09812). | Learns competitive policies through imagined self-play in a learned multi-agent latent world model. Joint transition conditions on both players' actions; the method also predicts opponent viewpoint and uses an opponent-action model. | Two-player visual racing with continuous control and partial observability. The paper reports racing experiments and policy iteration/self-play comparisons; it is not an enumerated, deterministic, fully observable board-game benchmark. This review does not transcribe numerical results because the accessible source extract used here did not include the full result tables; consult the paper before quoting numbers. | Directly defeats claims that a latent predictor conditioned on own and opponent actions, opponent-view prediction, or imagined competition is itself new. Remaining scope differences—turn-taking, exact legal-action sets, zero-sum board games—are not by themselves contributions. A new method needs a measured incremental objective/planning benefit. |
| **MA-JEPA**, Kaplowitz et al., arXiv:2609.33563, submitted 2026-09-27. [Preprint](https://arxiv.org/abs/2609.33563), [full text](https://arxiv.org/html/2609.33563). | Studies JEPA-style multi-agent world modeling: a joint predictor conditions on local states and synchronized joint actions and predicts target embeddings for agents' next observations; policies/critics use imagined latent rollouts. | Cooperative decentralized partially observable Markov game tasks on SMAC, with simultaneous actions and centralized training/decentralized execution. The paper compares with DMAWM, MAMBA, MAPPO, QMIX, and MAT over eight SMAC tasks; it reports top mean win rate on four of eight tasks, while e.g. 3s_vs_4z is reported as 74% ± 7.5 versus DMAWM 95.7% ± 2.3. These are source-reported results, not independently reproduced here. | Very recent and not peer-reviewed as of this audit date. It makes generic joint-action-conditioned JEPA and latent imagination in multi-agent games an especially unsafe novelty claim. Its cooperative, partially observed, simultaneous-action setting is outside the project's declared class; those differences do not establish that a turn-based zero-sum JEPA is novel. |
| **TD-JEPA**, Bagatella et al., ICLR 2026. [Proceedings](https://proceedings.iclr.cc/paper_files/paper/2026/hash/3d158f054ff0cb83397367234899db07-Abstract-Conference.html), [official code](https://github.com/facebookresearch/td_jepa). | Learns a policy-conditioned multi-step latent predictor and latent policies. | The paper evaluates 13 datasets / 65 tasks spanning locomotion, navigation, and manipulation, including zero-shot settings. Its official code identifies a CC BY-NC 4.0 license. | Sequential action-conditioned latent prediction and latent rollout are established. Conditioning on an extra player action alone is not a novelty argument. Do not copy code or use the noncommercially licensed artifact as a project dependency without a separate rights decision. |
| **SPR**, Schwarzer et al., ICLR 2021. [Paper](https://arxiv.org/abs/2007.05929). | Adds an EMA-target, action-conditioned multi-step latent prediction objective to representation learning. | Atari control with pixel observations; compared against established Atari representation/RL agents and ablations. | Establishes action-conditioned predictive representation objectives before JEPA branding. Use a close multi-step predictive non-JEPA baseline and identify the specific loss distinction. |
| **MuZero**, Schrittwieser et al., Nature 2020. [Paper](https://arxiv.org/abs/1911.08265), [official DeepMind summary](https://deepmind.google/blog/muzero-mastering-go-chess-shogi-and-atari/). | Learns latent dynamics plus reward, policy, and value signals chosen for planning, then searches in latent space. | Go, chess, shogi, and 57 Atari games; board-game evaluation reports performance matching AlphaZero on chess, shogi, and Go without supplied game rules. The original large-scale compute is a major reproducibility caveat for this repo. | Learned latent planning across several board games is established. A claim that JEPA merely enables a world model or planner to play multiple games is insufficient. A matched small-compute incremental comparison would be needed. |
| **AlphaZero**, Silver et al., Science 2018. [Author manuscript / source](https://arxiv.org/abs/1712.01815). | General self-play reinforcement learning with policy/value networks and tree search, using game rules. | Chess, shogi, and Go, each with its own rules and training; comparison includes leading domain engines/programs. | Multi-game board-game performance and game-specific training already have precedent. State explicitly whether any shared representation transfers or each game is independently trained. |
| **Value Equivalence Principle**, Grimm et al., NeurIPS 2020. [Proceedings](https://proceedings.neurips.cc/paper/2020/hash/3bb585ea00014b0e3ebe4c6dd165a358-Abstract.html), [paper](https://proceedings.neurips.cc/paper/2020/file/3bb585ea00014b0e3ebe4c6dd165a358-Paper.pdf). | Argues and formalizes that a learned model should preserve planning-relevant Bellman/value updates; state reconstruction can be unnecessary. | Theoretical/model-learning formulation with experiments comparing value-equivalent models to maximum-likelihood transition models; not a focused two-player board-game or JEPA study. | Strategic action ordering/value preservation is adjacent to established value-equivalence goals. A margin ranking loss over minimax action values may still be a useful instantiation, but must be compared to direct value-equivalent/task-prediction controls; naming it JEPA does not establish novelty. |
| **Model-Based Multi-Agent RL in Zero-Sum Markov Games**, Xie et al., NeurIPS 2020. [Proceedings](https://proceedings.neurips.cc/paper_files/paper/2020/hash/0cc6ee01c82fc49c28706e0918f57e2d-Abstract.html), [arXiv](https://arxiv.org/abs/2007.07461). | Gives sample-complexity guarantees for model-based learning of Nash-equilibrium values and policies in two-player zero-sum Markov games. | Tabular zero-sum Markov games; theoretical sample-complexity analysis rather than board-game JEPA experiments. | Worst-case/equilibrium objectives and model-based zero-sum planning are established. Keep equilibrium claims separate from fixed-opponent match outcomes and from opponent behavior prediction. |
| **Online Minimax Q Network Learning for Two-Player Zero-Sum Markov Games**, Zhu & Zhao, IEEE 2020. [IEEE Xplore](https://ieeexplore.ieee.org/document/9292435/). | Combines game theory, dynamic programming, and deep RL to learn Nash-equilibrium policies online in two-player zero-sum Markov games. | Function-approximation / Markov-game setting; the accessible IEEE record did not expose enough details to report exact environments, baselines, sample sizes, or numerical results here. | Direct neural minimax-value baseline family. The candidate must compare against a minimax-Q/value learner; action ordering under worst-case replies is not automatically new because that is central to minimax Q-values. |
| **Deep SOR Minimax Q-learning for Two-player Zero-sum Game**, arXiv:2511.16226. [Preprint](https://arxiv.org/abs/2511.16226). | Extends successive-over-relaxation minimax Q-learning with neural function approximation and gives finite-time analysis. | Two-player zero-sum Markov games; compares to minimax-Q learning and ablates the relaxation parameter. It reports faster convergence/lower error than the M2QN baseline in its experiments. The paper is a preprint, not treated as peer-reviewed here. | A direct modern neural minimax-Q baseline and objective precedent. Its stated algorithm is model-free and not JEPA or a deterministic board-game latent predictor, but any V2 study needs a fair minimax-Q/value baseline. |
| **A Two-Step Minimax Q-learning Algorithm for Two-Player Zero-Sum Markov Games**, Shreyas & Vijesh, arXiv:2407.04240. [Preprint](https://arxiv.org/abs/2407.04240). | Proposes a two-step minimax Q update and proves almost-sure convergence under assumptions. | Generated finite Markov games with 10/20/50 states, action sets of size five; compared with standard/generalized minimax Q variants over 50 episodes. Reports lower average error, with runtime tradeoffs. | Confirms a substantial non-JEPA minimax-learning literature; the repository must position its exact game-class and latent-representation question relative to these methods instead of treating its own minimax labels as new. |
| **After-Action Review for AI (AAR/AI)**, Khanna et al., ACM TiiS 2022. [ACM article](https://doi.org/10.1145/3487065), [author-hosted paper](https://faculty.ist.psu.edu/jxd6067/mypapers/J04-AARAI.pdf), [empirical study](https://faculty.ist.psu.edu/jxd6067/myPapers/J06-FindingFaults.pdf). | The underlying model-based RTS agent uses a learned transition model, learned leaf evaluation, and learned top-level action ranking inside minimax search; the 2022 study evaluates AAR/AI as a human process for localizing agent faults, not a new planner. | StarCraft II custom Tug-of-War RTS with two RL agents; sequential decision points and a 40-round cap. The human study compared AAR/AI vs. no AAR/AI with 65 domain-experienced participants, 10 seeded/exaggerated bug instances, identical explanations, and fault-localization outcomes. AAR/AI had higher bug recall and precision; participants were almost six times as likely to identify each particular bug. Those are human-study outcomes, not agent-strength results. | This is a close conceptual precedent for learned action ranking combined with a transition/value model and minimax search. It is not JEPA, not a board-game world-model comparison, and its empirical outcome is explainability. Still, a new learned minimax ordering component needs a precise distinction and matched baseline. |
| **Game-variant transfer**, Soemers et al. [Paper](https://arxiv.org/abs/2102.12375). | Studies policy/value transfer between board-game variants. | Board-game variants; this audit did not independently extract its exact split, baseline table, or results. Consult the source before making quantitative comparisons. | Cross-variant transfer is not inherently a JEPA contribution. The proposed study must report held-out game/variant transfer explicitly and compare with non-JEPA transfer controls. |

## Claim disposition

The following are **not supportable novelty claims**: first multi-game game
planner; first action-conditioned JEPA; first joint-action-conditioned latent
prediction; first competitive latent world model; first opponent-conditioned
imagination; or first minimax/model-based zero-sum learner.

The only candidate for further search is the conjunction of (a) training on the
complete legal counterfactual reply set at each sampled root and (b) a separate
JEPA-compatible objective that preserves ordering of worst-case action values,
then testing whether this changes decisions under a fixed planning budget. This
is not yet distinguishable from value-equivalence, minimax value learning,
MuZero-style planning signals, or other adversarial branch objectives. It is a
question to investigate, not a method claim. Before implementation, search the
primary literature for minimax-Q/model learning, action-gap or pairwise action
ranking, value-equivalent models in Markov games, and counterfactual branch-set
representation objectives. Search code and proceedings as well as preprints.

## Stop / pivot criteria

1. If a source describes an equivalent complete-reply-set objective with
   adversarial action-order preservation, stop claiming methodological novelty;
   consider a faithful replication or a benchmark paper.
2. If teacher-label coverage is low, varies systematically by root difficulty,
   or requires post-hoc root selection, do not train the candidate. Narrow the
   domain prospectively or pivot to outcome-only evaluation with no minimax-label
   claim.
3. If a matched direct value/task predictor reaches the same action ordering
   and decisions at equal data, updates, and compute, reject the JEPA mechanism
   claim even if the complete system plays well.
4. A positive exploratory result can only nominate a frozen candidate for
   model selection. It cannot establish cross-game superiority or equilibrium
   quality. Those require held-out games/variants, locked paired confirmation,
   and equilibrium metrics where claimed.

## Sources already in the repository

See [`V27_RESEARCH_POSITIONING.md`](V27_RESEARCH_POSITIONING.md) for earlier
related-work comparisons, objective sketches, and the distinction between
opponent response modeling, minimax planning, and policy-distribution
expectation. This re-audit supersedes its earlier realized-reply novelty
candidate; it does not supersede negative V2.5/V2.6/V2.7 feasibility evidence.

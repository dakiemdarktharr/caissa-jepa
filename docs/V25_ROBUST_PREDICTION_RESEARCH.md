# V2.5 design research: robustness across legal replies

2026-09-29. Prospective research note, not a frozen experiment or novelty claim.
The V2.4 screen did not establish a material additive-order obstruction. A later
architecture comparison must remain independent of that failed explanation.

## Additional primary-source search

Queries included adversarial world models/minimax latent consistency, worst-case
model learning, CVaR world-model errors, and the exact titles below. Search results
are leads, not an exhaustive systematic review; irrelevant adversarial-feature
learning and secondary summaries were excluded. Public sources were read only;
no implementation, data, checkpoint, dependency or license was acquired.

| Work / primary source | What it establishes in its own setting | Constraint on this project |
| --- | --- | --- |
| Farahmand, *Iterative Value-Aware Model Learning*, NeurIPS2018, [paper](https://proceedings.neurips.cc/paper_files/paper/2018/file/7a2347d96752880e3d58d72e9813cc14-Paper.pdf) | Fits transition models using the value functions arising during approximate value iteration; contrasts its tractable iterative formulation with robust optimization over a value-function class. | Task-aware or robust model loss is established prior art. A latent auxiliary must add evidence beyond scalar value consistency. |
| Voloshin, Jiang, Yue, *Minimax Model Learning*, AISTATS2021, [paper](https://proceedings.mlr.press/v130/voloshin21a/voloshin21a.pdf), [preprint](https://arxiv.org/abs/2103.02084) | Uses a decision-focused offline model loss to address distribution shift in off-policy evaluation and optimization. | Its minimax refers to the model-learning decision problem, not automatically an alternating-game equilibrium planner. Do not equate these meanings. |
| Rigter, Jiang, Posner, *Reward-Free Curricula for Training Robust World Models*, ICLR2024, [proceedings](https://proceedings.iclr.cc/paper_files/paper/2024/hash/0a2b3e9107efed3d361b29f300a903ff-Abstract-Conference.html), [official implementation](https://github.com/marc-rigter/waker) | Relates worst environment-instance model error to robustness and selects environments for exploration using model-error estimates. Evaluates robustness, efficiency and generalization. | Worst-error world-model optimization is not new. The proposed unit here would be a complete legal reply set at a fixed state/action, not WAKER's environment curriculum. |
| Guei et al., *Demystifying MuZero Planning: Interpreting the Learned Model*, arXiv2411.04580v2,17July2025, [paper](https://arxiv.org/html/2411.04580v2) | Studies reconstruction and latent planning in Go9x9, Gomoku and Atari. TableI sets state-consistency coefficient0 for board games and1 for Atari. | Board-game usefulness of added latent consistency cannot be presumed. Recurrent policy/value and decoded controls are necessary; observation accuracy alone does not establish strength. |
| Ye et al., *Mastering Atari Games with Limited Data*, NeurIPS2021, [paper](https://proceedings.neurips.cc/paper/2021/file/d5eca8dc3820cad9fe56a3bafda65ca1-Paper.pdf) | EfficientZero combines temporal consistency with value-prefix prediction and off-policy corrections in Atari100k. | Latent consistency alongside recurrent planning heads is established. Renaming it JEPA is not a contribution. |

An additional OpenReview lead (`33nhOe3cTd`, V-MCTS/Go9x9 consistency) appeared
in search snippets but opening required browser verification. It was not read
fully and cannot support detailed claims here. Keep it as an unresolved lead.

## Candidate mechanism and counterexamples

Uniform mean error can hide one harmful counterfactual reply. For a fixed value
head v with Lipschitz constant L, fixed target latents t_b, predictions u_b and
the same legal reply set, the elementary inequality is

`|min_b v(u_b) - min_b v(t_b)| <= max_b |v(u_b)-v(t_b)| <= L max_b ||u_b-t_b||_2`.

This is a conditional approximation statement, not a guarantee of oracle regret,
representation quality, multi-step search, generalization or a new theorem. The
target's own oracle error is additional. L can grow during learning, coordinates
can rescale, and scalar consistency may solve the relevant error more directly.
If per-coordinate MSE is used, its conversion to squared norm includes latent
dimension. Measure head norms and target/oracle error rather than hiding them.

Weighting only the oracle-worst reply is insufficient: another reply can become
spuriously pessimistic under the learned model and determine its minimum. A
uniform floor mitigates omission but does not prove a better minimax bound.
Complete-group mean/max residual aggregation covers that failure without adding
oracle labels to the latent auxiliary. However, decoded and scalar-target losses
must receive the same grouping/tail aggregation and task supervision.

Possible next comparison: one common nonlinear recurrent transition, shared
recurrent policy/value supervision, uniform JEPA versus half-mean/half-max JEPA,
matching scalar/decoded tail controls and direct/no-response controls. Grouped
sampling must be identical across methods, terminal overrides explicit, and
compute/parameter differences reported. No candidate or hyperparameter grid is
approved by this note. A separately frozen method and independent review precede
implementation/fitting. A favorable development result would still require
independent selection, transfer and confirmatory evaluation.

## Verified follow-up: latent prediction, weighting and robust model learning

Primary-source follow-up accessed 2026-09-29. The entries below distinguish
inspected methods from independently reproduced evidence; no external empirical
claim was reproduced. Paper bodies were inspected at the relevant method and
assumption sections, not claimed to have been exhaustively proof-checked.

| Work, date and original source | Inspected mechanism and novelty boundary |
| --- | --- |
| *TD-JEPA: Latent-predictive Representations for Zero-Shot Reinforcement Learning*, preprint2025, ICLR2026; [paper](https://arxiv.org/html/2510.00739v1), [proceedings](https://proceedings.iclr.cc/paper_files/paper/2026/file/3d158f054ff0cb83397367234899db07-Paper-Conference.pdf), [FAIR repository](https://github.com/facebookresearch/td_jepa) | Uses an off-policy temporal-difference latent objective with separate state/task encoders and a policy-conditioned predictor approximating successor features. Its theoretical claims concern an idealized setting with explicit assumptions; experiments cover ExoRL/OGBench, not alternating adversarial board games. This directly rules out novelty claims for JEPA plus Bellman/TD prediction, successor representations, or policy-conditioned long-term latent prediction alone. Paper method and author README inspected. |
| Voelcker et al., *Value Gradient weighted Model-Based Reinforcement Learning*, ICLR2022; [paper](https://arxiv.org/pdf/2204.01464), [author repository](https://github.com/pairlab/vagram), [author explanation](https://www.pair.toronto.edu/blog/2022/vagram-voelcker/) | VaGraM weights model prediction errors by value-function sensitivity to address the mismatch between observation accuracy and useful decisions. Its weighting is not a maximum over legal opponent replies. It nevertheless precludes presenting value-sensitive prediction-error weighting itself as new. Paper extraction and original lab explanation inspected; code was not executed. |
| *Task-aware world model learning with meta weighting via bi-level optimization*, NeurIPS2023; [official paper](https://papers.nips.cc/paper_files/paper/2023/file/a995960dd0193654d6b18eca4ac5b936-Paper-Conference.pdf) | TEMPO learns sample weights through a variational value-aware loss comparing prior/predicted and posterior/inferred latent-state values, while retaining the world model's reconstruction objective. Evaluations concern DMC/Atari. Task-aware weighting of world-model samples is established prior art; the proposed fixed reply-group residual weighting is a different, narrower instantiation, not evidence of priority. Method sections inspected. |
| Voelcker et al., *Lambda-models: Effective Decision-Aware Reinforcement Learning with Latent Models*, 2024 version; [paper](https://arxiv.org/html/2306.17366v3) | Studies latent implementation and value-learning choices underlying IterVAML/MuZero-style methods, including their differing behavior under stochasticity. These results reinforce the need to strengthen common architecture and recurrent task heads before attributing a difference to an auxiliary. The stochasticity results are not a reason to enlarge this project's deterministic-game scope. Methods inspected. |
| Ishibashi, Abe, Iwasaki, *Approximate State Abstraction for Markov Games*, preprint2024, AAAI2025; [paper](https://arxiv.org/pdf/2412.15877), [record](https://arxiv.org/abs/2412.15877) | Analyzes abstraction in two-player zero-sum Markov games through equilibrium duality-gap bounds and Markov Soccer experiments. Game-relevant abstraction guarantees are prior art; an empirical latent residual does not inherit those guarantees. Relevant PDF sections inspected. The HTML endpoint returned an unrelated formatting template and was rejected as method evidence. |
| Dann, Mansour, Mohri, *Theoretical Foundations and Effective Algorithms for Policy-Aware Simulator Learning*, preprint2026-05-27; [record](https://arxiv.org/abs/2605.29032), [paper](https://arxiv.org/html/2605.29032) | Proposes a model-versus-adversarial-policy minimax formulation, local critic errors and active collection targeting simulator exploitation. This is additional conceptual prior for adversarial, decision-focused model learning, not verified identity with the complete-reply auxiliary. Treat it as a preprint; proposed objectives inspected, proofs and empirical claims not independently validated. |
| Titonis, *WorldModel-ConnectX*, author repository created2026-08-11; [repository](https://github.com/alextitonis/WorldModel-ConnectX) | Documents an encoder/latent-dynamics/value model combined with adversarial ConnectX search and an exact endgame solver. This rules out a claim that putting a small latent world model into adversarial Connect4 search is itself new. Only author repository documentation was inspected; strength claims, implementation correctness and cross-domain assertions were not reproduced. |

Two qualifications supplement the earlier WAKER/MML entries. WAKER's reduction
assumes a suitable Markovian latent representation preserving policy returns;
its algorithm uses ensemble disagreement as a proxy for unknown dynamics error.
It does not establish that an arbitrary learned embedding's squared residual is
a calibrated error bound. MML's maximization combines value-function and
density-ratio function classes for distribution-shifted evaluation; these
adversaries are not the legal opposing player in the board game.

No inspected source established exact identity with half-mean/half-max latent
matching over every legal reply of a fixed own action. This bounded search does
not establish absence of prior art or justify a uniqueness claim. SPR,
EfficientZero, TD-JEPA, decision-aware model learning and robust error allocation
already supply the surrounding ingredients. A defensible incremental claim
would require the matched empirical contrasts specified separately in METHOD_V25.

Search accounting for this follow-up: 100 requested result slots in successful
Exa searches, plus 40 requested slots in four rejected calls missing a required
schema field. These are 140 requested slots, not 140 papers, unique sources or
fully read documents. Duplicate hits, secondary summaries and irrelevant topics
were excluded from substantive evidence. URL fetches are separate from that
search-slot count. No dataset, external source code, dependency or credential
was installed or acquired for training.

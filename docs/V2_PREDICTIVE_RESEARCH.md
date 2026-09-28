# V2 research: predictive representations for bounded adversarial planning

Research date: 2026-09-29. Status: targeted primary-source review and proposed
experiments, **not evidence of a v2 performance gain**. This complements
`RELATED_WORK.md`, `BENCHMARK_V2_SPEC.md` and `V2_RESEARCH_CONTROL.md`.

## Main finding

The best supported next step is to align the training distribution and objective
with the planner's actual counterfactual queries. A model trained on one observed
reply at each state is not thereby trained on the alternative replies searched
by minimax. Recurrent consistency, normalized latent losses and value-aware
objectives are established prior art. They are sensible controls and engineering
choices, not sufficient novelty claims.

The v1 receipt reports an exact-search ceiling, no full-JEPA advantage, and worse
hybrid Reversi decisions than direct re-encoding. Those observations motivate
the hypotheses below. They do not prove which mechanism caused failure. In
particular, Monte Carlo outcomes under random/immediate-win behavior are not
minimax labels; low error on those outcomes does not certify worst-case planning.

## Search method and coverage

Five Exa searches each requested ten results (50 result slots, **not 50 unique
papers read in full**). Search angles: SPR/EfficientZero recurrent consistency;
value-aware learning/bisimulation; action-conditioned JEPA planning shift;
counterfactual adversarial board-game dynamics; value equivalence theory.
Primary paper/proceedings URLs were fetched for the nine works below. Secondary
roundups and Exa library summaries were not used as final evidentiary sources.
Original-text extracts rather than complete page-by-page readings are identified
explicitly. This is a focused design review, not an exhaustive systematic review.
One PMLR value-aware-loss URL failed; two candidate arXiv identifiers resolved to
unrelated papers and were discarded. No claim depends on those pages.

## Evidence matrix

| Work and primary source | Design, domain and evidence inspected | Implication and overlap with v2 |
| --- | --- | --- |
| Schwarzer et al., **Data-Efficient Reinforcement Learning with Self-Predictive Representations**, ICLR 2021. [Paper](https://arxiv.org/pdf/2007.05929), [author code](https://github.com/mila-iqia/spr) | Full-text extracts: methods and ablations. SPR adds recurrent action-conditioned latent prediction to Rainbow, EMA targets, projection/prediction heads and cosine/normalized-L2 matching. Atari100k results and ablations compare prediction depths, target construction and losses. Unnormalized quadratic loss performs near random in their setting; projections and multistep prediction matter. | Strongest prior-art control for claiming JEPA benefit. Use a shared one-step predictor recursively during both training and inference; compare normalized projected loss against raw latent MSE. Their empirical findings concern visual Atari, not an already compact symbolic board. Do not transfer their numeric gains to CAISSA. |
| Ye et al., **Mastering Atari Games with Limited Data (EfficientZero)**, NeurIPS 2021. [Paper](https://arxiv.org/html/2111.00210v2), [author code](https://github.com/YeWR/EfficientZero) | Full-text extracts: sections 2,4,5. Adds SimSiam-style projected temporal consistency to MuZero, recurrent unrolls, value-prefix prediction and off-policy value correction. Atari100k and DMControl comparisons include a matched implementation of MuZero. The paper also notes earlier consistency results were mixed on low-dimensional environments. | Directly precludes a claim that adding latent consistency to a planning model is new. A fair local control needs the same policy/value targets, transitions, recurrence and capacity with consistency disabled. Consistency may help sparse supervision; symbolic tiny-games are a materially different test. |
| Schrittwieser et al., **Mastering Atari, Go, Chess and Shogi by Planning with a Learned Model (MuZero)**, Nature 2020. [Paper](https://arxiv.org/abs/1911.08265) | Full-text introduction/method extracts. Learns recurrent hidden transitions supervised by reward, search policy and value, without observation reconstruction. Demonstrates strong performance in Atari and multiple board games. | A non-JEPA recurrent policy/value dynamics baseline is essential. Cross-game applicability and action-conditioned latent planning alone are established. A small supervised NumPy analogue must be labelled an analogue, not a reproduced MuZero system. |
| Gelada et al., **DeepMDP: Learning Continuous Latent Space Models for Representation Learning**, ICML 2019. [Proceedings](https://proceedings.mlr.press/v97/gelada19a.html) | Proceedings abstract and metadata only. Reward prediction plus next-latent-distribution prediction, representation/model guarantees under stated assumptions; synthetic latent recovery and Atari auxiliary learning experiments reported. Full theorem assumptions were not independently checked here. | Dense latent prediction with value/reward learning substantially predates JEPA terminology. It motivates checking collapse and task sufficiency separately. Do not cite its guarantees as applying automatically to deterministic minimax or our finite neural model. |
| Grimm et al., **The Value Equivalence Principle for Model-Based Reinforcement Learning**, NeurIPS 2020. [Paper](https://arxiv.org/abs/2011.03506) | Full-text definition/introduction extracts. Models are equivalent relative to specified functions/policies when their Bellman updates match. Theory and illustrative experiments study allocating limited model capacity to planning-relevant information rather than generic transition likelihood. | Predictive latent accuracy is only an auxiliary metric. Test value error on counterfactual successors and root decision regret. A value-only dynamics control distinguishes a JEPA representation contribution from simply adding future-value supervision. MDP policy expectation is not automatically adversarial minimax. |
| Grimm et al., **Proper Value Equivalence**, NeurIPS 2021. [Paper](https://arxiv.org/abs/2106.10316) | Abstract and bibliographic record only. Extends equivalence to repeated Bellman operators and the limiting value-function case; connects the resulting loss to MuZero and reports a practical improvement. | Matching a single behavioral value function can be insufficient for policies encountered in planning. Multiple response policies or exact small-game minimax targets are sensible probes, but no theorem is imported without checking the full assumptions. |
| Grimm, Barreto and Singh, **Approximate Value Equivalence**, NeurIPS 2022. [Proceedings paper](https://papers.neurips.cc/paper_files/paper/2022/file/d53538ba21c05fa361d2b21704172753-Paper-Conference.pdf) | Full-text abstract/introduction/theory extracts. Replaces exact Bellman constraints by tolerances, derives relationships and performance bounds, and studies limited-capacity tradeoffs. More functions can be worse when capacity cannot fit them accurately. | Avoid assuming that more horizons, larger forks or extra heads must help. Record data-support and approximation error as breadth increases. A bounded low-CPU sweep should vary one mechanism at a time and retain negative results. |
| Chen et al., **Adversarial Counterfactual Environment Model Learning**, NeurIPS 2023. [Proceedings paper](https://proceedings.neurips.cc/paper_files/paper/2023/file/df927a06a0d9f5f06d9cd4a91ce58e56-Paper-Conference.pdf) | Full-text introduction and objective extracts. Shows behavior-policy selection bias can mislead even one-step model-based action selection. Adversarial weighted risk minimization and its practical GALILEO approximation target counterfactual distributions; synthetic, continuous-control and application studies are reported. | Strong mechanistic support for testing counterfactual support, not proof that it explains v1. Here exact legal rules make direct intervention data available: enumerate/sample alternative legal actions from train roots. That is simpler than copying their offline estimator. Their adversary maximizes model error, which is different from a zero-sum opponent minimizing utility. |
| Assran et al., **V-JEPA 2: Self-Supervised Video Models Enable Understanding, Prediction and Planning**, 2025 preprint (current fetched text revised 2026). [Paper](https://arxiv.org/abs/2506.09985), [author code](https://github.com/facebookresearch/vjepa2) | Full-text abstract/introduction extracts. Large-scale action-free video representation learning followed by action-conditioned robot-world-model post-training; frozen representations support image-goal planning. | Action conditioning and JEPA planning already exist. Staged representation learning versus joint training is a useful later ablation, but this robot/video result does not establish board-game adversarial transfer or justify a costly pretraining dependency. |

## Testable v2 hypotheses, ordered for a small CPU budget

### H1: support the branches the planner actually queries

From each eligible training root, construct legal `(our action, reply)` forks
using the exact adapter. Start with uniform, deterministic seeded fork sampling
or full enumeration when small. Include legal-but-suboptimal replies rather than
only trajectory continuations. Keep terminal branches with explicit masks and
correct player-to-move value signs. Any child value labels must come from the
declared teacher/minimax procedure; do not copy a trajectory outcome to a
counterfactual branch.

The diagnostic is prediction/value error on **unseen roots and their full legal
forks**, stratified by observed-versus-counterfactual branch, plus root action
regret. This hypothesis fails if fork coverage improves latent errors without
improving a held-out decision metric, or if any gain also occurs with the same
fork data in the strongest non-JEPA baseline.

All variants receive identical roots, branches, policy/value labels and exposure
counts. Report oracle transition and label-generation cost separately. A direct
policy/value learner must train on the same successor states; otherwise extra
data availability, not JEPA, can explain the result.

### H2: use one compositional dynamics operator

Train `z_hat_1 = g(z,a)` and `z_hat_2 = g(z_hat_1,b)` with loss at each supported
horizon; compare against separately conditioned H1/H2 outputs with matching
capacity and updates. This directly matches recurrent latent planning. A small
residual or multiplicatively action-gated predictor can be tested after the
shared recurrence baseline; additive concatenation is not guaranteed to capture
board-dependent action effects efficiently.

Recurrence and action gating are established modeling ideas. Their combination
does not establish uniqueness. Horizon masks, terminal handling and opponent
perspective require explicit tests. Zeroing an opponent action is an ablation,
not an opponent model or minimax solution.

### H3: decouple predictive geometry from decision features

Use a small projection/prediction head with normalized latent matching while
the policy/value head consumes the unprojected state representation. Compare
raw-MSE, normalized-MSE and zero-latent-loss at identical data/architecture,
initialization and optimization budgets. Continue measuring rank, covariance,
norms and gradients; normalization alone does not certify noncollapse.

The SPR evidence makes this an informed hypothesis, but its small-symbolic-game
benefit is unknown. If only direct policy/value generalization improves, claim
representation regularization; if latent planning additionally improves, show
the incremental gain separately.

### H4: preserve adversarially useful distinctions

A possible later candidate is a fork-relative latent loss matching differences
between the predicted successors of two replies to differences between their
stop-gradient target encodings. This asks the representation to retain response
contrasts rather than only average successor similarity. It is a **proposal**
requiring a separate novelty search and frozen amendment before fitting.

Compare against (a) ordinary pointwise latent matching on the same pairs,
(b) direct value-difference/ranking supervision, and (c) random paired states.
Hold total branch exposures and loss scale fixed. Do not introduce exact
minimax labels only for the JEPA variant. Reject the extra term if improvement
vanishes against these controls or if it merely tracks more supervision.

## Minimum control matrix and evaluation protections

| Contrast | What it can isolate | What must remain matched |
| --- | --- | --- |
| Direct policy/value vs recurrent value dynamics | Added dynamics/value prediction | Teacher labels, successor exposure, encoder capacity, tuning opportunities |
| Recurrent value dynamics vs same model plus JEPA loss | Incremental predictive representation objective | Parameters other than projection head, forks, losses shared by both, seed and update schedule |
| JEPA vs decoded dynamics | Latent targets versus observable-state reconstruction | Branches, dynamics capacity, policy/value targets, optimization budget |
| Trajectory-only vs counterfactual forks for every family | Data distribution intervention | Root pool and an explicit matched transition/exposure budget |
| H1-only unrolled vs recurrent multihorizon | Training horizon matching | Inference recurrence, train-step budget, supported target masks |
| Exact re-encoding vs latent rollout with one checkpoint | Contribution and failure of learned rollout | Root/schedule, legal-state tree, depth/nodes and timeout/censor policy |
| Learned variants vs zero/handcrafted leaf search | Whether benchmark needs learned evaluation | Legal tree, tie handling, depth/node budget |

1. Build a non-ceiling benchmark before model selection, using oracle-only
   difficulty strata and disjoint roots. Do not select positions because JEPA
   happens to beat the baseline there.
2. Every counterfactual successor used for training enters the overlap audit.
   Split before expansion where possible; quarantine cross-split canonical
   states under symmetry and role normalization. Outcome labels are not latent
   input features. Preserve source-trajectory grouping and report discarded
   support. Do not purge test states only after viewing errors.
3. Compare both equal-update/data budgets and a separate compute-matched track.
   Equal parameter count is not equal FLOPs or wall time. CPU measurements must
   use a pinned thread count; report median and tail decision time, exact-rule
   transitions, neural calls, censor counts and memory.
4. Keep a development attempt ledger with every variant, seed and tuning choice.
   Give baseline families comparable tuning opportunity. Select once using the
   selection stage; only then run a frozen independent final protocol. Repeatedly
   redesigning around the final set turns that set into development data.
5. Aggregate by game with prespecified weights and by independent seed/root
   clusters. Thousands of branches from a handful of roots are not thousands of
   independent samples. A positive pooled difference must not conceal a material
   loss on a game. Include full uncertainty and failure counts.
6. Establishing a v2 planning advantage requires an actual measured improvement
   over the strongest matched baseline, followed by independent replication.
   No source above promises that JEPA can satisfy this on the current hardware,
   games or dataset. If the controlled result remains negative, retain it and
   narrow the claim rather than weakening the baseline.

## Candidate contribution boundary

An appropriately cautious working contribution is an audited comparison of
branch-conditioned predictive representations under bounded minimax in multiple
small deterministic games, with shared parameters and explicitly measured
transfer. A new branch-relative objective would need additional prior-art review
and ablations. Neither recurrent consistency, JEPA action conditioning, multiple
games, nor better results after unrestricted tuning establishes methodological
novelty. Strong evidence might justify a professor-facing research candidate;
publication venue suitability remains a separate judgment.

Search accounting: 5 `web_search_exa` calls x10 requested results =50 slots.
Nine primary works retained in this focused matrix. No paid setup, external
dataset download, author contact or code change was performed for this review.

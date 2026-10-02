# Research positioning and search record

Search date: 2026-10-01 (targeted refresh). Status: scoped review for design v1, **not an exhaustive systematic literature review or a verified novelty claim**. Sources below are original papers, author repositories or official dataset hosts. Abstract-only entries are explicitly distinguished from full-text inspection. No published score is a local result.

## Search method and limits

Search families: JEPA foundations; predictive auxiliary objectives in RL; board-game planning; opponent/empirical game theory; transfer; statistical evaluation; official dataset licenses. Queries included `JEPA chess paper`, `JEPA board games`, `JEPA two player adversarial board game latent planning 2026`, `self predictive representations EfficientZero`, `Polygames zero learning transfer`, `OpenSpiel evaluation`, and original paper IDs. Followed primary-source links from results; discarded mirrors as evidence when originals were available. Checked direct chess prior art and recent 2026 planning preprints separately. No language/venue-complete index or forward-citation census was performed; that remains a paper-submission gate.

Full text inspected for the nearest chess method RePAIR and the EfficientZero consistency objective. Primary abstracts inspected for the remaining papers; detailed baseline/result replication is pending and cannot be implied from an abstract. Official repository/documentation inspected for Polygames, OpenSpiel licensing, Lichess and UCI data. Search stops here for the first design because key novelty threats are identified; it resumes before freezing confirmatory hypotheses and submission.

Follow-up during the bounded pilot: inspected full-text method/results passages
for MuZero and SPR, the I-JEPA architecture/collapse sections, and LeJEPA's SIGReg
construction. The initial matrix records first-pass depth; the notes below update
those four entries. This was literature review only; the running pilot design was
not altered after fitting began.

### Nearest-objective full-text checks

- [MuZero v2, Sections 3–4](https://arxiv.org/html/1911.08265v2): the recurrent
  action-conditioned model trains reward, policy and value at multiple unrolled
  steps; it does not require observation reconstruction or an explicit latent
  matching objective. Board-game experiments use five unrolled training steps
  and 800 search simulations. Thus our value-dynamics control probes a small
  part of this distinction, but lacks search-improved targets, learned reward
  and MuZero's architecture. It must never be labelled a MuZero replication.
- [SPR v3, Sections 2 and 4](https://arxiv.org/html/2007.05929v3): recurrent
  action-conditioned predictions match EMA target projections with normalized
  similarity; losses truncate at episode boundaries. The original evaluation
  covers 26 Atari games at 100k environment steps with ten SPR seeds and compares
  augmentation/no-augmentation controls. Our affine direct-H2 unnormalized MSE
  and behavior-policy supervision differ. A recurrent multi-step consistency
  control trained through both turns remains necessary; recurrent H1 inference
  alone does not provide that training control.
- [I-JEPA v3, Sections 2–3](https://arxiv.org/html/2301.08243v3): target-block
  positions condition the predictor, target encoders use EMA, and architectural
  asymmetry addresses collapse. Our action slots and supervised heads are an
  adaptation; merely using an EMA target does not establish planning benefit or
  a collapse guarantee in the tiny-game setting.
- [LeJEPA v3, Section 4](https://arxiv.org/html/2511.08544v3): SIGReg uses random
  projections and empirical characteristic-function discrepancy against Gaussian
  targets. Its construction is substantially different from the pilot's variance
  floor. The pilot is neither SIGReg nor a theoretical LeJEPA reproduction; the
  legacy bounded-tanh approximation cannot inherit the original claims.

## Related-work matrix

| Work and primary source | Question / design | Domain and data | Baseline / metric / relevant evidence | Difference and consequence for CAISSA |
| --- | --- | --- | --- | --- |
| Assran et al. (2023), [I-JEPA, arXiv:2301.08243](https://arxiv.org/abs/2301.08243), CVPR | Predict semantic target-block embeddings from context; EMA target | ImageNet and downstream vision | Linear classification and dense tasks; scalable image representations; abstract inspected | Provides latent prediction precedent, not actions/opponent/search evidence |
| Assran et al. (2025), [V-JEPA 2, arXiv:2506.09985](https://arxiv.org/abs/2506.09985) | Video pretraining then action-conditioned latent world model | Internet video; DROID robot interaction | Video understanding and robot goal-planning success; abstract inspected | Action-conditioned JEPA planning already exists. Robot goal-reaching is not minimax |
| Balestriero & LeCun (2025), [LeJEPA v3, arXiv:2511.08544](https://arxiv.org/abs/2511.08544v3), [author code](https://github.com/galilai-group/lejepa) | Prediction plus isotropic Gaussian distribution matching using SIGReg without EMA | Vision datasets/architectures | Frozen-backbone linear evaluation across many architectures; abstract inspected | Existing bounded-tanh chess adaptation does not inherit the theory. v1 new pilot uses EMA and a declared variance regularizer instead |
| Silver et al. (2017/2018), [AlphaZero preprint, arXiv:1712.01815](https://arxiv.org/abs/1712.01815), Science journal version | Policy/value self-play plus known-rule MCTS | Chess, shogi, Go; self-generated games | Matches against established engines; abstract and official project summary inspected | Multiple board games with one algorithm is old. Separate per-game networks do not demonstrate shared-weight transfer |
| Schrittwieser et al. (2019/2020), [MuZero, arXiv:1911.08265](https://arxiv.org/abs/1911.08265), Nature | Learned reward/policy/value-relevant dynamics plus search | Atari, chess, shogi, Go; self-play/interactions | Atari scores and board-game strength versus AlphaZero; abstract inspected | Action-conditioned latent planning across games is a direct novelty threat. A JEPA consistency loss alone needs a strong control |
| Ozair et al. (2021), [Vector Quantized Models for Planning, ICML / PMLR 139](https://proceedings.mlr.press/v139/ozair21a.html), [paper PDF](https://proceedings.mlr.press/v139/ozair21a/ozair21a.pdf) | Learn discrete latent variables for environment responses and plan with stochastic MCTS over agent actions and response latents | Chess in two-player and single-player settings; DeepMind Lab | Reports better performance than offline MuZero on a stochastic chess interpretation where the opponent is part of the environment; full PMLR abstract and two-player chess passage inspected | Directly covers latent planning over both players' actions in chess and an opponent-response-as-dynamics variant. It uses a discrete VQ model rather than JEPA and differs from exact deterministic minimax; nevertheless it makes opponent-conditioned latent planning a high-risk novelty claim. |
| Schwarzer et al. (2020/2021), [SPR, arXiv:2007.05929](https://arxiv.org/abs/2007.05929), ICLR | Multi-step future latent prediction to EMA targets as RL auxiliary objective | Atari 100k, augmented observations | Sample-efficient RL score versus prior pixel RL; abstract inspected | Multi-step EMA prediction is already established; must show opponent-specific incremental benefit |
| Ye et al. (2021), [EfficientZero, arXiv:2111.00210v2](https://arxiv.org/html/2111.00210v2), NeurIPS | MuZero with self-supervised consistency, value-prefix estimation, off-policy correction | Atari 100k; DMControl | Atari aggregate score and component ablations; full consistency section inspected | Closest learned-planning control family: consistency regularization is not new. Compact local surrogate must not be called a faithful EfficientZero reproduction |
| Hafner et al. (2018/2019), [PlaNet, arXiv:1811.04551](https://arxiv.org/abs/1811.04551), ICML | Learn latent dynamics for model-predictive control from images | Visual continuous control | Control return and sample efficiency; abstract inspected | Non-JEPA observation/dynamics objective is needed to isolate representation loss |
| Hansen et al. (2023/2024), [TD-MPC2, arXiv:2310.16828](https://arxiv.org/abs/2310.16828), ICLR | Decoder-free world model and latent trajectory optimization | Continuous-control tasks, multi-task agents | Return/scaling and shared multi-task models; abstract inspected | Shared weights across tasks are stronger than a common trainer. Opponent-minimax remains outside this evidence |
| Koller, Fürnkranz & Bertram (2026), [RePAIR, arXiv:2606.11860v1](https://arxiv.org/html/2606.11860v1), [author repo](https://github.com/Artificial-Chrisi/RePAIR) | Iterative masked latent sequence repair and per-state reconstruction | 80k Lichess training games, 10k validation, 10k test; opening/puzzle analyses | Loss ablations, reconstruction top-1 and representation clusters; full text inspected. The selected final objective omits the JEPA term; decoder-based variants perform better than short-decoder + JEPA in its setting | Direct chess prior art. Bidirectional sequence repair without explicit action inputs differs from causal action-conditioned planning. No local superiority follows; reconstruction scores are not playing strength |
| Ruoss et al. (2024), [Amortized Planning with Large-Scale Transformers: A Case Study on Chess, arXiv:2402.04494](https://arxiv.org/abs/2402.04494) | Supervised action-value prediction amortizes engine search | Large engine-annotated chess corpus | Action quality and searchless playing strength; primary abstract inspected | Teacher compute belongs in data budget; searchless baselines can absorb strong planning priors |
| Cazenave et al. (2020), [Polygames, arXiv:2001.09832](https://arxiv.org/abs/2001.09832), [author platform](https://github.com/facebookarchive/Polygames) | Fully convolutional/pooling Zero learning; board-size independence; opponent checkpoint pool | Multiple board games, self-play | Bot/human competitions and size scaling; abstract/repo inspected | Variable-board adapters and transfer are not sufficient novelty; distinguish architecture compatibility from measured transfer |
| Rabinowitz et al. (2018), [Machine Theory of Mind, arXiv:1802.07740](https://arxiv.org/abs/1802.07740), ICML | Infer agent behavior/characteristics from observed behavior | Populations in gridworlds | Behavioral prediction, ToM tasks; abstract inspected | Opponent identity/history conditioning predicts behavior, not worst-case play. A state-action predictor is not by itself opponent modeling |
| Lanctot et al. (2017), [PSRO, arXiv:1711.00832](https://arxiv.org/abs/1711.00832), NeurIPS | Approximate best responses to policy mixtures with meta-game solving | Coordination games and poker | Joint-policy correlation/generalization; abstract inspected | Opponent mixtures and meta-strategies must not be confused with a single uncalibrated policy expectation |
| Lanctot et al. (2019), [OpenSpiel, arXiv:1908.09453](https://arxiv.org/abs/1908.09453), [official repo](https://github.com/google-deepmind/open_spiel) | Unified games, search and game-theoretic evaluation | Many game classes including ones out of scope | Algorithms, terminology and evaluation tools; abstract/repo inspected | Game metadata must reject unsupported classes. Exact tiny-game best response is preferable to calling a win rate exploitability |
| Agarwal et al. (2021), [Statistical Precipice, arXiv:2108.13264](https://arxiv.org/abs/2108.13264), NeurIPS | Account for uncertainty in few-run RL comparisons | RL benchmark reanalysis | Interval estimates, performance profiles and robust aggregates; abstract inspected | Report seed-level results; a CI over positions alone does not cover retraining uncertainty |
| Bai & Xiong (2026), [Temporal-Distance JEPA, arXiv:2607.25337](https://arxiv.org/abs/2607.25337) | Align predictive representations and planning cost | Offline navigation/manipulation trajectories | Locked-evaluation success and cost/representation ablations; abstract only, preprint | Recent train-plan mismatch work strengthens the need for same-search controls; no adversarial-board-game evidence established here |
| Masip et al. (2026), [FF-JEPA, arXiv:2606.09311](https://arxiv.org/abs/2606.09311) | Action-conditioned dynamics plus latent subgoal planner | PushT preliminary study | Long-horizon task success; abstract only, preprint | Multi-horizon/hierarchical JEPA planning is already being explored; not a distinct contribution by itself |
| [CCranney/JEPA-chess](https://github.com/CCranney/JEPA-chess) | Experimental chess world-model development | Repository, not established benchmark study | README/code presence only; no independently verified strength result | Additional public overlap; do not claim to be the first chess JEPA |

## Positioning decision and falsification

Candidate empirical question, not a novelty claim: does recursive multi-step latent prediction over sequential actions from both roles improve a fixed four-ply max-min backup heuristic against matched task-value, raw-state dynamics and direct-leaf controls? The planner uses exact legal branches internally, while its approximate nonterminal leaf values are supervised on synthetic policy-mixture terminal outcomes; it is not a minimax-value estimator, opponent-specific response model, expected-response policy or equilibrium solver. Exact transitions maintain legality and terminal authority, so this is hybrid planning rather than simulator-free MuZero. V2.9 did not establish a benefit, and opponent-conditioned latent planning already has close prior art in MuZero and VQ planning. The instantiated study uses one shared checkpoint on Connect Four and Reversi, with board-size variants held out; this scope does not establish transfer to other game families.

First isolate the auxiliary objective under the same exact-state search. Then separately compare using predicted latents at two-ply leaves against re-encoding exact states. These answer different questions. If only the former helps, claim representation regularization, not faster latent planning. Match both optimization examples/steps and measured wall time in separate tracks; equal parameter allocations alone are insufficient.

Novelty status: **unverified/high risk**. Evidence required beyond this review: faithful or transparently scoped SPR/EfficientZero-style consistency control; component ablations; game/variant holdout with truly shared weights; several seeds; benefits at predeclared budgets; independent rules validation. If gains vanish against these controls, narrow to a reproducible negative result/benchmark or change the method. Never promote a method from a smoke-test pass.

### Targeted adversarial/J-EPA prior-art update (2026-10-01)

| Work and primary source | Question / design | Domain and data | Baseline / metric / relevant evidence | Difference and consequence for CAISSA |
| --- | --- | --- | --- | --- |
| Schwarting et al. (2021), [Deep Latent Competition, CoRL 2020 / PMLR 155](https://proceedings.mlr.press/v155/schwarting21a.html), [paper PDF](https://proceedings.mlr.press/v155/schwarting21a/schwarting21a.pdf) | Learn a joint latent transition model and opponent-viewpoint prediction; improve policies by imagined self-play | Visual autonomous racing; multi-agent, partially observed, continuous-control setting | Competitive racing benchmark, learned behavior and round-robin win-ratio evaluations; the primary paper describes joint transitions conditioned on ego/opponent actions and opponent-state prediction | This predates CAISSA and defeats any broad claim that joint action-conditioned latent prediction or imagined adversarial self-play is new. It is outside the proposed finite, deterministic, alternating perfect-information game class and is not JEPA. The candidate gap, if any, must be an empirical JEPA objective/planning benefit over matched non-JEPA latent and direct-state controls. |
| Kaplowitz, Obahor & Schroeder de Witt (2026), [MA-JEPA, arXiv:2609.33563v1](https://arxiv.org/abs/2609.33563), [full paper](https://arxiv.org/html/2609.33563) | Train a stochastic JEPA world model with local and joint action-conditioned embedding prediction, then learn policies from latent imagination | Cooperative, partially observed SMAC multi-agent tasks; centralized training / decentralized execution | At matched nominal environment-step budgets, reports mean win rate and seed standard deviation against DMAWM, MAMBA, MAPPO, QMIX and MAT on eight maps; matches or exceeds the strongest reported mean on four of eight, while DMAWM leads on 2s3z, so_many_baneling and 3s_vs_4z | This is a close JEPA/action-conditioned world-model precedent, but it is cooperative MARL with simultaneous joint actions and partial observations, not alternating two-player zero-sum minimax. Its task-dependent results reinforce the need for component ablations, multiple seeds and matched baselines; JEPA alone does not imply superiority. Its joint-action JEPA mechanism is not an acceptable novelty claim. |
| Zhang et al. (2026), [V-JEPA Policy, arXiv:2609.37250v1](https://arxiv.org/abs/2609.37250) | Build a world-action model on frozen V-JEPA 2.1 latents using an instruction-conditioned future-latent predictor coupled to a flow-matching action expert trained downstream | LIBERO, LIBERO-Plus and RoboCasa-GR1; 0.9B total / 0.6B trainable parameters, plus DROID video-instruction pretraining without action labels | The 2026-09-29 preprint reports competitive performance against WAM/VLA baselines and says a same-framework visual-foundation comparison favors predictive JEPA latents, especially under distribution shifts; no board-game or minimax metric | Reinforces that learned future latents can condition action generation and downstream planning; that mechanism is not unique. The robotics setting uses large visual pretraining and continuous actions, not known-rule alternating zero-sum games. A CAISSA claim must isolate the incremental decision benefit of its adversarial-game objective at small matched budgets. |
| Terver et al. (2026), [What Drives Success in Physical Planning with Joint-Embedding Predictive World Models?, arXiv:2512.24497v4](https://arxiv.org/abs/2512.24497), TMLR | Ablate model architecture, training objective and planner within JEPA world-model planning | Simulated and real-robot navigation/manipulation tasks | The v4 paper states its selected model outperforms DINO-WM and V-JEPA 2-AC on navigation and manipulation; its revision notes that tabulated standard deviations capture per-seed variability, not epoch variability | Directly supports treating representation, objective and planner as separate experimental factors. This is not adversarial board-game evidence, and paper-reported results are not a CAISSA comparison. |
| Kubíček & Lisý (2026), [LAMIR, ICLR 2026](https://arxiv.org/abs/2510.05048), [published paper](https://openreview.net/pdf?id=NnBbr4hI8a) | Learn player information-set representations, joint-action latent transitions, reward/termination and legal-action masks; learn a bounded abstraction; perform depth-limited look-ahead solving | Two-player zero-sum imperfect-information games, including Goofspiel and Oshi-Zumo; Leduc uses a chance-node test-time workaround | Full text reports that sufficient capacity recovers near-exact game structure, reduced-capacity abstractions improve exploitability in small games, and LAMIR reaches up to 80% head-to-head win rate over RNaD in large games. Its large study reports 864 GPU hours and 20,736 CPU hours; this resource figure is not directly comparable with CAISSA's local budget | Closest game-theoretic learned-model threat found so far. It is not JEPA and targets learned rule/observation abstraction where explicit rules/state are unavailable or intractable. It nevertheless already combines two-player zero-sum latent dynamics, opponent actions and test-time solving. CAISSA must not claim those ingredients as new. The residual hypothesis is narrower: a JEPA objective can improve strategic decisions or transfer over equally resourced task-prediction models in fully observed deterministic games with known rules. The existing task-value-dynamics arm is a compact, domain-appropriate task-prediction control, not a LAMIR replication; report this scope difference explicitly. |
| Becker & Sunberg (2025), [Simultaneous AlphaZero, arXiv:2512.12486](https://arxiv.org/abs/2512.12486) | Extend AlphaZero search to two-player zero-sum deterministic Markov games with simultaneous moves by solving matrix games in tree search | Pursuit-evasion and satellite custody maintenance | Reports robust strategies against maximally exploitative opponents; primary abstract inspected | Simultaneous action timing differs from this project's alternating-turn core. Classify separately; it reinforces that zero-sum planners and solution concepts vary with move timing. |

The September 29 V-JEPA Policy preprint is a post-v1 search addition; the full text and source record were checked on 2026-10-01. Together with MA-JEPA, DLC, action-sensitive world models and the JEPA-WM ablation study, these sources keep novelty risk critical for generic action-conditioned latent prediction, opponent-state prediction, imagined self-play, or action generation from predicted latents. Their domain mismatch does not remove them as prior art. V2.8's reply-set/minimax ordering hypothesis remains unverified and needs broader forward/backward citation and venue search before any submission claim. No claim of first method is approved.

### Planning-benefit and objective-alignment search (2026-10-01)

This follow-up search targeted primary conference proceedings for tests that
connect latent-model objectives to downstream planning, offline JEPA planning,
and learned game-theoretic models. It remains a targeted search rather than a
systematic review.

| Work and primary source | Question / design | Domain and data | Baseline / metric / relevant evidence | Difference and consequence for CAISSA |
| --- | --- | --- | --- | --- |
| Sobal et al. (2025), [Learning from Reward-Free Offline Data: A Case for Planning with Latent Dynamics Models, NeurIPS 2025](https://proceedings.neurips.cc/paper_files/paper/2025/hash/3e7cf447f21cd11c846463affefce665-Abstract-Conference.html) | Compare offline RL and control/planning using a JEPA latent dynamics model; vary data quality, diversity and environment variability | Offline reward-free navigation tasks and unseen layouts; details/results summarized from official proceedings abstract | Reports model-free RL benefits from high-quality data, while latent planning generalizes better to unseen layouts and is more data efficient; comparable trajectory stitching | Direct evidence that JEPA latent planning can be useful in an offline regime, but not a two-player/adversarial game comparison. CAISSA must use held-out game/rule variants and distinguish objective gain from data-quality and coverage effects. |
| Zhou et al. (2025), [DINO-WM, ICML 2025](https://proceedings.mlr.press/v267/zhou25t.html) | Predict future pretrained visual patch features and optimize action sequences toward target features without observation reconstruction | Six visual environments: mazes, object pushing and multi-particle tasks | Reports zero-shot goal-reaching and comparisons to prior planning methods; official PMLR abstract and metadata inspected | Strong precedent for latent prediction plus test-time action optimization, but uses visual goal reaching, single-agent actions and a pretrained DINOv2 representation. It reinforces that JEPA's contribution must be separated from encoder priors, planner, and target construction. |
| Saanum, Dayan & Schulz (2024), [Simplifying Latent Dynamics with Softly State-Invariant World Models, NeurIPS 2024](https://proceedings.neurips.cc/paper_files/paper/2024/hash/43ba0466af2b1ac76aa85d8fbec714e3-Abstract-Conference.html) | Regularize action effects in latent space using a parsimonious latent-space model, then assess future prediction, planning and model-free RL | Several control-model settings; official proceedings abstract inspected | Reports improved accuracy, generalization and downstream task performance from systematic action treatment | Action-structured latent geometry is a nearby non-JEPA/JEPA-adjacent objective family. Include action-effect/feature-dynamics controls and do not treat better latent loss alone as strategic benefit. |
| Schrittwieser et al. (2019/2020), [MuZero, Nature / arXiv:1911.08265](https://arxiv.org/abs/1911.08265) | Learn recurrent action-conditioned latent dynamics whose reward, policy and value predictions support tree search | Atari 57 plus Go, chess and shogi | Reports superhuman Atari results and board-game strength matching AlphaZero; primary abstract inspected; full-text method passage checked in the earlier targeted review above | This is already learned latent planning across board games with unknown rules. CAISSA's narrower exact-rule setting cannot claim generic latent game dynamics as new; a fair causal test must hold planner and measured inference compute constant and show a decision-quality gain from JEPA over task-prediction and direct-state controls. |

#### Experimental consequence

The relevant causal chain is not “lower future-latent error therefore a better
game player.” Report, separately, target-latent prediction by horizon, latent
rank/collapse diagnostics, legal-action ranking/value calibration, and paired
game outcome under identical search. A latent target loss can improve while
minimax choices do not; that is a negative planning result. When the exact
transition oracle is cheaper than learned imagination, latent prediction must
justify its own training and inference costs. Therefore V03 is strictly an
exploratory runtime/variance gate and cannot validate JEPA or decide method
superiority.

The V2 experiment should treat JEPA objective, model family and planner as
separate factors. At minimum, compare (i) the role-explicit JEPA candidate,
(ii) same-backbone direct policy/value learning, (iii) action-conditioned
task/value-prediction dynamics analogous in scope (but not labelled a MuZero
replication), (iv) a recurrent multi-step consistency objective, (v) a
feature-transition/decoded-state control, and (vi) exact-state search without
learned latent input. Keep data, game adapter, search algorithm, tree budget,
and opponent schedule matched. Report both equal-update and equal-measured
compute tracks; for small games, report exact minimax regret on held-out roots
where a complete oracle map is available, plus paired complete-game score on
the larger test cases. Select on development games/variants only; lock the final
game groups, candidate, seeds, practical margin, correction, censor rules and
analysis before confirmation. If JEPA loses to the strongest appropriately
matched task-prediction control, stop the superiority claim even if it beats a
weak direct-policy baseline.

LAMIR raises the novelty bar but should not be folded into the core scope: its
imperfect-information abstraction solves an information-set explosion absent
from the core games, while simultaneous actions and chance remain separate
classes. This comparison concerns learned strategic models and search; it is
not evidence that LAMIR is a JEPA or a baseline already run here. A LAMIR-
inspired task-model/abstraction arm is a high-value comparison, but its
information-set abstraction and CFR solver do not transfer unchanged to
known-rule perfect-information games. Port it only if state/action abstraction
and measured compute can be matched without giving an arm privileged
information.

### Strategic and value-aware model-learning update (2026-10-02)

The latest primary-source search materially raises the novelty bar for any
proposal to weight latent predictions by planner value or worst-case replies.
The V2.8 first development result is recorded separately in
`docs/validation/V28_DEVELOPMENT_MATCH_ANALYSIS_V01.json`; it does not support a
JEPA-superiority claim.

| Work and primary source | Question / design | Domain and data | Baseline / metric / relevant evidence | Difference and consequence for CAISSA |
| --- | --- | --- | --- | --- |
| Dann, Mansour & Mohri (2026), [Theoretical Foundations and Effective Algorithms for Policy-Aware Simulator Learning, arXiv:2605.29032v3](https://arxiv.org/abs/2605.29032), [full author preprint](https://arxiv.org/html/2605.29032) | How should a learned simulator be trained so an optimizing policy cannot exploit its errors? Formulates model learning as a minimax game against a policy adversary, develops TV/Wasserstein-critic relaxations and critic-guided active data selection | Five high-dimensional continuous-control tasks with generative sampling; biased training state-action distributions and uniform test coverage; additional policy-training tests on DeepMind Control/Gymnasium tasks | Compares with maximum-likelihood dynamics learning, reports RMSE over five seeds and separates average from high-sensitivity regions; reports 1.55–2.20× lower error in sensitive regions. In four policy-transfer tasks, policies trained in the learned simulator approach optimal real-environment returns while MLE-trained simulators fail on three tasks | Directly overlaps the principle of allocating model learning to strategically important regions and is a serious prior-art threat to generic adversarial/value-aware JEPA losses. It is not JEPA and studies stochastic continuous-control simulator exploitation, not alternating finite perfect-information games with exact transitions. CAISSA must test the narrower incremental benefit of EMA target-latent prediction and complete legal reply conditioning against equally decision-aware non-JEPA controls; a softmin-weighted JEPA loss alone is not an adequate novelty claim. |
| Jiang et al. (2026), [Boosting World Models Learning via Latent-Space Value Alignment, ICML 2026 / PMLR 306](https://proceedings.mlr.press/v306/jiang26ai.html) | Can latent-space value-alignment regularization combine dynamics fidelity with task-relevant representation learning, using an adaptive weight | Atari 100k and DeepMind Control benchmarks; published PMLR abstract inspected, full PDF fetch unavailable during this search | The official abstract says it improves existing world-model methods with minimal overhead; exact numerical results and baseline-by-task details were not available from the accessible proceedings page and are not inferred here | A close precedent for latent prediction plus task/value alignment. It is not a board-game JEPA/minimax study. Any CAISSA value-aware latent objective needs an explicit ablation against this objective family and cannot claim value alignment as new. |
| Voelcker et al. (2022), [Value Gradient weighted Model-Based Reinforcement Learning, ICLR](https://openreview.net/forum?id=4-D6CZkRXxI), [author preprint](https://arxiv.org/abs/2204.01464), [official code](https://github.com/pairlab/vagram) | Weight learned transition-model error using value-function gradients to align model fit with decision impact | MuJoCo continuous-control tasks; model-based policy learning | Compares value-gradient-weighted learning with maximum-likelihood dynamics; reports high returns and greater robustness in settings with limited model capacity or distracting state dimensions | A direct non-JEPA precedent for decision-impact-weighted dynamics learning. Minimax-critical JEPA weighting would need this as a control and cannot claim decision-aware weighting itself as new. |
| Farahmand, Barreto & Nikovski (2017), [Value-Aware Loss Function for Model-based Reinforcement Learning, AISTATS / PMLR 54](https://proceedings.mlr.press/v54/farahmand17a.html) | Replace generic transition likelihood fitting with a value-function-structured model loss and provide a finite-sample bound | A simple model-based RL example in the inspected proceedings abstract; broader claims require the paper and are not inferred from that abstract | Compares the proposed value-aware loss with maximum likelihood on a simple problem; the source establishes that decision-structured model losses predate CAISSA | Foundational overlap for objectives designed around value/planning. This is a conceptual prior, not a direct JEPA or two-player game baseline. |

Search limitations: the Dann et al. v3 preprint full text was inspected; the ICML 2026
Value-Aligned World Model was available here through its official abstract, not its
PDF. A backward/forward-citation and venue search is still required before a
submission novelty statement. No proposed loss or weighting scheme is designated
novel by this search.

### Planning-alignment and transfer update (2026-10-02)

The follow-up search targeted JEPA objectives that align latent prediction with
planning, value, reachability, and transfer. It used the official PMLR page,
arXiv author preprints, and the original Zenodo record. It did not establish an
exhaustive search or a novelty result.

| Work and primary source | Question / method | Domain, data, baseline and reported result | Consequence for CAISSA |
| --- | --- | --- | --- |
| Destrade et al. (2026), [Value-Guided Action Planning with JEPA World Models, arXiv:2601.00844](https://arxiv.org/abs/2601.00844) | Shape a JEPA latent space so embedding distance approximates a negative goal-conditioned value, then use that cost to guide action search | Simple goal-conditioned control tasks; the abstract reports improved planning over standard JEPA, but this search did not extract a complete task-by-task table | Value-shaped JEPA planning is already prior art. A minimax/value-aligned CAISSA objective would need stronger game-specific distinction and an explicit matched value-alignment baseline; it is not novel merely because values are zero-sum. |
| Li et al. (2026), [Predictive but Not Plannable: RC-aux for Latent World Models, arXiv:2605.07278](https://arxiv.org/abs/2605.07278) | Add multi-horizon open-loop prediction, budget-conditioned reachability supervision, and temporal hard negatives to a LeWorldModel backbone | Offline goal-conditioned pixel control and a LIBERO-Goal extension; compares with LeWM-style and control baselines; abstract reports improvements in locked evaluation. Detailed figures were not re-extracted in this update | Multi-horizon rollouts and planning-budget-aware latent supervision are directly overlapping mechanisms. They belong in related work and, if relevant to a later CAISSA design, as a baseline family rather than an originality claim. |
| Bai & Xiong (2026), [Temporal-Distance JEPA, arXiv:2607.25337](https://arxiv.org/abs/2607.25337), [author code](https://github.com/HKBU-KnowComp/Temporal-Distance-JEPA) | Mine directed temporal progress from trajectory order and cross-trajectory pairs, plus rollout consistency; use the cost directly or to shape JEPA representations | Offline navigation/manipulation. The author preprint reports locked evaluation, ablations, and gains against LeWM and concurrent RC-aux on its environments | Plan-aware JEPA objectives and horizon-matched rollout supervision are not new. The setting is goal progress, not adversarial utility or max-min search; any remaining gap is empirical and must be tested against these objective families. |
| Huang (2026), [VJEPA: Variational Joint Embedding Predictive Architectures as Probabilistic World Models, ICML 2026 / PMLR 306](https://proceedings.mlr.press/v306/huang26ba.html) | Replace deterministic future-latent prediction with a variational predictive distribution; connect it to predictive-state representations and modular priors | Published paper abstract frames uncertainty-aware planning/control; this search inspected the official proceedings abstract, not all experiments | Even in deterministic board games, learned forecasts can be epistemically uncertain under held-out variants. A stochastic latent head is a candidate tool, not a novelty claim; calibration and robust planning would need a separate frozen question. |
| Rodrigo-Ginés (2026), [Agentic-JEPA, Zenodo record 20237490](https://zenodo.org/records/20237490) | Train an EMA JEPA model from self-supervised state/action trajectories and plan by matching predicted states to goal embeddings | Text-based agent environments. The author record reports 100% success in-distribution but 0% on every tested OOD environment; k-step lookahead degrades from 100% to 40% at k=3 | This is a preprint/repository record, not evidence in board games. Its reported transfer and rollout failures reinforce that held-out game/variant transfer and open-loop error must be measured directly, not inferred from within-game play. |

Design update: after V2.9, do not treat a positive duration result as the
contribution. A next candidate must identify a precise two-player mechanism
that can improve fixed-budget max-min action selection, freeze that mechanism
before any new model-selection outcomes, and compare against both the current
task-value arm and the closest plan-aware JEPA/value-alignment family. If no
credible distinction survives, narrow the paper to a rigorous benchmark and
negative result rather than inflate the claim.

### Development outcome, board-game transfer, and gradient-routing update (2026-10-02)

The completed V2.9 outcome is preserved in
`docs/validation/V29_DEVELOPMENT_MATCH_ANALYSIS_V01.json`. Its recipe failed the
frozen nomination screen; this section does not reinterpret it as a JEPA win.
The follow-up search used the author arXiv records/full author sources and the
original NeurIPS paper page. This remains a targeted search, not a systematic
novelty certification.

| Work and primary source | Question / design | Domain / evidence inspected | Consequence for CAISSA |
| --- | --- | --- | --- |
| Soemers et al. (2021), [Transfer of Fully Convolutional Policy-Value Networks Between Games and Game Variants, arXiv:2102.12375](https://arxiv.org/abs/2102.12375), [author PDF](https://matthewstephenson.info/papers/Transfer%20of%20Fully%20Convolutional%20Policy-Value%20Networks%20Between%20Games%20and%20Game%20Variants.pdf) | Transfer AlphaZero-like fully convolutional policy/value parameters across games and variants using shared semantics in Ludii state/action channels; evaluates zero-shot transfer and fine-tuning | Nine board games with multiple variants, including board size/shape and rule changes; source abstract and author paper inspected | Shared-game or variant transfer is established prior art, including search-guided policy/value. CAISSA cannot claim transfer itself; a useful remaining test must isolate the incremental effect of opponent-conditioned JEPA over matched transferable non-JEPA controls. |
| Ben-Assayag & El-Yaniv (2021), [Train on Small, Play the Large: Scaling Up Board Games with AlphaZero and GNN, arXiv:2107.08387](https://arxiv.org/abs/2107.08387) | ScalableAlphaZero uses a graph network and subgraph sampling to train on small boards and play larger board instances | Othello, Gomoku, and Go at varying board sizes; author preprint reports small-board training transferred to larger-board tests and compares with larger-board AlphaZero trained substantially longer | Board-size scaling and small-to-large play are not novel. Any future CAISSA variant-size protocol needs this architecture/search family as a strong reference where a fair implementation is feasible. |
| Yu et al. (2020), [Gradient Surgery for Multi-Task Learning, NeurIPS](https://papers.neurips.cc/paper_files/paper/2020/hash/3fe78a8acf5fda99de95303940a2420c-Abstract.html), [author preprint](https://arxiv.org/abs/2001.06782) | PCGrad projects a task gradient away from a conflicting gradient on shared parameters | Supervised multi-task and multi-task RL experiments; primary abstract/paper inspected | Conflict projection is a known optimization tool. A future projected JEPA loss cannot claim gradient surgery as new; it needs a narrow controlled result and the raw objective plus strong controls. |
| Liu et al. (2021), [Conflict-Averse Gradient Descent for Multi-task Learning, NeurIPS](https://papers.neurips.cc/paper_files/paper/2021/hash/9d27fdf2477ffbff837d73ef7ae23db9-Abstract.html) | CAGrad minimizes average task loss while regularizing against worst local task improvement | Multi-task supervised and reinforcement learning; NeurIPS primary abstract inspected | Additional evidence that gradient conflict mitigation is mature prior art; CAISSA must not relabel a standard optimizer rule as a unique JEPA method. |
| Xu et al. (2026), [JEPA Policy: Diffusion-Free Imitation Learning via Paired Action and Future Representation Prediction, arXiv:2609.09630](https://arxiv.org/abs/2609.09630), [author project](https://jiejie567.github.io/JEPA-Policy/) | Shared-transformer paired action/future-representation prediction, with dual-branch and gradient-routing controls | Nine simulated tasks and a five-task, 630-episode robot evaluation are reported in the author abstract/project; source abstract inspected | JEPA gradient routing and future-prediction influence on action representations are already explicit in a recent preprint. Our candidate question is narrower: conflict between all-legal opponent-reply latent supervision and decision-task gradients in finite zero-sum games. No novelty follows from that distinction without a deeper citation search and reproducible matched result. |

Research decision: an independent reviewer found the match schedule/order,
seat swaps, paired cells and saved analysis internally consistent and no P1/P2
issues. Their plausible, non-causal diagnosis is that reply-set latent loss may
conflict with policy/value learning in shared encoder parameters. The next
authorized research step is therefore a no-update train-only gradient alignment
diagnostic with a frozen gate, not another longer fit or an immediate loss
intervention. See `docs/METHOD_V210_GRADIENT_DIAGNOSTIC.md` and `ROADMAP.md`.
The diagnostic gate is a project-specific screening rule, not a conventional
significance standard. If it fails, this candidate stops; there will be no
post-hoc subgroup search.

## V2.12 decision research update (2026-10-02)

The V2.11 result is now independently audited and does not nominate λ=8. A new
search added several sources that materially raise the novelty bar:

| Work | Research question and method | Domain/data/baselines/metrics available from primary source | Relevance to CAISSA-JEPA |
| --- | --- | --- | --- |
| [When Does LeJEPA Learn a World Model? (Klindt, LeCun & Balestriero, 2026)](https://arxiv.org/abs/2605.26379) | Under what assumptions does LeJEPA recover latent world variables up to rotation; proves identifiability under stationary additive-noise transitions and evaluates synthetic and robotic planning settings | Theoretical analysis plus experiments up to 1024-D and pixel-based robot control; the abstract/source was inspected | Gives principled representation hypotheses, but its assumptions/setting do not establish identifiability or planning gains in finite deterministic adversarial games. A Gaussian regularizer alone is not a contribution here. |
| [What Drives Success in Physical Planning with Joint-Embedding Predictive World Models? (Terver et al., ICLR 2026)](https://arxiv.org/abs/2512.24497), [official code](https://github.com/facebookresearch/jepa-wms) | Ablates JEPA-WM architecture, objective, horizon/context, inputs, and planner for planning in learned representation space | Simulated navigation/manipulation and robotic data; DINO-WM and V-JEPA-2-AC baselines; planning success and action metrics; primary abstract and code page inspected | Multi-step latent prediction and planner/model co-design are already directly studied. An adversarial-game adaptation alone may be an application paper but is not automatically algorithmically novel. |
| [JEPA Policy (Xu et al., 2026)](https://arxiv.org/abs/2609.09630), [author project](https://jiejie567.github.io/JEPA-Policy/) | Couple action prediction with future-representation prediction and test whether shared topology improves control | Nine simulated tasks and five-task, 630-episode robot study; MIP and Diffusion Policy comparisons; primary abstract inspected | Shared action/future representations and gradient routing are claimed there. Avoid presenting those ingredients as new. |
| [Boosting World Models Learning via Latent-Space Value Alignment (Jiang et al., ICML 2026)](https://proceedings.mlr.press/v306/jiang26ai.html) | Add latent value-alignment regularization to model learning while preserving dynamics structure | Atari 100k and DeepMind Control; existing world-model baselines; return/control outcomes; PMLR primary page inspected | Decision/value-aware latent prediction is established, so a planner-weighted JEPA loss needs direct differentiation and game-theoretic analysis to clear novelty review. |
| [Theoretical Foundations and Effective Algorithms for Policy-Aware Simulator Learning (Dann, Mansour & Mohri, 2026)](https://arxiv.org/abs/2605.29032) | Formulate strategic simulator robustness as a zero-sum minimax game against an adversarial policy, derive a critic-based bound and error-driven active data collection | Continuous-control tasks; ordinary prediction baselines; prediction error in strategically important regions and downstream performance; primary arXiv abstract inspected | This is the closest strategic model-learning prior found so far. The CAISSA question must be distinguished from policy-exploitation robustness in continuous control, not simply renamed as minimax-aware model fitting. |
| [Mastering Atari, Go, Chess and Shogi by Planning with a Learned Model (Schrittwieser et al., 2020)](https://arxiv.org/abs/1911.08265), [MiniZero comparative framework](https://arxiv.org/abs/2310.11305) | Learn planning representations and use search to master diverse games; MiniZero compares AlphaZero/MuZero-family variants | Go, chess, shogi, 57 Atari games; game/search baselines; strength, return and compute-related outcomes; primary arXiv abstracts inspected | Multi-game board-game planning and learned dynamics are not new. CAISSA needs a JEPA-specific advantage with matched search and at least one held-out game/variant, or a compelling negative-result benchmark contribution. |
| [One-Step Next-Latent Prediction Is Not a World Model (Wang, Cai & Hong, 2026)](https://arxiv.org/abs/2609.36227) | Shows one-step latent regression identifies a conditional mean, not generally a roll-outable transition kernel; studies multi-step error and short-context prediction | Linear-Gaussian and nonlinear synthetic dynamics, hidden rotation; one-step versus multi-step prediction error; primary arXiv abstract inspected | Direct warning for our current predictor: a low two-ply latent MSE alone is not evidence of a usable recursive world model. Any V2.12 must measure open-loop rollout error, minimax action/rank stability and strength as a function of planning horizon. |
| [Regret-Guided Search Control for Efficient Learning in AlphaZero (Tsai et al., ICLR 2026)](https://proceedings.iclr.cc/paper_files/paper/2026/hash/9e720fce64f91114c49cfd640d821da3-Abstract-Conference.html), [author code](https://github.com/rlglab/rgsc) | Learn regret values/rankings to prioritize high-regret states from self-play/search trees and restart AlphaZero training there | Go 9x9, Othello 10x10, Hex 11x11; ICLR primary abstract reports mean +77 Elo over AlphaZero and +89 over Go-Exploit, plus KataGo win-rate improvement in a trained-model setting | Board-game regret ranking and regret-guided state selection are now direct prior art. A future strategic/decision-aware JEPA cannot claim regret ranking or prioritizing hard states as new; compare against an appropriate RGSC-style control if that becomes the method. |
| [A Sharp Analysis of Model-based RL with Self-Play (Liu et al., 2021)](https://proceedings.mlr.press/v139/liu21z.html), [Incentivize without Bonus: Provably Efficient Model-based Online Multi-agent RL for Markov Games (Yang et al., ICML 2025)](https://proceedings.mlr.press/v267/yang25j.html) | Study model-based learning and equilibrium exploration in zero-sum or multi-agent Markov games | Theoretical finite-horizon Markov games and model-based online RL; regret/sample complexity and equilibrium-related objectives; PMLR primary sources inspected | Strong game-theoretic controls and solution concepts exist. We must define behavioral opponent prediction separately from worst-case minimax planning and compare against appropriate game-theoretic methods when making equilibrium claims. |

### V2.12 candidate, explicitly unverified

V2.11 suggests that raising the weight of the existing pair-conditioned target
did not improve play. A 2026 analysis also cautions that one-step latent
prediction need not define a roll-outable world model. V2.12 now specifies a
multi-step predictor trained along recorded alternating-player action
sequences and a four-ply max/min backup heuristic with mixture-outcome leaf
values. Its falsifiable question is whether that complete candidate improves
paired game score over five matched controls, with a shared checkpoint across
Connect Four and Reversi and held-out board sizes. It predicts neither a named
opponent nor a worst-case value function, and it is not an equilibrium method.
The exact candidate and controls are in `METHOD_SPEC_V212.md`; the spec remains
under independent review and the fixed 2.0-second Reversi8 rule-only cap
failed. After v04 is independently accepted, only the narrowly scoped
random-initialized, no-training inference/instrumentation pilot described in
the spec may proceed; training and matches remain blocked. Multi-step JEPA world
learning already exist, so neither novelty nor superiority is established.
Kill this direction if the JEPA arm cannot clear the predeclared all-control
gates, its advantage disappears under matched compute, or a closer prior-art
comparison removes the claimed increment.

Search limitations: searches used the exact title/topic terms recorded in this
update and prioritized arXiv, PMLR, OpenReview, and author-maintained code. They
are not a systematic database search and do not establish that no other
opponent-conditioned JEPA or strategic world-model method exists. Novelty
remains unverified.

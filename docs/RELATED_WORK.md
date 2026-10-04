# Research positioning and search record

Initial search: 2026-10-01; targeted primary-source refreshes through 2026-10-04. Status: scoped review for design v1, **not an exhaustive systematic literature review or a verified novelty claim**. Sources below are original papers, author repositories or official dataset hosts. Abstract-only entries are explicitly distinguished from full-text inspection. No published score is a local result.

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
| Koller, Fürnkranz & Bertram (2026), [RePAIR, arXiv:2606.11860v1](https://arxiv.org/html/2606.11860v1), [author repo](https://github.com/Artificial-Chrisi/RePAIR) | Iterative masked latent sequence repair and per-state reconstruction of chess boards; no explicit move input | 80k Lichess training games, 10k validation, 10k test; opening/puzzle analyses | Three-run 80%-mask loss ablation: 93.71% ± 0.05% square top-1 for short+long decoder losses, versus 93.90% ± 0.02% for long-decoder-only and 93.18% ± 0.02% for long-decoder+JEPA; always-empty baseline is 50%. Later experiments omit JEPA; full text inspected | Direct chess prior art for latent sequence repair, not action-conditioned planning or game strength. The reported metric is sparse square reconstruction, not move quality or decision regret. The visible repository file listing has no top-level license; code/data reuse rights remain unverified. |
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

### JEPA control-state, value-guidance, and world-action refresh (2026-10-03)

A follow-up primary-source search tested for closer overlaps on control-state
geometry, action sensitivity, and joint world/action prediction, and revisited
the already-listed value-guided JEPA paper in full text. Full methods were
inspected for the four additional preprints below. This remains a targeted
search rather than a systematic review.

The full-text revisit of Destrade et al. confirms its goal-conditioned reaching
value shapes the JEPA embedding geometry used as an MPC cost; it is already
listed in the 2026-10-02 matrix above. V2.12 instead uses policy-mixture
terminal-outcome labels with a side-to-move value head inside exact-rule
alternating max/min. These are different target and decision semantics, not
evidence that value-aware JEPA is new.

| Work and primary source | Method and evidence inspected | Relevance and distinction for CAISSA |
| --- | --- | --- |
| Zoabi, Ali & Wolf (2026), [Hamiltonian JEPA: Action-Conditioned World Models with an Inherited Control State, arXiv:2609.33497v1](https://arxiv.org/abs/2609.33497) | Separates perceptual and planner-facing state, uses an inherited-covariance control slice and phase-conditioned dissipative port-Hamiltonian dynamics; port-inverse consistency reweights rollout error toward action directions. Full method and abstract inspected. | Raises the bar for claims that generic latent geometry or prediction quality is enough for planning. V2.12 uses an ordinary small affine action-conditioned predictor and has no port-Hamiltonian state or action-direction reweighting; its novelty cannot be latent control-state design. The paper evaluates pixel-based continuous control, not exact symbolic adversarial games. |
| Zhang et al. (2026), [Delta-JEPA: Learning Action-Sensitive World Models via Latent Difference Decoding, arXiv:2606.31232v1](https://arxiv.org/abs/2606.31232) | Adds a latent-difference action decoder that reconstructs the executed action from adjacent-embedding displacement, alongside latent forward prediction; reports planning and action-sensitivity studies on continuous-control tasks. Full method/abstract inspected. | Action sensitivity and action-conditioned latent planning are explicit prior art. V2.12 conditions its forward predictor on the supplied legal action but does not decode that action from latent displacement. An action-sensitivity objective would be a new method variant requiring a new version and matched controls, not an implicit property of the current JEPA loss. |
| Wang et al. (2026), [WA-JEPA: Rethinking the Video JEPA Paradigm for World-Action Modeling in Autonomous Driving, arXiv:2608.20974v2](https://arxiv.org/abs/2608.20974) | Uses hybrid future masking, conditional flow matching over future latents, and a joint future-scene/action predictor; reports NAVSIM and HUGSIM results. Full method and abstract inspected. | Joint world/action prediction is another established planning-oriented JEPA direction. V2.12 predicts future states conditioned on recorded actions and has a root policy head, but does not jointly generate future actions with future-world tokens; it instead searches exact legal branches. WA-JEPA is driving and does not evaluate adversarial max/min. |
| Gan et al. (2026), [ActSWM: Action-Sensitive World Models for Long-Horizon Planning in Open-World Games, arXiv:2607.26712v2](https://arxiv.org/abs/2607.26712) | Combines a frozen action readout trained from latent transitions with rollout-level separation between recorded-action and all-zero-action predictions to address action-insensitive autoregressive rollouts; evaluates step drift, closed-loop Minecraft tasks, and CEM action recovery. Full method/abstract inspected; detailed source summary is in `docs/V28_PRIOR_ART_DELTA_20260930.md`. | Closest game-domain JEPA planning precedent in this search. Minecraft is a single-agent open-world control task; ActSWM does not study alternating players, zero-sum utility, exact discrete board rules, or max/min. It nevertheless establishes that multi-step JEPA in a game environment and action-sensitive rollout objectives are prior art. A V2.12 diagnostic should compare legal alternatives from the same root only when their exact-rule consequences differ, and report latent separation alongside exact-state, value, and ranking differences. Distinct legal actions need not map to distinct latents, and latent distance alone does not establish useful sensitivity. |

These sources narrow the plausible contribution further: V2.12 should be framed
as a controlled test of whether its particular EMA-target multi-horizon loss
adds value over matched value-/state-prediction controls in an exact-rule,
two-player finite-horizon setting. ActSWM also motivates a diagnostic comparing
same-root legal alternatives whose exact-rule consequences differ, with latent
separation reported alongside exact-state, value, and ranking differences.
Distinct legal actions need not map to distinct latents, and latent distance
alone does not establish useful sensitivity. Any spec change must be versioned
and reviewed. These papers do not establish that increment, and they do not
alter any data, compute, or training gate.

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
The exact candidate and controls are in `METHOD_SPEC_V212.md`; the spec was
independently accepted only for the narrowly scoped random-initialized,
no-training inference/instrumentation pilot. The fixed 2.0-second Reversi8
rule-only cap failed. Training and matches remain blocked. Multi-step JEPA world
learning already exist, so neither novelty nor superiority is established.
Kill this direction if the JEPA arm cannot clear the predeclared all-control
gates, its advantage disappears under matched compute, or a closer prior-art
comparison removes the claimed increment.

Search limitations: searches used the exact title/topic terms recorded in this
update and prioritized arXiv, PMLR, OpenReview, and author-maintained code. They
are not a systematic database search and do not establish that no other
opponent-conditioned JEPA or strategic world-model method exists. Novelty
remains unverified.

### Planning-range and reciprocal-response refresh (2026-10-03)

A targeted arXiv search after the v02 compute review found two September 2026
preprints that sharpen the scope and evaluation requirements. This is a
primary-source update, not a complete forward-citation or venue search.

| Work and primary source | Method and evidence inspected | Consequence for CAISSA |
| --- | --- | --- |
| Chahe & Zhou (2026), [PiJEPA: Policy-Guided World Model Planning for Language-Conditioned Visual Navigation, arXiv:2603.25981v1](https://arxiv.org/abs/2603.25981) | Uses an Octo action prior to initialize MPPI over a separate JEPA world model. The paper's method section specifies a frozen visual encoder, action-conditioned predictor, autoregressive multi-step latent MSE, and image-goal latent-distance planning; abstract reports navigation experiments. Full method sections 3.1–3.4 inspected. | Directly overlaps JEPA latent rollout plus action-sequence planning, so those ingredients are not novel. It differs from V2.12's jointly trained EMA-target small-board model and exact legal discrete alpha-beta max/min; PiJEPA is single-agent continuous robot navigation with policy-guided MPPI and goal-distance scoring. This is adjacent prior art, not a zero-sum game result or a matched control. |
| Alrasheed et al. (2026), [The Planning Limits of Latent World Models, arXiv:2609.39235](https://arxiv.org/abs/2609.39235), [full text](https://arxiv.org/html/2609.39235) | Tests action ranking and control across five frozen backbones, including V-JEPA 2/2.1, on Meta-World and BridgeData V2. With five-step imagined rollouts, reliable ranking is limited to targets about five to ten steps away; the authors also find a substantial horizon gap with a perfect simulator. | This is not adversarial board-game evidence, but it shows why prediction error alone cannot validate a short-horizon planner. V2.12 must report action-ranking/regret by imagined horizon, compare the learned rollout with exact transitions under identical search and leaf evaluation, and avoid attributing truncation error to JEPA. The current four-ply random-weight compute pilot says nothing about this question. |
| Ma et al. (2026), [ReWAM: Reciprocal World Action Models for Interactive Autonomous Driving, arXiv:2609.39245](https://arxiv.org/abs/2609.39245), [full text](https://arxiv.org/html/2609.39245) | Couples future-world representations with role-specific action generators in a finite Level-k response hierarchy; learns conditional responses from demonstrations and evaluates on NAVSIM. | Reciprocal latent-grounded response modeling is now an additional adjacent prior-art threat. ReWAM learns amortized conditional surrogates for bounded best-response behavior in driving, not a deterministic finite zero-sum game's exact legal branches or worst-case max-min values. CAISSA must keep behavioral response modeling distinct from minimax search and cannot claim reciprocal action conditioning alone as novel. |

Design implication: retain the current falsifiable question only as a possible
game-specific empirical increment over matched controls. Required tests already
listed in `docs/V212_RESEARCH_GATE.md` should be interpreted at each declared
rollout horizon, including exact-transition/oracle comparisons. The v02
compute envelope is random-weight instrumentation; neither it nor the reviewed
5-second proposal establishes a trained model's plannable range or operating
budget. No training or match gate changes as a result of this search.

### Recursive JEPA and rollout-diagnostic refresh (2026-10-03)

This targeted primary-source pass searched for recursive action-conditioned
JEPA objectives, rollout diagnostics, and direct symbolic/game precedents. It
does not constitute a systematic review or establish novelty.

| Work and primary source | Method and evidence inspected | Consequence for CAISSA |
| --- | --- | --- |
| Liu et al. (2026), [Semigroup-JEPA, arXiv:2609.10464](https://arxiv.org/abs/2609.10464), [author project and results](https://sg-jepa.github.io/) | Extends LeWorldModel with a gravity-conditioned predictor and trains encoder plus predictor through a discounted recursive multi-step latent rollout with SIGReg. The authors report longer-horizon prediction gains on synthetic 2D physics and improved control on 3D robotics. | Recursive multi-step latent prediction and training through rollout loss are established JEPA mechanisms. The preprint's explanation of where the gain comes from is internally mixed: its abstract/linear-feature account emphasizes encoder features that remain predictable under recursion, while an encoder/predictor reset ablation attributes the effect primarily to the predictor. Treat the mechanism attribution as unresolved. The method uses physical dynamics and a supplied gravity parameter rather than alternating legal board-game actions and worst-case max/min search; any contribution here must be a measured game-theoretic increment over matched multi-step JEPA and task-value controls. Recursion itself is not novel. |
| An et al. (2026), [Action-Conditioned Predictive Consistency, arXiv:2608.12939](https://arxiv.org/abs/2608.12939), [full text](https://arxiv.org/html/2608.12939v1) | Defines a frozen-model diagnostic comparing clean and visually perturbed inputs after rolling both forward under the same action sequence. Its prediction-error bound is samplewise; the planning-cost bound assumes squared distance to a fixed goal embedding and applies to the evaluated candidate pool. Experiments use CEM in visual-control tasks. | This is an adjacent evaluation method, not a new training objective or board-game result. It reinforces that action-conditioned rollout diagnostics should be tied to downstream cost/ranking and that low latent error alone is insufficient. Its fixed-goal bound is an analogy, not a guarantee for minimax value or action ranking in V2.12. Visual perturbation robustness does not transfer directly to exact symbolic board states; V2.12's relevant tests remain horizon-wise latent error, minimax ranking/regret, exact-transition comparison, and game outcomes. |

Search quality note: Semigroup-JEPA and ACPC were inspected through the
authors' arXiv papers/project page. The JEPA-Chess entry is retained solely to
record and quarantine a discovery artifact that could otherwise be mistaken
for verified prior art. None of these sources changes the V2.12 gate or
supports a superiority claim.

PiJEPA is an additional adjacent precedent: its primary arXiv full text confirms
that multi-step action-conditioned JEPA rollouts can be coupled to a planner,
while its action prior, continuous robot domain, and goal-distance MPPI objective
differ from the exact-rule, two-player max/min study here. This further narrows
the possible claim to an empirical incremental effect of latent matching under
the V2.12 controls; it does not establish novelty or clear the gate.

Unverified search lead (excluded from the matrix): Exa surfaced a purported
Zenodo item titled [JEPA-Chess: Action-Conditioned Joint Embedding Predictive
Architectures for Discrete Logical State Tracking](https://exa.ai/library/publication/5zmflyz8r3g).
Exact-title and source-targeted searches did not locate a canonical Zenodo
record, DOI, author manuscript, or repository, so its reported method/results
are not treated as evidence. The independently reachable
[CCranney/JEPA-chess repository](https://github.com/CCranney/JEPA-chess)
remains an experimental repository with no independently verified playing-
strength result, as noted above. Recheck the unverified lead against a primary
record before any submission novelty statement.

### Adversarial board-game latent-model planning check (2026-10-03)

A targeted Exa discovery pass used 13 queries across three overlapping
territories—JEPA in games, learned world models for adversarial board games,
and latent planning/transfer in chess and related games—with 92 requested
results before deduplication. Results were treated as leads, not evidence.
This is not a systematic database or citation search.

| Work and first-party evidence | Method and reported evidence | Relevance and limits for CAISSA |
| --- | --- | --- |
| Titonis, Droumalia & Mouliaras (2026), [World Models for Adversarial Games: Encoder–Dynamics–Value Planning Applied to ConnectX, Zenodo record](https://doi.org/10.5281/zenodo.21904378), [author repository](https://github.com/alextitonis/WorldModel-ConnectX) | The public author repo contains a whitepaper, implementation and MIT license. `train_utils.py` trains an encoder/dynamics/decoder with one-step latent, reconstruction and reward losses plus a three-step unrolled latent/reconstruction loss; the encoder itself supplies targets (no EMA target is specified). `env.py` bundles a fixed opponent's reply into each `step`, so a training action transition is not an alternating pair of separately conditioned plies. The deployed `adversarial_search.py` enumerates actual legal board moves/replies and uses the learned value head at leaves; `search.py` is the latent-beam comparison. The README reports a ConnectX 7×6 ladder result of 630 rating / rank 66 of 190 on 2026-09-02 and an internal opponent-harness table (the current deployed configuration with exact endgame solving reports 83.3% against its stronger heuristic); these are author-reported, not independently reproduced. | This is the closest directly verified adversarial board-game latent-model-plus-search precedent found in this pass, and it removes room to present that system-level setting as new. It is not a JEPA result: the model has no EMA-target objective, its trained transition incorporates one fixed-opponent response, and the deployed max/min uses exact rules with a learned leaf value rather than latent imagined branches. It studies one Connect Four board size, not cross-size or cross-game transfer. The paper/repo is a preprint/author project, not peer-reviewed evidence; the README's brief description says planning over the learned prediction, while its detailed method, code and results distinguish that latent-beam baseline from deployed exact adversarial search. Treat the code path and this wording discrepancy explicitly. |
| Hamara et al. (2025), [Learning to Plan via Supervised Contrastive Learning and Strategic Interpolation: A Chess Case Study](https://arxiv.org/abs/2506.04892), [official KDD-UMC paper PDF](https://kdd.org/kdd2025/wp-content/uploads/2025/07/CameraReady-17.pdf), [author code](https://github.com/andrewhamara/SOLIS) | Trains a transformer state encoder with supervised contrastive labels from Stockfish win-probability estimates over ChessBench positions; chooses moves using an evaluation-aligned latent direction and a six-ply beam. The paper reports an estimated Elo of 2593, but this is not a controlled JEPA/minimax comparison. | Board-game latent planning and shallow search are also prior art, but this method does not learn action-conditioned transition latents or model alternating opponent replies. It further narrows representation/planning claims while remaining adjacent to V2.12's exact-rule search and EMA-target loss. The camera-ready text exposes a placeholder DOI and the reported Elo is not independently verified here. |

These sources sharpen rather than resolve novelty. ConnectX overlaps the game
setting and the combination of a learned latent model with adversarial board
search, but not V2.12's specific EMA-target, alternating-action JEPA objective;
SOLIS overlaps board-state representation and latent-guided chess planning,
but not predictive dynamics. The only defensible V2.12 question remains a
controlled empirical increment over matched state/value baselines and a
same-search exact-state control. No V2.12 fit, match, score, or gate change
follows from this search.


### Causal-JEPA and structured counterfactual-like queries (2026-10-03)

Nam et al., [Causal-JEPA: Learning World Models through Object-Level Latent
Masking](https://proceedings.mlr.press/v306/nam26c.html), ICML 2026, extends
masked joint-embedding prediction to object-level latents. Its abstract says
masked object states are inferred from surrounding context, creating
“counterfactual-like” prediction queries; it reports counterfactual-reasoning
and agent-control results. This is relevant to V2.12's unresolved question of
how to represent counterfactual support, but it is not evidence that C-JEPA
evaluates all legal action branches or learns exact rule-governed transitions
in adversarial board games. It strengthens the need to distinguish structured
masked queries from complete legal-action coverage. This source does not resolve
the V2.12 protocol gap, establish novelty, or change any research gate.


### Action-discriminative multi-step JEPA and counterfactual planning (2026-10-03)

Two 2026 arXiv preprints directly narrow the action-aware-planning claim.
Qiu et al., [AD-WM: Action-Discriminative World Models for Counterfactual
Model Predictive Control](https://arxiv.org/abs/2609.30264) (v2, 2026-09),
train residual latent transitions on observed successors and add predictor-level
action-recovery objectives. At inference, the latent model is rolled out for
CEM candidate selection. Their planning-facing diagnostics compare predicted
and realized costs on a shared candidate bank, including global rank
correlation and normalized regret of the predicted elite set. The paper
reports improved results over its matched LeWM baseline on four of five
simulation environments and on a robot-transfer task; these are author-reported
preprint results and were not independently reproduced in this audit. This
makes action-discriminative JEPA dynamics, counterfactual candidate comparison,
and planner-facing regret diagnostics established prior art. Its continuous
robotic goal-reaching/CEM setting does not test exact finite legal action sets,
alternating adversarial players, or worst-case zero-sum max-min decisions.

Gan et al., [ActSWM: Action-Sensitive World Models for Long-Horizon Planning in
Open-World Games](https://arxiv.org/abs/2607.26712) (v2, 2026-08), are still
closer to the proposed multi-step objective. ActSWM combines JEPA-style
multi-step latent rollout prediction with (a) a contrast between recorded and
all-zero future action rollouts and (b) a frozen action readout that encourages
recoverable actions from predicted latent transitions. It evaluates closed-
loop CEM planning in Minecraft tasks and action recovery from offline
Counter-Strike 2, GTA V, and Apex Legends gameplay. These author-reported
preprint experiments establish multi-step action-sensitive JEPA planning and
cross-game action recovery as prior art, but do not evaluate exact legal
transitions in alternating, deterministic, two-player zero-sum games or
minimax decision regret. Its all-zero contrast must not be copied literally
into CAISSA: a zero action may be illegal or semantically special in a board
game.

Together these papers mean novelty cannot rest on multi-step JEPA, action
sensitivity/action recovery, counterfactual planning comparisons, or
cross-game action recoverability. The only plausible incremental empirical
question currently left is narrower: whether a frozen learned latent model
improves exact-rule, finite-horizon max-min decision quality in the declared
game scope at equal measured compute, beyond matched value/dynamics controls
and an action-sensitive JEPA control. That is a benchmark claim to test, not
an algorithmic novelty claim. The V2.12 v04 objective trains on recorded
trajectory branches and has no counterfactual-branch loss, so support coverage
alone cannot establish arbitrary legal-action ranking. Before any fit, a
versioned, independently reviewed protocol must resolve whether to add an
action-sensitive arm and must define full legal-root scoring and decision
regret against a bounded exact-search reference. No current method/spec gate
changes from this literature review.

### Action-sensitivity control scope review (2026-10-04)

The primary-source method comparison is now separated from the control
decision. ActSWM's frozen action readout constrains predicted latent
transitions to retain recoverable action information; its rollout contrast
uses recorded versus all-zero action sequences. The latter cannot be copied
literally for board games, where zero may be illegal or semantically special.
AD-WM applies inverse and normalized action recovery to predictor-generated
transitions and evaluates predicted versus realized costs on shared candidate
banks. Its authors report that the inverse-only increment is unresolved in the
Cube elite-regret diagnostic; the inverse objective has a smaller,
weight-dependent effect in the Cube success ablation. This source does not
establish a particular auxiliary as a necessary or sufficient control. Both
papers are arXiv preprints and their results remain author-reported, not
independently reproduced here.

`docs/V212_ACTION_SENSITIVITY_CONTROL_DISPOSITION_DRAFT_01.md` recommends
retaining v04's six arms only for their narrow predeclared contrast family,
subject to independent pre-fit acceptance of the scope exclusion. It does not
call a new seventh arm a matched control: a separate comparator would add a
benchmark contrast, compute, and multiplicity without changing the existing
candidate-versus-control estimands. A broader comparison to action-sensitive
JEPA requires a separately versioned and reviewed benchmark before fitting.
Regardless of arm count, the proposed decision-facing diagnostic must cover
every legal root action, distinguish recorded-support from counterfactual
actions, and pair latent response with exact consequences and exact/bounded
decision regret. Latent separation by itself is not a useful-action test.
This is a draft recommendation only; the research gate remains open and the
v04 method is unchanged.

### Exact Connect Four solution and oracle prior art (2025–2026)

The standard 7x6 Connect Four game has strong-solver prior art beyond the
small legacy games. Böck's 2025 preprint reports a BDD-based exact W/D/L
solution table of 89.6 GB, generated in 47 hours on one CPU core with 128 GB
RAM, plus alpha-beta search for fastest wins/slowest losses
([paper](https://arxiv.org/abs/2507.05267); [author artifact repository](https://github.com/markus7800/Connect4-Strong-Solver)).
The repository documents per-move W/D/L queries against the table and a
separate remoteness search. No license file was present in the inspected
repository tree; its code/artifact is not approved for reuse by this audit.

For a lighter exact action-value interface, the MIT-licensed Rust
[connect-four-ai](https://github.com/benjaminrall/connect-four-ai) source at
commit `28a112adaf3ff89ee23fb09411fa592b6597010e` provides
`get_all_move_scores` over playable columns. Its documentation says scores
are exact, side-to-move remoteness values; its `begin-hard` no-book benchmark
is author-reported and averages 5.09 s. The pinned source and API have not
been independently run or integrated. Pascal Pons's earlier solver also
exposes exact scores per move, but its source is AGPL-3.0-or-later
([pinned repository](https://github.com/PascalPons/connect4/tree/d6ba50d8aaf2308c769d9bf2abd42d90f34baf41)).
These are software/evaluation precedents, not learned-world-model methods.
They eliminate any claim that standard-board exact Connect Four evaluation
is itself novel; they do not establish novelty or value for JEPA.

These sources only narrow the full-game oracle gap for standard Connect Four
6x7. They do not cover Connect Four 8x8 or Reversi. Rust internal search
positions are not the V2.12 planner's 10,000-node accounting; its no-deadline
API and author-reported seconds-scale hard positions cannot be assumed to fit
the 5-second request budget. A future evaluation must predeclare root-player
W/D/L utility and keep remoteness secondary unless the method review chooses
otherwise. Adapter/correctness/license/resource review remains outstanding;
no code or table was run or downloaded.


### 6x6 Reversi semi-strong solution artifact (2026-10-04)

Takizawa's [semi-strong solving paper v2](https://arxiv.org/abs/2411.01029v2)
reports a score-valued exact solution artifact for 6x6 Othello/Reversi over a
certified region `R`, plus a proof certificate. The definition is explicitly
weaker than a strong solve: `R` covers positions reachable when one designated
player follows a canonical optimal policy and the opponent may choose any
legal move. For a declared orientation, every legal successor of a free-agent
node remains in that orientation's region, while an optimal-agent node only
certifies the canonical optimal continuation. The [Zenodo release](https://zenodo.org/records/18843225) describes
exact value queries on `R` and reports a 138.4 GB bundle. The Zenodo rights
metadata has no license value in the inspected snapshot. The artifact is a
potential exact-reference source only for certified roots/actions, not a
complete oracle for arbitrary policy-mixture roots.

The paper's terminal score assigns remaining empty squares to the winner;
CAISSA Reversi terminal utility is winner/draw. Inference from the shared
winner rule: the sign of exact score-margin minimax values equals W/D/L
minimax values, since the sign map is monotone through max/min. It does not
preserve distinctions among moves with the same W/D/L result. Only a root
certified in the orientation-specific region `R_P`, with the side to move
free under that same orientation, has the guarantee that every legal
successor is covered; membership in the union `R` alone is insufficient.
Such a root may support a complete exact W/D/L action row if every child query
is available; negate each child value to convert
from side-to-move to root perspective. At an optimal-agent root under that
orientation, only the canonical optimal continuation is certified, so a full
legal-action regret denominator is unavailable. Membership, orientation,
full child coverage, utility normalization, proof scope, license, and storage
all need verification before use. No artifact was
downloaded or queried. This narrows but does not close the V2.12 oracle gap;
the bounded references for Connect Four 8x8, Reversi6 outside `R`, and Reversi8
remain unselected. See
`docs/V212_COUNTERFACTUAL_DECISION_REGRET_DESIGN_01_DRAFT.md`.


### Weak solution of standard 8x8 Othello (2023)

Takizawa reports a **weak solution** of standard 8x8 Othello: the initial
position is a draw under perfect play, with a strategy that guarantees at
least a draw from that opening ([arXiv:2310.19387v3](https://arxiv.org/pdf/2310.19387)).
The paper defines weak solving as an opening-position result plus a strategy;
it explicitly says the work does not reach its proposed semi-strong category
of calculating best play for all positions. The proof selected 2,587 positions
with 50 empty squares and used exact/bounded-search support at 36-empty-square
subproblems; it is not a table of complete per-action values for arbitrary
reachable roots. The released modified Edax repository is GPL-3.0
([source](https://github.com/eukaryo/edax-reversi-AVX-v446mod2/tree/fbec6a324775b55cafe4a6d9691d92b3fdde2ffc));
raw analysis outputs are separately hosted on Figshare. No code or output was
run or downloaded.

The current Reversi8 implementation appears rule-compatible with standard
Othello's 8x8 opening, alternating turns, flips, forced passes, and terminal
stone-count result based on source inspection; a formal adapter equivalence
check would still be required. This is useful exact-play prior art and an
opening-position anchor, but it does not supply complete root-action scores
for the protocol's sampled reachable positions or change the regret metric.
Do not describe Reversi8 as an unsolved game; do not treat the weak opening
solution as a strong solution, arbitrary-position oracle, or model-evaluation
result. GPL-3.0 and artifact provenance also require review before any reuse.


### Decision-metric alignment and action-conditioned JEPA planning (2026)

Wang et al., *Decision-Metric Alignment in Latent World Models*, distinguish
task-variable decodability from whether a planner's latent cost ranks
candidate plans in the same order as environment outcomes. Their Plan-Real
Spearman and CEM-stage Spearman diagnostics evaluate ranking over random
plans and candidates as CEM concentrates its proposal. Their DA-LeWM adds
inverse-dynamics and demonstration-conditioned goal-action heads to an
action-conditioned LeWM predictor; the heads are discarded at inference, so
the base MPC planner and planning-time compute remain fixed. The authors
report improved convergence and online success across PushT, Reacher, Cube,
and TwoRoom, with similar probe scores ([arXiv:2608.18746v1](https://arxiv.org/abs/2608.18746)).
This is a recent preprint, not independently reproduced here.

The result materially narrows CAISSA-JEPA novelty claims: action-conditioned
JEPA dynamics, inverse-action/goal-action auxiliary supervision, and
planner-candidate rank diagnostics are established prior art and cannot be
claimed as standalone contributions. The benchmark and objective differ:
DA-LeWM uses single-agent Euclidean goal-distance MPC with CEM on four
robotics tasks, whereas CAISSA targets deterministic, fully observed,
alternating zero-sum games and ranks complete legal root actions after
finite-horizon max/min backup. That difference motivates a narrower
empirical question; it does not itself establish novelty.

The paper also reports a relevant negative result: on PushT, its CEM-stage
Spearman falls to approximately zero or below for every compared variant at
the elite stage, including action-supervised DA-LeWM (Table 3). Thus its
global/random-plan ranking lift does not establish local ranking quality
among the plans the optimizer ultimately selects. The paper reports one
training run per configuration and evaluation over three seeds, limiting
evidence about training-seed variability. Before any CAISSA fit, independent
review must assess a DA-LeWM-style inverse-action control and whether any
goal-action target is meaningful for policy-mixture trajectories without
confounding behavior imitation with adversarial decision quality. The present
V2.12 spec does not include this control; no method or gate is amended here.


### Learned latent models for two-player zero-sum games: LAMIR (ICLR 2026)

Kubíček and Lisý, *Look-ahead Reasoning with a Learned Model in Imperfect
Information Games* (LAMIR), directly establish that learned latent game models
can support look-ahead reasoning in two-player zero-sum games. Their
MuZero-inspired model encodes each player's information set, predicts both
players' next abstract information states from a joint action, and predicts
reward, termination, and legal actions. Training uses trajectory data and
recurrent losses for those targets, plus a learned information-set
abstraction; the paper does not present a JEPA objective. At test time the
learned model supports depth-limited reasoning with CFR+, rather than
CAISSA's exact-rule finite-horizon max/min backup.

The scope is materially different but closer than generic single-agent
world-model work: LAMIR addresses imperfect-information simultaneous-move
games without chance, including Leduc Hold'em and imperfect-information
Goofspiel/Oshi-Zumo. Its formalism notes that sequential games can be
represented with fictitious actions for the non-acting player, so
“alternating two-player game” alone is not a defensible novelty claim. The
paper reports lower exploitability than concurrently trained RNaD in smaller
games, and up to 80% head-to-head win rate in large games; these are
author-reported results, not independently reproduced here.

This closes any broad claim that learned latent models plus test-time
look-ahead or equilibrium-oriented reasoning are new to two-player
zero-sum games. A narrower CAISSA comparison remains possible: deterministic,
fully observed board states with known exact rules and legal-action
enumeration; JEPA-style state-latent prediction; and decision-rank/regret
evaluation under finite-horizon adversarial backup against compute-matched
non-JEPA controls. That difference defines a testable empirical question,
not established novelty or evidence of a JEPA advantage. V2.12's planner is a
max/min heuristic and must not be described as a Nash-equilibrium solver.
Source: [Kubíček & Lisý, arXiv:2510.05048](https://arxiv.org/abs/2510.05048),
whose paper identifies itself as published at ICLR 2026.


### JEPA Arcade: action-conditioned JEPA in two-player arcade games (author artifact)

The [JEPA Arcade model card](https://huggingface.co/sauravvvv/jepa-arcade)
describes a 13M-parameter pixel encoder and action-conditioned autoregressive
latent predictor for Pong, Tennis, and Boxing in two-player PettingZoo Atari
environments. It reports SIGReg anti-collapse regularization and supervised
state-head training, including privileged Atari RAM for labels/own-body state;
the playing controller is a hand-written policy over the decoded state. The
card's reported validation evidence is state-probe correlation and state-loss
reduction, not head-to-head strength, minimax planning, regret, or a comparison
against a matched non-JEPA model. It also warns that the collector uses heuristic
plus epsilon-random policies and does not characterize behavior outside that
distribution.

This author-hosted artifact is direct evidence against a broad claim that
action-conditioned JEPA representations have not been applied to two-player
games. It does not test discrete symbolic board states, known exact transition
rules, recursive 1/2/4-ply targets, or alternating max/min decision quality.
The inspected source was the model card; its linked [code repository](https://github.com/saurav-34/lepong)
was not independently reviewed in this pass, and no peer-reviewed paper was
identified. Treat all model-card metrics and descriptions as author-reported.
The narrow V2.12 hypothesis therefore remains an empirical comparison against
matched exact-state and task-prediction controls, not an established novelty
claim.


### Code World Models for General Game Playing (ICLR 2026)

Lehrach et al., *Code World Models for General Game Playing*, use an LLM to
synthesize an executable Python model of a game from its natural-language
rules and sampled trajectories. The code exposes legal actions, transitions,
observations/rewards, and termination; MCTS is used for perfect-information
games and ISMCTS for imperfect-information games, optionally with generated
leaf-value and hidden-state inference functions. Their ten-game evaluation
includes five perfect-information games, among them Connect Four, plus four
novel games; the paper reports matching or outperforming Gemini 2.5 Pro in
nine of ten games. The official ICLR 2026 proceedings page and the arXiv
paper are primary sources; results are author-reported, not reproduced here.

This is adjacent evidence that game-model construction plus classical search
is an established general-game approach, including Connect Four. It is not a
neural latent dynamics learner or JEPA objective: its central model is
LLM-generated executable code, and the comparison is against a general LLM
policy rather than matched learned-dynamics controls. Its trajectory-derived
tests verify sampled behavior, not correctness over every unseen reachable
state. It therefore narrows broad “model-based planning in new games” claims,
but does not resolve CAISSA's specific JEPA decision-quality question or
validate the V2.12 proposal. Sources: [ICLR 2026 proceedings](https://proceedings.iclr.cc/paper_files/paper/2026/hash/d8a12fde9e72444e1b356e8c37e53753-Abstract-Conference.html);
[arXiv:2510.04542](https://arxiv.org/abs/2510.04542).



### Exact chess-state tracking as an adjacent benchmark (2026)

Walker and Lyons' *Chess-World-Model* (arXiv:2605.30100) trains sequence
models to reconstruct the complete chess state after each prefix of legal
moves. Its benchmark uses 10 million Lichess games, a held-out human-game
split, and a uniformly random legal-play split; it compares a causal
Transformer with SLiCE, Mamba-3, and Gated DeltaNet under a shared prediction
interface. The authors report that the recurrent models outperform the
Transformer at the smaller 3M and 8M parameter scales, while the random-play
split remains discriminative at larger scales. The task is exact state
tracking, not move selection or game playing, and it does not evaluate a JEPA
loss, planning, or decision regret. It therefore rules out broad claims that
exact state tracking over deterministic board-game move histories is new,
while leaving the V2.12 objective-attributed decision-quality question open.
The repository is MIT-licensed; this audit did not download or run its code or
data, and its reported experiments were not independently reproduced.
Sources: [paper](https://arxiv.org/abs/2605.30100) and
[author repository](https://github.com/Benjamin-Walker/Chess-World-Model).


### Sequence-trained Othello representations (2025)

Yuan and Søgaard's *Revisiting the Othello World Model Hypothesis* trains
GPT-2, BART, T5, Flan-T5, LLaMA-2, Mistral, and Qwen2.5 variants to predict
the next move from Othello move histories. The source reports 132,588
championship games and 23,796,010 synthetic games, with 10,000 games from
each dataset held out for testing and another 10,000 for validation. The
primary move metric is top-1 next-move error, counting an illegal predicted
move as an error; a separate experiment checks two successive generated
moves. With the full synthetic data, the non-pretrained models report less
than 0.1% one-hop error, while the paper says multi-step generation remains
challenging. It also uses representation alignment and latent-move
projections to argue that board layout and spatial relations appear in the
learned features. These are author-reported results, not reproduced here.

This is direct Othello board-history representation and next-move prior art,
and it further rules out broad claims that learning board structure from
legal game sequences is new. Its next-move target is a recorded move, not a
complete legal-action value/ranking set; its two-hop legality check is not
adversarial look-ahead or decision-regret evaluation. The model is an
autoregressive sequence predictor, not a JEPA transition objective, and the
study does not compare a fixed-compute minimax planner. Therefore it does not
answer whether V2.12's latent matching changes max/min action quality against
matched controls. Source: [Yuan & Søgaard, arXiv:2503.04421](https://arxiv.org/abs/2503.04421),
[full text](https://arxiv.org/html/2503.04421).

### Multiple Othello world models in shared representations (MetaOthello, 2026)

Chawla, Hall, and Lovato's *MetaOthello* (camera-ready version accepted to
ICML 2026) studies small decoder-only Transformers trained on Othello-like
variants that share an 8×8 move syntax but differ in update rules or token
mapping. The suite includes Classic, NoMidFlip, DelFlank, and Iago; pure-game
models use 20 million sequences and mixed-game models use 40 million, with
sequences capped at 60 moves. The authors report next-move-distribution
α-scores above 0.98 across variants and causal cross-variant transfer of
linear board-state probes. For token-remapped isomorphic games, probe
representations align after orthogonal rotation. These are author-reported
representation and prediction results, not reproduced here. The appendix
states that each model was trained once with seed 42, so the study does not
provide across-training-seed uncertainty.

The paper explicitly uses “world model” in the representational sense of
recovering latent board state from a sequence, distinct from an explicit
forward-dynamics model. It therefore establishes shared board-state
representations across rule variants and narrows broad multi-game
representation-transfer claims. It does not evaluate a JEPA transition loss,
complete legal-action values, adversarial max/min planning, head-to-head game
strength, or decision regret; its prediction and probe scores do not establish
planning quality. The variants retain a common 8×8 syntax and do not test
V2.12's board-size transfer. No method or gate change follows: the open
question remains whether V2.12's latent-matching objective changes
fixed-compute decision quality over matched controls. Source:
[Chawla et al., arXiv:2602.23164 v2](https://arxiv.org/abs/2602.23164),
[full text](https://arxiv.org/html/2602.23164).

A separate exact-title search surfaced a 2026 aggregator entry titled
*JEPA-Chess: Action-Conditioned Joint Embedding Predictive Architectures for
Discrete Logical State Tracking*, attributed there to Yumnam Harryson Singh
and described as a Zenodo preprint. Exact-title searches of arXiv, Crossref,
and Zenodo's indexed results did not yield a matching primary record, DOI, or
author repository during this pass. This is a search lead only: the claimed
40-ply accuracy and other metrics are excluded from the evidence until a
verifiable primary source is located. This is distinct from the existing
[CCranney/JEPA-chess development repository](https://github.com/CCranney/JEPA-chess),
which does not establish a completed benchmark or strength result.



### Action-conditioned JEPA for reinforcement learning (ESANN 2025)

Kenneweg, Kenneweg, and Hammer adapt JEPA to image-based reinforcement
learning in CartPole. The context encoder receives three frames, the EMA
target encoder receives the following three-frame window, and a shallow MLP
predictor is conditioned on the one-hot action. They train a PPO actor-critic
on the encoder representation and compare four combinations of JEPA loss,
actor/critic gradient flow, and variance regularization over five runs of
100,000 environment steps. The authors report that joint JEPA and task-gradient
training learns fastest; JEPA-only encoder training collapses without
regularization, while the variance regularizer prevents collapse but learns
more slowly. These are author-reported CartPole results, not independent
replications.
This establishes action-conditioned JEPA representation learning for RL as
prior art. It does not test multi-step learned dynamics planning, exact
symbolic board states, alternating adversarial decisions, or decision regret.
V2.12 must therefore frame its open question as the incremental contribution
of recursive latent matching under exact-rule max/min search against matched
dynamics/value controls, not the first use of action-conditioned JEPA in RL.
Source: [Kenneweg et al., ESANN 2025 proceedings](https://www.esann.org/sites/default/files/proceedings/2025/ES2025-19.pdf);
[DOI](https://doi.org/10.14428/esann/2025.es2025-19).


### JEPA planning under geometry shifts and persistent online adaptation (2026-10-04)

Oberweger, Schwingshackl, and Murschitz, *Does Latent Planning Survive Point Clouds?* (arXiv:2608.29434v2, 28 September 2026), adapt three JEPA world-model designs to simulated LiDAR-style point clouds in four continuous-control scenes. Their action-sensitive Point-Delta-JEPA uses an action-reconstruction objective; evaluation uses receding-horizon CEM on shared fixed start-goal pairs, with ten seeds of 50 episodes. They report point-cloud planning performance comparable to image counterparts and strong results for Point-Delta-JEPA on OGBench-Cube, alongside environment-specific losses (including lower Point-Delta-JEPA scores on Push-T than the LeWM point model). The authors limit the evidence to four simulated tabletop scenes; real-world transfer is untested. This is direct prior art for action-sensitive JEPA planning and cross-observation-modality evaluation, but not for discrete alternating adversarial games, exact legal branches, worst-case reply search, or the V2.12 EMA-target loss. Its reported results are author-reported and were not reproduced here. Source: [arXiv v2](https://arxiv.org/abs/2608.29434).

Zhang et al., *JEPA-TTT: Persistent Test-Time Training of Latent World Models for Planning under Dynamics Shifts* (arXiv:2610.00722v1, 30 September 2026; accepted to the NeurIPS 2026 World Models in Physical AI Workshop), adapt only a pretrained action-conditioned predictor from self-supervised observed transitions, retaining the visual encoder, reward head, optimizer state, and replay buffer across episodes. In four continuous-control environments and eight fixed dynamics shifts, the paper reports higher planning metrics than frozen-JEPA, AdaJEPA, and PPO-TTT baselines, with three deployment runs per shift; its reported mean held-out planning-score AUC is 0.571 versus 0.267 for frozen JEPA. This is online predictor adaptation under changed dynamics, not a comparison of offline JEPA representation objectives or a two-player zero-sum setting. It reinforces that planning outcomes can improve through dynamics adaptation and should not be attributed to latent matching without matched controls. Results remain author-reported and unreplicated here. Source: [arXiv v1](https://arxiv.org/abs/2610.00722).

Together with Wang et al.'s *Decision-Metric Alignment in Latent World Models* (arXiv:2608.18746), these sources keep the defensible V2.12 question narrow: whether its fixed multi-step latent-matching term adds decision quality over matched value-/state-prediction controls under exact-rule adversarial search. Action-conditioned JEPA planning, action-sensitive latent objectives, and planning-aligned diagnostics are already established outside this exact domain. No method change, novelty claim, or fit authorization follows from this source update.


### Action-conditioned JEPA planning prior art: EB-JEPA (2026)

Terver et al.'s EB-JEPA paper and official author repository include AC-video-JEPA, an action-conditioned latent world model with autoregressive multi-step prediction and goal-conditioned MPPI/CEM planning in the Two Rooms environment. The model combines latent prediction with variance/covariance regularization, temporal similarity, and an inverse-dynamics head that predicts actions from adjacent latents. In the randomized-wall setup, the authors report 97±2% planning success, averaged over three training seeds and the last three checkpoints; their ablations report 47±3% without variance regularization, 46±3% without covariance, 61±2% without temporal similarity, and 1±1% without inverse dynamics. These are author-reported results, not independently reproduced here.

This closes any standalone claim to action-conditioned JEPA world-model planning, multi-step latent prediction, or inverse-action auxiliary objectives. The task is continuous 2D goal navigation, not a fully observed deterministic two-player zero-sum board game with exact legal branches and worst-case max/min search. The inverse-dynamics ablation makes the existing V2.12 inverse-action factorial worth explicit reviewer consideration, but it does not show that the same loss is needed when board states and rules are exact, nor does it establish a CAISSA performance effect. No method, baseline panel, or gate changes from this scan. Sources: [Terver et al., arXiv:2602.03604](https://arxiv.org/abs/2602.03604), [ICLR 2026 World Models Workshop paper](https://openreview.net/pdf?id=ZVAMdXGCUC), and the [official EB-JEPA repository and AC-video-JEPA results](https://github.com/facebookresearch/eb_jepa).


### Multimodal JEPA pretraining on interactive game trajectories (ICML 2026 workshop)

Campese and Moschitti study offline-to-online JEPA pretraining on Pokémon Red. Their workshop paper describes a multimodal encoder that fuses game pixels with engineered RAM features, pretrained on offline trajectories and then used as a frozen representation for PPO. They report evaluation on 48 held-out starting states and higher cumulative reward than DINOv3 features, random initialization, and full-encoder fine-tuning; a DINOv3-initialized JEPA is reported to have a mean comparable to DreamerV3 with lower cross-seed variation. They also report that trajectory diversity mattered more than expert-policy provenance in their tested data comparison. These are author-reported workshop results. The source reader exposed the official paper's abstract/first-page text but blocked full-text access, so finer protocol details were not independently extracted.

This establishes JEPA representation pretraining in an interactive videogame domain and narrows broad “first JEPA in games” positioning. The described setup does not establish an action-conditioned transition planner, complete legal-action scoring, two-player zero-sum play, or minimax decision quality; Pokémon Red is a partially observable RPG with a different task and state interface. Its data-diversity result is contextual only and does not change CAISSA's pinned policy mixture or data plan. No method or gate changes. Source: [Campese & Moschitti, ICML 2026 workshop paper](https://openreview.net/pdf/6d63e486bddf8678304b1ec6d1bb11ef034e620e).

### Decision-local JEPA action ranking and outcome supervision (2026-10-04 targeted update)

Two primary-source preprints sharpen the open support/decision question. Zhang
and Li's *ARC-Bench* (arXiv:2609.05461, submitted 12 August 2026) freezes a
context and candidate-action set, obtains candidate terminal costs from
offline executed or simulated rollouts, and measures scorer rankability with
top-1 regret, Hit@k, pairwise accuracy, Spearman correlation, wrong-anchor
rate, and a predeclared “Mirage” rate. It audits released JEPA-WM objectives
in navigation/manipulation settings and reports severe fixed-candidate
misranking; these numbers are author-reported and have not been reproduced
here. This makes direct candidate-ranking diagnostics established adjacent
work. Its candidate costs are goal-distance/task costs, not root-player
zero-sum values from exact adversarial search. It does not test legal board
actions, alternating opponents, or max/min backups. Source: [arXiv full
text](https://arxiv.org/html/2609.05461).

Liu et al.'s *D-JEPA: A Decision-Aligned Latent World Model* (arXiv:2609.24749,
submitted 21 September 2026) is a closer methodological precedent. Its
permutation-equivariant candidate-set relation module learns which predicted
futures should be preferred from candidate executions sharing the same
start/context and goal; candidate identities and availability are held fixed
across compared methods. The paper also studies restricted predictor
adaptation and realization of a learned ordering in JEPA-compatible future
geometry. It reports matched action-selection results across simulated
robotics, driving, and physical-robot tasks; those results remain
author-reported preprint evidence, not an independent replication or a
CAISSA result. The distinction is material: D-JEPA selects among outcome-
labelled goal-reaching candidates, whereas V2.12 predicts latent transitions
from a recorded policy-mixture trajectory and uses those representations in
a fixed exact-rule adversarial max/min tree. D-JEPA therefore defeats a broad
novelty claim for learning JEPA-informed candidate preferences from executed
outcomes, while leaving the narrower exact-board-game objective comparison
unresolved. Sources: [arXiv paper](https://arxiv.org/abs/2609.24749),
[author project and reported protocols](https://nebulis-lab.com/D-JEPA),
[author code repository](https://github.com/NEBULIS-Lab/D-JEPA).

Release status needs careful separation. The code repository identifies an
Apache-2.0 license, but the authors' [checkpoint card](https://huggingface.co/Shuaijun/D-JEPA)
says publication licensing and upstream-weight redistribution checks are not
complete; the linked [dataset card](https://huggingface.co/datasets/Shuaijun/D-JEPA-Dataset)
was empty and exposed no license at this snapshot. No D-JEPA code, model, or
data was downloaded or reused in this audit.

**V2.12 consequence:** action-ranking/regret metrics and outcome-supervised
candidate-set alignment cannot carry a standalone novelty claim. The six-arm
v04 panel should receive an explicit pre-fit review against this decision-
alignment precedent: determine whether a candidate-set, outcome-supervised
control is required to isolate the contribution of recursive JEPA transition
prediction, or document why the frozen estimand intentionally excludes it.
Do not add such a model, loss, candidate labels, or compute after v04 is
frozen. The existing counterfactual-support and decision-regret drafts remain
proposals; this scan does not freeze their oracle, root schedule, threshold,
or estimand. No method/gate changed and no scores, roots, data, training, or
outcomes were run or inspected.

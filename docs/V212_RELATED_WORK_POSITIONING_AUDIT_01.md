# V2.12 related-work positioning audit 01

Search snapshot: 2026-10-04. This is a sourced first-pass comparison, not a
completed systematic review or novelty clearance. The V2.12 method remains
gated; no code, training, model evaluation, or game outcome was produced here.

## Research question under review

V2.12-04 asks whether multi-step latent prediction along recorded actions,
combined with rollout-outcome value supervision, improves a fixed four-ply
max/min planner on two-player deterministic board games over matched
non-JEPA controls. It uses exact rules for legal actions/transitions and
synthetic policy-mixture trajectories; its learned leaf value is not a
minimax value or named-opponent model. The transfer claim is limited to
held-out board sizes within Connect Four and Reversi.

## Closest primary-source comparisons

| Work | What it establishes | Relation to V2.12 | Positioning consequence |
| --- | --- | --- | --- |
| [I-JEPA (CVPR 2023)](https://arxiv.org/abs/2301.08243) | Predicts target-block image representations from image context; establishes latent predictive representation learning, not action-conditioned game planning. | Foundation for JEPA objective family, but not the action-conditioned/dynamics or adversarial-game contribution. | Do not position latent prediction itself as new. |
| [V-JEPA 2](https://arxiv.org/abs/2506.09985) | Video JEPA pretraining followed by V-JEPA 2-AC, an action-conditioned latent world model trained from robot trajectories and used for planning. | Strong conceptual overlap in action-conditioned JEPA prediction and planning; domain is physical robot control with continuous actions, not alternating zero-sum game search. | Rules out broad claims that JEPA has not been used for action-conditioned planning. |
| [JEPA-WM physical planning study (TMLR 2026)](https://arxiv.org/abs/2512.24497) and its [released code/models](https://github.com/facebookresearch/jepa-wms) | Studies how architecture, objective, and planner affect JEPA-WM planning; compares against DINO-WM and V-JEPA 2-AC on navigation/manipulation. | Directly overlaps the empirical question of which JEPA objective/planning design improves planning, although not the turn-taking game setting. | A generic “JEPA planning works better” contribution is already crowded; the controlled game-specific contrast must carry the claim. |
| [DINO-WM (ICML 2025)](https://proceedings.mlr.press/v267/zhou25t.html) | Predicts future pretrained visual features from offline state-action trajectories and optimizes action sequences for goal reaching. | Shares latent future prediction, offline trajectories, and planning; differs in visual observations, continuous control, and goal-reaching objective. | Include as adjacent world-model prior art; do not imply V2.12 is first offline latent-dynamics planner. |
| [Value-Guided Action Planning with JEPA World Models (2025 preprint / 2026 workshop)](https://arxiv.org/abs/2601.00844) | Shapes JEPA representations so latent distance approximates a goal-conditioned value/cost, improving planning in simple control tasks. | Direct overlap with value-informed JEPA planning. V2.12 instead predicts separate synthetic-mixture outcome values and uses max/min search over legal game actions. | Clarify that V2.12 does not introduce value-guided JEPA planning or value-aligned latent geometry. |
| [Temporal-Distance JEPA (July 2026 preprint)](https://arxiv.org/abs/2607.25337) | Mines directed temporal progress/cost from reward-free trajectories and aligns representation/planning horizons; reports improvements on manipulation/navigation tasks. | Direct overlap with trajectory-derived temporal supervision and reducing the train-plan horizon gap; no alternating opponent or exact finite-game tree. | Treat multi-step/plan-aware trajectory supervision as established; compare conceptual distinctions carefully. |
| [LeJEPA (2025 preprint)](https://arxiv.org/abs/2511.08544) and [When Does LeJEPA Learn a World Model? (2026 preprint)](https://arxiv.org/abs/2605.26379) | SIGReg regularizes embedding geometry; later theory studies linear latent identifiability under specified transition assumptions. | Relevant to collapse control and theory. V2.12-04 instead uses EMA target prediction with variance/covariance regularizers; deterministic board dynamics may not meet the later paper's assumptions. | Do not imply variance/covariance regularization is novel; assess whether SIGReg is a necessary competing objective before fitting, through a new reviewed spec if needed. |
| [Generalization Theory for JEPA-Based World Models (June 2026 preprint)](https://arxiv.org/abs/2606.27014) | Connects an action-conditioned co-occurrence/spectral JEPA objective to planning-regret bounds under its assumptions. | Directly overlaps action-conditioned JEPA theory and links representation prediction to planning quality; not a two-player zero-sum board-game study. | Theoretical novelty must be narrower than “the first theory tying JEPA prediction to planning.” Check assumptions against deterministic adversarial transitions before drawing implications. |
| [Variational JEPA (ICML 2026)](https://proceedings.mlr.press/v306/huang26ba.html) | Extends JEPA world models with probabilistic latent predictions and discusses sufficient information states for control. | Adjacent uncertainty-aware predictive modeling; V2.12 assumes deterministic exact game transitions and uses a deterministic predictor. | Acknowledge probabilistic JEPA as a neighboring design; do not generalize V2.12 to stochastic games. |
| [JEPA-Bisim (2026 preprint)](https://arxiv.org/abs/2602.18639) and [Reward-Free Offline Planning with Latent Dynamics (2025 preprint)](https://arxiv.org/abs/2502.14819) | Study control-relevant/invariant latent representations and offline JEPA planning in navigation/manipulation settings. | Share offline trajectory learning and planning objectives, with continuous single-agent physical control rather than an exact legal-action adversarial tree. | Include in any objective/control comparison; distinguish game semantics from generic action-conditioned dynamics. |
| [MuZero (Nature 2020 / arXiv)](https://arxiv.org/abs/1911.08265) | Learns a latent model for reward, policy, and value used in tree search; reports Go, chess, shogi, and Atari results without supplying game rules to the model. | Strongest game-planning comparator: latent learned dynamics plus search in board games, but not JEPA target-representation prediction and not the same known-rules setup. | Avoid presenting learned latent game planning or board-game world models as new. Distinguish the training objective and controlled comparison. |
| [AlphaZero (2018)](https://arxiv.org/abs/1712.01815) | Learns policy/value by self-play while using exact game rules in search across chess, shogi, and Go. | Establishes the known-rules policy/value/tree-search baseline family. | The exact-rules planner and self-play are established; V2.12's mechanistic contribution concerns latent JEPA supervision, not search itself. |
| Titonis et al., [World Models for Adversarial Games: ConnectX](https://doi.org/10.5281/zenodo.21904378), [author repository](https://github.com/alextitonis/WorldModel-ConnectX) | Zenodo preprint/author project, not peer-reviewed. Learns encoder/dynamics/value and uses exact legal adversarial search on Connect Four. The author's detailed code/repo distinguishes its deployed exact-search system from a latent-beam baseline; metrics are author-reported and not independently reproduced. | Closest direct game-domain system precedent. It is not JEPA: no EMA target objective is specified, training transition bundles one fixed opponent reply, and it covers one board size. | Rules out framing latent model plus adversarial board search as a new system concept. Any remaining claim must isolate JEPA-specific objective effects against matched controls. The existing project ledger contains the detailed source/code audit. |
| Kubíček & Lisý, [LAMIR (ICLR 2026)](https://arxiv.org/abs/2510.05048) | MuZero-inspired learned latent game model supports depth-limited reasoning with CFR+ in imperfect-information two-player zero-sum simultaneous-move games. | Directly establishes learned latent models plus look-ahead in two-player zero-sum games, though not JEPA, deterministic fully observed boards, or exact-rule max/min search. | “Two-player zero-sum latent planning” is not novel in general. Position V2.12 around its narrower known-rules/full-observation/JEPA/control question. |
| Qiu et al., [AD-WM](https://arxiv.org/abs/2609.30264), and Gan et al., [ActSWM](https://arxiv.org/abs/2607.26712) | Recent preprints study action-discriminative or action-sensitive multi-step JEPA rollouts, action recovery, and planner-facing counterfactual comparisons. | Strong overlap with multi-step action-conditioned JEPA planning; evaluated in continuous control/open-world video games with CEM, not legal symbolic branches or zero-sum max/min. | Multi-step prediction, action sensitivity, or counterfactual candidate scoring cannot carry a standalone novelty claim. Compare a reviewed action-sensitive JEPA control before any fit. |
| Lehrach et al., [Code World Models for General Game Playing (ICLR 2026)](https://arxiv.org/abs/2510.04542) | Generates executable game models and uses MCTS/ISMCTS on multiple games including Connect Four. | Adjacent general-game model-plus-search work; model is synthesized code, not learned JEPA latent dynamics. | Further narrows broad claims about game-model construction and planning. |

## Game-domain leads outside peer-reviewed literature

The search also found [JEPA Arcade](https://huggingface.co/sauravvvv/jepa-arcade),
whose model card describes a frozen self-supervised world model, a small
linear state probe, and a hand-written policy in two-player PettingZoo Atari
environments. It is a direct game-domain and two-player lead, although its
public model card is not a peer-reviewed evaluation and describes a different
pipeline from V2.12's learned action-conditioned board-state predictor and
max/min planner. Other leads include [LeMario](https://www.benjamin-bai.com/projects/lemario),
an independent LeWorldModel reproduction on Super Mario Bros;
an [open-source JEPA-style Snake project](https://github.com/Thibault-GAREL/AI_snake_World_Model_version);
and [Agentic-JEPA](https://zenodo.org/records/20237490), a 2026 preprint on
text-based agent environments. These are demonstrations/preprints, not
peer-reviewed two-player board-game comparisons. LeMario's author reports
that short-horizon prediction/nearby image-goal movement did not yield reliable
progress over a longer game level, a useful warning that prediction accuracy
alone does not establish planning competence. Treat these as prior-art leads,
not validated baselines or evidence of novelty.

The repository's existing [`RELATED_WORK.md`](RELATED_WORK.md) contains
deeper source/code audits of ConnectX, LAMIR, AD-WM, ActSWM, Code World
Models, JEPA Arcade, and other board-game/world-model comparisons. This
snapshot summarizes their relevance; it does not replace the detailed audit.

## Preliminary novelty-risk assessment

Risk is **high** for a broad algorithmic claim and **moderate-to-high** for a
narrow empirical claim. The central ingredients are individually established:
multi-step action-conditioned latent prediction, learned latent values,
trajectory-based plan-aware supervision, and learned-model planning in board
games. The defensible candidate contribution is therefore a narrowly scoped,
matched-control experiment asking whether the multi-step JEPA term adds
measurable value inside this fixed deterministic alternating-player planner,
under held-out board-size evaluation. This is a candidate framing, not a
novelty conclusion.

The spec's controls are useful for attribution: single-pair JEPA,
recursive raw-state dynamics, value-only latent rollout, direct-leaf value,
and a single-horizon JEPA ablation. A research review must still decide whether
the comparison is scientifically adequate against current JEPA-WM variants,
especially value-guided/plan-aware objectives and LeJEPA/SIGReg. The frozen
six-arm v04 design cannot silently absorb a new arm or objective; any change
requires a new method version and independent review before fitting.

The sharper experimental risk is support mismatch: V2.12 trains latent targets
only along the recorded action sequence, but the test-time planner compares
alternative legal branches. Low prediction error on behavior trajectories does
not establish action discrimination or correct ranking of those unobserved
branches. Before any fit, decide through review whether the design needs an
action-sensitive JEPA control and a frozen diagnostic that scores every legal
root action and measures decision regret against a bounded exact-search
reference. The existing
V2.12-04 spec does not yet resolve that question; do not add either silently.

The exact legal-action max/min tree does not turn the leaf into a minimax
value. Because V2.12 labels are outcomes from a synthetic mixture of four
policies, results concern that specified heuristic and its head-to-head game
behavior. They do not establish equilibrium quality, exploitability, or
robustness to arbitrary opponents. Keep that distinction explicit when
comparing with AlphaZero/MuZero and opponent-modeling literature.

## Remaining search before novelty clearance

1. Search proceedings and bibliographies for JEPA/action-conditioned latent
   dynamics in discrete, alternating, competitive, or zero-sum games, including
   non-board game environments; record search terms and inclusion criteria.
2. Trace citations forward and backward from V-JEPA 2-AC, JEPA-WM,
   Value-Guided JEPA, TD-JEPA, the 2026 JEPA planning theory papers, MuZero,
   and AlphaZero. Separate peer-reviewed work, preprints, workshop papers,
   released-code claims, and unreviewed demos.
3. Compare the exact V2.12 objective and its six arms against the primary
   sources, including what each model predicts, its labels/data, planner,
   action/opponent assumptions, evaluation domains, and compute matching.
4. Resolve whether an action-sensitive JEPA arm, full legal-root scoring,
   bounded exact-search regret reference, and/or recent plan-aware/value-aligned
   JEPA baseline are required and feasible under the fixed budget. If the spec
   changes, version and review it before fitting; otherwise state the
   limitations and do not substitute comparators after seeing outcomes.

Read alongside the project's existing detailed ledger, this first pass found
peer-reviewed JEPA planning in physical domains and a non-peer-reviewed
project explicitly describing JEPA plus a hand-written policy for true
two-player Atari environments. A “first JEPA game planner” or “first
two-player JEPA game agent” claim is unsupported. ConnectX and LAMIR remove
broad claims to learned latent game planning or two-player zero-sum look-ahead.
The exact combination of JEPA prediction with known-rule deterministic
board-state max/min remains an unresolved narrow empirical question, not
established novelty. No scientific-performance or superiority conclusion
follows from this audit.

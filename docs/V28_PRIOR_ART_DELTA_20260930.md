# V2.8 prior-art delta: action-sensitive JEPA (2026-09-30)

This is a targeted update to the V2.7 review, not a systematic review or a
novelty certification. It uses primary full-text sources and narrows the
candidate claims before any JEPA fitting. No cited dataset, code or checkpoint
was acquired or used.

| Work | Question, method and domain | Data, baseline, metric and reported result | Relevance and boundary for CAISSA-JEPA |
| --- | --- | --- | --- |
| Zoabi, Ali & Wolf, **Hamiltonian JEPA: Action-Conditioned World Models with an Inherited Control State**, arXiv v1, 2026-09-27. [Paper](https://arxiv.org/html/2609.33497v1) | Can the planner-facing state geometry and dynamics be structured so action effects remain useful for planning? H-JEPA separates a perceptual code from a fixed orthonormal control-state slice, uses a port-Hamiltonian predictor, and ties inverse action readout to the same orthonormal input port. | Offline image/action trajectories on Two-Room, DeepMind Control Reacher, PushT and OGB-Cube; compares PLDM, LeWM, Sub-JEPA and Delta-JEPA under a shared planning protocol; 500 test episodes/task and three training seeds. Reported success: 100/86.13/90.40/91.93% for H-JEPA; OGB-Cube 91.93±1.30 versus Delta-JEPA 79.27±1.81. H-JEPA trains 10 epochs versus Delta-JEPA's 50. | Direct precedent for action-conditioned JEPA, a control-oriented latent, structured action effects, action decoding and planning gains. It is continuous/visual control, not turn-based adversarial play. **Do not claim that action-sensitive or planning-useful JEPA is new.** The remaining candidate must test whether alternating role/opponent reply structure adds value in a zero-sum decision setting. |
| Gan et al., **ActSWM: Action-Sensitive World Models for Long-Horizon Planning in Open-World Games**, arXiv v2, 2026-08-15. [Paper](https://arxiv.org/html/2607.26712v2) | Does explicit action sensitivity prevent latent rollouts from becoming action-agnostic over long horizons? ActSWM combines multi-step latent prediction, separation between recorded-action and alternative-action rollouts, and a frozen action readout of latent transitions. | Offline VPT Minecraft H5 trajectories for step-drift tests; MineStudio closed-loop torch placement, stone mining and pillar-building with a shared CEM/MPC planner; 20 trials/task. Reported outcomes include 19/20 versus 10/20 for mining, 20/20 versus 19/20 for torch placement, and 17/20 versus 11/20 for pillar-building against LeWM. It reports larger recorded-versus-zero action gaps and over 80% lower zero-action similarity in its step-drift diagnostic. | Closest game-domain JEPA world-model/planning precedent found in this delta. Minecraft is open-world control, not a two-player alternating zero-sum game; its planner tracks a reference trajectory rather than solving a minimax objective. Action-separation losses/readouts are established prior art, not a CAISSA contribution by themselves. |
| An et al., **Diagnosing JEPA World Models with Action-Conditioned Predictive Consistency**, arXiv v1, 2026-08-13. [Paper](https://arxiv.org/html/2608.12939v1) | Can paired multi-step predictions diagnose how visual perturbations affect a JEPA planner? ACPC compares clean/perturbed histories rolled under identical action sequences; Invariance Radius and Separation Rate jointly screen perturbation stability and representation collapse. | Four visual-control tasks, LeWM and PLDM; three training runs, trajectory-grouped cross-validation (16 disjoint groups) for prediction-error drift. The paper reports its multi-step action-conditioned diagnostic lowest cross-validated error in all 12 task/run cells, with 55.9±4.7% relative reduction to the base and 51.3±3.5% against an eight-step destroyed-action control. It is a diagnostic, not a training loss or direct improvement to the planner. | Suggests action-conditioned rollout diagnostics and matched destroyed-action controls; visual perturbation is not the same as game role-swap/symmetry or opponent counterfactuals. It does not establish an adversarial-game method. |
| Bagatella et al., **TD-JEPA: Latent-predictive Representations for Zero-Shot Reinforcement Learning**, ICLR 2026. [Proceedings paper](https://proceedings.iclr.cc/paper_files/paper/2026/hash/3d158f054ff0cb83397367234899db07-Abstract-Conference.html) | Can temporal-difference learning produce multi-step latent dynamics across policies/tasks from offline reward-free transitions? It uses explicit state/task encoders and a policy-conditioned multi-step predictor. | Evaluated over 13 ExoRL/OGBench datasets against zero-shot RL baselines; reports matching or outperforming leading baselines, especially pixel-based settings. | Multi-policy conditioning, multi-step prediction, and zero-shot transfer are already established. It does not model an adversarial player or minimax/equilibrium planning. |
| Balestriero & LeCun, **LeJEPA: Provable and Scalable Self-Supervised Learning Without the Heuristics**, arXiv v3, 2025-11-14. [Primary full text](https://arxiv.org/html/2511.08544v3) | Develops an isotropic-Gaussian embedding target and SIGReg, a sketched characteristic-function distribution-matching regularizer, alongside latent prediction; argues this can avoid EMA teacher/stop-gradient heuristics. | Reports stability across 60+ architectures and 10+ datasets, including large-scale image experiments; no alternating adversarial-game planner or board-game regret evaluation. | EMA/variance regularization is not the only principled collapse control. Treat SIGReg/LeJEPA as an objective-level comparator or justified alternative in development; do not claim anti-collapse regularization as novelty. Its reported theory/experiments do not directly establish guarantees for trajectory-correlated game states or minimax planning. |

## Design consequences

The original V2.8 candidate is not method-frozen. A two-ply EMA-JEPA auxiliary
on its own is not a unique contribution: action-conditioned JEPA, action
sensitivity/readouts, multi-step prediction, and task transfer all have close
prior art. The V2.7 audit separately identifies Athénan, minimax-Q, and
value-preserving abstraction as controls against generic complete-branch or
action-order claims.

If a distinct method survives feasibility, the narrowest defensible question
is whether a **role-conditioned, alternating-action latent predictor** yields a
better fixed-budget decision in a two-player zero-sum game than (i) the same
KLENT-style direct policy/Q learner, (ii) matched non-JEPA task prediction, and
(iii) a direct value/minimax control, when all receive the same legal reply
closure and planner. Report whether the advantage comes from the model, planner,
or additional target exposure. The experiment must include action-separation
diagnostics (recorded versus adversarial/reassigned replies), latent separation,
and decoded-state/task-prediction controls. This is a **candidate estimand**,
not a novelty claim.

Reversi4 has now passed only the exhaustive rules/transition subgate: 62,789
reachable player-states including terminal, 89,332 legal transitions checked,
8,988 forced-pass states, and 113,900 complete two-ply reply pairs. The audit
does not cover a training/test split, opponent power, compute parity, JEPA
training, or playing strength. Reversi4 is only a feasibility variant and does
not support a general board-game claim. See
`V28_REVERSI4_RULES_GATE_01.md` and its receipt.

## Stop rules

- If role-conditioned prediction is mathematically reducible to an existing
  minimax-Q/tree-value or action-sensitive world-model objective without a
  measured fixed-budget decision benefit, drop the algorithm-novelty claim.
- If a JEPA arm does not beat KLENT direct policy/Q **and** matched task
  prediction on the predeclared primary metric under identical planning and
  measured compute, retain the null result and pivot to a benchmark/negative
  result or a narrower question.
- If only Reversi4 passes, label any result as that toy variant; do not claim
  cross-game generalization.

## Sources

- H-JEPA, full primary text and reported table: https://arxiv.org/html/2609.33497v1
- ActSWM, full primary text and task tables: https://arxiv.org/html/2607.26712v2
- Action-Conditioned Predictive Consistency, full primary text: https://arxiv.org/html/2608.12939v1
- TD-JEPA, official ICLR 2026 proceedings: https://proceedings.iclr.cc/paper_files/paper/2026/hash/3d158f054ff0cb83397367234899db07-Abstract-Conference.html

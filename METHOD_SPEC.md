# CAISSA two-player JEPA — method specification v1

Frozen design: 2026-09-29, before new research code/training. Status: proposed CPU feasibility method, not a proven new algorithm. Amendments require a version and reason; this v1 text remains the protocol reference. Existing MARS-JEPA Chess stays a separate compatibility implementation.

## Games and semantics

A GameSpec defines finite states S, players p(s) in {+1,-1}, legal A(s), deterministic T(s,a), terminal predicate d(s), and terminal utility u(s) in {-1,0,+1} for player +1. The other player's utility is -u. Every legal move, including pass, changes player. Terminal states have no legal actions and cannot transition. Observation is the full rule state; history/clocks must be included when rules require them. No stochastic, simultaneous, hidden-information or general-sum adapter is accepted as in-scope.

First feasibility games: tic-tac-toe 3x3, gravity connect-3 on 4x4, and Reversi 4x4 with explicit forced pass. Hold out a connect variant (4x5 connect-4) from all training. These are tiny-game/variant experiments, not evidence of broad game-family generalization. Chess remains the legacy controlled domain until a complete history-aware adapter and independent rule replay are validated.

State features: board padded into an 8x8 grid with own/opponent/valid-cell planes, plus normalized height/width/connect target and rule-family/gravity descriptors. Own/opponent is relative to p(s). Actions identify placement cell in the same 8x8 coordinates; pass is index 64. Gravity actions map a column to its currently legal landing cell. Rule descriptors are fixed inputs, not learned per-game weights. One shared encoder/predictor/policy/value parameter set is trained jointly across the training games. Separate ablations and seeds have separate checkpoints, not separate game weights.

Geometric transforms: square placement games/Reversi use legal D4 symmetries; gravity permits horizontal reflection only. Transform state and actions together. Role relabeling multiplies board/player/utility by -1 and leaves side-to-move features invariant. Canonical state keys include game/rule parameters, board, player and pass/history data; use role-relative geometric canonical keys for overlap auditing. Never rotate gravity or apply chess color/board swaps without proven rule equivalence.

## Causal representation and targets

z_t = f_theta(x(s_t)); target zbar_t = f_xi(x(s_t)), with stop-gradient target and EMA xi <- 0.99 xi + 0.01 theta after each optimizer step. The pilot encoder is a tanh affine map to 32 latent dimensions. This deliberately small architecture tests feasibility, not state of the art. No normalization fitted on held-out data; features have fixed scaling.

g_phi(z_t, e(a_t), e(b_{t+1}), h) predicts zbar_(t+h), h in {1,2}. H1 has no opponent action; H2 includes the observed opponent reply. The predictor is a tanh affine layer on latent, two 65-dimensional one-hot action slots and a two-dimensional horizon indicator. Missing action slots are zeros. If a terminal state is reached before a requested horizon, that horizon is absent; never pad a terminal target as an observed future action. H1/H2 targets are always produced by exact legal transitions. H4 is deferred; the legacy chess H4 is not silently reused.

A state transition predictor given both actual actions is **not** a behavioral opponent model. A separate masked-softmax policy head pi_theta(a|s) is trained on observed actions; when applied on the opponent's actual state it predicts the generated data policy. No opponent identity/history embedding or calibrated personality model is claimed. A future such model must explicitly condition on opponent observations and evaluate calibration under held-out opponents. The pilot minimax planner does not average with pi.

v_theta(z) = tanh(w_v z + b_v) estimates outcome from **the player to move at the represented state**. Training label is p(s_t)u(s_terminal) from the generating trajectory, not minimax value. Odd-ply values negate when converted to root perspective; two-ply values keep sign. Exact terminals override neural predictions. Monte Carlo behavior values can be poor minimax leaf estimates; this is an explicit experimental limitation.

## Loss and optimizer

Each loss averages over its own valid sample count; no valid horizon targets means zero contribution and reported count zero. For each h, L_J,h = mean ||g_h - stopgrad(zbar_(t+h))||^2 / latent_dimension. Full JEPA uses L_J,1 + L_J,2. Policy CE is over all legal actions only; illegal logits are excluded. Value loss is mean squared error against the actual trajectory outcome.

Variance regularizer on online context latents: L_var = mean_j max(0, 0.1 - sqrt(var_batch(z_j)+1e-4))^2. Population batch variance; derivative follows the same formula. It is a collapse deterrent, not a full-rank or isotropic-Gaussian guarantee. Covariance/effective rank must be measured separately. No LeJEPA/SIGReg theory claim.

L_total = L_policy + L_value + L_J,1 + L_J,2 + 0.1 L_var. H1 ablation removes H2 loss; no-response removes only the opponent action input at H2; no-var sets variance coefficient to zero. Masks, weights and inputs are versioned in each checkpoint. No hard-negative margin replaces all-legal CE.

Direct control: identical encoder/policy/value, policy+value losses only. Decoded-dynamics control: same latent transition topology, but supervise a linear decoder of predicted latent against the fixed target state features (MSE), not an EMA latent target; policy/value remain. This is a compact non-JEPA dynamics control, not MuZero/EfficientZero. Predictive controls also train the value head on predicted latents with horizon-correct outcome signs (weight 0.25 per valid horizon) to reduce the train/inference latent-value mismatch; this term and its active compute must be reported. A later faithful consistency-control study is required for strong novelty claims.

Optimizer: Adam, lr=1e-3, beta1=.9, beta2=.999, epsilon=1e-8; global gradient norm cap 5. Batch size 64, fixed shuffled epochs, seeds 17/29/43. Float64 NumPy in initial pilot to make manual finite differences reliable; no mixed precision. Finite-difference checks freeze EMA targets and compare the unclipped analytic gradient before Adam. Record active/allocated parameter counts; do not claim exact FLOP matching merely because inactive tensors remain allocated.

## Data and runtime contract

Generate bounded deterministic-policy self-play trajectories with recorded generator seed and policy mixture (uniform random plus immediate-win preference for placement games; Reversi random). This is exploratory synthetic behavior, not optimal labels or human data. Replay all moves and compare terminal utility. Deduplicate canonical trajectories; assign deterministic grouped 70/10/10/10 train/validation/model-selection/locked-final-test by trajectory hash before samples. Held-out variant receives no training allocation. All context/H1/H2 state keys participate in a held-out-first ownership audit; quarantine conflicting records, count reasons, and require nonempty splits. Include generated-source hashes and generator configuration in identity; current Git HEAD is provenance, not the sole data hash.

Exact transition targets are allowed for states reached by the recorded trajectory; no counterfactual outcome label is fabricated. If future counterfactual branches are added, their states can be exact but outcome labels require separate rollout/oracle provenance and cost accounting.

Checkpoint saves contain model/EMA/Adam arrays, seed, step/epoch, config, objective version, source/config/data/split fingerprints and RNG state. Use temporary write + fsync + atomic replace; fresh refuses a collision. Resume requires full identity match and resumes only a committed epoch boundary; deterministic epoch seed reconstructs shuffle. Never load pickle. Generated artifacts are ignored. Diagnostics include traceback and phase on failure; zero optimization steps never equals trained.

## Planning tracks

1. **Same-search exact-state track:** deterministic legal-action order, shared depth-limited negamax, exact T and terminal checks, same node/time limits; model leaf is v(f(x(s))). This isolates learned representation/value changes without predicted-latent use.
2. **Hybrid latent two-ply track:** enumerate legal root action and opponent reply using exact T, override terminal branches, evaluate remaining two-ply leaves by v(g(z,a,b,2)); use max_a min_b. This is a depth-2 minimax approximation with learned leaves, not a full equilibrium solver and not simulator-free. H1 terminal/one-ply branches use correct sign. H1-only can use a separately reported one-ply predictor; direct policy-value re-encodes exact states. Comparison therefore has different encoder work, which must be charged.
3. **No-model control:** identical exact search with a declared simple heuristic or zero nonterminal value, plus exact minimax oracle on tractable states. Policy-only choice is a separate searchless control.

All tracks count legal transitions, searched nodes and neural calls and measure wall time, including root scoring. Stop cooperatively at configured limits; retain only completed root/depth decisions, record fallback/overrun. Late returns, illegal moves and infrastructure errors are failures/censored, not draws. A terminal result reached on the final allowed ply is a real result. Do not claim hard real-time guarantees.

## Evaluation and inference boundaries

Exploratory validation metrics: H1/H2 latent error and count, latent norm/std/covariance/effective rank, policy all-legal top-1/MRR/NLL, value MSE, and observed-policy calibration if estimated. Report by game/phase/tactical condition and seed; label behavior labels as behavior. Confidence intervals cluster by trajectory; seed summaries remain visible and are not replaced by pooled position intervals.

Same-search planning: use an immutable list of validation positions and budgets; report oracle action regret on tractable late-game states, complete color-swapped matches where feasible, and all censored/error outcomes. Exact tiny-game policy best response can measure NashConv/exploitability only when the full policy/tree is evaluated with a stated convention. Otherwise use the precise term action regret or match score.

Cross-game: evaluate unchanged shared weights on the held-out variant with no fitting; report zero-shot and compare to untrained/direct controls. Future few-shot adaptation uses fixed labeled budgets and a separately held-out test. Training games do not count as transfer.

Confirmatory protocol is **not authorized by a pilot result**. Before final evaluation freeze one primary metric (planned equal-game-weight paired score difference vs direct control), number of independent situations/matches, role swaps, >=3 seeds, budgets, source/checkpoint/data hashes, independent rules/engine identities, cluster CI method, Holm secondary correction, timeout/censor policy and fixed stopping. Sample size must be justified using development variance/power before opening final results. No replacement of failures/openings after viewing outcomes. Default confirmation gate remains closed until all fields and independent review pass.

## Acceptance and interpretation

Rules, target/mask/sign/gradient/serialization/resume/leakage tests precede training. Audited data and noncollapsed multi-seed learning precede any strength study. Improved latent MSE alone never establishes planning benefit. Multi-game shared weights are an implementation property; generalization is an empirical claim. Report negative results, approximate leaf-value bias, dataset-selection effects, short horizons, tiny-game scope, statistical limits and resources before discussing publication suitability.

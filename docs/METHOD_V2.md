# Method v2: recurrent reply-fork JEPA development study

Frozen before v2 model implementation/fitting, 2026-09-29. Scope: prospective
development candidates, not established novelty or a claim of improvement.
The original v1 source/receipts remain unchanged. Read the two v2 source reviews
and adaptive-development control first.

## Data and question

Survey03 supplies500 roots each of gravity connect4 4x5 and Reversi6x6, all with
5..8 empty cells, multiple legal actions, nonterminal depth2 leaves and unequal
exact action values. Both pass rule-only difficulty support. Root selection uses
no learned predictions. Reference bitboard v2 and exact adapter transitions must
agree. All generated data stays local.

Split root trajectories by stable hash50/20/15/15 into train/development/selection/
final. Canonical symmetry/role keys include rule configuration. Exclude roots
whose complete depth2 input/target closure overlaps another split, held-out-first.
Also exclude held-out closures overlapping v1.2 training feature states. Required
support per game after audit:100 train roots,50 development roots,40 selection
roots,40 final roots. No training from failed support or unresolved labels.

For every root enumerate legal own actions and all legal replies. Each child
and grandchild receives **its own exact mover-perspective minimax value** and a
policy target uniform over its exact optimal legal actions. Terminal states have
value labels but no policy loss. A root move ending the game has H1 and no H2.
The exact oracle may traverse unseen states for solving; those internal states
never become model features unless explicitly included in the audited closure.
Teacher computation and all query/source hashes are reported separately.

Every method sees identical observed root/child/grandchild features, legal masks,
oracle labels and branch samples. This prevents extra teacher/state exposure from
being attributed to JEPA. A later trajectory-label/fork ablation must be separately
declared; v2 gains over v1 would not isolate JEPA because labels and benchmark change.

## Architecture and objective

Features/actions retain the frozen198-dimensional padded role-relative contract
and65 cell/pass IDs. Encoder: tanh affine198->64 then tanh affine64->32. Policy:
linear32->65 with exact legal softmax; value: tanh linear32->1. One shared model
is trained on both games; no game-specific weights.

Shared recurrent dynamics: `g(z,a)=tanh(z Wg + onehot(a) Wa + bg)`, latent32.
Predict H1 from root and own action, H2 from predicted H1 and actual reply, with
backpropagation through both steps. It is an action-conditioned transition model,
not a behavioral opponent model. EMA0.99 target encoder follows online updates.

All variants have mean legal policy cross-entropy and value MSE over the valid
encoded root/child/grandchild states (same coverage and masks). Predictive variants
add0.25 times mean value MSE at each enabled predicted horizon against that
successor's independently computed mover-perspective oracle value. No reuse of
the root outcome for counterfactual actions. H1/H2 terminal targets are valid;
predictors are never asked to transition from a terminal state.

Candidate/control variants:

- `direct`: encoded policy/value supervision only.
- `value-dynamics`: same recurrent predictor and predicted-value losses, no
  reconstruction or latent objective.
- `decoded`: add per-horizon MSE from a linear32->198 decoder to successor features.
- `rjepa`: add per-horizon normalized projected latent matching. Online projection
 32->16 and prediction16->16; target projection is EMA of online projection,
 paired with EMA target encoder. Normalize with `sqrt(sum(v^2)+1e-6)` and use mean
 squared Euclidean distance summed across normalized coordinates (not divided
 by16). Stop all target gradients. Raw value/policy heads consume unprojected z.
- `raw-jepa`: same recurrence with unprojected latent MSE per dimension, the
 alternative objective nearest the v1 implementation.
- `no-response`: same as rjepa but zero only the second (opponent) action vector.
 It retains the first own action and all observed successor supervision.

Latent/reconstruction coefficient is1 for the initial grid; all online encoded
contexts receive0.1 variance-floor penalty with targetstd0.1 and epsilon1e-4,
except direct (zero). This choice is disclosed as a regularization-package
contrast; rjepa versus value-dynamics shares the variance penalty. Record
unprojected and projected effective rank separately; normalization is no proof
against collapse. Projected collapse invalidates a claim about useful JEPA
geometry even when policy/value works. No SIGReg/LeJEPA guarantee is claimed.

Manual gradients are checked against finite differences with EMA frozen for
every active tensor, including recurrent H2 pathways, projection normalization,
variance, legal soft targets and missing horizons. All models allocate matching
common tensors for initialization pairing, but active parameters/compute differ.

## Runtime and interface contract

Float64 NumPy; Adam(.9,.999,eps1e-8), global gradient cap5; batch128; latent32,
hidden64,projection16. Config includes variant,seed,learning_rate and jepa_weight.
Initial development grid: six variants x learning rates0.001/0.0003 x seeds17/29/43;
36 runs.40 epochs; one BLAS thread; one run at a time; per-run cap180s and a3GB
aggregate generated-artifact cap. Run every declared cell or report failure;
do not keep only best epochs. No adaptive early stopping in this first grid.

Epoch sampling:16 seeded fork draws per training root, balanced game weighting
by sampling the same number of roots per game (minority roots may repeat,
exposure counts reported). Every variant uses the identical seeded schedule.
The count of unique roots/forks and repeated samples stays visible.
Within a root sample complete legal forks uniformly, so an own action with more
legal replies receives more mass. This distribution is identical across controls;
it is neither a learned opponent policy nor uniform own-action sampling.

Model batch API: `x[N,3,198]`, `valid[N,3]` boolean, `legal[N,3,65]`,
`policy[N,3,65]` soft optimal-action distribution, `value[N,3,1]`,
`actions[N,2,65]`; missing H2 is zero features/action with valid=false.
`Model(Config)` exposes encode/value/policy_logits/rollout, loss_grad/update,
atomic save/load with tensor hashes and strict source/config/data/objective identity.
Epoch-addressed RNG permits exact epoch-boundary resume; checkpoint stores
optimizer/EMA/counters. Corrupted or mismatched identities fail closed.

## Evaluation, tuning and promotion

Primary development metric: equally weighted mean exact oracle action regret
across the two games using identical exact-state depth2 search. Same action order,
tie-break, legal branches, node4096/time1s caps. Paired differences use the same
roots/seeds; report every seed, per-game effects and trajectory/seed uncertainty.
Primary comparisons are against best-development direct and decoded/value-dynamics
configurations with the same learning-rate opportunity. This grid is adaptive
development, not confirmation or a formal significance test.

Separate hybrid recurrent-latent track has identical legal branches and terminal
overrides; it includes model rollout error. Direct re-encodes exact leaves.
Untrained neural and no-model zero-leaf search are fixed controls, not promotion
comparators. Report optimal-action rate, regret, neural leaves, oracle gaps,
censoring, value/policy and representation diagnostics by game/structural stratum.

Promotion target before fitting: at least0.05 absolute reduction in equal-game
mean regret against the strongest relevant tuned control, positive per-game
improvement in both families, and consistent direction in at least2/3 seeds,
without collapse or excess failures. This is a development screen, not proof.
A finite shortlist and separate selection protocol must be frozen before scoring
selection data. Final remains unopened until power/readiness review; no candidate
is called independently validated from this grid alone. Failure triggers a logged
new development hypothesis with fair baseline changes, not post-hoc threshold edits.

### Promotion mechanics clarified before any fitting

For each of the six families choose one global learning rate by the mean primary
regret across both games and all three seeds. Never choose a rate per seed/game.
Ties within1e-12 choose0.0003. Promotion-eligible JEPA families are rjepa and
raw-jepa; no-response is attribution only. Among eligible families choose the
lower development regret, preferring rjepa on an exact tie. Comparators are each
of direct,decoded,value-dynamics at their own globally selected rate; the
candidate must meet the0.05 aggregate margin against the strongest comparator
and positive per-game differences versus all three. At least2/3 paired training
seeds must have the favorable aggregate direction for each comparator.

Every declared training cell and scheduled decision must complete. Any numerical
failure, timeout or missing decision makes the screen inconclusive; no substitution
or silent deletion. Collapse is checked on all valid encoded development states,
stratified by game: effective rank<2 or median dimensionstd<1e-3 blocks a model.
For projected JEPA variants also apply these thresholds to online projected
development encodings. Unused projection tensors of other controls are ignored.
A candidate configuration with any seed/game collapse is ineligible; failed
controls cannot be silently bypassed to obtain promotion. Preserve all metrics.

Report paired per-seed effects and2,000 hierarchical paired bootstrap replicates
(seed901), resampling the same training-seed indices and root trajectories for
candidate/control, separately within each fixed game. Intervals describe the
development sample and three-seed cohort; they do not correct adaptive selection
or establish confirmation. No p-value or universal significance claim is made.

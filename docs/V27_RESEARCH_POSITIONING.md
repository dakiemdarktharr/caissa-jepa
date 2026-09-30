# V2.7 research positioning: outcome-trained adversarial game evaluation

**Status: pivot proposal, not frozen.** Only a model-blind match-schedule
feasibility helper and its small receipt exist; this is not a model or training
implementation. V2.6 exact-minimax supervision has not passed its model-blind
feasibility gate. This proposal does not reuse its roots, labels, or metrics as
evidence. No V2.7 self-play data have been generated and no model has been
trained.

## Why change the estimand

V2.5 was a complete negative development comparison. V2.6 then found the
feasibility gap between tiny positions where exact search is cheap and larger
positions where the current exact-label solver times out. Selecting only the
solved large-board positions would bias the benchmark. A match-based outcome
study avoids exact minimax labels for training and can measure end-to-end
strength on harder positions, but changes the question: win rate against a
fixed, declared opponent suite is not minimax regret, exploitability, or Nash
equilibrium quality.

Proposed falsifiable question: with the same local self-play trajectories,
game rules, policy/value labels, model capacity, training updates, and inference
search budget, does a two-ply, both-player-action-conditioned JEPA objective
improve paired match performance over direct policy/value, recurrent
task-prediction, and explicit state-feature prediction on at least two
deterministic zero-sum game families?

The target opponent suite would be fixed before training and include independent
legal-random, tactical heuristic, frozen historical self-play checkpoints, and
an independently implemented search reference where its rights and runtime
permit. Report every matchup and seat separately. A positive result supports
only the tested model, variants, budget, and opponent population. It does not
show response prediction for a named opponent unless that opponent is explicitly
identified in both training and evaluation; it does not show worst-case play.

## Nearest prior art and novelty risk

| Work | Established design/domain | Consequence for CAISSA-JEPA |
| --- | --- | --- |
| Assran et al., I-JEPA (CVPR 2023), [paper](https://arxiv.org/abs/2301.08243) | Predicts target-region embeddings from context embeddings without pixel reconstruction. | Latent prediction itself is not a contribution. |
| Schwarzer et al., SPR (ICLR 2021), [paper](https://arxiv.org/abs/2007.05929) | EMA-target, action-conditioned multi-step latent prediction for Atari control. | Action-conditioned multi-step consistency is established; include a close non-JEPA predictive control. |
| Schrittwieser et al., MuZero (Nature 2020), [paper](https://arxiv.org/abs/1911.08265) | Recurrent action-conditioned latent dynamics with reward, policy, and value learning; demonstrated on chess, shogi, Go, and Atari. | Latent planning across board games is established; do not claim it as new. |
| Ye et al., EfficientZero (NeurIPS 2021), [paper](https://arxiv.org/abs/2111.00210) | Adds latent consistency to recurrent MuZero-style planning, with Atari/continuous-control evidence. | A JEPA/consistency auxiliary beside a planner is established. |
| Bagatella et al., TD-JEPA (ICLR 2026), [proceedings](https://proceedings.iclr.cc/paper_files/paper/2026/hash/3d158f054ff0cb83397367234899db07-Abstract-Conference.html), [official code](https://github.com/facebookresearch/td_jepa) | State/task encoders, a policy-conditioned multi-step predictor, and latent policies for zero-shot RL. Official code states CC BY-NC 4.0. | The proposed sequential predictor is close prior art. Conditioning on a second player's action or changing the domain is not enough to establish novelty. No code is copied or used. |
| Soemers et al., board-game variant transfer, [paper](https://arxiv.org/abs/2102.12375) | Policy/value transfer across board-game variants. | Multi-variant game transfer is established independently of JEPA. |
| Grimm et al., Value Equivalence, NeurIPS 2020, [paper](https://arxiv.org/abs/2011.03506) | Argues that learned models should preserve planning-relevant value updates, not merely generic transitions. | Predictive loss must connect to a controlled decision metric; latent error alone is inadequate. |
| He et al., Opponent Modeling in Deep Reinforcement Learning, ICML 2016, [proceedings](https://proceedings.mlr.press/v48/he16.html) | DRON jointly learns a policy and opponent-strategy representation, evaluated in simulated soccer and trivia. It targets adapting to observed opponent behavior. | This is behavior modeling, unlike the proposed transition predictor conditioned on an observed reply. A match win against a fixed opponent does not establish opponent-model accuracy or generalization. |
| Rajeswaran et al., A Game Theoretic Framework for Model Based RL, ICML 2020, [proceedings](https://proceedings.mlr.press/v119/rajeswaran20a.html) | Treats policy and learned model as players in a Stackelberg-style game to address model-policy distribution shift in continuous-control MBRL. It is not a turn-based two-player board-game planner. | Game-theoretic model robustness is adjacent, but does not make our minimax planner, fixed-suite match estimator, and behavior model interchangeable. We need to state which one is evaluated. |
| Bai, Jin & Yu, self-play in zero-sum games, [paper](https://arxiv.org/abs/2006.12007) | Formalizes equilibrium-oriented learning and distinguishes it from best-response behavior. | Self-play match outcomes cannot be called equilibrium evidence without exploitability/Nash-gap analysis. |

This targeted review is not a systematic review. Current novelty disposition:
**high risk / unverified**. The only defensible potential increment is a rigorously
isolated study of how both-player counterfactual latent prediction changes
bounded-compute decisions in a defined game suite. This is a domain-specific
scientific question, not yet a unique method claim. Before freezing the method,
search specifically for reply-conditioned or two-player minimax JEPA, strategic
representation objectives, and outcome-trained latent planners. If an equivalent
method/evaluation already exists, narrow the question or stop the novelty claim.

## Proposed method family, subject to feasibility

The starting candidate is provisionally named **reply-conditioned two-ply JEPA**
only as an internal identifier. For observed nonterminal trajectory states
\(s_t\), acting-player action \(a_t\), and actual legal reply \(b_t\):

\[
z_t=f_\theta(s_t),\quad
\hat z_{t+1}=q_\psi(z_t,e(a_t),r_t),\quad
\hat z_{t+2}=q_\psi(\hat z_{t+1},e(b_t),r_{t+1}).
\]

EMA target embeddings of the actual successor states supply stop-gradient
targets at each valid nonterminal horizon. Separate policy and player-to-move
outcome-value heads train on the same visited states for every family. A JEPA
candidate is distinct from a behavior model: it predicts a state representation
conditioned on the observed legal action sequence; it does not claim to predict
which action a particular opponent will choose. The planner is fixed before
training and named explicitly: either policy-mixture expectation against the
declared opponent suite, or worst-case search. These are separate experimental
arms and may not be pooled. An opponent-policy model, if ever added, requires a
separate behavior-label objective and calibrated held-out opponent likelihood.

Minimum learned controls: direct PV; same recurrent predictor with task/reward/
policy-value prediction and no latent-state matching; same recurrent predictor
with decoded state-feature prediction; and JEPA with its latent loss ablated.
All controls share trajectory rows, outcomes, symmetries, legal masks, seed
schedules, encoder/head widths, tuning opportunity, and planner. Include a
no-search policy-only comparison and a fixed rule-search reference as separate
system baselines. Training-data generation and any extra counterfactual
transitions must be provided to controls or charged and disclosed.

This two-ply loss is still close to SPR, EfficientZero, TD-JEPA, and MuZero.
Do not fit it unless the targeted novelty check identifies a precise unresolved
question and the pre-fit audit confirms that the local code can test it fairly.
If it is merely a replication in another domain, label it a replication study.

## Data and evaluation gates

1. **Rules and domain pilot.** Use only project-owned deterministic rules. Extend
   board caps only after transition, terminal, symmetry, and independent
   reference checks pass. Candidate families are gravity Connect4 and Reversi;
   select exact dimensions after match length, branching, runtime, and heuristic
   strength probes. The 8x8 oracle-cost probes are feasibility receipts only.
2. **Self-play data audit.** Generate local trajectories from a frozen
   population (random, tactical, and archived policy opponents) with game IDs,
   opponent IDs, seats, seeds, outcomes, and rules fingerprint. Split by complete
   game trajectory and rule configuration before exposing outcomes. Hash every
   record; audit replay, legal transitions, duplicate/symmetric trajectories,
   seat balance, outcomes, and train/evaluation opponent separation. All records
   are project-generated and have no third-party data license dependency.
3. **Development feasibility.** Run a small fixed pilot with at least three
   training seeds and paired color/seat-swapped matches. This only checks data
   coverage, training stability, runtime, and whether all families learn above
   chance. No model selection or confirmatory claim.
4. **Adaptive development.** Only after audit, permit a finite set of
   development-driven objective/architecture changes. Give every baseline the
   same tuning rounds, data, compute cap, and evaluator. Preserve failed runs in
   an append-only ledger. Never retune using selection/final match outcomes.
5. **Model selection.** Freeze candidate and baseline configurations, matchup
   suite, run count, seat schedule, statistical analysis, censors, and
   multiplicity correction first. Keep the model-selection opponent pool
   disjoint from training opponents. Prior development opponents remain
   development evidence.
6. **Locked confirmation.** Use newly generated seeds and held-out variants or
   opponents, a predeclared primary paired win-rate/score metric, cluster
   uncertainty over complete games and training seeds, and fixed stopping rules.
   Report any timeouts as losses or by a predeclared censor rule. Report Elo only
   with its opponent graph and uncertainty. Do not call match score
   exploitability. Any equilibrium claim additionally requires a justified
   best-response/Nash-gap estimator and its own error audit.

### Feasibility pilot 01 (2026-09-29)

`tools/v27_match_feasibility.py` ran eight base seeds, all three policy
pairings, both seat assignments, and two project-owned games: 96 complete
matches in 5.207 seconds on Python 3.11.9/Windows CPU. Connect4-gravity-8x8
averaged 26.83 plies with 0 draws; Reversi8 averaged 59.44 plies with 1 draw.
Results were balanced in aggregate by construction. The sanity heuristic beat
random in all 16 heuristic-vs-random games in each game family; this indicates
that the current pair is too weak and saturated to serve as the learned-model
evaluation bank. It does not estimate strength or rules validity. The receipt
stores every seed, seat, outcome, length, and final-state hash in
`docs/validation/V27_MATCH_FEASIBILITY_01.json`. Three targeted tests pass; the
pilot tool is the only V2.7 code so far. Next model-blind feasibility step is
an independently implemented stronger search opponent and differential rules
validation, followed by repeated runtime/pairing checks. OpenSpiel's official
documentation lists minimax/alpha-beta and MCTS implementations, while its
Connect Four source exposes rows, columns, and connect-target parameters; this
is a viable source for a future executable differential audit, but `pyspiel` is
not installed in the current environment and no third-party code was acquired
or executed. See the [official Connect Four source](https://github.com/google-deepmind/open_spiel/blob/master/open_spiel/games/connect_four/connect_four.cc)
and [official algorithm inventory](https://openspiel.readthedocs.io/en/latest/algorithms.html).
No self-play dataset,
model fit, checkpoint, or positive JEPA result exists.

The tiny pilot's outcome balance is not sufficient to freeze the primary match
protocol: random and heuristic policies are engineering sanity controls, not a
credible opponent population. The candidate method, fairness matrix, and match
estimand remain proposals until an informative independent opponent suite
exists.

## Proposed V2.7 go/no-go thresholds

These thresholds are **provisional gates to calibrate from a model-blind power
pilot before method freeze**, not results or values to tune after outcomes:

- At least two game families must have replay-valid self-play data and
  non-saturated matches against the independent opponent bank.
- All learned families must complete the same minimum per-seed data and training
  budget. A family that does not learn above chance makes the run inconclusive.
- Primary development effect must exceed a predeclared practically meaningful
  paired match-score margin against the strongest tuned learned baseline, with
  favorable direction in each game family and at least 2/3 seeds. The margin and
  sample size must be set from a separate model-blind variance/power pilot.
- No result advances if JEPA collapses, match censoring differs, a positive
  effect is explained by extra data/search/parameters, or it wins only against
  the weakest heuristic.
- A development win only nominates a finite selection step. A selection win
  only nominates independent locked confirmation.

## Decision and stop rules

Pivot V2.6 to this separate proposal because exact labels do not offer a
workable large-game coverage/cost regime. Before writing model code, complete
the targeted novelty search and run model-blind rules/opponent/runtime pilots.
If the current CPU-only manual-gradient runtime cannot cover a fair training
grid, optimize the implementation or reduce the fixed development matrix
before fitting; do not install large frameworks or use cloud compute without
authorization. Do not reuse V2.5/V2.6 evaluation states as a fresh locked test.

Kill or narrow the JEPA claim if direct/task-prediction/state-prediction
baselines match it; if JEPA only improves behavior against training-like
opponents; if outcomes reverse by game/seat; if only the expected-opponent
planner wins but the worst-case arm does not; or if prior art already contains
the claimed mechanism. Negative results can support a careful empirical
comparison paper, but not a JEPA-superiority claim.

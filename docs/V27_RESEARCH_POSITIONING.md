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

The original broad hypothesis—both-player-action-conditioned latent
prediction improves bounded planning—remains the project's motivation, but is
no longer an adequate V2.7 novelty question after the prior-art re-audit.
Current falsifiable candidate: with identical complete legal counterfactual
reply sets, teacher coverage/censoring, capacity, optimizer updates and measured
training/search compute, does latent-state prediction plus a separate worst-case
action-order-preservation objective improve held-out minimax decision quality
over direct minimax-Q/value learning, Athénan-style tree-value learning,
approximate Q/minimax state abstraction, direct policy/value transfer,
task/reward/policy prediction, and decoded state-transition controls? These are
the required controls, not an assertion that the candidate differs sufficiently
from prior work. The candidate is not frozen; see
`V27_PRIOR_ART_REAUDIT_20260930.md`.

Two independent read-only audits sharpened the stop gate: direct minimax-Q can
learn the same action order from the same successor labels, while Athénan
already enumerates legal children and tree-bootstraps searched values. The
candidate therefore survives only if its latent target adds measurable
planning-relevant information or lowers decision regret at fixed measured
compute. Before training, run the model-blind closure/coverage gate in the
prior-art re-audit; if that added information or cost advantage is absent, drop
the JEPA-specific claim rather than promote the same minimax learner under a new
name.

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
| Cohen-Solal, Athénan (JMLR 2026), [paper](https://www.jmlr.org/papers/v27/25-2259.html) | Neural tree bootstrapping from search states, Descent minimax, richer outcome heuristics and ordinal action selection; evaluated on the exact two-player perfect-information zero-sum game class across Go, Hex, Othello, Arimaa, Connect6, Havannah and more. | Strong direct non-JEPA precedent/baseline: reports +62.51% ± 6.3% against ExIt across ten games and 91% vs. MoHex in Hex-11 at 2.5 s/move. Large compute limits local replication, not the relevance of its algorithmic control. Tree-state learning means complete branch supervision alone is not novel. |
| Cohen-Solal & Cazenave, *Minimax Strikes Back* (AAMAS 2023), [paper](https://www.lamsade.dauphine.fr/~cazenave/papers/MinimaxStrikesBack_AAMAS.pdf) | Direct Athénan-vs-Polygames/AlphaZero comparison; Athénan learns state evaluation using minimax/Descent and no policy. | Reports much lower training-state generation cost and competitive/superior game results under its own resource setup. Strong evidence that minimax value learning can be a powerful low-compute non-JEPA baseline. |
| Ishibashi et al., *Approximate State Abstraction for Markov Games* (AAAI 2025), [official paper](https://ojs.aaai.org/index.php/AAAI/article/download/33930/36085) | Extends approximate state aggregation by optimal Q/minimax value to two-player zero-sum Markov games, proves a duality-gap bound, and evaluates exact-Q aggregation in a 760-state Markov Soccer game. | Any general “JEPA learns a compact minimax-sufficient state” claim overlaps this work. Its experiments rely on solving the small game and do not use JEPA or multi-step predictive representation; those gaps are only starting points for a measured increment. |
| Zhao et al., PCZero (ICML 2022), [PMLR paper](https://proceedings.mlr.press/v162/zhao22h.html) | Adds path-consistency regularization to AlphaZero and uses historical plus MCTS-scouted paths for efficient learning. | Reports 94.1% against a 2015 Hex Olympiad champion on 13x13 Hex versus 84.3% for AlphaZero, with 900K self-play games; also reports Othello/Gomoku transfer and offline-learning results. This is an important non-JEPA consistency/efficiency control. |
| Soemers et al., *Transfer of Fully Convolutional Policy-Value Networks Between Games and Game Variants* (TMLR 2023), [arXiv full text](https://arxiv.org/html/2102.12375) | Uses AlphaZero-like networks and Ludii channel semantics for zero-shot and fine-tuned parameter transfer across board-game variants and distinct games. | Cross-game transfer is established for direct policy-value networks. JEPA needs a same-data/same-compute transfer control and held-out-family tests; transfer itself cannot be its novelty claim. Cite the TMLR version in the paper; the arXiv v1 is superseded. |
| Gao et al., *A transferable neural network for Hex* (ICGA Journal 2018), [publisher record](https://doi.org/10.3233/ICG-180055) | Transfers a board-size-independent neural network from a base Hex board to larger and smaller sizes, zero-shot and with fine-tuning, including search. | A board-size-only generalization result is not novel evidence for JEPA. Compare it to direct policy/value parameter transfer under the same search budget. |
| Ye et al., EfficientZero (NeurIPS 2021), [paper](https://arxiv.org/abs/2111.00210) | Adds latent consistency to recurrent MuZero-style planning, with Atari/continuous-control evidence. | A JEPA/consistency auxiliary beside a planner is established. |
| Schwarting et al., Deep Latent Competition (CoRL 2020; PMLR 2021), [proceedings](https://proceedings.mlr.press/v155/schwarting21a.html) | A competitive two-player racing agent uses a joint latent transition over both players' actions, opponent-view prediction, an opponent-action model, and imagined self-play. The environment is visual racing rather than a deterministic, fully observable board game. | Two-player competitive latent world models and opponent-conditioned imagination predate this project. Our novelty cannot be “include the opponent” or “use latent self-play.” We differ in game class, deterministic legal-action structure, and potentially worst-case minimax objectives; those differences need an empirical/theoretical increment. |
| Bagatella et al., TD-JEPA (ICLR 2026), [proceedings](https://proceedings.iclr.cc/paper_files/paper/2026/hash/3d158f054ff0cb83397367234899db07-Abstract-Conference.html), [official code](https://github.com/facebookresearch/td_jepa) | State/task encoders, a policy-conditioned multi-step predictor, and latent policies for zero-shot RL. Official code states CC BY-NC 4.0. | The proposed sequential predictor is close prior art. Conditioning on a second player's action or changing the domain is not enough to establish novelty. No code is copied or used. |
| Kaplowitz et al., MA-JEPA (arXiv preprint submitted 2026-09-27), [preprint](https://arxiv.org/abs/2609.33563), [full text](https://arxiv.org/html/2609.33563) | Joint-embedding world model for cooperative Dec-POMDP MARL/SMAC. A training-only predictor conditions on synchronized local states and simultaneous joint actions to predict each agent's next observation embedding; policy/value learning uses imagined latent rollouts. It is not an alternating, fully observable, two-player zero-sum game, and the source is a new preprint rather than peer-reviewed work. | This is very recent and materially increases risk: JEPA with joint action-conditioned multi-agent prediction and imagined planning is already explicit. Our contribution cannot be framed as the first multi-agent or opponent-action-conditioned JEPA. We must compare objectives and solution concept, not just the domain. |
| Soemers et al., board-game variant transfer, [paper](https://arxiv.org/abs/2102.12375) | Policy/value transfer across board-game variants. | Multi-variant game transfer is established independently of JEPA. |
| Grimm et al., Value Equivalence, NeurIPS 2020, [paper](https://arxiv.org/abs/2011.03506) | Argues that learned models should preserve planning-relevant value updates, not merely generic transitions. | Predictive loss must connect to a controlled decision metric; latent error alone is inadequate. |
| Xie et al., model-based multi-agent RL in zero-sum Markov games, NeurIPS 2020, [proceedings](https://proceedings.neurips.cc/paper_files/paper/2020/hash/0cc6ee01c82fc49c28706e0918f57e2d-Abstract.html) | Model-based learning of Nash-equilibrium values/policies with sample-complexity guarantees. | Zero-sum model-based game solving is established; keep equilibrium and fixed-opponent match estimands separate. |
| Zhu & Zhao, Online Minimax Q Network Learning (IEEE 2020), [source](https://ieeexplore.ieee.org/document/9292435/) | Neural minimax-Q learning for two-player zero-sum Markov games. | Include direct minimax-Q/value as a required non-JEPA control; this source's detailed benchmark configuration still needs full-text review. |
| Dodge et al., AAR/AI (ACM TiiS 2021), [method paper](https://faculty.ist.psu.edu/jxd6067/mypapers/J04-AARAI.pdf) | Their two-player simultaneous-action RTS agent uses learned transition, leaf evaluation and top-level action ranking with a two-round minimax search; the paper studies human assessment. | Learned ranking plus model/value components inside adversarial search clearly predates this candidate, though it does not report JEPA or compare a complete reply-set loss against a pairwise minimax-order objective. |
| He et al., Opponent Modeling in Deep Reinforcement Learning, ICML 2016, [proceedings](https://proceedings.mlr.press/v48/he16.html) | DRON jointly learns a policy and opponent-strategy representation, evaluated in simulated soccer and trivia. It targets adapting to observed opponent behavior. | This is behavior modeling, unlike the proposed transition predictor conditioned on an observed reply. A match win against a fixed opponent does not establish opponent-model accuracy or generalization. |
| Rajeswaran et al., A Game Theoretic Framework for Model Based RL, ICML 2020, [proceedings](https://proceedings.mlr.press/v119/rajeswaran20a.html) | Treats policy and learned model as players in a Stackelberg-style game to address model-policy distribution shift in continuous-control MBRL. It is not a turn-based two-player board-game planner. | Game-theoretic model robustness is adjacent, but does not make our minimax planner, fixed-suite match estimator, and behavior model interchangeable. We need to state which one is evaluated. |
| Bai, Jin & Yu, self-play in zero-sum games, [paper](https://arxiv.org/abs/2006.12007) | Formalizes equilibrium-oriented learning and distinguishes it from best-response behavior. | Self-play match outcomes cannot be called equilibrium evidence without exploitability/Nash-gap analysis. |

This targeted review is not a systematic review. Current novelty disposition:
**critical risk / unverified**. Deep Latent Competition already studies
two-player competitive imagined latent interaction with opponent actions, and
MA-JEPA now studies joint-action-conditioned target-embedding prediction and
latent imagination in a different multi-agent game class. The differences in
game timing, observability, reward structure, and solution concept are real,
but are not automatically novel contributions.

The only candidate question worth targeted follow-up is narrower: does training
on the **complete legal counterfactual reply set** with an auxiliary objective
that preserves the ordering of worst-case (minimax) action values improve
fixed-budget decisions over equally trained minimax-Q and Athénan-style
tree-value learners, task-prediction, and decoded-state controls in deterministic
alternating games? This is a
candidate empirical question, not a unique method claim. The exact targets,
planner, controls, transfer protocol, and feasibility gates are not frozen.
Before coding this objective, search specifically for minimax/world-model
value-equivalence methods, minimax-Q neural learners, learned action ranking in
minimax search, adversarial branch-prediction objectives, and counterfactual
action-set representation learning. AAR/AI is a close learned-ranking plus
transition/value plus minimax-search precedent; resolve the precise objective
distinction from the primary source. If an equivalent method or stronger
controlled study exists, stop or recast the work as replication/benchmark.

## Candidate method family, subject to novelty and feasibility gates

### Required direct-policy/Q control from KLENT

Full-text review of Ota et al. (ICML 2026 accepted) found a concrete strong
baseline omitted from the initial plan. KLENT directly trains policy and
action-value (Q(s,a)) in self-play with reverse-KL and entropy regularization
and λ-returns, with no search during training. Their five-game experiments use
a shared 6-block ResNet and three seeds. In the aggregate learning curve,
KLENT reaches 50% average win rate against its anchored Pgx opponents at 75M
simulator evaluations, versus 300M for Gumbel AlphaZero. Their separate
800M-training-evaluation match protocol gives each agent 800 test-time MCTS
rollouts and reports a 77.2% average for KLENT against the anchored baseline.
These are source-paper results only; do not present them as directly comparable
to CAISSA's measurements.

Any V2 claim of efficiency or advantage over learned baselines must include a
KLENT-style regularized direct policy/Q arm (or justify a faithful-port blocker)
alongside direct minimax-Q. They address different objectives: KLENT learns
regularized self-play policy/returns, while minimax-Q approximates worst-case
action values. Report environment calls separately from CPU wall time and
training compute, since simulator-call parity alone does not account for JEPA
encoding, prediction, and gradient costs. The precise source-level setup and
limits are recorded in `V27_PRIOR_ART_REAUDIT_20260930.md`.

The earlier realized-reply formulation is withdrawn as a novelty candidate:
conditioning on the observed own-action/opponent-reply sequence is too close to
SPR, TD-JEPA, Deep Latent Competition, and MA-JEPA. The narrower candidate for
follow-up is provisionally **legal-reply-set minimax-preservation JEPA**; this
name is only an internal label and the method is not frozen.

For deterministic turn-based rules \(T\), a nonterminal root \(s\), legal own
actions \(A(s)\), and legal replies \(B(T(s,a))\), enumerate
\(s_{ab}=T(T(s,a),b)\) for every legal pair. Let \(z=f_\theta(s)\) and
\(\hat z_{ab}=q_\psi(z,e(a),e(b),e(\mathrm{game}),e(\mathrm{turn}))\). A target
encoder supplies stop-gradient \(\bar z_{ab}=\bar f_\xi(s_{ab})\). The basic
counterfactual-set prediction loss would average over **all** legal \((a,b)\)
pairs at each sampled root, not just the pair that happened in one trajectory.
This alone is not novel; joint-action latent prediction is prior art.

The strategic candidate adds a separately specified worst-case action-order
preservation objective: where a predeclared teacher provides trustworthy
depth-two action values \(v_B(s,a)=\min_{b\in B(T(s,a))} V_B(s_{ab})\), train a
latent value head \(\hat v(s,a)\) to preserve pairwise ordering of own actions
with a fixed margin and tie mask. The planner then uses legal engine transitions
for branching and latent values at its declared cutoff; it does not ask a
learned policy distribution for the opponent's action. Teacher labels must be
complete for the admitted root bank or the whole predeclared root is censored;
no post-hoc filtering of hard positions is allowed. Exact teacher feasibility
is currently a known risk and the previous V2.6 cost gate failed on larger
roots.

This candidate is distinct from an opponent behavior model (no opponent action
distribution is predicted), distinct from a worst-case planner (minimax is the
planner's solution concept, not a learned model), and distinct from a policy-
mixture expectation. Expected-opponent planning and worst-case search remain
separate studies. If the teacher cannot cover a sufficiently discriminating
root bank without selection bias, do not fit this objective; return to method
design or stop the minimax claim.

Minimum learned controls for any future fit: direct PV; KLENT-style regularized
direct policy/Q self-play; direct minimax-Q; same predictor with task/reward/
policy-value prediction and no latent-state matching; same predictor with
decoded state-feature prediction; JEPA with latent matching but without the
minimax-order term; and the full candidate. All controls get the same
enumerated legal counterfactuals, teacher availability/censoring, game rules,
parameter budget, optimizer opportunity, seeds, and inference planner. Include
a no-search policy-only comparison and a fixed independent rule-search
reference as separate system baselines. Teacher/search FLOPs and counterfactual
transition generation must be common or accounted and disclosed.

The counterfactual-set loss is close to existing multi-agent joint predictors;
the unresolved candidate is whether minibatch training that preserves an
adversarial minimax action ordering contributes under equal compute in this
strict game class. Do not fit until targeted prior-art search identifies that
gap precisely, teacher labels pass a model-blind coverage/power pilot, and a
pre-fit fairness audit confirms the same target/censor/compute exposure for all
controls. If this only replicates minimax-Q/model-based game learning with a
JEPA auxiliary, describe it as such rather than claiming a new architecture.

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

### Bounded-search opponent feasibility, exploratory (2026-09-30)

An in-repository depth-limited negamax/alpha-beta opponent was added on top of
the separate bitboard `ReferenceGame` implementation. It has a fixed depth 3,
500-node per-move cap, a handwritten line/mobility/corner evaluator, and emits
its completed depth and node-cap diagnostics. This is a feasibility policy,
not a calibrated engine. Differential tests compare legal actions, terminal
outcomes, and every resulting board/player over four seeded trajectories in
each of Connect4-gravity-8x8, Reversi8, and rectangular Connect-6x7. The
independent implementation agrees on those tested trajectories; it remains
same-project validation, not third-party rule certification.

The fingerprinted paired-seat pilot in
`validation/V27_SEARCH_OPPONENT_03.json` contains 32 games (two seeds, four
pairings, both seats, two game families) and took 86.69 seconds locally. The
preceding same-schedule V2 run took 53.43 seconds; both are exploratory CPU
timings and should not be treated as stable performance estimates.
Search beat the simple center/corner policy and legal-random policy in 4/4
games per family for each pairing. That is encouraging only as an opponent-bank
sanity result: two seeds are not an estimate of strength or uncertainty. It
also exposed a serious diagnostic: search-vs-search in Reversi8 was won by the
minus seat in both unique seeded trajectories (four receipt rows include
duplicate seat swaps), and the pilot hit its per-move node cap 116 times
in that family. The earlier deterministic tie-order pilot is preserved in
`validation/V27_SEARCH_OPPONENT_01.json`; the revised seat-seeded tie ordering
is separately recorded in `validation/V27_SEARCH_OPPONENT_02.json`. These are
development receipts, not selection or confirmation data. Before this policy
can anchor training or evaluation, analyze color/dihedral equivariance,
improve Reversi budget completion, and repeat a model-blind seat-symmetric
variance/diversity pilot. Do not treat its wins as JEPA evidence.

### Reversi symmetry correction pilot (version 3; exploratory)

The search was changed to normalize the player-to-move as +1, map square
Reversi positions to a canonical D4 orientation, and sample uniformly among
symmetry-tied canonical maps. The same fingerprinted 32-match schedule in
`validation/V27_SEARCH_OPPONENT_04.json` took 51.19 seconds. The canonicalizer
unit test checks every rotation, reflection, and color/turn swap on a seeded
midgame state; all map to the same canonical position. Search again won the
center/corner and random pairings 4/4 per family. In Reversi it recorded 68
node-cap hits versus 116 in the prior V2 run, while total calls and trajectories
also changed; this small run is a diagnostic comparison, not an efficiency
claim. Reversi search-self-play favored the plus/first seat in the two unique
seeded trajectories (four receipt rows include duplicated seat-swap records),
whereas V2 favored the minus/second seat in its two unique trajectories. This
cannot separate first-move advantage from residual seat/RNG effects; the
discrepancy remains unresolved. Do not freeze this opponent suite or generate
training data from it yet.

### Novelty re-audit (2026-09-30)

A targeted primary-source search found two closer works than the initial review
captured. **Deep Latent Competition** already models two-player competitive
latent interaction, opponent view/action, and imagined self-play in visual
racing. **MA-JEPA**, a preprint submitted 2026-09-27, jointly predicts target
embeddings conditioned on all agents' local states and simultaneous actions,
then trains policies through imagined latent rollouts on cooperative SMAC. SMAC
is outside this project's primary class (partial observations, simultaneous
multi-agent actions, cooperative shared rewards), but the architecture makes
“joint-action-conditioned JEPA” untenable as a novelty claim. Together these
works push novelty risk to **critical**. The only candidate gap is now an
adversarial one: whether complete legal-reply-set prediction combined with
minimax action-order preservation adds value under a matched compute budget in
deterministic alternating games. This needs its own prior-art search, exact
definition, and teacher-coverage gate. The existence of this gap is not yet
verified. The candidate formulation above is not frozen, and no training should
start until that check passes.

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

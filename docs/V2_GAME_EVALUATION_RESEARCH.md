# V2 game planning and evaluation research

Date: 2026-09-29. Status: primary-source design review, not an executed v2 result.
This note supplements `RELATED_WORK.md`, `BENCHMARK_V2_SPEC.md`, and
`V2_RESEARCH_CONTROL.md`. It does not alter their frozen limits or authorize
opening model-selection/final predictions.

## Main finding

The strongest near-term hypothesis is that supervision over legal reply branches
improves representations used by a bounded adversarial planner, compared with
trajectory-only representation training. A measured gain must survive controls
for extra state coverage, better value labels, and recurrent consistency. This
is a prospective hypothesis, not an established novel method. MuZero, SPR,
EfficientZero, and value-equivalent modeling already cover large parts of the
conceptual space. A newly discovered ConnectX implementation also combines
learned latent dynamics, exact adversarial search, and a learned leaf evaluator.

The old pilot cannot decide this question: its exact-state planners all achieved
zero regret and its Connect3 roots never queried a learned leaf. More epochs
cannot repair an evaluation whose decisions do not depend on the representation.
The initial v2 rule-only feasibility survey is therefore appropriate.

## Search method and scope

Five Exa searches requested 10 results each. Their distinct angles were:

1. Learned latent models for adversarial minimax planning and action conditioning.
2. Board-game evaluator benchmarks, horizon effects, and independent game rules.
3. Adaptive model selection and uncertainty after trying multiple candidates.
4. Self-prediction, value equivalence, and counterfactual auxiliary supervision.
5. Official OpenSpiel rules/evaluation and reusable-holdout research.

The requested result-slot total is 50, not a count of 50 independently verified
papers. Search mirrors and snippets were discovery aids only. The table below
uses original papers, proceedings, official documentation, or author code.
Fetched passages were bounded; this is a targeted review, not an exhaustive
systematic review or a claim to have read every full paper. Search results on
hidden-information games were excluded from the primary design because their
belief-state/equilibrium machinery is outside the current scope.

## Work matrix

| Work and primary source | Question, design, domain/data | Comparisons, evidence, metric | Implication for CAISSA-JEPA and source quality |
| --- | --- | --- | --- |
| Silver et al., **AlphaZero** (2017), [original paper](https://arxiv.org/abs/1712.01815) | Can a common policy/value plus search/self-play algorithm master chess, shogi and Go? Separate trained instances per game use search policies and terminal outcomes. | Engine matches and strength versus search time; same broad algorithm across games already predates this project. | Direct policy/value with exact rules is a serious baseline. A shared training algorithm is not shared-weight transfer. Quality: original authors' paper; method/evaluation passages fetched. |
| Schrittwieser et al., **MuZero** (2019/2020), [original paper](https://arxiv.org/abs/1911.08265) | Learn a recurrent hidden dynamics model for reward, policy and value sufficient for planning, without observation reconstruction; board games and Atari. | Search-based performance, compared with AlphaZero and Atari methods. | Action-conditioned latent planning across board games is established. A small surrogate must be called MuZero-style, not a faithful reproduction or a beaten MuZero implementation. Quality: original paper; abstract/method passages fetched. |
| Schwarzer et al., **SPR** (2020/2021), [original paper](https://arxiv.org/abs/2007.05929) | Improve low-data RL with multi-step prediction of EMA target representations and augmentation; Atari100k interactions. | Sample-efficient RL baselines and component ablations; abstract reports improved aggregate human-normalized score. | Multi-step EMA prediction is prior art. Include a recurrent multi-step-trained consistency baseline; one-step-only training followed by unrolling is too weak a substitute. Quality: original paper abstract/version record, not full experimental replication. |
| Ye et al., **EfficientZero** (2021), [original paper](https://arxiv.org/html/2111.00210v2) | Add self-supervised consistency, value-prefix prediction and off-policy correction to MuZero for limited-data Atari. | Atari100k aggregate performance and components; public author implementation. | JEPA-like consistency plus value-driven planning is not a new combination. Our contribution would need to isolate alternating-player/reply-branch effects. Quality: original paper method passages and author code link; visual Atari evidence does not prove board-game gains. |
| Grimm et al., **Value Equivalence Principle** (2020), [original paper](https://arxiv.org/abs/2011.03506) | Models can preserve Bellman updates for selected functions and policies rather than reconstruct every state detail. Formal analysis and illustrative model-learning experiments. | Value-equivalent models versus conventional transition modeling; memory/capacity rationale. | Low latent prediction error alone is insufficient. Measure downstream action regret; retain value-only dynamics and decoded-dynamics controls. A minimax extension needs its own argument, not an automatic transfer of MDP guarantees. Quality: original theoretical paper and derivation context fetched. |
| Lanctot et al., **OpenSpiel** (2019), [paper](https://arxiv.org/abs/1908.09453), [official games](https://openspiel.readthedocs.io/en/stable/games.html), [algorithms](https://openspiel.readthedocs.io/en/stable/algorithms.html) | Common game interfaces, reference rules, minimax/MCTS and game-theoretic evaluation across different game classes. | Official catalog distinguishes deterministic/perfect-information properties and implementation maturity; best-response and NashConv tools exist. | Pin a supported game's rules/configuration for external differential replay when feasible. Local position regret is not exploitability; a best response to a whole policy is needed for that claim. Quality: original framework paper, maintained official documentation and code; no local installation or validation performed here. |
| Titonis, **WorldModel-ConnectX** (author repository, 2026), [repository](https://github.com/alextitonis/WorldModel-ConnectX) | Latent dynamics/value training, exact-rule adversarial search, optional endgame solver, and separate evaluation harness in Connect4. | README reports opponent matches and acknowledges bugs, online adaptation confounds and limits. Results were not independently reproduced in this review. | Direct overlap with our engineering workflow: do not claim first laptop world-model board-game planner, first independent harness, or first exact-search/latent-value combination. Quality: first-party implementation/README, non-peer-reviewed claims; useful novelty warning, not verified performance evidence. |
| Cawley and Talbot, **On Over-fitting in Model Selection and Subsequent Selection Bias in Performance Evaluation** (2010), [JMLR](https://jmlr.org/papers/v11/cawley10a.html) | A finite noisy selection criterion can itself be overfit, not only the training objective. | Analyses and experiments show selection bias can be comparable to algorithm differences. | Repeatedly adjusting the model until one validation win appears is development, not proof. Tune strong baselines too and separate model selection from final estimation. Quality: original peer-reviewed article abstract fetched. |
| Dwork et al., **Generalization in Adaptive Data Analysis and Holdout Reuse** (2015), [NeurIPS paper](https://proceedings.neurips.cc/paper/2015/file/bad5f33780c42f2588878a9d07405083-Paper.pdf) | Reusing holdout feedback adaptively can invalidate ordinary inference; constrained mechanisms such as Thresholdout address this under stated assumptions. | Theoretical guarantees and synthetic demonstration, not a game benchmark. | Do not describe an ordinary repeatedly queried set as a reusable holdout with these guarantees. Our simpler choice is a frozen finite shortlist and untouched final evaluation. Quality: original proceedings PDF; assumptions/introduction fetched. |
| Agarwal et al., **Deep RL at the Edge of the Statistical Precipice** (2021), [original paper](https://arxiv.org/abs/2108.13264) | Few-seed point estimates can produce unstable algorithm rankings. | RL benchmark reanalyses, uncertainty intervals, robust aggregates and performance profiles. | Report seed variability and paired effects; do not count many positions sharing three models as many independent training replicates. Game-balanced reporting prevents a large Reversi pool from dominating. Quality: original paper with public evaluation library; not a guarantee of significance with arbitrary small samples. |

## Prospective CPU-sized experiment

These are recommendations for a separately frozen method, not modifications to
the currently frozen survey. No improvement is promised.

### 1. Make the planner need its learned evaluator

Use the existing rule-only admission predicates: legal action alternatives,
nonterminal depth-two leaves, and different exact action outcomes. Preserve an
additional beyond-depth subset where the zero-leaf depth-two search cannot rank
actions. Freeze this admission rule before scoring any candidate. Publish counts
both for the broad eligible pool and the deliberately difficult subset: inference
from the latter concerns that subset, not average complete-game strength.

For each root, retain the parent trajectory, symmetry orbit, leaf count,
terminal-leaf fraction, legal branching factor, exact-action gap, oracle nodes,
timeouts and exclusion reason. The solver must return unresolved on a budget
failure; missing solutions are never draws. Development feasibility uses the
current 120s/game and 500,000-cache-state limits. Change these only through a
recorded prospective survey amendment.

### 2. Distinguish a distribution problem from an architecture problem

The v1 labels are returns from weak synthetic behavior; they estimate behavior
outcomes, not minimax values. A better model could reduce those losses without
improving worst-case decisions. On tractable development states, compare a common
oracle-labeled training table with a common trajectory-return table, so this
label change is measured separately from the JEPA change. If oracle labels cause
the gain for all methods, credit the teacher/data pipeline.

A reply-fork training unit can contain root s, legal own action a, legal reply b,
and exact two-ply successor T(T(s,a),b). This is simulator-generated branch
supervision, not causal counterfactual estimation from observational data and
not behavioral opponent modeling. If not all branches fit the budget, freeze a
deterministic sampled branch schedule and give that same schedule to every
predictive control. Count the generation cost and all teacher queries.

Every target in a fork needs its own valid utility label or an explicit missing
mask. Reusing the observed parent's trajectory outcome for an unplayed reply is
a label error. For relative-to-player values, one ply changes sign and two plies
restore perspective; forced passes still count as a change of player.

### 3. Candidate and baseline ladder

| Purpose | Required comparison |
| --- | --- |
| Practical reference | Exact-rule search with zero leaf, a fixed disclosed heuristic leaf, and an untrained network; exact solver is an oracle ceiling with separately reported compute. |
| Direct supervised baseline | Same encoder class, state coverage, policy/value labels, optimizer-step schedule and fair learning-rate/capacity tuning; also compare matched wall-time training. |
| Dynamics control | Non-JEPA decoded successor prediction plus the same policy/value losses; a value-only latent dynamics control with identical future-value supervision. |
| Strong consistency prior art control | One-step recurrent predictor trained by backpropagation through the same multiple horizons, EMA/stop-gradient and target normalization as the proposed model. |
| Candidate mechanism | Two-action reply-fork JEPA with the same observed branches. Vary only one prespecified component at a time. |
| Attribution ablations | Trajectory-only versus fork data; both-action versus reply-masked conditioning; auxiliary weight zero; recurrent versus direct two-ply prediction. |

Do not silently replace the baseline encoder with a weaker affine model while
giving JEPA a deeper network. Allocation counts, active parameters, optimizer
steps, examples, evaluated branches and elapsed time answer different fairness
questions and should all be reported. Give direct baselines supervised coverage
of the additional successor states even though they do not need a dynamics loss.

Start with a short finite development grid and a bounded run cap, extending only
after an explicit recorded result and amendment. A reasonable first diagnostic
is three common seeds, two capacities, and a few common learning rates before
mechanism variants. This is a suggestion, not a predeclared experiment count;
the root protocol must freeze the actual list and cap before fitting.

### 4. Separate representation and planner effects

Use one exact-state planner for the primary objective comparison: same legal
tree, move order, depth/node cap, tie break, root schedule and model-call batches;
only the learned evaluator changes. This isolates representation quality. Then
run a separate latent-rollout track that measures drift and practical speed;
its result includes transition approximation error. A faster encoder re-evaluation
may beat predicted latent rollouts on tiny boards, and that is an informative
negative result rather than a reason to handicap direct evaluation.

Report mean exact-action regret and optimal-action rate with counts by game,
seed and structural stratum. Add state-value error and action ranking on the
same oracle labels as explanatory metrics. Current latent loss scales vary with
the learned representation; do not rank candidates by raw latent MSE alone.
Only full matches with fixed role swaps and a predeclared starting distribution
support match win-rate claims. Exact best response to a complete policy, if
tractable, is a different evaluation from local root regret.

### 5. Preserve a credible route from adaptive development to evidence

Training/development may be iterative. Keep every attempted configuration,
failed run, tuning observation and compute total. Before fitting, freeze the
first promotion effect size and the minimum per-game support. Before selection,
freeze a finite candidate shortlist and equally tuned baseline configurations.
Before final evaluation, freeze one candidate, comparators, primary metric,
sample-size rationale, seeds, paired roles, intervals, multiplicity adjustment,
timeouts and stopping rule. Ordinary significance tests on the best result from
an adaptive search do not undo the selection process.

New trajectory seeds are insufficient for an untouched test in a small finite
game: symmetry-equivalent states and all actually encoded branch targets must
remain disjoint. Build a state/target overlap graph and either assign connected
components intact or explicitly quarantine overlaps, publishing the resulting
support loss. If the finite state space cannot support independent splits,
expand the game family/variant prospectively rather than rename reused data.
The previously exposed held-out-size variant is now development evidence.

Use paired differences within a frozen root schedule and uncertainty accounting
for both trajectory/root grouping and training seeds. Do not bootstrap thousands
of root decisions as though they were thousands of independently trained agents.
With only a few seeds, show every seed and describe intervals as exploratory.
A failed locked result stays failed. Further tuning needs fresh independent
confirmation, not removal of inconvenient roots or a new favorable stopping time.

## Novelty and stop conditions

Potential incremental contribution: a carefully controlled study of how reply
coverage and player-perspective-consistent latent prediction affect bounded
minimax planning and transfer across game rules. The candidate can become useful
before it becomes novel; no firstness claim is currently supported.

Do not promote if gains disappear against the strongest tuned direct or
non-JEPA dynamics control, only occur on one convenient seed/game, arise entirely
from extra oracle labels/search, or fail an independent frozen comparison.
If the expanded tiny-game benchmark remains saturated, it supports a scope
change, not a claim that JEPA has matched optimal strategic reasoning in general.
Strong evidence across two tiny families would justify a professor-facing
exploratory proposal; it would still leave larger games, held-out families,
full-match evaluation, mechanism analysis, and publication novelty unresolved.

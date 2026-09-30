# V2.8 candidate experiment: JEPA auxiliary versus direct policy/Q

**Status: design proposal; not frozen; no implementation or experiment yet.**
This note responds to the KLENT prior-art review and is intended to prevent an
unfair comparison that uses only search-heavy baselines. It is not a novelty
claim and does not replace the separate minimax-planning question.

## Question and permitted claim

Primary question: under an identical self-play experience stream, network
capacity, optimizer schedule, training-data access, measured CPU budget and
test-time action-selection budget, does an action-conditioned latent-prediction
auxiliary improve decision performance of a regularized direct policy/Q learner
over that learner without latent prediction?

The direct arm follows the published KLENT equations: a policy and action-value
head; policy improvement by reverse-KL and entropy regularization; and
lambda-return Q targets. The candidate adds an EMA-target JEPA predictor that
forecasts the next state-to-move latent conditioned on the current observation,
the acting player's legal action and the observed next-player reply at the
two-ply horizon. At training, all legal one-ply successors and complete legal
two-ply reply sets may be enumerated from the deterministic rules. The main
candidate must specify whether its two-ply target is sampled from the full
counterfactual set or from the realized trajectory; the former is the current
research choice, conditional on the fairness gate below. The JEPA loss remains
auxiliary; policy and Q targets are shared.

A positive result may support only the tested game variants, opponents, data
budget and inference policy. Against a fixed opponent suite, call the primary
measure opponent-suite score or win rate. This experiment does not establish
worst-case optimality, minimax regret, Nash equilibrium, or exploitability
unless a separate exact small-game analysis actually measures those quantities.

## Candidate components and ablations

1. **KLENT-style direct policy/Q:** clean-room implementation of the paper's
   published update equations; no upstream source code reuse unless a suitable
   code license is later established. Pin equation-level behavior, masks,
   reward perspective, lambda-return convention and temperature before the
   model-blind pilot.
2. **KLENT + one-ply JEPA:** add an EMA target encoder and predict the next
   player-to-move latent from state and own action.
3. **KLENT + two-ply realized-reply JEPA:** include the opponent reply only
   from the observed trajectory. This is a diagnostic, not the principal
   novelty candidate, because multi-agent action-conditioned prediction is
   established prior art.
4. **KLENT + complete legal-reply-set JEPA:** enumerate every legal own-action
   and opponent-reply pair for each admitted root and predict each resulting
   latent. This is the current candidate component, not presumed novel.
5. **Matched task-prediction control:** same predictor topology and target
   exposure, but predict decoded fixed board/rule features or reward/value
   targets instead of EMA latent targets.
6. **Latent-only ablation:** same JEPA target, without any adversarial/minimax
   ranking term. Include a minimax-ranking term only in a distinct worst-case
   track with separate labels, objective and acceptance criteria.

All primary comparison arms receive the same policy/Q training examples and
trajectory identities. Counterfactual enumeration creates extra states and
compute. Give each non-JEPA control the same enumerated state/action exposure
and optimization opportunity; report additional oracle calls, simulator
transitions, gradient updates, CPU wall time and peak memory. A comparison that
matches simulator calls but gives the JEPA arm extra generated labels is not
fair. A comparison that matches examples but hides extra predictor FLOPs is
also not fair.

## Data and split gate

Use project-owned, deterministic rules only. The initial feasible pilot should
use one game family and a second game/variant only after the rules and runtime
gate passes. Self-play populations must include random, tactical, archived
policy and self-play agents; each record carries game version, opponent/source,
seed, player role, terminal outcome and a replayable trajectory hash. No
third-party game records are needed for the pilot.

Split whole games/trajectories before generating sample windows. Keep separate
training, development/model-selection and locked-final groups; group related
positions, role swaps and transformed copies together. The held-out opponent
pool must not appear in training. Locked-final results remain unopened until
model and protocol freeze.

Before fitting any arm, publish a model-blind receipt with (a) legal transition
and terminal differential checks, (b) complete legal-pair counts and target
coverage, (c) root and trajectory leakage checks, (d) class/outcome and phase
counts, (e) candidate runtime/memory per root and per update, (f) expected
training wall time within the free local CPU budget, and (g) a model-blind
simulation-based power check on the locked evaluation schedule design. Do not
remove roots because an exact solver times out. If the JEPA arm cannot fit in
the measured budget, first narrow the candidate or game size; do not omit its
compute cost.

No production training before the audit passes. No paid GPU/cloud run is in
scope. Existing V2.7 receipts are engineering feasibility only and are not
training samples, outcome evidence, or fresh confirmatory positions.

## Evaluation protocol

Primary development estimand: paired score difference of JEPA-augmented
policy/Q versus KLENT-style direct policy/Q over the predeclared opponent suite,
with role/color swaps paired within situation and seed. Choose the smallest
meaningful effect and sample size from a model-blind power simulation before
opening development outcomes. Report all opponent strata separately and as a
preweighted macro-average; report game-family results separately. Do not pool
duplicate seat-swapped trajectories as independent games.

Training efficiency curves use multiple cost axes: number of environment
transitions, optimizer updates, measured CPU wall time, estimated operations or
profiler-accounted model compute, and memory. The paper's simulator-call ratio
is contextual prior art only. For each cost axis, report performance-vs-cost
area under the learning curve with seed-level intervals. Report policy all-
legal NLL/MRR, Q error, calibration where defined, latent prediction error,
effective rank/collapse diagnostics and per-game/phase strata as secondary
mechanistic metrics. Lower latent prediction error is not itself a success.

If learned policies are combined with search, define that as an additional
system track. Every arm receives identical legal rules, search algorithm,
node/time budget, action schedule, and reference opponents; inference cost is
included. The direct no-search KLENT replication and search-augmented agents
must be reported separately.

## Kill and pivot criteria

- **Fidelity failure:** if the clean-room direct policy/Q learner fails
  synthetic normal-form/finite-game checks or cannot reproduce key qualitative
  KLENT behaviors under a tractable local adaptation, pause comparisons and
  repair or omit it with a stated limitation.
- **No signal / ceiling:** if development opponents or game size yield
  saturated scores, redesign the model-blind benchmark before fitting. Do not
  change the locked set after seeing candidate results.
- **No incremental JEPA effect:** if the candidate is not better than both
  KLENT-style direct policy/Q and matched task-prediction at equal measured
  budget, do not promote a JEPA-superiority claim. Record the null/negative
  result and test at most a predeclared small set of training-only changes.
- **Compute-only illusion:** if an apparent improvement exists only on
  simulator calls, but not measured CPU/model compute, narrow the claim to
  sample efficiency and report the tradeoff; do not claim overall efficiency.
- **Method overlap:** if prior art or independent review finds the full
  objective equivalent to existing counterfactual, minimax-Q or consistency
  learning, pivot to a benchmark/replication contribution unless a measurable
  advantage survives a stronger control.
- **Cross-game claim:** if only one game passes the data/runtime and power gates,
  label the result single-game and defer transfer; do not generalize across the
  whole game class.

## Current gates and reproducibility

| Gate | Acceptance evidence | Status |
| --- | --- | --- |
| KLENT source audit | Full paper, official code presence, license state, objective and budget extracted | PASS for paper; upstream code license not established, no code fetched or used |
| Objective distinction | Independent method review explains which outcome is policy behavior and which is minimax; no conflation | OPEN |
| Clean-room baseline spec | Equations, perspective, legal-action masks, lambda targets, seed/config and synthetic checks frozen | K0.1 equations, masked targets, signed returns, separate policy/Q heads, finite-difference gradients and self-play collection are implemented. Independent review findings are repaired; corrected post-commit three-seed synthetic diagnostic and 346-test full regression pass. This remains engineering fidelity only. |
| Model-blind data/compute gate | Game rules, trajectory split, complete reply coverage, legal replay, runtime and power receipt pass | NOT STARTED |
| Development pilot | Multiple seeds, append-only config/data/checkpoint hashes; all controls and failures retained | NOT STARTED |
| Locked confirmation | Preregistered sample, primary metric, multiplicity, timeout policy and independent review | CLOSED |

All future receipts must record source commit, source/config hash, dataset
fingerprint, checkpoint hashes, seed, sample/skip counts, cost counters and
uncertainty. The first post-commit synthetic receipt is retained at
`docs/validation/V28_KLENT_COUNTUP_01.json`, but its policy TV/Brier metrics are
for the one-step improvement target \(\pi'\), not learned \(\pi_\theta\). The
corrected follow-up reports both metrics separately. Learned-policy TV is
0.0195–0.0284; improvement-target TV is 0.0161–0.0203. Its target is exact
backward-induction quantal response in one seven-state game; neither receipt
establishes board-game strength, transfer, JEPA benefit, or KLENT reproduction.
Raw per-state output is excluded under `chess_data/`. Independent fidelity
review is complete with fixes applied; the model-blind data/compute gate remains
pending before JEPA training.

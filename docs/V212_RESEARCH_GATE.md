# V2.12 Research Gate: Multi-step Alternating-Player JEPA

## Current checkpoint (2026-10-03)

The v04 method review permitted only a random-initialized, no-training
instrumentation pilot. Pilot v01 completed 96/96 variant/root/arm cells to
depth four under the declared safety ceilings. Overall wall-time p90 was
0.2689 s and maximum was 0.9901 s; no score, selected action, or outcome was
recorded. The independent `gpt-6-luna/high` review found no blocker to the
next no-training protocol-review step. This small sample does not set a common
search budget or establish fitted-model compute or playing strength.

The amended 1,152-cell v02 sampling plan and its no-training runner are frozen
in `docs/V212_COMPUTE_PILOT_V02.md` after independent protocol and implementation
review. The schedule uses one unique board at ply zero and five roots at each
later ply. The pilot completed 1,152/1,152 cells to depth four; 12 exceeded
2 seconds, and the maximum was 3.7419 seconds. Its receipt and report passed
independent review. Candidate `docs/V212_COMPUTE_BUDGET_AMENDMENT_05.md`
proposes a common 10,000-node/5-second planner cap, 6-second response deadline,
and 25% pragmatic reserve. The proposal passed independent review but is not
an operational cap; request-to-search headroom and implementation must pass
separate pre-fit verification. Do not open training/outcome data, fit, or play
matches; novelty, trajectory/replay, leakage, and separate pre-fit gates
remain closed.

Status: candidate research direction only. Not an implementation spec, training
grant, frozen protocol, or novelty claim. No V2.12 fit is authorized by this
note.

## Evidence motivating the question

The independently audited V2.11 λ=8 model failed its predeclared nomination
screen. Macro paired scores were −0.04375 vs reply-JEPA λ=1, −0.0500 vs
task-value dynamics, and −0.0375 vs direct-leaf. The compute screens passed,
so the result is not explained by extra search. It argues against simply
increasing the coefficient on the existing all-legal two-ply latent target.

The current model receives a state representation and a pair of actions
(current player, opponent response), then predicts the leaf representation.
This is a useful two-ply conditional prediction, but the deployed planner
evaluates only one such pair before choosing again from the observed state.
It does not test whether a latent predictor can be recursively rolled out over
multiple alternating decisions. A September 2026 preprint argues that
one-step next-latent regression generally learns a conditional mean rather than
a roll-outable transition kernel, and demonstrates that multi-step error may
grow even when one-step error is low ([Wang et al., 2026](https://arxiv.org/abs/2609.36227)).
Multi-step JEPA world models and learned-model game planning are established
prior art; any CAISSA contribution would need to come from a rigorously tested
game-theoretic setting and incremental evidence, not from naming the recipe.

## Falsifiable candidate hypothesis

At a fixed number of simulated nodes and a fixed inference/training compute
budget, a JEPA predictor trained on sequential alternating-player latent
rollouts will produce lower horizon-dependent minimax decision regret and
stronger play than a matched task-value latent dynamics model and a direct
leaf-value model, with the advantage persisting on held-out board-size/game
variants after zero-shot or explicitly budgeted few-shot transfer.

The hypothesis does **not** assume that the model predicts any particular
opponent's behavior. The target planner is finite-horizon worst-case max-min
search for the defined deterministic zero-sum games. It does not estimate a
behavior-policy expectation or guarantee a full-game equilibrium. The
distinctions are:

- A behavioral opponent model estimates actions from a named opponent-policy
  distribution; it is evaluated by calibrated action likelihood and
  policy-conditional outcomes.
- The V2.12 candidate would predict state latents conditional on the actions
  supplied for both alternating roles; it makes no behavioral prediction.
- The planner would choose max-min over legal action sequences to a fixed
  horizon, with a pinned leaf evaluator. This is neither a learned opponent
  response distribution nor an equilibrium solver for the full game.
- A policy-mixture expected-value planner would require a separately
  calibrated opponent distribution and is outside this candidate.

## Candidate model family to investigate

Represent state as (s_t), side to move as (p_t\in\{-1,+1\}), legal actions
as (A(s_t)), and exact deterministic transition as
(s_{t+1}=T(s_t,a_t)). An online encoder (z_t=f_\theta(s_t,p_t,g)) receives
the state, role, and compact game descriptor (g); an EMA target encoder
produces (z^*_t=f_{\bar\theta}(s_t,p_t,g)). A shared transition predictor
receives ((z_t,a_t,p_t,g)) and predicts (hat z_{t+1}=F_\phi(z_t,a_t,p_t,g)).
For a legal action sequence (a_{t:t+K-1}), recursively predict
(hat z_{t+k}) without re-encoding intermediate states. The exact engine is
still used to generate legal actions and audit the trajectory.

Candidate objective, subject to prior-art and leakage review:

\[
\mathcal L_{\mathrm{roll}}=\sum_{k\in\mathcal H}\alpha_k\,m_k\,
\ell(\hat z_{t+k},\operatorname{sg}(z^*_{t+k}))
 +\lambda_{\mathrm{task}}\mathcal L_{\mathrm{root/task}}
 +\lambda_{\mathrm{reg}}\mathcal L_{\mathrm{anti-collapse}}.
\]

Here \,\(\mathcal H\) must include more than one horizon, masks (m_k) exclude
sequences that encounter terminal states before (k), and terminal payoffs are
handled exactly. Candidate rollout lengths should be in *individual plies* so
the alternating role is explicit; report horizons in both plies and full
player-response pairs. EMA, loss scale, horizon weights, sequences, seeds,
optimizer, target normalization, and termination masks must be frozen before
any candidate fit. The exact values cannot be selected after seeing strength
outcomes.

The first design question is whether to predict every sequence's target latent
with a uniform action-pair distribution or use a frozen proposal distribution
for legal counterfactual action sequences. The latter risks collapsing into
known value-aligned or policy-aware model fitting. Do not add regret weighting
unless a separate primary-source comparison demonstrates a precise gap and a
train-only, non-tautological definition.

## Required controls and evaluation before a fit

1. Keep the current single two-ply reply-JEPA as the JEPA ablation.
2. Add an architecture/compute-matched non-JEPA multi-step latent dynamics
   control trained on decision targets, with identical sequences, horizon,
   EMA/regularization where applicable, and update count.
3. Keep task-value dynamics and direct-leaf controls. If a suitable independent
   engine/teacher is legally and technically available, pin its version/hash;
   otherwise use a transparent exact-search reference in small games and do
   not imply expert strength.
4. Same-search comparisons must share the exact state rules, legal-action
   handling, node budget, tie-breaking, situations, seat swaps, seeds, runtime,
   and termination policy. Report realized neural calls, transitions, CPU and
   wall time separately.
5. Representation evaluation must include one-step and open-loop latent
   errors at each horizon, covariance/effective rank, finite-value rates,
   predicted-versus-true minimax action ranking, worst-case value error, and
   action regret against an exact or explicitly bounded search oracle.
6. Strength evaluation needs paired outcomes against every control, self-play,
   random, tactical, and bounded-search opponents; enough held-out start
   situations; and at least one held-out board-size/game variant. Exact full
   game theoretical value/exploitability should be reported only where it can
   actually be computed.
7. Predeclare a primary metric and practical margin, power/sample rationale,
   seed and color schedule, confidence method, multiplicity handling,
   censoring/timeout rules, and stopping rule. Keep exploration, selection, and
   locked confirmation separate.

## Data, access and license

The initial investigation can use project-owned exact board-game code and
newly generated self-play from that code; no third-party data are needed. Keep
all generated records, fit artifacts and checkpoints under ignored
`chess_data/`. Bind each run to rules/source/dataset fingerprints, parser
version, split, seeds, and exact generation policy. Do not start a production
fit until the counterfactual rollout generator passes duplicate, illegal
transition, terminal-mask, episode/split leakage, and hash audits. No paid
compute or external service is allowed without separate authorization.

## Novelty and stop decision

This direction is not yet shown to be novel. Existing work includes I-JEPA and
V-JEPA 2, multi-step JEPA-WM studies, MuZero/AlphaZero, value-aligned world
models, policy-aware simulator learning formulated as minimax, and recent
next-latent critiques. The related-work matrix is in `docs/RELATED_WORK.md`.
The September 2026 Semigroup-JEPA preprint directly demonstrates recursive
multi-step latent rollout training that updates the encoder, although in
gravity-conditioned physical systems rather than alternating legal game
transitions. Therefore neither recursive JEPA training nor improved open-loop
prediction can serve as the method novelty by itself. A defensible increment
would have to survive matched recurrent-JEPA and decision-aware non-JEPA
controls and improve predeclared minimax decision measures under equal
measured compute. Action-Conditioned Predictive Consistency is adjacent prior
art for evaluating paired rollouts and downstream plan-cost stability, but its
planning-cost bound assumes squared distance to a fixed goal embedding and its
experiments use CEM in visual-control tasks; it does not guarantee minimax
value or action-ranking stability for V2.12. Its visual-perturbation setting
also does not directly apply to exact symbolic game states. Full source notes
and scope limits are in `docs/RELATED_WORK.md`.
Before implementation, write a complete method specification that explains
exactly what differs from each closest work. Kill or reframe the algorithmic
claim if the method is simply standard multi-step JEPA-WM plus a minimax
planner, if the baseline can match it with a task-value loss, if any apparent
gain comes from extra compute, or if it fails the predeclared held-out variant
and all-control margins. A carefully controlled benchmark/negative result
may remain useful, but is not a substitute for a demonstrated JEPA benefit.

## Acceptance status

V2.12 is **not ready for coding, training, or a professor-facing superiority
claim**. Next permitted internal work is a no-training audit of current adapter
capacity, candidate multistep data generation, prior-art definitions, and
resource requirements; then the exact method/protocol can be frozen and
independently reviewed before any fit.


## 2026-10-03 action-sensitive world-model literature refresh

A targeted primary-source audit added AD-WM (Qiu et al., arXiv:2609.30264v2)
and ActSWM (Gan et al., arXiv:2607.26712v2) to
`docs/RELATED_WORK.md`. AD-WM trains observed one-step latent transitions
with action-recovery objectives, then evaluates candidate counterfactuals
through CEM and shared-sequence elite-regret diagnostics. ActSWM directly
combines multi-step JEPA rollouts, an action-contrastive recorded-versus-zero
rollout loss, and a frozen action readout, with Minecraft planning and offline
action-recovery evaluations. Both are arXiv preprints; the reported results
were not independently reproduced here. Their continuous/open-world control
settings are materially different from exact-rule adversarial board games,
but they eliminate action sensitivity, counterfactual planning comparison,
and multi-step action-aware JEPA as standalone novelty claims.

This changes the pre-fit comparison requirement. The remaining plausible
increment is an empirical result about finite-horizon, exact-rule, alternating
zero-sum max-min decisions under matched compute. METHOD_SPEC_V212-04 currently
supervises only recorded trajectory branches and contains no counterfactual
branch training term; its support-count draft does not show that a latent
predictor ranks every legal alternative correctly. Before any fit or model
scoring, a new reviewed protocol version must decide whether to add a
compute-matched action-sensitive JEPA control, define full legal-root action
scores with exact/bounded-search reference values and bound provenance, and
predeclare decision-regret metrics on fixed reachable roots. Any branch
contrast must use legal game actions rather than importing ActSWM's all-zero
action contrast. Do not retrofit these changes into reviewed v04 or use
unreviewed outcomes to select them. Status remains no training, no matches,
and no superiority/novelty claim.


## 2026-10-04 interval-valued minimax-reference option

An alternative to a point-valued bounded reference is sound interval search:
initialize unexpanded nonterminal leaves to the valid W/D/L range `[-1,+1]`,
propagate lower/upper values through exact-rule MAX/MIN nodes, and report a
per-root regret interval. Zero-width intervals are point identified; unresolved
width is retained, not replaced by a midpoint. This avoids choosing/reusing a
policy-aligned scalar heuristic but may provide little decision resolution
under the available compute cap. A primary optimistic-minimax paper provides
a general interval-bound search precedent; it does not validate the proposed
CAISSA recursion, cap, or Reversi pass handling. Independent review found no
blocker in the derivation, subject to representing all omitted legal children
as unresolved intervals. No gate changes and no scoring is authorized. See
`docs/V212_COUNTERFACTUAL_DECISION_REGRET_DESIGN_01_DRAFT.md`.

### 2026-10-04 tiny-game interval verifier

An isolated deterministic-DFS candidate and focused tests now exist in
`two_player/v212_minimax_bounds_v01.py` and
`tests/test_v212_minimax_bounds_v01.py`. Tests passed for every integer
expansion budget on a late Tic-Tac-Toe fixture, including containment of exact
root/action values and executed-action regret, monotone narrowing, and collapse
at full resolution. A Reversi4 forced-pass fixture confirmed pass accounting;
zero-budget search retained every legal root action as unresolved. These checks
validate the tiny-fixture recurrence and implementation only. The DFS budget
counts expanded descendants rather than transitions, and is not frozen; cap
feasibility remains open, and the interval reference is not adopted. Independent
code review confirmed the recurrence and led to rejecting Boolean action IDs,
now regression-tested. The focused suite passes. The repository-wide suite ran
621 tests but ended with 24 environment/platform/data errors and 11 skips. No
roots, models, scores, or gates changed.

### 2026-10-04 hard-transition-cap minimax interval probe

Two additional isolated search orders now enforce a hard rule-transition
budget: DFS with atomic full-successor expansion, and even allocation across
root actions. Ten tiny-game tests pass, including exact containment,
forced-pass, monotonicity and cap accounting. A reproducible single-run
synthetic profile over only the standard opening state of Connect Four 6x7 and
Reversi6 found that root/action value intervals all retained full width 2 and
identified 0% of root actions through 65,536 transitions. At that cap the
observed single-run times were 11.345 s and 4.107 s, respectively. This is
negative evidence about these naive no-heuristic DFS orders on two opening
states, not a representative feasibility estimate or model pilot. Do not adopt
them or use this profile to change inference caps; a sound selective/best-first
reference or another prespecified estimand is still needed. No gate changed.
The search used exact terminal checks on descendants of the two synthetic
initial states; it accessed no training labels, benchmark root schedule,
model outputs, or empirical game results.

## 2026-10-04 source-code amendment proposal

The legacy V2.8 `_line_score` is used by both the positional policy and the
bounded-search data-generation policy, so its reuse as an evaluation
reference risks aligning the benchmark with its own source policies. Keep it
out of the reference absent an explicit policy-aligned estimand. For primary
executed-action regret, a complete exact fixed-horizon root maximum plus an
independent full-window query for the arm's selected action is sufficient;
an exact full-window Q table for all legal actions is needed only for the
separate action-ranking diagnostic. The proposed query optimization keeps the
complete legal-action root set and does not make a bounded reference
game-theoretic ground truth. Independent review found no blocker in this draft
amendment; it still needs a pinned evaluator/depth, compute allocation, and
adapter tests against tiny exhaustive games before protocol freeze. This
proposal changes no gate and authorizes no scoring. See
`docs/V212_COUNTERFACTUAL_DECISION_REGRET_DESIGN_01_DRAFT.md`.

## 2026-10-03 bounded-reference decision-regret design proposal

Source audit of the published compute-only runner found that
run_root_arm carries an incumbent root alpha across root actions, uses its
temporary values only to choose a move, then discards them. Later fail-low
returns may be upper bounds, not exact action values. The frozen v02 receipt
records no actions or values, so it cannot support a retrospective regret
calculation. A new design-only proposal,
docs/V212_COUNTERFACTUAL_DECISION_REGRET_DESIGN_01_DRAFT.md, defines
per-action full-window scores, a bounded-reference regret estimand, exact vs
bounded reference strata, all-legal-action completeness, and fail-closed
missing/bound handling. It explicitly keeps reference values evaluation-only
and does not assign a reference depth or heuristic.

This proposal is not frozen or independently reviewed and changes no gate.
Before model scoring, the reference heuristic/depth, diagnostic compute
allocation, root/seat weighting, tie metric, and relationship to the primary
match metric still require decision and review. No scores were extracted from
the pilot receipt, no code was changed, and no data/model/pilot was run.


## Exact-regret implementation precedent and oracle gap (2026-10-03)

A source audit identified an older, explicit exact-regret path in
two_player/evaluate.py and two_player/games.py. It scores all legal root
actions with a two-ply max-min planner, separately solves terminal outcomes
with exact_value, and sets regret only for a complete planner result. The
registered games are tiny (tic-tac-toe, 4x4 connect3, 4x4 reversi, and 3x4
connect3); exact_value is unbudgeted and its docstring requires restricting
state-space size. This establishes a usable software precedent for complete
action denominators and status-gated regret on small games, not an oracle for
the V2.12 Connect Four 6x7/8x8 and Reversi6/8 variants.

The inspected V2.12 runner uses those four larger variant configurations,
returns no root-action values, and has no separate nonterminal bounded
reference evaluator. METHOD_SPEC_V212-04 requires a pinned internal heuristic
for any larger bounded-depth reference, but no such function/config has been
selected in the inspected source. The next protocol decision must therefore
keep exact full-game regret limited to a predeclared tractable-position stratum
and specify a separate, fixed bounded reference for any larger-variant
decision-regret claim. Do not run the unbudgeted exact solver on large games
or silently substitute the legacy toy-game variants. This remains an
unreviewed design gap; no model score, data, or pilot was produced.


## V2.12 generation compatibility audit (2026-10-03)

A static read of V2.8 source blob
b252c703004f42af1574868e9d8c3fdd9a4b4f02 confirmed that it supports the
V2.12 training-size game rules and replayable terminal episodes, but is not a
compatible V2.12 corpus generator: train/validation policy assignment is
limited to two opposite uniform/tactical pairs instead of the required 16
ordered pairs; split-specific selection/locked policies differ; and its record
materializer applies V2.8 phase/dedup rules and emits H1/H2 rather than V2.12
H0-H4 windows with H1/H2/H4 targets. The V2.12 auditor only accepts episodes
in memory and explicitly is not a generator. Evidence and function-level
dispositions are in
docs/V212_GENERATION_PROTOCOL_COMPATIBILITY_AUDIT_01.md.

This proves an implementation incompatibility, not a data/leakage result or
928-window feasibility failure. A separately reviewed V2.12 generator and
manifest are required. No data or outcomes were inspected/generated, and
generation, fitting, scoring, and matches remain gated.


## V2.12 behavior-policy provenance audit (2026-10-03)

The compatibility audit now records each V2.8 behavior policy's actual source
semantics and the generation RNG boundary. The 192-node depth-four
bounded-search family may stop before all legal root actions are scored and
uses its own handcrafted positional leaf score. It is a data-generating
policy, not expert supervision or the game-theoretic reference. V2.8 also
derives policy pairs from split/episode parity and uses a single action RNG
stream; V2.12 requires an independently frozen draw over all 16 ordered pairs
and a pinned RNG/seed derivation. A V2.12 manifest must bind code/config hashes,
legal-action order, cap/depth, tie behavior, and RNG policy before generation.
No policy was executed and no data were generated.

## Exact reference source candidate (2026-10-03)

A read-only audit of Markus Thill's [MIT-licensed Connect-Four framework](https://github.com/MarkusThill/Connect-Four)
at pinned commit [`2a58844594ac022846385dd3ddc8bbbf0a26eae5`](https://github.com/MarkusThill/Connect-Four/tree/2a58844594ac022846385dd3ddc8bbbf0a26eae5)
identified a candidate for exact full-game action values on the V2.12
Connect Four 6x7 training variant only. The README claims exact state and
action values; inspected `AlphaBetaAgent.getNextVTable` enumerates legal
columns and invokes `rootNode(true)` separately after each move with a fresh
full window. Its 100-ply default search horizon exceeds the 42-cell board, and
passing `books=null` disables the opening-book paths. The fixed board
implementation is explicitly 7 columns by 6 rows. These facts make it a
promising source candidate, not a verified oracle. No code was executed and
no value was queried.

The 8x8 Connect Four and Reversi variants remain uncovered. Player-1 sign,
win-distance scoring, valid-turn assumptions, terminal handling, complete
legal-action coverage, code correctness, licensing/provenance, and resource
bounds still need independent adapter review and contract validation before
any evaluation use. Do not treat this as closing the overall oracle gap; it
does not change any scoring, generation, or training gate. See the detailed
[decision-regret design](V212_COUNTERFACTUAL_DECISION_REGRET_DESIGN_01_DRAFT.md).

## Exact Connect Four oracle source audit (2026-10-03)

A second primary-source pass identified a stronger interface candidate for
only the V2.12 Connect Four 6x7 training variant. The MIT-licensed Rust
repository [benjaminrall/connect-four-ai](https://github.com/benjaminrall/connect-four-ai),
pinned here to `28a112adaf3ff89ee23fb09411fa592b6597010e`, exposes
`Solver::get_all_move_scores`. Source says this returns an exact
side-to-move remoteness score for every playable column and `None` for full
columns; it assumes the position is valid and nonterminal. This is a better
API candidate than the previously recorded Thill Java framework, not a
validated oracle. The upstream's own no-book `begin-hard` benchmark reports
5.09 s average for that test set; it is author evidence on a different
machine/task, not an estimate for our roots. The call has no deadline, and
its internal positions are not commensurate with the V2.12 10,000-node cap.

The score sign is relative to the side to move and the magnitude encodes
remoteness. Before use, freeze conversion to root-player utility, including
whether the primary regret uses W/D/L only and remoteness is secondary. Review
reachable-history conversion, legal-column bijection, terminal exclusion,
all-action completeness, output status, dependencies/license provenance, and
an external hard process deadline. Keep any reference-evaluation compute
allocation separate from the planner's 5-second proposal. No engine was
installed/run and no positions or scores were queried.

Pascal Pons's AGPL-3.0-or-later solver also has an exact all-action
`analyze` API; its license requires separate review before integration. A
2025 preprint reports a strongly solved 7x6 W/D/L table requiring 89.6 GB and
128 GB RAM at generation, with 47 hours on one CPU core. Neither source
extends to 8x8 Connect Four or Reversi. The BDD artifact repository had no
license file in the inspected tree. These sources narrow the candidate-source
gap only; exact-oracle integration, bounded-reference design for the other
variants, scoring, generation, and fitting remain gated.


## Reversi8 weak-solution scope check (2026-10-03)

Takizawa's primary-source paper reports standard 8x8 Othello weakly solved as
a draw from the initial position, with a strategy guaranteeing at least that
result ([arXiv:2310.19387v3](https://arxiv.org/pdf/2310.19387)). It does not
strongly solve arbitrary positions or publish complete action values for
arbitrary roots; the author states the proposed semi-strong all-position
challenge remains future work. This narrows Reversi8's theoretical opening
status but does not close V2.12's per-root, all-legal-action regret oracle
gap. The paper's modified Edax source is GPL-3.0 and its raw outputs are
separate artifacts; neither was downloaded, run, or integrated. Source
inspection suggests our 8x8 opening/pass/flip/terminal rules match standard
Othello, but adapter equivalence and any license/provenance review remain
required. No method, outcome, scoring, or generation gate changes.


## Reversi6 semi-strong tablebase lead (2026-10-04)

Takizawa's primary v2 paper and Zenodo release describe an exact score-value
artifact for a certified region `R` of 6x6 Othello, not a strong solve over
all reachable states. A certified free-agent decision node for a declared
orientation covers all legal successors; an optimal-agent node for that
orientation only certifies the canonical optimal continuation. Thus the
artifact may support a complete exact W/D/L action
stratum only for prehashed roots in the orientation-specific region `R_P`,
where the side to move is the free agent under that same orientation and
every child query is covered; union-only membership is insufficient. Its
terminal score-margin utility
can be mapped to CAISSA's winner/draw value by sign, because monotone sign
preserves max/min; negate each child value to convert to root perspective.
This is a derivation, not a tested adapter. The release is
138.4 GB and its Zenodo rights/license field is blank in the inspected
snapshot. No download or query was attempted. Full scope, query, proof,
license, storage, and coverage review remains required; it does not replace
the bounded references needed for other variants or uncertified roots. See
`docs/V212_COUNTERFACTUAL_DECISION_REGRET_DESIGN_01_DRAFT.md` and
`docs/RELATED_WORK.md`. No gate changes.


## Decision-metric alignment prior-art update (2026-10-03)

Wang et al. (arXiv:2608.18746v1) introduce Plan-Real and CEM-stage Spearman
for ranking candidate plans by latent cost versus environment cost, and
DA-LeWM adds inverse-action and demonstration-conditioned goal-action losses
to an action-conditioned JEPA-style world model. This closes standalone
novelty claims for action-conditioned JEPA planning, inverse-action auxiliary
losses, goal-action supervision, and generic planner-rank diagnostics. Their
evidence is single-agent Euclidean-goal CEM on four robotics tasks, not
two-player zero-sum max/min over complete legal-action sets. A potentially
distinct CAISSA question remains empirical and unverified: root-player
decision regret/ranking under finite-horizon adversarial backup at matched
compute. Even there, adaptation of the DA-LeWM inverse-action control needs
independent review before fitting; a logged future-action target could
measure behavior imitation rather than decision quality.

The paper reports that CEM-stage Spearman is near zero or negative at the
elite stage for all compared variants, including DA-LeWM, despite positive
random-stage lift. This is a useful negative precedent: aggregate/global
ranking does not guarantee ranking among optimizer-selected candidates. Its
authors report one training run per configuration and three evaluation seeds,
so training-seed uncertainty is not established. The paper is a preprint and
was not independently reproduced. No CAISSA method, data, scoring, or training
gate changes; novelty remains high-risk and all outcome gates stay closed.


## Candidate inverse-action control after DA-LeWM (2026-10-03)

The current v04 model is already action-conditioned in its predictor and
behavior-supervised at the root. DA-LeWM adds inverse-action prediction from
consecutive latents, a distinct auxiliary that could alter representation
geometry. A separate
[design draft](V212_INVERSE_ACTION_CONTROL_DESIGN_01_DRAFT.md) proposes a
six-arm-by-two-level factorial to test this factor without treating logged
future actions as optimal labels. It is a proposal only, not a v04 amendment.
Reviewers must decide whether its cost, estimand, loss weight, initialization,
compute parity, and multiplicity are acceptable before any future fit.
No goal-action imitation head is presumed appropriate for adversarial
decision quality. No data, training, scoring, or match gate changes.


## Learned-model game-planning prior art: LAMIR (2026-10-03)

Kubíček and Lisý's ICLR 2026 LAMIR paper demonstrates learned latent
dynamics, legal-action prediction, recurrent trajectory supervision, and
test-time depth-limited reasoning in two-player zero-sum imperfect-information
games. It also notes that sequential games can be represented as simultaneous
games using fictitious non-acting-player actions. This closes broad novelty
claims for “learned game model plus look-ahead” and for alternating/zero-sum
game domain alone. LAMIR is MuZero-inspired rather than JEPA, models
information sets and a learned abstraction, and uses CFR+ reasoning; it does
not test CAISSA's deterministic fully observed exact-rule board-game setup or
its proposed JEPA-versus-matched-control decision-regret question.

The distinction is a candidate empirical comparison, not a novelty finding.
Published LAMIR results (lower exploitability than concurrent RNaD in small
games; up to 80% head-to-head in large games) are author-reported and were not
reproduced here. V2.12 still uses a finite-horizon max/min heuristic, not an
equilibrium solver. No method, implementation, gate, data, training, scoring,
or outcome status changes. Prior-art source:
[arXiv:2510.05048](https://arxiv.org/abs/2510.05048).


## Executable code world models in general games (2026-10-03)

The ICLR 2026 paper *Code World Models for General Game Playing* uses an LLM
to synthesize executable rule-transition/legal-action code from game rules
and sampled trajectories, then plans with MCTS/ISMCTS. Its ten-game suite
includes Connect Four and four paper-created games; the reported comparison
matches or beats Gemini 2.5 Pro on nine of ten games. This reinforces that
game-model-plus-search and game generality are not sufficient novelty claims.
The method is code synthesis, not a learned JEPA latent predictor, and its
comparison is not a matched latent-dynamics control. Passing trajectory-based
tests does not establish correctness on unsampled states. No CAISSA gate or
claim status changes. Sources: [ICLR proceedings](https://proceedings.iclr.cc/paper_files/paper/2026/hash/d8a12fde9e72444e1b356e8c37e53753-Abstract-Conference.html)
and [arXiv:2510.04542](https://arxiv.org/abs/2510.04542).


## Root-sampling inference source audit (2026-10-03)

A source-level audit recorded in
[docs/V212_ROOT_SAMPLING_INFERENCE_AUDIT_01_DRAFT.md](V212_ROOT_SAMPLING_INFERENCE_AUDIT_01_DRAFT.md)
finds that the cited crossed-bootstrap paper establishes mean consistency in
its crossed random-effects setting, while the multiway-clustering paper gives
asymptotic conditions for specific regression variance estimators. Survey
resampling and few-treated-cluster work are methodological analogies, not
coverage guarantees for V2.12's 20 seeds × 16 slots per occupancy stratum,
max-|T| intervals, and Holm-adjusted tests. This is an unresolved validation
requirement, not evidence of invalidity. Independent statistical review must
decide whether a design-matched synthetic coverage/power study is required
and predeclare scenarios and acceptance criteria. No root generation,
scoring, training, or gate transition is authorized.


A follow-on primary-source check found Owen and Eckles's multifactor product
reweighting method as a candidate variance-estimation comparison; its results
concern the mean under crossed random-effects conditions and do not establish
the proposed confidence/test family. A 2026 proportional random-effect block
bootstrap studies nested clustered mixed models, not the seed-by-root crossing,
so it is not a drop-in substitute. These are reviewer options only. The
source scope and required method disposition are in
docs/V212_ROOT_SAMPLING_INFERENCE_AUDIT_01_DRAFT.md; gates remain closed.


### 2026-10-03 null-versus-effects inference evidence

Bakshy and Eckles report that A/A checks address a sharp-null setting and do
not expose every failure under heterogeneous effects; in their user–item
simulations, one-way bootstrap coverage degrades under treatment interactions,
while their multiway method is mildly conservative in the studied scenarios.
This is contextual evidence only, not validation of CAISSA's seed × root,
max-|T|/Holm procedure. If a design-matched simulation is required, its frozen
scenarios should include both null and heterogeneous/nonzero-effect cases;
independent statistical review must decide and predeclare criteria. The
source's withdrawn Section 3.4/Figure 4 imbalance result is excluded. No
simulation, roots, outcomes, training, or gate transition occurred. See
docs/V212_ROOT_SAMPLING_INFERENCE_AUDIT_01_DRAFT.md.


### 2026-10-03 few-factor inference scope check

A primary-source review of multiway wild-cluster methods and cluster-robust
practice confirms that small cluster counts complicate inference and that
regression-based alternatives depend on a specified score/variance model and
bootstrap-cluster choice. The literature does not directly validate the
proposed 20-seed × 16-root-slot, stratified paired bootstrap or its
max-|T|/Holm family. Independent statistical review should disposition the
per-stratum factor counts and determine whether a design-matched study should
compare methods while preserving paired arms, fixed stratum weights, and the
15-contrast family. No method choice or gate transition follows; no roots,
simulation, outcomes, or training occurred. Scope details:
docs/V212_ROOT_SAMPLING_INFERENCE_AUDIT_01_DRAFT.md.


### 2026-10-03 crossed mixed-model comparator scan

Crossed subject/item mixed-effects models provide a closer structural analogy
for seed × root sampling than nested-cluster models. Kenward–Roger offers a
small-sample adjustment for fixed-effect inference in Gaussian mixed models.
Neither source validates CAISSA's paired game-score estimand or its 15-contrast
family. A model-based comparator would require a new reviewed specification
for outcome likelihood, crossed arm-specific slopes, fixed stratum weights,
missing cells, boundary behavior, and simultaneous inference. Independent
review may decide whether to compare it in a predeclared synthetic study;
there is no model selection or simulation authorization here. Gate remains
unchanged. Details:
docs/V212_ROOT_SAMPLING_INFERENCE_AUDIT_01_DRAFT.md.


### 2026-10-03 crossed interaction-component bootstrap check

Owen and Eckles's product-factor bootstrap targets variance of a mean. Under
their two-factor model, an interaction-only component is inflated by roughly
3×; their near-correct result relies on main-effect components dominating
under stated conditions. For the proposed complete 20 × 16 grid per occupancy
stratum, the design's duplication ratios are each 1/16, but this does not
verify the variance-component conditions or finite-sample calibration.
Independent review should decide whether any required synthetic study includes
main-effect- and seed × root-interaction-dominated regimes, under null and
nonzero heterogeneous effects, and evaluates the whole familywise procedure.
No variance components are known; no simulation, roots, outcomes, or training
occurred. This refines the validation question only; the gate remains closed.
See docs/V212_ROOT_SAMPLING_INFERENCE_AUDIT_01_DRAFT.md.


### 2026-10-03 bootstrap-replicate Monte Carlo precision

The frozen 10,000-replicate, plus-one p-value has finite Monte Carlo
precision. At the first Holm threshold (0.05/15 ≈ 0.003333), 32 versus 33
exceedances yield p ≈ 0.003300 versus 0.003400, on opposite sides of the
cutoff. Conditional binomial Monte Carlo SE at that tail probability is about
0.000576 (95% half-width ≈0.00113); this is distinct from uncertainty over
seeds/roots and from bootstrap validity. Independent review should decide
before outcomes whether 10,000 is acceptable under a declared precision
reporting rule or whether a versioned larger/adaptive replicate plan is
needed. No outcomes or bootstrap were computed; no gate changed. See the
inference audit.


### 2026-10-03 outer simulation precision requirement

If independent review requires calibration simulation, freeze both the inner
bootstrap B and the outer number R of independent synthetic datasets. Outer
FWER, coverage, and power estimates are proportions with their own Monte Carlo
error. For example, near a 5% rate, a normal 95% half-width of one percentage
point takes about 1,825 outer datasets per scenario-method cell; half a point
takes about 7,300. These are illustrations, not acceptance criteria. The
reviewer must predeclare R/precision, uncertainty intervals, scenario/method
multiplicity, and deterministic RNG streams before simulation. No simulation,
roots, outcomes, or gate transition occurred. Details:
docs/V212_ROOT_SAMPLING_INFERENCE_AUDIT_01_DRAFT.md.


### 2026-10-04 analytical root-yield sensitivity

For a common independent per-slot validity probability `p`, the exact
binomial-tail calculation for at least 16 valid slots among 64 in each of six
variant × occupancy strata gives an all-six schedule pass probability of
about 0.361 at `p=0.30`, 0.821 at `p=0.35`, and 0.976 at `p=0.40`. Common `p`
values of approximately 0.3662, 0.3834, and 0.4179 correspond to 90%, 95%,
and 99% all-six pass probabilities. This is illustrative analytical
sensitivity only: stratum rates and dependencies are unknown, no roots or
validity rates were observed, and no threshold was selected. The global
yield-failure rule and all V2.12 gates remain open. See the inference audit
draft.


### 2026-10-04 Othello sequence-model prior-art update

Full-text review of Yuan and Søgaard's Othello World Model study found
autoregressive next-move models trained on 132,588 championship games and a
23,796,010-game synthetic corpus, with held-out game sequences. Their reported
one-hop next-move error can be below 0.1% for non-pretrained models on the full
synthetic training scale; the authors state multi-step generation remains
challenging. Their representation probes/alignment concern board structure,
not complete legal-action values, adversarial max/min, or decision regret.
This narrows broad board-state-from-game-history claims but leaves the fixed-
compute V2.12 decision-quality question open. No data, model, code, scores,
root schedule, or outcomes were accessed; no method or gate changed. See
`docs/RELATED_WORK.md` and `docs/V212_NOVELTY_CROSSWALK_DRAFT_01.md`.

### 2026-10-04 MetaOthello multi-world representation update

Full-text review of Chawla, Hall, and Lovato's camera-ready MetaOthello paper
found controlled 8×8 Othello-like variants with shared move syntax and changed
rules or token mappings. The authors report cross-variant causal transfer of
board-state probes and next-move-distribution α-scores above 0.98; each model
was trained once with seed 42. The paper's “world model” means a latent-state
representation reconstructed from move histories, not an explicit JEPA
forward model. This closes broad claims to shared state representations across
board-rule variants, but does not test action-conditioned JEPA, full
legal-action values, adversarial search, board-size transfer, or decision
regret. Results are author-reported and unreplicated here. No code/data were
run, no CAISSA data or outcomes were accessed, and no method or gate changed.
Sources and details: `docs/RELATED_WORK.md` and
`docs/V212_NOVELTY_CROSSWALK_DRAFT_01.md`.

### 2026-10-04 static request-adapter capacity audit

The source-level random-weight inventory is small (9,761 parameter-array
values for ordinary pilot arms and 30,551 for the raw-state control), and the
10,000 entered-node cap gives a conservative ceiling of roughly 20,000–30,000
counted model calls depending on arm. These are arithmetic/control-flow bounds,
not latency or RSS measurements; Python/runtime overhead, model fitting state,
and the end-to-end request path are not represented. The v02 wrapper dispatches
its worker through the v01 module, so both adapter blobs are part of the
effective runtime identity. The request worker still shares its caller's
cgroup, its planner deadline is cooperative, and the v06
external-supervision/receipt correction remains a draft. No request, model,
data, score, or outcome was run or read; no resource or fit gate changed. See
`docs/V212_ADAPTER_CAPACITY_AUDIT_01.md`.

### 2026-10-04 root-sampling and generation-document reconciliation

A fresh read-only independent draft review found stale Design01 references,
conflicting canonical-window deduplication wording, and duplicate/overlap
text that still treated symmetry-unique roots as the current sampling unit.
The proposal documents now point to Design02, preserve repeated root slot
observations, and keep canonical-equivalent fit-window content diagnostic.
Current v05 and Design02 both propose a global six-stratum under-yield stop;
the older claim that they differ was corrected. This is editorial
reconciliation only: v04 remains the current method, root slots and inference
remain unreviewed for validity, and no roots, simulation, model, data, score, or
outcome were generated or accessed. Generation, scoring, fitting, and match
gates remain closed. See `docs/V212_ROOT_SAMPLING_REVIEW_01.md`.

### 2026-10-04 root-inference literature check

Primary methods research on crossed/pigeonhole bootstrap, multiway clustering,
few-cluster inference, and resampling-based multiple testing supports the
conclusion that the proposed v05 inferential procedure has no direct
finite-sample guarantee from the cited sources. See
`docs/V212_ROOT_INFERENCE_LITERATURE_NOTE_01.md`. The current research
recommendation is to require design-matched calibration before the v05
procedure can support nomination. This is not independent statistical
acceptance: the reviewer may accept, revise, or reject the recommendation
and must freeze the scenario grid, numerical tolerances, outer Monte Carlo
precision, and failure response before any simulation. v04 remains current;
no roots, simulations, scores, training, or outcomes were generated/read.

### 2026-10-04 production generator readiness review

Independent static review found no reviewed production-generation contract.
Do not implement a corpus generator until the v04/v05 split disposition,
numeric episode quotas/resource basis, RNG and manifest streams, 928-window
and terminal-target/minibatch semantics, identity-versus-lineage key/overlap
rules, and atomic artifact/receipt/failure behavior are versioned and
independently accepted. See `docs/V212_GENERATION_PROTOCOL_DESIGN_01.md`.
This does not show that a corpus is infeasible or contaminated. The synthetic
auditor stays fixture-only; no episode/policy/data was run or accessed and no
generation/training gate advanced.

### 2026-10-04 static episode quota lower bound

Under the unaccepted Draft v05 window eligibility, exact-rule structure bounds
one complete Connect Four 6×7 episode by 42 action-start windows and one
Reversi6 episode by 64. This yields only optimistic lower bounds of 23 and 15
episodes, respectively, to reach 928 source windows. It is not a quota,
expected yield, or resource measurement; early endings and audit failures raise
the actual requirement. No games or data were generated. See
`docs/V212_GENERATION_PROTOCOL_DESIGN_01.md`.

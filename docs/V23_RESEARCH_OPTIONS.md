# Future research option: action-dependent dynamics and decision sufficiency

Date: 2026-09-29. **Research proposal only: not a frozen method, implementation,
experiment or positive result.** Prepared while Grid03 runs. No Grid03 scores
were inspected; no fitting, locked-final access or runtime source changes occurred.
The original literature proposal used completed Grid01/02 reports only. A later
2026-09-29 update incorporates the Grid02 value-alignment diagnosis below. No
Grid03 result files were opened for this note; its negative status was reported
by the coordinating agent and is not used here to select a new architecture.

## Recommendation

The new evidence in [V21_VALUE_ALIGNMENT_DIAGNOSIS.md](V21_VALUE_ALIGNMENT_DIAGNOSIS.md)
**defers the action-gating study below**. First run a separately frozen, bounded
training-only convergence/capacity diagnosis. The 40-epoch histories continue
improving in every family; target-prior comparisons show real but uneven value
learning, especially weak encoded Reversi H1 fit. Neither an encoder-capacity
bottleneck nor a transition-architecture bottleneck has been demonstrated.

The proposed next diagnostic is 18 runs: direct/value-dynamics/raw JEPA,
hidden/latent 64/32 or 128/64, seeds 17/29/43, unchanged objectives and training
data, and fixed probes/checkpoints through epochs 40/80/160. It cannot support
JEPA superiority and must not import development/final evaluators. Larger
latent width changes several components, so call this total-model capacity.
The coordinating agent must freeze `METHOD_V23_DIAGNOSTIC.md` before any fit.

Factored state/action dynamics remains a conditional future hypothesis only
if the fixed-probe evidence points to recurrent transition error. A small
P-minus-E value-MSE gap does not itself clear the dynamics: squared-error cross
terms can cancel. If later tested, gating needs a credible nonlinear comparator
and common strong recurrent supervision. Equal gains across objectives would
be an architecture improvement, not an incremental JEPA result. The architecture
matrix and robust objectives later in this document remain unselected proposals.

## What the completed evidence actually says

Sources are the immutable local `chess_data/v2-grid-01-report/report.json` and
`chess_data/v21-grid-02-report/report.json`, plus
`V2_GRID01_DIAGNOSIS.md` and `V22_MECHANISM_ANALYSIS.md`.

| Completed study | Best eligible JEPA exact regret | Strongest tuned non-JEPA regret | Improvement, control minus JEPA | Decision |
| --- | ---: | ---: | ---: | --- |
| Grid01 | Projected 0.2491448293 | Value dynamics 0.2476635514 | -0.0014812779 | Not promoted |
| Grid02, coherent augmentation/weight tuning | Raw 0.2074247144 | Value dynamics 0.2122503207 | +0.0048256063 | Not promoted |

Grid02's descriptive 95% interval against value dynamics is
[-0.0390026571,0.0448449240]. Its raw candidate is worse than decoded dynamics
on Connect4 by 0.0124610592 regret, despite a favorable pooled difference.
The projected no-response attribution model has lower pooled regret than the
eligible candidate, but it has a different objective/selected weight: this is
not an isolated causal proof that reply information hurts. It does weaken any
claim that opponent conditioning has already been demonstrated beneficial.

The large improvement of several families between Grid01 and Grid02 cannot be
assigned entirely to JEPA; augmentation and expanded auxiliary tuning changed
together. Grid01's training-only gradient probe found no consistent conflict,
so there is no current case for gradient surgery. Sibling common-residual
energy is large, but the earlier bound/counterexample shows that removing it
can corrupt comparisons between own actions. None of these observations
identifies a proven cause of failure.

## Primary-source search and evidence matrix

Eight Exa searches requested 70 result slots: four 10-result searches covering
board-game JEPA, value equivalence, factored action dynamics, and planning
failure analyses; two 5-result searches attempted to resolve a named chess
JEPA preprint to its primary record; two further 10-result searches covered
game metrics and robust/value-aware model losses. This is 70 requested slots, not 70 unique
papers read. Author papers/repositories were retained; mirrors, summaries,
Exa library descriptions and unrelated work were excluded as evidence.
Original-text method/results extracts were inspected as specified below.
The table reuses earlier verified MuZero/SPR/EfficientZero/value-equivalence
coverage and adds directly retrieved primary sources. No result was reproduced.

| Primary work and source | Relevant positive evidence | Negative evidence, scope and implication |
| --- | --- | --- |
| **MuZero**, [original paper](https://arxiv.org/abs/1911.08265) | Original method extracts: recurrent hidden transitions predict reward, policy and value at each unroll; strong chess, Go, shogi and Atari performance. | It already establishes learned latent planning across board games. Our current recurrent model predicts successor value but supervises policy only on separately encoded states; it is not a faithful MuZero baseline. No claim of first multigame latent planner is available. |
| **SPR**, [original paper](https://arxiv.org/pdf/2007.05929) | Previously inspected method/ablation extracts support recurrent predictive representation learning with projections/EMA and augmentation in Atari 100k. | SPR uses the representation in a model-free agent. Representation gains do not by themselves prove that its transition is useful for explicit minimax rollout. Symbolic boards differ from pixels; its benefits cannot be imported as expected outcomes here. |
| **EfficientZero**, [proceedings](https://proceedings.neurips.cc/paper/2021/file/d5eca8dc3820cad9fe56a3bafda65ca1-Paper.pdf) | Method/ablation extracts: recurrent consistency, value-prefix learning and off-policy correction improve limited-data visual planning. Removing consistency is its largest reported component ablation. | Several mechanisms change together; consistency within learned planning is established prior art. Sparse/noisy RL targets differ materially from our exact solved state labels. No board-game-specific JEPA theorem follows. |
| **Value Equivalence / Approximate Value Equivalence**, [VE](https://arxiv.org/abs/2011.03506), [AVE proceedings](https://proceedings.neurips.cc/paper_files/paper/2022/file/d53538ba21c05fa361d2b21704172753-Paper-Conference.pdf) | Previously inspected definitions/theory extracts: model capacity should preserve relevant Bellman updates for stated policy/function classes, with approximate versions allowing tradeoffs. | A more accurate generic representation need not be a better planning model. MDP policy-expectation assumptions cannot be relabeled as adversarial minimax guarantees. More target functions can worsen finite-capacity approximation. |
| **What model does MuZero learn?**, [original text](https://arxiv.org/html/2306.00840) | Method/results extracts examine MuZero's model contribution separately from its policy/value networks in CartPole, LunarLander and Breakout. | Short-horizon values can be accurate while errors grow over longer unrolls and policies differing from data collection. Strong agent performance does not establish an accurate general-purpose simulator or counterfactual coverage. |
| **Visualizing MuZero Models**, [original PDF](https://arxiv.org/pdf/2102.12924) | Abstract/method extracts visualize encoded and recurrent trajectories and propose regularizers to improve alignment/stability. | Encoded and internally transitioned representations can diverge. This is prior art for representation/transition alignment; these extracts are not evidence that our tiny board-game architecture will benefit. |
| **Demystifying MuZero Planning**, [original text](https://arxiv.org/html/2411.04580v2) | Method/results extracts cover 9x9 Go, Outer-Open Gomoku and three Atari games; search can remain useful despite model drift. | Crucial Table 1 detail: state-consistency coefficient is 0 for board games and 1 for Atari. Do not describe its board results as a positive consistency ablation. Reconstruction does not substantially change overall playing performance; excessive search can hurt. Averaging effects in MCTS do not imply that our strict min/max backup cancels errors. |
| **RePAIR**, Koller, Fürnkranz and Bertram, [original text](https://arxiv.org/html/2606.11860), [author code](https://github.com/Artificial-Chrisi/RePAIR) | Full method/results extracts: masked sequence repair yields chess concept clusters and board reconstruction without explicit move/engine labels. Author arXiv record states IEEE CoG 2026 oral acceptance. | Table I reports long-decoder-only reconstruction 93.90%±0.02 versus 93.18%±0.02 with added JEPA loss; three runs, 80% state masking. These are reconstruction results, not playing-strength/minimax gains. Latent chess representation learning is already explicit prior art, and the auxiliary is not uniformly beneficial even there. |
| **Value-Guided Action Planning with JEPA World Models**, [original text](https://arxiv.org/html/2601.00844) | Method/results extracts shape latent distance/quasidistance toward goal-conditioned reaching value. Table 2 shows value/quasidistance variants improving planning in wall/maze navigation. | The authors report that adding prediction or variance regularization to their value objective can reduce planning performance. Their planner minimizes goal distance; ours evaluates adversarial utility with a separate head. Simply calling a new term “value-guided JEPA” is neither novel nor guaranteed useful. |
| **Action-Conditional Video Prediction**, Oh et al., NIPS 2015, [official paper](https://proceedings.neurips.cc/paper/2015/file/6ba3af5d7b2790e73f0de32e5c8c1798-Paper.pdf), [author code](https://github.com/junhyukoh/nips2015-action-conditional-video-prediction) | Full method/results extracts: factored multiplicative feature/action interactions model different action-dependent transformations; recurrent multistep predictions support Atari control. | The paper notes control-score differences larger than pixel-MSE differences, illustrating metric mismatch. Factorized action gating and recurrent training are longstanding ideas; implementing them is a baseline/inductive-bias test, not a new JEPA principle. |
| **Equivariant MuZero**, [original text](https://arxiv.org/html/2302.04798) | Method/theory/results extracts: equivariant components imply equivariant action selection under the stated construction; experiments improve rotated-map generalization in MiniPacman and ProcGen Chaser. | Replacing its equivariant encoder with a non-equivariant one removes much of the benefit even with an equivariant transition. Games named in its introduction are not its experimental board-game benchmark. Architectural symmetry is prior art and cannot be credited to JEPA alone. |
| **UniZero**, [original text](https://arxiv.org/html/2406.10667) | Method/results extracts disentangle observation representations and temporal context using a transformer world model and report improved heterogeneous-task handling. | In their history-poor setting, MuZero with SSL can fail to converge, while architecture/context changes matter. Our current games are fully observed Markov states; adding a history transformer would not address an established missing-history problem here and would be a large unmotivated compute jump. |

The author [CCranney/JEPA-chess repository](https://github.com/CCranney/JEPA-chess)
is additional direct evidence that chess JEPA experimentation predates this
project's proposed contribution. Its retrieved README explicitly focuses first
on a world model rather than a chess-playing agent; it is not a controlled
performance result.

An unresolved search lead named **JEPA-Chess: Action-Conditioned Joint Embedding
Predictive Architectures for Discrete Logical State Tracking**, attributed by
search summaries to Yumnam Harryson Singh/Zenodo, could not be resolved to an
original record in two targeted queries. Its differing summary descriptions
and numerical claims are **not accepted as evidence**. Keep this novelty risk
open; do not invent a DOI, claim the paper was reviewed, or argue absence of
prior art from this incomplete retrieval.

## Why raw latent MSE is not action-order sufficiency

For the actual scalar head `V(z)=tanh(z w+b)`, a small latent perturbation e has
first-order value effect `(1-V(z)^2) w^T e`. Squared latent error weights all
directions equally, while directions orthogonal to w have no first-order effect
on value. Errors aligned with w may dominate a decision despite occupying a
small share of total latent MSE. Near tied own-action minima, even a small value
error can switch the selected move.

Errors along currently value-irrelevant directions can still matter after a
later action transforms the representation. Therefore deleting them solely by
the current value gradient is also unsafe for deeper planning. A representation
sufficient for one present scalar value need not be sufficient for all legal
future transitions. Conversely, when exact V* is available at the actual depth 2
leaves, that scalar alone is sufficient for the fixed backup; reconstructing
every board detail is unnecessary for that particular decision.

Latent coordinates are learned and can change across methods. Rescaling or
changing a basis can alter their MSE without changing the information usable by
a correspondingly adjusted head. The exact transformations realizable by our
tanh network are constrained, but this does not make cross-model latent MSE a
common strategic scale. Variance/effective-rank checks diagnose collapse; they
do not certify action-relevant information.

The local bound from `V22_MECHANISM_ANALYSIS.md` remains the useful link:
if every leaf value has error at most epsilon, the chosen root action has regret
at most 2 epsilon. Relative sibling errors alone do not bound group-specific
offsets. Projected-normalized matching has an additional null-space/scale
problem because the value head consumes unprojected features.

Two proposed “value-aligned” shortcuts deserve explicit controls:

1. Weighting raw residuals by `w w^T` gives `(w^T e)^2`, which is matching
   scalar value preactivations. Locally weighting by the full value Jacobian
   similarly approximates scalar value consistency. It must be compared with
   the simpler EMA-value control, not described as wholly new latent learning.
2. Training several value/ranking heads can preserve more continuation
   functions, but supplies additional supervision. Non-JEPA recurrent controls
   must receive the identical labels/heads. Opponent-policy expectation heads
   are different targets from optimal/worst-case minimax value; they cannot be
   mixed under one “game-theoretic” claim.

## One narrow architectural candidate

The present predictor is `tanh(z W + a A + b)`. Its action changes an additive
preactivation offset; the nonlinear activation does permit interactions, so
the model is not action-independent. Nevertheless its structure provides no
explicit learned action-dependent linear map of z.

A small prospective replacement is

`g(z,a)=tanh(z W + a A + ((z U) elementwise_mul (a B)) C + b)`.

Use one fixed low rank, for example 8, shared across games and both plies.
With latent 32 and action 65, the new factors add 1032 parameters to the 3136
parameter affine transition, giving 4168 transition parameters. These are
architecture calculations, not measured resource results. Keep the first and
second legal actions explicitly conditioned; retain the reply-masking
attribution as a later required check if a candidate survives.

A two-layer additive transition of width 32 on concatenated `(z,a)`, with tanh
hidden/output, has 4192 parameters. It is a credible near-parameter comparator
(24 more than the gated transition), unlike comparing only against the smaller
affine model. Actual forward/backward work must also be measured; nominal
parameter matching is not a compute guarantee. Do not add dummy work to a
cheaper baseline.

The falsifiable mechanism is that explicit state/action interactions reduce
counterfactual successor-value and own-action-minimum errors at a fixed useful
capacity, and that JEPA contributes more than the same architecture trained
with task supervision/reconstruction. Action-factor visualizations or lower
latent MSE do not establish that mechanism.

## Strengthen the recurrent control before attributing a gain

MuZero supervises policy at recurrent states. Our current common policy loss
does not: it sees `encode(actual_state)`, whereas the recurrent output has only
value and an optional auxiliary. A future serious control should include legal
soft policy CE on predicted H1/H2 states wherever policy labels are available,
using actual successor legality solely for a common training mask. Terminal
and missing-horizon policy losses remain zero.

This does not require a new oracle target on the already labeled bank, but is
a new objective term and must be frozen prospectively with one coefficient
and denominator convention shared by all recurrent families. In the scarce
regime, hidden policies remain unavailable; never unmask them to create a
“better baseline” or candidate. The direct model retains the same encoded
supervision. If recurrent policy supervision alone closes the gap, report the
value of a stronger non-JEPA planning model.

Do not simultaneously add group reweighting, wider encoders, more horizons,
new data and new search budgets. A spatial/equivariant encoder is a credible
second option, supported by Equivariant MuZero, but would alter both direct
state evaluation and dynamics. It should be investigated separately if encoder
sufficiency diagnostics, rather than transition diagnostics, identify the
bottleneck. Connect4 admits horizontal reflection, not gravity-breaking D4;
Reversi6 has its own valid symmetry group.

## Diagnostics that decide whether to proceed

Before freezing a new fitting matrix, use a bounded **training-only**,
preselected-root diagnostic to separate three failures:

- Encoded value/policy insufficiency: exact-state evaluation is already wrong.
- Transition insufficiency: recurrent values/policies disagree with re-encoded
  successors even when the latter are accurate.
- Search/value-tail mismatch: average errors are small but a decisive reply's
  error changes the minimum and root ranking.

Report per-game/horizon counts, paired seed distributions, signed backup bias,
worst-reply errors, within- versus between-own-action value errors, and error
components along/orthogonal to the value direction. Sample roots by a frozen
ID/seed schedule before examining model errors; include all legal branches.
These probes localize hypotheses, not prove causality. Do not select development
positions because the gated or JEPA model wins them.

If transition-induced value error is negligible relative to encoded error,
do not launch a gating study merely because it is available. If transition
error is material, a frozen-encoder diagnostic may isolate dynamics fitting,
but must state what the encoder was trained on and must not call reused
training representations an unseen-state generalization result.

## Possible finite matrix and discriminating tests

One prospective full-label mechanism matrix could use three transitions
(current affine, rank 8 gated, width 32 nonlinear additive), three recurrent
objectives (strong policy/value dynamics, decoded dynamics, raw JEPA), two
rates and three seeds: 54 cells, plus six direct cells, totaling 60. This
full-label choice isolates architecture from label-mask changes; EMA-value
is algebraically redundant with value dynamics at full labels. If instead a
scarce regime is selected for a scientific reason, include EMA-value as an
additional independent control and declare the larger matrix in advance.
Do not choose whichever fraction or architecture looks best in partial runs.

This is a size illustration, not authorization or a frozen protocol. Fix loss
coefficients, initialization, batch schedule, budgets, selection rule and all
architectural sizes before fitting. Reuse the same immutable roots and existing
split policy, every legal branch, augmentation, labels and evaluation schedule.
Keep all attempted cells. Historical Grid01/02/03 numbers remain visible but
do not replace contemporaneous controls with the strengthened recurrent loss.

The following contrasts must be distinct in analysis:

| Contrast | Supported conclusion if favorable | Failure interpretation |
| --- | --- | --- |
| Gated versus near-parameter nonlinear transition under value dynamics | Explicit state/action factorization is useful at this capacity | Any gain over affine alone may be generic capacity/nonlinearity |
| Gated raw JEPA versus gated value dynamics, decoded and EMA-value where applicable | Incremental predictive-representation benefit survives stronger controls | No JEPA-specific candidate, even if gated models are stronger |
| JEPA improvement under gated versus under nonlinear/additive dynamics | Evidence about the proposed architecture/objective interaction | Equal improvements across architectures do not support the special interaction |
| Hybrid versus exact-state behavior with the same checkpoint | Whether the learned transition preserves usable values for search | Exact-only gain is encoder regularization, not improved model rollout |
| Matched active-compute replication and later reply-action ablation | Whether the advantage survives resource accounting and requires response conditioning | More training/search or generic regularization may explain the gain |

Retain the existing 0.05 development margin, positive per-game requirements,
paired-seed direction and collapse/failure gates. Additionally report the
prespecified architecture interaction with uncertainty; do not treat a noisy
interaction as established because one arm passes a screening threshold.
If an otherwise promising architecture has no incremental JEPA advantage,
preserve the negative finding and narrow the research claim. Never lower the
margin, remove a strong control, select easier states or consume the locked
final set to keep iterating toward a win.

## Deferred alternative: tail-weighted error over complete reply forks

This is a separate prospective objective, not an addition to the architecture
grid above. It should remain deferred until Grid03 and the planned value-alignment
diagnosis are complete. For one fixed state and own action, enumerate all K legal
opponent replies and define squared latent prediction errors ell_b. A uniform
upper-tail objective with tail mass tau in (0,1] is

`CVaR_tau(ell) = min_eta [eta + sum_b max(ell_b - eta, 0)/(tau K)]`.

Here tau=1 gives the mean, and tau<=1/K gives the maximum. Fractional weighting
at the quantile boundary matters when legal-reply counts differ; selecting
ceil(tau K) replies and averaging them changes the requested tail mass. The
future protocol must fix tau, any mean/tail interpolation, tie handling and
root/action/group weighting before fitting. Keep complete groups and the same
transition exposures for every arm. No branch can be removed after seeing
prediction error, development regret or utility.

**The largest model error is not the opponent's lowest-utility reply.** Uniform
branch weights define a training measure, not a behavioral opponent policy.
CVaR of deterministic prediction residuals is also not CVaR of stochastic game
returns. A rare large latent error may lie in a value-irrelevant direction;
tail weighting could therefore divert capacity from the actual decision.
Keep absolute pointwise/value anchors so different own-action groups cannot
acquire arbitrary offsets. The earlier sibling-mean counterexample still
applies if a relative objective replaces those anchors.

The discriminating experiment would compare mean versus the same prespecified
tail objective for latent JEPA, oracle predicted-value error and decoded-state
error; add EMA-value error under a restricted-label protocol. All arms need
the same group sampler, examples, labels, update budget and measured runtime.
Report both mean and tail value discrepancies, worst-reply identity stability,
root action margins and the unchanged primary regret metric. A gain explained
by CVaR value or decoded supervision is evidence for robust model fitting, not
an incremental JEPA mechanism. Worsening action ranking despite lower tail
latent error directly refutes the proposed alignment story.

## Deferred alternative: legal-reply operator probes

For fixed normalized scalar probes f_j of latent state, one can compare, for
each own action a, the backed-up feature values

`B_j(a) = min_{b in legal_replies(s,a)} f_j(z_ab)`

between recurrent predictions and stop-gradient encodings of actual successors.
Player perspective, terminal outcomes and truncated branches must be defined
before applying the minimum. Include the actual value head as a separate probe;
random linear probes would test additional directions without additional
oracle labels. Match the vector indexed by own action, not merely its maximum:
permuting own-action values can preserve max_a B_j(a) while choosing the wrong
action. Legal replies themselves come from the shared exact rules, so this
would not establish that the latent model learns legality.

This objective has serious identifiability limits. Even matching minima of
**all** linear probes identifies only the convex hull of the successor latent
set. It need not recover interior states, multiplicities, or which reply led to
which successor. A finite random probe bank is weaker. Such a representation
can match one backup yet fail recurrent planning where action correspondence
and subsequent legal structure matter. It is not a bisimulation guarantee or
equivalence for every future learned value function. Minimum gradients also
touch only extremal branches, while collapsed latents can agree on every probe;
pointwise and anti-collapse anchors remain necessary.

A fair mechanism study would compare the same fixed bank with pointwise probe
matching, actual-value-only backup matching, deliberately shuffled reply groups,
and strong policy/value, decoded and EMA-value controls as applicable. Fix the
probe bank independently of development outcomes and never choose probes by
their development correlation. If probes use extra supervised values, provide
those labels and heads to all controls. Improvement over plain latent MSE
without improvement over the actual-value backup control would not establish
that random feature equivalence contributes anything. Failure of a one-step
operator score to predict two-step decision accuracy is a direct negative test.

### Closest verified primary theory and limits of transfer

| Original source inspected | Relevant prior result | Boundary for this proposal |
| --- | --- | --- |
| de Alfaro, Majumdar, Raman and Stoelinga, [Game Refinement Relations and Metrics](https://arxiv.org/html/0806.4956), original abstract and definition extracts | Quantitative refinement/bisimulation metrics for two-player games relate state distance to differences in quantitative winning objectives. | Game-aware behavioral distances predate JEPA. The paper treats broader stochastic/concurrent settings and formal operators; a finite probe loss does not inherit its guarantees. |
| Chatterjee, de Alfaro, Majumdar and Raman, [Algorithms for Game Metrics](https://drops.dagstuhl.de/entities/document/10.4230/LIPIcs.FSTTCS.2008.1745), official proceedings abstract and PDF algorithm extracts | Algorithms explicitly cover game metrics for turn-based stochastic games, MDPs and concurrent games. | Turn-based game bisimulation is direct prior art for an adversarial sufficiency claim, even though our games are deterministic. No new metric or proof has been supplied here. |
| Asadi, Cater, Misra and Littman, [Equivalence Between Wasserstein and Value-Aware Loss for Model-based Reinforcement Learning](https://arxiv.org/pdf/1806.01265), original PDF method/theory extracts | Under its function-class assumptions, the value-aware model loss is related to Wasserstein model error via Lipschitz value functions. | Worst-case value-function discrepancy and value-aware losses are established ideas. Random probes are an approximation with coverage limits, not a new equivalence theorem. |
| Kastner, Erdogdu and Farahmand, [Distributional Model Equivalence for Risk-Sensitive Reinforcement Learning](https://sologen.net/papers/DistEquiv(NeurIPS2023).pdf), author-hosted NeurIPS 2023 paper abstract/theory extracts | Risk-neutral proper value equivalence need not suffice for risk-sensitive planning; distributional equivalence addresses richer return criteria. | CVaR of model residuals is a different object from CVaR of returns. This source motivates carefully naming the objective, not claiming its guarantees for deterministic fork errors. |

These sources complement the value-equivalence and approximate-value-equivalence
papers already reviewed above. The robust and operator-probe options are
plausible failure-capable mechanisms, but presently weaker recommendations than
diagnosing the representation/transition bottleneck. None is selected, frozen
or implemented. They must not be appended opportunistically to the running grid.

## Novelty and publication boundary

Action-conditioned latent planning, recurrent consistency, value-shaped
representations, multiplicative transitions, symmetry-aware world models and
chess JEPA representations all have clear prior art. A publishable direction
would need a reproducible controlled contribution beyond those components,
independent evaluation and a defensible account of why adversarial decisions
benefit. A positive development interaction is an interesting candidate, not
a unique architecture, broad superiority claim or Q1 acceptance guarantee.

Search accounting: eight `web_search_exa` calls, requested slots 10+10+10+10+5+5+10+10=70.
Fetches are not counted as search slots. Source summaries used only for locating
primary work are explicitly excluded from substantive evidence.

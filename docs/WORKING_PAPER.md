# Testing action-conditioned latent prediction for bounded two-player planning

Working research note, 2026-09-29. This is an exploratory negative/feasibility
report, not a submission-ready paper. Authorship and publication venue are not
assigned by the agent. Q1 is a future quality target, not an acceptance claim.

## Abstract

We investigate whether predicting future latent states conditional on both
players' actions improves bounded planning in deterministic, alternating,
perfect-information, zero-sum games. We implement shared-weight models across
tic-tac-toe, gravity connect-3 and small Reversi, with a held-out board-size
combination. A strict trajectory/context/target isolation audit rejects the
initial whole-game dataset for inadequate coverage. A pre-fitting amendment
narrows the task to middle/late positions. Seven objectives and three seeds are
evaluated under fixed two-ply exact-state and hybrid latent search. All learned
models achieve zero oracle action regret in the exact-state diagnostic, exposing
a benchmark ceiling. Hybrid full JEPA incurs five regret units across72 Reversi
decisions, compared with zero for direct re-encoding and five for decoded
dynamics. These limited exploratory observations do not demonstrate a JEPA
advantage. The principal current deliverables are an auditable experimental
pipeline, reproduced protocol defects and explicit benchmark limitations.

## Research question and positioning

The falsifiable question concerns incremental planning value of the predictive
objective, not whether one implementation can run multiple games. MuZero already
learns action-conditioned latent models for board-game planning; SPR already
uses recurrent future-representation prediction as an auxiliary learning signal.
[MuZero](https://arxiv.org/html/1911.08265v2),
[SPR](https://arxiv.org/html/2007.05929v3).

Our candidate method uses separate own/reply action slots and exact legal
minimax branches. This is a proposed adaptation whose novelty is unverified.
The scoped [related-work matrix](RELATED_WORK.md) includes JEPA foundations,
LeJEPA, EfficientZero, AlphaZero, RePAIR, opponent modeling and evaluation.
An exhaustive citation-screening record and stronger recurrent consistency
controls are still required before submission. Conditioning on observed replies
does not infer a particular opponent's behavior, and predicted leaf values do
not solve an equilibrium.

## Method and study design

The immutable [v1 method](../METHOD_SPEC.md), [pre-fitting amendments](METHOD_AMENDMENTS.md)
and [executed report](TWO_PLAYER_PILOT_20260929.md) specify state/player perspective,
rules and terminal/pass semantics, shared padded features, action masking, EMA,
all loss coefficients, seven controls, optimizer, seeds and fixed schedules.
Direct-H2 prediction and recurrent-H1 inference are distinguished. Value targets
come from behavior rollouts, not minimax labels. Exact transitions preserve
legality while model leaves approximate outcome: the hybrid is not simulator-free.

The procedural dataset uses hash-grouped train/validation/selection/final splits
with held-out-first symmetry-aware context/H1/H2 ownership. Exact duplicate
trajectories are removed; repeated states within a split can remain. Generation,
audit, optimizer and model-selection costs must be separated in any later
efficiency study. This pilot equalizes batches/epochs, not FLOPs or wall-time.

## Results and negative evidence

The executed report and its aggregate JSON contain all runs, confidence methods,
seed-level outcomes, exclusions and hashes. There are no confirmatory scores.
The initial coverage failure and subsequent pre-fitting scope change remain
visible. The small passing dataset has1,129 training records. No collapse alert
fires, but this neither proves representation usefulness nor theoretical
non-collapse. The planning schedule contains68 roots, including only2 connect3
positions; many decisions are resolved by exact terminal rules. All learned
exact-state variants hit a zero-regret ceiling, while full JEPA does not improve
over direct or decoded controls in the hybrid track. Held-out-size results do
not demonstrate a transfer advantage. No claim of statistical superiority,
equivalence, whole-game strength or opponent robustness is supported.

## Limitations and threats to validity

Internal validity: hand-written rules/oracle share implementation outside the
independent tic-tac-toe fixture; Monte Carlo behavior value supervision can be
biased for minimax leaves; tiny data and near-inactive variance regularization
limit ablation interpretation. Strict exclusion changes the sampled distribution.
Sample-weighted training favors Reversi. Representation losses compare different
learned spaces. Independent review improves defect detection but is not formal
verification.

External validity: tiny middle/late positions, one board-size holdout, no unseen
family, no few-shot test, no full matches, no independent engine/reference pool,
no exploitability or calibrated opponent evaluation. Three seeds on one dataset
do not characterize generalization uncertainty. Timings include instrumentation
and concurrent work; memory is traced allocations rather than RSS. Confirmation
is blocked, and all final predictions remain unopened.

## Reproducibility, data and license statement

Source commit66ff9f2, exact hashes, pinned environment, commands, local artifact
paths and checkpoint fingerprints are documented in the executed report. CPU-only
generation and training need no paid resources. All21 checkpoint hashes were
independently verified. Generated trajectories/checkpoints remain local and are
not distributed without an owner-approved license/storage plan. No external
dataset is used; official rights of potential sources are in the
[license register](DATA_SOURCES.md). Fixture/unit tests are excluded from research
performance evidence. Manuscript numbers are generated from actual receipts.

## Decision and submission gate

Current evidence justifies a benchmark-development pivot, not more training of
the same fixed setup or a positive method paper. The next protocol must have
adequate discriminating positions, independent rules, multi-step-trained
consistency/untrained controls, compute tracks and new development data.
Only subsequent validated evidence can justify power analysis, a locked
confirmatory study and a publication claim. Negative results remain publishable
evidence in principle, but the present limited study is not asserted to meet
Q1 novelty or methodological standards.
# Versioned evidence update: v2 and v2.1

This research note remains exploratory and not submission-ready. The frozen
v1 pilot below is historical evidence. Subsequent independent-rule datasets and
development grids are documented separately in METHOD_V2, METHOD_V21 and their
complete reports; they do not retroactively validate the v1 hypothesis.

The36-cell v2 study found projected JEPA regret0.249145 versus strongest tuned
value-dynamics0.247664. The60-cell coherent-symmetry/weight follow-up found raw
JEPA0.207425 versus value-dynamics0.212250, improvement0.004826 with descriptive
paired95% interval[-0.039003,0.044845]. Both failed their prospective0.05 and
per-game promotion requirements. All reported decisions/artifact identities
were independently checked. No selection/final predictions have occurred.

The full-label evidence therefore does not establish incremental JEPA planning
superiority. Exact-state changes can reflect encoder regularization; hybrid
rollouts still substantially degrade Reversi decisions. No-response's strong
exact-state score also limits opponent-action attribution. All controls received
the same labels, states and sampling; augmentation improved several families.

![V2.1 development results](figures/v21-grid02.png)

References and complete outcomes: [v2 report](V2_GRID01_RESULTS.md),
[v2.1 report](V21_GRID02_RESULTS.md),
[independent review](V21_INDEPENDENT_RESULTS_REVIEW.md), and
[training-only diagnosis](V2_GRID01_DIAGNOSIS.md). A restricted-label experiment
is prospectively specified in METHOD_V22; it has no results and changes the
scientific regime rather than erasing these negative full-label findings.

# Testing action-conditioned latent prediction for bounded two-player planning

Working research note, 2026-09-29. This is an exploratory negative/feasibility
report, not a submission-ready paper. Authorship and publication venue are not
assigned by the agent. Q1 is a future quality target, not an acceptance claim.

## Abstract

We investigate whether predicting future latent states conditional on both
players' actions improves bounded planning in deterministic, alternating,
perfect-information, zero-sum games. An initial tiny-game pilot exposed a
zero-regret benchmark ceiling. Three subsequent development grids on Connect4
4x5 and Reversi 6x6 use 209 fixed roots, three optimizer seeds and exact/hybrid
two-ply search. The 36-cell full-label grid and 60-cell symmetry-augmented grid
failed their prospective promotion gates. The latest 72-cell study restricts
training-label access using one fixed canonical mask, with a full-label
sensitivity arm. In the primary scarce regime, raw JEPA has equal-game exact
regret 0.293339 versus 0.283917 for the strongest tuned direct control: improvement
-0.009422, descriptive paired 95% interval [-0.075730, 0.047922]. It is worse
in both games. No failed/censored decisions or collapse alerts explain this
negative result. Current evidence does not establish JEPA planning superiority,
label efficiency, transfer or publication readiness. The contribution so far is
an auditable pipeline, explicit negative evidence and increasingly controlled
tests of predictive auxiliary objectives. All grids remain adaptive development;
selection and final predictions remain unopened.

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

## Historical v1 method and study design

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

## Historical v1 results and negative evidence

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

## Historical v1 limitations and threats to validity

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

## V1 reproducibility, data and license statement

Source commit66ff9f2, exact hashes, pinned environment, commands, local artifact
paths and checkpoint fingerprints are documented in the executed report. CPU-only
generation and training need no paid resources. All21 checkpoint hashes were
independently verified. Generated trajectories/checkpoints remain local and are
not distributed without an owner-approved license/storage plan. No external
dataset is used; official rights of potential sources are in the
[license register](DATA_SOURCES.md). Fixture/unit tests are excluded from research
performance evidence. Manuscript numbers are generated from actual receipts.

## Historical v1 decision and submission gate

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
v1 pilot above is historical evidence. Subsequent independent-rule datasets and
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
[training-only diagnosis](V2_GRID01_DIAGNOSIS.md). The completed restricted-label experiment below changes the scientific regime
rather than erasing these negative full-label findings.


## Completed v2.2 restricted-label study

The [frozen method](METHOD_V22.md) prespecified 72 cells: two fractions, six
families, two learning rates and three seeds. The same 509 training roots,
transitions, epoch schedules and coherent symmetries are used across fractions.
Only nonterminal label availability changes. The primary mask selects 25% of
roots per game and reveals their canonical two-ply closure; actual labeled
nonterminal state counts are 848/3,468 for Connect4 and 1,386/5,444 for Reversi.
Free terminal utilities remain shared. Trainer artifacts physically redact
hidden targets and label-derived identifiers, and a separate development-only
export prevents reading hidden parent training labels. This simulates access
restrictions on a previously solved bank; it measures no oracle-compute saving.

| Scarce-arm tuned family | Equal-game exact regret |
| --- | ---: |
| Direct policy/value | 0.283917 |
| Value dynamics | 0.308045 |
| Decoded dynamics | 0.298164 |
| Raw JEPA | 0.293339 |
| EMA-value dynamics | 0.298394 |
| Raw no-response attribution ablation | 0.283764 |

Raw JEPA is the only eligible candidate; the no-response ablation cannot replace
it. Improvement means control regret minus candidate regret. All four primary
comparisons have two favorable paired seeds out of three, but their descriptive
95% hierarchical bootstrap intervals include zero:

| Tuned comparator | Improvement | 95% development interval |
| --- | ---: | --- |
| Direct | -0.009422 | [-0.075730, 0.047922] |
| Value dynamics | 0.014706 | [-0.051831, 0.081014] |
| Decoded | 0.004826 | [-0.055340, 0.063496] |
| EMA-value | 0.005055 | [-0.059770, 0.069122] |

The primary candidate is worse than direct in both games, ties value-dynamics
on Connect4 and loses to EMA-value on Connect4. It fails the unchanged 0.05 and
per-game requirements. Intervals condition on one fixed label mask, two games
and three optimizer seeds, without adaptive-selection correction. The study
therefore does not support the proposed restricted-label advantage.

Full-label sensitivity reuses each family's scarce-selected learning rate:
raw JEPA 0.205867, direct 0.224788, value-dynamics/EMA-value 0.249145, decoded
0.255757 and raw-no-response 0.210693. This descriptive ordering is not a
comparison against independently tuned full-label baselines and cannot replace
the failed primary endpoint. Full-label EMA-value/value-dynamics online, target
and Adam tensors match for every rate/seed pair, as the objective predicts.

All 72 cells completed: 30,096 learned decisions and 836 fixed-control decisions,
zero failures/censoring/collapse alerts, and zero strict report verification
errors. Recorded training totals 1,102.6110401 seconds (11.9296–23.8614 per cell),
excluding evaluation and previous data generation. Process-lifetime peak RSS is
251,486,208 bytes; this includes preprocessing/previous cells and is not a
per-model peak. Run artifacts total 78,628,950 bytes and remain locally excluded.
No selection/final predictions were made. Original v1/v2/v2.1 results remain.

Source commit: `9e3d10bb3d01f4761db552ec6b2d7241957cf2e0`; ledger SHA-256:
`660fe61f7612ed3ca69ff7b9dcb5bb91a3c4cf4c656c05c6332df412f29c1f26`.
The [complete 72-cell report](V22_GRID03_RESULTS.md) and
[exact aggregate JSON](validation/V22_GRID03_RESULTS.json) retain all settings,
label counts, checkpoint identities, representation diagnostics and outcomes.
Independent post-result review verified counts, paired schedules and tensor
equivalence. The complete full-label table also contains direct at learning
rate 0.001 with regret 0.196598, below raw JEPA's 0.205867. This descriptive
check does not retune the primary endpoint; it demonstrates the importance of
not claiming full-label superiority from scarce-selected sensitivity alone.

![V2.2 primary restricted-label development results](figures/v22-grid03.png)

The current decision is not to promote this method or weaken its gates. Further
work requires a new prospective mechanistic hypothesis, credible related-work
differentiation, stronger replication and eventual untouched confirmation.
Exact-state representation effects must remain distinct from learned-rollout
benefits. Multiple games in the training pool do not demonstrate held-out-game
transfer; local action regret does not establish whole-game strength. These
limits and the three negative development screens belong in any future paper.

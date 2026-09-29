# Constraints on the next claim-bearing development experiment

Date: 2026-09-29. **Design critique only; no new method freeze or experiment.**
Prepared while the complete 18-cell V23 diagnostic is pending. No partial V23
metrics, new model predictions, protected data or external searches were used.
This memo relies on the frozen methods and primary reviews already recorded in
`V23_RESEARCH_OPTIONS.md` and `V22_MECHANISM_ANALYSIS.md`. It does not select a
new capacity, training duration, label regime, loss or architecture.

## 1. A diagnostic response must strengthen the comparison symmetrically

If V23 indicates that the training budget is limiting, a later comparison must
give the same newly frozen training opportunity to the candidate and all strong
controls. Do not train JEPA longer while keeping a historical 40-epoch baseline.
The current six families are direct, value-dynamics, decoded, raw-jepa,
EMA-value and raw-no-response. Keep strong controls and attribution roles clear:
raw-no-response is not an eligible replacement candidate. At full labels,
EMA-value and value-dynamics have identical online updates; disclose that
redundancy rather than counting them as independent scientific evidence.

V23 includes only three families and full labels. Its outcome cannot determine
scarce-label EMA-value or decoded performance, or justify removing either from
a subsequent relevant comparison. Likewise, 128/64 changes encoder, latent
state, heads and dynamics together; it does not identify encoder width as the
cause. A training-only improvement cannot establish generalization.

Freeze one finite grid, a common budget/capacity rule, identical data exposure,
augmentation, seeds and tuning opportunities before viewing new development
results. Report both update/data matching and actual time/memory; equal epochs
are not equal active compute. No extra candidate-only rate, checkpoint, seed,
label mask or early-stop opportunity. Preserve failed/censored cells and all
earlier negative grids. Do not extend a run or grid until JEPA wins.

## 2. Strengthen recurrent task supervision before a model-based claim

The current encoded policy/value control supervises policy on actual encoded
states. Recurrent H1/H2 states receive successor-value supervision, but no
policy CE. Therefore the present value-dynamics control is a useful matched
ablation, **not a faithful MuZero baseline**. MuZero trains recurrent reward,
policy and value predictions; recurrent consistency also has established
precedent in EfficientZero. [MuZero](https://arxiv.org/abs/1911.08265),
[EfficientZero](https://proceedings.neurips.cc/paper/2021/file/d5eca8dc3820cad9fe56a3bafda65ca1-Paper.pdf).

A serious future recurrent control should consider policy CE on predicted
successors wherever existing policy labels are available, with one coefficient,
legal-action mask and denominator convention shared by all recurrent families.
Missing/terminal policies contribute exactly zero; scarce labels remain hidden.
Introducing this term is a new prospective objective, so it belongs in all
contemporaneous controls and the candidate, never only in JEPA. If it explains
the gain, credit stronger task supervision. In the present terminal-utility
games, exact reward/terminal handling can be shared; do not add a redundant
learned reward head solely to imitate terminology.

Even this strengthened control should be called a matched recurrent
policy/value model. Claiming superiority to MuZero itself would require a
documented implementation and comparable search/training setup. Current
complete legal-tree evaluation differs materially from MuZero's MCTS and
self-play learning. Neither policy accuracy nor an uncalibrated policy
expectation is a minimax guarantee.

## 3. State precisely what an adversarial representation must preserve

For root s, own legal action a and legal reply b, let q_ab be continuation value
in the **root player's perspective**. Define m_a=min_b q_ab and choose
argmax_a m_a. A branch terminal after the first action contributes its known
utility directly; it is not an empty minimum or an invented second action.
Pass actions and terminal/absent targets need explicit masks and count audits.

If predicted leaf values satisfy |qhat_ab-q_ab|<=epsilon uniformly over the
fixed legal tree, minimum/maximum nonexpansiveness bounds selected-action regret
by 2 epsilon. A positive root action gap exceeding 2 epsilon is sufficient to
preserve membership in the optimal action set. These elementary bounds do not
make average latent MSE a certificate: one bad reply can change a minimum.

For an L-Lipschitz value head, target-value error eta and prediction error e
give |qhat-q|<=eta+L||e||. For V(z)=tanh(z w+b), L<=||w||_2. The relevant norm
must act on the space consumed by that head. Projection matching can leave
uncontrolled directions, while lowering the weight of an own-action group's
common residual can arbitrarily change comparisons between own actions.
Anti-collapse rank alone does not prevent that failure. See the explicit
counterexample in `V22_MECHANISM_ANALYSIS.md`.

Necessary mechanism measurements include signed leaf-value errors, worst-reply
and own-action ordering, action margins, game/horizon strata and branch-count
weighting, alongside latent diagnostics. Preserve entire predefined legal
forks. Do not select development positions because the candidate wins them.
Random-value probes and CVaR residuals would be separate hypotheses: linear
probe minima identify at most a successor convex hull, and the branch with
maximum prediction error need not be the opponent's lowest-utility reply.
Relevant function-class and game-metric prior art already exists; a new loss
does not inherit its guarantees. [Value equivalence](https://arxiv.org/abs/2011.03506),
[Game refinement relations and metrics](https://arxiv.org/html/0806.4956).

## 4. Separate the mechanism from the evaluation machinery

The existing exact-state track re-encodes real successor states and bypasses
the recurrent predictor. A gain there supports representation regularization
for that evaluator. It cannot establish better learned-transition planning.
The hybrid track exercises recurrence, but still obtains legality and terminal
facts from exact rules. It cannot establish a standalone latent simulator or
learning the rules. Explicitly report that assistance and its compute.

For a learned-planning claim, a new protocol must predeclare a primary metric
that actually uses the learned transition and its fixed budget. Keep the
historical exact-state results visible. Do not switch primary tracks after
seeing scores. Same-search comparisons need identical tree rules, root
schedule, terminal overrides, ordering/ties, node/time limits and failure
handling; end-to-end strength is a separate experiment. A smaller latent loss
without improved value/action ordering is a failed mechanism test.

An action-conditioned transition predicts what follows a supplied reply. It
does not predict which reply a particular opponent will choose. Reply masking
isolates use of the reply input only when objective, architecture, data and
training opportunities match. It neither fits a behavioral opponent nor
proves equilibrium search. Policy expectations require a declared, calibrated
distribution; worst-case minimax requires the legal adversarial backup.

## 5. Bound the claims and keep the next decision finite

Use the complete V23 outcome first, including failures and seed disagreement.
No partial diagnostic chooses a new architecture. Freeze one next question
and its finite experiment; do not jointly change capacity, losses, data,
planner and budget and then attribute the whole change to JEPA. If several
changes are necessary, include contrasts that distinguish their contributions.

The next development screen must retain the existing meaningful margin and
per-game/paired-seed requirements; a failed strong control cannot be bypassed.
Repeated use of these development roots is adaptive. Development confidence
intervals do not correct that history or establish confirmatory significance.
Only a surviving candidate justifies an independent, separately frozen
replication/selection plan and later protected confirmation. Leave the final
set untouched while making these choices.

JEPA's incremental effect requires matched non-JEPA task supervision, decoded
dynamics, and EMA-value consistency where label scarcity makes it distinct.
Useful recurrent latent consistency is already present in SPR/EfficientZero;
board-game latent planning is already present in MuZero; chess JEPA work also
exists. A positive controlled effect would be a research lead, not uniqueness
or Q1 acceptance. A two-game in-distribution result would still leave held-out
game/variant transfer, stronger reference opponents and end-to-end strength
unproved. [SPR](https://arxiv.org/pdf/2007.05929),
[RePAIR](https://arxiv.org/html/2606.11860).

Stop or pivot if the finite study remains negative, if common supervision or
compute explains the advantage, or if improvements do not survive the required
controls. Preserve that result for the professor-facing research account.
The deliverable is a falsifiable explanation with reproducible evidence, not
a promise that enough adjustments will force JEPA superiority.

# V2.12 counterfactual support protocol draft 01

**Status: proposal for independent review only.** This draft turns the open
measurement question in `V212_COUNTERFACTUAL_SUPPORT_AUDIT_DESIGN_01.md` into
candidate definitions. It is not frozen, does not amend METHOD_SPEC_V212-04,
and does not authorize trajectory/root generation, fitting, match play, or
outcome access. No dataset or result was inspected to make these proposals.

## Keep three populations distinct

“Counterfactual coverage” currently risks conflating three different things.
Report them separately; do not combine them into one score.

### 1. Behavior-data support

The behavior-support ledger is computed from the exact episodes and windows
assigned to fitting, before any model is fit. Define the eligible training
state set `S_fit` as every exact state that is actually supplied to a V2.12
training loss or used as an intermediate state in a valid one-, two-, or
four-ply predictor unroll. Define

`E_fit = {(game, rules, variant, s, a) : s in S_fit and a in Legal(s)}`

and `O_fit` as the subset of those exact state-action edges that occur in the
predeclared fitting trajectories/windows. The exact-state action support rate
is `|O_fit| / |E_fit|`. If `E_fit` is empty, report `not_defined`; do not emit
zero or one. This is a descriptive property of the realized fit bank, not a
quality estimate, data-sufficiency threshold, or model-based OOD detector.

For each edge, retain occurrence count, distinct episode count, policy-pair
count, and seat/actor counts. Publish aggregate histograms by game, variant,
ply/phase, and policy family; do not publish labels or use terminal outcomes
to define the support key. Report the legal-but-unobserved edge count
explicitly. Terminal transitions, forced Reversi passes, and window-tail
masking need separate enumerated counts.

Exact keys include rules version and board dimensions. Report raw exact keys
first. Role-normalized and spatially canonical counts may be secondary only
after the adapter's transformations are shown to preserve legality and exact
transition semantics. Such canonicalization is descriptive; it must not merge
training examples or alter the frozen 928-window selection.

### 2. Root decision-set coverage

For every frozen evaluation root, the required denominator is the complete
exact legal root action set. Report the number of legal root actions, the
number receiving a valid candidate score, and the number receiving an oracle
or reference score. Stratify by actor, game/variant, occupancy band, and
predeclared tactical flags. A timeout, invalid action, incomplete search, or
missing arm remains an explicit missing/failure row; it is not removed from
the denominator. Preserve the predeclared primary match metric and all frozen
nomination rules.

This root denominator does not imply that every interior node or every
root-to-leaf sequence was searched. At interior nodes, report materialized
nodes, exact legal-action opportunities at visited states, expanded edges,
terminal/pass edges, alpha-beta cutoffs, and budget-stopped branches. Label
`expanded / available-at-visited-states` as conditional search expansion, not
full-tree counterfactual coverage. Keep node visits, distinct states, edges,
model calls, and exact transition calls as separate counts.

### 3. Training-support match for evaluation branches

On training-size variants only, attach each frozen evaluation edge to its raw
exact state-action support count, then report results in predeclared buckets:
zero, one episode, and multiple independent episodes. Freeze the exact bucket
boundaries before model outcomes are opened. If the evaluation state's exact
key is absent, count it as an unseen state; do not reclassify it as an
unsupported action at a known state.

The primary V2.12 development variants are held-out board sizes, so exact
state-action keys cannot match the fit variants by construction. Report that
as structural holdout and set exact support to `not_comparable`. Do not
manufacture a cross-size “support rate” by dropping dimensions or by hashing
only action IDs. Any future dimensionless context/action bins must be
game-aware, justified from rules, fixed before data generation, and labelled
descriptive strata rather than an OOD detector.

## Prediction quality on counterfactual actions

If a later reviewed evaluation includes a latent-prediction diagnostic, use a
fixed prehashed set of root-action edges and action prefixes. For each scored
edge, compare the predicted latent after the supplied exact legal action(s)
with the EMA target encoder applied to the exact state reached by the rule
adapter. Report latent error by horizon, root, action class, and the support
category above where comparable. For held-out sizes, report errors by frozen
game-aware strata without claiming data support.

Latent error is not a decision metric. Pair it with the existing exact or
bounded-reference action regret and action-ranking agreement, using the same
roots, actor perspective, depth, legal-action order, and compute budget. Do
not infer useful action sensitivity from distance between predicted latents
alone. Exact rule transitions may be used to build an audit/evaluation target;
they do not become additional JEPA training targets unless a new method
version explicitly says so and receives independent review.

## Denominators, sampling, and failure handling

- Freeze the root schedule, legal-action ordering, seed for any interior-edge
  sample, action-prefix construction, common cap, and tie handling before
  model scoring.
- Prefer every legal root action. If exhaustive interior enumeration does not
  fit the reviewed compute cap, use a deterministic, predeclared sample and
  report its inclusion rule and the unsampled population size. Do not replace
  cap-stopped branches with easier samples.
- Keep terminal positions, forced passes, and no-legal-action transitions
  under explicit rules-based categories. Do not silently count a forced pass
  as a missing action.
- For each metric give `eligible`, `scored`, `missing-by-reason`, and the
  denominator. If no valid denominator exists for a stratum, report
  `not_estimable`.
- Do not tune method, support buckets, roots, or the evaluation sample from
  these diagnostics. Apply the method spec's multiplicity and nomination rules
  to decision metrics; descriptive support summaries are not extra selection
  criteria unless a reviewed version predeclares them as such.

## Rationale and limits

Alrasheed et al. compare expert action sequences against random alternatives
using a fixed imagined horizon, and report prediction and action ranking as
separate measures. Their continuous robot goal-reaching setting does not
validate these definitions for adversarial board games; it supports the
general design choice to connect imagined-state diagnostics to direct
decision-ranking evidence. See their [primary paper](https://arxiv.org/html/2609.39235v1),
Sections 3–5.

This draft does not specify the minimum corpus size, support-rate threshold,
interior sample size, or any new training arm. Resolve those only after the
episode/split matrix, held-out-root protocol, common compute budget, and exact
target-generation semantics are reviewed together. Until then, V2.12-04 and
its existing gates remain unchanged.

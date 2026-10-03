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

Compute the behavior-support ledger from the selected fit windows before any
model is fit. Keep **encoder-state exposure** separate from **observed
transition support**. Encoder exposure counts exact nonterminal root/target
states actually encoded for losses. It does not create legal action
opportunities for the dynamics-support denominator.

For each selected window, every horizon `k` with a valid nonterminal target
(`m_k=1`) contributes its full exact recorded transition prefix to `T_fit`.
`T_fit` is the deduplicated set of exact `(game, rules, variant, s, a, s')`
transitions in those prefixes. If one recorded edge contributes to multiple
valid horizons or overlapping selected windows, count its occurrences
separately but count its exact edge once in the support set. Keep terminal-
masked final edges in a separate terminal-transition ledger; do not silently
classify them as ordinary unobserved actions. Confirm this derivation against
the eventual trainer's actual loss mask and unroll implementation before
corpus generation, since no V2.12 trainer exists yet.

At intermediate plies the predictor receives its own `zhat`, not an encoder
output for the exact corresponding state. Therefore `T_fit` describes the
recorded rule-transition prefixes used to supervise prediction; it is not a
density estimate over the predictor's latent recurrent inputs.

For each source state `s` represented in `T_fit`, let `A_fit(s)` be the set of
distinct legal actions represented by those transitions, and `n_ep(s)` the
number of distinct fitting episodes contributing an edge from `s`. Per-state
observed-transition coverage is `c(s) = |A_fit(s)| / |Legal(s)|`; report its
full distribution and stratify by `n_ep(s)=1`, `n_ep(s)>=2`, and observed
policy-pair/seat diversity. Also report distinct observed edges and distinct
unobserved legal edges. States only used as root/target encoder inputs belong
in the separate exposure ledger, not in this dynamics-support denominator.

Do not headline the pooled ratio
`sum_s |A_fit(s)| / sum_s |Legal(s)|`: repeated states can dominate it, and
its magnitude changes mechanically with game branching factor. If retained
for debugging, label it pooled, give the per-game/variant value and state
frequency distribution, and never use it as a sufficiency threshold. None of
these support summaries estimates prediction or playing quality.

For each observed edge, retain occurrence count, distinct episode count,
policy-pair count, and seat/actor counts. Publish aggregate histograms by
game, variant, ply/phase, and policy family; do not publish labels or use
terminal outcomes to define the support key. Terminal transitions, forced
Reversi passes, and window-tail masking need separate enumerated counts.

Exact keys include rules version and board dimensions. Report raw exact keys
first. Role-normalized and spatially canonical counts may be secondary only
after the adapter's transformations are shown to preserve legality and exact
transition semantics. Such canonicalization is descriptive; it must not merge
training examples or alter the frozen 928-window selection.

For a canonical transition-support count, transform the complete edge
`(s, a, s')` with one and the same spatial mapping; never canonicalize the
state and action independently. Verify both that the mapping sends the full
legal-action set bijectively to the transformed state's legal-action set and
that it commutes with the transition,
`T(g(s), g(a)) = g(T(s, a))`. A role swap relabels both board pieces and the
side to move while leaving the spatially mapped action unchanged; rules,
dimensions, and game identity remain part of the key. Forced pass id 64 must
remain fixed. Keep raw exact-edge counts primary even when these checks pass.

The current `two_player/v212_trajectory_audit.py` canonical-window signature
does map each action using the same spatial mapping as its states and then
checks role-swapped paths. That routine detects duplicate ordered windows; it
does not implement the proposed per-edge support ledger or by itself verify
the adapter-wide legal-set and transition-commutation properties. Treat the
canonical edge statistic as unavailable until a dedicated audit verifies
those properties for every in-scope game variant.

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

#### Root action score semantics under alpha-beta

The current compute-only runner carries the incumbent root `alpha` between
root actions, records each returned value in a temporary iteration map, and
discards that map after choosing the action. A later root action whose branch
fails low may therefore have only an upper bound, not an exact depth-limited
minimax value; a completed search iteration does not make every root-action
entry an exact score. This follows from the current
[`run_root_arm` implementation](https://github.com/dakiemdarktharr/caissa-jepa/blob/main/two_player/v212_pilot.py)
and the standard alpha-beta bound semantics described by
[Knuth and Moore (1975)](https://doi.org/10.1016/0004-3702(75)90019-3).
The frozen compute-only pilot does not publish these temporary values, so this
is a future diagnostic contract issue, not a correction to pilot results or
the selected-action contract.

For any future all-root-action diagnostic, report each entry's status as
`exact`, `upper_bound`, `lower_bound`, or `missing` and retain its search
window/bound provenance. Do not rank bounds as point estimates or calculate
point-valued regret from them. Report pairwise order only when the available
bounds establish it; otherwise mark the comparison unresolved. If the intended
metric requires exact scores for all legal root actions, the protocol must
predeclare a full-window per-action or exhaustive diagnostic, its distinct
compute accounting, and its failure rule. Decide this before fitting or model
scoring; no diagnostic budget or estimand is frozen by this clarification.

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

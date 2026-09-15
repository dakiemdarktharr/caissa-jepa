# MARS-JEPA Chess research protocol, version 2

The canonical scope and compatibility boundary are defined in
[RESEARCH_IDENTITY.md](docs/RESEARCH_IDENTITY.md). This protocol supersedes the
historical three-JEPA roster and minimum-over-replies inference description.

## Data and history

Version-2 research audit plans bind actual shard SHA-256, byte/row/position
counts, unfinished rows, code identity, source hashes, licenses and deterministic
train/validation/locked-final-test assignments. Canonical game identity combines
normalized move sequence and stable event provenance; an additional trajectory
identity detects copies with changed headers. Game/event groups remain together.

Before any split, duplicate games and positions are counted. Held-out records
own shared positions; conflicting records in earlier splits are quarantined,
including records whose future targets overlap held-out positions. Context and
H1/H2/H4 targets are included in overlap checks. The gate rejects empty splits,
invalid transitions, unknown licenses and stale fingerprints. Every exclusion
has a reason and source identity. Final-test records never enter training caches.

Legality validation covers all six FEN fields, including en-passant and clocks.
FEN cannot reconstruct repetition history. Existing encoders retain their
compatibility feature shapes and omit clocks/history. Exact chess rules and a
full-history independent referee determine terminal outcomes. Models must not
be described as fully history-aware. JEPA uses absolute board/action coordinates;
no geometric augmentation or side-to-move board symmetry is currently applied.

## Objectives and response aggregation

The registered ablations are H1, H1/H2, H1/H2/H4, no-response, LeJEPA-inspired,
direct policy/value and local NNUE-style. H1 predicts a state after our action;
there is no opponent reply inside a one-ply target. The response-aware hypothesis
is tested by the longer-horizon variants. Disabled predictors remain allocated
for checkpoint compatibility; allocated parameter matching is not active-FLOP
matching. Training and inference time must also be matched and reported.

The chosen mismatch resolution is restriction to the learned behavioral response
policy: H2 branch values are averaged using the current policy head on the actual
post-action state. The historical policy objective is a margin loss, so its
softmax probabilities are an **uncalibrated surrogate**, not a calibrated response
likelihood or worst-case estimate. H1 values are negated from next-player POV;
H2 values already have root-player POV. Exact terminal rules override prediction.
H4 remains an auxiliary observed-trajectory objective. Missing targets are
explicitly absent and excluded from the corresponding losses. No counterfactual
outcome labels are invented.

LeJEPA-inspired uses bounded tanh latents and simplified SIGReg quadrature. Its
manual gradients are checked numerically; this does not reproduce the published
method's assumptions or theoretical guarantees.

## Four separate experiment families

1. Representation: horizon target errors, variance/covariance, effective rank,
   norms and at least three-seed stability. No engine-strength conclusion.
2. Policy/value: all-legal top-1/top-5, MRR, NLL, value MSE and tactical/endgame
   strata. WDL Brier/calibration from a declared scalar-to-WDL surrogate must be
   labelled as such; it is not a learned WDL head.
3. Same-search: matched data, model parameters, search, seeds and compute to
   isolate architecture effects. Different search methods cannot establish this.
4. Engine strength: complete systems with their own search, clearly separated
   from architecture causality.

## Confirmatory contract

`confirmatory_protocol.py` implements a fail-closed versioned contract and paired
statistics. Smoke protocols require at least 50 unique legal opening positions;
final protocols require at least 100. The 120 checked-in legal opening fixtures
are synthetic variations of six families and require an independent diversity
review before final confirmation. Merely increasing their count is insufficient.

Pin an independent UCI binary's SHA-256, version, options and analysis time;
freeze checkpoint/configuration/dataset/split identities, at least three model
seeds, and search algorithm/time/node/thread budgets. Every opening/seed receives
a color-swapped pair. Exactly one primary metric is predeclared: paired game
score. Use fixed-sample opening-cluster confidence intervals with a conservative bounded-score envelope, conditional on the tested checkpoint cohort, keeping all seeds
within each opening cluster, and Holm correction for secondary comparisons.
No optional stopping or replacement of failed games is allowed.

Timeouts, illegal moves, cancellations, infrastructure errors and max-ply
truncations are censored/error outcomes, never silent draws. Incomplete pairs
block confirmatory ranking. Only chess-rule terminal draws are draws. The GUI's
continuous arena remains exploratory; a classical display referee cannot make
`ranking_ready` true. Missing or changed dataset identity also blocks confirmation.

## Kill criteria

Freeze the design before opening final-test results. If `full` fails to beat
`h1`, `h1-h2`, and `no-response` with uncertainty intervals under matched data,
parameters, search and compute, narrow the claim to the supported component or
pivot. Report negative results, all failed/censored outcomes and seed variation.
A lower auxiliary loss alone is not evidence of stronger chess planning.

No production training or valid model-v-model result was created in the
hardening task because the dataset was intentionally removed.

The default paired adapter is `research_search.py` (`mars-common-negamax-v1`). It uses the same root-ordering interface and exact negamax for all registered models, with explicit tree-node accounting and measured wall-time overruns. `tools/run_confirmatory.py --validate-only` checks a supplied frozen protocol without playing games. The default manifest is blocked until verified data, checkpoints and referee configuration are supplied.

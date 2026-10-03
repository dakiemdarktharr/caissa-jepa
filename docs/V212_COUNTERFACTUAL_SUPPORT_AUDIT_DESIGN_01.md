# V2.12 counterfactual support audit design 01

**Status: static source/design audit only.** No generated trajectories, labels,
checkpoints, match results, or locked outcomes were read or created. This note
does not amend the reviewed V2.12-04 method, freeze an evaluation protocol,
authorize corpus generation, or authorize fitting.

## Finding

`METHOD_SPEC_V212.md` says that the candidate's only JEPA targets at horizons
1, 2, and 4 are states on the recorded action sequence and that
“counterfactual coverage is measured in evaluation.” The spec separately
lists latent error, oracle regret, and action-ranking agreement, but does not
define a counterfactual-support metric, its denominator, the legal branch
population, or how missing support is reported.

The distinction matters because training applies the predictor to recorded
actions, while the max/min planner can query it for exact-legal actions that
were not selected by the data policies. This is a distribution-support
question and an evaluation-definition gap. It is not evidence that a model
will fail, that a dataset leaks, or that JEPA is inferior.

## Source evidence

- In `two_player/v28_data.py`, `_build_records_unchecked()` constructs model-
  facing records from each recorded action and its recorded next action,
  producing H1/H2 targets. `_closure_keys()` separately enumerates every
  legal action and reply, but `audit()` uses those states as overlap keys for
  component assignment and leakage checks. The `counterfactual_branch_states`
  and `unique_branch_keys` receipt fields count that closure; they do not mean
  the predictor was trained on those branches or that its quality was scored
  there.
- `two_player/v212_trajectory_audit.py::audit_trajectories()` validates the
  supplied path, forms windows from its recorded actions, and checks state
  overlap. It does not enumerate the exact-legal counterfactual tree.
- `METHOD_SPEC_V212.md` already requires oracle regret, action-ranking
  agreement, and latent error by horizon. These are useful decision metrics,
  but they do not by themselves state what constitutes supported versus
  unsupported actions, nor do they establish complete branch coverage.
- The random-weight pilot in `two_player/v212_pilot.py` traverses exact legal
  branches and counts rule/model calls for compute feasibility. Random weights
  have no training support distribution or outcome meaning, so this pilot
  cannot close the coverage question.

## What a later frozen protocol should define

Before generating a V2.12 corpus or scoring a fitted model, a versioned and
independently reviewed protocol should make the following quantities
operational:

1. **Behavior support:** for each training-variant state represented in the
   predeclared train schedule, count occurrences of each exact legal
   state-action pair. Report zero-count legal actions and the number of
   distinct episodes, policy pairs, and seats contributing each observed
   pair. Keep support counts separate from JEPA targets and outcomes.
2. **Canonical support:** report an additional role- and symmetry-normalized
   key only where the game's transform preserves exact transition semantics.
   Retain raw-key counts as well. A canonical collision is a diagnostic, not
   an automatic reason to merge labels or declare support.
3. **Evaluation denominator:** for every frozen development root and each
   declared depth, state whether the evaluation includes every legal branch,
   a complete legal reply closure, or a deterministic sample. Give the exact
   number of eligible and scored edges/prefixes by ply, actor role, game, and
   root. Never count a pruned or unmaterialized branch as evaluated.
4. **Missingness:** distinguish an exact state absent from the training
   trajectories, an observed state with an unobserved legal action, an
   incomplete branch due to terminal/pass rules, and a model evaluation
   missing due to compute cap. Keep all failure and cap-hit rows in the
   denominator accounting.
5. **Held-out board sizes:** exact state-action support is necessarily absent
   when the variant identity differs. Report this as structural holdout, not
   as a numeric support rate. If dimensionless action/context strata are
   proposed, freeze their game-aware features and boundaries before corpus
   generation; label them descriptive strata, not a calibrated OOD detector.
6. **Prediction and decision quality:** where compute permits, compare
   action-conditioned latent error against exact target-encoder embeddings
   and report the spec's existing action-ranking/regret metrics on the same
   fixed roots. Stratify by the predeclared support strata and horizon. Do
   not infer useful action sensitivity from latent distance alone.
7. **Compute and selection:** freeze the root/edge schedule, sampling seed,
   all-arm budget, truncation rule, and multiplicity plan before any model
   outcome is opened. Report full population counts and results for all
   eligible arms; do not select easy or well-supported branches post hoc.

The protocol must also say whether enumeration is only for audit/measurement
or supplies model targets. This note proposes no counterfactual training loss;
using exact transitions to audit support does not silently authorize adding
those branches to the training bank.

## Prior-art implication

Alrasheed et al., *The Planning Limits of Latent World Models* (2026), compare
an expert action sequence with random alternatives at a fixed imagined horizon
and separately measure latent prediction and action ranking. Their robot
goal-reaching tasks and distance-based planner are not zero-sum board games,
so their findings do not transfer as a result for CAISSA-JEPA. They do support
keeping decision-ranking evidence distinct from latent-prediction error and
matching the imagined horizon when interpreting either measure. See the
[primary paper](https://arxiv.org/html/2609.39235v1), especially Sections 3–5.

## Decision and next gate

The current spec already has useful decision metrics, so this finding alone
does not require changing the candidate objective. The missing item is a
predeclared operational definition linking observed-action support, legal
counterfactual evaluation, and the held-out-size limitation. Draft that
definition as a new protocol version and obtain independent review before
corpus generation. Keep V2.12-04 unchanged until that review decides whether
an amendment is necessary. No data generation, fitting, match, or superiority
claim follows from this audit.

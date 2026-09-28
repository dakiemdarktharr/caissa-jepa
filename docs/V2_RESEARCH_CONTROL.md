# V2 adaptive development control

This document records the user's request to keep improving a JEPA model/workflow
toward a credible advantage. Positive performance is the research target, not a
guaranteed stopping condition or permission to relabel repeated validation wins
as independent evidence.

## Sequence

1. Deep primary-source review and rule-only benchmark feasibility.
2. Freeze a versioned candidate family, ablations, equal-opportunity baseline
   search space, data/seed/budget identities and promotion metric before fitting.
3. Train/development cycles may adapt using development results. Every attempted
   model, configuration and failed run stays in an append-only ledger. A new
   cycle records which observations motivated each change. No final-set feedback.
4. Freeze a finite shortlist before model-selection evaluation. Choose on that
   distinct set with multiplicity/selection caveats. Previously exposed transfer
   domains remain development diagnostics; they cannot become untouched tests.
5. Freeze one candidate and baseline configurations, training seeds and a new
   independently audited final protocol. Evaluate once. A failed final result
   remains a failure; another design needs new independent data for confirmation.

## Fairness and candidate promotion

All compared methods receive the same legal state/action information and
supervised labels. Any additional unlabeled trajectories or counterfactual
transitions are offered to predictive/reconstruction controls and their collection
cost is reported. Direct policy/value uses the same supervised state coverage;
it is not deliberately restricted to fewer labels or an inferior encoder.

Use two separate budgets: equal examples/optimizer steps to isolate objectives,
and matched measured compute for practical efficiency. Parameter counts alone
are insufficient. Retain a no-model search and untrained-model control. Ablate
the claimed JEPA component and both-player action conditioning. Tune learning
rate/capacity fairly on development, preserving the full baseline search record.

A promising development candidate must improve the predeclared planning metric
against the strongest tuned direct and non-JEPA predictive controls, across at
least two game families and several seeds, with no unexplained failure/censor
imbalance. Report absolute and paired effect sizes and uncertainty; a tiny noisy
win is insufficient. The exact promotion margin must be frozen after the
rule-only benchmark feasibility survey and before candidate fitting.

Low latent MSE, a favorable single seed, a new model name, or winning against
only an untrained/weak baseline cannot promote a candidate. If improvements come
from exact rules, teacher labels, more search or extra compute, attribute them
to those factors rather than JEPA. Publish negative candidates in the ledger.

## Novelty gate

Deep review must distinguish original contributions from combinations or
domain adaptations. A new candidate can be useful without being novel. The
professor dossier must present the nearest prior art, unresolved novelty risks,
specific incremental hypothesis, rigorous comparisons and a reproducibility
package. No claim of firstness or Q1 acceptance follows from development wins.

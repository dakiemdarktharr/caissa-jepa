# V2.5 prospective method review

2026-09-29. Two independent method/model reviews and an evaluation-design review
completed before implementation. **No remaining specification blocker.** This
does not approve an untested implementation or establish scientific benefit.

Resolved before code:

- Scalar consistency now compares the SAME online value head on prediction and
  EMA-encoded target, detaching the entire target branch. An EMA value head
  would mix head lag into the comparator for the fixed-head error bound.
- One global learning rate per family is selected on the original EXACT regret
  criterion and carried unchanged to HYBRID. No per-track retuning.
- Max gradients share exact ties; central differences at3+ tied maxima do not
  verify that chosen subgradient. Use unique-max finite differences and explicit
  analytical/directional/permutation tests at ties.
- Common policy/value uses original complete-group1/K occurrence weights.
  Auxiliary H2 uses eligible nonterminal subset means and then eligible-group
  means. Terminal supervision remains common and terminal planner values exact.
- The conditional oracle bound uses maximum absolute target/oracle reply error,
  not average/MSE. It does not guarantee optimization or generalization.
- Scaled-uniform matches instantaneous forward auxiliary at identical residuals;
  it does not match gradient norm or separate evolving training trajectories.
- Source/data/config fingerprints, same initialization/draws/augmentations,
  active/dormant parameter counts and actual group/fork exposure are required.

The42-cell comparison is a fixed adaptive development experiment, with strong
task-only/scalar/decoded controls and no candidate substitution. MLP dynamics is
a standard shared comparator; V2.4 did not prove its need. Broad novelty is ruled
out by the reviewed robust/value-aware and latent-consistency literature. A
positive result only supports separately gated replication and selection.

Implementation, gradient/data/report/runtime tests, independent source review,
source commit/push and Obsidian synchronization remain gates before training.

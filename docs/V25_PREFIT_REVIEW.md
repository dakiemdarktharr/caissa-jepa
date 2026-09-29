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

## Implementation gate

The separate `two_player_v25/` implementation now passes independent model,
runtime, diagnostic and report reviews. Before fitting, reviewers found and
resolved terminal-H1 oracle consistency, between-cell resource-failure
journaling, and history/report schema drift for new factor/tie diagnostics.
The report replays original-K weighted label denominators, avoiding a silent
change to eligible-subset policy weights. The last cell-ledger write remains
inside deadline acceptance checks. All older source versions remain unchanged.

Verification: full repository **290 tests pass in106.256s**; final focused V2.5
suite **49 pass in10.385s**. Tests include directional/coordinate gradients for
every tensor/allseven families with frozen detached contexts; analytical max-tie
subgradients; actual legal-group sampler/model/report integration; all42-cell
mock runtime paths; and checkpoint/source/data/resource failures. Synthetic
fixtures and mocked updates are engineering evidence only, never research data.
The scalar/model and runtime/metrics reviewers were distinct from their authors.

Next gate is source commit/push and vault mirror, followed by one fresh bounded
attempt at `chess_data/v25-grid04`. No V2.5 research fit exists at this update.

## Prospective monitor repair after grid04 failure

The subsequent attempt failed its memory cap because the inherited monitor
retains ctypes pointer types on every call. V25_GRID04_FAILURE_AUDIT preserves
its costs/exposure and identifies the defect with an independent no-model probe.
V25_RUNTIME_AMENDMENT freezes only a constant-type monitor and scoped source
inventory bindings; two_player_v25r delegates the unchanged model/runtime/report.
Original packages and scientific method hashes remain unchanged.

Verification:58 targeted tests PASS in11.713s (49 original V2.5,9 repair checks).
The new checks cover10,000 measurements without pointer-cache growth, peak field
and Windows ABI, API error propagation, restoration even on BaseException,
non-reentrant/concurrent-use rejection, and exact two-binding source identity.
Four old final checkpoints have192 tensor hashes pinned before any new fit for
a later numerical-neutrality comparison. These are engineering checks, not
comparative research evidence. Independent review/push/vault gates precede the
fresh42-cell grid05; no completed cell from the failed attempt may be reused.

Independent repair review subsequently found no blocker. A separate reviewer
reran all9 repair tests:PASS in0.069s, including10,000 actual Windows measurements.
The hash-only four-checkpoint reference file SHA-256 is
`e6d7a27624cc864fe6edcd8c0b21c9f93e7b239781729684bfc3bafe8a8b5b3c`.
Root also ran the original strict reporter on failed grid04; it returned
inconclusive with `Grid failed or incomplete`, without comparative scoring.

## Independent post-run tooling prepared while grid05 is active

The completed-grid audit tool independently checks exact source Git blobs,
standalone legal closures,480 sampling/symmetry plans,6720 histories,2016 tensors,
all saved decisions and the192 preregistered repair-reference hashes. It must
not execute until all42 cells finish. No audit pass is claimed in advance.

Aggregate export and plotting helpers received separate review. Findings repaired:
unknown nested fields could bypass the initial public-data allowlist; checkpoint
hashes were not cross-bound to run IDs; the600-second boundary was inclusive.
Strict nested schemas, matching receipts and the original strict boundary now
apply. Nine persisted synthetic-only public-report tests PASS in0.472s, including
all42-cell preservation, exact-only tuning and pure saved-value plot extraction.
The independently reviewed tools have not read partial results or rendered figures.

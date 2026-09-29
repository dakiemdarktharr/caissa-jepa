# V2.3 training-only convergence and capacity diagnostic

Frozen 2026-09-29 after Grid03 and the Grid02 value-alignment analysis, before
implementation or new fitting. This is a diagnostic protocol, not a new JEPA
method or a development superiority experiment. The three completed development
grids remain negative under their respective frozen promotion criteria.

## Question and interpretation

Does the present training budget leave substantial improvement in fitting the
available training labels, and does a modest increase in total model capacity
change that conclusion? Large absolute training MSE alone is insufficient:
target variance differs by game/horizon, and current models outperform some
constant references. Existing epoch-20 to epoch-40 losses continue improving.
Moreover, predicted minus encoded value MSE is not an additive dynamics error;
residual/displacement cross terms can cancel. Read V21_VALUE_ALIGNMENT_DIAGNOSIS.

Do not interpret a training fit improvement as generalization, playing strength,
JEPA superiority or a unique architecture. No development, selection or final
artifact is supplied to this runner. No planner, new oracle query, opponent
match or action-scoring schedule is executed.

## Data and unchanged objective

Use only `chess_data/v22-full-01`, fingerprint
`73acd3d11c3a30fa56703d19768d899dff51c6af6ccf2afddc0f5f007d46cc18`.
Require its standalone training role, full labels, seed 271828, passing source/
mask/transition audit and 509 roots / 9,237 nodes / 6,750 forks. It inherits the
original train split and procedural provenance; terminal utility remains free.
The runner accepts no parent-bank or development path. Importing a data-preparation
module is not permission to invoke its parent loader.

Keep the V2.2 model equations, available-label masks, optimizer, EMA 0.99,
gradient clipping, value/policy conventions, variance rule and objective version.
Three families: direct, value-dynamics and raw-jepa. The first two have canonical
auxiliary weight 1; raw-jepa has weight 0.1. Direct still has no trained dynamics.
No new loss or recurrent policy term is added. This isolates budget/capacity
feasibility before considering the architectural proposals in V23_RESEARCH_OPTIONS.

## Finite grid and training schedule

- Capacities (hidden, latent): (64, 32) and (128, 64); projection width remains 16.
  This changes encoder, heads and transition size together, so it is a total-model
  capacity test, not a causal intervention on the encoder alone.
- Families: direct, value-dynamics, raw-jepa; seeds 17, 29, 43.
- One learning rate, 0.001, fixed for every cell. It is the rate selected for all
  three families in the completed fully labeled Grid02. This is not a new rate search.
- 2 capacities x 3 families x 3 seeds = 18 fresh runs. Each trains exactly 160
  epochs, with snapshots at epochs 0, 40, 80 and 160. Do not stop a favorable run
  early or train an unfavorable run for extra steps.
- Batch 128, 16 complete-fork draws per root, balanced game sampling, the same
  epoch-addressed sampling and coherent legal-symmetry augmentation as V2.2.
  Within each seed, indices and transformations must match across every family
  and capacity. All cells use the same state-only root identifiers from V2.2.
  This pairing does not recreate Grid02's older root-ID ordering.
- The nine small-model epoch-40 snapshots must exactly reproduce the matching
  full-label Grid03 online/EMA/Adam tensors and counters. The prefit hash-only
  reference list is `validation/V23_EPOCH40_REFERENCES.json`; bind its hash in
  source identity. It contains no development decisions or targets. All models
  still initialize from their seed, never from these historical checkpoints.
  A mismatch makes the diagnostic inconclusive and stops further interpretation.
- Float64 NumPy, one BLAS/OMP thread, serial cells. Record 8,352 draws and 66
  steps per epoch, totaling 1,336,320 draws and 10,560 updates per completed run.

## Fixed training diagnostics

At each of the four snapshots, evaluate the unaugmented training artifact only.
Reuse only the source-pinned `diagnostic(model, dataset, saved=None, ...)` helper
from `tools/diagnose_v21_value_alignment.py`, never its CLI or inventory loader
(which serve a different, train/development analysis). H1 deduplicates (root, own action),
H2 retains complete (root, own action, reply) paths; missing H2 is counted. Keep
all/nonterminal/terminal strata, transition-weighted and equal-root summaries,
counts and the per-root local receipt. Raw latent MSE has no common strategic
scale across capacities or models. Direct's unused dynamics must remain unscored.

For each game and horizon, define E as the mean squared encoded-value error:
average over nonterminal legal paths within each root, then over roots with at
least one such target. Define the diagnostic scalar S as the equal average of E
over the two games and two horizons. All four cells must have nonzero support.
Also retain predicted-value/oracle MSE and predicted/encoded value discrepancy
for the two trained dynamics families; never label their difference a causal
error decomposition. Initial zero-step snapshots are engineering/fit references,
not untrained playing-strength measurements. At each snapshot also record
unprojected latent effective rank and median/mean dimension standard deviation
on every unique raw training node, separately by game. Label this raw-node
weighting explicitly. A nonfinite diagnostic or a collapse flag (effective rank
below 2 or median dimension standard deviation below 1e-3) makes interpretation
inconclusive; initial snapshots are checked by the same rule.

Retain every epoch's sampling/augmentation receipts, available-label counts,
sample-weighted objective terms and gradient norm. These training-stream means
have a different weighting from S. No bootstrap interval treating training roots
or repeated transitions as independent research replications is permitted.

## Prespecified descriptive decision rules

For each family/capacity/seed, report S at all snapshots and
`r = (S80 - S160) / max(S80, 1e-12)`. A family/capacity is flagged as still making
material fit progress when the median r across the three seeds exceeds 0.05.
Otherwise label it "no material improvement under this threshold", not converged
or optimal. Negative changes and individual seed disagreement remain visible.

At epoch 160, compare small and large capacities within every family/seed using
`c = (Ssmall - Slarge) / max(Ssmall, 1e-12)`. A family has a material capacity
response only when median c exceeds 0.05 and at least two seeds have c > 0.
Report all per-game/horizon effects; pooled improvement does not hide a harmed
game. No architecture is selected as a research winner here. Negative capacity
findings are conditional on the fixed learning rate/optimizer. S measures value
fit and does not establish joint policy convergence or irreducible error.

If any family/capacity still improves materially at 160, state that the budget
may be limiting and require a separately frozen budget decision before another
development grid. If all show little further progress but large capacity helps,
consider a common larger-capacity comparison with equally strengthened baselines.
If neither intervention helps, examine objectives/state representation rather
than blindly extending epochs. These are diagnostic branches, not automatic
permission for an unbounded search or for weakening the original promotion gates.

## Resource, identity and failure gates

Pilot-based linear extrapolation puts small-model training near 51–62 seconds
at 160 epochs, excluding new diagnostics; this is an estimate, not a measurement.
Use a 300-second acceptance limit per cell including diagnostics/checkpoint verification,
5,400 seconds of cumulative cell work and 3 GB aggregate local output. A cap or
nonfinite result makes the diagnostic grid inconclusive; preserve the failed cell
and stop dependent interpretation rather than replacing it. Deadlines are checked
between batches and after diagnostics/checkpoint I/O; NumPy calls are not preempted
by an OS-hard timer. Any measured overrun is a failure and its actual elapsed
time counts toward the cumulative budget. No cloud/GPU spending.

Bind source inventory, frozen specification, actual code commit, config, dataset,
environment, sampler/augmentation and checkpoint identities. Atomic checkpoint
writes preserve the old file on failure. Verify saved online/EMA/Adam tensors and
epoch/update counters. Retain four separately hashed checkpoints per cell at
0/0, 40/2640, 80/5280 and 160/10560 epoch/update pairs (72 snapshots in all),
rather than overwriting intermediate snapshots. Store an active budget journal before fitting; interrupted
work with unaccounted time is not silently resumed or relabeled a fresh successful
cell. All output directories must be new. Original V2/V2.1/V2.2 sources remain
unchanged. Commit and verify this implementation on main before running the grid.

Independent review must confirm training-only artifact access, 18-cell completeness,
all paired schedules/counts, snapshot steps, resource accounting and the stated
descriptive rules. The output cannot nominate a JEPA model: a later development
protocol and genuinely protected evaluation remain necessary.

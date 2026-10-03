# V2.12 no-training compute pilot v02 — expanded sampling proposal

Status: frozen for the expanded no-training pilot after independent
`gpt-6-luna/high` protocol and implementation review. It extends the v01
random-weight instrumentation pilot after that harness and its compute-only
report passed independent review. The first protocol draft requested four
distinct ply-zero roots, which is impossible because the board is the same
initial state for every episode seed. The amended schedule retains one
ply-zero root and allocates five roots at each of plies 8, 16, and 24. This
protocol does not revise the search budget or authorize training, matches,
outcome collection, or model selection.

## Purpose

Measure how much the v01 timing and pruning observations vary across more
synthetic positions and paired random initializations. The v01 sample had only
four roots per board variant and one initialization. Even though its 96 cells
all completed depth four below the pilot safety ceilings, it is too small to
set a common move budget for later fitted models.

## Frozen sampling proposal

- Variants: Connect Four 6x7/k4, Connect Four 8x8/k4, Reversi6, and Reversi8,
  using the project `BoardGame` rules and fixed legal-action order.
- Root plies: 0, 8, 16, and 24. At ply zero, the initial board is unique, so
  retain the single v01 root. At each of plies 8, 16, and 24, retain the v01
  root as ordinal `j=0` and generate four more distinct roots (`j=1..4`). The
  v01 roots use their original scans beginning at `66271 + 1000*v + 100*p`.
  For added roots, let `q` be the index 0..2 of the nonzero target ply within
  `(8,16,24)`, and calculate the disjoint seed-window index
  `k = ((v*3 + q)*4 + (j-1))`, where `v` is variant index 0..3. Scan the 64
  seeds beginning at `80000 + 64*k`. Take the first legal nonterminal state
  at the target ply whose fingerprint has not already been selected for that
  variant. These added windows are mutually disjoint and begin above every
  possible v01 seed. Scan at most 64 consecutive seeds per added root; fail
  before inference if a root cannot be selected.
- Random-weight initializations: `212701`, `212702`, and `212703`; initialize
  once per arm/seed and reuse that immutable model across roots. Preserve named
  paired module seeds for compatible arms. The first initialization is the
  same seed used in v01.
- Arms: the same six v04 arms and model-call definitions as v01. For each
  initialization seed `s`, derive the shared named weights as encoder `s+1`,
  predictor `s+2`, decoder `s+3`, and value head `s+4`, using the v01 fan-in
  scaling. Compatible arms receive identical shared module weights. Initialize
  once per arm/seed and reuse that immutable model across roots.
- Workload: iterative-deepening alpha-beta through four individual plies on
  every root, arm, and initialization. Preserve move ordering, last-completed
  depth behavior, and the first-legal fallback from v01.
- Coverage: 4 variants × 16 roots (1 at ply zero; 5 at each other ply) × 6
  arms × 3 initializations = 1,152 root-arm-initialization cells. Use the
  first scheduled root (Connect Four
  6x7, ply zero, v01 root seed) for one warm-up per arm/initialization; report
  warm-up counters separately from the measured cells.
- Safety ceilings: retain v01's per-cell 500,000 entered nodes, 8.0 seconds,
  and 1.5 GiB sampled RSS. These remain stop limits for this measurement, not
  proposed operating budgets.

The result may contain only root fingerprints and compute instrumentation:
completed depth, stop reason, node visits, exact rules transitions, per-module
and total model calls, wall time, and sampled RSS. Do not retain search values,
selected actions, scores, winners, or outcomes. No training data, checkpoints,
or training/outcome labels may be opened; no parameters may be updated and no
trained checkpoint may be saved.

## Analysis and decision boundary

Verify exact schedule reconstruction, distinct roots, all 1,152 cells,
finite measurements, source and receipt hashes, and forbidden-field absence.
Report nearest-rank p50, p90, p95, and p99 plus maxima overall and by variant,
arm, initialization, and target ply. Preserve censored cells and their stop
reasons; do not silently drop them. Review the report before proposing a
separate common-budget amendment.

This sample still uses synthetic positions and random weights on one host. It
cannot establish fitted-model runtime, playing strength, or universal worst
case. A follow-on budget must use one cap for all arms/variants, define what
happens when depth four is incomplete, and receive independent review before
any data-fitting work. Any cell reaching a safety ceiling means this sample
does not establish a complete-depth compute envelope; stop and version a new
no-outcome plan rather than infer a cap from only completed cells.

## Review gate

The amended sampling schedule and implementation passed independent review.
This permits only the expanded no-training pilot, not budget adoption, data
access, a training grant, or a performance claim. Its receipt and report must
pass independent review before any follow-on budget change.

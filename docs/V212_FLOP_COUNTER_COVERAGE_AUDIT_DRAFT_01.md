# V2.12 training-FLOP counter coverage audit — draft 01

**Status: static source audit only; not a counter, preregistration amendment,
profile, or authorization.** This audit advances the implementation checklist
required by `V212_TRAINING_FLOP_PROFILE_PROTOCOL_DRAFT_03.md`. It reads source
definitions only. No batch was profiled, no training data or labels were read,
and no parameters were updated. The six-arm ≤5% compute gate remains
**untested and unpassed**.

## Scope and counting contract

The proposed profile unit remains one 64-window batched scheduled update under
D03. Count one floating-point add, subtract, multiply, or divide as one FLOP;
a multiply-add is two. Report comparisons, indexing, integer operations,
transcendentals, copies, allocation, and wall time separately unless a
reviewed, fixed conversion is adopted. Dense matrix multiplication of shapes
`[m,k] @ [k,n]` contributes `2*m*k*n` FLOPs under this convention. Reduction
counts must state their summation tree/implementation; do not silently count
MACs, parameter totals, or per-example averages as the panel estimand. The
array expressions written as `x ** 2` need a declared treatment. An approved
independent review accepts counting each fixed-shape array square as one
candidate multiplication per element under a consistent semantic source-level
convention. This does not claim the loaded NumPy power loop executes one
hardware multiply. Scalar bias-correction powers remain separately reported
and are not converted.

## Source-operation inventory

The table maps the current no-update graph and scratch update to accounting
obligations. The named functions are the source anchors; their file hashes,
runtime, numerical libraries, BLAS/LAPACK backend, and thread settings must be
captured at the later freeze. No implementation-specific FLOP claim is made
here.

| Source anchor | Work that belongs in the per-update ledger | Branch or coverage obligation |
| --- | --- | --- |
| `V212Model._encode`, `_value` | Dense projections, bias adds, `tanh` calls and backward derivatives; report each matmul by actual active rows and fixed dimensions | Root encoding is common; future online and target encodes depend on arm and valid-horizon counts |
| Policy head in `V212Model.loss_grad` | Logit projection, bias, stable max/shift, `exp`, normalization, NLL/log, selected-action gradient, and both backward matmuls | Arithmetic operations count as FLOPs; max/comparison/indexing and `exp`/`log` are separate categories |
| `V212Model._regularize` | Batch means, centering, squares, standard deviations, shortfall, covariance matmul, diagonal/off-diagonal work, covariance loss and its gradient | Include this diagnostic/loss path for every arm and update; disclose exact reduction treatment |
| `V212Model._regularize`: `np.linalg.eigvalsh` | The 32×32 symmetric eigenspectrum work, plus spectrum clipping, sum, threshold selection, probability normalization, `log`, reduction and `exp` for effective rank | NumPy 2.4 documents LAPACK `_syevd` for real symmetric inputs. Reference LAPACK `DSYEVD` with eigenvalues-only (`JOBZ='N'`) reduces via `DSYTRD`, then calls `DSTERF`. Netlib reference `DSTERF` bounds its total iteration loop by `30*N` (960 at N=32). This narrows the path, but exact coverage remains **unresolved** until the profile's actual LAPACK implementation/build is pinned and DSYTRD/DSTERF/scale branches have exact counts or a reviewed conservative bound |
| Remaining `V212Model.loss_grad` diagnostics | Root latent mean/std, covariance spectrum output, effective rank, total-loss scalar combination, returned gradient L2 norm, parameter-size aggregation, and finite-value guards | The returned gradient norm is separate from the scratch optimizer's clipping norm and executes once per loss call. Count its coordinate squares/reduction and square root under the declared categories; count comparisons/conversion/serialization separately |
| Recurrent predictor in `V212Model.loss_grad` | For each active step `s`, predictor projection from 104 to 32 coordinates, bias, `tanh`, and its reverse-pass derivative/parameter/input-gradient matmuls | Rows are `_active_prefix_masks(valid)`; count active rows for all four steps, including unsupervised intermediate prefixes needed by later valid horizons |
| Recursive raw-state arm | Per active step, 32→198 decoder projection, decoder bias, 198→32 online re-encoding, corresponding tanh and complete reverse `F→D→E` gradient path | This arm has four possible recurrent steps; actual rows come from the common frozen mask schedule. Static forward MAC inventory is not total training FLOPs |
| Value-only latent rollout | Value head and backward work at each valid horizon | Count valid rows by H1/H2/H4; do not infer work solely from number of valid target cells because shared prefixes execute once |
| JEPA target encodes | Frozen target-encoder projections and `tanh`; target gradients are absent | Multi-step uses valid H1/H2/H4 rows, single-pair H2, single-horizon H1; count actual invocations/rows and distinguish them from active online prefixes |
| Direct-leaf value arm | H4-selected future online encoder, value head, loss and backward projections | Every scheduled batch must have at least one valid nonterminal H4 leaf; the graph rejects a zero-H4 minibatch even when another horizon has targets. The frozen mask schedule must expose this per-batch condition and reject the panel on violation. |
| `preflight_batch` and metric serialization | Mask construction, `np.isin`/finite checks, integer nonzero counting, indexing, Python control flow, and list/dict conversion | Action validation uses `np.count_nonzero(actions, axis=2)` over 256×65 entries per `loss_grad` invocation. It adds no floating-point row-sum reduction; account for the integer/comparison scan separately on every call because structural preflight reruns. Dataset-level exact-rule preflight remains a separate one-time cost under D03 |
| `scratch_adam_ema_step` | Input validation/copies, global gradient-square/reduction, clipping multiplication, first/second moments, bias-corrected Adam, parameter update, and EMA for the three JEPA arms | `tools/v212_optimizer_flop_accounting.py` gives an analytical per-arm formula for this helper and bounds `norm <= 5`/`norm > 5`; zero norm uses the no-division branch. It is a subcomponent only, not an executed counter. Keep scratch arrays disposable; report validation, copies and finite checks outside FLOPs |
| Python scalar bias corrections | `0.9**t` and `0.999**t`, denominator construction and per-update scalar use | Power is not add/subtract/multiply/divide under D03's convention. Report scalar power separately and count any surrounding FLOPs; do not silently convert it |
| Explicit `@` sites in `V212Model.loss_grad` and helpers | Root/task projections, predictor/decoder/re-encoder projections, value/target heads, all explicit reverse-pass matrix products, and covariance/regularizer products | `tools/v212_model_matmul_flop_accounting.py` derives `2*m*k*n` counts from the active horizon masks and shared-prefix union. `np.linalg.eigvalsh`, elementwise/reduction work, and all non-matmul operations remain outside this subcounter |
| Affine bias, `tanh`, and `tanh` derivative sites | Bias vector additions, activation element counts, the square/subtract/upstream-gradient multiply at each explicit `1-z**2` derivative, and separately the value-loss delta scaling before the derivative multiply | `tools/v212_model_activation_flop_accounting.py` derives per-arm counts from the same horizon/active-prefix masks. The upstream array scales are separate to prevent double-counting; scalar coefficient construction and other elementwise loss/gradient operations, nonlinear `tanh` cost, reductions, and eigensolver work remain outside this subcounter |
| Loss residuals and squared-error arrays | Root/direct-leaf MSE, rollout-value residuals, latent/raw target residuals, and repeated square materializations used by per-horizon means plus pooled sums | `tools/v212_model_loss_residual_accounting.py` derives array element counts from horizon masks. Its square report is a subset of the independently reviewed unified square-site inventory, not an additive subtotal. Reductions, scalar weighting, gradients, and other objective work are excluded |
| Objective and diagnostic reductions | `mean`/`sum` input/output shapes, repeated softmax denominator sums, per-horizon skips, bias-gradient reductions, per-parameter gradient-norm reductions, and the root `np.std` path | `tools/v212_model_reduction_shape_accounting.py` emits candidate ordinary reduction additions (`inputs - outputs`) and mean divisions (`outputs`) from masks; effective-rank activity and selected count are explicit. It expands the NumPy 2.4.6 `_std → _var` source path for `z0[64,32]`, axis 0, ddof 0: 2,016 internal-mean additions, 32 mean divisions, 2,048 deviations and squares, 2,016 variance-reduction additions, 32 variance divisions, and 32 square roots. Actual loaded NumPy/kernel identity and summation execution remain unfrozen. These counts need independent review before D03 use |
| Root policy softmax/NLL elementwise work | Legal-logit selection, per-row max comparisons, shifted logits, exponentials, probability divisions, NLL logarithms/residuals, and selected-label gradient subtraction | `tools/v212_policy_softmax_accounting.py` counts the fixed `[64,65]` elementwise path and candidate row-max comparisons. The two denominator reductions and NLL mean remain owned by the reduction inventory; policy/head and gradient matmuls remain owned by the matmul inventory. This source-shape subcounter is not an accepted loaded-kernel trace |
| Root regularizer elementwise and scalar weighting | Centering/shortfall/off-diagonal arithmetic, regularizer-gradient broadcasts and accumulation, root gradient scaling, and scalar objective/metric weights | `tools/v212_regularizer_elementwise_accounting.py` reports candidate elementwise/scalar arithmetic. Reductions, squares, and both dense products are delegated to their existing inventories; `np.maximum`, square root, and linked eigensolver are reported separately or excluded. This is not a loaded-kernel trace or full counter |
| Pooled horizon-objective scalar weighting | Shared root-value gradient coefficient; outcome/target denominator terms; per-horizon scale and target-width divisions; pooled-loss scalar multiplication/accumulation; target-gradient scalar coefficient construction; final pooled-loss combination | `tools/v212_objective_scalar_accounting.py` counts these scalar sites by nonempty horizon masks and rejects direct-leaf schedules without valid H4. After an AST gap review and independent confirmation, all-valid illustrative per-invocation subtotals are 46 / 30 / 46 / 22 / 3 / 30 in frozen arm order. Array arithmetic, reductions, base/root regularizer loss composition, and optimizer work are excluded; do not add this subtotal to a counter that already owns those scalar sites |
| Loss-gradient array accumulations | Explicit policy/root/horizon/recurrent state additions, raw-feature-gradient merges, and parameter-gradient buffer additions | `tools/v212_gradient_accumulation_accounting.py` counts candidate additions per output element under horizon masks, excluding the regularizer-owned root-gradient accumulation. Independent review caught and corrected the initial raw-state omission of `fw/fb` buffer updates: full-valid illustrative counts are now 48,709 / 44,613 / 182,877 / 42,565 / 19,043 / 44,613 in frozen arm order. This source-shape subcounter is not a loaded-kernel trace or full counter |
| Latent/raw target-gradient coefficient multiplication | Elementwise multiply of the scalar gradient coefficient by the target residual before accumulator addition | `tools/v212_objective_gradient_elementwise_accounting.py` counts `valid_rows × 32` for enabled latent targets and `valid_rows × 198` for raw-state targets. Full-valid illustrative counts are 6,144 / 2,048 / 38,016 / 0 / 0 / 2,048 in frozen arm order. An approved read-only review found no overlap with the inspected activation, residual/square, or matmul inventories; this remains a source-shape subcounter |
| Effective-rank selected-spectrum branch | Probability normalization, `log`, elementwise probability/log product, entropy reduction, final `exp`, and selected-set comparisons | `tools/v212_effective_rank_branch_accounting.py` bounds the active-set work after eigensolver/spectrum-sum: per call, zero entropy work when inactive, or K=1..32 divisions/logs/multiplies, K-1 candidate additions and one exp when active. Across 1,740 scheduled updates per arm, upper bounds are 55,680 divisions/logs/multiplies, 53,940 candidate additions and 1,740 exp calls. It excludes DSYEVD/LAPACK and does not establish which branches actually occur |
| Fixed array-square sites | All source `** 2` array expressions in regularization, supervised losses, activation derivatives, recurrent reverse passes, and gradient norm | `tools/v212_model_square_flop_accounting.py` inventories the 20 AST sites and mask-dependent element counts. Under the reviewed semantic convention each element is one candidate multiply; no loaded NumPy power-kernel claim is made. Scalar bias-correction powers are excluded. Existing activation, residual, and latent-`std` reports overlap this inventory and must not be summed with it |

## Candidate additive ownership reconciliation (reviewed for partial ledger only)

The subcounter JSON objects are **not** independent totals. A future aggregator
must use the following owner partition, taking component fields rather than
adding each tool's headline total. `tools/v212_partial_flop_ledger.py`
implements these owners for the currently inventoried source-level components
of one invocation. The ownership is not a complete D03 counter, and no
replay-derived 20×87 total or parity result is emitted.

| Additive component | Sole candidate owner | Remove or do not add from these overlapping reports |
| --- | --- | --- |
| Explicit dense products, including the two covariance products | `v212_model_matmul_flop_accounting.py::all_explicit_matmul_flops` | Do not add the matmul counts reported as delegated by the regularizer inventory. Bias additions are separate and remain in activation. |
| Every model array `** 2` site, including the root-`std` deviation square and all activation/loss/regularizer squares | `v212_model_square_flop_accounting.py::candidate_square_multiplications` | Do not add `square_operation_elements` from the residual inventory, `squares_as_multiplications` from activation, `squared_deviation_square_operations` from reduction, or squared-array counts from regularizer. The optimizer uses `g*g`, not these model AST sites, and remains optimizer-owned. |
| Loss residual subtractions for value/latent/raw-state losses | `v212_model_loss_residual_accounting.py::residual_subtraction_flops` | Ignore that tool's combined `flops_if_each_square_is_counted_as_one_multiply`; its square portion belongs only to the square owner. It does not own policy NLL/label subtractions or tanh-derivative subtractions. |
| Affine bias additions, explicit tanh-derivative `1-z²` subtractions and upstream-gradient multiplications, and value-gradient pre-scaling | `v212_model_activation_flop_accounting.py` component fields | From `tanh_derivative_flops`, subtract `tanh_derivative_breakdown.squares_as_multiplications`; those squares belong to the unified square owner. `tanh` calls and element counts are non-FLOP reporting. |
| Ordinary model reductions (candidate sum additions and mean divisions), excluding effective-rank entropy reduction | `v212_model_reduction_shape_accounting.py::candidate_addition_owner_totals.reduction_inventory` and `candidate_mean_divisions_owner_total` | Schema v04 tags each reduction row with its addition owner and splits the summed additions into ordinary-reduction and effective-rank owners. For root `std`, the records own internal-mean and squared-deviation-sum additions plus internal-mean divisions. Select deviation subtractions and population-variance divisions from `latent_std_candidate_operations.owner_components`; exclude repeated additions, square, and aggregate fields. The square owner handles deviation squares; square roots remain a separate transcendental count. |
| Effective-rank probability normalization, log/probability products, entropy reduction, and final exp after the spectrum sum | `v212_effective_rank_branch_accounting.py::branch_work` | Its `candidate_fp_additions` owns the entropy reduction additions. Cross-check against schema v04's `candidate_addition_owner_totals.effective_rank_branch`; never add that same site from both reports. Do not add the separately listed fixed spectrum-sum reduction twice. The eigensolver itself remains uncounted. |
| Policy softmax/NLL elementwise arithmetic | `v212_policy_softmax_accounting.py::per_invocation` | Use elementwise fields only. Denominator sum and NLL mean work belongs to reductions; policy/head gradient matmuls belong to matmul. Max comparisons, exp/log calls remain non-FLOP categories. |
| Root regularizer elementwise/scalar arithmetic, excluding squares, reductions, dense products, and eigensolver | `v212_regularizer_elementwise_accounting.py::per_invocation` | Use only candidate add/subtract/multiply/divide fields. Its separately named square/reduction/matmul delegation fields are references, not extra work. Keep maximum comparisons and square roots outside FLOPs. |
| Pooled horizon objective scalar arithmetic | `v212_objective_scalar_accounting.py::candidate_fp_scalar_operations_per_invocation` | Do not add loss-array work, reductions, regularizer scalar weighting, or optimizer work. |
| Explicit objective/gradient-buffer array additions | `v212_gradient_accumulation_accounting.py::candidate_array_additions_per_invocation` | Keep its exclusion of regularizer-owned `dz0 += ...`; do not use the regularizer's separately reported accumulation again. |
| Target-gradient coefficient × residual array multiplications | `v212_objective_gradient_elementwise_accounting.py::candidate_array_multiplications_total` | Do not add target residual subtraction, square, matmul, scalar-coefficient construction, or subsequent buffer addition from their other owners. |
| Scratch Adam/clipping/EMA arithmetic, including optimizer `g*g` and both clipping branches' gradient scaling | `v212_optimizer_flop_accounting.py::floating_point_arithmetic` | Do not add its square-root, power, finite-predicate, comparison, copy, validation, or indexing fields to FLOPs. Preserve both clip intervals; zero norm follows `norm_le_5`. |

This ownership partition and partial aggregator do not provide a complete
counter. The independent follow-up found no overlap defect in the components
currently composed, but did not accept them as a D03 counter. The linked LAPACK
eigensolver has no accepted operation bound, and comparisons, integer/indexing,
finite guards, allocations/copies, transcendentals, and source/runtime dispatch
are not fully enumerated. A complete D03 aggregation still requires the
replay-derived 20×87 masks, actual loaded runtime/backend identity, bounds for
all value-dependent work, and a trainer trace proving the scheduled objective
and optimizer calls. Graph freeze remains **NO** and the ≤5% gate remains
**untested and unpassed**.

### Owner-reconciled partial ledger (2026-10-07)

`tools/v212_partial_flop_ledger.py` composes the currently assigned source-level
FP components for one 64-window invocation. It selects only the owner fields
from the partition above, removes the activation/square and residual/square
overlaps, takes ordinary reductions from schema-v04 owner rows, and keeps
effective-rank and optimizer branches as separate lower/upper intervals. Its
regression suite checks component summation, all six arm totals, a masked
fixture, the direct-leaf H4 rejection, and explicit withholding of both parity
and graph freeze. An approved read-only follow-up found no owner/overlap defect
and confirmed the interval is explicitly limited to this source-covered
subset. It requested exact mask-dependent fixture expectations; those were
added for all six arms, and the ledger-level checks now also assert the
mask-invariant policy and regularizer components. The reviewer ran no tests.

For the illustrative all-valid mask fixture, the source-covered candidate
intervals per invocation are 9,540,294–9,540,390 (multi-step JEPA),
7,885,496–7,885,592 (single-pair JEPA), 27,130,644–27,130,740 (recursive
raw-state), 7,038,991–7,039,087 (value-only latent rollout), 4,588,091–
4,588,187 (direct-leaf value), and 7,885,496–7,885,592 (single-horizon
JEPA). Raw-state is a material compute-risk signal within the counted subset.
These are not total FLOPs, are not aggregated over the 20×87 schedule, use no
replay-derived masks, and do not establish the ≤5% pass/fail outcome. The
counter remains incomplete and unreviewed for D03; runtime/reduction/LAPACK,
non-FP work, and trainer/schedule evidence remain open. No research data,
profile, roots, inference, outcomes, or training were used.

The ledger also carries forward the non-FP/unconverted counts already exposed
by its owners: activation-call/element counts, policy comparisons/exp/log
elements, regularizer comparisons/sqrt outputs/eigensolver call count,
effective-rank comparisons/negations/log-output elements and exp-call branch
counts, optimizer comparisons/finite predicates/powers/sqrt output elements
and invocations, and the regularizer's two integer shape multiplications.
These are reported in their native count units; they are not converted to
FLOPs. They do not complete the inventory of
preflight validation, indexing, allocation/copy, Python control flow, runtime
dispatch, or unsupported operators.
An approved read-only follow-up confirmed the log/sqrt fields distinguish
vectorized call invocations from output-element counts and that these are
known-only categories, not a complete non-FP ledger. The reviewer ran no tests.

## Independent source review follow-up (2026-10-07)

An approved read-only source-wide sweep across `_encode`, `_value`,
`_regularize`, `loss_grad`, and `scratch_adam_ema_step` found plausible
source-level owners for the explicit FP arithmetic sites and confirmed the
corrected pooled-objective scalar inventory. This is **not** acceptance of a
complete counter: `np.linalg.eigvalsh` and the linked LAPACK work remain
unbounded for the actual runtime; candidate reduction shapes do not establish
the loaded kernel/tree; per-update comparisons, integer/indexing, preflight,
finite checks, and branch bookkeeping are incomplete; and the objective plus
optimizer are not joined by an integrated trainer trace. Square, residual,
activation, and reduction inventories intentionally overlap and must be
reconciled before any aggregate is reported. Graph freeze remains **NO** and
the ≤5% gate is **untested and unpassed**.

An approved read-only `gpt-6-luna/high` review found an undercount in the
Python scalar gradient-norm reduction. `V212Model.loss_grad` computes
`sum(np.sum(g ** 2) for g in grad.values())`; built-in `sum` starts from zero
and adds each yielded tensor norm, so `k` gradient tensors require `k` scalar
additions, not `k-1`. The inventory and six-arm full-valid illustrative totals
were corrected by one addition per invocation: 58,507 (multi-step JEPA),
50,319 (single-pair JEPA), 186,745 (raw-state), 46,225 (value-only), 36,376
(direct-leaf), and 50,319 (single-horizon). Mean-division totals are unchanged.
The source regression now guards the built-in `sum` call's implicit default
start.

The same independent review conditionally accepts one candidate multiplication
per element for every fixed-shape array `x ** 2` expression as a semantic
source-level conversion. It does not claim that the loaded NumPy power ufunc
executes one hardware multiply; scalar optimizer bias-correction powers stay
separate. A new mask-parameterized subcounter maps all 20 `** 2` AST sites to
arm- and horizon-dependent element counts, including regularizer and
gradient-norm squares omitted by the residual/activation subcounters. For
fully valid illustrative masks, its candidate square-multiply counts are
38,242 (multi-step JEPA), 30,050 (single-pair), 116,712 (raw-state), 25,954
(value-only), 16,002 (direct-leaf), and 30,050 (single-horizon). The residual,
activation, and latent-`std` subcounters overlap these sites; their subtotals
must not be added to this unified square count.

The reviewer accepts `I-O` additions for ordinary reductions and `O` divisions
for mean as analytical candidates under the declared binary-reduction and
divide-by-count conventions. They are not exact counts for an unfrozen loaded
NumPy reduction kernel. The v03 gradient-norm correction is source-consistent.
These narrow dispositions establish neither full-counter coverage nor graph
readiness.

The reviewer found the `np.std(z0, axis=0)` expansion source-consistent for
the current `z0` shape `(64, 32)`, `float64`, and `ddof=0`: two 64-to-1 sums,
elementwise deviation/square, variance division and square root. NumPy's
tagged v2.4.6 Python source calls `_std` → `_var`, with two `umr_sum` calls,
`subtract`, `square`, `true_divide`, then `sqrt`. The tagged C sources contain
the floating-add reduction implementation and pairwise-sum helper. This
supports the operation-site interpretation, not the loaded runtime's exact
dispatch/build or counter acceptance. A local NumPy 2.4.6 wheel/runtime was
unavailable: the attempted PyPI download failed because `pypi.org` DNS could
not resolve. The locked Python 3.11.9 / NumPy 2.4.6 runtime, reduction kernel,
and linked LAPACK therefore remain unverified.

The per-update model `preflight_batch` call remains separate from D03's
one-time dataset-level exact-rule preflight. Count its repeated integer/action
validation scan per model call; report the dataset-level preflight separately.
This interpretation clarifies the audit but does not amend the accepted
profile protocol. No model or research data was run, no profile was made, and
no gate changed.

## Required branch accounting

1. **Mask-dependent graph work.** The frozen per-seed/update mask schedule must
   provide, for each horizon, valid nonterminal, terminal-masked,
   missing/truncated, and invalid-transition counts. Derive each step's active
   prefix rows from the union of downstream valid horizons. The model graph
   rejects invalid transitions and zero-target batches before they enter a
   successful panel; preserve rejection receipts rather than counting them as
   successful updates.
2. **Per-horizon loops.** Loss and value loops skip empty masks and accumulate
   shared reverse-pass gradients. Count loop bodies per executed horizon and
   distinguish rows, calls, and invocation-level fixed work.
3. **Covariance spectrum and effective rank.** NumPy's public v2.4 reference
   identifies `_syevd` for this real symmetric matrix; Netlib's reference
   `DSYEVD` eigenvalues-only path calls `DSYTRD` then `DSTERF`. Netlib's
   reference `DSTERF` bounds its total iterations by `30*N` (960 for N=32),
   which gives a finite reference-loop cap but is not itself an FP operation
   bound. The driver and eigensolver can conditionally scale data, and executed
   iteration work varies with the matrix. Freeze the actual runtime LAPACK
   implementation/build and count that path, or derive a conservative bound
   from its exact source. The
   `spectrum_sum <= 1e-12` branch can skip effective-rank work; otherwise the
   number of eigenvalues selected by `spectrum > 1e-12` can vary from 1 to 32.
   `tools/v212_effective_rank_branch_accounting.py` now bounds the later
   probability/log/entropy branch across all 20 × 87 update slots per arm,
   including its inactive case and all selected counts K=1..32. This remains a
   source-level sub-bound: it does not bound the eigensolver and does not
   attest the active branch sequence in an actual mask/data schedule. The
   actual wheel/backend path is not established by this source audit.
4. **Global clipping.** Bound both sides of the norm threshold for every arm.
   `scratch_adam_ema_step` materializes `grads[key] * clip_scale` on both
   branches, so the per-coordinate multiplication is present for either norm;
   only the scalar `5.0 / gradient_norm` division is exclusive to the greater-
   than-5 branch. `tools/v212_optimizer_flop_accounting.py` now reports these
   branch components separately and an AST regression ties the accounting to
   the current source. Do not use an observed scratch trajectory to narrow the
   preregistered intervals.
5. **Finite/error guards.** Finite-value checks and failures are comparisons
   and control flow, not successful scheduled updates. Record unsupported or
   incomplete paths and never selectively replace a failed seed/update.

## Coverage gaps and next admissible work

- There is no full counter, trainer/update integration, selected-window
  manifest/materializer, exact-rule selected-window replay, frozen 20-seed ×
  87-update mask schedule, or counter/runtime fingerprint.
- `two_player/v212_window_batch.py::windows_to_model_batch` now enforces exactly
  64 windows per invocation. This closes the adapter's batch-size mismatch, but
  does not enforce the schedule's 32-per-game composition, identical batch
  boundaries across arms, or selected-window provenance. The integrated
  trainer and manifest/replay receipt must still establish those conditions.
  An approved read-only review accepts the guard for this narrow adapter
  contract; `preflight_batch` and `loss_grad` remain callable with other batch
  sizes, so trainer integration must prove the guard cannot be bypassed for
  scheduled updates.
- `np.linalg.eigvalsh` is the blocking coverage item: the graph executes a
  32×32 symmetric eigensolver in every arm/update. The pinned NumPy 2.4 public
  docs identify `_syevd`; Netlib's reference `DSYEVD` shows the eigenvalues-
  only `DSYTRD` → `DSTERF` path, including conditional scaling. This is useful
  algorithmic evidence, not proof of the locked wheel's linked implementation
  or its exact count. The effective-rank branch sub-bound starts only after the
  eigensolver and fixed spectrum sum. A frozen implementation trace or reviewed
  full-schedule bound remains required.
- The current model calls `preflight_batch` inside every `loss_grad` call.
  Unlike the one-time dataset-level preflight in D03, the repeated structural
  check scans the 256×65 action entries using integer nonzero counting. The
  former floating-point row-sum was removed without changing the binary
  one-hot acceptance rule; no total-work reduction is inferred. Account for
  this scan and the other comparison/indexing work on every update. Independent
  review must accept the treatment before profile execution.
- The currently available synthetic runtime (NumPy 2.5.3 / Python 3.14.7) is
  not the locked research runtime. No runtime fingerprint, BLAS configuration,
  host identity, counter version, or profile result is inferred from it.

The square-as-multiply semantic convention and candidate ordinary-reduction
shape convention now have narrow independent dispositions; neither establishes
exact loaded-kernel counts. Next, verify the source-expanded `np.std` path
against the locked NumPy runtime, resolve the linked eigensolver and complete
branch bounds, and implement/validate a counter against the frozen objective
and optimizer traces. A synthetic instrumentation check can establish coverage
only; data/preflight authorization, all six reviewed graphs, complete branch
bounds, and separate pre-fit gates remain required before a D03 profile. No
gate opens from this audit.

## Optimizer-only analytical accounting follow-up (2026-10-07)

`tools/v212_optimizer_flop_accounting.py` translates the current scratch
Adam/EMA source expressions into per-arm FP add/subtract/multiply/divide
counts. It includes the global-norm reduction, per-coordinate gradient-scale
multiply on both clipping branches, moment updates, bias correction, parameter
update, and the three JEPA encoder EMA updates. The only value-dependent FLOP
branch in this helper is the optional scalar clip-scale division; the report
gives per-update and 20×87 optimizer-only intervals. Scalar powers, square
roots, finite predicates, and non-FLOP validation/copy work are disclosed
separately.

Three synthetic accounting tests compare parameter and target coordinate/tensor
counts with the six model-arm definitions and assert the arithmetic formulas
and branch interval widths. This is formula validation, not execution of the
optimizer or a FLOP instrumentation/profile. It omits all objective-graph work,
including the unresolved linked-LAPACK eigensolver. Therefore it cannot decide
the ≤5% panel gate or satisfy D03's source/runtime, mask, data/replay, or
independent-review prerequisites. No gate opens.

## Explicit model-matmul accounting follow-up (2026-10-07)

`tools/v212_model_matmul_flop_accounting.py` inventories each source-level
dense `@` in the objective graph and manual reverse pass using `2*m*k*n`.
Inputs are the three 64-row horizon-valid masks; the tool derives active prefix
rows as the union of all valid downstream horizons, matching the graph's
prefix rule. It reports each call site, active rows, forward projection
matmuls, covariance matmuls, and the total explicit-matmul FLOPs. It includes
the raw-state `F→D→E` forward and backward products and the direct-leaf branch.

Four synthetic tests verify the all-valid forward projection inventory against
the existing six-arm MAC audit, assert the current source-level `@` sites,
check masked prefixes/target-encoder rows, and reject malformed inputs. These
accounting tests do not execute the graph; the combined regression command
also ran existing objective tests on synthetic fixtures. For an illustrative fully valid 64-row
batch, the explicit matmul totals range from 4,329,472 FLOPs (direct-leaf) to
26,128,384 FLOPs (raw-state). These are shape-derived matrix-product counts,
not observed work or the frozen training-mask schedule. They omit
elementwise/reduction operations, nonlinearities, the LAPACK eigensolver,
optimizer, preflight, and runtime effects; they cannot decide total parity.
No data, game positions, model graph execution, profile, or training was used.

## Activation and affine-bias accounting follow-up (2026-10-07)

`tools/v212_model_activation_flop_accounting.py` accounts for every affine
bias-add output, each `tanh` element, and the explicit elementwise derivative
`1-z**2` (square, subtraction, and gradient multiplication), using the same
64-row horizon and shared-prefix masks. An AST check in the tests asserts the
four current `np.tanh` source sites. Four synthetic/source tests verify all six
full-valid arm totals, mask-dependent rows, and the value-loss scaling sites.

The follow-up AST guard covers the three value-head gradient scale assignments
and confirms their explicit multiplication structure. The focused
model/optimizer/matmul/activation regression set passes 20/20; `compileall` and
`git diff --check` pass. These synthetic/source checks still do not execute
the graph or establish a full counter.

For an illustrative fully valid batch, bias additions range from 8,384
(direct-leaf) to 73,536 (raw-state), `tanh` element counts range from 4,224 to
18,688, and `tanh` derivative FLOPs range from 12,672 to 56,064. `tanh` itself
is reported separately as a nonlinear call, not converted to FLOPs. These
counts omit other elementwise losses/gradients, reductions, the LAPACK
eigensolver, matmul, optimizer, preflight, and runtime; they do not establish
total compute or parity. The accounting tests use only synthetic masks and do
not execute the graph. The combined validation separately includes existing
no-update model tests on synthetic fixture arrays. No real data or profile was
used, and no gate opens.

### Value-loss gradient scaling correction (2026-10-07)

Source reinspection found a multiply immediately before the tanh-derivative
multiply in each value-head gradient expression: the upstream value delta is
scaled by its loss coefficient. The earlier derivative-only count correctly
covered `z**2`, `1-z**2`, and multiplication by that derivative, but did not
include this separate array scaling operation. The activation subcounter now
reports the upstream scaling multiplications by call site and a combined
activation-gradient array subtotal; scalar coefficient construction remains
outside it. Fully valid illustrative masks add 256 such multiplications for
the recurrent arms and 128 for direct-leaf. This correction changes no method
or objective, and does not cover other elementwise/reduction work or LAPACK.

### Loss residual/square shape inventory (2026-10-07)

`tools/v212_model_loss_residual_accounting.py` counts residual subtraction
elements and squared-error elements for the root objective and the selected
horizon losses. It explicitly counts two square evaluations where source
materializes one for a per-horizon mean and another for the pooled sum; it
does not assume compiler/common-subexpression elimination. The accompanying
four tests check all six full-valid shape formulas, horizon-dependent masks,
malformed masks, and the source sites.

For fully valid illustrative masks, residual-subtraction counts range from
128 (direct-leaf) to 38,272 (raw-state); square elements range from 128 to
76,480. Under the reviewed semantic convention the corresponding residual
square elements are candidate multiplications, but this subcounter is
overlapped by the unified square-site inventory and must not be added to it.
NumPy reduction costs, scalar weighting, gradient-buffer additions,
regularizer/effective-rank work, LAPACK, and remaining elementwise arithmetic
are still excluded. No graph, profile, or data was executed or read.

### Objective reduction-shape inventory (2026-10-07)

`tools/v212_model_reduction_shape_accounting.py` inventories NumPy `mean` and
`sum` calls in the objective and its diagnostics. It includes the two separate
softmax row-denominator reductions, mask-dependent outcome/latent/raw loss
reductions, bias-gradient sums, one gradient-norm reduction per parameter
tensor, and the source-expanded root latent standard deviation. The effective-
rank entropy reduction receives explicit activity and selected-spectrum-size
inputs so its data-dependent range remains visible.

The tool provisionally counts an ordinary reduction of `I` input elements to
`O` output elements as `I-O` additions and a mean as `O` divisions. For fully
valid illustrative masks with 32 selected spectrum entries, these candidate
addition counts now include 4,032 candidate additions from the internal-mean
and variance reductions, ranging from 36,376 (direct-leaf) to 186,745
(raw-state); candidate mean divisions range from 132 to 137. The `std` path
also records 4,096 candidate deviation/square operations, 32 population-
variance divisions, and 32 square roots per invocation. These are not accepted
FLOPs: actual runtime/reduction-kernel identity remains unfrozen, and
eigensolver/LAPACK plus other non-reduction arithmetic remain outside. Source
references: NumPy [v2.4.6 `_methods.py`](https://github.com/numpy/numpy/blob/v2.4.6/numpy/_core/_methods.py)
and [v2.4 `std` documentation](https://numpy.org/doc/2.4/reference/generated/numpy.std.html).
Five synthetic/source tests plus the focused accounting suite pass; no model
batch or data ran.

## Primary implementation references checked

- [NumPy 2.4 `eigvalsh` reference](https://numpy.org/doc/2.4/reference/generated/numpy.linalg.eigvalsh.html): documents `_syevd` / `_heevd` for real symmetric / complex Hermitian matrices.
- [NumPy v2.4.6 `_linalg.py` source](https://github.com/numpy/numpy/blob/v2.4.6/numpy/linalg/_linalg.py): pinned high-level implementation reference.
- [Netlib LAPACK `DSYEVD` source](https://www.netlib.org/lapack/explore-html/d1/da2/dsyevd_8f_source.html): eigenvalues-only code path calls `DSYTRD` and `DSTERF`; source also contains conditional scaling.
- [Netlib LAPACK `DSTERF` source](https://www.netlib.org/lapack/explore-html/d9/df2/dsterf_8f_source.html): documents `MAXIT=30` and at most `30*N` iterations.
- [Netlib LAPACK `DSYTRD` source](https://www.netlib.org/lapack/explore-html/d5/d7a/dsytrd_8f_source.html): dispatch depends on `ILAENV` block size and workspace.

These references establish the documented/reference call path only. They do
not identify which LAPACK binary is linked into a future execution environment,
so the source-level count remains incomplete.

## Follow-up: action-validation accounting (2026-10-07)

The source-level `actions.sum(axis=2)` operation noted above has been replaced
in `preflight_batch` by `np.count_nonzero(actions, axis=2)`, after the same
finite/range/binary checks. The one-hot acceptance rule is unchanged: existing
transitions require exactly one nonzero and absent transitions require zero.
Synthetic regression cases cover valid input, multiple set bits, action bits in
padding, and a nonbinary value. The focused six-module suite passes 28/28;
`compileall` and `git diff --check` pass.

This removes the identified floating-point summation from that validation path;
it does not establish a net runtime or total-work reduction. The count still
scans 256×65 entries per batch, and its integer/comparison implementation must
be represented separately in the eventual counter. No counter/profile,
selected-window data, roots, inference, outcomes, or training ran. This source
change does not address the unresolved linked-LAPACK eigensolver path or open
any D03 gate; the six-arm ≤5% compute gate remains **untested and unpassed**.

## Repeated model-preflight scan cardinalities (2026-10-07)

`tools/v212_preflight_scan_accounting.py` reports source-shaped cardinalities
for the `preflight_batch` call executed by each `loss_grad` invocation. At the
illustrative 64-row shape, the seven numeric arrays passed through finite
checks contain 80,640 elements total. The action array contributes 16,640
entries to `count_nonzero`, 256 output row counts, and 66,560 action-domain
predicate-element evaluations across the four `<`, `>`, `!=`, `!=` checks.
These native cardinalities are reported separately from candidate FLOPs and
are not an estimate of NumPy runtime cost. Predicate totals describe the
successful valid-batch path: Python `or` short-circuits for malformed batches,
so failed inputs may evaluate fewer operands and predicates.

Three focused tests pin these values and the source call sites; the partial
ledger carries the same subinventory for each arm because the invocation's
preflight is shared by all six. The full accounting suite passes 58/58, and
targeted `compileall` and `git diff --check` pass. An approved read-only review
confirmed the counts and scope and prompted the short-circuit qualification;
the reviewer ran no code. This is deliberately incomplete: other
legal/value/actor/transition/mask checks, terminal row scans, indexing,
allocation/copy/control flow, NumPy implementation cost, and the one-time
dataset preflight remain outside it. It does not aggregate 20×87 updates or
change any D03 precondition. No batch/data, profile, or training was run.
Graph freeze remains **NO** and the ≤5% gate remains **untested and unpassed**.

## Runtime observation utility (2026-10-07)

`tools/v212_runtime_observation.py` adds a read-only collector for Python and
NumPy versions/configuration, environment thread controls, platform fields,
and file-backed executable mappings whose path, device and inode can be
matched while hashing the backing file. Its receipt digest is deterministic
for identical collected fields. It reports whether the process versions match
the declared Python 3.11.9 / NumPy 2.4.6 lock.

This is operationally useful inventory only. The collector marks the result
`observational_only` and `execution_bytes_verified=false`: a hash read after
startup does not prove the bytes already executed or currently mapped pages.
The thread fields capture environment requests, not active native threadpool
state; NumPy build configuration and mapped names do not alone prove the
runtime's active BLAS/LAPACK dispatch. The collector imports the relevant
NumPy native modules before taking its mapping list, removes map-order-only
fields, and compares normalized executable segment ranges, permissions,
offsets and backing-object identities before and after backing-file hashing.
The normalized segment inventory is also hashed into the report. This can
detect observed changes but is not an atomic snapshot. Three tests cover maps
parsing, mapped device/inode checks and the explicit
non-attestation contract. A one-off in-memory check on Python 3.14.7 / NumPy
2.5.3 matched 36 mapped executable backing files by path/device/inode at read
time, found equal normalized segment
inventories before and after hashing, and recomputed the digest. The lock-match
flag was false; both NumPy native modules resolved under
`/tmp/caissa-jepa-pv-deps`. No receipt was persisted. This does not clear the
D03 runtime/backend or counter-coverage gate.

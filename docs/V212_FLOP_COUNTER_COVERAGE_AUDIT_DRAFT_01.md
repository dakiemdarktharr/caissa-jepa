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
array expressions written as `x ** 2` also need a frozen treatment: either
count each square as one multiplication under a reviewed semantic rule or
report the power operation separately. Do not assume all exponentiation is
equivalent to scalar bias-correction work.

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
   Provide lower/upper work bounds for all possibilities over all 20 × 87
   scheduled updates. The actual wheel/backend path is not established by this
   source audit.
4. **Global clipping.** Bound both sides of the norm threshold for every arm,
   including the scalar division and elementwise clipping only on the greater-
   than-5 branch. Do not use an observed scratch trajectory to narrow the
   preregistered intervals.
5. **Finite/error guards.** Finite-value checks and failures are comparisons
   and control flow, not successful scheduled updates. Record unsupported or
   incomplete paths and never selectively replace a failed seed/update.

## Coverage gaps and next admissible work

- There is no full counter, trainer/update integration, selected-window
  manifest/materializer, exact-rule selected-window replay, frozen 20-seed ×
  87-update mask schedule, or counter/runtime fingerprint.
- `np.linalg.eigvalsh` is the blocking coverage item: the graph executes a
  32×32 symmetric eigensolver in every arm/update. The pinned NumPy 2.4 public
  docs identify `_syevd`; Netlib's reference `DSYEVD` shows the eigenvalues-
  only `DSYTRD` → `DSTERF` path, including conditional scaling. This is useful
  algorithmic evidence, not proof of the locked wheel's linked implementation
  or its exact count. A frozen implementation trace or reviewed full-schedule
  bound remains required.
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

Next, resolve eigensolver coverage and per-call versus one-time preflight
accounting in a reviewed counter specification. Then implement and validate a
counter against the frozen objective and optimizer operation traces. A
synthetic instrumentation check can establish coverage only; data/preflight
authorization, all six reviewed graphs, complete branch bounds, and the
separate pre-fit gates remain required before a D03 profile. No gate opens from
this audit.

## Optimizer-only analytical accounting follow-up (2026-10-07)

`tools/v212_optimizer_flop_accounting.py` translates the current scratch
Adam/EMA source expressions into per-arm FP add/subtract/multiply/divide
counts. It includes the global-norm reduction, per-coordinate clip multiply,
moment updates, bias correction, parameter update, and the three JEPA encoder
EMA updates. The only value-dependent FLOP branch in this helper is the
optional scalar clip-scale division; the report gives per-update and 20×87
optimizer-only intervals. Scalar powers, square roots, finite predicates, and
non-FLOP validation/copy work are disclosed separately.

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

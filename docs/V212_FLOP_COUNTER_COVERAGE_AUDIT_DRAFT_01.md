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
| `V212Model._regularize`: `np.linalg.eigvalsh` | The 32×32 symmetric eigenspectrum work, plus spectrum clipping, sum, threshold selection, probability normalization, `log`, reduction and `exp` for effective rank | **Unresolved:** current source delegates eigensolver arithmetic to NumPy/LAPACK. Freeze an auditable algorithm-specific counter or conservative full-schedule bound, including backend/runtime identity and convergence/active-set work; otherwise coverage is incomplete |
| Remaining `V212Model.loss_grad` diagnostics | Root latent mean/std, covariance spectrum output, effective rank, total-loss scalar combination, returned gradient L2 norm, parameter-size aggregation, and finite-value guards | The returned gradient norm is separate from the scratch optimizer's clipping norm and executes once per loss call. Count its coordinate squares/reduction and square root under the declared categories; count comparisons/conversion/serialization separately |
| Recurrent predictor in `V212Model.loss_grad` | For each active step `s`, predictor projection from 104 to 32 coordinates, bias, `tanh`, and its reverse-pass derivative/parameter/input-gradient matmuls | Rows are `_active_prefix_masks(valid)`; count active rows for all four steps, including unsupervised intermediate prefixes needed by later valid horizons |
| Recursive raw-state arm | Per active step, 32→198 decoder projection, decoder bias, 198→32 online re-encoding, corresponding tanh and complete reverse `F→D→E` gradient path | This arm has four possible recurrent steps; actual rows come from the common frozen mask schedule. Static forward MAC inventory is not total training FLOPs |
| Value-only latent rollout | Value head and backward work at each valid horizon | Count valid rows by H1/H2/H4; do not infer work solely from number of valid target cells because shared prefixes execute once |
| JEPA target encodes | Frozen target-encoder projections and `tanh`; target gradients are absent | Multi-step uses valid H1/H2/H4 rows, single-pair H2, single-horizon H1; count actual invocations/rows and distinguish them from active online prefixes |
| Direct-leaf value arm | H4-selected future online encoder, value head, loss and backward projections | Exact H4-valid row count; if zero, source skips the leaf path, while the arm's fixed-batch validity rule rejects a zero-H4 minibatch |
| `preflight_batch` and metric serialization | Mask construction, `np.isin`/finite checks, reductions, indexing, Python control flow, and list/dict conversion | Comparisons, integer/indexing work, and data movement are reported separately. D03 treats one-time preflight separately; reconcile that with the current per-call validation before a profile freeze |
| `scratch_adam_ema_step` | Input validation/copies, global gradient-square/reduction, clipping multiplication, first/second moments, bias-corrected Adam, parameter update, and EMA for the three JEPA arms | Count every trainable coordinate each update. Bound both `norm <= 5` and `norm > 5`; zero norm uses the no-division branch. Keep scratch arrays disposable; report validation, copies and finite checks outside FLOPs |
| Python scalar bias corrections | `0.9**t` and `0.999**t`, denominator construction and per-update scalar use | Power is not add/subtract/multiply/divide under D03's convention. Report scalar power separately and count any surrounding FLOPs; do not silently convert it |

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
3. **Covariance spectrum and effective rank.** The `spectrum_sum <= 1e-12`
   branch can skip effective-rank work; otherwise the number of eigenvalues
   selected by `spectrum > 1e-12` can vary from 1 to 32. Provide lower/upper
   work bounds for all possibilities over all 20 × 87 scheduled updates. The
   eigensolver itself is also backend-dependent and currently unbounded by this
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
- `np.linalg.eigvalsh` is the blocking source-level coverage item: the current
  graph executes it in every arm/update, but neither the protocol nor this
  source identifies an algorithm-specific FLOP count or a reviewed upper
  bound. The fixed 32×32 input shape alone is not sufficient evidence for an
  exact backend operation trace.
- The current model calls `preflight_batch` inside every `loss_grad` call,
  while D03 describes one-time preflight separately. Its successful-path FLOP
  contribution is likely zero under the add/subtract/multiply/divide metric,
  but comparison/indexing and repeated validation costs need explicit table
  treatment before profile execution.
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

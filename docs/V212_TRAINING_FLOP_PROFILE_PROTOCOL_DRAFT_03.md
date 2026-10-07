# V2.12 six-arm training-FLOP profile protocol — draft 03

**Status: accepted as a preregistration for v06 only; no profile is authorized
or run.** Draft 02 was accepted for the prior v05 method and is superseded by
this draft for v06. This document defines prerequisites for measuring the
current v06 six-arm training-compute gate. It does not authorize reading or
generating trajectories, roots, labels, scores, or outcomes; it does not
authorize inference, fitting, parameter updates, or an empirical claim. The
≤5% gate remains **untested and unpassed**. Drafts 01 and 02 are retained as
review history.

## 1. Question and estimand

The question is whether total forward-and-backward training FLOPs are within 5%
across all six frozen arms under the common V2.12 training schedule. For arm
`a`, seed `s`, and scheduled update `u`, let `C[a,s,u]` be the counted FLOPs.
The primary total is `F[a] = sum(s=1..20) sum(u=1..87) C[a,s,u]`. Report
`(max_a F[a] - min_a F[a]) / min_a F[a]`; the gate passes only at or below
`0.05`. Report per-seed and per-update diagnostics, but they do not replace the
pooled 20-seed × 87-update estimand. A smaller representative schedule is
inadmissible unless an independent reviewer accepts a proof that its count is
exactly invariant to omitted seeds and updates, including every branch below.

The denominator for each `C[a,s,u]` is one scheduled update, including the
arm's full batch of 64 (32 windows from each game), all root and active-horizon
graph work, loss and gradient computation, global-norm clipping, Adam update
arithmetic, and EMA update arithmetic where specified. Initialization and
one-time preflight are reported separately and are not silently spread over
updates. Diagnostics executed by the training graph—including covariance
eigenspectrum and effective-rank calculation—are included.

FLOPs count one floating-point addition, subtraction, multiplication, or
division as one operation; a multiply-add is two. Report transcendental,
comparison, indexing, and integer operations separately unless the selected
counter has a documented, consistently applied conversion. Explicitly report
scalar powers/bias correction, zero-norm branch handling, and unsupported
operators. MAC-only counts, parameter counts, wall time, and hardware
utilization cannot substitute for total training FLOPs. Disclose the counter
implementation, version, coverage, conversion, and unsupported operators
before measurement. Bound omitted floating-point work tightly enough to make
the ≤5% pass/fail decision invariant to uncertainty; unchanged arm ordering
alone is insufficient.

## 2. Required freeze before profile execution

Before profile execution, freeze and hash:

1. v06 method and all six arm graphs, including common initialization,
   target-encoder calls, exact terminal/truncation behavior, and diagnostic
   outputs;
2. forward, loss, manual-backward, and the exact v06 clipping/Adam/EMA update
   implementation. Actual training semantics use zero-initialized persistent
   moments with one-based `t=1..87`; the profile uses zero moments reset per
   scheduled batch, `t=u`, online-initialized EMA scratch targets, and discarded
   parameter/target outputs. Freeze norm computation, global clipping scope,
   zero-norm scale `1`/no-division behavior, scalar powers and
   bias-correction work for every update, EMA routing/timing, and all other
   choices in `docs/METHOD_SPEC_V212_V06_ADAM_EMA_AMENDMENT.md`;
3. runtime, numerical libraries, BLAS backend/thread settings, counter
   implementation/version/coverage, hardware identity, unsupported operators,
   and any frozen conversion for non-FLOP work. Specify treatment of scalar
   powers, comparisons, indexing, and integer operations, including whether they
   are reported separately or converted;
4. a roster of exactly 20 paired seeds and, for each seed, the deterministic
   87-update batch order, update boundaries, and mask schedule;
5. per-horizon valid, terminal-masked, missing/truncated, and
   invalid-transition counts for every arm and scheduled update. For every
   direct-leaf batch, the frozen schedule must additionally show at least one
   valid nonterminal H4 leaf, matching the current graph's explicit guard;
   generic nonzero-target validity is insufficient for that arm.

All selected windows must first pass the v06 exact-rule replay and preflight
requirements. A malformed or invalid selected transition, prohibited
zero-target batch, mismatched mask, nonfinite value, or changed batch boundary
rejects the entire panel before profile comparison. No arm may skip scheduled
batches or updates, bypass method-required operations, or receive a different
mask or batch. This does not prohibit v05 per-example masking retained by v06 or
active-prefix execution. Counters must distinguish per-example executed calls
and work from per-invocation work.

`two_player/v212_window_batch.py::windows_to_model_batch` now rejects any input
whose length is not exactly 64. The integrated trainer must preserve this
guard, and the selected-window manifest and replay receipt must prove the same
batch boundaries for all arms and updates. This adapter check does not establish
the required 32-windows-per-game composition, selected-window provenance, or
the frozen 20×87 schedule. An approved read-only review accepts this guard for
the adapter's 64-window contract. `preflight_batch` and `loss_grad` still accept
other sizes for synthetic/model-level use, so the trainer must prove that every
scheduled model invocation passes through this adapter or enforce the same
size at its own boundary.

The direct-leaf H4 condition is an implementation-level rejection rule already
enforced by `two_player/v212_model.py`; it does not change v06 target semantics
or authorize materializing a schedule. Record violations and stop before any
profile comparison rather than dropping or replacing affected batches.

Every FLOP table must label units explicitly. The primary table reports
**FLOPs per batched invocation** for one 64-window scheduled update and
**FLOPs per scheduled update** (the same value, with all update components
included). Any per-example average is derived by dividing that invocation's
count by 64 and labeled **FLOPs per example, descriptive only**; it is not the
gate estimand. Call-count tables distinguish invocations from active rows.
Report the mask and transition counts above for every seed, update, and arm so
shared exposure and arm-specific operation counts remain auditable.

The current repository has a no-update NumPy objective/manual-gradient graph
and a pure one-step scratch Adam/clipping/EMA helper in
`two_player/v212_scratch_optimizer.py`. An independent read-only code review
confirmed that the helper's formulas are coherent with v06 and that EMA is
routed to exactly the three JEPA arms; four focused synthetic-array tests cover
the equations, immutability, and all six routing cases. The helper is not integrated
with the objective graph or a trainer. Data materialization, selected-window
manifest, exact-rule replay runner, and full training FLOP counter are also
absent. Therefore no profile can currently satisfy this protocol. A structural
run on synthetic arrays could test instrumentation coverage only; it cannot
establish the v06 panel gate or represent the frozen selected-window mask
schedule.

An analytical optimizer-only subcomponent is now present at
`tools/v212_optimizer_flop_accounting.py`. It computes source-derived Adam/EMA
arithmetic intervals from the six arms' trainable/EMA shapes and the clipping
branch, with synthetic formula checks. It is not a full counter, is not
independently accepted, and does not change the no-profile disposition above.

A mask-parameterized inventory of explicit model matrix products is also
present at `tools/v212_model_matmul_flop_accounting.py`, covering forward and
manual-backward `@` sites plus covariance products. Its synthetic full-valid
counts and mask fixtures check formulas only. It omits eigensolver and other
objective operations and is not the full counter or an authorization to
profile.

`tools/v212_model_activation_flop_accounting.py` additionally counts affine
bias additions, `tanh` element counts, and explicit `tanh`-derivative
arithmetic by horizon mask. It is another analytical subcounter only; other
elementwise/reduction work, `tanh` cost, and eigensolver coverage remain open.

`tools/v212_model_loss_residual_accounting.py` reports residual subtraction
and square-element shapes. `tools/v212_model_reduction_shape_accounting.py`
reports candidate addition/division cardinalities for ordinary means and sums
and makes mask/active-set branches explicit. It now expands the source-level
NumPy 2.4.6 `std` path for the root latent diagnostic. Neither subcounter is
independently accepted as a complete D03 counter. An approved review accepts
one candidate multiplication per element for each fixed-shape `x ** 2` site
under the semantic source-level convention; this does not establish the loaded
NumPy power-kernel trace. The actual NumPy reduction implementation and
linked-LAPACK path remain open.

## 3. Non-fitting execution and branch-bound contract

Protocol approval alone does not authorize data or label access. A future
profile requires separate data/preflight authorization and may use only the
reviewed training-target batch scope needed to exercise the loss graph; it must
not read development scores or locked-confirmatory outcomes. Method, compute
protocol, counter, data/preflight scope, and remaining pre-fit gates require
their own independent reviews before profile execution.

The profile runs in an isolated process with no checkpoint writer and no
persistent training/update state. For each paired seed and arm, every scheduled
batch starts from the frozen initialization; scratch parameter, moment, and EMA
arrays are discarded after that update and never feed a later batch. Record
parameter and target hashes before and after to prove no changes persist.
Forward and backward use the same frozen batches for all arms. Optimizer and
EMA costs must execute the exact v06 arithmetic into disposable scratch arrays
with `t=u`, reset moments, and reset targets as specified in the v06 amendment.

Because this contract does not carry updated parameters or optimizer state
between batches, it does not reproduce an evolving training trajectory and
cannot be used to ignore value-dependent branches. Before any profile, enumerate
all such branches and derive per-arm, per-seed, full-87-update lower and upper
FLOP totals. At minimum, bound both outcomes of the global-norm clipping
threshold branch and all possible active-set paths in covariance/effective-rank
diagnostics. Sum bounds over the frozen updates and all 20 seeds. If another
branch can change FLOPs, include it in the bound. A single-trajectory scratch
simulation is not a substitute for the branch bounds.

For the gate, use the resulting uncertainty intervals conservatively. The
profile passes only if the worst-case ratio
`(max_a upper(F[a]) - min_a lower(F[a])) / min_a lower(F[a])` is at most
`0.05`. It fails only if even the best-case ratio
`max(0, max_a lower(F[a]) - min_a upper(F[a])) / min_a upper(F[a])` is greater
than `0.05`. If all arm intervals share a common value, this best-case ratio is
zero. Otherwise the result is **indeterminate**, so no fit is authorized.
An independent reviewer must accept the interval construction and counter
coverage before the profile; observed representative outcomes cannot tighten
the bounds after inspection.

If faithful optimizer/EMA arithmetic cannot be exercised without persistent
changes, instrument a separately reviewed scratch implementation and prove its
operation trace matches the intended update equations. Do not estimate missing
work from parameter counts or infer it from a different framework. Warm-up is
separate from the primary count. Report per-update and 87-update component
tables by arm and seed, branch-bound intervals, mask counts, source/runtime
fingerprints, and errors or unsupported operations. Wall time, peak memory,
and counter overhead are supplemental feasibility telemetry.

## 4. Stop conditions and interpretation

Stop before interpreting parity if any graph, batch, mask, update equation,
counter coverage, or source/runtime fingerprint differs across arms; parameter
or optimizer state persists; the profile accesses outcomes beyond the
separately approved training-target scope; or an operator/branch is omitted
without a reviewed bound sufficient for the pass/fail decision. Preserve every
failure and partial receipt as incomplete; do not replace failed cells or rerun
selectively.

A complete profile above 5% is a negative compute result. It blocks fitting
under the current v06 six-arm controls. Do not add filler operations, change update
counts, omit diagnostics, or grant unequal work to manufacture parity. Any
control/config revision requires a new version and independent review before
any fit. A passing profile clears only this compute gate; it does not clear
novelty, data provenance, split/leakage, runtime, root schedule,
action-sensitivity, regret, inference-budget, or separate pre-fit gates, and it
establishes no JEPA superiority.

## 5. Current disposition

An approved read-only reviewer rejected draft 01 as a preregistration because
it did not freeze and aggregate all 20 paired seeds × 87 updates and did not
bound value-dependent work under the no-persistent-update contract. It also
requested explicit FLOP-table units. A read-only follow-up accepted draft 02
as a preregistration for v05 and confirmed the interval formulas are valid and
conservative. V06 adopts the independently reviewed Adam/EMA semantics. The
approved reviewer accepts draft 03 as a preregistration for v06 only and
confirms the 20 × 87 aggregation, stateful-training/reset-scratch distinction,
and interval bounds. Draft 03 supersedes draft 02 for v06; the v06 amendment
points to draft 03. This acceptance does not authorize data access, profile
execution, or any other gate. Before execution, freeze the explicit counter
checklist in §§1–2: scalar powers/bias correction, comparisons, indexing and
integer work, conversion/reporting, zero-norm handling, unsupported operators,
coverage, and source/runtime identity. The reviewer ran no tests or profile.
No optimizer dry-run, trajectory replay, fitting, inference, root generation,
score access, or outcome evaluation was performed while drafting this revision.
No measured result or gate changed. The trainer, selected-window
data/preflight, and full-counter prerequisites remain open. Keep the existing
Reversi8 2-second p90 negative and all novelty risks in force.

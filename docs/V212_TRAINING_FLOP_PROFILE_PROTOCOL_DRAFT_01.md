# V2.12 six-arm training-FLOP profile protocol — draft 01

**Status: non-operative protocol draft; not independently reviewed or run.**
This document defines prerequisites for measuring the frozen v05 six-arm
training-compute gate. It does not authorize reading or generating trajectories,
roots, labels, scores, or outcomes; it does not authorize inference, fitting,
parameter updates, or an empirical claim. The ≤5% gate remains **untested and
unpassed**.

## 1. Question and estimand

The question is whether the total forward-and-backward training FLOPs per
scheduled update are within 5% across all six frozen arms under the common
V2.12 training schedule. Report the largest pairwise relative difference
`(max_arm - min_arm) / min_arm`; the gate passes only at or below 0.05. Also
report absolute per-arm totals and per-component counts. Do not average away a
failing arm or compare only the multi-step JEPA and raw-state arms.

The denominator is one scheduled update, including each arm's full batch of
64 (32 windows from each game), all root and active-horizon graph work, loss
and gradient computation, global-norm clipping, Adam update arithmetic, and
EMA update arithmetic where specified. Multiply by 87 updates only as a
separate schedule total; all arms use 87. Initialization and one-time
preflight are reported separately and are not silently spread over updates.
Diagnostics executed by the training graph—including covariance eigenspectrum
and effective-rank calculation—must be included in the measured total.

FLOPs count one floating-point addition, subtraction, multiplication, or
division as one operation; a multiply-add is two. Report transcendental,
comparison, indexing, and integer operations separately unless the selected
counter has a documented and consistently applied conversion. MAC-only counts,
parameter counts, wall time, and hardware utilization cannot substitute for
total training FLOPs. The counter implementation, version, coverage, and
unsupported operators must be disclosed before measurement; any uncounted
floating-point operation that could change cross-arm ordering blocks a gate
decision.

## 2. Required freeze before profile execution

Before creating a profile batch, freeze and hash:

1. v05 method and all six arm graphs, including common initialization,
   target-encoder calls, exact terminal/truncation behavior, and diagnostic
   outputs;
2. forward, loss, manual-backward, clipping, Adam, and EMA implementation;
3. runtime, numerical libraries, BLAS backend/thread settings, counter, and
   hardware identity;
4. deterministic batch order and mask schedule, with per-horizon valid,
   terminal-masked, missing/truncated, and invalid-transition counts;
5. the same 87 update boundaries and 32/32 game balance for every arm.

All selected windows must first pass the v05 exact-rule replay and preflight
requirements. A malformed or invalid selected transition, zero-target batch
where prohibited, mismatched mask, nonfinite value, or changed batch boundary
rejects the entire panel before profile comparison. No arm may skip work or
receive a different mask or batch.

The current repository has only `two_player/v212_model.py`, a no-update NumPy
objective and manual-gradient graph. It has no optimizer, clipping, EMA update
path, data materializer, selected-window manifest, exact-rule replay runner, or
full training FLOP counter. Therefore no profile can currently satisfy this
protocol. A structural run on synthetic arrays could test instrumentation and
coverage only; it cannot establish the v05 panel gate or represent the frozen
selected-window mask schedule.

## 3. Non-fitting execution contract for a future profile

After the method, compute protocol, counter, and remaining pre-fit gates receive
the required independent reviews, the profile must run in an isolated process
with no checkpoint writer or persistent parameter update. Each arm starts from
the same frozen paired seed initialization used by the method. Forward and
backward execute against the same fixed dry-run batches. For optimizer and EMA
cost, compute the exact v05 update arithmetic into disposable scratch arrays,
then discard them; do not feed updated arrays into the next batch. This
measures one-update work without fitting. Record hashes before and after to
prove model and target parameters did not change.

If faithful optimizer/EMA arithmetic cannot be exercised without changing
parameters, instrument a separately reviewed scratch implementation and prove
its operation trace matches the intended update equations. Do not estimate the
missing work from parameter counts or infer it from a different framework.

Use warm-up only for runtime stability, clearly separated from the primary
count. The FLOP counter must be deterministic and cover every operator in the
frozen graph. Report per-update and 87-update component tables by arm, repeated
profile variation if the counter is nondeterministic, mask counts, source and
runtime fingerprints, and any errors or unsupported operations. Wall time,
peak memory, and counter overhead are supplemental feasibility telemetry.

## 4. Stop conditions and interpretation

Stop before interpreting parity if any graph, batch, mask, update equation,
counter coverage, or source/runtime fingerprint differs across arms; any
parameter changes persist; the profile accesses outcomes beyond the already
approved training-target scope; or an operator is omitted without a reviewed
bound showing it cannot affect the 5% result. Preserve every failure and partial
receipt as incomplete; do not replace failed cells or rerun selectively.

A complete profile above 5% is a negative compute result. It blocks fitting
under the current six-arm controls. Do not add filler operations, change update
counts, omit diagnostics, or grant unequal work to manufacture parity. Any
control/config revision requires a new version and independent review before
any fit. A passing profile would clear only this compute gate; it would not
clear novelty, data provenance, split/leakage, runtime, root schedule,
action-sensitivity, regret, inference-budget, or separate pre-fit gates, and
would establish no JEPA superiority.

## 5. Current disposition

No profile, optimizer dry-run, trajectory replay, fitting, inference, root
generation, score access, or outcome evaluation was performed while drafting
this protocol. No result or gate changed. The protocol itself needs independent
review, and the missing implementation and data/preflight prerequisites remain
open. Keep the existing Reversi8 2-second p90 negative and all novelty risks in
force.

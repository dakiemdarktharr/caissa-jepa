# V2.5 runtime repair: prospective fresh attempt

2026-09-29. Engineering amendment after the first bounded attempt failed, before
any replacement fit. Read METHOD_V25 for the unchanged scientific protocol and
V25_GRID04_FAILURE_AUDIT for the failed attempt. This does not change the
candidate, objectives, selection gates, data, optimizer or resource limits.

## Failure and permitted repair

Source5102ea0588198f993874a495d18bfef1e868e2ec launched grid04. Three direct
cells completed; the fourth completed160 epochs but failed during diagnostics
at a process-lifetime peak of1,004,228,608 bytes, above the1,000,000,000 cap.
The whole attempt is inconclusive. Preserve all local artifacts and account for
496.25913929991657 cell seconds, including136.73790700000245 failed-cell seconds.
There is no completed JEPA/control comparison, and partial outcome scores are
not used to choose this repair. Selection/final predictions remain closed.
The ledger's1,254 development decisions count finalized receipts only. The
traceback occurs after the fourth418-decision evaluation passed its completion
check: at least1,672 learned decisions were computed, with418 not saved, plus
836 controls. This inferred extra exposure is retained in the failure audit;
do not describe the ledger counter as all executed predictions.

Independent source reviewers identified that the inherited process_peak_rss
defines a new ctypes.Structure on every call. ctypes.POINTER caches each new
type, retaining it after the call. A bounded monitor-only reproduction confirmed
32 new retained pointer types after32 calls, surviving explicit garbage
collection. The Windows structure layout and peak-memory field are correct;
the defect is the repeated creation and retention of types. The old helper and
all frozen scientific source files remain unchanged for artifact identity.

New package two_player_v25r will define the ctypes structure, pointer type and
Windows function bindings once at module initialization. It must return the
same Windows process-lifetime PeakWorkingSetSize, raise on measurement failure,
and retain no per-call types or history. Do not clear private ctypes caches,
reset process peak memory, disable guards, change limits or mask failures.

Use a scoped binding context around the unchanged two_player_v25 runtime and
report: replace only process_peak_rss and runtime_source, restoring both in a
finally block even on BaseException. Reject nested/concurrent binding contexts;
this is a serial runtime. The new source inventory is the complete original inventory plus
this amendment and every Python file of the repair package. The report uses
the same bindings and verifies this augmented identity. The scientific method,
objective and artifact schemas stay V2.5; the new package/path/source commit
distinguish the engineering attempt. No globals involving learning, sampling,
evaluation, promotion, budgets or input identity may be replaced.

## Acceptance before restart

- Independently audit grid04 failure status, completed/failed/planned counts,
  costs and the monitor-only reproduction; no partial comparative scoring.
- After warmup,10,000 repaired measurements must leave the pointer-type cache
  size unchanged and yield positive, monotone lifetime peaks. Measurement
  failure remains an error; Windows field layout remains explicitly checked.
- Test scoped restoration on success and exceptions, augmented source identity,
  and that runtime/report delegation changes only the two named bindings.
- Run original V2.5 regression checks, review the small repair independently,
  commit/push verified source on main and mirror documents to Obsidian.

Before restarting, save hash-only tensor references for the four grid04 final
checkpoints (including the failed diagnostic cell's trained checkpoint), without
reading outcome scores. After the fresh attempt, independently compare all48
model/EMA/Adam tensors and epoch/step counters for these four same configurations.
Identity metadata/file hashes will differ with the repaired source; the192
numerical tensor hashes must be identical. A mismatch blocks a claim that this
was a numerically neutral monitor repair and requires investigation. Do not
initialize from these references or select checkpoints by this comparison.

Then one fresh attempt at chess_data/v25-grid05 may execute all42 cells from
their original seeds. Recompute controls; do not resume, import trained weights,
reuse completed cells, tune from partial outcomes, add seeds or change160 epochs.
All existing limits remain600s/cell,25200 cumulative cell seconds,3GB output
and1GB lifetime peak RSS. Record failed grid04 cost separately and together with
the new attempt's cost; the retry does not erase earlier compute.

If the repaired attempt violates a limit or another integrity condition, stop
and preserve it as inconclusive. Any further attempt requires another explicit
prospective amendment and causal diagnosis; this document does not authorize
unlimited retries. Only a complete verified42-cell result can be compared using
the original frozen exact/hybrid/mechanism gates.

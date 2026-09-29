# V2.5 grid04 independent operational failure audit

2026-09-29. **The attempt is inconclusive and must not support comparative
research claims.** This audit inspected operational journals, history counters,
source and raw file hashes only. It did not inspect outcome scores/losses, run
model inference, rank partial cells, or execute the completed-grid audit.

## Preserved attempt and costs

Frozen launch source: `5102ea0588198f993874a495d18bfef1e868e2ec`.
Local artifacts: `chess_data/v25-grid04/`. All 31 normalized source files match
both that commit's Git blobs and the current frozen files. All three completed
receipt/checkpoint byte hashes match the ledger without parsing their outcome
contents. Ledger SHA-256:
`f60386efffe3a5de03ee22075b1af4418768944ddab98b4a2f864b05a6a2f0e5`.

| Cell | Status | Recorded cell seconds | Epochs | Updates |
| --- | --- | ---: | ---: | ---: |
| direct-lr0.001-s17 | complete | 125.2624886999838 | 160 | 10560 |
| direct-lr0.001-s29 | complete | 126.4377449999447 | 160 | 10560 |
| direct-lr0.001-s43 | complete | 107.82099859998561 | 160 | 10560 |
| direct-lr0.0003-s17 | failed | 136.73790700000245 | 160 | 10560 |

The other 38 cells remain planned and have no directories. The four histories
preserve 640 epoch records, 42240 updates, 1336320 group draws and 4292139 fork-row
occurrences. A completed optimizer schedule does not make the fourth cell a
completed research cell: its final receipt is absent and its budget is failed.

Recorded cumulative cell cost is 496.25913929991657 seconds, including all
136.73790700000245 failed-cell seconds. It equals the sum of the four recorded
cell costs. Preparation took 7.607825600018259 seconds; total wall time was
503.9463644999778 seconds. These are operational costs, not efficiency results.
Persistent input arrays total 71896300 bytes; retained output totals 17456603 bytes.

The failure was `MemoryError: Frozen peak RSS limit exceeded`. Recorded
process-lifetime peak working set was 1004228608 bytes, exceeding the unchanged
1000000000-byte acceptance cap by 4228608 bytes. This was a deliberate resource
guard exception, not evidence that the OS or NumPy allocator refused an allocation.
Cell/aggregate time and output-byte caps were not the triggered limits.

## Monitor defect: reproduced independently

The inherited `two_player_v23_diagnostic/runtime.py:70` creates a new
`ctypes.Structure` class on every measurement; line 76 requests its pointer type.
Python caches pointer types, so distinct newly created classes produce distinct
retained entries. This behavior is documented in the official
[Python 3.11 ctypes POINTER reference](https://docs.python.org/3.11/library/ctypes.html#ctypes.POINTER).

A fresh Python 3.11.9 subprocess called only the old monitor 2000 times, without
data loading, model execution or fitting. A separate structure/pointer/DLL binding,
created once, measured current and peak working set. Explicit `gc.collect()` ran
before each sample. The diagnostic took 0.16592200001468882 seconds.

| Old monitor calls | Pointer cache entries | Current working set, bytes | Peak working set, bytes |
| ---: | ---: | ---: | ---: |
| 0 | 21 | 29843456 | 29843456 |
| 500 | 521 | 33955840 | 33955840 |
| 1000 | 1021 | 37965824 | 37965824 |
| 1500 | 1521 | 41771008 | 41771008 |
| 2000 | 2021 | 45703168 | 45703168 |

Each call adds one retained pointer-cache entry. Memory grew 15859712 bytes
(about 7930 bytes/call) despite explicit collection. This establishes an allocation
defect in the monitor itself and strongly supports it as the reason repeated
batch guards exhausted the process cap. The completed process was not traced
allocation-by-allocation, so this is not a claim that every byte of its 1GB peak
came from that defect.

The Windows ABI/field interpretation is correct: DWORD 4 bytes, HANDLE/SIZE_T 8,
structure size 72; PeakWorkingSetSize offset 8 and WorkingSetSize offset 16.
Microsoft defines both fields in bytes in
[PROCESS_MEMORY_COUNTERS](https://learn.microsoft.com/en-us/windows/win32/api/psapi/ns-psapi-process_memory_counters).
The defect is repeated type allocation, not a units, field-offset or truncation
error. The measurement is a process lifetime peak, not an isolated model peak.

## Termination and exposure accounting

The traceback reaches `two_player_v25/metrics.py:40`: a guard after the first
game's occurrence representation calculation, called from runtime diagnostics.
The scheduler marked the current cell failed, included its elapsed cost, marked
the grid inconclusive, retained its checkpoint/history/budget, and stopped before
the next planned cell. The orchestrator observed process exit1. Artifact state
independently confirms no continuation into the 38 planned cells.

The orchestrator also invoked the frozen strict reporter on this incomplete
attempt. It returned `inconclusive` with one verification error before partial
scores were analyzed; the rejection report is retained locally at
`chess_data/v25-grid04-report/`.

One bookkeeping limitation remains: ledger `development_decisions=1254` counts
only decisions in the three finalized cell receipts. Runtime reaches diagnostics
only after the fourth cell's evaluator has returned 418 complete decisions and
passed its status/count check. Thus 1672 learned development decisions were
executed, of which 418 were not retained in a final receipt. This is a deduction
from the frozen control flow and traceback, not inspection of those predictions.
There were also 836 control decisions. Additional partial diagnostic computations
are not included in either decision counter. Selection/final counters remain 0.
Future failure reports must distinguish finalized counts from executed exposure;
the original ledger is preserved unchanged.

## Prospective disposition and reproducibility

The [runtime amendment](V25_RUNTIME_AMENDMENT.md) permits one fresh attempt only
after a constant-type Windows monitor passes bounded retention/ABI/error tests.
It preserves the scientific source, all 42 cells, seeds, data, 160 epochs, limits,
and exact-selected comparison gates; no scores from this incomplete attempt are
used to choose a model or reuse a checkpoint. Its scoped wrapper changes only
the memory monitor and source inventory and restores both on every exit.
No scientific/fairness blocker was found in that prospective scope. A future
failure audit must continue to document the exposure-counter limitation above.

After explicit authorization to inspect tensor integrity only, all four final
checkpoints were verified at epoch 160 / step 10560, with 48 finite float64
model/EMA/Adam arrays per checkpoint, valid shapes and stored tensor hashes.
The [neutral-repair references](validation/V25_GRID04_TENSOR_REFERENCES.json)
preserve all 192 hashes, config/source/data identity and checkpoint file hashes,
without arrays or outcomes. File SHA-256:
`e6d7a27624cc864fe6edcd8c0b21c9f93e7b239781729684bfc3bafe8a8b5b3c`.
The prospective fresh retry must reproduce those numerical hashes, without
initializing from them; source metadata and checkpoint byte hashes may change.

Independent source review of the five `two_player_v25r` modules found no blocking
defect in this narrow repair. The Windows structure/pointer/DLL bindings persist
at module scope; the serial context changes and restores exactly the monitor
and source functions, including on exceptions. All nine repair tests were
independently rerun and passed in 0.069 seconds, including 10000 actual repaired
measurements with unchanged pointer-cache size and positive monotone peaks.
These are engineering checks, not research experiments or comparative timings.

The compact public [operational receipt](validation/V25_GRID04_FAILURE_OPERATIONAL.json)
contains costs, counters and hashes without outcome values. Canonical JSON
SHA-256 (sorted keys, compact separators, UTF-8, no nonfinite values):
`7257149c7503173733308d6f86dcd55a5b31c6e5826d5c76d9ea942dfe7b69a5`.
Checkpoint/data/log artifacts remain excluded from Git. No frozen package,
original method, checkpoint or grid artifact was edited by this audit.

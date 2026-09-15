> Historical receipt from recovery commit `223e9ad`. The production dataset was
> subsequently intentionally removed. This document is not evidence from the
> MARS-JEPA Chess hardening task and does not validate current checkpoints.

# Pipeline recovery — 2026-09-13

## Scope

Canonical checkout: `D:\CAISSA-JEPA\source`. The starting commit was `dddd3d3`
and the checkout was clean. The attached handoff was treated as the requested
work specification; its prior results were checked against current files.
No production training or confirmation tournament was started.

## Confirmed failure and correction (P0)

The exact original cache directory name was tested with
`Path.mkdir(parents=True, exist_ok=True)`. Through
`C:\Users\ANHKHOI\AppData\Local\CAISSA-JEPA\fen_dataset`, it raised
`FileExistsError: [WinError 183]`. The same operation at the resolved
`D:\CAISSA-JEPA\fen_dataset` path succeeded. The directory was not visible in
`listdir` before the probe. Evidence:
`build/cache-mkdir-reproduction.json` and
`build/cache-mkdir-path-comparison.json`.

The confirmed failing operation is creation through the junction alias. This
is not a claim about the underlying NTFS/reparse implementation defect.
Cache, writer locks, atomic JSON, checkpoint generation and restore paths now
resolve to the physical destination before writes. Ordinary file collisions
still fail: they are not deleted or hidden. Training failures record full
tracebacks, exception type/filename, and requested/resolved model, report,
generation, latest-pointer, dataset, cache and lock paths. GUI worker errors
also expose tracebacks for failures outside the trainer.

Fallback: use the physical D: dataset path and a new isolated checkpoint root.
Do not change/remove junctions or delete old checkpoints to conceal a failure.
The source and frozen self-tests exercise a real Windows junction, a deliberate
generation-file collision and five-model train/resume on temporary data.

## Dataset integrity and preservation (P1)

A read-only pre-training gate scans all rows and verifies aggregate counters,
shard membership/count, sizes, SHA-256, game-hash uniqueness and completed
status. `TARGET_REACHED` is insufficient by itself. The ingestion writer now
detects stale counters and persists per-shard counts on future writes. It was
not opened against the existing raw data during recovery.

New version: `D:\CAISSA-JEPA\datasets\audited-v1-20260913`.

| Measure | Derived |
|---|---:|
| Games | 90,001 |
| Positions | 8,284,281 |
| JSONL bytes | 4,035,243,006 |
| Shards | 17 |
| Duplicate rows excluded | 2 |

Manifest SHA-256:
`db71651b9ca8a11f4c6b4c675b53b181479a962e05680538439f1b982371b2f6`.
The version is `COMPLETE`, not a claim of reaching 4 GiB. Original raw rows and
manifest were retained. Each input shard was checked against its original
size/hash while deriving. `provenance.jsonl` identifies copied shards and
excluded duplicate locations; `audit_receipt.json` records the complete scan.
A conflicting duplicate aborts derivation. Existing output versions are never
overwritten; interrupted derivation remains unavailable for training.

## Cache, progress and scheduling (P2–P3)

Cache v6 verifies source SHA-256, binary SHA-256, metadata checksum/version,
source identity, a contiguous frame index, frame lengths, sample counts and
aggregate split counts. Same-size binary corruption and damaged metadata cause
only the affected prepared shard to rebuild. Existing v3/v4/v5 caches remain
on disk and are excluded from Git.

The GUI divides eight active training hours equally among newly selected
models. The active deadline starts after data/cache preparation; queued models
do not exhaust it while waiting. Queue, dataset validation, cache, training,
validation and checkpoint I/O durations are separate. This is an equal-budget
protocol, not an eight-hour end-to-end completion promise. Early completion
can leave unused time; it is not redistributed. Cache preparation has its own
cooperative eight-hour ceiling. Disk/OS stalls are not hard-killed.

Epoch counters advance only after the corresponding checkpoint generation
commits. A failed commit rolls back reported epochs/steps to the last committed
generation. Bounded fixture epochs are not full-production epochs. Legacy tiny
fixtures can have an empty validation split and are marked as such; they are
not research evidence. Throughput uses a high-resolution timer and actual
sample counts. Warm-cache runs report real shard/position totals.

## Research controls (P4–P5)

`research_protocol.py` provides header/provenance-independent observed
trajectory identity, chronological event-group split plans, separate
train/validation/model-selection/final-test assignments, and a disk-backed
position overlap audit over input and prediction-target FENs. Canonical
trajectory duplicates, unfinished results and missing event/date metadata
are explicitly excluded by the plan. The raw-derived dataset remains intact.

`--split-plan` binds checkpoint/cache identity to the plan hash and prevents
selection/test/excluded games from entering the trainer. A complete assignment
and four nonempty research splits are required. A frozen final test is a
workflow constraint, not an access-control mechanism.

CLI ablations support EMA averaging on/off (`--ema-decay 0`), SIGReg on/off
(`--sigreg-weight 0`), response conditioning (`--model-variant no-response`),
and horizon sets (`h1`, `h1-h2`, `full`), in addition to direct policy/value and
NNUE-style baselines. EMA/SIGReg settings persist in checkpoints and cannot be
changed silently on resume. Three deterministic seeds are specified.

The experiment design defines primary/secondary metrics, color pairing,
search/time budgets, stopping, censoring, descriptive paired uncertainty,
multiple-comparison policy and a frozen-checkpoint confirmation stage. The
existing six-opening suite has repeated openings: it does not establish
120 independent opening positions or unconditional superiority. No real
Stockfish/Lc0 reference is configured, and the classical referee remains
explicitly uncalibrated. Ablation experiments, independent-reference matches,
final-test evaluation and confirmation tournaments still need to be executed.
`research_ready` and `ranking_allowed` remain false.

## Reproduction

Run from the canonical D: checkout with `.venv\Scripts\python.exe`:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -p 'test_*.py' -q
.\.venv\Scripts\python.exe test_core.py
.\.venv\Scripts\python.exe release_smoke.py build\source-smoke.json
.\build_installer.ps1 -SkipInstaller
.\.venv\Scripts\python.exe tools\prepare_research_dataset.py audit D:\CAISSA-JEPA\fen_dataset build\raw-audit.json
# The following output paths must be new versions; do not reuse completed ones.
.\.venv\Scripts\python.exe tools\prepare_research_dataset.py derive D:\CAISSA-JEPA\fen_dataset D:\CAISSA-JEPA\datasets\new-version
.\.venv\Scripts\python.exe tools\prepare_research_dataset.py split D:\CAISSA-JEPA\datasets\new-version D:\CAISSA-JEPA\research\new-plan
```

Large dataset/cache/checkpoint/build/log/research audit artifacts remain outside
Git or under existing exclusions. No push was requested.

## Final verification and installed state (P6)

- 52 unittest tests passed; core assertions passed.
- Source, PyInstaller frozen, and installed-executable smoke receipts passed.
- Each smoke run trains and resumes five models with nonempty train and
  validation subsets, checks junction resolution, cache corruption recovery,
  startup diagnostics, Qt monitor/graphs/SVG assets, ZIP decoding, arena play
  and JSONL/PGN persistence. Synthetic fixtures do not establish production
  throughput or model strength.
- `pip check` passed for the existing D: runtime: Python 3.9.13, NumPy 2.0.2,
  PySide6 6.10.3. Dependency recreation was unnecessary.
- Installed EXE replaced at `D:\CAISSA-JEPA\Caissa-JEPA.exe`; portable and
  installed EXE hashes match. The previous EXE and `_internal` directory are
  backed up under `D:\CAISSA-JEPA\releases\before-recovery-20260913`.
- All 11 preexisting checkpoint/report/verification JSON files checked before
  and after deployment have unchanged SHA-256. Old FAILED reports remain as
  historical evidence; installing the fix does not fabricate a new run.
- Installed and source `chess_data/dataset_location.json` select the new audited
  dataset and locked split plan. These runtime settings are excluded from Git.

### Full research audit result

Plan: `D:\CAISSA-JEPA\research\protocol-v1-20260913\split_plan.json`.

| Assignment | Games |
|---|---:|
| Train | 71,738 |
| Validation | 8,942 |
| Model selection | 4,607 |
| Locked final test | 4,231 |
| Excluded | 483 |

Exclusions comprise 474 duplicate canonical observed trajectories and nine
unfinished games. This is additional to the two duplicate raw-hash rows
removed from the separately derived dataset.

| Pair | Shared unique position keys | Shared beyond ply 12 in both sets |
|---|---:|---:|
| Train / validation | 48,212 | 34,318 |
| Train / selection | 30,124 | 20,445 |
| Train / final test | 28,176 | 18,997 |
| Validation / selection | 15,463 | 8,810 |
| Validation / final test | 14,286 | 7,960 |
| Selection / final test | 10,743 | 5,602 |

These counts cover input and prediction-target FEN keys. They demonstrate
shared positions, not necessarily identical labels, and must be addressed or
disclosed before a confirmatory analysis. Temporal grouping and canonical
trajectory deduplication alone do not establish position independence. The
full scan completed; no final-test predictions or tournament results were
produced. The compact committed evidence is
`docs/validation/pipeline-recovery-20260913.json`.

## Changed source and evidence files

- `adversarial_jepa.py`
- `benchmark_training_runtime.py`
- `dataset_integrity.py`
- `docs/PIPELINE_RECOVERY_20260913.md`
- `docs/validation/pipeline-recovery-20260913.json`
- `fen_dataset_tool.py`
- `main.py`
- `release_smoke.py`
- `research_protocol.py`
- `research_ui.py`
- `runtime_safety.py`
- `test_pipeline_audit.py`
- `test_pipeline_recovery.py`
- `test_research_upgrade.py`
- `tools/prepare_research_dataset.py`
- `train_caissa_v7.py`
- `training_runtime.py`

The installed application was reopened after its self-test. Production training remains unstarted.

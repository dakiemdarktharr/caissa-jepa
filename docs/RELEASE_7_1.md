# CAISSA-JEPA 7.1 - reliability release

This is a packaged desktop research prototype, not a claim of Q1 readiness or
measured playing superiority. Existing datasets and trained checkpoints are
preserved. UI text remains English.

## Start and data location

Install `installer-output/CAISSA-JEPA-Setup.exe`, or run the portable
`dist/Caissa-JEPA/Caissa-JEPA.exe`. Neither requires a separately installed Python.
Installed application data lives in `%LOCALAPPDATA%/CAISSA-JEPA`, not beside the
read-only executable. Select **TRAIN MODEL dropdown > Select FEN dataset folder**
to reuse the existing `fen_dataset` folder without copying 4 GB.

**IMPORT ZIP** imports and decodes raster images into an image staging folder.
It does not convert board images to FEN and does not train a vision model.
Chess training still consumes the portable FEN dataset. Import errors are counted;
Windows alternate streams, reserved names, traversal, links, invalid images and
excessive image dimensions are rejected.

## Training safeguards and fallback

- Kernel-owned cross-process cache/writer locks; no Windows PID signal probe.
- Source-stat/hash-specific prepared-v5 cache directories and worker checksum
  verification. Old prepared-v4 caches remain untouched and are not reused.
- Cache workers receive cancellation, check it between positions, and shut down
  cooperatively. Completed shards survive cancellation; an unfinished shard is
  rebuilt. A blocked disk/OS operation can still delay shutdown.
- One GUI trainer at a time, up to two cache processes by default. Other selected
  models remain queued. One shared eight-hour session deadline includes queue,
  cache, training and validation, with a checkpoint/shutdown reserve.
- **Eight hours is a cooperative budget, not a guarantee that five full epochs
  over the entire dataset finish for every model.** Unfinished jobs are reported
  as stopped/budget-exceeded, never as successfully completed.
- Cache ETA uses newly processed work, excluding cached work from previous runs.
  Cache ETA is explicitly cache-only. An unstarted model has no measured ETA;
  validation throughput is provisional until measured. No exact-finish guarantee.
- NEW training fails if its checkpoint already exists; Resume is explicit in the
  trainer API and automatic for existing GUI roster checkpoints (labelled RESUME).
- Checkpoints and their epoch report are committed in immutable generations.
  `latest.json` selects the consistent weights/Adam/EMA generation. The canonical
  NPZ is a convenience publication. Keep the `.generations` directory with it.
- Stop/crash fallback: **roll back the unfinished epoch**, rather than apply its
  earlier batches twice to partially trained weights. At most one epoch is lost.
  Exact mid-batch/cursor continuation is not implemented. A legacy checkpoint
  has no earlier generation; its saved weights become the first safe boundary.
- H1 skips H2/H4 predictors and target forward passes. NNUE sparse gather/scatter
  replaces dense input matrix multiplication while retaining dense Adam semantics.
  Training mixes positions through a bounded deterministic inter-game buffer.
- SIGReg regularization excludes missing-horizon substitute targets. The model
  is labelled **LeJEPA-inspired**, not a faithful reproduction of the paper.

## Arena safeguards and interpretation

- All agents use the same six frozen standard opening lines, 12 plies each.
  A seed selects a line. Reversed-color legs reuse the same line/seed.
- Series identity includes checkpoint, build, protocol and opening-suite hashes.
  Changing them requires a new series. Scoreboards never combine different series.
- AJ search observes its deadline during legal-action scoring, falling back to
  its trained policy head for remaining actions without dropping legal coverage.
- Exact rules/SAN/FEN remain authoritative. The optional external UCI referee is
  independent of move choice; invalid reference configuration falls back visibly.
- History summaries are indexed in SQLite and imported incrementally from JSONL;
  per-move telemetry stays in JSONL and PGN exports. Long-lived GUI history no
  longer retains every move object. Current-series statistics still scan summaries.
- Truncated games are censored, not draws. The monitor shows censored/error counts.
  Statistics also expose worst/best-case score bounds for censored results.
- Continuous play is exploratory. Descriptive intervals are **not** sequential
  significance or evidence of a winner. No actual full-dataset win rates were
  measured during release tests.

## Remaining research work - explicitly not solved by packaging

1. Canonical-game deduplication, event/player separation, immutable train/val/test
   splits, and a dataset-wide overlap audit. Existing splits still use legacy
   game hashes; do not present their validation scores as leakage-free evidence.
2. A frozen, representative final test set and game-clustered uncertainty. The
   current offline evaluator still uses a bounded source-order sample.
3. Shared-search/value-head controlled comparisons in addition to native engine
   comparisons. The current native search track confounds representation and search.
4. Preregistered fixed-budget confirmatory matches, seed repeats, multiple-testing
   control and an adequate opening suite; six built-in openings are only a starter.
5. Teacher-labelled WDL/policy targets, legal hard-negative training and ablations.
   The existing game-outcome and ranking objectives remain research baselines.
6. A faithful LeJEPA/SIGReg implementation with explicit architectural/objective
   version migration; draw-clock/history features; compact array/mmap cache;
   sparse optimizer/incremental NNUE accumulators and hardware-specific profiling.
7. Exact mid-epoch generation/cursor commits and bounded process termination for
   pathological I/O stalls. Current documented fallback is epoch/shard rollback.

These items require new experiment protocols and potentially fresh training.
Do not silently migrate existing checkpoints or claim they are fixed by this release.

## Rebuild and verify

`build_installer.ps1 -Python <python.exe> -InnoCompiler <ISCC.exe>` builds the
bundle and installer. `-SkipInstaller` explicitly requests portable-only output.
PyInstaller must be installed; a project-local `build/build-tools` installation
is supported. Build manifests bind the frozen binary to source hashes.

Run the test suite with `python -B -m unittest discover -v`, plus
`python -B test_core.py`. The executable supports
`Caissa-JEPA.exe --self-test <absolute-receipt.json>` for isolated temporary-data
train/resume, Qt/SVG, image ZIP and arena smoke checks. This is not a full-size
training benchmark and does not alter the user's dataset/checkpoints.

Build tooling source: [Inno Setup official downloads](https://jrsoftware.org/isdl.php).
Downloaded compiler installer signature was checked before execution. The CAISSA
installer itself is unsigned; no signing certificate was supplied.

The builder isolates DLL discovery from unrelated PATH entries (including
Poppler ICU) and supplies the Qt-compatible VC runtime at the bundle root.
A frozen executable smoke test is a mandatory gate before installer compilation.

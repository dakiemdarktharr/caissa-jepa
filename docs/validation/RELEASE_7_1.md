# Release verification - 2026-09-12

Environment: Windows x64, Python 3.9.13, NumPy 2.0.2, PySide6 6.10.3,
PyInstaller 6.22.2, Inno Setup 6.7.3. BLAS threads: 1.

## Passed

- 41 unittest tests (`python -B -m unittest discover -v`).
- Standalone core rules/database/model assertions (`python -B test_core.py`).
- PowerShell parser validation and `git diff --check`.
- 13 new safety tests included in the 41: kernel locks without signals; generation
  restore; NEW-mode protection; H1 branch exclusion; sparse/dense NNUE agreement;
  resumed-cache ETA; worker cancellation/lock release; checksum rejection/cache
  invalidation; six legal opening lines; ZIP ADS/reserved-name rejection; indexed
  history deduplication; exact checkpoint equality after epoch rollback/resume;
  deadline expiry while waiting for another cache builder.
- Source and frozen smoke: all five model architectures train and resume using
  temporary fixture data; Qt monitor renders with bundled SVG assets; image ZIP
  import accepts a valid image and rejects a corrupt image/ADS path; arena plays
  12 common opening plies followed by model search and saves JSONL/PGN history.
- Clean build's mandatory executable self-test: PASSED, frozen=true, 8 checks.
- Actual installer to `build/installed-smoke`: exit 0.
- Same 8-check self-test from the installed executable: exit 0, PASSED.
- Uninstall from that isolated directory: exit 0; test executable removed; no
  restart required. This only removed files created by the installer test.
- Training and arena monitor fixture screenshots visually inspected at 1500x1000.
  These depict synthetic UI state, not measured scientific performance.

## Installer artifact

- File: `installer-output/CAISSA-JEPA-Setup.exe`
- Size: 40,085,148 bytes
- SHA-256: `2faa1d78ec07e521546a884190122e644d3f97bf8f90535074d716ce31e52928`
- Unsigned application installer. No code-signing certificate was provided.
- Build logs, screenshots and JSON smoke receipts remain in ignored `build/`.

## Packaging failure found and fixed

An early bundle built successfully but could not import QtWidgets. DLL analysis
identified Poppler's versioned ICU being collected from ambient PATH instead of
Qt's Windows ICU dependency. Build DLL discovery now uses a restricted PATH,
Qt-compatible VC runtime files are published at the bundle root, and a failed
frozen smoke test blocks installer compilation. No Windows security setting was
changed. Native Computer Use inspection was unavailable due to a sandbox helper
failure; bootstrap exception receipts and DLL analysis provided the diagnosis.

## Small performance comparison

Against the previous Git HEAD, same temporary samples, latent size 96, batch 64,
one process/BLAS thread, median of 10 steps after 2 warmup steps:

| Training implementation | Before | After | Speedup |
| --- | ---: | ---: | ---: |
| JEPA H1 | 12.6685 ms | 7.03435 ms | 1.80x |
| NNUE-style | 42.1445 ms | 34.8327 ms | 1.21x |

These are microbenchmarks during build activity, not full-dataset throughput or
evidence that every model can finish five epochs in eight hours.

## Not verified / remaining

No full 4-GB cache preparation, five-model full-size run, long tournament,
external Stockfish strength comparison, final-test leakage audit, or Q1-ready
statistical confirmation was performed. The continuous arena is exploratory.
See [remaining research work](../RELEASE_7_1.md) for explicit unresolved items
and implemented fallbacks. Existing user data/checkpoints were preserved;
release tests used isolated temporary datasets and models.

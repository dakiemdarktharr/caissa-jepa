# Master handoff verification — 2026-10-25

This receipt covers repository reconciliation, synthetic verification, and the
handoff package. It is not a research gate pass, a full release certification,
or reproduction of historical experiments.

## Tested source and environment

- Incoming source: `0cba5d6`; pending local changes preserved as `e3d73bd`.
- Remote source fetched: `a11668982eabebab7e6925e058eddb80a93df0d8` (415 commits
  ahead of the incoming source; zero unique committed local ancestors).
- Reconciliation merge: `4d67caf50a183396dfb6f032c56ddad6595b6442`. Its tracked
  tree was verified identical to the fetched GitHub tree. Both parents are
  retained. The handoff subsequently changes documentation only.
- Linux, CPython 3.11.9, NumPy 2.4.6 in the project `.venv`.
- Test environment: `OPENBLAS_NUM_THREADS=1`, `OMP_NUM_THREADS=1`, Python `-B`.
- PySide6 is absent. The Windows runtime, GUI, installer, real systemd service
  paths and OOM behavior were not validated by this handoff.

## Executed tests

| Source | Command (with thread environment above) | Result |
| --- | --- | --- |
| Incoming source plus pending local changes | `.venv/bin/python -B -m unittest discover -s tests -p 'test_v212*.py' -v` | 25 tests, 19.876 s, all pass |
| Same incoming snapshot | `.venv/bin/python -B -m unittest discover -s tests -v` | 154 tests, 44.522 s: 149 passed, 3 errors, 2 skipped |
| Reconciled current source | `.venv/bin/python -B -m unittest discover -s tests -p 'test_v212*.py' -v` | **488 tests, 96.221 s, all pass** |

The current V2.12 run covers the 74 `test_v212*.py` modules: objective/gradient
fixtures, masks/schedules/receipts, partial accounting, analytic protocol
helpers, pilot safety fixtures, bounded references, symmetry, worker IPC,
bootstrap binding, and mocked supervision. Temporary subprocess/filesystem
tests are included. A printed V03 `rss_cap`/`stopped_safety` row is an expected
mocked safety fixture in a temporary directory, not a failed research pilot.

The three broader-suite errors were explicit environment/artifact limits:

1. `test_v211_protocol.V211ProtocolTests.test_frozen_spec_and_schedule_reproduce`
   needs missing `chess_data/v29_fit_panel_dev01/panel.json`.
2. `test_v211_protocol.V211ProtocolTests.test_schedule_hash_is_sensitive_to_control_label`
   needs the same missing, hash-bound historical panel.
3. `test_v29_panel_supervisor.V29PanelSupervisorTests.test_dataset_must_be_exact_pinned_dev09`
   reaches the Windows-only supervisor guard on Linux and raises `OSError`.

The two skips are Windows Job Object and Windows supervisor path checks.
These were not hidden by weakening tests or inventing experiment files. The
broader suite result belongs to the preserved incoming snapshot; the complete
post-merge historical/GUI suite was not rerun. The current-source pass claim
is specifically the 488 V2.12 tests. Root-level legacy test modules and
`release_smoke.py` were not run. The next Windows/artifact-equipped environment
should run the applicable broader checks before a release or historical
experiment verification.

## Static and publication checks

Handoff validation passed: **339 tracked Python files parsed**, **57 relative
links resolved**, **627 inventory file hashes verified** against the recorded
Git tree, and **12 excluded pilot-file hashes verified** with ignore status.
The inventory JSON and `git diff --check` pass. The original `.gitignore` is
unchanged, and the merge tree matches the fetched remote tree. The publish
workflow commits the handoff, pushes normally to the configured `origin/main`,
and compares the remote branch hash with local `HEAD`; the final chat response
records the published commit rather than putting a self-referential hash in
this document.

The inventory contains 627 tracked files / 12,393,847 bytes at the merge commit
and 12 excluded local V01/V02 pilot files / 1,702,737 bytes. Only metadata and
hashes of those pilot files are in the inventory. Environments, caches,
generated data, checkpoints, logs and raw result files remain excluded.

## Reproduction scope

The normal clone contains source, curated evidence, and this handoff. It does
not contain the raw DEV09/V2.9/V2.11 datasets, trained checkpoints, legacy
chess/FEN archive, external Obsidian vault, or private chat transcripts. Missing
artifacts must be restored through a separately agreed storage plan and
verified against the original provenance before use. No protected outcomes
were opened to complete this handoff.

The source/fixture checks establish software behavior only. They do not
establish graph freeze, authenticated corpus provenance, a complete measured
training-FLOP counter, ≤5% parity, root/bootstrap calibration, live supervision
reliability, training authorization, or JEPA performance. No method or research
gate advanced during publication.

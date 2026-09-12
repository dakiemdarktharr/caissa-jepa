# C: cleanup and D: runtime — 2026-09-13

The installed application is `D:/CAISSA-JEPA/Caissa-JEPA.exe`.
The working source copy is `D:/CAISSA-JEPA/source` with a recreated `.venv`
(Python 3.9.13, NumPy 2.0.2, PySide6 6.10.3). Runtime packages were preserved
locally and console launchers regenerated for D:. The shared system Python
installation on C: is not project data and was not removed.

Data locations:

- Active dataset: `D:/CAISSA-JEPA/fen_dataset`.
- Installed-app checkpoints/database: `D:/CAISSA-JEPA/app-data/chess_data`.
- Older source-run checkpoints/database and legacy archive: `D:/CAISSA-JEPA/source/chess_data`.
- Source dataset link: `D:/CAISSA-JEPA/source/fen_dataset` points to the active dataset.
- AppData `CAISSA-JEPA/fen_dataset` and `CAISSA-JEPA/chess_data` on C: are
  directory junctions to the two active data directories above, not extra copies.

Every retained file in the old C: `chess_data`, `fen_dataset`, `build`, `dist`,
`installer-output`, `_external_crawl_smoke`, and installed AppData `chess_data`
was SHA-256 checked against its D: copy before removal. Inventories are saved
as `migration_verification.json` in each corresponding D: destination. The
26 current installed-app files (15,210,284 bytes) include the failed zero-step
checkpoints/reports; they were preserved, not replaced with older source models.

The six old project data/build folders above, old `.venv`, `__pycache__`, and
original AppData `chess_data` were moved to Windows Recycle Bin. They can be
restored until the bin is emptied. No unrelated C: directories were removed;
disk space remains occupied by the recycled copies until the bin is emptied.

The active C: workspace root, source files and Git directory remain intentionally.
Deleting the current workspace root is not performed from this task. Continue
future source work in `D:/CAISSA-JEPA/source`; source scripts on the old C: copy
no longer have a local runtime/dataset. After switching the workspace, the
remaining old source copy can be reviewed for removal separately.

See `PIPELINE_AUDIT_20260913.md` for the confirmed production failures and each
primary/fallback proposal. Migration does not fix or silently rewrite those
experimental defects. Do not infer five successful full-data epochs from the
passing temporary-fixture tests.

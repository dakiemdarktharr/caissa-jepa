# Consolidating the legacy chess workspace

Destination project: `C:/Users/ANHKHOI/Documents/ChatGPT/caissa-jepa`.
The separate installed application at `D:/CAISSA-JEPA` is not a source project
and is not part of this migration.

All legacy source files, assets, model checkpoints, GM game files and the old
SQLite database from `D:/chess_robot_app` are preserved under:

`chess_data/legacy_chess_robot_app_20260912/`

This directory is intentionally excluded from Git by the existing `chess_data/`
rule. Legacy code/data does not overwrite the current application, FEN dataset,
checkpoints or database. The 4,772 GM text files remain in the archive's
`gm_games/` folder, and the old approximately 3-GB database remains in its
`chess_data/chess_engine.db` file.

The old virtual environment is recreated, not relocated: Windows virtual
environments contain absolute paths. The project-local `.venv` uses the same
Python 3.9.13 base installation and runtime packages NumPy 2.0.2 and PySide6
6.10.3 (matching Essentials/Addons/shiboken6). Runtime packages and metadata
were copied locally into the newly created environment; 26 console launchers
were regenerated against the new interpreter. `pip check` passed. Generated `__pycache__` files
and the obsolete virtual environment do not need to be retained.

Default interpreter in all active launch/training/build scripts:
`$PSScriptRoot/.venv/Scripts/python.exe`. Old paths in dated validation receipts
and archived legacy code are historical evidence, not active dependencies.

Before deleting the source workspace, verify a SHA-256 match for every retained
file, run the source/core safety tests with the new interpreter, and check its
isolated all-model train/resume/Qt/ZIP/arena smoke test. The migration inventory
and verification receipt are stored alongside the archived data.

To recover a legacy artifact after source removal, copy it from the archive.
Do not overwrite current checkpoints or databases without an explicit experiment
migration. The old directory is no longer necessary once these checks pass.

## Completed verification (2026-09-12)

All 4,796 retained files (3,009,924,643 bytes) passed SHA-256 comparison twice,
including immediately before removal. The inventory is
`chess_data/legacy_chess_robot_app_20260912/migration_verification.json`.
The new environment passed 41 unit tests plus core assertions, PowerShell
parsing for the three updated scripts, and the isolated smoke test covering
five-model training/resume, Qt/assets, ZIP validation and arena persistence.

`D:/chess_robot_app` was moved to the Windows Recycle Bin after verifying no
active process referenced it and the source contained no reparse points. The
directory no longer exists at its original path; it can be restored from the
Recycle Bin until emptied. Space is not reclaimed until the bin is emptied.
The installed application at `D:/CAISSA-JEPA` remains untouched.

The complete isolated smoke test passed again after removal, recorded in
`build/migration-post-removal-smoke.json`. Archived datasets, checkpoints,
the recreated environment and generated verification receipts remain excluded
from Git; this migration does not import old checkpoints into active training.

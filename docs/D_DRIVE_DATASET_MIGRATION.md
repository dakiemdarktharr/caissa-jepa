# Installed-app dataset migration (2026-09-12)

The installed executable remains `D:/CAISSA-JEPA/Caissa-JEPA.exe`.
All 121 files (4,466,711,405 bytes) from the source project's `fen_dataset`
were copied to `D:/CAISSA-JEPA/fen_dataset` and individually SHA-256 verified.
The receipt is stored in that destination as `migration_verification.json`.

The frozen app reads `%LOCALAPPDATA%/CAISSA-JEPA`, independently of its install
directory. Its `fen_dataset` child is now a Windows directory junction to the
dataset on D:. The existing application database was not overwritten, and no
training was started. The installed app was reopened successfully.

## Dataset quality warning

Migration checks passed, but the pre-existing dataset fails its strict verifier.
All manifest-listed shard hashes match. Reading all listed shards gives 90,003
game rows, 90,001 unique game hashes (two duplicate rows), 8,284,410 positions,
and 4,035,308,412 JSONL bytes. The manifest instead reports 95,577 games,
8,819,061 positions and 4,294,932,427 bytes. No on-disk JSONL shard is unlisted.
Do not treat the manifest totals as verified training sample counts. Dataset
repair/deduplication and any resulting fingerprint change require a separate,
recorded step; the migration deliberately preserves original content.

## Source preservation and removal status

The C: project remains the active task workspace and has not been deleted.
A source backup at `D:/CAISSA-JEPA/source` preserves Git history, source,
archived legacy data and build artifacts. It excludes `.venv`, `__pycache__`,
and `fen_dataset` (already copied separately above). Recreate `.venv` before
running source scripts from the new location; the installed app does not need it.

Before removing the old C: project, switch to a task whose workspace is the new
source location and resolve the dataset validation warning. The C: dataset is
also retained pending that step. Do not recursively delete the currently active
workspace or follow the AppData junction when cleaning up old directories.

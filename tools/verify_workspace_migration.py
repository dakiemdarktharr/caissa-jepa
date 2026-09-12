"""Verify a legacy workspace copy without altering or deleting its source."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from runtime_safety import atomic_json


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def verify(source, destination):
    source, destination = Path(source).resolve(strict=True), Path(destination).resolve(strict=True)
    if not source.is_dir() or not destination.is_dir():
        raise ValueError("Source and destination must both be directories")
    if source == destination or source in destination.parents or destination in source.parents:
        raise ValueError("Source and destination must be disjoint directories")
    records = []
    for directory, names, files in os.walk(source, followlinks=False):
        relative_directory = Path(directory).relative_to(source)
        names[:] = [name for name in names if name != "__pycache__" and not (relative_directory == Path(".") and name == ".venv")]
        for name in names:
            child = Path(directory) / name
            if child.is_symlink() or (child.stat().st_file_attributes & 0x400 if os.name == "nt" else False):
                raise ValueError(f"Unexpected directory link: {child}")
        for name in sorted(files):
            original = Path(directory) / name
            relative = original.relative_to(source)
            copied = destination / relative
            if original.is_symlink() or copied.is_symlink():
                raise ValueError(f"Unexpected file link: {relative}")
            before = original.stat()
            source_hash = sha256(original)
            if copied.stat().st_size != before.st_size or sha256(copied) != source_hash:
                raise ValueError(f"Copy mismatch: {relative}")
            after = original.stat()
            if before.st_mtime_ns != after.st_mtime_ns or before.st_size != after.st_size:
                raise ValueError(f"Source changed while verifying: {relative}")
            records.append({"path": relative.as_posix(), "bytes": before.st_size, "sha256": source_hash})
    receipt = {"status": "VERIFIED", "source": str(source), "destination": str(destination),
               "files": len(records), "bytes": sum(r["bytes"] for r in records),
               "excluded_generated_directories": [".venv (recreated)", "__pycache__"],
               "records": records}
    atomic_json(destination / "migration_verification.json", receipt)
    print(json.dumps({k: v for k, v in receipt.items() if k != "records"}, indent=2))
    return receipt


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source")
    parser.add_argument("destination")
    args = parser.parse_args()
    verify(args.source, args.destination)

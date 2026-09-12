"""Cross-process locks and atomic persistence for local training jobs."""
from __future__ import annotations

import json
import os
import time
import uuid
import shutil
from pathlib import Path


class FileLease:
    """Kernel-owned advisory lock. A crashed process releases it automatically.

    The lock file intentionally persists: unlinking a locked file can create two
    independent lock identities. Never use os.kill(pid, 0) on Windows.
    """
    def __init__(self, path):
        self.path = Path(path)
        self.handle = None

    def acquire(self):
        if self.handle is not None:
            return True
        self.path.parent.mkdir(parents=True, exist_ok=True)
        handle = self.path.open("a+b")
        handle.seek(0, os.SEEK_END)
        if handle.tell() == 0:
            handle.write(b"\0")
            handle.flush()
        handle.seek(0)
        try:
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            handle.close()
            return False
        self.handle = handle
        return True

    def release(self):
        if self.handle is not None:
            handle, self.handle = self.handle, None
            try:
                handle.seek(0)
                if os.name == "nt":
                    import msvcrt
                    msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
            finally:
                handle.close()

    def __enter__(self):
        if not self.acquire():
            raise RuntimeError(f"Another process owns this job: {self.path}")
        return self

    def __exit__(self, *_):
        self.release()


def atomic_json(path, payload, attempts=8):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
    try:
        with temporary.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False)
            handle.flush()
            os.fsync(handle.fileno())
        for attempt in range(attempts):
            try:
                temporary.replace(path)
                return
            except PermissionError:
                if attempt + 1 == attempts:
                    raise
                time.sleep(min(0.05 * 2 ** attempt, 1.0))
    finally:
        temporary.unlink(missing_ok=True)


def publish_file(source, target):
    target = Path(target)
    temporary = target.with_name(target.name + "." + uuid.uuid4().hex + ".tmp")
    try:
        with open(source, "rb") as src, temporary.open("wb") as dst:
            shutil.copyfileobj(src, dst, 1024 * 1024)
            dst.flush()
            os.fsync(dst.fileno())
        os.replace(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)


def checkpoint_commit(model, report):
    """Publish model + optimizer/EMA and matching report as one generation.

    latest.json is the commit point; the canonical npz is a convenience copy.
    Resume always restores the committed generation, never half an epoch.
    """
    canonical = model.model_path
    root = canonical.with_suffix(".generations")
    root.mkdir(parents=True, exist_ok=True)
    generation = uuid.uuid4().hex + ".npz"
    try:
        model.model_path = root / generation
        model.save()
        with model.model_path.open("r+b") as handle:
            os.fsync(handle.fileno())
    finally:
        model.model_path = canonical
    atomic_json(root / "latest.json", {"checkpoint": generation, "report": report})
    publish_file(root / generation, canonical)


def restore_committed(model_path):
    model_path = Path(model_path)
    root = model_path.with_suffix(".generations")
    pointer = root / "latest.json"
    if not pointer.exists():
        return None
    payload = json.loads(pointer.read_text(encoding="utf-8"))
    name = payload["checkpoint"]
    if Path(name).name != name or not name.endswith(".npz"):
        raise ValueError("Invalid checkpoint generation")
    publish_file(root / name, model_path)
    return payload["report"]

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
        self.path = Path(path).resolve()
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
    path = Path(path).resolve()
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
    target = Path(target).resolve()
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
    canonical = Path(model.model_path).resolve()
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
    publish_file(root / generation, canonical)
    import hashlib
    checksum = hashlib.sha256((root / generation).read_bytes()).hexdigest()
    atomic_json(root / "latest.json", {"version": 2, "checkpoint": generation, "sha256": checksum, "report": report})


def restore_committed(model_path):
    model_path = Path(model_path).resolve()
    root = model_path.with_suffix(".generations")
    pointer = root / "latest.json"
    if not pointer.exists():
        return None
    payload = json.loads(pointer.read_text(encoding="utf-8"))
    name = payload["checkpoint"]
    if Path(name).name != name or not name.endswith(".npz"):
        raise ValueError("Invalid checkpoint generation")
    import hashlib
    if payload.get("sha256") != hashlib.sha256((root / name).read_bytes()).hexdigest():
        raise ValueError("Checkpoint generation checksum missing or mismatched; weights preserved")
    publish_file(root / name, model_path)
    return payload["report"]


def path_diagnostics(arguments):
    """Keep both requested and physical paths for Windows junction failures."""
    model = Path(arguments.model)
    dataset = Path(getattr(arguments, "dataset", "."))
    paths = {"model": model, "training_report": model.with_suffix(".training.json"),
             "generations": model.with_suffix(".generations"),
             "latest_pointer": model.with_suffix(".generations") / "latest.json",
             "writer_lock": model.with_suffix(".writer.lock"), "dataset": dataset}
    try:
        import hashlib
        from training_runtime import SampleCache
        manifest = json.loads((dataset / "dataset_manifest.json").read_text(encoding="utf-8"))
        fingerprint = hashlib.sha256((dataset / "dataset_manifest.json").read_bytes()).hexdigest()
        signature = SampleCache._signature(dataset.resolve(), manifest, verify_sources=False)
        if getattr(arguments, "split_plan", None):
            plan_bytes = Path(arguments.split_plan).read_bytes()
            plan = json.loads(plan_bytes)
            fingerprint = plan.get("dataset_fingerprint") or hashlib.sha256((fingerprint + hashlib.sha256(plan_bytes).hexdigest()).encode()).hexdigest()
        identity = hashlib.sha256(signature.encode()).hexdigest()[:16]
        paths["cache"] = dataset / f"prepared-v{SampleCache.VERSION}-{fingerprint[:16]}-{getattr(arguments, 'validation_percent', 10)}-{identity}"
        paths["cache_lock"] = paths["cache"] / ".build.lock"
    except Exception:
        pass
    result = {}
    for key, path in paths.items():
        try:
            result[key] = {"requested": str(path.absolute()), "resolved": str(path.resolve()),
                           "exists": path.exists(), "is_directory": path.is_dir()}
        except OSError as error:
            result[key] = {"requested": str(path), "inspection_error": repr(error)}
    return result


def archive_checkpoint(model_path):
    """Preserve a checkpoint set for an explicitly requested fresh generation.

    Caller must hold its writer lease. Every move is restricted to the resolved
    checkpoint parent. Roll back completed moves if the archive cannot finish.
    """
    model = Path(model_path).resolve()
    base = model.parent
    destination = (base / "archived_checkpoints" / (model.stem + "-" + uuid.uuid4().hex)).resolve()
    sources = [model, model.with_suffix(".generations"), model.with_suffix(".training.json"), model.with_suffix(".evaluation.json")]
    operations = []
    for source in sources:
        if not source.exists():
            continue
        source = source.resolve(strict=True)
        target = destination / source.name
        if base not in source.parents or base not in target.resolve().parents:
            raise ValueError("Checkpoint archive path escapes its intended parent")
        operations.append((source, target))
    destination.mkdir(parents=True, exist_ok=False)
    moved = []
    try:
        for source, target in operations:
            source.rename(target)
            moved.append((source, target))
        atomic_json(destination / "archive.json", {"reason": "explicit fresh training", "files": [{"original": str(a), "archived": str(b)} for a,b in moved]})
    except BaseException:
        for source, target in reversed(moved):
            target.rename(source)
        raise
    return str(destination)

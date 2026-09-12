"""Shared disk sample cache, bounded metrics and measured training ETA."""
from __future__ import annotations

import json
import hashlib
import math
import os
import pickle
import struct
import time
import zlib
from collections import defaultdict, deque
from concurrent.futures import FIRST_COMPLETED, ProcessPoolExecutor, wait
from pathlib import Path

import numpy as np
from runtime_safety import FileLease, atomic_json as _atomic_json

_worker_cancel = None


def _init_cache_worker(cancel):
    global _worker_cancel
    _worker_cancel = cancel


def _check_worker(deadline):
    if _worker_cancel is not None and _worker_cancel.is_set():
        raise InterruptedError("Cache preparation stopped")
    if deadline and time.time() >= deadline:
        raise TimeoutError("Cache time budget exceeded")


class MetricMean:
    """Sample-weighted running means; memory does not grow with epoch length."""
    def __init__(self):
        self.sums = defaultdict(float)
        self.weights = defaultdict(int)

    def add(self, metrics, count):
        for key, value in metrics.items():
            if not math.isfinite(float(value)):
                raise FloatingPointError(f"Non-finite training metric: {key}={value}")
            self.sums[key] += float(value) * count
            self.weights[key] += count

    def result(self):
        return {key: value / self.weights[key] for key, value in self.sums.items()}


class TrainingETA:
    """Phase-specific rolling batch times; estimates become available after warmup."""
    def __init__(self, phase_batches, epochs):
        self.phase_batches = phase_batches
        self.epochs = epochs
        self.total = sum(phase_batches.values()) * epochs
        self.times = {phase: deque(maxlen=64) for phase in phase_batches}
        self.done = defaultdict(int)
        self.completed = 0

    def observe(self, phase, seconds):
        self.times[phase].append(max(1e-6, seconds))
        self.done[phase] += 1
        self.completed += 1

    def fields(self):
        remaining = {p: n * self.epochs - self.done[p] for p, n in self.phase_batches.items()}
        known = all(len(self.times[p]) >= min(3, n) for p, n in self.phase_batches.items() if n)
        eta = 0.0 if self.completed >= self.total else None
        spread = None
        if known:
            eta = sum(remaining[p] * float(np.mean(self.times[p])) for p in remaining if self.times[p])
            spread = sum(remaining[p] * float(np.std(self.times[p])) for p in remaining if self.times[p])
        elif len(self.times.get("train", [])) >= min(3, self.phase_batches.get("train", 0)) and self.times.get("train"):
            # Before validation has run, borrow train throughput and disclose it.
            baseline = float(np.mean(self.times["train"]))
            eta = sum(remaining[p] * (float(np.mean(self.times[p])) if self.times[p] else baseline) for p in remaining)
            spread = eta * 0.5
        return {
            "overall_processed": self.completed,
            "overall_total": self.total,
            "progress_percent": 100.0 * self.completed / max(1, self.total),
            "eta_seconds": eta,
            "eta_range_seconds": [max(0.0, eta - spread), eta + spread] if spread is not None else None,
            "eta_status": "MEASURED ESTIMATE" if known else "PROVISIONAL (validation unmeasured)" if eta is not None else "CALIBRATING",
            "estimated_finish_timestamp": time.time() + eta if eta is not None else None,
        }


def _legacy_atomic_json(path: Path, payload: dict) -> None:
    """Write progress and manifest records atomically."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, separators=(",", ":"))
        handle.flush()
        os.fsync(handle.fileno())
    temporary.replace(path)


def _write_frame(handle, value) -> tuple[int, int]:
    payload = zlib.compress(pickle.dumps(value, protocol=pickle.HIGHEST_PROTOCOL), level=1)
    offset = handle.tell()
    handle.write(struct.pack("<Q", len(payload)))
    handle.write(payload)
    return offset, 8 + len(payload)


def _read_frame(handle, offset: int, length: int):
    handle.seek(offset)
    stored_length = struct.unpack("<Q", handle.read(8))[0]
    if stored_length != length - 8:
        raise RuntimeError("Corrupt prepared cache frame")
    return pickle.loads(zlib.decompress(handle.read(stored_length)))


def _cache_shard_worker(payload: dict) -> dict:
    """Prepare one source shard in a separate Windows-spawn-safe process."""
    deadline_epoch = payload.get("deadline_epoch")
    from adversarial_jepa import sample_from_dataset_position, stable_split

    dataset = Path(payload["dataset"])
    source_path = dataset / payload["source_path"]
    output_path = Path(payload["output_path"])
    metadata_path = Path(payload["metadata_path"])
    progress_path = Path(payload["progress_path"])
    output_part = output_path.with_suffix(output_path.suffix + ".part")
    metadata_part = metadata_path.with_suffix(metadata_path.suffix + ".part")
    output_part.unlink(missing_ok=True)
    metadata_part.unlink(missing_ok=True)
    started = time.monotonic()
    last_update = 0.0
    source_bytes = source_positions = valid_positions = skipped = 0
    records = []
    source_digest = hashlib.sha256()
    rng = np.random.default_rng(20260903 + int(payload["index"]))

    def progress(done=False):
        elapsed = max(1e-6, time.monotonic() - started)
        _atomic_json(progress_path, {
            "index": payload["index"],
            "source_bytes": source_bytes,
            "source_positions": source_positions,
            "valid_positions": valid_positions,
            "skipped_samples": skipped,
            "elapsed_seconds": elapsed,
            "positions_per_second": source_positions / elapsed,
            "done": done,
        })

    with source_path.open("rb") as source, output_part.open("wb") as output:
        for raw_line in source:
            _check_worker(deadline_epoch)
            source_digest.update(raw_line)
            source_bytes += len(raw_line)
            positions = []
            try:
                game = json.loads(raw_line)
                positions = game.get("positions", [])
                source_positions += len(positions)
                result = game.get("headers", {}).get("Result")
                if result not in ("1-0", "0-1", "1/2-1/2"):
                    skipped += len(positions)
                    continue
                prepared = []
                for position in positions:
                    _check_worker(deadline_epoch)
                    sample = sample_from_dataset_position(position, rng)
                    if sample is None:
                        skipped += 1
                    else:
                        prepared.append(sample)
                        valid_positions += 1
                if prepared:
                    split = stable_split(game["game_hash"], payload["validation_percent"])
                    offset, length = _write_frame(output, {"split": split, "samples": prepared})
                    records.append({
                        "offset": offset,
                        "length": length,
                        "split": split,
                        "n": len(prepared),
                    })
            except (KeyError, TypeError, ValueError, json.JSONDecodeError):
                skipped += len(positions)
            now = time.monotonic()
            if now - last_update >= 0.5:
                progress()
                last_update = now
        output.flush()
        os.fsync(output.fileno())
    expected = payload.get("source_sha256")
    if expected and source_digest.hexdigest() != expected:
        raise ValueError(f"Source checksum mismatch: {source_path}")
    output_part.replace(output_path)
    elapsed = max(1e-6, time.monotonic() - started)
    metadata = {
        "version": 5,
        "signature": payload.get("signature"),
        "source_sha256": source_digest.hexdigest(),
        "output_bytes": output_path.stat().st_size,
        "index": payload["index"],
        "source_path": payload["source_path"],
        "source_bytes": source_bytes,
        "source_positions": source_positions,
        "valid_positions": valid_positions,
        "skipped_samples": skipped,
        "records": records,
        "elapsed_seconds": elapsed,
    }
    _atomic_json(metadata_part, metadata)
    metadata_part.replace(metadata_path)
    progress(True)
    return metadata


class SampleCache:
    """Parallel, resumable binary cache shared by all model workers.

    Version 3 used one SQLite writer transaction for the complete dataset. That
    forced the selected trainers to queue behind one process and discarded work
    when that process was interrupted. Version 4 prepares source shards in
    parallel and publishes each completed shard atomically.
    """
    VERSION = 5

    def __init__(self, dataset, fingerprint, validation_percent, callback=None, workers=None, deadline_epoch=None):
        self.dataset = Path(dataset)
        self.fingerprint = fingerprint
        self.validation_percent = validation_percent
        self.callback = callback or (lambda payload: None)
        self.workers = int(workers or os.environ.get("CAISSA_CACHE_WORKERS", "0") or 0)
        self.deadline_epoch = float(deadline_epoch) if deadline_epoch else None
        self.path = self.dataset / f"prepared-v{self.VERSION}-{fingerprint[:16]}-{validation_percent}"
        self.lock_path = self.path / ".build.lock"
        self.manifest = None
        self._lease = None
        self._baseline = None

    @staticmethod
    def _signature(dataset: Path, dataset_manifest: dict) -> str:
        signature = []
        for shard in dataset_manifest.get("shards", []):
            source = dataset / shard["path"]
            stat = source.stat()
            signature.append((shard["path"], stat.st_size, stat.st_mtime_ns, shard.get("sha256")))
        return json.dumps(signature, separators=(",", ":"), sort_keys=True)

    def _read_json(self, path: Path) -> dict | None:
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (FileNotFoundError, PermissionError, json.JSONDecodeError):
            return None

    def _ready_manifest(self, signature: str) -> dict | None:
        metadata = self._read_json(self.path / "manifest.json")
        if not metadata or metadata.get("version") != self.VERSION or metadata.get("signature") != signature:
            return None
        if metadata.get("status") != "COMPLETE":
            return None
        for shard in metadata.get("shards", []):
            if not (self.path / shard["file"]).exists() or not (self.path / shard["metadata"]).exists():
                return None
            if (self.path / shard["file"]).stat().st_size != shard.get("output_bytes"):
                return None
        return metadata

    def _load_complete(self, metadata: dict):
        self.manifest = metadata
        counts = metadata.get("counts", {})
        self.counts = {"train": int(counts.get("train", 0)), "validation": int(counts.get("validation", 0))}
        self.skipped = int(metadata.get("skipped", 0))
        return self

    def _acquire_lock(self) -> bool:
        if self._lease is None:
            self._lease = FileLease(self.lock_path)
        return self._lease.acquire()

    def _release_lock(self):
        if self._lease is not None:
            self._lease.release()

    def _check_deadline(self):
        if self.deadline_epoch and time.time() >= self.deadline_epoch:
            raise TimeoutError("Cache time budget exceeded")

    def _progress(self, manifest: dict, phase: str, started: float, workers: int):
        source_shards = manifest.get("shards", [])
        total_bytes = max(1, sum(int(shard.get("bytes", 0)) for shard in source_shards))
        completed = {int(item["index"]): item for item in source_shards if item.get("complete")}
        byte_count = sum(int(item.get("source_bytes", 0)) for item in completed.values())
        position_count = sum(int(item.get("source_positions", 0)) for item in completed.values())
        valid_count = sum(int(item.get("valid_positions", 0)) for item in completed.values())
        skipped = sum(int(item.get("skipped_samples", 0)) for item in completed.values())
        for shard in source_shards:
            if shard.get("complete"):
                continue
            progress_name = shard.get("progress", f"shard_{int(shard['index']):05d}.progress.json")
            progress = self._read_json(self.path / progress_name)
            if progress:
                byte_count += int(progress.get("source_bytes", 0))
                position_count += int(progress.get("source_positions", 0))
                valid_count += int(progress.get("valid_positions", 0))
                skipped += int(progress.get("skipped_samples", 0))
        elapsed = max(1e-6, time.monotonic() - started)
        if self._baseline is None:
            self._baseline = (byte_count, position_count, time.monotonic())
        base_bytes, base_positions, base_time = self._baseline
        elapsed = max(1e-6, time.monotonic() - base_time)
        rate = max(0, byte_count - base_bytes) / elapsed
        eta = max(0, total_bytes - byte_count) / rate if rate > 0 else None
        self.callback({
            "phase": phase,
            "prepared_positions": position_count,
            "valid_cache_positions": valid_count,
            "source_positions": manifest.get("source_positions"),
            "source_bytes_processed": byte_count,
            "source_bytes_total": total_bytes,
            "skipped_samples": skipped,
            "cache_shards_completed": len(completed),
            "cache_shards_total": len(source_shards),
            "cache_workers": workers,
            "cache_rows_per_second": max(0, position_count - base_positions) / elapsed,
            "eta_scope": "cache only; training not yet calibrated",
            "eta_seconds": eta,
            "estimated_finish_timestamp": time.time() + eta if eta is not None else None,
            "eta_status": "MEASURED CACHE ESTIMATE" if eta is not None else "CALIBRATING CACHE",
            "progress_percent": 100.0 * byte_count / total_bytes,
            "overall_processed": position_count,
            "overall_total": manifest.get("source_positions", 0),
        })

    def _mark_shard(self, manifest: dict, result: dict):
        for shard in manifest["shards"]:
            if int(shard["index"]) == int(result["index"]):
                shard.update(result)
                shard["complete"] = True
                return
        raise RuntimeError(f"Unknown prepared cache shard {result.get('index')}")

    def _build_missing(self, manifest: dict, missing: list[dict], workers: int):
        started = time.monotonic()
        payloads = []
        for shard in missing:
            payloads.append({
                "dataset": str(self.dataset),
                "source_path": shard["path"],
                "output_path": str(self.path / shard["file"]),
                "metadata_path": str(self.path / shard["metadata"]),
                "progress_path": str(self.path / shard["progress"]),
                "validation_percent": self.validation_percent,
                "index": shard["index"],
                "deadline_epoch": self.deadline_epoch,
                "signature": manifest["signature"],
                "source_sha256": shard.get("sha256"),
            })
        context = __import__("multiprocessing").get_context("spawn")
        cancel = context.Event()
        executor = ProcessPoolExecutor(max_workers=workers, mp_context=context,
                                       initializer=_init_cache_worker, initargs=(cancel,))
        pending = {executor.submit(_cache_shard_worker, payload): payload for payload in payloads}
        try:
            while pending:
                self._check_deadline()
                done, _ = wait(pending, timeout=0.5, return_when=FIRST_COMPLETED)
                self._progress(manifest, "preparing_cache", started, workers)
                for future in done:
                    future.result()
                    result = self._read_json(Path(pending[future]["metadata_path"]))
                    pending.pop(future)
                    if not result:
                        raise RuntimeError("Cache worker completed without metadata")
                    self._mark_shard(manifest, result)
                    self._progress(manifest, "preparing_cache", started, workers)
        finally:
            cancel.set()
            executor.shutdown(wait=True, cancel_futures=True)

    def prepare(self):
        if self.deadline_epoch and time.time() >= self.deadline_epoch:
            raise TimeoutError("Cache time budget exceeded before preparation")
        dataset_manifest = json.loads((self.dataset / "dataset_manifest.json").read_text(encoding="utf-8"))
        signature = self._signature(self.dataset, dataset_manifest)
        identity = hashlib.sha256(signature.encode()).hexdigest()[:16]
        self.path = self.dataset / f"prepared-v{self.VERSION}-{self.fingerprint[:16]}-{self.validation_percent}-{identity}"
        self.lock_path = self.path / ".build.lock"
        ready = self._ready_manifest(signature)
        if ready:
            return self._load_complete(ready)
        self.path.mkdir(parents=True, exist_ok=True)
        if not self._acquire_lock():
            started = time.monotonic()
            while True:
                self._check_deadline()
                ready = self._ready_manifest(signature)
                if ready:
                    return self._load_complete(ready)
                waiting_manifest = {
                    "source_positions": dataset_manifest.get("positions", 0),
                    "shards": [
                        {**shard, "index": index, "progress": f"shard_{index:05d}.progress.json"}
                        for index, shard in enumerate(dataset_manifest.get("shards", []))
                    ],
                }
                self._progress(waiting_manifest, "waiting_for_shared_cache", started, 0)
                if self._acquire_lock():
                    break
                time.sleep(0.5)
        try:
            current = self._read_json(self.path / "manifest.json")
            if not current or current.get("signature") != signature:
                manifest = {
                    "version": self.VERSION,
                    "status": "BUILDING",
                    "signature": signature,
                    "source_positions": int(dataset_manifest.get("positions", 0)),
                    "shards": [],
                }
                for index, shard in enumerate(dataset_manifest.get("shards", [])):
                    stem = f"shard_{index:05d}"
                    manifest["shards"].append({
                        "index": index,
                        "path": shard["path"],
                        "bytes": int(shard.get("bytes", 0)),
                        "sha256": shard.get("sha256"),
                        "file": stem + ".bin",
                        "metadata": stem + ".json",
                        "progress": stem + ".progress.json",
                        "complete": False,
                    })
                _atomic_json(self.path / "manifest.json", manifest)
            else:
                manifest = current
            missing = []
            for shard in manifest["shards"]:
                metadata = self._read_json(self.path / shard["metadata"])
                if (metadata and metadata.get("version") == self.VERSION
                        and metadata.get("signature") == signature
                        and (self.path / shard["file"]).exists()
                        and (self.path / shard["file"]).stat().st_size == metadata.get("output_bytes")):
                    shard.update(metadata)
                    shard["complete"] = True
                    continue
                shard["complete"] = False
                missing.append(shard)
            workers = max(1, min(len(missing), self.workers or min(2, os.cpu_count() or 1))) if missing else 1
            self._progress(manifest, "preparing_cache", time.monotonic(), workers)
            if missing:
                self._build_missing(manifest, missing, workers)
            counts = {"train": 0, "validation": 0}
            skipped = 0
            for shard in manifest["shards"]:
                if not shard.get("complete"):
                    raise RuntimeError(f"Prepared cache shard incomplete: {shard.get('path')}")
                for record in shard.get("records", []):
                    counts[record["split"]] += int(record["n"])
                skipped += int(shard.get("skipped_samples", 0))
            manifest.update({"status": "COMPLETE", "counts": counts, "skipped": skipped, "completed_at": time.time()})
            _atomic_json(self.path / "manifest.json", manifest)
            return self._load_complete(manifest)
        finally:
            self._release_lock()

    def batches(self, split, batch_size, seed):
        rng = np.random.default_rng(seed)
        references = []
        for shard in self.manifest.get("shards", []):
            references.extend(
                {**record, "file": shard["file"]}
                for record in shard.get("records", [])
                if record.get("split") == split
            )
        if split == "train":
            rng.shuffle(references)
        handles = {}
        pending = []
        shuffle_buffer = []
        buffer_limit = max(batch_size * 8, 512)
        try:
            for reference in references:
                file_name = reference["file"]
                if file_name not in handles:
                    handles[file_name] = (self.path / file_name).open("rb")
                record = _read_frame(handles[file_name], int(reference["offset"]), int(reference["length"]))
                samples = record["samples"]
                if split == "train":
                    rng.shuffle(samples)
                for item in samples:
                    for name in ("own_action", "opponent_action", "next_our_action", "second_opponent_action", "negative_action"):
                        if item[name] is not None:
                            item[name] = tuple(item[name])
                    alternatives = item.pop("legal_alternatives", [])
                    item["negative_action"] = tuple(alternatives[int(rng.integers(len(alternatives)))]) if alternatives else item["own_action"]
                    if split == "train":
                        shuffle_buffer.append(item)
                        if len(shuffle_buffer) < buffer_limit:
                            continue
                        index = int(rng.integers(len(shuffle_buffer)))
                        item = shuffle_buffer[index]
                        shuffle_buffer[index] = shuffle_buffer[-1]
                        shuffle_buffer.pop()
                    pending.append(item)
                    if len(pending) == batch_size:
                        yield pending
                        pending = []
            rng.shuffle(shuffle_buffer)
            for item in shuffle_buffer:
                pending.append(item)
                if len(pending) == batch_size:
                    yield pending
                    pending = []
            if pending:
                yield pending
        finally:
            for handle in handles.values():
                handle.close()

"""Shared disk sample cache, bounded metrics and measured training ETA."""
from __future__ import annotations

import json
import math
import sqlite3
import time
import zlib
from collections import defaultdict, deque
from pathlib import Path

import numpy as np


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


class SampleCache:
    """One compressed JSON record per game; reuse legal/FEN parsing across models.

    SQLite serializes builders across threads/processes. Only a committed COMPLETE
    cache is consumed. An interrupted build rolls back and cannot look complete.
    Source shards are stat-checked as well as manifest-fingerprinted.
    """
    VERSION = 3

    def __init__(self, dataset, fingerprint, validation_percent, callback=None):
        self.dataset = Path(dataset)
        self.fingerprint = fingerprint
        self.validation_percent = validation_percent
        self.path = self.dataset / f"prepared-v{self.VERSION}-{fingerprint[:16]}-{validation_percent}.sqlite"
        self.callback = callback or (lambda payload: None)

    def prepare(self):
        from adversarial_jepa import iter_dataset_games, sample_from_dataset_position, stable_split
        manifest = json.loads((self.dataset / "dataset_manifest.json").read_text(encoding="utf-8"))
        signature = [(s["path"], (self.dataset / s["path"]).stat().st_size,
                      (self.dataset / s["path"]).stat().st_mtime_ns) for s in manifest["shards"]]
        signature = json.dumps(signature)
        con = sqlite3.connect(self.path, timeout=0.5)
        try:
            while True:
                try:
                    con.execute("BEGIN IMMEDIATE")
                    break
                except sqlite3.OperationalError as error:
                    if "locked" not in str(error):
                        raise
                    self.callback({"phase": "waiting_for_shared_cache", "prepared_positions": 0})
            con.execute("CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT)")
            con.execute("CREATE TABLE IF NOT EXISTS games (id INTEGER PRIMARY KEY, split TEXT, n INTEGER, data BLOB)")
            metadata = dict(con.execute("SELECT key,value FROM meta"))
            if metadata.get("signature") != signature or metadata.get("status") != "COMPLETE":
                con.execute("DELETE FROM games")
                con.execute("DELETE FROM meta")
                count = skipped = 0
                rng = np.random.default_rng(0)
                last_update = 0.0
                for game in iter_dataset_games(self.dataset):
                    if game.get("headers", {}).get("Result") not in ("1-0", "0-1", "1/2-1/2"):
                        skipped += len(game.get("positions", []))
                        continue
                    prepared = []
                    for position in game["positions"]:
                        sample = sample_from_dataset_position(position, rng)
                        if sample is None:
                            skipped += 1
                        else:
                            prepared.append(sample)
                        count += 1
                        if time.monotonic() - last_update >= 0.5:
                            self.callback({"phase": "preparing_cache", "prepared_positions": count,
                                           "source_positions": manifest.get("positions"), "skipped_samples": skipped})
                            last_update = time.monotonic()
                    if prepared:
                        blob = zlib.compress(json.dumps(prepared, separators=(",", ":")).encode(), level=1)
                        con.execute("INSERT INTO games(split,n,data) VALUES(?,?,?)",
                                    (stable_split(game["game_hash"], self.validation_percent), len(prepared), blob))
                con.executemany("INSERT INTO meta VALUES(?,?)",
                                [("signature", signature), ("status", "COMPLETE"), ("skipped", str(skipped))])
            self.counts = {p: 0 for p in ("train", "validation")}
            self.counts.update(dict(con.execute("SELECT split,SUM(n) FROM games GROUP BY split")))
            self.skipped = int(dict(con.execute("SELECT key,value FROM meta")).get("skipped", 0))
            con.commit()
        finally:
            con.close()
        return self

    def batches(self, split, batch_size, seed):
        rng = np.random.default_rng(seed)
        con = sqlite3.connect(self.path)
        try:
            ids = np.array([row[0] for row in con.execute("SELECT id FROM games WHERE split=? ORDER BY id", (split,))])
            if split == "train":
                rng.shuffle(ids)
            pending = []
            for game_id in ids:
                raw = con.execute("SELECT data FROM games WHERE id=?", (int(game_id),)).fetchone()[0]
                samples = json.loads(zlib.decompress(raw))
                if split == "train":
                    rng.shuffle(samples)
                for item in samples:
                    for name in ("own_action", "opponent_action", "next_our_action", "second_opponent_action", "negative_action"):
                        if item[name] is not None:
                            item[name] = tuple(item[name])
                    alternatives = item.pop("legal_alternatives", [])
                    item["negative_action"] = tuple(alternatives[int(rng.integers(len(alternatives)))]) if alternatives else item["own_action"]
                    pending.append(item)
                    if len(pending) == batch_size:
                        yield pending
                        pending = []
            if pending:
                yield pending
        finally:
            con.close()

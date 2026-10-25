"""Small durable research journal; no training, scheduling, or network actions.

SQLite transactions preserve acknowledged events across process interruption.
Exports are immutable, checksummed snapshots suitable for an explicitly
reviewed Git checkpoint. Hardware loss still loses unexported local events.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import os
from pathlib import Path
import re
import sqlite3
import tempfile
import time
from datetime import datetime, timezone


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def file_sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def measured_objective(ledger, run_id, event_key, step, model, batch):
    """Persist the existing objective's returned metrics without an update.

    Optimizer, dataset, evaluation and process-monitor events belong at their
    respective caller boundaries; this adapter does not pretend to log them.
    """
    start = time.perf_counter()
    def normalize(value):
        if isinstance(value, dict):
            return {str(k): normalize(v) for k, v in value.items()}
        if isinstance(value, (list, tuple)):
            return [normalize(v) for v in value]
        return value
    stage = "objective"
    try:
        metrics, gradients = model.loss_grad(batch)
        stage = "measurement"
        measurements = normalize({k: v for k, v in metrics.items() if k != "arm"})
        measurements["objective_wall_seconds"] = time.perf_counter() - start
        ledger.record(run_id, event_key, "objective", step=step, metrics=measurements,
                      dimensions={"arm": metrics.get("arm")})
    except Exception as error:
        ledger.record(run_id, event_key + ":failure", "failure", step=step,
                      dimensions={"exception": type(error).__name__, "stage": stage},
                      metrics={"objective_result": None}, missing_reason="Objective or measurement failed",
                      note="No successful objective observation was acknowledged; inspect and use a new attempt ID")
        raise
    return metrics, gradients


def _identifier(value):
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,159}", value):
        raise ValueError("invalid identifier")


def _metrics(value):
    if value is None:
        return True
    if type(value) in (int, float):
        if not math.isfinite(value):
            raise ValueError("nonfinite metric; record null with a reason and a failure event")
        return False
    if isinstance(value, dict):
        missing = False
        for key, item in value.items():
            _identifier(key)
            missing = _metrics(item) or missing
        return missing
    if isinstance(value, list):
        return any([_metrics(item) for item in value])
    raise ValueError("metrics must be numeric, null, or nested numeric containers")


def _sync_dir(path):
    if os.name != "nt":
        fd = os.open(path, os.O_RDONLY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)


class Ledger:
    """One database, multiple independent run IDs, idempotent event keys."""

    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.path, timeout=30, isolation_level=None)
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("PRAGMA synchronous=FULL")
        self.db.execute("PRAGMA foreign_keys=ON")
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS runs (
                run_id TEXT PRIMARY KEY, manifest TEXT NOT NULL, hash TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS events (
                run_id TEXT NOT NULL REFERENCES runs(run_id),
                sequence INTEGER NOT NULL, event_key TEXT NOT NULL,
                payload TEXT NOT NULL, previous_hash TEXT NOT NULL, hash TEXT NOT NULL,
                PRIMARY KEY(run_id, sequence), UNIQUE(run_id, event_key));
        """)

    def close(self):
        self.db.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def create_run(self, manifest):
        required = {"run_id", "phase", "protocol_id", "code_commit", "config", "inputs", "environment"}
        if not required <= manifest.keys():
            raise ValueError("manifest missing required provenance fields")
        _identifier(manifest["run_id"])
        _identifier(manifest["protocol_id"])
        if manifest["phase"] not in {"workflow", "smoke", "development", "locked"}:
            raise ValueError("unknown phase")
        if not re.fullmatch(r"(?:[0-9a-f]{40}|[0-9a-f]{64})", manifest["code_commit"]):
            raise ValueError("full code commit required")
        for name in ("config", "inputs", "environment"):
            if not isinstance(manifest[name], dict):
                raise ValueError(f"{name} must be an object")
        for name, fingerprint in manifest["inputs"].items():
            _identifier(name)
            if not re.fullmatch(r"[0-9a-f]{64}", fingerprint):
                raise ValueError("input fingerprints must be SHA-256")
        if manifest["phase"] in {"development", "locked"}:
            if not {"dataset", "split", "protocol"} <= manifest["inputs"].keys():
                raise ValueError("scientific runs require dataset, split, and protocol identities")
            if type(manifest.get("seed")) is not int or not manifest.get("arm"):
                raise ValueError("scientific runs require arm and integer seed")
        for kind, names in manifest.get("required_metrics", {}).items():
            _identifier(kind)
            if not isinstance(names, list) or len(names) != len(set(names)):
                raise ValueError("required metrics must be unique lists")
            for name in names:
                _identifier(name)
        serialized = canonical(manifest)
        fingerprint = digest(manifest)
        self.db.execute("BEGIN IMMEDIATE")
        try:
            previous = self.db.execute("SELECT manifest FROM runs WHERE run_id=?", (manifest["run_id"],)).fetchone()
            if previous and previous[0] != serialized:
                raise ValueError("run identity already exists with different metadata")
            self.db.execute("INSERT OR IGNORE INTO runs VALUES (?,?,?)", (manifest["run_id"], serialized, fingerprint))
            self.db.commit()
        except BaseException:
            self.db.rollback()
            raise
        return fingerprint

    def record(self, run_id, event_key, kind, *, step=None, metrics=None,
               dimensions=None, note="", missing_reason=None):
        for identifier in (run_id, event_key, kind):
            _identifier(identifier)
        if step is not None and (type(step) is not int or step < 0):
            raise ValueError("step must be a nonnegative integer or null")
        metrics = {} if metrics is None else metrics
        dimensions = {} if dimensions is None else dimensions
        if not isinstance(metrics, dict) or not isinstance(dimensions, dict):
            raise ValueError("metrics and dimensions must be objects")
        if _metrics(metrics) and not (isinstance(missing_reason, str) and missing_reason.strip()):
            raise ValueError("null metrics require a missing_reason")
        if not isinstance(note, str) or len(note) > 4000:
            raise ValueError("note must be a short decision or evidence summary")
        content = dict(event_key=event_key, kind=kind, step=step, metrics=metrics,
                       dimensions=dimensions, note=note, missing_reason=missing_reason)
        canonical(content)
        self.db.execute("BEGIN IMMEDIATE")
        try:
            row = self.db.execute("SELECT manifest,hash FROM runs WHERE run_id=?", (run_id,)).fetchone()
            if not row:
                raise ValueError("unknown run")
            manifest = json.loads(row[0])
            if not set(manifest.get("required_metrics", {}).get(kind, [])) <= metrics.keys():
                raise ValueError("missing required metrics for this event kind")
            old = self.db.execute("SELECT payload,hash FROM events WHERE run_id=? AND event_key=?", (run_id, event_key)).fetchone()
            if old:
                original = json.loads(old[0])
                if original["content"] != content:
                    raise ValueError("event key reused with changed content")
                self.db.commit()
                return old[1]
            last = self.db.execute("SELECT sequence,hash FROM events WHERE run_id=? ORDER BY sequence DESC LIMIT 1", (run_id,)).fetchone()
            sequence, previous = (last[0] + 1, last[1]) if last else (1, row[1])
            payload = dict(run_id=run_id, sequence=sequence, previous_hash=previous,
                           utc=datetime.now(timezone.utc).isoformat(), content=content)
            fingerprint = digest(payload)
            self.db.execute("INSERT INTO events VALUES (?,?,?,?,?,?)",
                            (run_id, sequence, event_key, canonical(payload), previous, fingerprint))
            self.db.commit()
            return fingerprint
        except BaseException:
            self.db.rollback()
            raise

    def snapshot(self):
        """Read and verify a consistent DB snapshot, even with concurrent writers."""
        self.db.execute("BEGIN")
        try:
            runs = []
            for run_id, raw, fingerprint in self.db.execute("SELECT * FROM runs ORDER BY run_id").fetchall():
                manifest = json.loads(raw)
                if digest(manifest) != fingerprint or manifest["run_id"] != run_id:
                    raise ValueError("run manifest integrity failure")
                previous, expected, events = fingerprint, 1, []
                for seq, key, raw_event, prev, hashed in self.db.execute(
                    "SELECT sequence,event_key,payload,previous_hash,hash FROM events WHERE run_id=? ORDER BY sequence", (run_id,)
                ).fetchall():
                    event = json.loads(raw_event)
                    if (seq != expected or prev != previous or digest(event) != hashed
                            or event["previous_hash"] != previous or event["run_id"] != run_id
                            or event["sequence"] != seq or event["content"]["event_key"] != key):
                        raise ValueError("event integrity failure")
                    events.append(dict(event, sha256=hashed))
                    previous, expected = hashed, expected + 1
                runs.append(dict(manifest=manifest, manifest_sha256=fingerprint, events=events))
            self.db.commit()
            return runs
        except BaseException:
            self.db.rollback()
            raise

    def export(self, destination, *, release=None, max_bytes=2_000_000):
        """Publish an immutable snapshot. Locked runs require a bound release record.

        A release record is an explicit audit decision, not an access-control
        system. The operator must have authority to release those results.
        """
        snapshot = self.snapshot()
        permitted, withheld = [], []
        for run in snapshot:
            run_id = run["manifest"]["run_id"]
            if run["manifest"]["phase"] == "locked":
                if release is None:
                    withheld.append(run_id)
                    continue
                if (not release.get("reason") or
                        not re.fullmatch(r"[0-9a-f]{64}", release.get("review_receipt_sha256", "")) or
                        release.get("run_manifest_hashes", {}).get(run_id) != run["manifest_sha256"]):
                    raise ValueError("locked release must bind each manifest and a review receipt")
            permitted.append(run)
        payload = dict(schema_version=1, runs=permitted, withheld_run_ids=withheld, release=release)
        data = (canonical(payload) + "\n").encode()
        stream = io.StringIO(newline="")
        writer = csv.writer(stream)
        writer.writerow(["run_id", "phase", "sequence", "utc", "kind", "step", "event_key",
                         "metrics_json", "dimensions_json", "missing_reason", "note", "event_sha256"])
        for run in permitted:
            for event in run["events"]:
                c = event["content"]
                writer.writerow([run["manifest"]["run_id"], run["manifest"]["phase"], event["sequence"],
                                 event["utc"], c["kind"], c["step"], c["event_key"], canonical(c["metrics"]),
                                 canonical(c["dimensions"]), c["missing_reason"], c["note"], event["sha256"]])
        table = stream.getvalue().encode()
        if len(data) + len(table) > max_bytes:
            raise ValueError("snapshot exceeds curated export limit; partition or aggregate explicitly")
        bundle = {"snapshot.json": data, "events.csv": table}
        checksums = {name: hashlib.sha256(blob).hexdigest() for name, blob in bundle.items()}
        identity = digest(checksums)
        bundle["checksums.json"] = (canonical(checksums) + "\n").encode()
        parent = Path(destination)
        parent.mkdir(parents=True, exist_ok=True)
        final = parent / ("snapshot-" + identity)
        if final.exists():
            if any((final / name).read_bytes() != blob for name, blob in bundle.items()):
                raise ValueError("existing export is inconsistent")
            return final
        temp = Path(tempfile.mkdtemp(prefix=".export-", dir=parent))
        try:
            for name, blob in bundle.items():
                with open(temp / name, "xb") as stream:
                    stream.write(blob)
                    stream.flush()
                    os.fsync(stream.fileno())
            _sync_dir(temp)
            os.rename(temp, final)
            _sync_dir(parent)
        finally:
            if temp.exists():
                for child in temp.iterdir():
                    child.unlink()
                temp.rmdir()
        return final

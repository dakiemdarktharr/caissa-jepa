"""Detached Windows supervisor for the exploratory V2.8 proxy pilot.

This utility records durable heartbeat and terminal status beside the selected
artifact. It is run as its own hidden process; its game runner is assigned to a
Windows Job Object with an explicit CPU-time cap. It does not make the pilot a
JEPA evaluation or authorize training.
"""

from __future__ import annotations

import argparse
import ctypes
import datetime as dt
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback

import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


CODE_INPUTS = (
    "tools/v28_modelblind_match_pilot.py",
    "tools/v28_modelblind_pilot_supervisor.py",
    "two_player/v28_data.py",
    "two_player/games.py",
    "two_player/data.py",
)


def _code_fingerprints(paths=None) -> dict:
    """Hash the pilot entry point and project modules that define its policies/rules."""
    paths = paths or {name: ROOT / name for name in CODE_INPUTS}
    return {name: _sha256(Path(path)) for name, path in sorted(paths.items())}


def _code_fingerprint_digest(fingerprints: dict) -> str:
    canonical = json.dumps(fingerprints, sort_keys=True, separators=(",", ":"),
                           allow_nan=False).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def _atomic_json(path: Path, value: dict) -> None:
    temp = path.with_suffix(path.suffix + ".tmp")
    with temp.open("w", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temp, path)


def _selected_schedule(blocks: int):
    from tools.v28_modelblind_match_pilot import (
        CHECKPOINT_SEEDS, PROXY_COMPARISONS, V28_GAMES, make_schedule)

    cells = len(PROXY_COMPARISONS) * len(V28_GAMES)
    if type(blocks) is not int or blocks < cells or blocks % cells:
        raise ValueError("blocks must be a positive multiple of all game/comparison cells")
    per_cell = blocks // cells
    checkpoint_count = min(len(CHECKPOINT_SEEDS), per_cell)
    matches_per_checkpoint = per_cell // checkpoint_count
    if checkpoint_count * matches_per_checkpoint != per_cell:
        raise ValueError("pilot size must divide evenly across checkpoint strata")
    return make_schedule(matches_per_checkpoint=matches_per_checkpoint,
                         checkpoint_seeds=CHECKPOINT_SEEDS[:checkpoint_count])


def _derived_paths(output: Path) -> tuple[Path, ...]:
    receipt = output.with_suffix(output.suffix + ".receipt.json")
    status = output.with_suffix(output.suffix + ".supervisor.json")
    return (
        output,
        output.with_suffix(output.suffix + ".tmp"),
        output.with_suffix(output.suffix + ".partial.jsonl"),
        receipt,
        receipt.with_suffix(receipt.suffix + ".tmp"),
        status,
        status.with_suffix(status.suffix + ".tmp"),
        status.with_suffix(status.suffix + ".terminal-fallback.json"),
        output.with_suffix(output.suffix + ".runner.stdout.log"),
        output.with_suffix(output.suffix + ".runner.stderr.log"),
    )


def _validate_completion(output: Path, *, blocks: int,
                         source_sha: str, schedule_sha: str,
                         code_fingerprints: dict) -> dict:
    if code_fingerprints.get("tools/v28_modelblind_match_pilot.py") != source_sha:
        raise ValueError("pilot entry source fingerprint mismatch")
    if _code_fingerprints() != code_fingerprints:
        raise ValueError("pilot code inputs changed during run")
    receipt_path = output.with_suffix(output.suffix + ".receipt.json")
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    if receipt.get("schema") != "v28-modelblind-match-pilot-v01-receipt":
        raise ValueError("pilot receipt schema mismatch")
    if receipt.get("block_count") != blocks:
        raise ValueError("pilot receipt block count mismatch")
    if receipt.get("source_sha256") != source_sha:
        raise ValueError("pilot receipt runner source hash mismatch")
    if receipt.get("schedule_sha256") != schedule_sha:
        raise ValueError("pilot receipt selected schedule hash mismatch")
    artifact = receipt.get("artifact")
    if not isinstance(artifact, dict):
        raise ValueError("pilot receipt lacks artifact fingerprint")
    if artifact.get("path") != str(output):
        raise ValueError("pilot receipt output path mismatch")
    if artifact.get("bytes") != output.stat().st_size:
        raise ValueError("pilot receipt artifact size mismatch")
    artifact_sha = _sha256(output)
    if artifact.get("sha256") != artifact_sha:
        raise ValueError("pilot receipt artifact hash mismatch")
    with output.open("r", encoding="utf-8") as stream:
        try:
            manifest = json.loads(next(stream))
        except (StopIteration, json.JSONDecodeError) as exc:
            raise ValueError("pilot artifact has no valid manifest") from exc
        count = sum(1 for line in stream if line.strip())
    if manifest.get("schedule_sha256") != schedule_sha:
        raise ValueError("pilot artifact selected schedule hash mismatch")
    if manifest.get("source_sha256") != source_sha:
        raise ValueError("pilot artifact runner source hash mismatch")
    if manifest.get("block_count") != blocks or count != blocks:
        raise ValueError("pilot artifact row count mismatch")
    return {"path": str(output), "bytes": output.stat().st_size,
            "sha256": artifact_sha, "block_count": count,
            "schedule_sha256": schedule_sha, "source_sha256": source_sha,
            "code_fingerprint_sha256": _code_fingerprint_digest(code_fingerprints)}


class _JobLimit:
    """Windows job handle limiting the child process CPU time."""

    def __init__(self, process: subprocess.Popen, cpu_cap_seconds: int):
        if os.name != "nt":
            raise OSError("the detached pilot supervisor currently requires Windows")
        from ctypes import wintypes

        class IoCounters(ctypes.Structure):
            _fields_ = [(name, ctypes.c_ulonglong) for name in (
                "ReadOperationCount", "WriteOperationCount", "OtherOperationCount",
                "ReadTransferCount", "WriteTransferCount", "OtherTransferCount")]

        class BasicLimit(ctypes.Structure):
            _fields_ = [
                ("PerProcessUserTimeLimit", ctypes.c_longlong),
                ("PerJobUserTimeLimit", ctypes.c_longlong),
                ("LimitFlags", wintypes.DWORD),
                ("MinimumWorkingSetSize", ctypes.c_size_t),
                ("MaximumWorkingSetSize", ctypes.c_size_t),
                ("ActiveProcessLimit", wintypes.DWORD),
                ("Affinity", ctypes.c_size_t),
                ("PriorityClass", wintypes.DWORD),
                ("SchedulingClass", wintypes.DWORD),
            ]

        class ExtendedLimit(ctypes.Structure):
            _fields_ = [
                ("BasicLimitInformation", BasicLimit),
                ("IoInfo", IoCounters),
                ("ProcessMemoryLimit", ctypes.c_size_t),
                ("JobMemoryLimit", ctypes.c_size_t),
                ("PeakProcessMemoryUsed", ctypes.c_size_t),
                ("PeakJobMemoryUsed", ctypes.c_size_t),
            ]

        self._kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        self._kernel32.CreateJobObjectW.restype = wintypes.HANDLE
        self._kernel32.SetInformationJobObject.argtypes = [
            wintypes.HANDLE, wintypes.INT, ctypes.c_void_p, wintypes.DWORD]
        self._kernel32.SetInformationJobObject.restype = wintypes.BOOL
        self._kernel32.AssignProcessToJobObject.argtypes = [
            wintypes.HANDLE, wintypes.HANDLE]
        self._kernel32.AssignProcessToJobObject.restype = wintypes.BOOL
        self._kernel32.TerminateJobObject.argtypes = [wintypes.HANDLE, wintypes.UINT]
        self._kernel32.TerminateJobObject.restype = wintypes.BOOL
        self._kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
        self._kernel32.CloseHandle.restype = wintypes.BOOL

        self._handle = self._kernel32.CreateJobObjectW(None, None)
        if not self._handle:
            raise ctypes.WinError(ctypes.get_last_error())
        limits = ExtendedLimit()
        limits.BasicLimitInformation.PerProcessUserTimeLimit = int(cpu_cap_seconds * 1e7)
        # JOB_OBJECT_LIMIT_PROCESS_TIME | JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        limits.BasicLimitInformation.LimitFlags = 0x2 | 0x2000
        if not self._kernel32.SetInformationJobObject(
                self._handle, 9, ctypes.byref(limits), ctypes.sizeof(limits)):
            error = ctypes.get_last_error()
            self.close()
            raise ctypes.WinError(error)
        if not self._kernel32.AssignProcessToJobObject(
                self._handle, wintypes.HANDLE(int(process._handle))):
            error = ctypes.get_last_error()
            self.close()
            raise ctypes.WinError(error)

    def terminate(self, exit_code: int = 1) -> None:
        self._kernel32.TerminateJobObject(self._handle, exit_code)

    def close(self) -> None:
        handle = getattr(self, "_handle", None)
        if handle:
            self._kernel32.CloseHandle(handle)
            self._handle = None


def _run(output: Path, *, blocks: int, cpu_cap: int, heartbeat_seconds: float) -> dict:
    output = output.resolve()
    if not output.is_relative_to((ROOT / "chess_data").resolve()):
        raise ValueError("pilot outputs must be placed under the ignored chess_data directory")
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(output.suffix + ".tmp")
    partial = output.with_suffix(output.suffix + ".partial.jsonl")
    receipt = output.with_suffix(output.suffix + ".receipt.json")
    status = output.with_suffix(output.suffix + ".supervisor.json")
    stdout_path = output.with_suffix(output.suffix + ".runner.stdout.log")
    stderr_path = output.with_suffix(output.suffix + ".runner.stderr.log")
    paths = _derived_paths(output)
    collisions = [str(path) for path in paths if path.exists()]
    if collisions:
        raise FileExistsError("refusing to overwrite existing pilot files: " + ", ".join(collisions))

    runner = ROOT / "tools" / "v28_modelblind_match_pilot.py"
    from tools.v28_modelblind_match_pilot import _canonical
    schedule = _selected_schedule(blocks)
    code_fingerprints = _code_fingerprints()
    source_sha = code_fingerprints["tools/v28_modelblind_match_pilot.py"]
    schedule_sha = hashlib.sha256(_canonical(schedule)).hexdigest()
    expected_rows = len(schedule)
    base = {
        "schema": "v28-modelblind-supervisor-v01",
        "status": "starting",
        "started_utc": _utc_now(),
        "supervisor_pid": os.getpid(),
        "runner_sha256": source_sha,
        "code_fingerprints": code_fingerprints,
        "code_fingerprint_sha256": _code_fingerprint_digest(code_fingerprints),
        "supervisor_sha256": code_fingerprints[
            "tools/v28_modelblind_pilot_supervisor.py"],
        "python_version": sys.version,
        "numpy_version": np.__version__,
        "selected_schedule_sha256": schedule_sha,
        "block_count_expected": expected_rows,
        "requested_blocks": blocks,
        "cpu_cap_seconds": cpu_cap,
        "output_path": str(output),
        "interpretation": "Exploratory proxy-policy runtime/variance diagnostic only; no learned model or JEPA effect.",
    }
    started = time.monotonic()
    process = None
    job = None
    reason = "error"
    error_text = None
    exit_code = None
    try:
        _atomic_json(status, base)
        flags = subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP
        with stdout_path.open("xb") as stdout, stderr_path.open("xb") as stderr:
            command = [sys.executable, "-B", "-m", "tools.v28_modelblind_match_pilot",
                       str(output), "--blocks", str(blocks)]
            process = subprocess.Popen(command, cwd=ROOT, stdin=subprocess.DEVNULL,
                                       stdout=stdout, stderr=stderr, creationflags=flags)
            job = _JobLimit(process, cpu_cap)
            base.update({"status": "running", "runner_pid": process.pid,
                         "launched_utc": _utc_now()})
            _atomic_json(status, base)
            last_heartbeat = 0.0
            while process.poll() is None:
                now = time.monotonic()
                if now - last_heartbeat >= heartbeat_seconds:
                    progress_path = temporary if temporary.exists() else partial
                    base.update({
                        "status": "running",
                        "heartbeat_utc": _utc_now(),
                        "elapsed_wall_seconds": now - started,
                        "artifact_bytes": progress_path.stat().st_size if progress_path.exists() else 0,
                        "runner_log_bytes": stdout_path.stat().st_size + stderr_path.stat().st_size,
                    })
                    _atomic_json(status, base)
                    last_heartbeat = now
                time.sleep(min(1.0, heartbeat_seconds / 4))
            exit_code = process.wait()
        if (exit_code == 0 and output.exists() and receipt.exists()
                and not temporary.exists() and not partial.exists()):
            validated = _validate_completion(output, blocks=expected_rows,
                                             source_sha=source_sha,
                                             schedule_sha=schedule_sha,
                                             code_fingerprints=code_fingerprints)
            reason = "completed"
        else:
            reason = "runner_error"
            validated = None
    except BaseException as exc:
        error_text = f"{type(exc).__name__}: {exc}"
        if process is not None and process.poll() is None:
            try:
                if job is not None:
                    job.terminate(1)
                else:
                    process.kill()
                process.wait(timeout=20)
            except Exception:
                pass
        raise
    finally:
        if job is not None:
            job.close()
        elapsed = time.monotonic() - started
        artifact = output if output.exists() else partial if partial.exists() else temporary
        terminal = dict(base)
        terminal.update({
            "status": reason,
            "finished_utc": _utc_now(),
            "elapsed_wall_seconds": elapsed,
            "exit_code": exit_code,
            "supervisor_error": error_text,
            "artifact_path": str(artifact) if artifact.exists() else None,
            "artifact_bytes": artifact.stat().st_size if artifact.exists() else 0,
            "artifact_sha256": _sha256(artifact) if artifact.exists() else None,
            "receipt_path": str(receipt) if receipt.exists() else None,
            "validated_completion": locals().get("validated"),
        })
        try:
            _atomic_json(status, terminal)
        except BaseException:
            # Keep a recognizable terminal sidecar even if atomic replacement fails.
            fallback = status.with_suffix(status.suffix + ".terminal-fallback.json")
            with fallback.open("x", encoding="utf-8", newline="\n") as stream:
                json.dump(terminal, stream, sort_keys=True, indent=2)
                stream.write("\n")
                stream.flush()
                os.fsync(stream.fileno())
    return terminal


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--blocks", type=int, default=9600)
    parser.add_argument("--cpu-cap-seconds", type=int, default=14400)
    parser.add_argument("--heartbeat-seconds", type=float, default=15.0)
    args = parser.parse_args(argv)
    if (args.blocks <= 0 or args.cpu_cap_seconds <= 0
            or not math.isfinite(args.heartbeat_seconds)
            or args.heartbeat_seconds < 1):
        parser.error("blocks/cpu cap must be positive and heartbeat at least one second")
    try:
        result = _run(args.output, blocks=args.blocks, cpu_cap=args.cpu_cap_seconds,
                      heartbeat_seconds=args.heartbeat_seconds)
    except BaseException:
        traceback.print_exc()
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())

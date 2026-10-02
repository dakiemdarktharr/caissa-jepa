"""Bounded Windows supervisor for the local V2.11 development fit panel."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
RUNNER = ROOT / "tools" / "v211_run_development_panel.py"
LIMITER_HELPER = ROOT / "tools" / "v29_development_panel_supervisor.py"
MEMORY_GATE_BYTES = 2_000_000_000
AVAILABLE_MEMORY_FLOOR_BYTES = 1_000_000_000
PROCESS_COMMIT_LIMIT_BYTES = 1_300_000_000
PROCESS_CPU_LIMIT_SECONDS = 4 * 60 * 60
PANEL_WALL_LIMIT_SECONDS = 6 * 60 * 60
STABLE_SAMPLE_INTERVAL_SECONDS = 20
STABLE_SAMPLE_COUNT = 4
PREFLIGHT_WAIT_LIMIT_SECONDS = 30 * 60
RESOURCE_SAMPLE_INTERVAL_SECONDS = 1
RUNNER_BOOTSTRAP = (
    "import runpy,sys; token=sys.stdin.buffer.read(1); sys.stdin.close(); "
    "(token == b'1') or sys.exit(97); script=sys.argv[1]; "
    "sys.argv=[script,*sys.argv[2:]]; runpy.run_path(script,run_name='__main__')")


def _sha(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _atomic_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp",
                                     dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(value, stream, sort_keys=True, indent=2, allow_nan=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _supervisor_impl():
    from tools.v29_development_panel_supervisor import _MemoryCpuJob, _available_memory
    return _MemoryCpuJob, _available_memory


def run_panel_supervised(dataset: Path, approval: Path, output: Path) -> dict:
    if os.name != "nt":
        raise OSError("V2.11 resource supervisor requires Windows")
    from two_player.v211_development import DATASET_ROOT, validate_spec

    validate_spec()
    dataset, approval, output = dataset.resolve(), approval.resolve(), output.resolve()
    data_root = (ROOT / "chess_data").resolve()
    if dataset != DATASET_ROOT:
        raise ValueError("V2.11 supervisor is limited to audited DEV09")
    if (data_root not in output.parents or output.exists()
            or DATASET_ROOT in output.parents or output in DATASET_ROOT.parents):
        raise ValueError("V2.11 output must be fresh and disjoint under ignored chess_data")
    if (ROOT / "chess_data") not in approval.parents or not approval.is_file():
        raise ValueError("V2.11 approval must exist under ignored chess_data")
    status_path = output.with_suffix(".supervisor.json")
    stdout_path = output.with_suffix(".stdout.log")
    stderr_path = output.with_suffix(".stderr.log")
    for path in (status_path, stdout_path, stderr_path):
        if path.exists():
            raise FileExistsError(f"refusing to overwrite supervisor artifact: {path}")
    helper_sha = _sha(LIMITER_HELPER)
    MemoryCpuJob, available_memory = _supervisor_impl()
    runner_sha = _sha(RUNNER)
    supervisor_sha = _sha(Path(__file__))
    samples = []

    def status(name, **fields):
        _atomic_json(status_path, {
            "schema": "caissa-jepa-v211-panel-supervisor-v01",
            "status": name, "dataset": str(dataset), "approval": str(approval),
            "output": str(output), "runner_sha256": runner_sha,
            "supervisor_sha256": supervisor_sha,
            "resource_helper_sha256": helper_sha,
            "memory_gate_bytes": MEMORY_GATE_BYTES,
            "available_memory_floor_bytes": AVAILABLE_MEMORY_FLOOR_BYTES,
            "process_commit_limit_bytes": PROCESS_COMMIT_LIMIT_BYTES,
            "process_cpu_limit_seconds": PROCESS_CPU_LIMIT_SECONDS,
            "panel_wall_limit_seconds": PANEL_WALL_LIMIT_SECONDS,
            "preflight_samples": samples, **fields})

    wait_started = time.perf_counter()
    while time.perf_counter() - wait_started < PREFLIGHT_WAIT_LIMIT_SECONDS:
        available, load = available_memory()
        samples.append({"available_physical_bytes": available,
                        "memory_load_percent": load,
                        "elapsed_seconds": round(time.perf_counter() - wait_started, 3)})
        if available < MEMORY_GATE_BYTES:
            samples.clear()
        else:
            samples = samples[-STABLE_SAMPLE_COUNT:]
        status("waiting_for_stable_memory", consecutive_passes=len(samples),
               current_available_memory_bytes=available)
        if len(samples) == STABLE_SAMPLE_COUNT:
            break
        time.sleep(STABLE_SAMPLE_INTERVAL_SECONDS)
    if len(samples) != STABLE_SAMPLE_COUNT:
        status("stopped_preflight_timeout", fit_started=False)
        return {"status": "stopped_preflight_timeout", "fit_started": False}
    available, _ = available_memory()
    if (available < MEMORY_GATE_BYTES or _sha(RUNNER) != runner_sha
            or _sha(Path(__file__)) != supervisor_sha
            or _sha(LIMITER_HELPER) != helper_sha):
        status("stopped_preflight", fit_started=False,
               current_available_memory_bytes=available)
        return {"status": "stopped_preflight", "fit_started": False}

    token = secrets.token_hex(32)
    command = [sys.executable, "-B", "-c", RUNNER_BOOTSTRAP, str(RUNNER),
               str(dataset), str(approval), str(output),
               "--supervision-token", token]
    child_environment = os.environ.copy()
    child_environment["CAISSA_V211_SUPERVISOR_TOKEN"] = token
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0) | \
        getattr(subprocess, "BELOW_NORMAL_PRIORITY_CLASS", 0)
    started = time.perf_counter()
    with stdout_path.open("xb") as stdout, stderr_path.open("xb") as stderr:
        process = subprocess.Popen(command, cwd=ROOT, stdin=subprocess.PIPE,
                                   stdout=stdout, stderr=stderr,
                                   creationflags=flags, env=child_environment)
        try:
            with MemoryCpuJob(process, memory_bytes=PROCESS_COMMIT_LIMIT_BYTES,
                              cpu_seconds=PROCESS_CPU_LIMIT_SECONDS) as job:
                status("running", child_pid=process.pid,
                       initial_available_memory_bytes=available,
                       child_released=False)
                assert process.stdin is not None
                process.stdin.write(b"1")
                process.stdin.flush()
                process.stdin.close()
                reason = None
                peak_working_set = 0
                while process.poll() is None:
                    elapsed = time.perf_counter() - started
                    available_now, _ = available_memory()
                    try:
                        _, observed_peak = job.working_set_bytes()
                    except OSError:
                        if process.poll() is not None:
                            break
                        raise
                    peak_working_set = max(peak_working_set, observed_peak)
                    if available_now < AVAILABLE_MEMORY_FLOOR_BYTES:
                        reason = "available_memory_floor"
                    elif elapsed > PANEL_WALL_LIMIT_SECONDS:
                        reason = "panel_wall_limit"
                    if reason:
                        status("terminating", termination_reason=reason,
                               elapsed_seconds=elapsed,
                               available_memory_bytes=available_now,
                               peak_working_set_bytes=peak_working_set)
                        job.terminate(94 if reason == "available_memory_floor" else 95)
                        break
                    time.sleep(RESOURCE_SAMPLE_INTERVAL_SECONDS)
                return_code = process.wait()
                if _sha(LIMITER_HELPER) != helper_sha:
                    reason = "resource_helper_changed"
                if return_code != 0 and reason is None:
                    reason = "runner_failed"
                if reason is not None and return_code == 0:
                    return_code = 96
                result = {"status": "complete" if return_code == 0 else "failed",
                          "fit_started": True, "return_code": return_code,
                          "termination_reason": reason,
                          "elapsed_seconds": time.perf_counter() - started,
                          "peak_working_set_bytes": peak_working_set,
                          "output": str(output)}
                fields = {key: value for key, value in result.items()
                          if key != "status"}
                status(result["status"], **fields)
                if return_code == 0:
                    panel_path = output / "panel.json"
                    panel = json.loads(panel_path.read_text(encoding="utf-8"))
                    if panel.get("status") != "complete":
                        raise ValueError("fit child exited successfully without a complete ledger")
                    panel["supervisor_attestation"] = {
                        "status_path": str(status_path.resolve()),
                        "status_sha256": _sha(status_path),
                        "supervisor_code_sha256": supervisor_sha,
                        "resource_helper_sha256": helper_sha,
                        "runner_code_sha256": runner_sha,
                        "job_object_assigned": True,
                        "process_commit_limit_bytes": PROCESS_COMMIT_LIMIT_BYTES,
                        "process_cpu_limit_seconds": PROCESS_CPU_LIMIT_SECONDS,
                        "available_memory_floor_bytes": AVAILABLE_MEMORY_FLOOR_BYTES,
                        "memory_gate_bytes": MEMORY_GATE_BYTES,
                        "stable_preflight_samples": samples,
                        "peak_working_set_bytes": peak_working_set,
                        "elapsed_seconds": result["elapsed_seconds"],
                        "termination_reason": reason,
                    }
                    _atomic_json(panel_path, panel)
                    result["panel_ledger_sha256"] = _sha(panel_path)
                return result
        except BaseException as exc:
            if process.poll() is None:
                process.kill()
                process.wait()
            status("supervisor_error", fit_started=True,
                   error_type=type(exc).__name__, error=str(exc))
            raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset", type=Path)
    parser.add_argument("approval", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    print(json.dumps(run_panel_supervised(args.dataset, args.approval, args.output),
                     sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()

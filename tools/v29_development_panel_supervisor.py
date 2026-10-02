"""Resource-guarded launcher for the frozen V2.9 development fit panel.

The child is constrained by per-process and per-job committed-memory limits and
a CPU-time limit in a Windows Job Object. The supervisor waits for stable free
memory first and samples the reactive available-RAM guard once per second. It
runs below normal priority and writes only lifecycle/resource status. It never
inspects training metrics.
"""
from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "tools" / "v29_run_development_panel.py"
APPROVAL_PATH = ROOT / "chess_data" / "v29_data_dev09_approval.json"
MEMORY_GATE_BYTES = 2_000_000_000
AVAILABLE_MEMORY_FLOOR_BYTES = 1_000_000_000
PROCESS_COMMIT_LIMIT_BYTES = 1_300_000_000
PROCESS_CPU_LIMIT_SECONDS = 4 * 60 * 60
PANEL_WALL_LIMIT_SECONDS = 6 * 60 * 60
STABLE_SAMPLE_INTERVAL_SECONDS = 20
STABLE_SAMPLE_COUNT = 4
PREFLIGHT_WAIT_LIMIT_SECONDS = 30 * 60
HEARTBEAT_INTERVAL_SECONDS = 5
RESOURCE_SAMPLE_INTERVAL_SECONDS = 1
RUNNER_BOOTSTRAP = (
    "import runpy,sys; token=sys.stdin.buffer.read(1); "
    "sys.stdin.close(); "
    "(token == b'1') or sys.exit(97); "
    "script=sys.argv[1]; sys.argv=[script,*sys.argv[2:]]; "
    "runpy.run_path(script,run_name='__main__')")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


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


def _available_memory() -> tuple[int, int]:
    class MemoryStatus(ctypes.Structure):
        _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong),
                    ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong),
                    ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]

    status = MemoryStatus()
    status.dwLength = ctypes.sizeof(status)
    if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
        raise ctypes.WinError(ctypes.get_last_error())
    return int(status.ullAvailPhys), int(status.dwMemoryLoad)


class _MemoryCpuJob:
    """Hard process/job commit and per-process user CPU-time limits."""

    def __init__(self, process: subprocess.Popen, *, memory_bytes: int,
                 cpu_seconds: int):
        if os.name != "nt":
            raise OSError("V2.9 panel resource supervisor requires Windows")
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
                ("Affinity", ctypes.c_size_t), ("PriorityClass", wintypes.DWORD),
                ("SchedulingClass", wintypes.DWORD)]

        class ExtendedLimit(ctypes.Structure):
            _fields_ = [("BasicLimitInformation", BasicLimit), ("IoInfo", IoCounters),
                        ("ProcessMemoryLimit", ctypes.c_size_t),
                        ("JobMemoryLimit", ctypes.c_size_t),
                        ("PeakProcessMemoryUsed", ctypes.c_size_t),
                        ("PeakJobMemoryUsed", ctypes.c_size_t)]

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
        class ProcessMemoryCounters(ctypes.Structure):
            _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD),
                        ("PeakWorkingSetSize", ctypes.c_size_t),
                        ("WorkingSetSize", ctypes.c_size_t),
                        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                        ("PagefileUsage", ctypes.c_size_t),
                        ("PeakPagefileUsage", ctypes.c_size_t)]
        self._psapi = ctypes.WinDLL("psapi", use_last_error=True)
        self._psapi.GetProcessMemoryInfo.argtypes = [
            wintypes.HANDLE, ctypes.POINTER(ProcessMemoryCounters), wintypes.DWORD]
        self._psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
        self._kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL,
                                                wintypes.DWORD]
        self._kernel32.OpenProcess.restype = wintypes.HANDLE
        self._memory_handle = self._kernel32.OpenProcess(
            0x0400 | 0x0010, False, process.pid)
        if not self._memory_handle:
            error = ctypes.get_last_error()
            self.close()
            raise ctypes.WinError(error)
        self._memory_counters_type = ProcessMemoryCounters
        self._handle = self._kernel32.CreateJobObjectW(None, None)
        if not self._handle:
            error = ctypes.get_last_error()
            self.close()
            raise ctypes.WinError(error)
        limits = ExtendedLimit()
        limits.BasicLimitInformation.PerProcessUserTimeLimit = int(cpu_seconds * 1e7)
        # PROCESS_TIME | PROCESS_MEMORY | JOB_MEMORY | KILL_ON_JOB_CLOSE.
        limits.BasicLimitInformation.LimitFlags = 0x2 | 0x100 | 0x200 | 0x2000
        limits.ProcessMemoryLimit = memory_bytes
        limits.JobMemoryLimit = memory_bytes
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

    def working_set_bytes(self) -> tuple[int, int]:
        counters = self._memory_counters_type()
        counters.cb = ctypes.sizeof(counters)
        if not self._psapi.GetProcessMemoryInfo(
                self._memory_handle, ctypes.byref(counters), counters.cb):
            raise ctypes.WinError(ctypes.get_last_error())
        return int(counters.WorkingSetSize), int(counters.PeakWorkingSetSize)

    def terminate(self, exit_code: int) -> None:
        if self._handle and not self._kernel32.TerminateJobObject(
                self._handle, exit_code):
            raise ctypes.WinError(ctypes.get_last_error())

    def close(self) -> None:
        memory_handle = getattr(self, "_memory_handle", None)
        if memory_handle:
            self._kernel32.CloseHandle(memory_handle)
            self._memory_handle = None
        handle = getattr(self, "_handle", None)
        if handle:
            self._kernel32.CloseHandle(handle)
            self._handle = None

    def __enter__(self):
        return self

    def __exit__(self, *_exc):
        self.close()


def run_panel_supervised(dataset: Path, approval: Path, output: Path) -> dict:
    if os.name != "nt":
        raise OSError("V2.9 panel resource supervisor requires Windows")
    dataset, approval, output = dataset.resolve(), approval.resolve(), output.resolve()
    data_root = (ROOT / "chess_data").resolve()
    audited_root = (ROOT / "chess_data" / "v28_data_dev09").resolve()
    if dataset != audited_root:
        raise ValueError("supervised panel is limited to the exact audited DEV09 dataset")
    if approval != APPROVAL_PATH.resolve():
        raise ValueError("supervised panel requires the exact local V2.9 development grant")
    if (output == data_root or data_root not in output.parents
            or output == audited_root or audited_root in output.parents
            or output in audited_root.parents):
        raise ValueError("panel output must be a fresh child of ignored chess_data")
    for path in (output, output.with_suffix(".supervisor.json"),
                 output.with_suffix(".stdout.log"), output.with_suffix(".stderr.log")):
        if path.exists():
            raise FileExistsError(f"refusing to overwrite existing pilot/panel artifact: {path}")
    status_path = output.with_suffix(".supervisor.json")
    stdout_path = output.with_suffix(".stdout.log")
    stderr_path = output.with_suffix(".stderr.log")
    runner_sha = _sha256(RUNNER)
    supervisor_sha = _sha256(Path(__file__))
    wait_start = time.perf_counter()
    samples: list[dict] = []

    def status(name: str, **fields) -> None:
        _atomic_json(status_path, {
            "schema": "caissa-jepa-v29-development-panel-supervisor-v01",
            "status": name, "dataset": str(dataset), "approval": str(approval),
            "output": str(output), "panel_runner_sha256": runner_sha,
            "supervisor_sha256": supervisor_sha,
            "memory_gate_bytes": MEMORY_GATE_BYTES,
            "available_memory_floor_bytes": AVAILABLE_MEMORY_FLOOR_BYTES,
            "available_memory_floor_is_reactive": True,
            "resource_sample_interval_seconds": RESOURCE_SAMPLE_INTERVAL_SECONDS,
            "process_commit_limit_bytes": PROCESS_COMMIT_LIMIT_BYTES,
            "job_commit_limit_bytes": PROCESS_COMMIT_LIMIT_BYTES,
            "process_cpu_limit_seconds": PROCESS_CPU_LIMIT_SECONDS,
            "panel_wall_limit_seconds": PANEL_WALL_LIMIT_SECONDS,
            "preflight_samples": samples, **fields})

    status("waiting_for_stable_memory", wait_started_unix=time.time())
    while time.perf_counter() - wait_start < PREFLIGHT_WAIT_LIMIT_SECONDS:
        available, load = _available_memory()
        samples.append({"available_physical_bytes": available,
                        "memory_load_percent": load,
                        "elapsed_seconds": round(time.perf_counter() - wait_start, 3)})
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
        status("stopped_preflight_timeout", fit_started=False,
               wait_elapsed_seconds=time.perf_counter() - wait_start)
        return {"status": "stopped_preflight_timeout", "fit_started": False}

    available, _ = _available_memory()
    if available < MEMORY_GATE_BYTES:
        status("stopped_preflight", fit_started=False,
               current_available_memory_bytes=available)
        return {"status": "stopped_preflight", "fit_started": False}
    if _sha256(RUNNER) != runner_sha or _sha256(Path(__file__)) != supervisor_sha:
        status("stopped_source_changed", fit_started=False,
               source_hash_rechecked_before_spawn=True)
        return {"status": "stopped_source_changed", "fit_started": False}
    # The bootstrap blocks on a parent release byte. The runner cannot import
    # or allocate model/data memory before Job Object assignment succeeds.
    command = [sys.executable, "-B", "-c", RUNNER_BOOTSTRAP, str(RUNNER),
               str(dataset), str(approval), str(output)]
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0) | \
            getattr(subprocess, "BELOW_NORMAL_PRIORITY_CLASS", 0)
    started = time.perf_counter()
    with stdout_path.open("xb") as stdout, stderr_path.open("xb") as stderr:
        process = subprocess.Popen(command, cwd=ROOT, stdin=subprocess.PIPE,
                                   stdout=stdout, stderr=stderr,
                                   creationflags=flags)
        try:
            with _MemoryCpuJob(process, memory_bytes=PROCESS_COMMIT_LIMIT_BYTES,
                               cpu_seconds=PROCESS_CPU_LIMIT_SECONDS) as job:
                status("running", child_pid=process.pid,
                       panel_started_unix=time.time(), initial_available_memory_bytes=available,
                       child_released=False)
                assert process.stdin is not None
                process.stdin.write(b"1")
                process.stdin.flush()
                process.stdin.close()
                termination_reason = None
                peak_working_set = 0
                next_heartbeat = time.perf_counter()
                while process.poll() is None:
                    elapsed = time.perf_counter() - started
                    available_now, _ = _available_memory()
                    try:
                        _, observed_peak = job.working_set_bytes()
                    except OSError:
                        if process.poll() is not None:
                            break
                        raise
                    peak_working_set = max(peak_working_set, observed_peak)
                    if available_now < AVAILABLE_MEMORY_FLOOR_BYTES:
                        termination_reason = "available_memory_floor"
                    elif elapsed >= PANEL_WALL_LIMIT_SECONDS:
                        termination_reason = "panel_wall_limit"
                    if termination_reason is not None:
                        status("terminating_resource_limit", child_pid=process.pid,
                               termination_reason=termination_reason,
                               elapsed_seconds=elapsed,
                               peak_working_set_bytes=peak_working_set,
                               available_memory_bytes=available_now)
                        job.terminate(94 if termination_reason == "available_memory_floor" else 95)
                        break
                    if time.perf_counter() >= next_heartbeat:
                        status("running", child_pid=process.pid, elapsed_seconds=elapsed,
                               peak_working_set_bytes=peak_working_set,
                               available_memory_bytes=available_now,
                               child_released=True)
                        next_heartbeat = time.perf_counter() + HEARTBEAT_INTERVAL_SECONDS
                    time.sleep(RESOURCE_SAMPLE_INTERVAL_SECONDS)
                return_code = process.wait()
        except BaseException:
            if process.poll() is None:
                process.terminate()
                process.wait(timeout=10)
            status("supervisor_failed", child_pid=process.pid,
                   elapsed_seconds=time.perf_counter() - started)
            raise

    panel_manifest = output / "panel.json"
    complete = False
    if panel_manifest.is_file():
        try:
            panel = json.loads(panel_manifest.read_text(encoding="utf-8"))
            complete = (panel.get("status") == "completed"
                        and panel.get("expected_runs") == 60
                        and len(panel.get("runs", [])) == 60
                        and all(row.get("status") == "completed"
                                for row in panel["runs"]))
        except (OSError, json.JSONDecodeError, TypeError):
            complete = False
    final_status = "completed" if return_code == 0 and complete else "failed_or_incomplete"
    result = {"status": final_status, "fit_started": True,
              "return_code": return_code, "elapsed_seconds": time.perf_counter() - started,
              "peak_working_set_bytes": peak_working_set,
              "panel_path": str(panel_manifest) if panel_manifest.is_file() else None,
              "panel_sha256": _sha256(panel_manifest) if panel_manifest.is_file() else None,
              "runner_stdout_path": str(stdout_path),
              "runner_stderr_path": str(stderr_path),
              "termination_reason": termination_reason}
    status(final_status, **{key: value for key, value in result.items()
                            if key not in ("status", "fit_started")})
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset", type=Path)
    parser.add_argument("approval", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    result = run_panel_supervised(args.dataset, args.approval, args.output)
    print(json.dumps(result, sort_keys=True, indent=2, allow_nan=False))
    if result["status"] != "completed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()

"""No-inference normal-exit receipt collector for a transient user service.

This version is intentionally limited to one synthetic, non-inference worker.
It does not collect kernel OOM records or certify OOM supervision. Unit and IPC
evidence are retained on any failure before the pre-cleanup receipt is durable.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import secrets
import selectors
import stat
import subprocess
import sys
import time
from typing import Any, Sequence

from two_player import v212_live_supervision_v01 as live
from two_player import v212_supervision_receipt_v02 as assembler
from two_player import v212_worker_ipc as ipc

SCHEMA = "caissa.v212.no-inference-live-smoke.v01"
MARKER_PREFIX = "CAISSA_V212_NO_INFERENCE_MARKER "
MAX_COMMAND_OUTPUT = 4_194_304
MAX_JOURNAL_RECORD_BYTES = 65_536
MAX_JOURNAL_RECORDS = 1024
MEMORY_MAX = 134_217_728
MEMORY_HIGH = 100_663_296
FILE_SIZE_LIMIT = 65_536
RUNTIME_LIMIT_SECONDS = 8


class CollectorError(RuntimeError):
    """No trustworthy pre-cleanup receipt could be produced."""


def _run(argv: Sequence[str], *, timeout: float, max_output: int = 65_536,
         stdout: int = subprocess.PIPE, deadline: float | None = None) -> bytes:
    """Run a command with a hard wall-clock and streaming output bound."""
    name = Path(argv[0]).name
    end = time.monotonic() + timeout
    if deadline is not None:
        end = min(end, deadline)
    if end <= time.monotonic():
        raise CollectorError(f"{name} could not start before caller deadline")
    try:
        proc = subprocess.Popen(
            list(argv), stdin=subprocess.DEVNULL, stdout=stdout,
            stderr=subprocess.DEVNULL, close_fds=True)
    except OSError as exc:
        raise CollectorError(f"{name} failed to start") from exc
    data = bytearray()
    try:
        if proc.stdout is not None:
            with selectors.DefaultSelector() as selector:
                selector.register(proc.stdout, selectors.EVENT_READ)
                while True:
                    remaining = end - time.monotonic()
                    if remaining <= 0:
                        raise CollectorError(f"{name} timed out")
                    ready = selector.select(remaining)
                    if not ready:
                        raise CollectorError(f"{name} timed out")
                    chunk = os.read(proc.stdout.fileno(), min(65_536, max_output + 1 - len(data)))
                    if not chunk:
                        selector.unregister(proc.stdout)
                        break
                    data.extend(chunk)
                    if len(data) > max_output:
                        raise CollectorError(f"{name} output exceeded its byte bound")
        remaining = end - time.monotonic()
        if remaining <= 0:
            raise CollectorError(f"{name} timed out")
        returncode = proc.wait(timeout=remaining)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise CollectorError(f"{name} failed or timed out") from exc
    finally:
        if proc.poll() is None:
            proc.kill()
            try:
                proc.wait(timeout=0.5)
            except subprocess.TimeoutExpired:
                pass
        if proc.stdout is not None:
            proc.stdout.close()
    if deadline is not None and time.monotonic() >= deadline:
        raise CollectorError("caller-observed response deadline expired")
    if returncode != 0:
        raise CollectorError(f"{name} exited with status {returncode}")
    return bytes(data)


def _show(unit: str, *, timeout: float = 1.0, deadline: float | None = None) -> dict[str, str]:
    props = ("LoadState", "InvocationID", "ControlGroup", "ActiveState",
             "SubState", "Result", "ExecMainStatus", "MainPID",
             "EffectiveMemoryMax", "EffectiveMemoryHigh", "MemorySwapMax",
             "LimitFSIZE", "RuntimeMaxUSec", "Restart", "OOMPolicy",
             "RemainAfterExit")
    output = _run(("systemctl", "--user", "show", "--no-pager",
                   "--property=" + ",".join(props), unit), timeout=timeout,
                  deadline=deadline)
    try:
        return live.parse_systemd_show(output.decode("utf-8", errors="strict"))
    except (UnicodeError, live.LiveEvidenceError) as exc:
        raise CollectorError("systemd properties were not valid bounded text") from exc


def _monotonic_us() -> int:
    return time.monotonic_ns() // 1000


def _check_deadline(deadline: float) -> None:
    if time.monotonic() >= deadline:
        raise CollectorError("caller-observed response deadline expired")


def _workspace_path_state(workspace: ipc.WorkerIPCWorkspace) -> str:
    try:
        info = os.lstat(workspace.directory)
    except FileNotFoundError:
        return "absent_at_reconciliation_check"
    except OSError:
        return "unknown_at_reconciliation_check"
    if (info.st_dev == workspace.directory_device
            and info.st_ino == workspace.directory_inode
            and stat.S_ISDIR(info.st_mode)):
        return "original_directory_present_at_reconciliation_check"
    return "path_replaced_at_reconciliation_check"


def _boot_id() -> str:
    try:
        value = Path("/proc/sys/kernel/random/boot_id").read_text(encoding="ascii").strip()
        return assembler.normalize_boot_id(value)
    except (OSError, UnicodeError, assembler.ReceiptError) as exc:
        raise CollectorError("host boot ID is unavailable or malformed") from exc


def _proc_cgroup(pid: int | None = None) -> str:
    path = Path("/proc/self/cgroup") if pid is None else Path(f"/proc/{pid}/cgroup")
    try:
        lines = path.read_text(encoding="ascii").splitlines()
    except (OSError, UnicodeError) as exc:
        raise CollectorError("process cgroup placement is unavailable") from exc
    matches = [line[3:] for line in lines if line.startswith("0::")]
    if len(matches) != 1:
        raise CollectorError("process is not in one unified cgroup-v2 hierarchy")
    try:
        return assembler._cgroup(matches[0])
    except assembler.ReceiptError as exc:
        raise CollectorError("process cgroup path is malformed") from exc


def _cgroup_scalar(control_group: str, name: str) -> str:
    if name not in {"memory.max", "memory.high", "memory.swap.max"}:
        raise CollectorError("unsupported cgroup property")
    root = Path("/sys/fs/cgroup")
    try:
        group = assembler._cgroup(control_group)
        root_real = root.resolve(strict=True)
        directory = root.joinpath(*group.lstrip("/").split("/")).resolve(strict=True)
        if not directory.is_relative_to(root_real) or not directory.is_dir():
            raise CollectorError("worker cgroup is outside the cgroup-v2 root")
        path = directory / name
        fd = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    except CollectorError:
        raise
    except (OSError, assembler.ReceiptError) as exc:
        raise CollectorError(f"worker {name} is unavailable") from exc
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode):
            raise CollectorError(f"worker {name} is not a regular cgroup file")
        data = os.read(fd, 128)
        if len(data) == 128:
            raise CollectorError(f"worker {name} exceeds its read bound")
    finally:
        os.close(fd)
    try:
        value = data.decode("ascii").strip()
    except UnicodeDecodeError as exc:
        raise CollectorError(f"worker {name} is not ASCII") from exc
    if not value or "\n" in value:
        raise CollectorError(f"worker {name} is malformed")
    return value


def _journal_markers(unit: str, *, invocation_id: str, worker_cgroup: str,
                     deadline: float | None = None) -> list[dict[str, Any]]:
    output = _run(("journalctl", "--user", "--unit=" + unit,
                   "--output=json", "--no-pager", "--lines=1025"),
                  timeout=2.0, max_output=MAX_COMMAND_OUTPUT, deadline=deadline)
    records: list[dict[str, Any]] = []
    if output and not output.endswith(b"\n"):
        raise CollectorError("unit journal ended with a partial record")
    lines = output.splitlines()
    if len(lines) > MAX_JOURNAL_RECORDS:
        raise CollectorError("unit journal exceeds its record bound")
    for line in lines:
        if len(line) > MAX_JOURNAL_RECORD_BYTES:
            raise CollectorError("unit journal record exceeds its byte bound")
        try:
            record = json.loads(line.decode("utf-8", errors="strict"))
        except (UnicodeError, json.JSONDecodeError) as exc:
            raise CollectorError("unit journal contains malformed JSON") from exc
        if not isinstance(record, dict):
            raise CollectorError("unit journal record is not an object")
        message = record.get("MESSAGE")
        if isinstance(message, str) and message.startswith(MARKER_PREFIX):
            records.append(record)
    if len(records) != 1:
        raise CollectorError("unit journal must contain exactly one worker marker")
    record = records[0]
    record_unit = record.get("_SYSTEMD_USER_UNIT", record.get("_SYSTEMD_UNIT"))
    if record_unit != unit:
        raise CollectorError("worker marker unit metadata did not match the requested unit")
    if record.get("_SYSTEMD_INVOCATION_ID") != invocation_id:
        raise CollectorError("worker marker invocation metadata did not match the active invocation")
    if record.get("_SYSTEMD_CGROUP") != worker_cgroup:
        raise CollectorError("worker marker cgroup metadata did not match the active worker cgroup")
    return records


def _verify_effective_properties(properties: dict[str, str]) -> None:
    expected = {
        "EffectiveMemoryMax": str(MEMORY_MAX),
        "EffectiveMemoryHigh": str(MEMORY_HIGH),
        "MemorySwapMax": "0",
        "LimitFSIZE": str(FILE_SIZE_LIMIT),
        # systemctl show formats this usec property as a timespan (for example, 8s).
        "RuntimeMaxUSec": f"{RUNTIME_LIMIT_SECONDS}s",
        "Restart": "no", "OOMPolicy": "kill",
        "RemainAfterExit": "yes",
    }
    for key, value in expected.items():
        if properties.get(key, "").lower() != value.lower():
            raise CollectorError(f"effective worker property {key} did not match")


def _worker_source() -> str:
    # This synthetic worker only validates file-backed IPC and journald binding.
    return (
        "import json,os,sys,syslog,time\n"
        "request=json.load(sys.stdin)\n"
        "if request.get('schema') != 'caissa.synthetic.request.v01': sys.exit(21)\n"
        "invocation=os.environ.get('INVOCATION_ID','')\n"
        "if len(invocation) != 32: sys.exit(22)\n"
        "time.sleep(0.45)\n"
        f"syslog.syslog(syslog.LOG_INFO, {MARKER_PREFIX!r}+invocation)\n"
        "time.sleep(0.25)\n"
        "json.dump({'schema':'caissa.synthetic.response.v01',"
        "'nonce':request['nonce'],'status':'ok'},sys.stdout,"
        "separators=(',',':'),allow_nan=False)\n"
        "sys.stdout.write('\\n');sys.stdout.flush()\n"
    )


def run_no_inference_smoke(*, receipt_path: Path, timeout_seconds: float = 10.0
                           ) -> dict[str, Any]:
    """Run one synthetic worker and persist its same-invocation receipt.

    On any failure after dispatch and before receipt durability, leave the
    retained unit and private IPC directory in place for evidence reconciliation.
    The caller must stop/remove them only after examining the reported unit.
    The timeout is a no-late-success deadline through cleanup. Blocking local
    persistence/fsync cannot be safely preempted, so timeout reporting may be
    delayed if the filesystem blocks; no late result is returned as success.
    """
    if (isinstance(timeout_seconds, bool) or not isinstance(timeout_seconds, (int, float))
            or not 2 <= timeout_seconds <= 30):
        raise ValueError("timeout_seconds must be between 2 and 30")
    try:
        destination = live.validate_receipt_destination(Path(receipt_path))
    except live.LiveEvidenceError as exc:
        raise CollectorError("receipt destination failed pre-dispatch validation") from exc
    request_started = _monotonic_us()
    deadline = time.monotonic() + timeout_seconds
    boot = _boot_id()
    caller_cgroup = _proc_cgroup()
    nonce = secrets.token_hex(16)
    workspace: ipc.WorkerIPCWorkspace | None = None
    unit = "caissa-v212-smoke-" + secrets.token_hex(8) + ".service"
    started = False
    persistence_attempted = False
    persisted = False
    unit_stopped = False
    workspace_cleaned = False
    active: dict[str, Any] | None = None
    events_before: dict[str, Any] | None = None
    events_after: dict[str, Any] | None = None
    response: dict[str, Any] | None = None
    try:
        workspace = ipc.create_workspace({
            "schema": "caissa.synthetic.request.v01",
            "nonce": nonce,
        })
        command = ["systemd-run", "--user", "--unit=" + unit,
                   "--remain-after-exit",
                   "--property=MemoryMax=128M",
                   "--property=MemoryHigh=96M",
                   "--property=MemorySwapMax=0",
                   "--property=RuntimeMaxSec=8s",
                   "--property=Restart=no",
                   "--property=OOMPolicy=kill",
                   "--property=LimitFSIZE=65536",
                   "--property=StandardInput=file:" + str(workspace.request_path),
                   "--property=StandardOutput=truncate:" + str(workspace.response_path),
                   "--property=StandardError=null",
                   sys.executable, "-B", "-c", _worker_source()]
        _check_deadline(deadline)
        started = True
        _run(command, timeout=2.0, deadline=deadline)
        _check_deadline(deadline)
        active_props: dict[str, str] | None = None
        while time.monotonic() < deadline:
            props = _show(unit, timeout=1.0, deadline=deadline)
            _check_deadline(deadline)
            if props.get("LoadState") == "loaded" and props.get("ActiveState") == "active" \
                    and props.get("SubState") in {"start", "running"}:
                active_props = props
                break
            time.sleep(0.02)
        if active_props is None:
            raise CollectorError("transient worker did not reach active state before deadline")
        active_time = _monotonic_us()
        active = live.snapshot_from_properties(
            unit=unit, properties=active_props, boot_id=boot,
            captured_monotonic_us=active_time, active=True)
        worker_cgroup = active["control_group"]
        invocation_id = active["invocation_id"]
        main_pid_text = active_props.get("MainPID", "")
        if not main_pid_text.isdecimal() or int(main_pid_text) <= 1:
            raise CollectorError("active transient service has no main process")
        worker_proc_cgroup = _proc_cgroup(int(main_pid_text))
        if worker_proc_cgroup != worker_cgroup or worker_cgroup == caller_cgroup:
            raise CollectorError("worker and caller cgroup placement did not verify")
        _verify_effective_properties(active_props)
        if (_cgroup_scalar(worker_cgroup, "memory.max") != str(MEMORY_MAX)
                or _cgroup_scalar(worker_cgroup, "memory.high") != str(MEMORY_HIGH)
                or _cgroup_scalar(worker_cgroup, "memory.swap.max") != "0"):
            raise CollectorError("live worker cgroup limits did not match manager properties")
        _check_deadline(deadline)
        events_before = live.read_memory_events_local(
            cgroup_root=Path("/sys/fs/cgroup"), control_group=worker_cgroup,
            boot_id=boot, captured_monotonic_us=_monotonic_us())
        time.sleep(0.08)
        events_after = live.read_memory_events_local(
            cgroup_root=Path("/sys/fs/cgroup"), control_group=worker_cgroup,
            boot_id=boot, captured_monotonic_us=_monotonic_us())
        _check_deadline(deadline)

        exited_props: dict[str, str] | None = None
        while time.monotonic() < deadline:
            props = _show(unit, timeout=1.0, deadline=deadline)
            _check_deadline(deadline)
            if ((props.get("ActiveState"), props.get("SubState")) in {
                    ("active", "exited"), ("inactive", "exited"),
                    ("failed", "failed")}):
                exited_props = props
                break
            time.sleep(0.02)
        if exited_props is None:
            raise CollectorError("transient worker did not exit before caller deadline")
        manager_snapshot = live.snapshot_from_properties(
            unit=unit, properties=exited_props, boot_id=boot,
            captured_monotonic_us=_monotonic_us(), active=False)
        if manager_snapshot["result"] != "success" or manager_snapshot["main_status"] != 0:
            raise CollectorError("synthetic worker did not exit successfully")
        response = ipc.read_response(workspace)
        if (response.get("schema") != "caissa.synthetic.response.v01"
                or response.get("nonce") != nonce
                or response.get("status") != "ok"):
            raise CollectorError("synthetic worker response did not match its schema")
        records = _journal_markers(
            unit, invocation_id=invocation_id, worker_cgroup=worker_cgroup,
            deadline=deadline)
        _check_deadline(deadline)
        if records[0].get("MESSAGE") != MARKER_PREFIX + invocation_id:
            raise CollectorError("unit marker did not carry the manager invocation ID")
        receipt = assembler.assemble_receipt(
            requested_unit=unit, request_boot_id=boot,
            request_started_monotonic_us=request_started,
            worker_snapshot=active, manager_snapshot=manager_snapshot,
            journal_records=records, events_before=events_before,
            events_after=events_after)
        receipt_bytes = json.dumps(receipt, sort_keys=True, separators=(",", ":"),
                                   ensure_ascii=False, allow_nan=False).encode("utf-8")
        envelope = {
            "schema": SCHEMA,
            "no_inference": True,
            "collector_source_sha256": hashlib.sha256(
                Path(__file__).read_bytes()).hexdigest(),
            "kernel_oom_journal": "not_collected_no_oom_operation",
            "request_sha256": hashlib.sha256(
                json.dumps({"schema": "caissa.synthetic.request.v01",
                            "nonce": nonce}, sort_keys=True, separators=(",", ":"),
                           ensure_ascii=False, allow_nan=False).encode("utf-8")).hexdigest(),
            "response_sha256": hashlib.sha256(
                json.dumps(response, sort_keys=True, separators=(",", ":"),
                           ensure_ascii=False, allow_nan=False).encode("utf-8")).hexdigest(),
            "receipt_sha256": hashlib.sha256(receipt_bytes).hexdigest(),
            "runtime": {
                "worker_cgroup": worker_cgroup,
                "caller_cgroup": caller_cgroup,
                "effective_memory_max": MEMORY_MAX,
                "effective_memory_high": MEMORY_HIGH,
                "memory_swap_max": 0,
                "limit_fsize": FILE_SIZE_LIMIT,
                "restart": "no", "oom_policy": "kill",
                "counter_source": "memory.events.local",
            },
            "receipt": receipt,
        }
        _check_deadline(deadline)
        persistence_attempted = True
        live.persist_receipt_once(destination, envelope)
        persisted = True
        _check_deadline(deadline)
        _run(("systemctl", "--user", "stop", unit), timeout=2.0,
             stdout=subprocess.DEVNULL, deadline=deadline)
        after_stop = _show(unit, timeout=1.0, deadline=deadline)
        if after_stop.get("LoadState") != "not-found":
            raise CollectorError("transient unit remained loaded after cleanup")
        unit_stopped = True
        ipc.cleanup_workspace(workspace)
        workspace_cleaned = True
        _check_deadline(deadline)
        return {"unit": unit, "receipt_path": str(destination),
                "invocation_id": invocation_id,
                "worker_cgroup": worker_cgroup,
                "caller_cgroup": caller_cgroup,
                "response_valid": True, "receipt_persisted_before_cleanup": True,
                "unit_load_state_after_cleanup": "not-found"}
    except KeyboardInterrupt as exc:
        if not started and workspace is not None and not workspace_cleaned:
            try:
                ipc.cleanup_workspace(workspace)
                workspace_cleaned = True
            except ipc.WorkerIPCError:
                pass
        if started:
            receipt_state = ("receipt_persisted" if persisted else
                             "receipt_publication_or_durability_uncertain"
                             if persistence_attempted else "receipt_not_attempted")
            unit_state = "unit_stopped" if unit_stopped else "unit_retained_or_state_unknown"
            ipc_state = ("ipc_workspace_cleaned" if workspace_cleaned
                         else _workspace_path_state(workspace))
            context = (f"{receipt_state} receipt_path={destination} {unit_state} "
                       f"unit={unit} {ipc_state} ipc_directory={workspace.directory}")
        elif workspace is None:
            context = "predispatch_ipc_workspace_not_created"
        elif workspace_cleaned:
            context = f"predispatch_ipc_workspace_cleaned ipc_directory={workspace.directory}"
        else:
            context = (f"predispatch_ipc_{_workspace_path_state(workspace)} "
                       f"ipc_directory={workspace.directory}")
        prior = str(exc)
        exc.args = ((prior + "; " if prior else "") + context,)
        raise
    except Exception as exc:
        predispatch_cleanup_error: str | None = None
        if not started and workspace is not None and not workspace_cleaned:
            try:
                ipc.cleanup_workspace(workspace)
                workspace_cleaned = True
            except ipc.WorkerIPCError as cleanup_exc:
                predispatch_cleanup_error = type(cleanup_exc).__name__
        if isinstance(exc, (CollectorError, ipc.WorkerIPCError)):
            detail = str(exc)
        else:
            detail = f"collector failed with {type(exc).__name__}"
        if started:
            if persisted:
                receipt_state = "receipt_persisted"
            elif persistence_attempted:
                receipt_state = "receipt_publication_or_durability_uncertain"
            else:
                receipt_state = "receipt_not_attempted"
            unit_state = "unit_stopped" if unit_stopped else "unit_retained_or_state_unknown"
            ipc_state = ("ipc_workspace_cleaned" if workspace_cleaned
                         else _workspace_path_state(workspace))
            detail += (f"; {receipt_state} receipt_path={destination} "
                       f"{unit_state} unit={unit} {ipc_state} "
                       f"ipc_directory={workspace.directory} for reconciliation")
        elif workspace is None:
            detail += "; transient worker was not dispatched and IPC workspace creation did not complete"
        elif predispatch_cleanup_error is not None:
            detail += (f"; predispatch_ipc_cleanup_failed={predispatch_cleanup_error} "
                       f"{_workspace_path_state(workspace)} "
                       f"ipc_directory={workspace.directory} for reconciliation")
        raise CollectorError(detail) from exc

"""No-inference transient-service smoke for the armed release protocol.

This version composes the private release FIFO, deadline-bound token verifier,
systemd/cgroup evidence capture, and receipt-before-cleanup path. Its worker
callback only writes a journal marker and a synthetic JSON response; it never
imports CAISSA model/search code.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
import time
from typing import Any

from two_player import v212_armed_protocol_v01 as armed
from two_player import v212_live_supervision_v01 as live
from two_player import v212_release_token_v01 as release
from two_player import v212_supervision_collector_v01 as collector
from two_player import v212_supervision_receipt_v02 as assembler
from two_player import v212_worker_ipc as ipc


SCHEMA = "caissa.v212.armed-no-inference-smoke.v01"
REQUEST_SCHEMA = "caissa.synthetic.armed-request.v01"
RESPONSE_SCHEMA = "caissa.v212.armed-no-inference-response.v01"
MARKER_PREFIX = collector.MARKER_PREFIX
WORKER_MODULES = (
    "two_player/v212_worker_ipc.py",
    "two_player/v212_release_token_v01.py",
    "two_player/v212_armed_protocol_v01.py",
)
HOST_EVIDENCE_MODULES = (
    "two_player/v212_armed_service_smoke_v01.py",
    "two_player/v212_live_supervision_v01.py",
    "two_player/v212_supervision_collector_v01.py",
    "two_player/v212_supervision_receipt_v02.py",
)


class ArmedServiceSmokeError(RuntimeError):
    """The armed no-inference service could not produce a durable receipt."""


def _worker_source() -> str:
    """Bootstrap source hashes modules before loading their verified bytes."""
    return r'''import hashlib,json,os,sys,syslog,time,types
from pathlib import Path

def reject_pairs(pairs):
    out={}
    for key,value in pairs:
        if key in out: raise ValueError("duplicate request key")
        out[key]=value
    return out

request=json.load(sys.stdin,object_pairs_hook=reject_pairs)
if not isinstance(request,dict) or set(request)!={"schema","nonce","source_manifest","source_manifest_sha256"} or request.get("schema")!="caissa.synthetic.armed-request.v01":
    sys.exit(31)
if not isinstance(request.get("nonce"),str) or len(request["nonce"])!=32 or any(c not in "0123456789abcdef" for c in request["nonce"]): sys.exit(40)
root=Path(sys.argv[3]).resolve(strict=True)
argv=Path("/proc/self/cmdline").read_bytes().split(b"\0")
if len(argv)<7 or argv[1:5]!=[b"-I",b"-S",b"-B",b"-c"]: sys.exit(32)
manifest=request.get("source_manifest")
if not isinstance(manifest,dict) or set(manifest)!={"bootstrap_sha256","files"}: sys.exit(33)
if hashlib.sha256(argv[5]).hexdigest()!=manifest["bootstrap_sha256"]: sys.exit(34)
files=manifest.get("files")
expected={"two_player/v212_worker_ipc.py","two_player/v212_release_token_v01.py","two_player/v212_armed_protocol_v01.py"}
if not isinstance(files,dict) or set(files)!=expected: sys.exit(35)
verified={}
for relative,digest in files.items():
    path=(root/relative).resolve(strict=True)
    if not path.is_relative_to(root): sys.exit(36)
    data=path.read_bytes()
    if hashlib.sha256(data).hexdigest()!=digest: sys.exit(37)
    verified[relative]=data
canonical=json.dumps(manifest,sort_keys=True,separators=(",",":"),allow_nan=False).encode()
if hashlib.sha256(canonical).hexdigest()!=request.get("source_manifest_sha256"): sys.exit(38)
os.chdir(root)
sys.path.insert(0,str(root))
package=types.ModuleType("two_player")
package.__path__=[str(root/"two_player")]
package.__package__="two_player"
sys.modules["two_player"]=package
for short,relative in (("v212_worker_ipc","two_player/v212_worker_ipc.py"),
                       ("v212_release_token_v01","two_player/v212_release_token_v01.py"),
                       ("v212_armed_protocol_v01","two_player/v212_armed_protocol_v01.py")):
    name="two_player."+short
    module=types.ModuleType(name)
    module.__file__=str(root/relative)
    module.__package__="two_player"
    sys.modules[name]=module
    exec(compile(verified[relative],module.__file__,"exec"),module.__dict__)
    setattr(package,short,module)

ipc=sys.modules["two_player.v212_worker_ipc"]
release=sys.modules["two_player.v212_release_token_v01"]
armed=sys.modules["two_player.v212_armed_protocol_v01"]
directory=Path(sys.argv[1])
unit=sys.argv[2]
boot=Path("/proc/sys/kernel/random/boot_id").read_text(encoding="ascii").strip().replace("-","").lower()
matches=[line[3:] for line in Path("/proc/self/cgroup").read_text(encoding="ascii").splitlines() if line.startswith("0::")]
if len(matches)!=1: sys.exit(39)
group=matches[0]
def identity(name): return ipc.FileIdentity.from_stat(os.stat(directory/name,follow_symlinks=False))
directory_info=os.stat(directory,follow_symlinks=False)
workspace=ipc.WorkerIPCWorkspace(
    directory=directory,request_path=directory/ipc.REQUEST_NAME,
    response_path=directory/ipc.RESPONSE_NAME,
    response_identity=identity(ipc.RESPONSE_NAME),
    request_identity=identity(ipc.REQUEST_NAME),
    directory_device=directory_info.st_dev,directory_inode=directory_info.st_ino,
    request_bytes=(directory/ipc.REQUEST_NAME).stat().st_size,
    release_path=directory/ipc.RELEASE_NAME,
    release_identity=identity(ipc.RELEASE_NAME))
def callback(token):
    invocation=os.environ.get("INVOCATION_ID","")
    if len(invocation)!=32: raise RuntimeError("missing systemd invocation ID")
    syslog.syslog(syslog.LOG_INFO,"CAISSA_V212_NO_INFERENCE_MARKER "+invocation)
    time.sleep(0.45)
    return {"schema":"caissa.v212.armed-no-inference-response.v01",
            "nonce":request["nonce"],"status":"released_no_inference"}
response=armed.run_synthetic_armed_worker(
    workspace,expected_nonce=request["nonce"],expected_service_unit=unit,
    invocation_id=os.environ.get("INVOCATION_ID"),boot_id=boot,
    self_control_group=group,
    expected_source_manifest_sha256=request["source_manifest_sha256"],
    on_release=callback)
json.dump(response,sys.stdout,separators=(",",":"),allow_nan=False)
sys.stdout.write("\n")
sys.stdout.flush()
'''


def _source_manifest(repo_root: Path, worker_source: str) -> tuple[dict[str, Any], str]:
    files: dict[str, str] = {}
    for relative in WORKER_MODULES:
        path = repo_root / relative
        files[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
    manifest = {
        "bootstrap_sha256": hashlib.sha256(worker_source.encode("utf-8")).hexdigest(),
        "files": files,
    }
    encoded = json.dumps(manifest, sort_keys=True, separators=(",", ":"),
                         ensure_ascii=False, allow_nan=False).encode("utf-8")
    return manifest, hashlib.sha256(encoded).hexdigest()


def _assert_source_manifest(repo_root: Path, manifest: dict[str, Any],
                            worker_source: str) -> None:
    actual_bootstrap = hashlib.sha256(worker_source.encode("utf-8")).hexdigest()
    if actual_bootstrap != manifest["bootstrap_sha256"]:
        raise ArmedServiceSmokeError("verified worker bootstrap changed during service run")
    for relative, expected in manifest["files"].items():
        actual = hashlib.sha256((repo_root / relative).read_bytes()).hexdigest()
        if actual != expected:
            raise ArmedServiceSmokeError("verified worker source changed during service run")


def _host_evidence_manifest(repo_root: Path) -> dict[str, str]:
    return {
        relative: hashlib.sha256((repo_root / relative).read_bytes()).hexdigest()
        for relative in HOST_EVIDENCE_MODULES
    }


def _assert_host_evidence_manifest(repo_root: Path,
                                   expected: dict[str, str]) -> None:
    if _host_evidence_manifest(repo_root) != expected:
        raise ArmedServiceSmokeError("host evidence source changed during service run")


def _hash_verified_request(workspace: ipc.WorkerIPCWorkspace) -> str:
    """Hash only the original bounded request file inside its private directory."""
    if workspace.request_path != workspace.directory / ipc.REQUEST_NAME:
        raise ArmedServiceSmokeError("request path does not match IPC workspace")
    directory_fd = request_fd = -1
    try:
        directory_fd = os.open(
            workspace.directory,
            os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
            | getattr(os, "O_NOFOLLOW", 0))
        directory_info = os.fstat(directory_fd)
        if ((directory_info.st_dev, directory_info.st_ino)
                != (workspace.directory_device, workspace.directory_inode)):
            raise ArmedServiceSmokeError("IPC directory identity changed before request hashing")
        request_fd = os.open(ipc.REQUEST_NAME,
                             os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0),
                             dir_fd=directory_fd)
        opened = os.fstat(request_fd)
        if ipc.FileIdentity.from_stat(opened) != workspace.request_identity:
            raise ArmedServiceSmokeError("request file identity changed before hashing")
        digest = hashlib.sha256()
        total = 0
        while True:
            chunk = os.read(request_fd, min(4096, workspace.request_bytes + 1 - total))
            if not chunk:
                break
            total += len(chunk)
            if total > workspace.request_bytes:
                raise ArmedServiceSmokeError("request file grew beyond its recorded size")
            digest.update(chunk)
        if total != workspace.request_bytes:
            raise ArmedServiceSmokeError("request file size changed before hashing")
        after = os.fstat(request_fd)
        current = os.stat(ipc.REQUEST_NAME, dir_fd=directory_fd, follow_symlinks=False)
        if (ipc.FileIdentity.from_stat(after) != workspace.request_identity
                or ipc.FileIdentity.from_stat(current) != workspace.request_identity):
            raise ArmedServiceSmokeError("request file identity changed during hashing")
        return digest.hexdigest()
    except OSError as exc:
        raise ArmedServiceSmokeError("verified request file could not be hashed") from exc
    finally:
        if request_fd >= 0:
            os.close(request_fd)
        if directory_fd >= 0:
            os.close(directory_fd)


def _active_reconciliation_ids(active: dict[str, Any] | None) -> str:
    if active is None:
        return ""
    return (f"invocation_id={active.get('invocation_id', 'unavailable')} "
            f"worker_cgroup={active.get('control_group', 'unavailable')}")


def run_no_inference_armed_smoke(*, receipt_path: Path,
                                 timeout_seconds: float = 10.0) -> dict[str, Any]:
    """Verify the real FIFO release barrier on one bounded synthetic service.

    No model/search code is imported. Any post-dispatch failure preserves the
    service/workspace handles for reconciliation, and receipt uncertainty
    prevents cleanup.
    """
    if (isinstance(timeout_seconds, bool) or not isinstance(timeout_seconds, (int, float))
            or not 2 <= timeout_seconds <= 30):
        raise ValueError("timeout_seconds must be between 2 and 30")
    request_started = collector._monotonic_us()
    deadline = time.monotonic() + timeout_seconds
    try:
        destination = live.validate_receipt_destination(Path(receipt_path))
    except live.LiveEvidenceError as exc:
        raise ArmedServiceSmokeError("receipt destination failed pre-dispatch validation") from exc

    # Include source preflight and request construction in the caller deadline.
    repo_root = Path(__file__).resolve().parents[1]
    worker_source = _worker_source()
    source_manifest, source_manifest_sha256 = _source_manifest(repo_root, worker_source)
    host_evidence_sources_sha256 = _host_evidence_manifest(repo_root)
    boot = collector._boot_id()
    caller_cgroup = collector._proc_cgroup()
    nonce = secrets.token_hex(16)
    workspace: ipc.WorkerIPCWorkspace | None = None
    unit = "caissa-v212-armed-smoke-" + secrets.token_hex(8) + ".service"
    started = False
    persistence_attempted = False
    persisted = False
    unit_stopped = False
    workspace_cleaned = False
    active: dict[str, Any] | None = None
    events_before: dict[str, Any] | None = None
    events_after: dict[str, Any] | None = None

    try:
        workspace = ipc.create_workspace({
            "schema": REQUEST_SCHEMA,
            "nonce": nonce,
            "source_manifest": source_manifest,
            "source_manifest_sha256": source_manifest_sha256,
        }, with_release_fifo=True)
        request_sha256 = _hash_verified_request(workspace)
        command = ["systemd-run", "--user", "--unit=" + unit,
                   "--remain-after-exit",
                   "--property=MemoryMax=128M",
                   "--property=MemoryHigh=96M",
                   "--property=MemorySwapMax=0",
                   "--property=RuntimeMaxSec=8s",
                   "--property=Restart=no",
                   "--property=OOMPolicy=kill",
                   "--property=LimitFSIZE=65536",
                   "--property=WorkingDirectory=" + str(repo_root),
                   "--property=StandardInput=file:" + str(workspace.request_path),
                   "--property=StandardOutput=truncate:" + str(workspace.response_path),
                   "--property=StandardError=null", sys.executable, "-I", "-S", "-B", "-c",
                   worker_source, str(workspace.directory), unit, str(repo_root)]
        collector._check_deadline(deadline)
        started = True
        collector._run(command, timeout=2.0, deadline=deadline)
        active_props: dict[str, str] | None = None
        while time.monotonic() < deadline:
            props = collector._show(unit, timeout=1.0, deadline=deadline)
            collector._check_deadline(deadline)
            if (props.get("LoadState") == "loaded"
                    and props.get("ActiveState") == "active"
                    and props.get("SubState") in {"start", "running"}):
                active_props = props
                break
            time.sleep(0.02)
        if active_props is None:
            raise ArmedServiceSmokeError("armed worker did not reach active state before deadline")
        active = live.snapshot_from_properties(
            unit=unit, properties=active_props, boot_id=boot,
            captured_monotonic_us=collector._monotonic_us(), active=True)
        worker_cgroup = active["control_group"]
        invocation_id = active["invocation_id"]
        main_pid = active_props.get("MainPID", "")
        if not main_pid.isdecimal() or int(main_pid) <= 1:
            raise ArmedServiceSmokeError("armed worker has no valid service MainPID")
        if (collector._proc_cgroup(int(main_pid)) != worker_cgroup
                or worker_cgroup == caller_cgroup):
            raise ArmedServiceSmokeError("armed worker/caller cgroup placement did not verify")
        collector._verify_effective_properties(active_props)
        live_cgroup = {
            "memory.max": collector._cgroup_scalar(worker_cgroup, "memory.max"),
            "memory.high": collector._cgroup_scalar(worker_cgroup, "memory.high"),
            "memory.swap.max": collector._cgroup_scalar(worker_cgroup, "memory.swap.max"),
        }
        if live_cgroup != {"memory.max": str(collector.MEMORY_MAX),
                           "memory.high": str(collector.MEMORY_HIGH),
                           "memory.swap.max": "0"}:
            raise ArmedServiceSmokeError("armed worker live cgroup limits did not match policy")

        events_before = live.read_memory_events_local(
            cgroup_root=Path("/sys/fs/cgroup"), control_group=worker_cgroup,
            boot_id=boot, captured_monotonic_us=collector._monotonic_us())
        collector._check_deadline(deadline)
        release_snapshot = {
            "schema": release.SCHEMA,
            "request_nonce": nonce,
            "service_unit": unit,
            "invocation_id": invocation_id,
            "boot_id": boot,
            "control_group": worker_cgroup,
            "effective_properties": {
                key: active_props[key] for key in armed.EXPECTED_EFFECTIVE_PROPERTIES
            },
            "live_cgroup": live_cgroup,
            "source_manifest_sha256": source_manifest_sha256,
            "captured_monotonic_ns": time.monotonic_ns(),
        }
        token = armed.release_when_ready(workspace, release_snapshot,
                                         deadline=deadline)
        if not isinstance(token, bytes) or not token:
            raise ArmedServiceSmokeError("release token was empty")
        time.sleep(0.08)
        events_after = live.read_memory_events_local(
            cgroup_root=Path("/sys/fs/cgroup"), control_group=worker_cgroup,
            boot_id=boot, captured_monotonic_us=collector._monotonic_us())
        collector._check_deadline(deadline)

        exited_props: dict[str, str] | None = None
        while time.monotonic() < deadline:
            props = collector._show(unit, timeout=1.0, deadline=deadline)
            collector._check_deadline(deadline)
            if ((props.get("ActiveState"), props.get("SubState")) in {
                    ("active", "exited"), ("inactive", "exited"), ("failed", "failed")}):
                exited_props = props
                break
            time.sleep(0.02)
        if exited_props is None:
            raise ArmedServiceSmokeError("armed worker did not exit before caller deadline")
        manager_snapshot = live.snapshot_from_properties(
            unit=unit, properties=exited_props, boot_id=boot,
            captured_monotonic_us=collector._monotonic_us(), active=False)
        if manager_snapshot["result"] != "success" or manager_snapshot["main_status"] != 0:
            raise ArmedServiceSmokeError("armed synthetic worker did not exit successfully")
        if (manager_snapshot["unit"] != active["unit"]
                or manager_snapshot["invocation_id"] != invocation_id
                or manager_snapshot["boot_id"] != active["boot_id"]
                or (manager_snapshot["control_group"] is not None
                    and manager_snapshot["control_group"] != worker_cgroup)):
            raise ArmedServiceSmokeError(
                "post-exit manager snapshot identity did not match active worker")

        collector._check_deadline(deadline)
        response = ipc.read_response(workspace)
        collector._check_deadline(deadline)
        if (response.get("schema") != RESPONSE_SCHEMA
                or response.get("nonce") != nonce
                or response.get("status") != "released_no_inference"):
            raise ArmedServiceSmokeError("armed worker response did not match its release")
        _assert_source_manifest(repo_root, source_manifest, worker_source)
        records = collector._journal_markers(
            unit, invocation_id=invocation_id, worker_cgroup=worker_cgroup,
            deadline=deadline)
        collector._check_deadline(deadline)
        expected_marker = MARKER_PREFIX + invocation_id
        if len(records) != 1 or records[0].get("MESSAGE") != expected_marker:
            raise ArmedServiceSmokeError("armed marker did not bind the active invocation")
        _assert_host_evidence_manifest(repo_root, host_evidence_sources_sha256)
        if _hash_verified_request(workspace) != request_sha256:
            raise ArmedServiceSmokeError("request bytes changed during service run")
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
            "armed_release_verified": True,
            "source_manifest_sha256": source_manifest_sha256,
            "source_manifest": source_manifest,
            "host_evidence_sources_sha256": host_evidence_sources_sha256,
            "request_sha256": request_sha256,
            "response_sha256": hashlib.sha256(
                json.dumps(response, sort_keys=True, separators=(",", ":"),
                           ensure_ascii=False, allow_nan=False).encode("utf-8")).hexdigest(),
            "receipt_sha256": hashlib.sha256(receipt_bytes).hexdigest(),
            "collector_source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "kernel_oom_journal": "not_collected_no_oom_operation",
            "runtime": {
                "worker_cgroup": worker_cgroup,
                "caller_cgroup": caller_cgroup,
                "effective_memory_max": collector.MEMORY_MAX,
                "effective_memory_high": collector.MEMORY_HIGH,
                "memory_swap_max": 0,
                "limit_fsize": collector.FILE_SIZE_LIMIT,
                "restart": "no", "oom_policy": "kill",
                "counter_source": "memory.events.local",
            },
            "receipt": receipt,
        }
        collector._check_deadline(deadline)
        persistence_attempted = True
        live.persist_receipt_once(destination, envelope)
        persisted = True
        collector._check_deadline(deadline)
        collector._run(("systemctl", "--user", "stop", unit), timeout=2.0,
                       stdout=subprocess.DEVNULL, deadline=deadline)
        after_stop = collector._show(unit, timeout=1.0, deadline=deadline)
        if after_stop.get("LoadState") != "not-found":
            raise ArmedServiceSmokeError("armed transient unit remained loaded after cleanup")
        unit_stopped = True
        ipc.cleanup_workspace(workspace)
        workspace_cleaned = True
        collector._check_deadline(deadline)
        return {"unit": unit, "invocation_id": invocation_id,
                "worker_cgroup": worker_cgroup, "caller_cgroup": caller_cgroup,
                "receipt_path": str(destination), "receipt_persisted_before_cleanup": True,
                "armed_release_verified": True, "source_manifest_sha256": source_manifest_sha256,
                "unit_load_state_after_cleanup": "not-found"}
    except KeyboardInterrupt as exc:
        if not started and workspace is not None and not workspace_cleaned:
            try:
                ipc.cleanup_workspace(workspace)
                workspace_cleaned = True
            except ipc.WorkerIPCError as cleanup_exc:
                cleanup_failure = f"pre_dispatch_cleanup_failed={type(cleanup_exc).__name__}: {cleanup_exc}"
            else:
                cleanup_failure = ""
        else:
            cleanup_failure = ""
        if started:
            receipt_state = ("receipt_persisted" if persisted else
                             "receipt_publication_or_durability_uncertain"
                             if persistence_attempted else "receipt_not_attempted")
            unit_state = "unit_stopped" if unit_stopped else "unit_retained_or_state_unknown"
            workspace_state = ("ipc_workspace_cleaned" if workspace_cleaned
                               else collector._workspace_path_state(workspace)
                               if workspace is not None else "ipc_workspace_unknown")
            context = (f"{receipt_state} receipt_path={destination} {unit_state} "
                       f"unit={unit} {workspace_state} ipc_directory="
                       f"{workspace.directory if workspace is not None else 'unavailable'} "
                       f"{_active_reconciliation_ids(active)}")
        elif workspace is None:
            context = "service_not_dispatched; ipc_workspace_not_created"
        elif workspace_cleaned:
            context = f"service_not_dispatched; ipc_workspace_cleaned ipc_directory={workspace.directory}"
        else:
            context = (f"service_not_dispatched; {collector._workspace_path_state(workspace)} "
                       f"ipc_directory={workspace.directory} {cleanup_failure}")
        prior = str(exc)
        exc.args = ((prior + "; " if prior else "") + context,)
        raise
    except Exception as exc:
        if not started and workspace is not None and not workspace_cleaned:
            try:
                ipc.cleanup_workspace(workspace)
                workspace_cleaned = True
            except ipc.WorkerIPCError as cleanup_exc:
                cleanup_failure = f"pre_dispatch_cleanup_failed={type(cleanup_exc).__name__}: {cleanup_exc}"
            else:
                cleanup_failure = ""
        else:
            cleanup_failure = ""
        if started:
            if persisted:
                receipt_state = "receipt_persisted"
            elif persistence_attempted:
                receipt_state = "receipt_publication_or_durability_uncertain"
            else:
                receipt_state = "receipt_not_attempted"
            unit_state = "unit_stopped" if unit_stopped else "unit_retained_or_state_unknown"
            workspace_state = ("ipc_workspace_cleaned" if workspace_cleaned
                               else collector._workspace_path_state(workspace)
                               if workspace is not None else "ipc_workspace_unknown")
            detail = (f"{type(exc).__name__}: {exc}; {receipt_state} "
                      f"receipt_path={destination} {unit_state} unit={unit} "
                      f"{workspace_state} ipc_directory="
                      f"{workspace.directory if workspace is not None else 'unavailable'} "
                      f"{_active_reconciliation_ids(active)}")
        else:
            if workspace is None:
                workspace_state = "ipc_workspace_not_created"
                workspace_path = "unavailable"
            elif workspace_cleaned:
                workspace_state = "ipc_workspace_cleaned"
                workspace_path = str(workspace.directory)
            else:
                workspace_state = collector._workspace_path_state(workspace)
                workspace_path = str(workspace.directory)
            detail = (f"{type(exc).__name__}: {exc}; service_not_dispatched; "
                      f"{workspace_state} ipc_directory={workspace_path} {cleanup_failure}")
        raise ArmedServiceSmokeError(detail) from exc


__all__ = ["ArmedServiceSmokeError", "run_no_inference_armed_smoke"]

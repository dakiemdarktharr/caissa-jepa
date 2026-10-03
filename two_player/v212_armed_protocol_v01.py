"""Synthetic caller/worker armed-release protocol; no service or model code."""
from __future__ import annotations

import math
import os
from pathlib import Path
import re
import time
from typing import Any, Callable, Mapping

from two_player import v212_release_token_v01 as release
from two_player import v212_worker_ipc as ipc


_POSITIVE_INT = re.compile(r"^[1-9][0-9]*$")
_TIMESPAN = re.compile(r"^[1-9][0-9]*(?:us|ms|s|min|h)?$")
EXPECTED_EFFECTIVE_PROPERTIES = {
    "EffectiveMemoryMax": "134217728",
    "EffectiveMemoryHigh": "100663296",
    "MemorySwapMax": "0",
    "LimitFSIZE": "65536",
    "RuntimeMaxUSec": "8s",
    "Restart": "no",
    "OOMPolicy": "kill",
    "RemainAfterExit": "yes",
}
_SNAPSHOT_FIELDS = frozenset({
    "schema", "request_nonce", "service_unit", "invocation_id", "boot_id",
    "control_group", "effective_properties", "live_cgroup",
    "source_manifest_sha256", "captured_monotonic_ns",
})


class ArmedProtocolError(RuntimeError):
    """The controller/worker handshake failed before the release point."""


def _validate_snapshot(snapshot: Mapping[str, Any], *,
                       deadline_monotonic_ns: int) -> bytes:
    if not isinstance(snapshot, Mapping) or set(snapshot) != _SNAPSHOT_FIELDS:
        raise ArmedProtocolError("verified snapshot fields do not match protocol schema")
    if snapshot.get("schema") != release.SCHEMA:
        raise ArmedProtocolError("verified snapshot schema is unsupported")
    props = snapshot.get("effective_properties")
    live = snapshot.get("live_cgroup")
    if not isinstance(props, Mapping) or not isinstance(live, Mapping):
        raise ArmedProtocolError("verified snapshot resource fields are malformed")
    if dict(props) != EXPECTED_EFFECTIVE_PROPERTIES:
        raise ArmedProtocolError("effective service properties do not match the v01 policy")
    for property_name, cgroup_name in (
            ("EffectiveMemoryMax", "memory.max"),
            ("EffectiveMemoryHigh", "memory.high"),
            ("MemorySwapMax", "memory.swap.max")):
        value = props.get(property_name)
        live_value = live.get(cgroup_name)
        if not isinstance(value, str) or not _POSITIVE_INT.fullmatch(value) \
                and not (property_name == "MemorySwapMax" and value == "0"):
            raise ArmedProtocolError(f"effective {property_name} is not finite")
        if not isinstance(live_value, str) or value != live_value:
            raise ArmedProtocolError(f"effective {property_name} disagrees with live cgroup")
    memory_max = int(props["EffectiveMemoryMax"])
    memory_high = int(props["EffectiveMemoryHigh"])
    if memory_high > memory_max:
        raise ArmedProtocolError("effective MemoryHigh exceeds MemoryMax")
    if props["MemorySwapMax"] != "0":
        raise ArmedProtocolError("effective MemorySwapMax must be zero")
    for name, expected in (("Restart", "no"), ("OOMPolicy", "kill"),
                           ("RemainAfterExit", "yes")):
        if props.get(name) != expected:
            raise ArmedProtocolError(f"effective {name} violates the worker policy")
    file_size = props.get("LimitFSIZE")
    if not isinstance(file_size, str) or not _POSITIVE_INT.fullmatch(file_size):
        raise ArmedProtocolError("effective LimitFSIZE must be finite and positive")
    runtime = props.get("RuntimeMaxUSec")
    if not isinstance(runtime, str) or not _TIMESPAN.fullmatch(runtime):
        raise ArmedProtocolError("effective RuntimeMaxUSec must be finite and positive")

    captured_ns = snapshot.get("captured_monotonic_ns")
    if type(captured_ns) is not int or captured_ns <= 0:
        raise ArmedProtocolError("snapshot capture time must be a positive monotonic integer")
    if type(deadline_monotonic_ns) is not int or deadline_monotonic_ns <= captured_ns:
        raise ArmedProtocolError("caller deadline must follow snapshot capture")
    try:
        unsigned = dict(snapshot)
        unsigned["deadline_monotonic_ns"] = deadline_monotonic_ns
        token = dict(unsigned, token_sha256=release.token_digest(unsigned))
        payload = release.canonical_json(token)
        release.parse_token(payload)
    except release.ReleaseTokenError as exc:
        raise ArmedProtocolError("verified snapshot cannot form a valid release token") from exc
    return payload


def release_when_ready(workspace: ipc.WorkerIPCWorkspace,
                       snapshot: Mapping[str, Any], *, deadline: float,
                       clock: Callable[[], float] | None = None,
                       sleep: Callable[[float], None] | None = None,
                       poll_interval: float = 0.005) -> bytes:
    """Send a token only after the worker reached its FIFO read barrier."""
    if not isinstance(deadline, (int, float)) or not math.isfinite(deadline):
        raise ArmedProtocolError("caller deadline must be finite monotonic time")
    if not isinstance(poll_interval, (int, float)) or not math.isfinite(poll_interval) \
            or poll_interval <= 0:
        raise ArmedProtocolError("poll interval must be finite and positive")
    now = clock or time.monotonic
    pause = sleep or time.sleep
    payload = _validate_snapshot(
        snapshot, deadline_monotonic_ns=int(deadline * 1_000_000_000))
    while True:
        remaining = deadline - now()
        if remaining <= 0:
            raise ArmedProtocolError("caller deadline expired before release")
        try:
            writer = ipc.open_release_writer(workspace)
        except ipc.WorkerIPCError as exc:
            raise ArmedProtocolError("worker release FIFO failed identity checks") from exc
        if writer is None:
            pause(min(poll_interval, remaining))
            continue
        if deadline - now() <= 0:
            os.close(writer)
            raise ArmedProtocolError("caller deadline expired at worker readiness")
        try:
            ipc.write_release(workspace, writer, payload)
        except ipc.WorkerIPCError as exc:
            raise ArmedProtocolError("release token could not be safely written") from exc
        return payload


def run_synthetic_armed_worker(
        workspace: ipc.WorkerIPCWorkspace, *, expected_nonce: str,
        expected_service_unit: str, invocation_id: str | None, boot_id: str,
        self_control_group: str, expected_source_manifest_sha256: str,
        on_release: Callable[[Mapping[str, Any]], Any],
        cgroup_root: Path = Path("/sys/fs/cgroup"),
        monotonic_ns: Callable[[], int] | None = None) -> Any:
    """Consume and verify release before invoking a synthetic callback.

    A real worker must call the verifier before importing model/search modules.
    This harness deliberately has no compute-capable imports or service launch.
    """
    try:
        if workspace.release_identity is None:
            raise ArmedProtocolError("workspace has no verified release FIFO")
        payload = release.read_release_fifo(
            workspace.directory,
            directory_device=workspace.directory_device,
            directory_inode=workspace.directory_inode,
            fifo_identity=workspace.release_identity)
        token = release.verify_token(
            payload, expected_nonce=expected_nonce,
            expected_service_unit=expected_service_unit,
            invocation_id=invocation_id, boot_id=boot_id,
            self_control_group=self_control_group,
            expected_source_manifest_sha256=expected_source_manifest_sha256,
            cgroup_root=cgroup_root)
    except (release.ReleaseTokenError, ipc.WorkerIPCError) as exc:
        raise ArmedProtocolError("worker rejected release before compute") from exc
    now_ns = (monotonic_ns or time.monotonic_ns)()
    if type(now_ns) is not int or now_ns >= token["deadline_monotonic_ns"]:
        raise ArmedProtocolError("worker rejected release after caller deadline")
    return on_release(token)

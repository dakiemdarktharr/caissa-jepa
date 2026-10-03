"""Bounded caller-side adapters for live V2.12 supervision evidence.

The helpers normalize systemd/cgroup snapshots and persist a receipt without
replacing prior evidence. They do not launch units, run inference, or induce
resource pressure. A caller must keep the transient unit retained until the
receipt is durable.
"""
from __future__ import annotations

import os
from pathlib import Path
import re
import stat
import tempfile
from typing import Any, Mapping

from two_player import v212_supervision_receipt_v02 as assembler

SCHEMA = "caissa.v212.live-supervision.v01"
MAX_SHOW_BYTES = 65_536
MAX_COUNTER_FILE_BYTES = 16_384
MAX_COUNTER_VALUE = (1 << 64) - 1
REQUIRED_COUNTERS = set(assembler.OOM_KEYS) | {"low", "high", "max"}


class LiveEvidenceError(ValueError):
    """Live system evidence is absent, malformed, or unsafe to persist."""


def parse_systemd_show(text: str, *, max_bytes: int = MAX_SHOW_BYTES) -> dict[str, str]:
    if not isinstance(text, str) or len(text.encode("utf-8")) > max_bytes:
        raise LiveEvidenceError("systemd properties exceed the bounded text limit")
    properties: dict[str, str] = {}
    for line in text.splitlines():
        if not line:
            continue
        key, separator, value = line.partition("=")
        if not separator or not re.fullmatch(r"[A-Za-z][A-Za-z0-9]*", key):
            raise LiveEvidenceError("systemd property output is malformed")
        if key in properties:
            raise LiveEvidenceError("systemd property output contains duplicates")
        properties[key] = value
    return properties


def _required(properties: Mapping[str, str], key: str) -> str:
    value = properties.get(key)
    if not isinstance(value, str) or not value:
        raise LiveEvidenceError(f"systemd property {key} is missing")
    return value


def _unsigned(value: str, label: str) -> int:
    if len(value) > 20 or not re.fullmatch(r"[0-9]+", value):
        raise LiveEvidenceError(f"systemd property {label} is malformed")
    parsed = int(value)
    if parsed > MAX_COUNTER_VALUE:
        raise LiveEvidenceError(f"systemd property {label} is out of range")
    return parsed


def snapshot_from_properties(*, unit: str, properties: Mapping[str, str],
                             boot_id: str, captured_monotonic_us: int,
                             active: bool) -> dict[str, Any]:
    if not isinstance(properties, Mapping):
        raise LiveEvidenceError("systemd properties must be a mapping")
    if not isinstance(unit, str) or not unit.endswith(".service") or "/" in unit:
        raise LiveEvidenceError("unit name is malformed")
    try:
        normalized_boot = assembler.normalize_boot_id(boot_id)
    except assembler.ReceiptError as exc:
        raise LiveEvidenceError("boot ID is malformed") from exc
    if type(captured_monotonic_us) is not int or captured_monotonic_us < 0:
        raise LiveEvidenceError("monotonic capture time is malformed")
    invocation = _required(properties, "InvocationID").lower()
    if not re.fullmatch(r"[0-9a-f]{32}", invocation):
        raise LiveEvidenceError("InvocationID is malformed")
    control_group = properties.get("ControlGroup", "") or None
    active_state = _required(properties, "ActiveState")
    sub_state = _required(properties, "SubState")
    if active:
        if active_state != "active" or sub_state not in {"start", "running"}:
            raise LiveEvidenceError("service is not in an accepted active state")
        if not control_group:
            raise LiveEvidenceError("active service has no ControlGroup")
        try:
            assembler._cgroup(control_group)
        except assembler.ReceiptError as exc:
            raise LiveEvidenceError("ControlGroup is malformed") from exc
        if control_group.rsplit("/", 1)[-1] != unit:
            raise LiveEvidenceError("ControlGroup does not belong to the requested unit")
    else:
        if ((active_state, sub_state) not in {
                ("inactive", "exited"), ("active", "exited"),
                ("failed", "failed")}):
            raise LiveEvidenceError("service has not reached a post-exit state")
    snapshot: dict[str, Any] = {
        "schema": assembler.SYSTEMD_SNAPSHOT_SCHEMA,
        "unit": unit,
        "invocation_id": invocation,
        "control_group": control_group,
        "boot_id": normalized_boot,
        "captured_monotonic_us": captured_monotonic_us,
        "active_state": active_state,
        "sub_state": sub_state,
    }
    if not active:
        # systemd exposes failed units as ActiveState=failed, while the receipt
        # schema models lifecycle completion as inactive plus an exit outcome.
        # Preserve the raw manager value alongside the normalized state.
        snapshot["manager_active_state"] = active_state
        snapshot["active_state"] = "inactive"
        snapshot["result"] = _required(properties, "Result")
        snapshot["main_status"] = _unsigned(
            _required(properties, "ExecMainStatus"), "ExecMainStatus")
    return snapshot


def read_memory_events_local(*, cgroup_root: Path, control_group: str,
                             boot_id: str, captured_monotonic_us: int) -> dict[str, Any]:
    try:
        group = assembler._cgroup(control_group)
        normalized_boot = assembler.normalize_boot_id(boot_id)
    except assembler.ReceiptError as exc:
        raise LiveEvidenceError("cgroup or boot binding is malformed") from exc
    if type(captured_monotonic_us) is not int or captured_monotonic_us < 0:
        raise LiveEvidenceError("monotonic capture time is malformed")
    root = Path(cgroup_root)
    if not root.is_absolute() or root.is_symlink():
        raise LiveEvidenceError("cgroup root must be an absolute non-symlink path")
    relative_parts = group.lstrip("/").split("/")
    if any(part in {"", ".", ".."} for part in relative_parts):
        raise LiveEvidenceError("ControlGroup escapes the cgroup root")
    group_dir = root.joinpath(*relative_parts)
    try:
        root_real = root.resolve(strict=True)
        group_real = group_dir.resolve(strict=True)
        if not group_real.is_relative_to(root_real) or not group_real.is_dir():
            raise LiveEvidenceError("worker cgroup is outside the cgroup root")
        events_path = group_real / "memory.events.local"
        if events_path.is_symlink():
            raise LiveEvidenceError("memory.events.local cannot be a symlink")
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
        fd = os.open(events_path, flags)
    except LiveEvidenceError:
        raise
    except OSError as exc:
        raise LiveEvidenceError("worker memory.events.local is unavailable") from exc
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_size > MAX_COUNTER_FILE_BYTES:
            raise LiveEvidenceError("memory.events.local is not a bounded regular file")
        chunks: list[bytes] = []
        total = 0
        while True:
            chunk = os.read(fd, min(4096, MAX_COUNTER_FILE_BYTES + 1 - total))
            if not chunk:
                break
            total += len(chunk)
            if total > MAX_COUNTER_FILE_BYTES:
                raise LiveEvidenceError("memory.events.local exceeds its byte bound")
            chunks.append(chunk)
    finally:
        os.close(fd)
    try:
        text = b"".join(chunks).decode("ascii")
    except UnicodeDecodeError as exc:
        raise LiveEvidenceError("memory.events.local is not ASCII") from exc
    counters: dict[str, int] = {}
    for line in text.splitlines():
        fields = line.split()
        if len(fields) != 2 or not re.fullmatch(r"[a-z_]+", fields[0]):
            raise LiveEvidenceError("memory.events.local row is malformed")
        key, raw_value = fields
        if (key in counters or len(raw_value) > 20
                or not re.fullmatch(r"[0-9]+", raw_value)):
            raise LiveEvidenceError("memory.events.local has duplicate or invalid values")
        value = int(raw_value)
        if value > MAX_COUNTER_VALUE:
            raise LiveEvidenceError("memory.events.local counter is out of range")
        counters[key] = value
    if not REQUIRED_COUNTERS.issubset(counters):
        raise LiveEvidenceError("memory.events.local lacks required counters")
    return {"schema": assembler.COUNTER_SCHEMA,
            "source": "memory.events.local", "cgroup": group,
            "boot_id": normalized_boot,
            "captured_monotonic_us": captured_monotonic_us,
            "counters": counters}


def persist_receipt_once(path: Path, receipt: Mapping[str, Any]) -> None:
    """Persist evidence without replacing an earlier receipt at this path.

    The parent directory must be a private caller-owned directory. A surviving
    `.claim` file after an error intentionally blocks retries until reconciled.
    """
    destination = Path(path)
    parent = destination.parent
    if not parent.is_absolute():
        raise LiveEvidenceError("receipt parent path must be absolute")
    trusted_temp_root = Path(tempfile.gettempdir()).absolute()
    current = Path(parent.anchor)
    for part in parent.parts[1:]:
        current = current / part
        try:
            ancestor = os.lstat(current)
        except OSError as exc:
            raise LiveEvidenceError("receipt parent path cannot be inspected") from exc
        if not stat.S_ISDIR(ancestor.st_mode):
            raise LiveEvidenceError("receipt parent path contains a non-directory")
        mode = stat.S_IMODE(ancestor.st_mode)
        trusted_sticky_temp = (current == trusted_temp_root
                               and bool(ancestor.st_mode & stat.S_ISVTX))
        if ancestor.st_uid in {0, os.getuid()}:
            safe = not bool(mode & 0o022) or trusted_sticky_temp
        else:
            safe = not bool(mode & 0o222) or trusted_sticky_temp
        if not safe:
            raise LiveEvidenceError("receipt ancestors must be trusted and non-writable")
    try:
        parent_info = os.lstat(parent)
    except OSError as exc:
        raise LiveEvidenceError("receipt parent directory is unavailable") from exc
    if (not stat.S_ISDIR(parent_info.st_mode) or parent_info.st_uid != os.getuid()
            or stat.S_IMODE(parent_info.st_mode) & 0o077):
        raise LiveEvidenceError("receipt parent must be private and caller-owned")
    if (destination.name in {"", ".", ".."}
            or os.path.lexists(destination)):
        raise LiveEvidenceError("receipt destination is unsafe")
    claim = destination.with_name(destination.name + ".claim")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(claim, flags, 0o600)
    except FileExistsError as exc:
        raise LiveEvidenceError("receipt path is already claimed for reconciliation") from exc
    except OSError as exc:
        raise LiveEvidenceError("receipt path cannot be exclusively claimed") from exc
    os.close(fd)
    try:
        # Reserve the destination too: the atomic writer may replace only this
        # invocation's placeholder, never a pre-existing receipt.
        reservation_fd = os.open(destination, flags, 0o600)
    except OSError as exc:
        raise LiveEvidenceError("receipt destination cannot be reserved exclusively") from exc
    try:
        reserved_info = os.fstat(reservation_fd)
        if (not stat.S_ISREG(reserved_info.st_mode)
                or reserved_info.st_uid != os.getuid()
                or stat.S_IMODE(reserved_info.st_mode) != 0o600
                or reserved_info.st_nlink != 1):
            raise LiveEvidenceError("receipt reservation failed identity checks")
        os.fsync(reservation_fd)
    finally:
        os.close(reservation_fd)
    dir_fd = os.open(parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(dir_fd)
    finally:
        os.close(dir_fd)
    try:
        current_info = os.lstat(destination)
        if (current_info.st_dev != reserved_info.st_dev
                or current_info.st_ino != reserved_info.st_ino
                or current_info.st_uid != reserved_info.st_uid
                or stat.S_IMODE(current_info.st_mode) != 0o600
                or current_info.st_nlink != 1
                or not stat.S_ISREG(current_info.st_mode)):
            raise LiveEvidenceError("receipt reservation changed before persistence")
        assembler.atomic_write_json(destination, receipt)
        claim.unlink()
        dir_fd = os.open(parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
        try:
            os.fsync(dir_fd)
        finally:
            os.close(dir_fd)
    except BaseException:
        # Keep the claim as a durable fail-closed reconciliation marker.
        raise

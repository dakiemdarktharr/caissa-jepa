"""Fail-closed V2.12 receipt assembly with invocation-bound provenance.

This module consumes already-captured evidence. It does not launch services,
read journals, run inference, or establish operational supervision readiness.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any, Mapping, Sequence


SCHEMA = "caissa.v212.supervision-receipt.v02"
COUNTER_SCHEMA = "cgroup-v2.memory.events.local.v1"
SYSTEMD_SNAPSHOT_SCHEMA = "systemd-show-invocation.v01"
ASSEMBLER_VERSION = "v02"
MAX_JOURNAL_RECORDS = 1024
MAX_JOURNAL_RECORD_BYTES = 65_536
MAX_JOURNAL_BATCH_BYTES = 4_194_304
MAX_COUNTER_KEYS = 64
MAX_RECEIPT_BYTES = 1_048_576
OOM_KEYS = ("oom", "oom_kill", "oom_group_kill")


class ReceiptError(ValueError):
    """Required provenance is missing, malformed, or contradictory."""


def normalize_boot_id(value: Any) -> str:
    if not isinstance(value, str):
        raise ReceiptError("boot ID must be text")
    normalized = value.replace("-", "").lower()
    if not re.fullmatch(r"[0-9a-f]{32}", normalized):
        raise ReceiptError("boot ID is malformed")
    return normalized


def _time(value: Any, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ReceiptError(f"{label} monotonic timestamp is malformed")
    return value


def _text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ReceiptError(f"{label} is missing or malformed")
    return value


def _unit(value: Any) -> str:
    unit = _text(value, "unit name")
    if "/" in unit or unit in {".", ".."}:
        raise ReceiptError("unit name is malformed")
    return unit


def _invocation(value: Any) -> str:
    result = _text(value, "invocation ID")
    if not re.fullmatch(r"[0-9a-fA-F]{32}", result):
        raise ReceiptError("systemd invocation ID is malformed")
    return result.lower()


def _cgroup(value: Any) -> str:
    path = _text(value, "worker control group")
    if not path.startswith("/"):
        raise ReceiptError("worker control group is malformed")
    parts = path.split("/")[1:]
    if not parts or any(part in {"", ".", ".."} for part in parts):
        raise ReceiptError("worker control group is not canonical")
    return path


def _snapshot(record: Mapping[str, Any], *, label: str,
              expected_unit: str, expected_invocation: str,
              expected_boot: str) -> tuple[int, str | None]:
    if not isinstance(record, Mapping):
        raise ReceiptError(f"{label} snapshot must be an object")
    if record.get("schema") != SYSTEMD_SNAPSHOT_SCHEMA:
        raise ReceiptError(f"{label} snapshot schema does not match")
    if _unit(record.get("unit")) != expected_unit:
        raise ReceiptError(f"{label} snapshot unit does not match request")
    if _invocation(record.get("invocation_id")) != expected_invocation:
        raise ReceiptError(f"{label} snapshot invocation ID does not match")
    if normalize_boot_id(record.get("boot_id")) != expected_boot:
        raise ReceiptError(f"{label} snapshot boot ID does not match")
    captured = _time(record.get("captured_monotonic_us"), f"{label} capture")
    cgroup = record.get("control_group")
    if cgroup is not None:
        cgroup = _cgroup(cgroup) if cgroup else None
        if cgroup is not None and cgroup.rsplit("/", 1)[-1] != expected_unit:
            raise ReceiptError(f"{label} ControlGroup does not belong to unit")
    return captured, cgroup


def _journal_time(record: Mapping[str, Any]) -> int:
    value = record.get("__MONOTONIC_TIMESTAMP")
    if not isinstance(value, str) or not value.isdecimal():
        raise ReceiptError("journal monotonic timestamp is malformed")
    return int(value)


def _message_value(message: str, key: str) -> str | None:
    match = re.search(rf"(?<![A-Za-z0-9_]){re.escape(key)}=([^,\s]+)", message)
    return match.group(1) if match else None


def _fingerprint(record: Mapping[str, Any]) -> str:
    try:
        return json.dumps(record, sort_keys=True, separators=(",", ":"),
                          ensure_ascii=True, allow_nan=False, default=str)
    except (TypeError, ValueError) as exc:
        raise ReceiptError("journal record is not safely serializable") from exc


def _invocation_markers(records: Sequence[Mapping[str, Any]], *, unit: str,
                        invocation_id: str, boot_id: str,
                        start_us: int, end_us: int) -> list[dict[str, Any]]:
    seen: dict[str, tuple[str, dict[str, Any]]] = {}
    for record in records:
        record_units = (record.get("_SYSTEMD_UNIT"),
                        record.get("_SYSTEMD_USER_UNIT"))
        if any(value is not None and not isinstance(value, str)
               for value in record_units):
            raise ReceiptError("unit journal fields are malformed")
        if not any(value == unit for value in record_units):
            continue
        cursor = _text(record.get("__CURSOR"), "unit journal cursor")
        current_id = record.get("_SYSTEMD_INVOCATION_ID")
        if not isinstance(current_id, str) or current_id.lower() != invocation_id:
            raise ReceiptError("unit journal record has a conflicting invocation ID")
        record_boot = normalize_boot_id(record.get("_BOOT_ID"))
        timestamp = _journal_time(record)
        if record_boot != boot_id:
            raise ReceiptError("unit journal record has a conflicting boot ID")
        if not start_us <= timestamp <= end_us:
            raise ReceiptError("unit journal record is outside the invocation window")
        proof = {"cursor": cursor, "boot_id": record_boot,
                 "monotonic_us": timestamp}
        fingerprint = _fingerprint(record)
        prior = seen.get(cursor)
        if prior is not None and prior[0] != fingerprint:
            raise ReceiptError("journal cursor has conflicting records")
        seen[cursor] = (fingerprint, proof)
    return sorted((proof for _, proof in seen.values()),
                  key=lambda item: (item["monotonic_us"], item["cursor"]))


def _kernel_oom_proofs(records: Sequence[Mapping[str, Any]], *, cgroup: str,
                       boot_id: str, start_us: int, end_us: int
                       ) -> tuple[int, list[dict[str, Any]]]:
    seen: dict[str, str] = {}
    candidate_count = 0
    matches: list[dict[str, Any]] = []
    for record in records:
        message = record.get("MESSAGE")
        if not isinstance(message, str) or "oom-kill:" not in message:
            continue
        cursor = _text(record.get("__CURSOR"), "OOM journal cursor")
        fingerprint = _fingerprint(record)
        previous = seen.get(cursor)
        if previous is not None:
            if previous != fingerprint:
                raise ReceiptError("journal cursor has conflicting OOM records")
            continue
        seen[cursor] = fingerprint
        candidate_count += 1
        if record.get("_TRANSPORT") != "kernel":
            continue
        event_boot = normalize_boot_id(record.get("_BOOT_ID"))
        timestamp = _journal_time(record)
        if event_boot != boot_id or not start_us <= timestamp <= end_us:
            continue
        constraint = _message_value(message, "constraint")
        oom_memcg = _message_value(message, "oom_memcg")
        task_memcg = _message_value(message, "task_memcg")
        if (constraint, oom_memcg, task_memcg) != (
                "CONSTRAINT_MEMCG", cgroup, cgroup):
            continue
        matches.append({
            "cursor": cursor,
            "boot_id": event_boot,
            "monotonic_us": timestamp,
            "transport": "kernel",
            "constraint": constraint,
            "oom_memcg": oom_memcg,
            "task_memcg": task_memcg,
            "message_sha256": hashlib.sha256(message.encode("utf-8")).hexdigest(),
        })
    return candidate_count, sorted(matches,
                                    key=lambda item: (item["monotonic_us"],
                                                      item["cursor"]))


def _counter_snapshot(record: Mapping[str, Any] | None, *, label: str,
                      cgroup: str, boot_id: str, start_us: int,
                      end_us: int) -> tuple[int, dict[str, int]] | None:
    if record is None:
        return None
    if not isinstance(record, Mapping):
        raise ReceiptError(f"{label} memory event snapshot must be an object")
    if record.get("schema") != COUNTER_SCHEMA:
        raise ReceiptError(f"{label} memory event snapshot schema does not match")
    if record.get("source") != "memory.events.local":
        raise ReceiptError(f"{label} counter source is not memory.events.local")
    if _cgroup(record.get("cgroup")) != cgroup:
        raise ReceiptError(f"{label} counter cgroup does not match worker")
    if normalize_boot_id(record.get("boot_id")) != boot_id:
        raise ReceiptError(f"{label} counter boot ID does not match")
    captured = _time(record.get("captured_monotonic_us"),
                     f"{label} counter capture")
    if not start_us <= captured <= end_us:
        raise ReceiptError(f"{label} counter capture is outside invocation window")
    counters = record.get("counters")
    if not isinstance(counters, Mapping) or len(counters) > MAX_COUNTER_KEYS:
        raise ReceiptError(f"{label} memory event counters are malformed")
    if not set(OOM_KEYS).issubset(counters):
        raise ReceiptError(f"{label} memory event counters are incomplete")
    normalized: dict[str, int] = {}
    for key, value in counters.items():
        if (not isinstance(key, str) or isinstance(value, bool)
                or not isinstance(value, int) or value < 0):
            raise ReceiptError(f"{label} memory event counters are malformed")
        normalized[key] = value
    return captured, normalized


def assemble_receipt(*, requested_unit: str, request_boot_id: str,
                     request_started_monotonic_us: int,
                     worker_snapshot: Mapping[str, Any],
                     manager_snapshot: Mapping[str, Any],
                     journal_records: Sequence[Mapping[str, Any]],
                     events_before: Mapping[str, Any] | None = None,
                     events_after: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Bind manager, cgroup counters, and journal proof to one invocation.

    The active manager snapshot is the sole source of the worker cgroup path.
    Both counter samples must carry matching cgroup, boot, schema, source, and
    in-window capture time. Kernel messages are retained only as normalized
    fields plus a SHA-256 digest; raw journal text is never copied to the
    receipt.
    """
    unit = _unit(requested_unit)
    boot_id = normalize_boot_id(request_boot_id)
    start_us = _time(request_started_monotonic_us, "request start")
    if (not isinstance(journal_records, Sequence)
            or isinstance(journal_records, (str, bytes, bytearray))):
        raise ReceiptError("journal record batch must be a sequence")
    if len(journal_records) > MAX_JOURNAL_RECORDS:
        raise ReceiptError("journal record batch exceeds the receipt bound")
    if any(not isinstance(record, Mapping) for record in journal_records):
        raise ReceiptError("journal record batch contains a non-object record")
    batch_bytes = 0
    for record in journal_records:
        record_bytes = len(_fingerprint(record).encode("utf-8"))
        if record_bytes > MAX_JOURNAL_RECORD_BYTES:
            raise ReceiptError("journal record exceeds the input size bound")
        batch_bytes += record_bytes
        if batch_bytes > MAX_JOURNAL_BATCH_BYTES:
            raise ReceiptError("journal record batch exceeds the input size bound")
    if not isinstance(worker_snapshot, Mapping):
        raise ReceiptError("active worker snapshot must be an object")

    active_time, cgroup = _snapshot(
        worker_snapshot, label="active worker", expected_unit=unit,
        expected_invocation=_invocation(worker_snapshot.get("invocation_id")),
        expected_boot=boot_id)
    if cgroup is None:
        raise ReceiptError("active worker snapshot lacks ControlGroup")
    invocation_id = _invocation(worker_snapshot.get("invocation_id"))
    active_state = worker_snapshot.get("active_state")
    active_sub_state = worker_snapshot.get("sub_state")
    if (active_state != "active" or not isinstance(active_sub_state, str)
            or active_sub_state not in {"start", "running"}):
        raise ReceiptError("worker snapshot was not captured while service was active")
    if not start_us <= active_time:
        raise ReceiptError("active worker snapshot predates the request")

    manager_time, manager_cgroup = _snapshot(
        manager_snapshot, label="manager result", expected_unit=unit,
        expected_invocation=invocation_id, expected_boot=boot_id)
    if manager_time <= active_time:
        raise ReceiptError("manager result snapshot does not follow active snapshot")
    manager_active_state = manager_snapshot.get("active_state")
    manager_sub_state = manager_snapshot.get("sub_state")
    if (manager_active_state != "inactive"
            or not isinstance(manager_sub_state, str)
            or manager_sub_state not in {"exited", "failed"}):
        raise ReceiptError("manager result snapshot was not captured after exit")
    if manager_cgroup not in {None, cgroup}:
        raise ReceiptError("manager result ControlGroup conflicts with active snapshot")
    manager_result = _text(manager_snapshot.get("result"), "systemd manager result")
    main_status = manager_snapshot.get("main_status")
    if main_status is not None and (isinstance(main_status, bool)
                                    or not isinstance(main_status, int)):
        raise ReceiptError("manager main status is malformed")

    evidence_start_us = active_time + 1
    markers = _invocation_markers(
        journal_records, unit=unit, invocation_id=invocation_id,
        boot_id=boot_id, start_us=evidence_start_us, end_us=manager_time)
    if not markers:
        raise ReceiptError("no journal record binds the unit to this invocation")
    candidate_count, oom_proofs = _kernel_oom_proofs(
        journal_records, cgroup=cgroup, boot_id=boot_id,
        start_us=evidence_start_us, end_us=manager_time)

    before = _counter_snapshot(events_before, label="before", cgroup=cgroup,
                               boot_id=boot_id, start_us=evidence_start_us,
                               end_us=manager_time)
    after = _counter_snapshot(events_after, label="after", cgroup=cgroup,
                              boot_id=boot_id, start_us=evidence_start_us,
                              end_us=manager_time)
    if (before is None) != (after is None):
        raise ReceiptError("both counter snapshots must be supplied together")
    deltas = None
    positive_oom = False
    positive_kill = False
    if before and after:
        before_time, before_counts = before
        after_time, after_counts = after
        if before_time >= after_time:
            raise ReceiptError("counter snapshots are not in increasing time order")
        keys = set(before_counts) | set(after_counts)
        deltas = {key: after_counts.get(key, 0) - before_counts.get(key, 0)
                  for key in sorted(keys)}
        if any(value < 0 for value in deltas.values()):
            raise ReceiptError("memory event counters moved backwards")
        positive_oom = any(deltas.get(key, 0) > 0 for key in OOM_KEYS)
        positive_kill = any(deltas.get(key, 0) > 0
                            for key in ("oom_kill", "oom_group_kill"))

    if manager_result == "oom-kill":
        if len(oom_proofs) > 1:
            classification = "ambiguous_multiple_worker_cgroup_oom_events"
        elif oom_proofs and positive_kill:
            classification = "worker_cgroup_oom_attributed_by_journal_and_local_counters"
        elif oom_proofs:
            classification = "worker_cgroup_oom_attributed_by_kernel_journal"
        elif positive_kill:
            classification = "worker_cgroup_oom_attributed_by_local_counters"
        else:
            classification = "manager_oom_unattributed"
    elif oom_proofs or positive_kill:
        classification = "conflict_oom_evidence_with_non_oom_manager_result"
    elif positive_oom:
        classification = "worker_cgroup_oom_event_without_kill"
    elif manager_result == "success" and main_status == 0:
        classification = "normal_exit"
    else:
        classification = "non_oom_failure"

    try:
        source_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    except OSError as exc:
        raise ReceiptError("assembler source digest unavailable; do not persist receipt") from exc

    return {
        "schema": SCHEMA,
        "assembler": {
            "version": ASSEMBLER_VERSION,
            "source_sha256": source_hash,
        },
        "phase": "pre-cleanup",
        "classification": classification,
        "binding": {
            "unit": unit,
            "invocation_id": invocation_id,
            "worker_cgroup": cgroup,
            "boot_id": boot_id,
            "request_started_monotonic_us": start_us,
            "systemd_snapshot_schema": SYSTEMD_SNAPSHOT_SCHEMA,
            "counter_snapshot_schema": COUNTER_SCHEMA,
            "worker_snapshot_monotonic_us": active_time,
            "manager_snapshot_monotonic_us": manager_time,
            "unit_invocation_journal_markers": markers,
        },
        "manager": {"active_state": "inactive",
                    "reported_active_state": manager_snapshot.get(
                        "manager_active_state", manager_active_state),
                    "sub_state": manager_sub_state,
                    "result": manager_result, "main_status": main_status},
        "kernel_oom": {"candidate_record_count": candidate_count,
                        "matching_worker_cgroup_events": oom_proofs,
                        "raw_message_included": False,
                        "cursor_retrieval_required_for_parser_reverification": True},
        "memory_events_local": {
            "schema": COUNTER_SCHEMA,
            "before": None if before is None else {
                "captured_monotonic_us": before[0], "counters": before[1]},
            "after": None if after is None else {
                "captured_monotonic_us": after[0], "counters": after[1]},
            "delta": deltas,
            "positive_oom_counter": positive_oom,
            "positive_kill_counter": positive_kill,
        },
    }


def atomic_write_json(path: str | os.PathLike[str], payload: Mapping[str, Any]) -> None:
    """Atomically persist a bounded private receipt and fsync file + directory."""
    destination = Path(path)
    parent = destination.parent
    if not parent.is_dir():
        raise ReceiptError("receipt parent directory must already exist")
    fd = -1
    temporary: str | None = None
    try:
        fd, temporary = tempfile.mkstemp(prefix=f".{destination.name}.",
                                         suffix=".tmp", dir=parent)
        os.fchmod(fd, 0o600)
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"),
                             ensure_ascii=False, allow_nan=False) + "\n"
        if len(encoded.encode("utf-8")) > MAX_RECEIPT_BYTES:
            raise ReceiptError("receipt exceeds the durable size bound")
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            fd = -1
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, destination)
        temporary = None
        directory_fd = os.open(parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    except ReceiptError:
        raise
    except (OSError, TypeError, ValueError) as exc:
        raise ReceiptError("durable receipt write failed; do not clean up evidence") from exc
    finally:
        if fd >= 0:
            os.close(fd)
        if temporary is not None:
            try:
                os.unlink(temporary)
            except FileNotFoundError:
                pass

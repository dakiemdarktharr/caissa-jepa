"""One-shot armed-worker release FIFO and token verification primitives.

This module is pure supervision plumbing. It does not import model/search code,
launch a service, or start inference. Callers should invoke verification before
any compute-capable import.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import posixpath
import re
import stat
from typing import Any, Mapping

from two_player import v212_worker_ipc as ipc


SCHEMA = "caissa.v212.worker-release.v01"
MAX_RELEASE_BYTES = ipc.MAX_RELEASE_BYTES
PROPERTY_KEYS = frozenset({
    "EffectiveMemoryMax", "EffectiveMemoryHigh", "MemorySwapMax",
    "LimitFSIZE", "RuntimeMaxUSec", "Restart", "OOMPolicy",
    "RemainAfterExit",
})
CGROUP_KEYS = frozenset({"memory.max", "memory.high", "memory.swap.max"})
_HEX32 = re.compile(r"^[0-9a-f]{32}$")
_HEX64 = re.compile(r"^[0-9a-f]{64}$")


class ReleaseTokenError(ValueError):
    """The worker is not safely bound to the caller's verified snapshot."""


def canonical_json(value: Mapping[str, Any]) -> bytes:
    try:
        return json.dumps(value, ensure_ascii=False, allow_nan=False,
                          separators=(",", ":"), sort_keys=True).encode("utf-8")
    except (TypeError, ValueError, UnicodeError) as exc:
        raise ReleaseTokenError("release token is not canonical finite JSON") from exc


def token_digest(fields: Mapping[str, Any]) -> str:
    if "token_sha256" in fields:
        raise ReleaseTokenError("digest input must not contain token_sha256")
    return hashlib.sha256(canonical_json(fields)).hexdigest()


def _pairs_without_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ReleaseTokenError("release token contains a duplicate JSON key")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise ReleaseTokenError(f"release token contains non-finite number {value}")


def _text(value: Any, label: str, *, limit: int = 512) -> str:
    if not isinstance(value, str) or not value or len(value) > limit:
        raise ReleaseTokenError(f"{label} must be bounded nonempty text")
    if "\x00" in value or "\n" in value or "\r" in value:
        raise ReleaseTokenError(f"{label} contains a control character")
    return value


def _validate_cgroup_path(value: Any) -> str:
    path = _text(value, "control_group")
    if (not path.startswith("/") or path == "/" or posixpath.normpath(path) != path
            or any(part in {".", ".."} for part in path.split("/"))):
        raise ReleaseTokenError("control_group is not a normalized absolute path")
    return path


def parse_token(payload: bytes) -> dict[str, Any]:
    if not isinstance(payload, bytes) or not 1 <= len(payload) <= MAX_RELEASE_BYTES:
        raise ReleaseTokenError("release token must be 1..4096 bytes")
    try:
        parsed = json.loads(payload.decode("utf-8", errors="strict"),
                            object_pairs_hook=_pairs_without_duplicates,
                            parse_constant=_reject_constant)
    except ReleaseTokenError:
        raise
    except (UnicodeError, json.JSONDecodeError, RecursionError, ValueError) as exc:
        raise ReleaseTokenError("release token is not valid UTF-8 JSON") from exc
    if not isinstance(parsed, dict):
        raise ReleaseTokenError("release token must be one JSON object")
    if canonical_json(parsed) != payload:
        raise ReleaseTokenError("release token encoding is not canonical sorted JSON")
    required = {
        "schema", "request_nonce", "service_unit", "invocation_id", "boot_id",
        "control_group", "effective_properties", "live_cgroup", "source_manifest_sha256",
        "captured_monotonic_ns", "token_sha256",
    }
    if set(parsed) != required:
        raise ReleaseTokenError("release token fields do not match the versioned schema")
    if parsed["schema"] != SCHEMA:
        raise ReleaseTokenError("release token schema is unsupported")
    _text(parsed["request_nonce"], "request_nonce", limit=128)
    _text(parsed["service_unit"], "service_unit")
    for key in ("invocation_id", "boot_id"):
        if not isinstance(parsed[key], str) or not _HEX32.fullmatch(parsed[key]):
            raise ReleaseTokenError(f"{key} must be a lowercase 32-hex identifier")
    _validate_cgroup_path(parsed["control_group"])
    if not isinstance(parsed["effective_properties"], dict) \
            or set(parsed["effective_properties"]) != PROPERTY_KEYS:
        raise ReleaseTokenError("effective_properties do not match the versioned schema")
    for key, value in parsed["effective_properties"].items():
        _text(value, f"effective_properties.{key}")
    if not isinstance(parsed["live_cgroup"], dict) \
            or set(parsed["live_cgroup"]) != CGROUP_KEYS:
        raise ReleaseTokenError("live_cgroup does not match the versioned schema")
    for key, value in parsed["live_cgroup"].items():
        _text(value, f"live_cgroup.{key}", limit=128)
    source_hash = parsed["source_manifest_sha256"]
    if not isinstance(source_hash, str) or not _HEX64.fullmatch(source_hash):
        raise ReleaseTokenError("source_manifest_sha256 must be lowercase SHA-256")
    if type(parsed["captured_monotonic_ns"]) is not int or parsed["captured_monotonic_ns"] <= 0:
        raise ReleaseTokenError("captured_monotonic_ns must be a positive integer")
    digest = parsed["token_sha256"]
    unsigned = {key: value for key, value in parsed.items() if key != "token_sha256"}
    if not isinstance(digest, str) or not _HEX64.fullmatch(digest) \
            or token_digest(unsigned) != digest:
        raise ReleaseTokenError("release token digest does not match its canonical fields")
    return parsed


def _read_cgroup_value(root: Path, control_group: str, name: str) -> str:
    if name not in CGROUP_KEYS:
        raise ReleaseTokenError("unsupported live cgroup property")
    try:
        root_real = root.resolve(strict=True)
        group_dir = root.joinpath(*control_group.lstrip("/").split("/")).resolve(strict=True)
        if not group_dir.is_relative_to(root_real) or not group_dir.is_dir():
            raise ReleaseTokenError("worker cgroup resolves outside cgroup-v2 root")
        fd = os.open(group_dir / name, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    except ReleaseTokenError:
        raise
    except OSError as exc:
        raise ReleaseTokenError(f"worker cgroup {name} is unavailable") from exc
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode):
            raise ReleaseTokenError(f"worker cgroup {name} is not a regular file")
        data = os.read(fd, 129)
        if len(data) > 128:
            raise ReleaseTokenError(f"worker cgroup {name} exceeds its read bound")
    finally:
        os.close(fd)
    try:
        return data.decode("ascii", errors="strict").strip()
    except UnicodeError as exc:
        raise ReleaseTokenError(f"worker cgroup {name} is not ASCII") from exc


def verify_token(payload: bytes, *, expected_nonce: str, expected_service_unit: str,
                 invocation_id: str | None, boot_id: str,
                 self_control_group: str, expected_source_manifest_sha256: str,
                 cgroup_root: Path = Path("/sys/fs/cgroup")) -> dict[str, Any]:
    """Validate digest and bind token to this worker's runtime context."""
    token = parse_token(payload)
    comparisons = (
        (token["request_nonce"], expected_nonce, "request nonce"),
        (token["service_unit"], expected_service_unit, "service unit"),
        (token["invocation_id"], invocation_id, "systemd invocation ID"),
        (token["boot_id"], boot_id, "boot ID"),
        (token["control_group"], self_control_group, "worker cgroup"),
        (token["source_manifest_sha256"], expected_source_manifest_sha256,
         "worker source manifest"),
    )
    for actual, expected, label in comparisons:
        if not isinstance(expected, str) or actual != expected:
            raise ReleaseTokenError(f"release token {label} does not match worker context")
    for name, expected in token["live_cgroup"].items():
        if _read_cgroup_value(cgroup_root, token["control_group"], name) != expected:
            raise ReleaseTokenError(f"release token {name} does not match the live worker cgroup")
    return token


def read_release_fifo(directory: Path, *, directory_device: int,
                      directory_inode: int, fifo_identity: ipc.FileIdentity) -> bytes:
    """Block at the worker barrier, then consume one bounded FIFO payload to EOF."""
    directory_fd = -1
    try:
        directory_fd = os.open(directory,
                               os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
                               | getattr(os, "O_NOFOLLOW", 0))
        parent = os.fstat(directory_fd)
        if (parent.st_dev != directory_device or parent.st_ino != directory_inode
                or parent.st_uid != os.getuid()
                or stat.S_IMODE(parent.st_mode) != 0o700):
            raise ReleaseTokenError("worker IPC directory identity changed")
        before = os.stat(ipc.RELEASE_NAME, dir_fd=directory_fd,
                         follow_symlinks=False)
        ipc._validate_fifo_stat(before, expected_owner=os.getuid())
        if ipc.FileIdentity.from_stat(before) != fifo_identity:
            raise ReleaseTokenError("release FIFO identity changed before worker open")
        # Blocking read-open is the no-compute readiness barrier.
        fd = os.open(ipc.RELEASE_NAME,
                     os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0),
                     dir_fd=directory_fd)
        try:
            opened = os.fstat(fd)
            after = os.stat(ipc.RELEASE_NAME, dir_fd=directory_fd,
                            follow_symlinks=False)
            ipc._validate_fifo_stat(opened, expected_owner=os.getuid(),
                                    label="opened release FIFO")
            ipc._validate_fifo_stat(after, expected_owner=os.getuid())
            if (ipc.FileIdentity.from_stat(opened) != fifo_identity
                    or ipc.FileIdentity.from_stat(after) != fifo_identity):
                raise ReleaseTokenError("release FIFO identity changed during worker open")
            chunks = bytearray()
            while True:
                chunk = os.read(fd, min(1024, MAX_RELEASE_BYTES + 1 - len(chunks)))
                if not chunk:
                    break
                chunks.extend(chunk)
                if len(chunks) > MAX_RELEASE_BYTES:
                    raise ReleaseTokenError("release token exceeds 4096 bytes")
            if not chunks:
                raise ReleaseTokenError("release FIFO closed without a token")
            return bytes(chunks)
        finally:
            os.close(fd)
    except ReleaseTokenError:
        raise
    except ipc.WorkerIPCError as exc:
        raise ReleaseTokenError("release FIFO failed its identity checks") from exc
    except OSError as exc:
        raise ReleaseTokenError("release FIFO could not be safely consumed") from exc
    finally:
        if directory_fd >= 0:
            os.close(directory_fd)

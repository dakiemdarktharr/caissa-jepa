"""Private, bounded file-backed IPC primitives for a future V2.12 worker.

This module only prepares request/response files and validates completed
response bytes. It does not start systemd units, workers, inference, or write
receipts. Callers must retain the directory until the worker is stopped and
its supervision receipt has been persisted.
"""
from __future__ import annotations

import json
import math
import os
from pathlib import Path
import stat
import tempfile
from dataclasses import dataclass
from typing import Any, Mapping


MAX_IPC_BYTES = 65_536
REQUEST_NAME = "request.json"
RESPONSE_NAME = "response.json"


class WorkerIPCError(ValueError):
    """IPC files are unsafe, oversized, malformed, or not one JSON object."""


@dataclass(frozen=True)
class FileIdentity:
    device: int
    inode: int
    owner: int
    mode: int
    links: int

    @classmethod
    def from_stat(cls, result: os.stat_result) -> "FileIdentity":
        return cls(result.st_dev, result.st_ino, result.st_uid,
                   stat.S_IMODE(result.st_mode), result.st_nlink)


@dataclass(frozen=True)
class WorkerIPCWorkspace:
    directory: Path
    request_path: Path
    response_path: Path
    response_identity: FileIdentity
    directory_device: int
    directory_inode: int
    request_bytes: int


def _write_all(fd: int, payload: bytes) -> None:
    offset = 0
    while offset < len(payload):
        written = os.write(fd, payload[offset:])
        if written <= 0:
            raise WorkerIPCError("short IPC file write")
        offset += written


def _create_file(directory: Path, name: str, payload: bytes = b"") -> os.stat_result:
    path = directory / name
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    flags |= getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(path, flags, 0o600)
    try:
        try:
            os.fchmod(fd, 0o600)
            _write_all(fd, payload)
            os.fsync(fd)
            result = os.fstat(fd)
            _validate_file_stat(result, expected_owner=os.getuid())
        except BaseException as primary:
            try:
                opened = os.fstat(fd)
                current = os.lstat(path)
                if (current.st_dev != opened.st_dev
                        or current.st_ino != opened.st_ino):
                    raise OSError("created IPC path changed during setup")
                path.unlink()
            except FileNotFoundError:
                pass
            except OSError as cleanup_error:
                raise WorkerIPCError(
                    f"failed to create {name}; partial-file cleanup failed"
                ) from primary
            raise
    finally:
        os.close(fd)
    return result


def _validate_file_stat(result: os.stat_result, *, expected_owner: int,
                        label: str = "IPC file") -> None:
    if not stat.S_ISREG(result.st_mode):
        raise WorkerIPCError(f"{label} is not a regular file")
    if result.st_uid != expected_owner:
        raise WorkerIPCError(f"{label} owner does not match caller")
    if stat.S_IMODE(result.st_mode) != 0o600:
        raise WorkerIPCError(f"{label} mode is not 0600")
    if result.st_nlink != 1:
        raise WorkerIPCError(f"{label} must have exactly one link")


def _validate_parent_path(base: Path) -> None:
    if not base.is_absolute():
        raise WorkerIPCError("IPC parent path must be absolute")
    trusted_temp_root = Path(tempfile.gettempdir()).absolute()
    current = Path(base.anchor)
    for part in base.parts[1:]:
        current = current / part
        try:
            result = os.lstat(current)
        except OSError as exc:
            raise WorkerIPCError("IPC parent path cannot be inspected") from exc
        if not stat.S_ISDIR(result.st_mode):
            raise WorkerIPCError("IPC parent path contains a non-directory")
        mode = stat.S_IMODE(result.st_mode)
        is_trusted_temp = current == trusted_temp_root
        trusted_sticky = is_trusted_temp and bool(result.st_mode & stat.S_ISVTX)
        if result.st_uid in {0, os.getuid()}:
            writable_by_others = bool(mode & 0o022)
            safe = not writable_by_others or trusted_sticky
        else:
            # Container/rootless mounts can expose immutable ancestors with a
            # mapped owner. Accept those only when no class can write there.
            safe = not bool(mode & 0o222) or trusted_sticky
        if not safe:
            raise WorkerIPCError(
                "IPC parent path ancestors must be trusted and non-writable"
            )


def create_workspace(request: Mapping[str, Any], *,
                     parent: Path | None = None,
                     max_bytes: int = MAX_IPC_BYTES) -> WorkerIPCWorkspace:
    """Create a mode-0700 directory and exclusive 0600 request/response files."""
    if type(max_bytes) is not int or not 1 <= max_bytes <= MAX_IPC_BYTES:
        raise ValueError("max_bytes must be between 1 and the IPC hard limit")
    if not isinstance(request, Mapping) or any(
            not isinstance(key, str) for key in request):
        raise WorkerIPCError("request must be an object with string keys")
    try:
        encoded = json.dumps(request, ensure_ascii=False, allow_nan=False,
                             separators=(",", ":"), sort_keys=True).encode("utf-8")
    except (TypeError, ValueError, UnicodeError) as exc:
        raise WorkerIPCError("request is not finite JSON data") from exc
    if len(encoded) > max_bytes:
        raise WorkerIPCError("request exceeds the configured IPC byte limit")

    base = Path(parent) if parent is not None else Path(tempfile.gettempdir())
    _validate_parent_path(base)
    directory = Path(tempfile.mkdtemp(
        prefix="caissa-v212-", dir=str(base)
    ))
    created: list[Path] = []
    try:
        dir_stat = os.lstat(directory)
        if (not stat.S_ISDIR(dir_stat.st_mode)
                or stat.S_IMODE(dir_stat.st_mode) != 0o700
                or dir_stat.st_uid != os.getuid()):
            raise WorkerIPCError("private IPC directory failed ownership/mode checks")

        _create_file(directory, REQUEST_NAME, encoded)
        created.append(directory / REQUEST_NAME)
        response_stat = _create_file(directory, RESPONSE_NAME)
        created.append(directory / RESPONSE_NAME)
        dir_fd = os.open(directory, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
        try:
            os.fsync(dir_fd)
        finally:
            os.close(dir_fd)
        return WorkerIPCWorkspace(
            directory=directory,
            request_path=directory / REQUEST_NAME,
            response_path=directory / RESPONSE_NAME,
            response_identity=FileIdentity.from_stat(response_stat),
            directory_device=dir_stat.st_dev,
            directory_inode=dir_stat.st_ino,
            request_bytes=len(encoded),
        )
    except BaseException as primary:
        cleanup_errors: list[OSError] = []
        for path in created:
            try:
                path.unlink()
            except FileNotFoundError:
                pass
            except OSError as exc:
                cleanup_errors.append(exc)
        try:
            directory.rmdir()
        except OSError as exc:
            cleanup_errors.append(exc)
        if cleanup_errors:
            raise WorkerIPCError(
                f"workspace setup failed; cleanup incomplete at {directory}"
            ) from primary
        raise


def _pairs_without_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise WorkerIPCError("response contains a duplicate JSON key")
        result[key] = value
    return result


def _reject_nonfinite(value: str) -> None:
    raise WorkerIPCError(f"response contains non-finite JSON number {value}")


def _finite_float(value: str) -> float:
    parsed = float(value)
    if not math.isfinite(parsed):
        raise WorkerIPCError("response number overflows to a non-finite value")
    return parsed


def read_response(workspace: WorkerIPCWorkspace, *,
                  max_bytes: int = MAX_IPC_BYTES) -> dict[str, Any]:
    """Read one bounded object response without following or trusting a new path."""
    if type(max_bytes) is not int or not 1 <= max_bytes <= MAX_IPC_BYTES:
        raise ValueError("max_bytes must be between 1 and the IPC hard limit")
    try:
        if (workspace.request_path != workspace.directory / REQUEST_NAME
                or workspace.response_path != workspace.directory / RESPONSE_NAME):
            raise WorkerIPCError("IPC workspace paths do not match their directory")
        directory_stat = os.lstat(workspace.directory)
        if (not stat.S_ISDIR(directory_stat.st_mode)
                or directory_stat.st_dev != workspace.directory_device
                or directory_stat.st_ino != workspace.directory_inode
                or directory_stat.st_uid != os.getuid()
                or stat.S_IMODE(directory_stat.st_mode) != 0o700):
            raise WorkerIPCError("private IPC directory identity changed")

        before = os.lstat(workspace.response_path)
        _validate_file_stat(before, expected_owner=os.getuid(), label="response file")
        if FileIdentity.from_stat(before) != workspace.response_identity:
            raise WorkerIPCError("response file identity changed")
        if before.st_size > max_bytes:
            raise WorkerIPCError("response exceeds the configured IPC byte limit")

        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
        fd = os.open(workspace.response_path, flags)
        try:
            opened = os.fstat(fd)
            _validate_file_stat(opened, expected_owner=os.getuid(),
                                label="opened response file")
            if FileIdentity.from_stat(opened) != workspace.response_identity:
                raise WorkerIPCError("opened response file identity changed")
            read_start = (opened.st_size, opened.st_mtime_ns, opened.st_ctime_ns)
            chunks: list[bytes] = []
            total = 0
            while True:
                chunk = os.read(fd, min(8192, max_bytes + 1 - total))
                if not chunk:
                    break
                chunks.append(chunk)
                total += len(chunk)
                if total > max_bytes:
                    raise WorkerIPCError("response exceeds the configured IPC byte limit")
            after_open = os.fstat(fd)
        finally:
            os.close(fd)
        after_path = os.lstat(workspace.response_path)
        _validate_file_stat(after_path, expected_owner=os.getuid(),
                            label="response file")
        if (FileIdentity.from_stat(after_open) != workspace.response_identity
                or FileIdentity.from_stat(after_path) != workspace.response_identity
                or read_start != (after_open.st_size, after_open.st_mtime_ns,
                                  after_open.st_ctime_ns)
                or read_start != (after_path.st_size, after_path.st_mtime_ns,
                                  after_path.st_ctime_ns)
                or after_path.st_size != total):
            raise WorkerIPCError("response file changed while it was read")

        try:
            parsed = json.loads(
                b"".join(chunks).decode("utf-8", errors="strict"),
                object_pairs_hook=_pairs_without_duplicates,
                parse_constant=_reject_nonfinite,
                parse_float=_finite_float,
            )
        except WorkerIPCError:
            raise
        except (UnicodeError, json.JSONDecodeError, RecursionError, ValueError) as exc:
            raise WorkerIPCError("response is not valid UTF-8 JSON") from exc
        if not isinstance(parsed, dict):
            raise WorkerIPCError("response must be one JSON object")
        return parsed
    except WorkerIPCError:
        raise
    except OSError as exc:
        raise WorkerIPCError("response file could not be safely read") from exc

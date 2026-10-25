"""Collect a read-only observation of the current V2.12 Python/NumPy runtime.

This is not executed-byte attestation and cannot satisfy D03 by itself. It
records versions, build metadata, process settings, and hashes of currently
mapped executable files where their mapped identity can be matched at read
time. A writable backing file could still differ from already mapped pages.
"""
from __future__ import annotations

import hashlib
import importlib
import json
import os
import platform
import re
import stat
import sys
import sysconfig


SCHEMA = "caissa.v212.runtime-observation.v01"
LOCKED_PYTHON = (3, 11, 9)
LOCKED_NUMPY = "2.4.6"
THREAD_ENVIRONMENT = (
    "OPENBLAS_NUM_THREADS",
    "MKL_NUM_THREADS",
    "OMP_NUM_THREADS",
    "BLIS_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
    "NUMEXPR_NUM_THREADS",
)
_MAPS_LINE = re.compile(
    r"^(?P<start>[0-9a-f]+)-(?P<end>[0-9a-f]+)\s+"
    r"(?P<perms>\S+)\s+(?P<offset>[0-9a-f]+)\s+"
    r"(?P<device>[0-9a-f]+:[0-9a-f]+)\s+(?P<inode>\d+)\s*(?P<path>.*)$"
)


def parse_proc_maps(text: str) -> list[dict]:
    """Parse file-backed executable mappings without treating paths as proof."""
    if not isinstance(text, str):
        raise TypeError("maps content must be text")
    objects = {}
    for line in text.splitlines():
        match = _MAPS_LINE.match(line)
        if match is None:
            continue
        item = match.groupdict()
        inode = int(item["inode"])
        path = item["path"]
        if inode == 0 or len(item["perms"]) < 3 or item["perms"][2] != "x" or not path.startswith("/"):
            continue
        deleted = path.endswith(" (deleted)")
        lookup_path = path[:-10] if deleted else path
        device_major, device_minor = (int(part, 16) for part in item["device"].split(":"))
        key = (device_major, device_minor, inode, path)
        row = objects.setdefault(key, {
            "path_as_mapped": path,
            "lookup_path": lookup_path,
            "device_major": device_major,
            "device_minor": device_minor,
            "inode": inode,
            "deleted_suffix": deleted,
            "segments": [],
        })
        row["segments"].append({
            "start": int(item["start"], 16),
            "end": int(item["end"], 16),
            "permissions": item["perms"],
            "offset": int(item["offset"], 16),
        })
    rows = []
    for key in sorted(objects):
        row = objects[key]
        segments = sorted(row["segments"], key=lambda segment: (
            segment["start"], segment["end"], segment["offset"], segment["permissions"]))
        rows.append({
            **row,
            "segments": segments,
            "executable_mapping_count": len(segments),
        })
    return rows


def _file_observation(path: str, expected_device=None, expected_inode=None) -> dict:
    """Hash a regular file through one descriptor, retaining identity outcome."""
    result = {"path": path, "sha256": None, "status": "unavailable"}
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0)
    try:
        fd = os.open(path, flags)
    except OSError as exc:
        result["error"] = exc.errno
        return result
    try:
        before = os.fstat(fd)
        if not stat.S_ISREG(before.st_mode):
            result["status"] = "not_regular"
            return result
        if expected_inode is not None:
            expected_dev = os.makedev(expected_device[0], expected_device[1])
            if (before.st_dev, before.st_ino) != (expected_dev, expected_inode):
                result["status"] = "mapped_identity_mismatch"
                return result
        digest = hashlib.sha256()
        while True:
            block = os.read(fd, 1024 * 1024)
            if not block:
                break
            digest.update(block)
        after = os.fstat(fd)
        stable = (before.st_dev, before.st_ino, before.st_size,
                  before.st_mtime_ns, before.st_ctime_ns) == (
                      after.st_dev, after.st_ino, after.st_size,
                      after.st_mtime_ns, after.st_ctime_ns)
        if not stable:
            result["status"] = "changed_during_read"
            return result
        result.update({
            "sha256": digest.hexdigest(),
            "size_bytes": after.st_size,
            "device": after.st_dev,
            "inode": after.st_ino,
            "status": "mapped_identity_hash_match" if expected_inode is not None else "path_hash_observed",
        })
        return result
    except OSError as exc:
        result["error"] = exc.errno
        return result
    finally:
        os.close(fd)


def _normalized_config(value):
    if value is None or type(value) in (str, int, float, bool):
        return value
    if isinstance(value, dict):
        return {str(key): _normalized_config(item)
                for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))}
    if isinstance(value, (list, tuple)):
        return [_normalized_config(item) for item in value]
    if hasattr(value, "item"):
        return _normalized_config(value.item())
    return {"unsupported_type": type(value).__qualname__}


def _canonical_sha256(value) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"),
                         ensure_ascii=False, allow_nan=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def collect_runtime_observation(proc_root: str = "/proc") -> dict:
    """Return a deterministic, explicitly non-attesting runtime observation."""
    import numpy as np

    numpy_native = {}
    numpy_native_status = {}
    for module_name in ("numpy._core._multiarray_umath", "numpy.linalg._umath_linalg"):
        try:
            module = importlib.import_module(module_name)
        except ImportError as exc:
            numpy_native[module_name] = None
            numpy_native_status[module_name] = f"unavailable_{type(exc).__name__}"
        else:
            numpy_native[module_name] = getattr(module, "__file__", None)
            numpy_native_status[module_name] = "imported_for_observation"

    try:
        numpy_distribution = importlib.import_module("importlib.metadata")
        numpy_distribution_version = numpy_distribution.version("numpy")
    except Exception as exc:  # report metadata trouble; do not silently claim a match
        numpy_distribution_version = None
        numpy_distribution_error = type(exc).__name__
    else:
        numpy_distribution_error = None

    proc_self = os.path.join(proc_root, "self")
    maps_path = os.path.join(proc_self, "maps")
    try:
        with open(maps_path, "r", encoding="utf-8", errors="replace") as stream:
            mappings = parse_proc_maps(stream.read())
            maps_status = "read"
    except OSError as exc:
        mappings = []
        maps_status = f"unavailable_errno_{exc.errno}"
    segment_inventory_sha256 = _canonical_sha256(mappings)

    mapped_files = []
    for entry in mappings:
        observation = _file_observation(
            entry["lookup_path"],
            expected_device=(entry["device_major"], entry["device_minor"]),
            expected_inode=entry["inode"],
        )
        observation["path_as_mapped"] = entry["path_as_mapped"]
        observation["executable_mapping_count"] = entry["executable_mapping_count"]
        if entry["deleted_suffix"]:
            observation["status"] = "deleted_mapping_path_unavailable"
        mapped_files.append(observation)

    try:
        with open(maps_path, "r", encoding="utf-8", errors="replace") as stream:
            final_mappings = parse_proc_maps(stream.read())
            segment_inventory_stable = mappings == final_mappings
    except OSError:
        segment_inventory_stable = False

    executable_link = os.path.join(proc_self, "exe")
    try:
        executable_path = os.readlink(executable_link)
        executable = _file_observation(executable_link)
        executable["resolved_path_observed"] = executable_path
    except OSError as exc:
        executable = {"sha256": None, "status": "unavailable", "error": exc.errno}

    config = _normalized_config(getattr(np.__config__, "CONFIG", {}))
    config_bytes = json.dumps(config, sort_keys=True, separators=(",", ":"),
                              ensure_ascii=False, allow_nan=False).encode("utf-8")

    python_version = tuple(sys.version_info[:3])
    report = {
        "schema": SCHEMA,
        "identity_status": "observational_only",
        "execution_bytes_verified": False,
        "limitation": (
            "post-startup file hashes identify backing bytes at read time only; they do not prove the bytes already executed or mapped pages"
        ),
        "locked_version_match": {
            "python_3_11_9": python_version == LOCKED_PYTHON,
            "numpy_2_4_6": np.__version__ == LOCKED_NUMPY,
            "both": python_version == LOCKED_PYTHON and np.__version__ == LOCKED_NUMPY,
        },
        "python": {
            "implementation": platform.python_implementation(),
            "version": platform.python_version(),
            "cache_tag": getattr(sys.implementation, "cache_tag", None),
            "executable_path": sys.executable,
            "executable_observation": executable,
            "sysconfig": {
                name: sysconfig.get_config_var(name)
                for name in ("SOABI", "ABIFLAGS", "MULTIARCH", "CC", "CFLAGS")
            },
        },
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "logical_cpu_count": os.cpu_count(),
        },
        "numpy": {
            "version": np.__version__,
            "distribution_version": numpy_distribution_version,
            "distribution_error": numpy_distribution_error,
            "module_path": getattr(np, "__file__", None),
            "native_module_paths": numpy_native,
            "native_module_status": numpy_native_status,
            "build_configuration_sha256": hashlib.sha256(config_bytes).hexdigest(),
            "build_configuration": config,
        },
        "thread_controls": {
            "status": "environment_values_only; actual active threadpool state is not queried",
            "environment": {name: os.environ.get(name) for name in THREAD_ENVIRONMENT},
        },
        "mapped_executable_files": {
            "maps_status": maps_status,
            "normalized_segment_inventory_sha256": segment_inventory_sha256,
            "segment_inventory_stable_before_after_hashing": segment_inventory_stable,
            "snapshot_limitation": "compares normalized executable segment ranges, permissions, offsets and backing-object identities before/after hashing; not atomic",
            "objects": mapped_files,
            "all_backing_file_observations_match_mapping": bool(mapped_files)
                and all(row["status"] == "mapped_identity_hash_match" for row in mapped_files),
        },
    }
    canonical = json.dumps(report, sort_keys=True, separators=(",", ":"),
                           ensure_ascii=False, allow_nan=False).encode("utf-8")
    report["observation_sha256"] = hashlib.sha256(canonical).hexdigest()
    return report


if __name__ == "__main__":
    print(json.dumps(collect_runtime_observation(), sort_keys=True, indent=2,
                     ensure_ascii=False, allow_nan=False))

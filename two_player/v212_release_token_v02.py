"""Release-token v02 adds exact bounded request-byte binding to v01."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from two_player import v212_release_token_v01 as v01


SCHEMA = "caissa.v212.worker-release.v02"
MAX_RELEASE_BYTES = v01.MAX_RELEASE_BYTES
_HEX64 = re.compile(r"^[0-9a-f]{64}$")


class ReleaseTokenError(ValueError):
    """The v02 release token or request-byte binding is invalid."""


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ReleaseTokenError("release token contains a duplicate JSON key")
        result[key] = value
    return result


def parse_token(payload: bytes) -> dict[str, Any]:
    if not isinstance(payload, bytes) or not 1 <= len(payload) <= MAX_RELEASE_BYTES:
        raise ReleaseTokenError("release token must be 1..4096 bytes")
    try:
        parsed = json.loads(payload.decode("utf-8", errors="strict"),
                            object_pairs_hook=_pairs,
                            parse_constant=v01._reject_constant)
    except ReleaseTokenError:
        raise
    except (UnicodeError, json.JSONDecodeError, RecursionError, ValueError) as exc:
        raise ReleaseTokenError("release token is not valid UTF-8 JSON") from exc
    if not isinstance(parsed, dict) or v01.canonical_json(parsed) != payload:
        raise ReleaseTokenError("release token must be one canonical JSON object")
    required = {
        "schema", "request_nonce", "request_sha256", "service_unit",
        "invocation_id", "boot_id", "control_group", "effective_properties",
        "live_cgroup", "source_manifest_sha256", "captured_monotonic_ns",
        "deadline_monotonic_ns", "token_sha256",
    }
    if set(parsed) != required or parsed.get("schema") != SCHEMA:
        raise ReleaseTokenError("release token fields do not match the v02 schema")
    request_sha256 = parsed["request_sha256"]
    if not isinstance(request_sha256, str) or not _HEX64.fullmatch(request_sha256):
        raise ReleaseTokenError("request_sha256 must be lowercase SHA-256")
    digest = parsed["token_sha256"]
    unsigned = {key: value for key, value in parsed.items() if key != "token_sha256"}
    if not isinstance(digest, str) or not _HEX64.fullmatch(digest) \
            or v01.token_digest(unsigned) != digest:
        raise ReleaseTokenError("release token digest does not match its canonical fields")

    # Let the frozen v01 parser validate every unchanged resource/context field.
    legacy_unsigned = dict(unsigned)
    legacy_unsigned["schema"] = v01.SCHEMA
    legacy_unsigned.pop("request_sha256")
    legacy = dict(legacy_unsigned,
                  token_sha256=v01.token_digest(legacy_unsigned))
    try:
        v01.parse_token(v01.canonical_json(legacy))
    except v01.ReleaseTokenError as exc:
        raise ReleaseTokenError("v02 token has invalid v01 context fields") from exc
    return parsed


def verify_token(payload: bytes, *, expected_nonce: str,
                 expected_request_sha256: str, expected_service_unit: str,
                 invocation_id: str | None, boot_id: str,
                 self_control_group: str, expected_source_manifest_sha256: str,
                 cgroup_root: Path = Path("/sys/fs/cgroup")) -> dict[str, Any]:
    token = parse_token(payload)
    if (not isinstance(expected_request_sha256, str)
            or not _HEX64.fullmatch(expected_request_sha256)
            or token["request_sha256"] != expected_request_sha256):
        raise ReleaseTokenError("release token request-byte digest does not match worker input")
    legacy = {key: value for key, value in token.items()
              if key not in {"request_sha256", "token_sha256"}}
    legacy["schema"] = v01.SCHEMA
    legacy["token_sha256"] = v01.token_digest(legacy)
    try:
        v01.verify_token(
            v01.canonical_json(legacy), expected_nonce=expected_nonce,
            expected_service_unit=expected_service_unit,
            invocation_id=invocation_id, boot_id=boot_id,
            self_control_group=self_control_group,
            expected_source_manifest_sha256=expected_source_manifest_sha256,
            cgroup_root=cgroup_root)
    except v01.ReleaseTokenError as exc:
        raise ReleaseTokenError("v02 release token context verification failed") from exc
    return token


read_release_fifo = v01.read_release_fifo
canonical_json = v01.canonical_json
token_digest = v01.token_digest


__all__ = ["ReleaseTokenError", "SCHEMA", "canonical_json", "parse_token",
           "read_release_fifo", "token_digest", "verify_token"]

"""Offline validator for the unreviewed V2.12 request/response v02 proposal.

This module is an audit aid only. It is not imported by either request adapter,
does not launch a worker, and does not authorize service, inference, or pilot
execution.
"""
from __future__ import annotations

import hashlib
import json
import re
from typing import Any

REQUEST_SCHEMA = "caissa.synthetic.request.v02"
RESPONSE_SCHEMA = "caissa.synthetic.response.v02"
MAX_REQUEST_BYTES = 811
MAX_RESPONSE_BYTES = 747
MAX_I64 = (1 << 63) - 1
MAX_PLANNER_NS = 5_000_000_000
VARIANT_CELLS = {
    "connect4-gravity-6x7": 42,
    "connect4-gravity-8x8": 64,
    "reversi6": 36,
    "reversi8": 64,
}
ARMS = {
    "multi-step-jepa",
    "single-pair-jepa",
    "recursive-raw-state-dynamics",
    "value-only-latent-rollout",
    "direct-leaf-value",
    "single-horizon-jepa",
}
STOP_REASONS = {
    "depth_4_complete", "node_cap", "wall_cap", "rss_cap",
    "no_completed_root_action",
}
REQUEST_KEYS = {
    "schema", "nonce", "variant", "target_ply", "root_seed",
    "root_state_sha256", "board", "player", "arm", "model_seed",
    "request_started_ns", "planner_deadline_ns", "node_cap",
    "rss_cap_bytes", "expected_cgroup_path_sha256", "expected_memory_max",
}
RESPONSE_KEYS = {
    "schema", "nonce", "request_sha256", "action", "completed_depth",
    "stop_reason", "node_visits", "transition_calls", "encoder_calls",
    "predictor_calls", "decoder_calls", "value_calls", "model_calls",
    "terminal_nodes", "peak_sampled_rss_bytes", "search_wall_ns",
    "worker_cgroup_path_sha256", "worker_memory_max",
}
_HEX32 = re.compile(r"[0-9a-f]{32}\Z")
_HEX64 = re.compile(r"[0-9a-f]{64}\Z")


def canonical_bytes(value: Any) -> bytes:
    """Encode the proposal's canonical JSON representation."""
    try:
        return json.dumps(
            value, ensure_ascii=False, allow_nan=False,
            separators=(",", ":"), sort_keys=True,
        ).encode("utf-8", errors="strict")
    except (TypeError, ValueError, UnicodeEncodeError) as exc:
        raise ValueError("value cannot be represented as canonical JSON") from exc


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON object key")
        result[key] = value
    return result


def _reject_float(value: str) -> None:
    raise ValueError("JSON floats are forbidden")


def _reject_constant(value: str) -> None:
    raise ValueError("non-finite JSON constants are forbidden")


def _integer(value: Any, low: int, high: int, field: str) -> None:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{field} is outside its integer domain")


def _digest(value: Any, pattern: re.Pattern[str], field: str) -> None:
    if not isinstance(value, str) or pattern.fullmatch(value) is None:
        raise ValueError(f"{field} is not canonical lowercase hex")


def decode_canonical(data: bytes, cap: int) -> dict[str, Any]:
    if type(data) is not bytes or len(data) > cap:
        raise ValueError("payload exceeds byte cap or is not bytes")
    try:
        value = json.loads(
            data.decode("utf-8", errors="strict"),
            object_pairs_hook=_unique_object,
            parse_float=_reject_float,
            parse_constant=_reject_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("payload is not valid UTF-8 JSON") from exc
    if type(value) is not dict:
        raise ValueError("payload must be one top-level object")
    if canonical_bytes(value) != data:
        raise ValueError("payload is not canonical JSON")
    return value


def validate_request(value: Any) -> None:
    if type(value) is not dict or set(value) != REQUEST_KEYS:
        raise ValueError("request keys do not match the closed schema")
    if value["schema"] != REQUEST_SCHEMA:
        raise ValueError("request schema version mismatch")
    _digest(value["nonce"], _HEX32, "nonce")
    variant = value["variant"]
    if type(variant) is not str or variant not in VARIANT_CELLS:
        raise ValueError("unknown game variant")
    ply = value["target_ply"]
    if type(ply) is not int or ply not in {0, 8, 16, 24}:
        raise ValueError("target_ply is outside the frozen schedule")
    _integer(value["root_seed"], 0, MAX_I64, "root_seed")
    _digest(value["root_state_sha256"], _HEX64, "root_state_sha256")
    board = value["board"]
    if (type(board) is not list or len(board) != VARIANT_CELLS[variant]
            or any(type(cell) is not int or cell not in {-1, 0, 1}
                   for cell in board)):
        raise ValueError("board shape or cell domain does not match variant")
    if type(value["player"]) is not int or value["player"] not in {-1, 1}:
        raise ValueError("player must be -1 or 1")
    if type(value["arm"]) is not str or value["arm"] not in ARMS:
        raise ValueError("unknown arm")
    _integer(value["model_seed"], 0, MAX_I64, "model_seed")
    started = value["request_started_ns"]
    deadline = value["planner_deadline_ns"]
    _integer(started, 0, MAX_I64, "request_started_ns")
    _integer(deadline, 0, MAX_I64, "planner_deadline_ns")
    if not started < deadline <= started + MAX_PLANNER_NS:
        raise ValueError("planner deadline is outside the allowed interval")
    _integer(value["node_cap"], 1, 10_000, "node_cap")
    _integer(value["rss_cap_bytes"], 1, MAX_I64, "rss_cap_bytes")
    _digest(value["expected_cgroup_path_sha256"], _HEX64,
            "expected_cgroup_path_sha256")
    _integer(value["expected_memory_max"], 1, MAX_I64,
             "expected_memory_max")


def validate_response(value: Any, request: dict[str, Any],
                      request_bytes: bytes) -> None:
    validate_request(request)
    if (type(request_bytes) is not bytes
            or len(request_bytes) > MAX_REQUEST_BYTES
            or canonical_bytes(request) != request_bytes):
        raise ValueError("request object and canonical wire bytes differ")
    if type(value) is not dict or set(value) != RESPONSE_KEYS:
        raise ValueError("response keys do not match the closed schema")
    if value["schema"] != RESPONSE_SCHEMA:
        raise ValueError("response schema version mismatch")
    if value["nonce"] != request["nonce"]:
        raise ValueError("response nonce mismatch")
    expected_request_digest = hashlib.sha256(request_bytes).hexdigest()
    if value["request_sha256"] != expected_request_digest:
        raise ValueError("response request digest mismatch")
    if value["worker_cgroup_path_sha256"] != request["expected_cgroup_path_sha256"]:
        raise ValueError("response worker cgroup digest mismatch")
    if value["worker_memory_max"] != request["expected_memory_max"]:
        raise ValueError("response worker memory limit mismatch")
    _integer(value["action"], 0, 64, "action")
    _integer(value["completed_depth"], 0, 4, "completed_depth")
    if type(value["stop_reason"]) is not str or value["stop_reason"] not in STOP_REASONS:
        raise ValueError("unknown stop_reason")
    for field in (
        "node_visits", "transition_calls", "encoder_calls", "predictor_calls",
        "decoder_calls", "value_calls", "model_calls", "terminal_nodes",
        "peak_sampled_rss_bytes", "search_wall_ns",
    ):
        _integer(value[field], 0, MAX_I64, field)
    _digest(value["worker_cgroup_path_sha256"], _HEX64,
            "worker_cgroup_path_sha256")
    _integer(value["worker_memory_max"], 1, MAX_I64, "worker_memory_max")


def validate_response_wire(response_bytes: bytes, request: dict[str, Any],
                           request_bytes: bytes) -> tuple[dict[str, Any], dict[str, Any]]:
    """Validate proposal response bytes and derive metadata from those bytes.

    This offline audit helper does not publish or authenticate a supervision
    receipt. Its digest and length describe the exact bounded wire buffer.
    """
    value = decode_canonical(response_bytes, MAX_RESPONSE_BYTES)
    validate_response(value, request, request_bytes)
    evidence = {
        "response_schema": value["schema"],
        "response_sha256": hashlib.sha256(response_bytes).hexdigest(),
        "response_byte_length": len(response_bytes),
    }
    return value, evidence


def request_witness(variant: str) -> dict[str, Any]:
    cells = VARIANT_CELLS[variant]
    return {
        "schema": REQUEST_SCHEMA, "nonce": "f" * 32, "variant": variant,
        "target_ply": 24, "root_seed": MAX_I64,
        "root_state_sha256": "f" * 64, "board": [-1] * cells,
        "player": -1, "arm": "recursive-raw-state-dynamics",
        "model_seed": MAX_I64,
        "request_started_ns": MAX_I64 - MAX_PLANNER_NS,
        "planner_deadline_ns": MAX_I64, "node_cap": 10_000,
        "rss_cap_bytes": MAX_I64,
        "expected_cgroup_path_sha256": "f" * 64,
        "expected_memory_max": MAX_I64,
    }


def response_witness(nonce: str, request_bytes: bytes) -> dict[str, Any]:
    return {
        "schema": RESPONSE_SCHEMA, "nonce": nonce,
        "request_sha256": hashlib.sha256(request_bytes).hexdigest(),
        "action": 64, "completed_depth": 4,
        "stop_reason": "no_completed_root_action",
        "node_visits": MAX_I64, "transition_calls": MAX_I64,
        "encoder_calls": MAX_I64, "predictor_calls": MAX_I64,
        "decoder_calls": MAX_I64, "value_calls": MAX_I64,
        "model_calls": MAX_I64, "terminal_nodes": MAX_I64,
        "peak_sampled_rss_bytes": MAX_I64, "search_wall_ns": MAX_I64,
        "worker_cgroup_path_sha256": "f" * 64,
        "worker_memory_max": MAX_I64,
    }


def verify_proposal_caps() -> tuple[int, str, int]:
    candidates = []
    for variant in VARIANT_CELLS:
        request = request_witness(variant)
        validate_request(request)
        encoded = canonical_bytes(request)
        if len(encoded) > MAX_REQUEST_BYTES:
            raise AssertionError("request schema cap is too small")
        candidates.append((len(encoded), variant, len(request["board"])))
    request_size, variant, cells = max(candidates)
    request_bytes = canonical_bytes(request_witness(variant))
    response = response_witness("f" * 32, request_bytes)
    validate_response(response, request_witness(variant), request_bytes)
    if len(canonical_bytes(response)) > MAX_RESPONSE_BYTES:
        raise AssertionError("response schema cap is too small")
    return request_size, variant, cells


if __name__ == "__main__":
    size, variant, cells = verify_proposal_caps()
    response = response_witness("f" * 32, canonical_bytes(request_witness(variant)))
    print(f"valid_request_max_bytes={size} variant={variant} board_cells={cells}")
    print(f"response_witness_bytes={len(canonical_bytes(response))}")

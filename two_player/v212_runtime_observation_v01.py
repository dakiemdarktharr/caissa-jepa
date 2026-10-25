"""Diagnostic-only inventory format for runtime identity observations.

This schema records observations for later reproducibility analysis. It does
not attest executed bytes, create a trust anchor, or satisfy any runtime gate.
"""
from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Mapping


SCHEMA = "caissa.v212.runtime-observation.v01"
MAX_INVENTORY_BYTES = 65_536
_HEX64 = re.compile(r"^[0-9a-f]{64}$")
_TOP_FIELDS = frozenset({
    "schema", "captured_monotonic_ns", "assurance_status",
    "immutable_execution_boundary", "trust_anchor_sha256", "components",
    "inventory_sha256",
})
_COMPONENT_FIELDS = frozenset({
    "component_id", "component_type", "evidence_status", "measurement_source",
    "value",
})


class RuntimeObservationError(ValueError):
    """A diagnostic runtime observation inventory is malformed."""


def _validate_json_value(value: Any, path: str = "value") -> None:
    if value is None or type(value) in {str, bool}:
        if isinstance(value, str):
            try:
                value.encode("utf-8", errors="strict")
            except UnicodeEncodeError as exc:
                raise RuntimeObservationError(f"{path} contains an invalid Unicode scalar") from exc
        return
    if type(value) is int:
        if not -(1 << 63) <= value < (1 << 63):
            raise RuntimeObservationError(f"{path} integer is outside signed 64-bit range")
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            _validate_json_value(item, f"{path}[{index}]")
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            if not isinstance(key, str):
                raise RuntimeObservationError(f"{path} object keys must be strings")
            _validate_json_value(key, f"{path}.<key>")
            _validate_json_value(item, f"{path}.{key}")
        return
    raise RuntimeObservationError(f"{path} contains an unsupported JSON value")


def canonical_json(value: Mapping[str, Any]) -> bytes:
    if not isinstance(value, Mapping):
        raise RuntimeObservationError("inventory must be a JSON object")
    try:
        _validate_json_value(value)
        return json.dumps(value, ensure_ascii=False, allow_nan=False,
                          separators=(",", ":"), sort_keys=True).encode("utf-8")
    except RuntimeObservationError:
        raise
    except (TypeError, ValueError, UnicodeError, RecursionError) as exc:
        raise RuntimeObservationError("inventory cannot be encoded canonically") from exc


def _unsigned_inventory(inventory: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(inventory, Mapping) or set(inventory) != _TOP_FIELDS:
        raise RuntimeObservationError("inventory fields do not match the v01 schema")
    if inventory.get("schema") != SCHEMA:
        raise RuntimeObservationError("inventory schema is unsupported")
    captured = inventory.get("captured_monotonic_ns")
    if type(captured) is not int or captured <= 0:
        raise RuntimeObservationError("capture time must be a positive monotonic integer")
    if inventory.get("immutable_execution_boundary") is not False:
        raise RuntimeObservationError("v01 cannot assert an immutable execution boundary")
    if inventory.get("trust_anchor_sha256") is not None:
        raise RuntimeObservationError("v01 has no independent trust-anchor field")

    components = inventory.get("components")
    if not isinstance(components, list):
        raise RuntimeObservationError("components must be an array")
    identifiers: set[str] = set()
    observed_any = False
    for component in components:
        if not isinstance(component, Mapping) or set(component) != _COMPONENT_FIELDS:
            raise RuntimeObservationError("component fields do not match the v01 schema")
        component_id = component.get("component_id")
        component_type = component.get("component_type")
        evidence_status = component.get("evidence_status")
        source = component.get("measurement_source")
        value = component.get("value")
        if not isinstance(component_id, str) or not component_id:
            raise RuntimeObservationError("component_id must be a nonempty string")
        if component_id in identifiers:
            raise RuntimeObservationError("component_id values must be unique")
        identifiers.add(component_id)
        if not isinstance(component_type, str) or not component_type:
            raise RuntimeObservationError("component_type must be a nonempty string")
        if (not isinstance(evidence_status, str)
                or evidence_status not in {"observed_unverified", "unavailable"}):
            raise RuntimeObservationError("v01 cannot mark a component verified")
        if not isinstance(source, str) or not source:
            raise RuntimeObservationError("measurement_source must be a nonempty string")
        if evidence_status == "observed_unverified":
            observed_any = True
            if not isinstance(value, Mapping):
                raise RuntimeObservationError("observed component value must be an object")
        elif value is not None:
            raise RuntimeObservationError("unavailable component value must be null")

    expected_assurance = "partial" if observed_any else "unavailable"
    if inventory.get("assurance_status") != expected_assurance:
        raise RuntimeObservationError("assurance_status does not match diagnostic evidence")
    unsigned = {key: value for key, value in inventory.items()
                if key != "inventory_sha256"}
    # Route recursive validation through the canonical encoder so deeply
    # nested caller-supplied values become the schema's stable error type.
    canonical_json(unsigned)
    digest = inventory.get("inventory_sha256")
    if (not isinstance(digest, str) or not _HEX64.fullmatch(digest)
            or hashlib.sha256(canonical_json(unsigned)).hexdigest() != digest):
        raise RuntimeObservationError("inventory digest does not match canonical fields")
    return unsigned


def build_inventory(*, captured_monotonic_ns: int,
                    components: list[Mapping[str, Any]]) -> dict[str, Any]:
    """Create an integrity-checksummed inventory that is never an attestation."""
    has_observation = any(
        isinstance(component, Mapping)
        and component.get("evidence_status") == "observed_unverified"
        for component in components
    )
    unsigned = {
        "schema": SCHEMA,
        "captured_monotonic_ns": captured_monotonic_ns,
        "assurance_status": "partial" if has_observation else "unavailable",
        "immutable_execution_boundary": False,
        "trust_anchor_sha256": None,
        "components": [dict(component) if isinstance(component, Mapping) else component
                       for component in components],
    }
    digest = hashlib.sha256(canonical_json(unsigned)).hexdigest()
    inventory = dict(unsigned, inventory_sha256=digest)
    _unsigned_inventory(inventory)
    if len(canonical_json(inventory)) > MAX_INVENTORY_BYTES:
        raise RuntimeObservationError("inventory exceeds its byte bound")
    return inventory


def encode_inventory(inventory: Mapping[str, Any]) -> bytes:
    _unsigned_inventory(inventory)
    payload = canonical_json(inventory)
    if not 1 <= len(payload) <= MAX_INVENTORY_BYTES:
        raise RuntimeObservationError("inventory exceeds its byte bound")
    return payload


def parse_inventory(payload: bytes) -> dict[str, Any]:
    if not isinstance(payload, bytes) or not 1 <= len(payload) <= MAX_INVENTORY_BYTES:
        raise RuntimeObservationError("inventory bytes exceed the bounded schema")

    def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        parsed: dict[str, Any] = {}
        for key, value in items:
            if key in parsed:
                raise RuntimeObservationError("inventory contains a duplicate JSON key")
            parsed[key] = value
        return parsed

    def reject_constant(_value: str) -> None:
        raise RuntimeObservationError("inventory contains a non-finite number")

    try:
        value = json.loads(payload.decode("utf-8", errors="strict"),
                           object_pairs_hook=pairs, parse_constant=reject_constant)
    except RuntimeObservationError:
        raise
    except (UnicodeError, json.JSONDecodeError, RecursionError, ValueError) as exc:
        raise RuntimeObservationError("inventory is not bounded UTF-8 JSON") from exc
    if not isinstance(value, dict) or canonical_json(value) != payload:
        raise RuntimeObservationError("inventory must use canonical JSON bytes")
    _unsigned_inventory(value)
    return value


__all__ = ["MAX_INVENTORY_BYTES", "RuntimeObservationError", "SCHEMA",
           "build_inventory", "canonical_json", "encode_inventory", "parse_inventory"]

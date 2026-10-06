import hashlib
import unittest

from two_player.v212_runtime_observation_v01 import (
    MAX_INVENTORY_BYTES,
    RuntimeObservationError,
    build_inventory,
    canonical_json,
    encode_inventory,
    parse_inventory,
)


def observed_component():
    return {
        "component_id": "python-interpreter",
        "component_type": "interpreter",
        "evidence_status": "observed_unverified",
        "measurement_source": "diagnostic-fixture",
        "value": {"path": "/usr/bin/python", "sha256": "a" * 64},
    }


def unavailable_component():
    return {
        "component_id": "dynamic-loader",
        "component_type": "loader",
        "evidence_status": "unavailable",
        "measurement_source": "not-measured",
        "value": None,
    }


def resigned(inventory):
    unsigned = {key: value for key, value in inventory.items()
                if key != "inventory_sha256"}
    return dict(unsigned, inventory_sha256=hashlib.sha256(
        canonical_json(unsigned)).hexdigest())


class RuntimeObservationV01Tests(unittest.TestCase):
    def test_observations_round_trip_as_partial_diagnostic(self):
        inventory = build_inventory(captured_monotonic_ns=123, components=[
            observed_component(), unavailable_component()])
        self.assertEqual(inventory["assurance_status"], "partial")
        self.assertFalse(inventory["immutable_execution_boundary"])
        self.assertIsNone(inventory["trust_anchor_sha256"])
        self.assertEqual(parse_inventory(encode_inventory(inventory)), inventory)

    def test_all_unavailable_is_unavailable(self):
        inventory = build_inventory(captured_monotonic_ns=123,
                                    components=[unavailable_component()])
        self.assertEqual(inventory["assurance_status"], "unavailable")
        self.assertIsNone(inventory["components"][0]["value"])

    def test_inventory_cannot_assert_trusted_execution(self):
        baseline = build_inventory(captured_monotonic_ns=123,
                                   components=[observed_component()])
        for field, value in (("assurance_status", "verified"),
                             ("immutable_execution_boundary", True),
                             ("trust_anchor_sha256", "b" * 64)):
            with self.subTest(field=field):
                candidate = dict(baseline, **{field: value})
                with self.assertRaises(RuntimeObservationError):
                    encode_inventory(resigned(candidate))

    def test_component_cannot_be_marked_verified(self):
        component = dict(observed_component(), evidence_status="verified")
        with self.assertRaises(RuntimeObservationError):
            build_inventory(captured_monotonic_ns=123, components=[component])
        component = dict(observed_component(), evidence_status=[])
        with self.assertRaises(RuntimeObservationError):
            build_inventory(captured_monotonic_ns=123, components=[component])

    def test_rejects_duplicate_keys_noncanonical_json_and_nonfinite_values(self):
        inventory = build_inventory(captured_monotonic_ns=123,
                                    components=[observed_component()])
        encoded = encode_inventory(inventory)
        with self.assertRaises(RuntimeObservationError):
            parse_inventory(encoded.replace(b'{"assurance_status":',
                                             b'{"schema":"duplicate","assurance_status":', 1))
        with self.assertRaises(RuntimeObservationError):
            parse_inventory(encoded + b" ")
        with self.assertRaises(RuntimeObservationError):
            parse_inventory(b'{"x":NaN}')

    def test_rejects_integer_outside_signed_64_bit_range(self):
        with self.assertRaises(RuntimeObservationError):
            build_inventory(captured_monotonic_ns=123, components=[dict(
                observed_component(), value={"counter": 1 << 63})])

    def test_deeply_nested_values_use_schema_error_contract(self):
        inventory = build_inventory(captured_monotonic_ns=123,
                                    components=[observed_component()])
        nested = {}
        for _ in range(1500):
            nested = {"next": nested}
        component = dict(observed_component(), value=nested)
        candidate = dict(inventory, components=[component])
        with self.assertRaises(RuntimeObservationError):
            encode_inventory(candidate)

    def test_byte_bound_is_enforced(self):
        with self.assertRaises(RuntimeObservationError):
            parse_inventory(b" " * (MAX_INVENTORY_BYTES + 1))
        with self.assertRaises(RuntimeObservationError):
            build_inventory(captured_monotonic_ns=123, components=[dict(
                observed_component(), value={"description": "x" * MAX_INVENTORY_BYTES})])


if __name__ == "__main__":
    unittest.main()

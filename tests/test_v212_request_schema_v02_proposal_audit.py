import copy
import hashlib
import unittest

from two_player import v212_request_schema_v02_proposal_audit as audit


class RequestSchemaProposalAuditTests(unittest.TestCase):
    def test_valid_variant_witnesses_and_caps(self):
        self.assertEqual(audit.verify_proposal_caps(),
                         (811, "connect4-gravity-8x8", 64))
        self.assertEqual(len(audit.canonical_bytes(audit.response_witness(
            "f" * 32,
            audit.canonical_bytes(audit.request_witness("connect4-gravity-8x8")),
        ))), 747)

    def test_cross_variant_board_size_is_rejected(self):
        request = audit.request_witness("connect4-gravity-6x7")
        request["board"] = [-1] * 64
        with self.assertRaisesRegex(ValueError, "board shape"):
            audit.validate_request(request)

    def test_request_rejects_boolean_integer_float_and_open_keys(self):
        cases = []
        for key, value in (("root_seed", True), ("root_seed", 1.0),
                           ("target_ply", 1), ("node_cap", 10_001)):
            request = audit.request_witness("reversi8")
            request[key] = value
            cases.append(request)
        request = audit.request_witness("reversi8")
        request["extra"] = 0
        cases.append(request)
        for request in cases:
            with self.subTest(request=request):
                with self.assertRaises(ValueError):
                    audit.validate_request(request)

    def test_deadline_and_digest_domains_are_enforced(self):
        request = audit.request_witness("reversi8")
        request["planner_deadline_ns"] = request["request_started_ns"]
        with self.assertRaisesRegex(ValueError, "deadline"):
            audit.validate_request(request)
        request = audit.request_witness("reversi8")
        request["root_state_sha256"] = "F" * 64
        with self.assertRaisesRegex(ValueError, "lowercase hex"):
            audit.validate_request(request)

    def test_wire_decoder_rejects_duplicate_noncanonical_and_float_json(self):
        for raw in (
            b'{"x":1,"x":1}',
            b'{"x":{"y":1,"y":1}}',
            b'{ "x":1}',
            b'{"x":1.0}',
            b'{"x":NaN}',
            b'{"x":"\\ud800"}',
            b"\xef\xbb\xbf{}",
            b'{} {}',
        ):
            with self.subTest(raw=raw):
                with self.assertRaises(ValueError):
                    audit.decode_canonical(raw, 64)

    def test_request_wire_size_cap_includes_cap_plus_one_rejection(self):
        request = audit.request_witness("connect4-gravity-8x8")
        raw = audit.canonical_bytes(request)
        self.assertEqual(len(raw), audit.MAX_REQUEST_BYTES)
        self.assertEqual(audit.decode_canonical(raw, audit.MAX_REQUEST_BYTES),
                         request)
        with self.assertRaisesRegex(ValueError, "byte cap"):
            audit.decode_canonical(b" " * (audit.MAX_REQUEST_BYTES + 1),
                                   audit.MAX_REQUEST_BYTES)


class ResponseSchemaProposalAuditTests(unittest.TestCase):
    def setUp(self):
        self.request = audit.request_witness("reversi8")
        self.request_bytes = audit.canonical_bytes(self.request)
        self.response = audit.response_witness(self.request["nonce"],
                                               self.request_bytes)

    def test_valid_response_maximum_and_binding(self):
        audit.validate_response(self.response, self.request, self.request_bytes)
        raw = audit.canonical_bytes(self.response)
        self.assertEqual(len(raw), audit.MAX_RESPONSE_BYTES)
        self.assertEqual(audit.decode_canonical(raw, audit.MAX_RESPONSE_BYTES),
                         self.response)
        self.assertEqual(hashlib.sha256(self.request_bytes).hexdigest(),
                         self.response["request_sha256"])

    def test_response_wire_validation_binds_exact_digest_schema_and_length(self):
        raw = audit.canonical_bytes(self.response)
        validated, evidence = audit.validate_response_wire(
            raw, self.request, self.request_bytes)
        self.assertEqual(validated, self.response)
        self.assertEqual(evidence, {
            "response_schema": audit.RESPONSE_SCHEMA,
            "response_sha256": hashlib.sha256(raw).hexdigest(),
            "response_byte_length": len(raw),
        })

    def test_response_wire_validation_rejects_noncanonical_and_oversized_bytes(self):
        raw = audit.canonical_bytes(self.response)
        for payload in (raw + b" ", b" " * (audit.MAX_RESPONSE_BYTES + 1)):
            with self.subTest(length=len(payload)):
                with self.assertRaises(ValueError):
                    audit.validate_response_wire(
                        payload, self.request, self.request_bytes)

    def test_response_wire_cap_rejects_cap_plus_one(self):
        with self.assertRaisesRegex(ValueError, "byte cap"):
            audit.decode_canonical(b" " * (audit.MAX_RESPONSE_BYTES + 1),
                                   audit.MAX_RESPONSE_BYTES)

    def test_response_rejects_wrong_binding_or_open_schema(self):
        response = copy.deepcopy(self.response)
        response["nonce"] = "0" * 32
        with self.assertRaisesRegex(ValueError, "nonce"):
            audit.validate_response(response, self.request, self.request_bytes)
        response = copy.deepcopy(self.response)
        response["extra"] = 0
        with self.assertRaisesRegex(ValueError, "closed schema"):
            audit.validate_response(response, self.request, self.request_bytes)
        response = copy.deepcopy(self.response)
        response["request_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "request digest"):
            audit.validate_response(response, self.request, self.request_bytes)
        response = copy.deepcopy(self.response)
        response["worker_cgroup_path_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "cgroup digest"):
            audit.validate_response(response, self.request, self.request_bytes)
        response = copy.deepcopy(self.response)
        response["worker_memory_max"] += 1
        with self.assertRaisesRegex(ValueError, "memory limit"):
            audit.validate_response(response, self.request, self.request_bytes)

    def test_response_rejects_request_bytes_mismatch(self):
        with self.assertRaisesRegex(ValueError, "canonical wire bytes"):
            audit.validate_response(self.response, self.request,
                                    self.request_bytes + b" ")

    def test_response_rejects_boolean_counters_and_noncanonical_action_type(self):
        for key, value in (("node_visits", True), ("action", 1.0),
                           ("completed_depth", 5),
                           ("worker_memory_max", 0)):
            response = copy.deepcopy(self.response)
            response[key] = value
            with self.subTest(key=key):
                with self.assertRaises(ValueError):
                    audit.validate_response(response, self.request,
                                           self.request_bytes)


if __name__ == "__main__":
    unittest.main()

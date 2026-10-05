import hashlib
import json
import tempfile
import threading
import time
import unittest
from pathlib import Path

from two_player import v212_armed_protocol_v02 as armed
from two_player import v212_release_token_v02 as release
from two_player import v212_worker_ipc as ipc


class ArmedProtocolV02Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.parent = self.root / "ipc"
        self.parent.mkdir(mode=0o700)
        self.cgroup_root = self.root / "cgroup"
        self.control_group = "/user.slice/caissa-mock.service"
        cgroup = self.cgroup_root / self.control_group.lstrip("/")
        cgroup.mkdir(parents=True)
        for key, value in (("memory.max", "134217728"),
                           ("memory.high", "100663296"),
                           ("memory.swap.max", "0")):
            (cgroup / key).write_text(value + "\n", encoding="ascii")
        self.nonce = "a" * 32
        self.request_bytes = json.dumps(
            {"schema": "synthetic.request.v01", "nonce": self.nonce},
            sort_keys=True, separators=(",", ":")).encode()
        self.request_sha256 = hashlib.sha256(self.request_bytes).hexdigest()
        self.source_sha256 = hashlib.sha256(b"worker source").hexdigest()
        self.snapshot = {
            "schema": release.SCHEMA,
            "request_nonce": self.nonce,
            "request_sha256": self.request_sha256,
            "service_unit": "caissa-mock.service",
            "invocation_id": "b" * 32,
            "boot_id": "c" * 32,
            "control_group": self.control_group,
            "effective_properties": dict(armed.EXPECTED_EFFECTIVE_PROPERTIES),
            "live_cgroup": {"memory.max": "134217728",
                            "memory.high": "100663296",
                            "memory.swap.max": "0"},
            "source_manifest_sha256": self.source_sha256,
            "captured_monotonic_ns": time.monotonic_ns(),
        }

    def tearDown(self):
        self.temp.cleanup()

    def _workspace(self):
        return ipc.create_workspace({"schema": "fixture"}, parent=self.parent,
                                    with_release_fifo=True)

    def _worker(self, workspace, request_bytes, callbacks, failures):
        try:
            result = armed.run_synthetic_armed_worker(
                workspace, request_bytes=request_bytes,
                expected_nonce=self.nonce,
                expected_service_unit=self.snapshot["service_unit"],
                invocation_id=self.snapshot["invocation_id"],
                boot_id=self.snapshot["boot_id"],
                self_control_group=self.control_group,
                expected_source_manifest_sha256=self.source_sha256,
                cgroup_root=self.cgroup_root,
                on_release=lambda token: callbacks.append(token["request_sha256"])
                or "released")
            callbacks.append(result)
        except BaseException as exc:
            failures.append(exc)

    def test_release_token_binds_hash_of_exact_request_bytes(self):
        payload = armed._validate_snapshot(
            self.snapshot, deadline_monotonic_ns=time.monotonic_ns() + 5_000_000_000)
        token = release.parse_token(payload)
        self.assertEqual(token["request_sha256"], self.request_sha256)
        altered = dict(token)
        altered["request_sha256"] = "0" * 64
        unsigned = {key: value for key, value in altered.items()
                    if key != "token_sha256"}
        altered["token_sha256"] = release.token_digest(unsigned)
        with self.assertRaisesRegex(release.ReleaseTokenError, "request-byte digest"):
            release.verify_token(
                release.canonical_json(altered), expected_nonce=self.nonce,
                expected_request_sha256=self.request_sha256,
                expected_service_unit=self.snapshot["service_unit"],
                invocation_id=self.snapshot["invocation_id"],
                boot_id=self.snapshot["boot_id"],
                self_control_group=self.control_group,
                expected_source_manifest_sha256=self.source_sha256,
                cgroup_root=self.cgroup_root)

    def test_matching_exact_bytes_release_after_token_verification(self):
        workspace = self._workspace()
        callbacks, failures = [], []
        thread = threading.Thread(
            target=self._worker,
            args=(workspace, self.request_bytes, callbacks, failures), daemon=True)
        thread.start()
        try:
            armed.release_when_ready(
                workspace, self.snapshot, deadline=time.monotonic() + 1)
            thread.join(timeout=1)
            self.assertFalse(thread.is_alive())
            self.assertEqual(failures, [])
            self.assertEqual(callbacks, [self.request_sha256, "released"])
        finally:
            thread.join(timeout=1)
            ipc.cleanup_workspace(workspace)

    def test_changed_bytes_with_same_nonce_never_reach_callback(self):
        workspace = self._workspace()
        changed = self.request_bytes + b" "
        callbacks, failures = [], []
        thread = threading.Thread(
            target=self._worker, args=(workspace, changed, callbacks, failures),
            daemon=True)
        thread.start()
        try:
            armed.release_when_ready(
                workspace, self.snapshot, deadline=time.monotonic() + 1)
            thread.join(timeout=1)
            self.assertFalse(thread.is_alive())
            self.assertEqual(callbacks, [])
            self.assertEqual(len(failures), 1)
            self.assertIsInstance(failures[0], armed.ArmedProtocolError)
            self.assertIn("before compute", str(failures[0]))
        finally:
            thread.join(timeout=1)
            ipc.cleanup_workspace(workspace)

    def test_request_parser_rejects_duplicate_keys_nonobject_and_oversize(self):
        for payload in (b'{"nonce":"a","nonce":"b"}', b"[]",
                        b" " * (ipc.MAX_IPC_BYTES + 1)):
            with self.subTest(payload_len=len(payload)):
                with self.assertRaises(armed.ArmedProtocolError):
                    armed._parse_request_bytes(payload)

    def test_invalid_request_is_rejected_before_waiting_on_release_fifo(self):
        workspace = self._workspace()
        try:
            with self.assertRaisesRegex(armed.ArmedProtocolError, "duplicate JSON"):
                armed.run_synthetic_armed_worker(
                    workspace, request_bytes=b'{"nonce":"a","nonce":"b"}',
                    expected_nonce=self.nonce,
                    expected_service_unit=self.snapshot["service_unit"],
                    invocation_id=self.snapshot["invocation_id"],
                    boot_id=self.snapshot["boot_id"],
                    self_control_group=self.control_group,
                    expected_source_manifest_sha256=self.source_sha256,
                    cgroup_root=self.cgroup_root, on_release=lambda _token: self.fail())
            self.assertFalse(workspace.release_writer_state.claimed)
        finally:
            ipc.cleanup_workspace(workspace)


if __name__ == "__main__":
    unittest.main()

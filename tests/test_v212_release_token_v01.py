import hashlib
import json
import os
from pathlib import Path
import tempfile
import threading
import time
import unittest

from two_player import v212_release_token_v01 as release
from two_player import v212_worker_ipc as ipc


class ReleaseTokenTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.control_group = "/user.slice/caissa-test.service"
        self.group_dir = self.root / self.control_group.lstrip("/")
        self.group_dir.mkdir(parents=True)
        self.live = {"memory.max": "134217728", "memory.high": "100663296",
                     "memory.swap.max": "0"}
        for name, value in self.live.items():
            (self.group_dir / name).write_text(value + "\n", encoding="ascii")
        self.context = {
            "expected_nonce": "n" * 64,
            "expected_service_unit": "caissa-test.service",
            "invocation_id": "a" * 32,
            "boot_id": "b" * 32,
            "self_control_group": self.control_group,
            "expected_source_manifest_sha256": hashlib.sha256(
                b"source bundle").hexdigest(),
            "cgroup_root": self.root,
        }

    def tearDown(self):
        self.temp.cleanup()

    def _payload(self, **changes):
        fields = {
            "schema": release.SCHEMA,
            "request_nonce": self.context["expected_nonce"],
            "service_unit": self.context["expected_service_unit"],
            "invocation_id": self.context["invocation_id"],
            "boot_id": self.context["boot_id"],
            "control_group": self.control_group,
            "effective_properties": {
                "EffectiveMemoryMax": "134217728",
                "EffectiveMemoryHigh": "100663296",
                "MemorySwapMax": "0",
                "LimitFSIZE": "65536",
                "RuntimeMaxUSec": "8s",
                "Restart": "no",
                "OOMPolicy": "kill",
                "RemainAfterExit": "yes",
            },
            "live_cgroup": dict(self.live),
            "source_manifest_sha256": hashlib.sha256(b"source bundle").hexdigest(),
            "captured_monotonic_ns": 123456789,
            "deadline_monotonic_ns": 987654321,
        }
        fields.update(changes)
        token = dict(fields, token_sha256=release.token_digest(fields))
        return release.canonical_json(token)

    def test_parses_and_verifies_a_valid_bound_token(self):
        payload = self._payload()
        parsed = release.verify_token(payload, **self.context)
        self.assertEqual(parsed["schema"], release.SCHEMA)

    def test_rejects_request_unit_invocation_boot_and_cgroup_mismatches(self):
        payload = self._payload()
        for key, value in (
                ("expected_nonce", "wrong"),
                ("expected_service_unit", "other.service"),
                ("invocation_id", "c" * 32),
                ("boot_id", "d" * 32),
                ("self_control_group", "/user.slice/other.service"),
                ("expected_source_manifest_sha256", "f" * 64)):
            with self.subTest(key=key), self.assertRaises(release.ReleaseTokenError):
                release.verify_token(payload, **dict(self.context, **{key: value}))

    def test_rejects_digest_or_live_cgroup_limit_mismatch(self):
        token = json.loads(self._payload())
        token["live_cgroup"]["memory.max"] = "268435456"
        stale_digest = release.canonical_json(token)
        with self.assertRaisesRegex(release.ReleaseTokenError, "digest"):
            release.verify_token(stale_digest, **self.context)

        token = json.loads(self._payload())
        token["live_cgroup"]["memory.max"] = "268435456"
        unsigned = {key: value for key, value in token.items() if key != "token_sha256"}
        token["token_sha256"] = release.token_digest(unsigned)
        changed = release.canonical_json(token)
        with self.assertRaisesRegex(release.ReleaseTokenError, "memory.max"):
            release.verify_token(changed, **self.context)

    def test_rejects_duplicate_keys_unknown_fields_bad_schema_and_oversize(self):
        with self.assertRaisesRegex(release.ReleaseTokenError, "duplicate"):
            release.parse_token(b'{"schema":"a","schema":"b"}')
        token = json.loads(self._payload())
        token["schema"] = "wrong.v1"
        with self.assertRaisesRegex(release.ReleaseTokenError, "schema"):
            release.parse_token(release.canonical_json(token))
        token = json.loads(self._payload())
        token["extra"] = 1
        with self.assertRaisesRegex(release.ReleaseTokenError, "fields"):
            release.parse_token(release.canonical_json(token))
        with self.assertRaisesRegex(release.ReleaseTokenError, "canonical"):
            release.parse_token(b" " + self._payload())
        with self.assertRaisesRegex(release.ReleaseTokenError, "1..4096"):
            release.parse_token(b" " * 4097)

    def test_rejects_traversal_and_missing_or_unexpected_cgroup_files(self):
        token = json.loads(self._payload())
        token["control_group"] = "/user.slice/../escape"
        unsigned = {key: value for key, value in token.items() if key != "token_sha256"}
        token["token_sha256"] = release.token_digest(unsigned)
        with self.assertRaisesRegex(release.ReleaseTokenError, "normalized"):
            release.verify_token(release.canonical_json(token), **self.context)

        token = json.loads(self._payload())
        token["control_group"] = "/user.slice//caissa-test.service"
        unsigned = {key: value for key, value in token.items() if key != "token_sha256"}
        token["token_sha256"] = release.token_digest(unsigned)
        with self.assertRaisesRegex(release.ReleaseTokenError, "normalized"):
            release.verify_token(release.canonical_json(token), **self.context)

        (self.group_dir / "memory.high").unlink()
        with self.assertRaisesRegex(release.ReleaseTokenError, "unavailable"):
            release.verify_token(self._payload(), **self.context)

    def test_worker_blocks_on_fifo_open_then_consumes_one_payload_to_eof(self):
        workspace = ipc.create_workspace({"request_schema": "test.v1"},
                                         parent=self.root,
                                         with_release_fifo=True)
        result = []
        failures = []
        opening = threading.Event()

        def worker():
            try:
                opening.set()
                result.append(release.read_release_fifo(
                    workspace.directory,
                    directory_device=workspace.directory_device,
                    directory_inode=workspace.directory_inode,
                    fifo_identity=workspace.release_identity))
            except BaseException as exc:
                failures.append(exc)

        thread = threading.Thread(target=worker, daemon=True)
        thread.start()
        self.assertTrue(opening.wait(1))
        writer = None
        try:
            deadline = time.monotonic() + 1
            while writer is None and time.monotonic() < deadline:
                writer = ipc.open_release_writer(workspace)
                if writer is None:
                    time.sleep(0.001)
            self.assertIsNotNone(writer)
            payload = self._payload()
            ipc.write_release(workspace, writer, payload)
            thread.join(timeout=1)
            self.assertFalse(thread.is_alive())
            self.assertEqual(failures, [])
            self.assertEqual(result, [payload])
            release.verify_token(result[0], **self.context)
        finally:
            if writer is not None and workspace.release_writer_state is not None \
                    and not workspace.release_writer_state.consumed:
                os.close(writer)
            thread.join(timeout=1)
        ipc.cleanup_workspace(workspace)

    def test_worker_rejects_fifo_eof_without_a_release_payload(self):
        workspace = ipc.create_workspace({"request_schema": "test.v1"},
                                         parent=self.root,
                                         with_release_fifo=True)
        errors = []

        def worker():
            try:
                release.read_release_fifo(
                    workspace.directory,
                    directory_device=workspace.directory_device,
                    directory_inode=workspace.directory_inode,
                    fifo_identity=workspace.release_identity)
            except release.ReleaseTokenError as exc:
                errors.append(str(exc))

        thread = threading.Thread(target=worker, daemon=True)
        thread.start()
        writer = None
        try:
            deadline = time.monotonic() + 1
            while writer is None and time.monotonic() < deadline:
                writer = ipc.open_release_writer(workspace)
                if writer is None:
                    time.sleep(0.001)
            self.assertIsNotNone(writer)
            os.close(writer)
            thread.join(timeout=1)
            self.assertFalse(thread.is_alive())
            self.assertEqual(errors, ["release FIFO closed without a token"])
        finally:
            thread.join(timeout=1)
        ipc.cleanup_workspace(workspace)

    def test_worker_rejects_substituted_fifo_before_blocking_open(self):
        workspace = ipc.create_workspace({"request_schema": "test.v1"},
                                         parent=self.root,
                                         with_release_fifo=True)
        workspace.release_path.unlink()
        os.mkfifo(workspace.release_path, 0o600)
        with self.assertRaisesRegex(release.ReleaseTokenError, "identity changed"):
            release.read_release_fifo(
                workspace.directory,
                directory_device=workspace.directory_device,
                directory_inode=workspace.directory_inode,
                fifo_identity=workspace.release_identity)

    def test_worker_rejects_fifo_payload_over_4096_bytes(self):
        workspace = ipc.create_workspace({"request_schema": "test.v1"},
                                         parent=self.root,
                                         with_release_fifo=True)
        errors = []
        ready = threading.Event()

        def worker():
            try:
                ready.set()
                release.read_release_fifo(
                    workspace.directory,
                    directory_device=workspace.directory_device,
                    directory_inode=workspace.directory_inode,
                    fifo_identity=workspace.release_identity)
            except release.ReleaseTokenError as exc:
                errors.append(str(exc))

        thread = threading.Thread(target=worker, daemon=True)
        thread.start()
        writer = None
        offset = 0
        payload = b"x" * (release.MAX_RELEASE_BYTES + 1)
        try:
            self.assertTrue(ready.wait(1))
            deadline = time.monotonic() + 1
            while writer is None and time.monotonic() < deadline:
                writer = ipc.open_release_writer(workspace)
                if writer is None:
                    time.sleep(0.001)
            self.assertIsNotNone(writer)
            deadline = time.monotonic() + 1
            while offset < len(payload) and time.monotonic() < deadline:
                try:
                    offset += os.write(writer, payload[offset:])
                except BrokenPipeError:
                    break
            self.assertEqual(offset, len(payload))
            thread.join(timeout=1)
            self.assertFalse(thread.is_alive())
            self.assertEqual(errors, ["release token exceeds 4096 bytes"])
        finally:
            if writer is not None:
                os.close(writer)
            thread.join(timeout=1)
        ipc.cleanup_workspace(workspace)


if __name__ == "__main__":
    unittest.main()

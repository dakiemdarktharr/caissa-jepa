import hashlib
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from two_player import v212_armed_protocol_v01 as armed
from two_player import v212_release_token_v01 as release
from two_player import v212_worker_ipc as ipc


class ArmedProtocolTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.ipc_parent = self.root / "ipc-parent"
        self.ipc_parent.mkdir(mode=0o700)
        self.cgroup_root = self.root / "cgroup"
        self.control_group = "/user.slice/caissa-mock.service"
        self.cgroup = self.cgroup_root / self.control_group.lstrip("/")
        self.cgroup.mkdir(parents=True)
        self.live = {"memory.max": "134217728", "memory.high": "100663296",
                     "memory.swap.max": "0"}
        for name, value in self.live.items():
            (self.cgroup / name).write_text(value + "\n", encoding="ascii")
        self.source_hash = hashlib.sha256(b"verified source manifest").hexdigest()
        self.snapshot = {
            "schema": release.SCHEMA,
            "request_nonce": "e" * 64,
            "service_unit": "caissa-mock.service",
            "invocation_id": "a" * 32,
            "boot_id": "b" * 32,
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
            "source_manifest_sha256": self.source_hash,
            "captured_monotonic_ns": 123456789,
        }

    def tearDown(self):
        self.temp.cleanup()

    def _workspace(self):
        return ipc.create_workspace({"schema": "mock.v1"},
                                    parent=self.ipc_parent,
                                    with_release_fifo=True)

    def _worker_kwargs(self, *, nonce=None):
        return {
            "expected_nonce": nonce or self.snapshot["request_nonce"],
            "expected_service_unit": self.snapshot["service_unit"],
            "invocation_id": self.snapshot["invocation_id"],
            "boot_id": self.snapshot["boot_id"],
            "self_control_group": self.control_group,
            "expected_source_manifest_sha256": self.source_hash,
            "cgroup_root": self.cgroup_root,
        }

    def test_worker_callback_runs_only_after_verified_controller_release(self):
        workspace = self._workspace()
        completed = []
        failures = []
        ready = threading.Event()

        def worker():
            try:
                ready.set()
                result = armed.run_synthetic_armed_worker(
                    workspace, **self._worker_kwargs(),
                    on_release=lambda token: completed.append(token["token_sha256"]) or "ok")
                completed.append(result)
            except BaseException as exc:
                failures.append(exc)

        thread = threading.Thread(target=worker, daemon=True)
        thread.start()
        self.assertTrue(ready.wait(1))
        try:
            token_bytes = armed.release_when_ready(
                workspace, self.snapshot, deadline=time.monotonic() + 1)
            thread.join(timeout=1)
            self.assertFalse(thread.is_alive())
            self.assertEqual(failures, [])
            self.assertEqual(len(completed), 2)
            self.assertEqual(completed[-1], "ok")
            self.assertEqual(release.parse_token(token_bytes)["token_sha256"],
                             completed[0])
        finally:
            thread.join(timeout=1)
        ipc.cleanup_workspace(workspace)

    def test_invalid_effective_properties_fail_before_fifo_open(self):
        for name, value in (("OOMPolicy", "continue"), ("Restart", "always"),
                            ("EffectiveMemoryMax", "max"),
                            ("LimitFSIZE", "infinity"),
                            ("RuntimeMaxUSec", "infinity")):
            with self.subTest(property=name):
                workspace = self._workspace()
                bad = {**self.snapshot,
                       "effective_properties": dict(self.snapshot["effective_properties"])}
                bad["effective_properties"][name] = value
                with patch.object(armed.ipc, "open_release_writer") as open_writer:
                    with self.assertRaisesRegex(armed.ArmedProtocolError,
                                                "effective service properties"):
                        armed.release_when_ready(workspace, bad, deadline=1)
                open_writer.assert_not_called()
                ipc.cleanup_workspace(workspace)

    def test_wrong_worker_nonce_rejects_before_callback(self):
        workspace = self._workspace()
        callbacks = []
        errors = []

        def worker():
            try:
                armed.run_synthetic_armed_worker(
                    workspace, **self._worker_kwargs(nonce="wrong"),
                    on_release=lambda token: callbacks.append(token))
            except armed.ArmedProtocolError as exc:
                errors.append(str(exc))

        thread = threading.Thread(target=worker, daemon=True)
        thread.start()
        try:
            armed.release_when_ready(
                workspace, self.snapshot, deadline=time.monotonic() + 1)
            thread.join(timeout=1)
            self.assertFalse(thread.is_alive())
            self.assertEqual(callbacks, [])
            self.assertEqual(errors, ["worker rejected release before compute"])
        finally:
            thread.join(timeout=1)
        ipc.cleanup_workspace(workspace)

    def test_worker_rechecks_deadline_after_release_before_callback(self):
        workspace = self._workspace()
        callbacks = []
        errors = []

        def worker():
            try:
                armed.run_synthetic_armed_worker(
                    workspace, **self._worker_kwargs(),
                    on_release=lambda token: callbacks.append(token),
                    monotonic_ns=lambda: int((time.monotonic() + 2) * 1_000_000_000))
            except armed.ArmedProtocolError as exc:
                errors.append(str(exc))

        thread = threading.Thread(target=worker, daemon=True)
        thread.start()
        try:
            armed.release_when_ready(
                workspace, self.snapshot, deadline=time.monotonic() + 1)
            thread.join(timeout=1)
            self.assertFalse(thread.is_alive())
            self.assertEqual(callbacks, [])
            self.assertEqual(errors, ["worker rejected release after caller deadline"])
        finally:
            thread.join(timeout=1)
        ipc.cleanup_workspace(workspace)

    def test_deadline_expiry_without_ready_worker_sends_nothing(self):
        workspace = self._workspace()
        now = [10.0]

        def fake_sleep(duration):
            now[0] += duration

        with self.assertRaisesRegex(armed.ArmedProtocolError, "deadline expired"):
            armed.release_when_ready(workspace, self.snapshot, deadline=10.02,
                                     clock=lambda: now[0], sleep=fake_sleep,
                                     poll_interval=0.01)
        self.assertFalse(workspace.release_writer_state.claimed)
        ipc.cleanup_workspace(workspace)

    def test_snapshot_and_live_cgroup_disagreement_never_releases(self):
        workspace = self._workspace()
        bad = {**self.snapshot, "live_cgroup": dict(self.snapshot["live_cgroup"])}
        bad["live_cgroup"]["memory.max"] = "268435456"
        with patch.object(armed.ipc, "open_release_writer") as open_writer:
            with self.assertRaisesRegex(armed.ArmedProtocolError, "disagrees"):
                armed.release_when_ready(workspace, bad, deadline=1)
        open_writer.assert_not_called()
        ipc.cleanup_workspace(workspace)


if __name__ == "__main__":
    unittest.main()

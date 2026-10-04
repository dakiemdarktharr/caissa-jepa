import json
from contextlib import ExitStack, contextmanager
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from two_player import v212_supervision_collector_v01 as collector
from two_player import v212_worker_ipc as ipc


class CollectorParsingTests(unittest.TestCase):
    def test_journal_query_filters_startup_records_and_keeps_worker_marker(self):
        unit = "caissa-v212-test.service"
        marker = {
            "__CURSOR": "cursor-1", "_BOOT_ID": "a" * 32,
            "__MONOTONIC_TIMESTAMP": "42", "_SYSTEMD_UNIT": unit,
            "_SYSTEMD_INVOCATION_ID": "b" * 32,
            "_SYSTEMD_CGROUP": "/user.slice/caissa-v212-test.service",
            "MESSAGE": collector.MARKER_PREFIX + "b" * 32,
        }
        records = [
            {"MESSAGE": "Started caissa", "_SYSTEMD_USER_UNIT": unit},
            marker,
        ]
        output = b"".join(json.dumps(record).encode() + b"\n" for record in records)
        with patch.object(collector, "_run", return_value=output) as run:
            self.assertEqual(collector._journal_markers(
                unit, invocation_id="b" * 32,
                worker_cgroup="/user.slice/caissa-v212-test.service"), [marker])
        self.assertIn("--output=json", run.call_args.args[0])
        self.assertIn("--lines=1025", run.call_args.args[0])

    def test_journal_query_fails_closed_on_missing_or_duplicate_marker(self):
        unit = "caissa-v212-test.service"
        marker = {"MESSAGE": collector.MARKER_PREFIX + "c" * 32}
        for records in ([], [marker, marker]):
            output = b"".join(json.dumps(record).encode() + b"\n" for record in records)
            with self.subTest(count=len(records)), \
                    patch.object(collector, "_run", return_value=output), \
                    self.assertRaises(collector.CollectorError):
                collector._journal_markers(
                    unit, invocation_id="c" * 32,
                    worker_cgroup="/user.slice/caissa-v212-test.service")

    def test_journal_query_rejects_marker_with_mismatched_trusted_metadata(self):
        unit = "caissa-v212-test.service"
        base = {
            "_SYSTEMD_USER_UNIT": unit,
            "_SYSTEMD_INVOCATION_ID": "d" * 32,
            "_SYSTEMD_CGROUP": "/user.slice/caissa-v212-test.service",
            "MESSAGE": collector.MARKER_PREFIX + "d" * 32,
        }
        for key, value in (("_SYSTEMD_USER_UNIT", "other.service"),
                           ("_SYSTEMD_INVOCATION_ID", "e" * 32),
                           ("_SYSTEMD_CGROUP", "/user.slice/other.service")):
            record = dict(base, **{key: value})
            output = json.dumps(record).encode() + b"\n"
            with self.subTest(field=key), patch.object(
                    collector, "_run", return_value=output), \
                    self.assertRaises(collector.CollectorError):
                collector._journal_markers(
                    unit, invocation_id="d" * 32,
                    worker_cgroup="/user.slice/caissa-v212-test.service")

    def test_runtime_limit_accepts_systemctl_timespan_format(self):
        props = {
            "EffectiveMemoryMax": str(collector.MEMORY_MAX),
            "EffectiveMemoryHigh": str(collector.MEMORY_HIGH),
            "MemorySwapMax": "0", "LimitFSIZE": str(collector.FILE_SIZE_LIMIT),
            "RuntimeMaxUSec": "8s", "Restart": "no", "OOMPolicy": "kill",
            "RemainAfterExit": "yes",
        }
        collector._verify_effective_properties(props)
        props["RuntimeMaxUSec"] = "8000000"
        with self.assertRaises(collector.CollectorError):
            collector._verify_effective_properties(props)

    def test_run_enforces_streaming_output_bound(self):
        with self.assertRaisesRegex(collector.CollectorError, "byte bound"):
            collector._run((sys.executable, "-B", "-c", "print('x' * 100000)"),
                           timeout=2, max_output=128)

    def test_run_kills_child_at_caller_deadline(self):
        deadline = time.monotonic() + 0.05
        with self.assertRaisesRegex(collector.CollectorError, "timed out"):
            collector._run((sys.executable, "-B", "-c", "import time; time.sleep(1)"),
                           timeout=2, deadline=deadline)

    def test_invalid_receipt_path_is_rejected_before_ipc_or_service(self):
        with tempfile.TemporaryDirectory() as temp:
            existing = Path(temp) / "already-there.json"
            existing.write_text("prior evidence", encoding="utf-8")
            with patch.object(collector.ipc, "create_workspace") as create:
                with self.assertRaises(collector.CollectorError):
                    collector.run_no_inference_smoke(receipt_path=existing)
            create.assert_not_called()

    def test_cleanup_failure_before_dispatch_reports_ipc_path(self):
        with tempfile.TemporaryDirectory() as temp:
            receipt_path = Path(temp) / "receipt.json"
            workspace = ipc.create_workspace({"schema": "test.v01"})
            with patch.object(collector, "_boot_id", return_value="a" * 32), \
                    patch.object(collector, "_proc_cgroup", return_value="/user.slice/app.slice"), \
                    patch.object(ipc, "create_workspace", return_value=workspace), \
                    patch.object(collector, "_check_deadline",
                                 side_effect=collector.CollectorError("deadline")), \
                    patch.object(ipc, "cleanup_workspace",
                                 side_effect=ipc.WorkerIPCError("cleanup")):
                with self.assertRaisesRegex(
                        collector.CollectorError,
                        f"predispatch_ipc_cleanup_failed=WorkerIPCError.*{workspace.directory}"):
                    collector.run_no_inference_smoke(receipt_path=receipt_path)

    def test_partial_workspace_creation_error_preserves_helper_path(self):
        leftover = "/tmp/caissa-v212-partial"
        with tempfile.TemporaryDirectory() as temp:
            with patch.object(collector, "_boot_id", return_value="a" * 32), \
                    patch.object(collector, "_proc_cgroup", return_value="/user.slice/app.slice"), \
                    patch.object(ipc, "create_workspace",
                                 side_effect=ipc.WorkerIPCError(
                                     f"workspace setup failed; cleanup incomplete at {leftover}")):
                with self.assertRaises(collector.CollectorError) as raised:
                    collector.run_no_inference_smoke(
                        receipt_path=Path(temp) / "receipt.json")
        self.assertIn(leftover, str(raised.exception))
        self.assertIn("IPC workspace creation did not complete", str(raised.exception))

    def test_workspace_path_state_distinguishes_absent_directory(self):
        workspace = ipc.create_workspace({"schema": "test.v01"})
        self.assertEqual(collector._workspace_path_state(workspace),
                         "original_directory_present_at_reconciliation_check")
        ipc.cleanup_workspace(workspace)
        self.assertEqual(collector._workspace_path_state(workspace),
                         "absent_at_reconciliation_check")

    def test_keyboard_interrupt_preserves_recovery_handles_after_dispatch(self):
        created = []
        real_create_workspace = ipc.create_workspace

        def create_workspace(request):
            workspace = real_create_workspace(request)
            created.append(workspace)
            return workspace

        with tempfile.TemporaryDirectory() as temp:
            receipt_path = Path(temp) / "receipt.json"
            with patch.object(collector, "_boot_id", return_value="a" * 32), \
                    patch.object(collector, "_proc_cgroup", return_value="/user.slice/app.slice"), \
                    patch.object(ipc, "create_workspace", side_effect=create_workspace), \
                    patch.object(collector, "_run", side_effect=KeyboardInterrupt):
                with self.assertRaises(KeyboardInterrupt) as raised:
                    collector.run_no_inference_smoke(receipt_path=receipt_path)
            detail = str(raised.exception)
            self.assertIn("receipt_not_attempted", detail)
            self.assertIn("unit=caissa-v212-smoke-", detail)
            self.assertIn(f"ipc_directory={created[0].directory}", detail)
            ipc.cleanup_workspace(created[0])


class CollectorOrchestrationTests(unittest.TestCase):
    """Exercise the collector lifecycle with every host boundary mocked."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.receipt_path = self.root / "receipt.json"
        self.ipc_parent = self.root / "ipc"
        self.ipc_parent.mkdir(mode=0o700)
        self.workspaces = []

    def tearDown(self):
        for workspace in self.workspaces:
            if workspace.directory.exists():
                try:
                    ipc.cleanup_workspace(workspace)
                except ipc.WorkerIPCError:
                    pass
        self.temp.cleanup()

    @contextmanager
    def _mock_host(self, *, response_status="ok", manager_result="success",
                   fail_start=False, fail_stop=False, fail_persist=False,
                   fail_after_publish=False, fail_cleanup=False,
                   fail_counter_at=None, fail_journal=False):
        unit_data = {"unit": None, "cgroup": None, "show_count": 0,
                     "counter_count": 0, "sequence": []}
        original_create = ipc.create_workspace
        original_cleanup = ipc.cleanup_workspace

        def create_workspace(request):
            workspace = original_create(request, parent=self.ipc_parent)
            self.workspaces.append(workspace)
            return workspace

        def run(argv, **kwargs):
            command = tuple(argv[:3]) if len(argv) >= 3 else tuple(argv)
            unit_data["sequence"].append(
                "systemctl" if command[:2] == ("systemctl", "--user")
                else Path(argv[0]).name)
            if argv[0] == "systemd-run":
                if fail_start:
                    raise collector.CollectorError("mock dispatch failed")
                request_arg = next(arg for arg in argv
                                   if arg.startswith("--property=StandardInput=file:"))
                response_arg = next(arg for arg in argv
                                    if arg.startswith("--property=StandardOutput=truncate:"))
                request_path = Path(request_arg.split("StandardInput=file:", 1)[1])
                response_path = Path(response_arg.split("StandardOutput=truncate:", 1)[1])
                request = json.loads(request_path.read_text(encoding="utf-8"))
                unit_data["pending_response"] = (response_path, json.dumps({
                    "schema": "caissa.synthetic.response.v01",
                    "nonce": request["nonce"], "status": response_status,
                }, separators=(",", ":")))
                return b""
            if command == ("systemctl", "--user", "stop"):
                if fail_stop:
                    raise collector.CollectorError("mock stop failed")
                return b""
            raise AssertionError(f"unexpected host command: {argv[0]}")

        def show(unit, **kwargs):
            unit_data["unit"] = unit
            unit_data["show_count"] += 1
            cgroup = "/user.slice/" + unit
            unit_data["cgroup"] = cgroup
            common = {
                "LoadState": "loaded", "InvocationID": "a" * 32,
                "ControlGroup": cgroup, "MainPID": "4242",
                "EffectiveMemoryMax": str(collector.MEMORY_MAX),
                "EffectiveMemoryHigh": str(collector.MEMORY_HIGH),
                "MemorySwapMax": "0", "LimitFSIZE": str(collector.FILE_SIZE_LIMIT),
                "RuntimeMaxUSec": "8s", "Restart": "no", "OOMPolicy": "kill",
                "RemainAfterExit": "yes",
            }
            if unit_data["show_count"] == 1:
                unit_data["sequence"].append("snapshot_active")
                return dict(common, ActiveState="active", SubState="running")
            if unit_data["show_count"] == 2:
                unit_data["sequence"].append("snapshot_exited")
                if "pending_response" in unit_data:
                    response_path, response_bytes = unit_data.pop("pending_response")
                    response_path.write_text(response_bytes, encoding="utf-8")
                return dict(common, ControlGroup="", ActiveState="inactive",
                            SubState="exited", Result=manager_result,
                            ExecMainStatus="0" if manager_result == "success" else "9")
            return {"LoadState": "not-found"}

        def proc_cgroup(pid=None):
            if pid is None:
                return "/user.slice/app.slice"
            return unit_data["cgroup"]

        def read_events(**kwargs):
            unit_data["counter_count"] += 1
            if fail_counter_at == unit_data["counter_count"]:
                raise collector.live.LiveEvidenceError("mock local counter failure")
            return {
                "schema": collector.assembler.COUNTER_SCHEMA,
                "source": "memory.events.local",
                "cgroup": unit_data["cgroup"], "boot_id": "b" * 32,
                "captured_monotonic_us": 13000 if unit_data["counter_count"] == 1 else 18000,
                "counters": {"low": 0, "high": 0, "max": 0, "oom": 0,
                             "oom_kill": 0, "oom_group_kill": 0},
            }

        def journal(unit, *, invocation_id, worker_cgroup, deadline):
            if fail_journal:
                raise collector.CollectorError("mock journal marker missing")
            return [{
                "__CURSOR": "mock-cursor", "_BOOT_ID": "b" * 32,
                "__MONOTONIC_TIMESTAMP": "16000", "_SYSTEMD_UNIT": unit,
                "_SYSTEMD_INVOCATION_ID": invocation_id,
                "_SYSTEMD_CGROUP": worker_cgroup,
                "MESSAGE": collector.MARKER_PREFIX + invocation_id,
            }]

        original_persist = collector.live.persist_receipt_once
        original_read_response = ipc.read_response

        def read_response(workspace):
            unit_data["sequence"].append("response_read")
            return original_read_response(workspace)

        def persist(destination, envelope):
            unit_data["sequence"].append("persist_attempt")
            if fail_persist:
                raise collector.live.LiveEvidenceError("mock receipt fsync failure")
            result = original_persist(destination, envelope)
            unit_data["sequence"].append("persist_complete")
            if fail_after_publish:
                raise collector.live.LiveEvidenceError(
                    "mock durability status lost after receipt publication")
            return result

        def cleanup(workspace):
            unit_data["sequence"].append("cleanup")
            if fail_cleanup:
                raise ipc.WorkerIPCError("mock cleanup substitution")
            return original_cleanup(workspace)

        with ExitStack() as stack:
            stack.enter_context(patch.object(collector, "_boot_id", return_value="b" * 32))
            stack.enter_context(patch.object(collector, "_proc_cgroup", side_effect=proc_cgroup))
            stack.enter_context(patch.object(collector, "_monotonic_us",
                                             side_effect=[10000, 12000, 13000, 18000, 20000]))
            stack.enter_context(patch.object(collector, "_run", side_effect=run))
            stack.enter_context(patch.object(collector, "_show", side_effect=show))
            stack.enter_context(patch.object(collector, "_cgroup_scalar",
                                             side_effect=[str(collector.MEMORY_MAX),
                                                          str(collector.MEMORY_HIGH), "0"]))
            stack.enter_context(patch.object(collector, "_journal_markers",
                                             side_effect=journal))
            stack.enter_context(patch.object(collector.live, "read_memory_events_local",
                                             side_effect=read_events))
            stack.enter_context(patch.object(collector.live, "persist_receipt_once",
                                             side_effect=persist))
            stack.enter_context(patch.object(ipc, "read_response",
                                             side_effect=read_response))
            stack.enter_context(patch.object(ipc, "create_workspace",
                                             side_effect=create_workspace))
            stack.enter_context(patch.object(ipc, "cleanup_workspace", side_effect=cleanup))
            stack.enter_context(patch.object(collector.time, "sleep", return_value=None))
            yield unit_data

    def test_success_persists_receipt_before_unit_and_ipc_cleanup(self):
        with self._mock_host() as host:
            result = collector.run_no_inference_smoke(receipt_path=self.receipt_path)
        self.assertTrue(result["receipt_persisted_before_cleanup"])
        envelope = json.loads(self.receipt_path.read_text(encoding="utf-8"))
        self.assertTrue(envelope["no_inference"])
        self.assertEqual(envelope["receipt"]["classification"], "normal_exit")
        self.assertLess(host["sequence"].index("persist_complete"),
                        host["sequence"].index("systemctl"))
        self.assertLess(host["sequence"].index("response_read"),
                        host["sequence"].index("persist_attempt"))
        self.assertLess(host["sequence"].index("snapshot_exited"),
                        host["sequence"].index("response_read"))
        self.assertLess(host["sequence"].index("systemctl"),
                        host["sequence"].index("cleanup"))

    def test_bad_response_retains_unit_workspace_and_no_receipt(self):
        with self._mock_host(response_status="invalid"):
            with self.assertRaisesRegex(collector.CollectorError,
                                        "receipt_not_attempted.*unit_retained_or_state_unknown"):
                collector.run_no_inference_smoke(receipt_path=self.receipt_path)
        self.assertFalse(self.receipt_path.exists())
        self.assertTrue(self.workspaces[0].directory.exists())

    def test_dispatch_failure_keeps_reconciliation_handles(self):
        with self._mock_host(fail_start=True) as host:
            with self.assertRaisesRegex(collector.CollectorError,
                                        "receipt_not_attempted.*unit_retained_or_state_unknown"):
                collector.run_no_inference_smoke(receipt_path=self.receipt_path)
        self.assertFalse(self.receipt_path.exists())
        self.assertTrue(self.workspaces[0].directory.exists())
        self.assertEqual(host["sequence"], ["systemd-run"])

    def test_non_success_manager_result_never_persists_or_stops(self):
        with self._mock_host(manager_result="timeout") as host:
            with self.assertRaisesRegex(collector.CollectorError,
                                        "did not exit successfully.*receipt_not_attempted"):
                collector.run_no_inference_smoke(receipt_path=self.receipt_path)
        self.assertFalse(self.receipt_path.exists())
        self.assertTrue(self.workspaces[0].directory.exists())
        self.assertNotIn("systemctl", host["sequence"])

    def test_persistence_failure_is_uncertain_and_prevents_cleanup(self):
        with self._mock_host(fail_persist=True) as host:
            with self.assertRaisesRegex(collector.CollectorError,
                                        "receipt_publication_or_durability_uncertain"):
                collector.run_no_inference_smoke(receipt_path=self.receipt_path)
        self.assertNotIn("systemctl", host["sequence"])
        self.assertTrue(self.workspaces[0].directory.exists())

    def test_post_publication_uncertainty_keeps_receipt_and_reconciliation_handles(self):
        with self._mock_host(fail_after_publish=True) as host:
            with self.assertRaisesRegex(collector.CollectorError,
                                        "receipt_publication_or_durability_uncertain"):
                collector.run_no_inference_smoke(receipt_path=self.receipt_path)
        self.assertTrue(self.receipt_path.exists())
        self.assertTrue(self.workspaces[0].directory.exists())
        self.assertNotIn("systemctl", host["sequence"])

    def test_stop_failure_keeps_durable_receipt_and_reconciliation_handles(self):
        with self._mock_host(fail_stop=True) as host:
            with self.assertRaisesRegex(collector.CollectorError,
                                        "receipt_persisted.*unit_retained_or_state_unknown"):
                collector.run_no_inference_smoke(receipt_path=self.receipt_path)
        self.assertTrue(self.receipt_path.exists())
        self.assertTrue(self.workspaces[0].directory.exists())
        self.assertNotIn("cleanup", host["sequence"])

    def test_cleanup_failure_preserves_receipt_and_reports_stopped_unit(self):
        with self._mock_host(fail_cleanup=True) as host:
            with self.assertRaisesRegex(collector.CollectorError,
                                        "receipt_persisted.*unit_stopped"):
                collector.run_no_inference_smoke(receipt_path=self.receipt_path)
        self.assertTrue(self.receipt_path.exists())
        self.assertEqual(host["sequence"].count("systemctl"), 1)
        self.assertEqual(host["sequence"].count("cleanup"), 1)
        self.assertTrue(self.workspaces[0].directory.exists())

    def test_missing_local_counter_or_journal_marker_blocks_receipt(self):
        for options in ({"fail_counter_at": 2}, {"fail_journal": True}):
            with self.subTest(options=options), self._mock_host(**options) as host:
                with self.assertRaises(collector.CollectorError):
                    collector.run_no_inference_smoke(receipt_path=self.receipt_path)
                self.assertFalse(self.receipt_path.exists())
                self.assertNotIn("systemctl", host["sequence"])
                self.assertNotIn("cleanup", host["sequence"])
                self.assertTrue(self.workspaces[-1].directory.exists())


if __name__ == "__main__":
    unittest.main()

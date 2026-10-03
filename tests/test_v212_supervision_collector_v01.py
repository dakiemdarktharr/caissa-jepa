import json
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


if __name__ == "__main__":
    unittest.main()

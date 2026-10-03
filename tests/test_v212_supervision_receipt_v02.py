import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from two_player import v212_supervision_receipt_v02 as sr


UNIT = "caissa-v212-test.service"
INVOCATION = "0123456789abcdef0123456789abcdef"
CGROUP = f"/app.slice/{UNIT}"
BOOT = "abcdef0123456789abcdef0123456789"
START = 10_000
ACTIVE = 12_000
BEFORE = 13_000
AFTER = 18_000
FINISHED = 20_000


def worker_snapshot(*, unit=UNIT, invocation=INVOCATION, cgroup=CGROUP,
                    boot=BOOT, captured=ACTIVE, active="active", sub="running"):
    return {"schema": sr.SYSTEMD_SNAPSHOT_SCHEMA,
            "unit": unit, "invocation_id": invocation, "control_group": cgroup,
            "boot_id": boot, "captured_monotonic_us": captured,
            "active_state": active, "sub_state": sub}


def manager_snapshot(*, unit=UNIT, invocation=INVOCATION, cgroup=None,
                     boot=BOOT, captured=FINISHED, active="inactive",
                     sub="failed", result="oom-kill", status=9):
    return {"schema": sr.SYSTEMD_SNAPSHOT_SCHEMA,
            "unit": unit, "invocation_id": invocation, "control_group": cgroup,
            "boot_id": boot, "captured_monotonic_us": captured,
            "active_state": active, "sub_state": sub,
            "result": result, "main_status": status}


def marker(cursor="unit-cursor", invocation=INVOCATION, unit=UNIT,
           boot=BOOT, timestamp=14_000):
    return {"__CURSOR": cursor, "_BOOT_ID": boot,
            "__MONOTONIC_TIMESTAMP": str(timestamp), "_SYSTEMD_UNIT": unit,
            "_SYSTEMD_INVOCATION_ID": invocation, "MESSAGE": "worker-ready"}


def kernel_oom(cursor="kernel-cursor", cgroup=CGROUP, boot=BOOT,
               timestamp=16_000):
    return {"__CURSOR": cursor, "_BOOT_ID": boot,
            "__MONOTONIC_TIMESTAMP": str(timestamp), "_TRANSPORT": "kernel",
            "MESSAGE": ("oom-kill:constraint=CONSTRAINT_MEMCG,nodemask=(null),"
                        f"oom_memcg={cgroup},task_memcg={cgroup},task=python,pid=42")}


def counters(*, captured, cgroup=CGROUP, boot=BOOT, schema=sr.COUNTER_SCHEMA,
             source="memory.events.local", values=None):
    if values is None:
        values = {"low": 0, "high": 0, "max": 0, "oom": 0,
                  "oom_kill": 0, "oom_group_kill": 0}
    return {"schema": schema, "source": source, "cgroup": cgroup,
            "boot_id": boot, "captured_monotonic_us": captured,
            "counters": values}


def receipt(records, *, worker=None, manager=None, before=None, after=None,
            start=START):
    return sr.assemble_receipt(
        requested_unit=UNIT,
        request_boot_id=BOOT,
        request_started_monotonic_us=start,
        worker_snapshot=worker or worker_snapshot(),
        manager_snapshot=manager or manager_snapshot(),
        journal_records=records,
        events_before=before,
        events_after=after,
    )


class ReceiptAssemblyTests(unittest.TestCase):
    def test_kernel_event_is_bound_to_manager_unit_invocation_cgroup_and_time(self):
        out = receipt([marker(), kernel_oom()])
        self.assertEqual(out["classification"],
                         "worker_cgroup_oom_attributed_by_kernel_journal")
        self.assertEqual(out["binding"]["unit"], UNIT)
        self.assertEqual(out["binding"]["invocation_id"], INVOCATION)
        self.assertEqual(out["binding"]["worker_cgroup"], CGROUP)
        self.assertEqual(out["kernel_oom"]["matching_worker_cgroup_events"][0]["constraint"],
                         "CONSTRAINT_MEMCG")

    def test_receipt_keeps_normalized_event_and_message_digest_not_raw_message(self):
        out = receipt([marker(), kernel_oom()])
        encoded = json.dumps(out)
        proof = out["kernel_oom"]["matching_worker_cgroup_events"][0]
        self.assertEqual(len(proof["message_sha256"]), 64)
        self.assertEqual(out["assembler"]["version"], "v02")
        self.assertEqual(len(out["assembler"]["source_sha256"]), 64)
        self.assertNotIn("oom-kill:", encoded)
        self.assertNotIn("task=python", encoded)
        self.assertTrue(out["kernel_oom"]["cursor_retrieval_required_for_parser_reverification"])
        self.assertEqual(proof["oom_memcg"], CGROUP)
        self.assertEqual(proof["task_memcg"], CGROUP)

    def test_user_unit_field_is_used_when_system_unit_is_user_manager(self):
        record = marker()
        record["_SYSTEMD_UNIT"] = "user@1000.service"
        record["_SYSTEMD_USER_UNIT"] = UNIT
        self.assertEqual(receipt([record, kernel_oom()])["classification"],
                         "worker_cgroup_oom_attributed_by_kernel_journal")

    def test_other_memcg_or_task_memcg_is_not_attributed(self):
        wrong_memcg = kernel_oom(cursor="other-memcg")
        wrong_memcg["MESSAGE"] = wrong_memcg["MESSAGE"].replace(
            f"oom_memcg={CGROUP}", "oom_memcg=/other")
        wrong_task = kernel_oom(cursor="other-task")
        wrong_task["MESSAGE"] = wrong_task["MESSAGE"].replace(
            f"task_memcg={CGROUP}", "task_memcg=/other")
        self.assertEqual(receipt([marker(), wrong_memcg, wrong_task])["classification"],
                         "manager_oom_unattributed")

    def test_kernel_record_must_have_kernel_transport_and_matching_boot_window(self):
        forged = kernel_oom()
        forged["_TRANSPORT"] = "journal"
        old = kernel_oom(cursor="old", timestamp=START - 1)
        wrong_boot = kernel_oom(cursor="boot", boot="0" * 32)
        out = receipt([marker(), forged, old, wrong_boot])
        self.assertEqual(out["classification"], "manager_oom_unattributed")

    def test_pre_active_kernel_event_or_unit_marker_cannot_bind_to_invocation(self):
        prior = kernel_oom(timestamp=ACTIVE - 1)
        out = receipt([marker(), prior])
        self.assertEqual(out["classification"], "manager_oom_unattributed")
        self.assertEqual(out["kernel_oom"]["matching_worker_cgroup_events"], [])
        with self.assertRaisesRegex(sr.ReceiptError, "outside the invocation window"):
            receipt([marker(timestamp=ACTIVE - 1), kernel_oom()])
        same_microsecond = kernel_oom(cursor="same-time", timestamp=ACTIVE)
        out = receipt([marker(), same_microsecond])
        self.assertEqual(out["classification"], "manager_oom_unattributed")

    def test_historical_oom_is_not_attached_to_normal_current_invocation(self):
        old = kernel_oom(timestamp=START - 1)
        out = receipt([marker(), old], manager=manager_snapshot(
            result="success", status=0, sub="exited"))
        self.assertEqual(out["classification"], "normal_exit")
        self.assertEqual(out["kernel_oom"]["matching_worker_cgroup_events"], [])

    def test_non_oom_result_conflicting_with_same_invocation_event_fails_closed(self):
        out = receipt([marker(), kernel_oom()], manager=manager_snapshot(
            result="success", status=0, sub="exited"))
        self.assertEqual(out["classification"],
                         "conflict_oom_evidence_with_non_oom_manager_result")

    def test_manager_oom_without_kernel_or_counter_evidence_is_unattributed(self):
        self.assertEqual(receipt([marker()])["classification"],
                         "manager_oom_unattributed")

    def test_counter_delta_attributes_only_bound_worker_local_kill(self):
        before = counters(captured=BEFORE)
        after = counters(captured=AFTER, values={
            "low": 0, "high": 0, "max": 1, "oom": 1,
            "oom_kill": 1, "oom_group_kill": 0})
        out = receipt([marker()], before=before, after=after)
        self.assertEqual(out["classification"],
                         "worker_cgroup_oom_attributed_by_local_counters")
        self.assertTrue(out["memory_events_local"]["positive_kill_counter"])

    def test_max_and_oom_without_kill_are_not_kill_attribution(self):
        before = counters(captured=BEFORE)
        after = counters(captured=AFTER, values={
            "low": 0, "high": 0, "max": 3, "oom": 1,
            "oom_kill": 0, "oom_group_kill": 0})
        out = receipt([marker()], manager=manager_snapshot(
            result="success", status=0, sub="exited"), before=before, after=after)
        self.assertEqual(out["classification"],
                         "worker_cgroup_oom_event_without_kill")
        self.assertFalse(out["memory_events_local"]["positive_kill_counter"])
        self.assertEqual(out["memory_events_local"]["delta"]["max"], 3)

    def test_worker_snapshot_binds_exact_unit_invocation_cgroup_and_boot(self):
        cases = [
            (worker_snapshot(unit="other.service"), "unit does not match"),
            (worker_snapshot(invocation="f" * 32), "invocation ID does not match"),
            (worker_snapshot(boot="0" * 32), "boot ID does not match"),
            (worker_snapshot(captured=START - 1), "predates the request"),
            (worker_snapshot(active="inactive", sub="failed"), "not captured while service was active"),
        ]
        for snapshot, message in cases:
            with self.subTest(message=message), self.assertRaisesRegex(sr.ReceiptError, message):
                receipt([marker(), kernel_oom()], worker=snapshot)
        stale_schema = worker_snapshot()
        stale_schema["schema"] = "systemd-show-unit.v0"
        with self.assertRaisesRegex(sr.ReceiptError, "snapshot schema does not match"):
            receipt([marker(), kernel_oom()], worker=stale_schema)

    def test_manager_snapshot_must_match_invocation_and_be_post_exit(self):
        cases = [
            (manager_snapshot(unit="other.service"), "unit does not match"),
            (manager_snapshot(invocation="f" * 32), "invocation ID does not match"),
            (manager_snapshot(boot="0" * 32), "boot ID does not match"),
            (manager_snapshot(cgroup="/other/worker.service"), "ControlGroup does not belong to unit"),
            (manager_snapshot(captured=ACTIVE), "does not follow active snapshot"),
            (manager_snapshot(active="active", sub="running"), "not captured after exit"),
            (manager_snapshot(result="",), "manager result is missing"),
        ]
        for snapshot, message in cases:
            with self.subTest(message=message), self.assertRaisesRegex(sr.ReceiptError, message):
                receipt([marker()], manager=snapshot)

    def test_manager_snapshot_schema_and_request_boot_are_bound(self):
        bad_manager = manager_snapshot()
        bad_manager["schema"] = "systemd-show-unit.v0"
        with self.assertRaisesRegex(sr.ReceiptError, "snapshot schema does not match"):
            receipt([marker()], manager=bad_manager)
        with self.assertRaisesRegex(sr.ReceiptError, "boot ID does not match"):
            sr.assemble_receipt(
                requested_unit=UNIT,
                request_boot_id="0" * 32,
                request_started_monotonic_us=START,
                worker_snapshot=worker_snapshot(),
                manager_snapshot=manager_snapshot(),
                journal_records=[marker(), kernel_oom()],
            )

    def test_counter_snapshots_reject_wrong_cgroup_boot_schema_source_and_window(self):
        valid_before = counters(captured=BEFORE)
        cases = [
            (counters(captured=BEFORE, cgroup="/foreign/worker.service"), "cgroup does not match"),
            (counters(captured=BEFORE, boot="0" * 32), "boot ID does not match"),
            (counters(captured=BEFORE, schema="memory.events.v1"), "schema does not match"),
            (counters(captured=BEFORE, source="memory.events"), "not memory.events.local"),
            (counters(captured=START - 1), "outside invocation window"),
            (counters(captured=FINISHED + 1), "outside invocation window"),
        ]
        for bad_after, message in cases:
            with self.subTest(message=message), self.assertRaisesRegex(sr.ReceiptError, message):
                receipt([marker()], before=valid_before, after=bad_after)

    def test_counter_pair_cannot_precede_the_active_worker_snapshot(self):
        with self.assertRaisesRegex(sr.ReceiptError, "outside invocation window"):
            receipt([marker()], before=counters(captured=START + 100),
                    after=counters(captured=ACTIVE - 1))
        with self.assertRaisesRegex(sr.ReceiptError, "outside invocation window"):
            receipt([marker()], before=counters(captured=ACTIVE),
                    after=counters(captured=AFTER))

    def test_counter_snapshots_require_complete_pair_schema_and_monotonic_order(self):
        before = counters(captured=BEFORE)
        with self.assertRaisesRegex(sr.ReceiptError, "supplied together"):
            receipt([marker()], before=before)
        partial = counters(captured=AFTER, values={"oom": 0})
        with self.assertRaisesRegex(sr.ReceiptError, "incomplete"):
            receipt([marker()], before=before, after=partial)
        with self.assertRaisesRegex(sr.ReceiptError, "increasing time order"):
            receipt([marker()], before=counters(captured=AFTER),
                    after=counters(captured=BEFORE))

    def test_cgroup_unit_path_binding_and_journal_batch_type_are_enforced(self):
        with self.assertRaisesRegex(sr.ReceiptError, "ControlGroup does not belong to unit"):
            receipt([marker(), kernel_oom()],
                    worker=worker_snapshot(cgroup="/app.slice/other.service"))
        with self.assertRaisesRegex(sr.ReceiptError, "journal record batch must be a sequence"):
            sr.assemble_receipt(
                requested_unit=UNIT,
                request_boot_id=BOOT,
                request_started_monotonic_us=START,
                worker_snapshot=worker_snapshot(),
                manager_snapshot=manager_snapshot(),
                journal_records=None,
            )
        for malformed in ([], {}):
            bad_marker = marker()
            bad_marker["_SYSTEMD_USER_UNIT"] = malformed
            with self.subTest(malformed=type(malformed).__name__), self.assertRaisesRegex(
                    sr.ReceiptError, "unit journal fields are malformed"):
                receipt([bad_marker, kernel_oom()])

    def test_journal_input_size_is_bounded(self):
        oversized = marker()
        oversized["MESSAGE"] = "x" * (sr.MAX_JOURNAL_RECORD_BYTES + 1)
        with self.assertRaisesRegex(sr.ReceiptError, "record exceeds the input size bound"):
            receipt([oversized, kernel_oom()])

    def test_counter_regression_and_bool_counts_are_rejected(self):
        before = counters(captured=BEFORE, values={
            "oom": 1, "oom_kill": 1, "oom_group_kill": 0})
        after = counters(captured=AFTER, values={
            "oom": 0, "oom_kill": 1, "oom_group_kill": 0})
        with self.assertRaisesRegex(sr.ReceiptError, "moved backwards"):
            receipt([marker()], before=before, after=after)
        bad = counters(captured=AFTER, values={
            "oom": 0, "oom_kill": True, "oom_group_kill": 0})
        with self.assertRaisesRegex(sr.ReceiptError, "malformed"):
            receipt([marker()], before=counters(captured=BEFORE), after=bad)

    def test_missing_marker_conflict_and_duplicate_cursor_are_rejected(self):
        with self.assertRaisesRegex(sr.ReceiptError, "no journal record"):
            receipt([kernel_oom()])
        wrong = marker(invocation="f" * 32)
        with self.assertRaisesRegex(sr.ReceiptError, "conflicting invocation"):
            receipt([wrong, kernel_oom()])
        first, second = marker(), marker()
        second["MESSAGE"] = "conflict"
        with self.assertRaisesRegex(sr.ReceiptError, "conflicting"):
            receipt([first, second, kernel_oom()])

    def test_malformed_time_cursor_boot_and_reversed_boot_format_fail_closed(self):
        bad_time = kernel_oom()
        bad_time["__MONOTONIC_TIMESTAMP"] = "not-a-time"
        with self.assertRaisesRegex(sr.ReceiptError, "timestamp is malformed"):
            receipt([marker(), bad_time])
        bad_marker = marker()
        bad_marker.pop("__CURSOR")
        with self.assertRaisesRegex(sr.ReceiptError, "cursor"):
            receipt([bad_marker, kernel_oom()])
        with self.assertRaisesRegex(sr.ReceiptError, "malformed"):
            sr.normalize_boot_id("not-a-boot-id")
        self.assertEqual(sr.normalize_boot_id("abcdef01-2345-6789-abcd-ef0123456789"),
                         "abcdef0123456789abcdef0123456789")


class AtomicWriteTests(unittest.TestCase):
    def test_writes_private_json_atomically(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "receipt.json"
            sr.atomic_write_json(path, {"schema": sr.SCHEMA, "ok": True})
            self.assertEqual(json.loads(path.read_text()), {"schema": sr.SCHEMA, "ok": True})
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            self.assertEqual(list(Path(directory).glob("*.tmp")), [])

    def test_replace_and_directory_fsync_failures_are_visible(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "receipt.json"
            path.write_text('{"old":true}\n')
            with mock.patch.object(sr.os, "replace", side_effect=OSError("injected")):
                with self.assertRaisesRegex(sr.ReceiptError, "durable receipt write failed"):
                    sr.atomic_write_json(path, {"new": True})
            self.assertEqual(path.read_text(), '{"old":true}\n')
            with mock.patch.object(sr.os, "fsync", side_effect=[None, OSError("dir fsync")]):
                with self.assertRaisesRegex(sr.ReceiptError, "do not clean up evidence"):
                    sr.atomic_write_json(path, {"new": True})
            self.assertEqual(json.loads(path.read_text()), {"new": True})

    def test_assembler_source_hash_failure_prevents_receipt_creation(self):
        with mock.patch.object(sr.Path, "read_bytes", side_effect=OSError("source unavailable")):
            with self.assertRaisesRegex(sr.ReceiptError, "source digest unavailable"):
                receipt([marker(), kernel_oom()])

    def test_nonfinite_and_oversize_receipts_do_not_replace_existing_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "receipt.json"
            path.write_text('{"old":true}\n')
            with self.assertRaises(sr.ReceiptError):
                sr.atomic_write_json(path, {"bad": float("nan")})
            with self.assertRaisesRegex(sr.ReceiptError, "size bound"):
                sr.atomic_write_json(path, {"payload": "x" * sr.MAX_RECEIPT_BYTES})
            self.assertEqual(path.read_text(), '{"old":true}\n')


if __name__ == "__main__":
    unittest.main(verbosity=2)

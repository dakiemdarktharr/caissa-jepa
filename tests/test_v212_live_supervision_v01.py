import os
import tempfile
import unittest
from pathlib import Path

from two_player import v212_live_supervision_v01 as live
from two_player import v212_supervision_receipt_v02 as assembler

UNIT = "caissa-v212-live-test.service"
INVOCATION = "0123456789abcdef0123456789abcdef"
BOOT = "abcdef0123456789abcdef0123456789"
CGROUP = f"/app.slice/{UNIT}"


def properties(**overrides):
    base = {"InvocationID": INVOCATION, "ControlGroup": CGROUP,
            "ActiveState": "active", "SubState": "running",
            "Result": "success", "ExecMainStatus": "0"}
    base.update(overrides)
    return base


class SystemdSnapshotTests(unittest.TestCase):
    def test_parse_show_rejects_duplicate_and_malformed_properties(self):
        self.assertEqual(live.parse_systemd_show("InvocationID=x\nActiveState=active\n"),
                         {"InvocationID": "x", "ActiveState": "active"})
        with self.assertRaises(live.LiveEvidenceError):
            live.parse_systemd_show("InvocationID=x\nInvocationID=y\n")
        with self.assertRaises(live.LiveEvidenceError):
            live.parse_systemd_show("not-a-property\n")

    def test_active_snapshot_binds_exact_service(self):
        out = live.snapshot_from_properties(unit=UNIT, properties=properties(),
                                            boot_id=BOOT, captured_monotonic_us=9,
                                            active=True)
        self.assertEqual(out["control_group"], CGROUP)
        self.assertEqual(out["invocation_id"], INVOCATION)
        self.assertEqual(out["schema"], "systemd-show-invocation.v01")

    def test_active_snapshot_rejects_wrong_unit_or_state(self):
        with self.assertRaises(live.LiveEvidenceError):
            live.snapshot_from_properties(unit=UNIT, properties=properties(
                ControlGroup="/app.slice/other.service"), boot_id=BOOT,
                captured_monotonic_us=9, active=True)
        with self.assertRaises(live.LiveEvidenceError):
            live.snapshot_from_properties(unit=UNIT, properties=properties(
                ActiveState="inactive", SubState="dead"), boot_id=BOOT,
                captured_monotonic_us=9, active=True)

    def test_exit_snapshot_requires_finished_unit_and_exit_properties(self):
        out = live.snapshot_from_properties(unit=UNIT, properties=properties(
            ControlGroup="", ActiveState="inactive", SubState="exited"),
            boot_id=BOOT, captured_monotonic_us=10, active=False)
        self.assertEqual((out["result"], out["main_status"]), ("success", 0))
        retained = live.snapshot_from_properties(unit=UNIT, properties=properties(
            ControlGroup="", SubState="exited"), boot_id=BOOT, captured_monotonic_us=40,
            active=False)
        self.assertEqual(retained["active_state"], "inactive")
        self.assertEqual(retained["manager_active_state"], "active")
        active = live.snapshot_from_properties(
            unit=UNIT, properties=properties(), boot_id=BOOT,
            captured_monotonic_us=20, active=True)
        receipt = assembler.assemble_receipt(
            requested_unit=UNIT, request_boot_id=BOOT,
            request_started_monotonic_us=10, worker_snapshot=active,
            manager_snapshot=retained,
            journal_records=[{
                "__CURSOR": "retained-success-cursor", "_BOOT_ID": BOOT,
                "__MONOTONIC_TIMESTAMP": "30", "_SYSTEMD_UNIT": UNIT,
                "_SYSTEMD_INVOCATION_ID": INVOCATION,
                "MESSAGE": "synthetic marker",
            }])
        self.assertEqual(receipt["manager"]["reported_active_state"], "active")
        self.assertEqual(receipt["classification"], "normal_exit")
        failed = live.snapshot_from_properties(unit=UNIT, properties=properties(
            ControlGroup="", ActiveState="failed", SubState="failed",
            Result="oom-kill", ExecMainStatus="9"), boot_id=BOOT,
            captured_monotonic_us=10, active=False)
        self.assertEqual(failed["active_state"], "inactive")
        self.assertEqual(failed["manager_active_state"], "failed")
        self.assertEqual(failed["result"], "oom-kill")
        with self.assertRaises(live.LiveEvidenceError):
            live.snapshot_from_properties(unit=UNIT, properties=properties(
                ActiveState="activating", SubState="start"), boot_id=BOOT,
                captured_monotonic_us=10, active=False)

    def test_exit_snapshot_rejects_missing_post_exit_state_properties(self):
        for field in ("ActiveState", "SubState"):
            with self.subTest(field=field):
                incomplete = properties(ControlGroup="")
                del incomplete[field]
                with self.assertRaisesRegex(
                        live.LiveEvidenceError,
                        f"systemd property {field} is missing"):
                    live.snapshot_from_properties(
                        unit=UNIT, properties=incomplete, boot_id=BOOT,
                        captured_monotonic_us=10, active=False)


class CgroupSnapshotTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / "cgroup"
        self.group = self.root / CGROUP.lstrip("/")
        self.group.mkdir(parents=True)
        (self.group / "memory.events.local").write_text(
            "low 0\nhigh 1\nmax 2\noom 0\noom_kill 0\noom_group_kill 0\n",
            encoding="ascii")

    def tearDown(self):
        self.temp.cleanup()

    def test_reads_typed_local_counters(self):
        out = live.read_memory_events_local(cgroup_root=self.root,
                                            control_group=CGROUP, boot_id=BOOT,
                                            captured_monotonic_us=14)
        self.assertEqual(out["source"], "memory.events.local")
        self.assertEqual(out["counters"]["max"], 2)
        self.assertEqual(out["counters"]["oom_kill"], 0)

    def test_rejects_missing_counter_and_path_escape(self):
        path = self.group / "memory.events.local"
        path.write_text("max 0\noom 0\noom_kill 0\n", encoding="ascii")
        with self.assertRaises(live.LiveEvidenceError):
            live.read_memory_events_local(cgroup_root=self.root,
                                          control_group=CGROUP, boot_id=BOOT,
                                          captured_monotonic_us=14)
        with self.assertRaises(live.LiveEvidenceError):
            live.read_memory_events_local(cgroup_root=self.root,
                                          control_group="/../outside", boot_id=BOOT,
                                          captured_monotonic_us=14)

    def test_rejects_symlinked_counter_file(self):
        path = self.group / "memory.events.local"
        content = path.read_text(encoding="ascii")
        path.unlink()
        target = self.group / "elsewhere"
        target.write_text(content, encoding="ascii")
        path.symlink_to(target)
        with self.assertRaises(live.LiveEvidenceError):
            live.read_memory_events_local(cgroup_root=self.root,
                                          control_group=CGROUP, boot_id=BOOT,
                                          captured_monotonic_us=14)

    def test_rejects_fifo_counter_substitution_without_blocking(self):
        path = self.group / "memory.events.local"
        path.unlink()
        os.mkfifo(path)
        with self.assertRaises(live.LiveEvidenceError):
            live.read_memory_events_local(cgroup_root=self.root,
                                          control_group=CGROUP, boot_id=BOOT,
                                          captured_monotonic_us=14)

    def test_rejects_malformed_duplicate_non_ascii_and_oversize_counters(self):
        valid = b"low 0\nhigh 1\nmax 2\noom 0\noom_kill 0\noom_group_kill 0\n"
        invalid = {
            "malformed row": valid + b"pressure\n",
            "extra field": valid + b"max 3 extra\n",
            "duplicate name": valid + b"oom_kill 1\n",
            "negative count": valid.replace(b"max 2", b"max -2"),
            "overflow": valid.replace(b"max 2", b"max 18446744073709551616"),
            "non-ascii": valid + b"high \xff\n",
            "oversize": b" " * (live.MAX_COUNTER_FILE_BYTES + 1),
        }
        path = self.group / "memory.events.local"
        for label, data in invalid.items():
            with self.subTest(case=label):
                path.write_bytes(data)
                with self.assertRaises(live.LiveEvidenceError):
                    live.read_memory_events_local(
                        cgroup_root=self.root, control_group=CGROUP,
                        boot_id=BOOT, captured_monotonic_us=14)


class ReceiptPersistenceTests(unittest.TestCase):
    def test_persists_once_atomically_and_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as temp:
            parent = Path(temp) / "private"
            parent.mkdir(mode=0o700)
            destination = parent / "receipt.json"
            live.persist_receipt_once(destination, {"schema": "test", "ok": True})
            self.assertIn('"ok":true', destination.read_text(encoding="utf-8"))
            self.assertFalse(destination.with_name("receipt.json.claim").exists())
            with self.assertRaises(live.LiveEvidenceError):
                live.persist_receipt_once(destination, {"schema": "changed"})
            self.assertIn('"ok":true', destination.read_text(encoding="utf-8"))
            self.assertFalse(destination.with_name("receipt.json.claim").exists())

    def test_rejects_shared_directory_before_claim(self):
        with tempfile.TemporaryDirectory() as temp:
            parent = Path(temp) / "shared"
            parent.mkdir(mode=0o755)
            with self.assertRaises(live.LiveEvidenceError):
                live.persist_receipt_once(parent / "receipt.json", {"ok": True})
            self.assertFalse((parent / "receipt.json.claim").exists())

    def test_rejects_writable_ancestor_even_when_leaf_is_private(self):
        with tempfile.TemporaryDirectory() as temp:
            ancestor = Path(temp) / "writable"
            ancestor.mkdir(mode=0o700)
            ancestor.chmod(0o777)
            parent = ancestor / "private"
            parent.mkdir(mode=0o700)
            with self.assertRaises(live.LiveEvidenceError):
                live.persist_receipt_once(parent / "receipt.json", {"ok": True})
            self.assertFalse((parent / "receipt.json.claim").exists())


if __name__ == "__main__":
    unittest.main()

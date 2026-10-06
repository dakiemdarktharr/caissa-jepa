import unittest

from two_player import v212_supervision_receipt_v02 as v02
from two_player import v212_supervision_receipt_v03 as v03
from tests.test_v212_supervision_receipt_v02 import (
    AFTER, BEFORE, UNIT, BOOT, START, counters, marker, receipt,
    manager_snapshot, worker_snapshot,
)


class ReceiptV03CounterPairTests(unittest.TestCase):
    def test_v03_rejects_both_counter_snapshots_omitted(self):
        with self.assertRaisesRegex(v03.ReceiptError,
                                    "v03 requires both counter snapshots"):
            v03.assemble_receipt(
                requested_unit=UNIT,
                request_boot_id=BOOT,
                request_started_monotonic_us=START,
                worker_snapshot=worker_snapshot(),
                manager_snapshot=manager_snapshot(),
                journal_records=[marker()],
            )

    def test_v03_rejects_either_one_sided_counter_snapshot(self):
        # Use valid snapshots from the established fixture contract; the
        # missing-pair check must happen before delegated evidence parsing.
        base = {
            "requested_unit": UNIT,
            "request_boot_id": BOOT,
            "request_started_monotonic_us": START,
            "worker_snapshot": {},
            "manager_snapshot": {},
            "journal_records": [],
        }
        for kwargs in (
            {"events_before": counters(captured=BEFORE)},
            {"events_after": counters(captured=AFTER)},
        ):
            with self.subTest(kwargs=tuple(kwargs)), self.assertRaisesRegex(
                    v03.ReceiptError, "v03 requires both counter snapshots"):
                v03.assemble_receipt(**base, **kwargs)

    def test_v03_accepts_pair_and_identifies_both_assembler_sources(self):
        before = counters(captured=BEFORE)
        after = counters(captured=AFTER)
        # Reuse v02's canonical fixture inputs via the test module helpers.
        out = v03.assemble_receipt(
            requested_unit=UNIT,
            request_boot_id=BOOT,
            request_started_monotonic_us=START,
            worker_snapshot=worker_snapshot(),
            manager_snapshot=manager_snapshot(),
            journal_records=[marker()],
            events_before=before,
            events_after=after,
        )
        self.assertEqual(out["schema"], v03.SCHEMA)
        self.assertEqual(out["assembler"]["version"], "v03")
        self.assertEqual(len(out["assembler"]["source_sha256"]), 64)
        self.assertEqual(out["assembler"]["delegated_assembler"]["version"], "v02")
        self.assertEqual(len(out["assembler"]["delegated_assembler"]["source_sha256"]), 64)
        self.assertEqual(out["memory_events_local"]["before"]["captured_monotonic_us"], BEFORE)
        self.assertEqual(out["memory_events_local"]["after"]["captured_monotonic_us"], AFTER)

    def test_v03_rejects_counter_rollback_and_malformed_values(self):
        before_values = {"low": 0, "high": 0, "max": 0, "oom": 1,
                         "oom_kill": 1, "oom_group_kill": 0}
        cases = [
            ({"low": 0, "high": 0, "max": 0, "oom": 0,
              "oom_kill": 1, "oom_group_kill": 0}, "moved backwards"),
            ({"low": 0, "high": 0, "max": 0, "oom": 0,
              "oom_kill": True, "oom_group_kill": 0}, "malformed"),
            ({"low": 0, "high": 0, "max": 0, "oom": -1,
              "oom_kill": 0, "oom_group_kill": 0}, "malformed"),
            ({"low": 0, "high": 0, "max": 0, "oom": 0.5,
              "oom_kill": 0, "oom_group_kill": 0}, "malformed"),
            ({"low": 0, "high": 0, "max": 0, "oom": 0,
              "oom_kill": 0}, "incomplete"),
        ]
        for after_values, message in cases:
            with self.subTest(message=message, values=after_values):
                with self.assertRaisesRegex(v03.ReceiptError, message):
                    v03.assemble_receipt(
                        requested_unit=UNIT,
                        request_boot_id=BOOT,
                        request_started_monotonic_us=START,
                        worker_snapshot=worker_snapshot(),
                        manager_snapshot=manager_snapshot(),
                        journal_records=[marker()],
                        events_before=counters(captured=BEFORE,
                                               values=before_values),
                        events_after=counters(captured=AFTER,
                                              values=after_values),
                    )

    def test_v02_keeps_legacy_behavior_when_both_counters_are_omitted(self):
        legacy = receipt([marker()])
        self.assertEqual(legacy["schema"], v02.SCHEMA)
        self.assertIsNone(legacy["memory_events_local"]["before"])
        self.assertIsNone(legacy["memory_events_local"]["after"])


if __name__ == "__main__":
    unittest.main()

import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from two_player.v212_pilot import (
    RandomInferenceModel,
    VARIANTS,
    build_root_schedule,
    run_root_arm,
)
from two_player.v212_pilot_v03 import (
    ReceiptPublicationUncertain,
    append_progress_record,
    create_progress_journal,
    run_root_arm_v03,
    write_new_receipt_atomic,
)
from tools.v212_random_weight_compute_pilot_v03 import (
    _verify_v03_receipt,
    main as run_v03_runner,
)
from two_player.v212_pilot_v02 import build_root_schedule_v02


class V212PilotV03Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = build_root_schedule()[0]
        cls.game = VARIANTS[0]

    def test_rss_crossing_at_entry_returns_a_zero_work_row(self):
        samples = iter((151,))
        row = run_root_arm_v03(
            self.game, self.root, RandomInferenceModel("multi-step-jepa"),
            rss_cap_bytes=150, rss_sampler=lambda: next(samples),
        )
        self.assertEqual(row["stop_reason"], "rss_cap")
        self.assertEqual(row["node_visits"], 0)
        self.assertEqual(row["encoder_calls"], 0)
        self.assertEqual(row["completed_depth"], 0)

    def test_known_entry_crossing_is_returned_even_if_next_sample_would_fail(self):
        calls = []

        def sample():
            calls.append(None)
            if len(calls) == 1:
                return 151
            raise OSError("sampler failed")

        row = run_root_arm_v03(
            self.game, self.root, RandomInferenceModel("multi-step-jepa"),
            rss_cap_bytes=150, rss_sampler=sample,
        )
        self.assertEqual(row["stop_reason"], "rss_cap")
        self.assertEqual(len(calls), 1)

    def test_periodic_rss_crossing_is_caught_and_reported(self):
        samples = iter((100, 200, 100))
        row = run_root_arm_v03(
            self.game, self.root, RandomInferenceModel("multi-step-jepa"),
            node_cap=10_000, wall_cap_seconds=5.0, rss_cap_bytes=150,
            rss_sampler=lambda: next(samples),
        )
        self.assertEqual(row["stop_reason"], "rss_cap")
        self.assertGreaterEqual(row["node_visits"], 256)
        self.assertLessEqual(row["node_visits"], 10_000)
        self.assertEqual(row["peak_sampled_rss_bytes"], 200)

    def test_final_rss_crossing_overrides_node_stop_without_escaping(self):
        samples = iter((100, 200))
        row = run_root_arm_v03(
            self.game, self.root, RandomInferenceModel("multi-step-jepa"),
            node_cap=1, rss_cap_bytes=150,
            rss_sampler=lambda: next(samples),
        )
        self.assertEqual(row["stop_reason"], "rss_cap")
        self.assertEqual(row["node_visits"], 1)
        self.assertEqual(row["peak_sampled_rss_bytes"], 200)
        self.assertTrue(row["fallback_action_available"])

    def test_no_cap_crossing_preserves_v02_search_counters(self):
        reference = run_root_arm(
            self.game, self.root, RandomInferenceModel("single-pair-jepa"),
            node_cap=5_000, wall_cap_seconds=5.0, rss_cap_bytes=1 << 60,
        )
        revised = run_root_arm_v03(
            self.game, self.root, RandomInferenceModel("single-pair-jepa"),
            node_cap=5_000, wall_cap_seconds=5.0, rss_cap_bytes=1 << 60,
            rss_sampler=lambda: 100,
        )
        for field in (
            "completed_depth", "stop_reason", "node_visits", "transition_calls",
            "encoder_calls", "predictor_calls", "decoder_calls", "value_calls",
            "model_calls", "terminal_nodes",
        ):
            self.assertEqual(revised[field], reference[field], field)

    def test_progress_journal_is_append_only_parseable_jsonl(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "pilot.progress.jsonl"
            append_progress_record(path, {"record_type": "manifest", "cells": 2})
            append_progress_record(path, {"record_type": "cell", "sequence": 1})
            rows = [json.loads(line) for line in path.read_text().splitlines()]
        self.assertEqual([row["record_type"] for row in rows], ["manifest", "cell"])
        self.assertEqual(rows[1]["sequence"], 1)

    def test_progress_journal_is_create_only_and_starts_with_manifest(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "pilot.progress.jsonl"
            create_progress_journal(path, {"record_type": "manifest", "cells": 2})
            with self.assertRaises(FileExistsError):
                create_progress_journal(
                    path, {"record_type": "manifest", "cells": 3}
                )
            rows = [json.loads(line) for line in path.read_text().splitlines()]
        self.assertEqual(rows, [{"record_type": "manifest", "cells": 2}])

    def test_final_receipt_creation_never_replaces_existing_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "pilot.json"
            write_new_receipt_atomic(path, {"receipt": 1})
            with self.assertRaises(FileExistsError):
                write_new_receipt_atomic(path, {"receipt": 2})
            self.assertEqual(json.loads(path.read_text()), {"receipt": 1})

    def test_directory_fsync_failure_is_distinguished_after_link(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "pilot.json"
            with mock.patch(
                "two_player.v212_pilot_v03.fsync_directory",
                side_effect=OSError("simulated directory fsync failure"),
            ):
                with self.assertRaises(ReceiptPublicationUncertain) as caught:
                    write_new_receipt_atomic(path, {"receipt": "verified"})
            self.assertEqual(caught.exception.path, path)
            self.assertEqual(json.loads(path.read_text()), {"receipt": "verified"})

    def test_temp_unlink_failure_after_link_is_publication_uncertain(self):
        import os

        real_unlink = os.unlink
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "pilot.json"

            def fail_temp_unlink(candidate):
                if Path(candidate).name.startswith("pilot.json."):
                    raise OSError("simulated temp unlink failure")
                return real_unlink(candidate)

            with mock.patch(
                "two_player.v212_pilot_v03.os.unlink",
                side_effect=fail_temp_unlink,
            ):
                with self.assertRaises(ReceiptPublicationUncertain) as caught:
                    write_new_receipt_atomic(path, {"receipt": "verified"})
            self.assertEqual(caught.exception.path, path)
            self.assertEqual(json.loads(path.read_text()), {"receipt": "verified"})

    def test_runner_journals_rss_stop_without_publishing_aggregate(self):
        scheduled = build_root_schedule_v02()[0]
        with tempfile.TemporaryDirectory() as directory:
            repository = Path(directory)
            (repository / "tools").mkdir()
            (repository / "chess_data").mkdir()
            runner = __import__(
                "tools.v212_random_weight_compute_pilot_v03", fromlist=["runner"]
            )
            with (
                mock.patch.object(runner, "__file__", str(repository / "tools" / "runner.py")),
                mock.patch.object(runner, "build_root_schedule_v02", return_value=[scheduled]),
                mock.patch.object(runner, "ARMS", ("multi-step-jepa",)),
                mock.patch.object(runner, "INIT_SEEDS", (7,)),
                mock.patch.object(runner, "_warmup"),
                mock.patch.object(runner, "source_sha256", return_value="a" * 64),
                mock.patch.object(runner, "run_root_arm_v03", return_value={
                    "stop_reason": "rss_cap", "completed_depth": 0,
                    "peak_sampled_rss_bytes": 151, "wall_seconds": 0.01,
                    "node_visits": 0,
                }),
            ):
                status = run_v03_runner(["chess_data/test-v03.json"])
            receipt = repository / "chess_data" / "test-v03.json"
            journal = repository / "chess_data" / "test-v03.progress.jsonl"
            rows = [json.loads(line) for line in journal.read_text().splitlines()]
        self.assertEqual(status, 2)
        self.assertFalse(receipt.exists())
        self.assertEqual([row["record_type"] for row in rows],
                         ["manifest", "cell", "terminal"])
        self.assertEqual(rows[-1]["status"], "stopped_safety")

    def test_runner_marks_linked_receipt_with_failed_directory_fsync_uncertain(self):
        scheduled = build_root_schedule_v02()[0]
        with tempfile.TemporaryDirectory() as directory:
            repository = Path(directory)
            (repository / "tools").mkdir()
            (repository / "chess_data").mkdir()
            runner = __import__(
                "tools.v212_random_weight_compute_pilot_v03", fromlist=["runner"]
            )

            def publish_then_fail(path, payload):
                path.write_text(json.dumps(payload))
                raise ReceiptPublicationUncertain(path, OSError("fsync failed"))

            with (
                mock.patch.object(runner, "__file__", str(repository / "tools" / "runner.py")),
                mock.patch.object(runner, "build_root_schedule_v02", return_value=[scheduled]),
                mock.patch.object(runner, "ARMS", ("multi-step-jepa",)),
                mock.patch.object(runner, "INIT_SEEDS", (7,)),
                mock.patch.object(runner, "_warmup"),
                mock.patch.object(runner, "source_sha256", return_value="a" * 64),
                mock.patch.object(runner, "run_root_arm_v03", return_value={
                    "stop_reason": "depth_4_complete", "completed_depth": 4,
                    "peak_sampled_rss_bytes": 100, "wall_seconds": 0.01,
                    "node_visits": 1,
                }),
                mock.patch.object(runner, "create_receipt_v02", return_value={
                    "pilot_version": "v212-random-weight-compute-pilot-v02",
                    "results": [],
                }),
                mock.patch.object(runner, "_verify_v03_receipt"),
                mock.patch.object(runner, "write_new_receipt_atomic",
                                  side_effect=publish_then_fail),
            ):
                status = run_v03_runner(["chess_data/test-v03.json"])
            receipt = repository / "chess_data" / "test-v03.json"
            journal = repository / "chess_data" / "test-v03.progress.jsonl"
            receipt_exists = receipt.exists()
            rows = [json.loads(line) for line in journal.read_text().splitlines()]
        self.assertEqual(status, 1)
        self.assertTrue(receipt_exists)
        self.assertEqual(rows[-1]["status"], "publication_uncertain")
        self.assertEqual(rows[-1]["receipt"], str(receipt))

    def test_v03_verifier_preserves_completed_depth_and_wall_cap_label(self):
        receipt = {
            "pilot_version": "v212-random-weight-compute-pilot-v03",
            "schedule_source_sha256": "a" * 64,
            "results": [{"completed_depth": 4, "stop_reason": "wall_cap"}],
        }
        with mock.patch(
            "tools.v212_random_weight_compute_pilot_v03.verify_receipt_v02"
        ) as legacy_verifier:
            _verify_v03_receipt(receipt)
        legacy = legacy_verifier.call_args.args[0]
        self.assertEqual(legacy["pilot_version"],
                         "v212-random-weight-compute-pilot-v02")
        self.assertEqual(legacy["results"][0]["stop_reason"],
                         "depth_4_complete")
        self.assertEqual(receipt["results"][0]["stop_reason"], "wall_cap")


if __name__ == "__main__":
    unittest.main()

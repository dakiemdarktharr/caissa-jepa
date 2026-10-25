"""Isolated synthetic producer fixtures, with no project corpus generation."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from research_ledger import Ledger, file_sha256
from tools import counterplay_data as producer


class CounterplayProducerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "research").mkdir()
        (self.root / "research/protocol.yaml").write_text('{}')
        self.recipe = {"corpus_seed": 2026102501, "train_episodes_per_game": 1,
                       "development_episodes_per_game": 1, "train_windows_per_game": 32,
                       "development_windows_per_game": 32}
        (self.root / "research/data_contract.json").write_text(json.dumps({"pilot_recipe": self.recipe}))
        self.fixture = {"roots": [{"root_id": "fixture", "reference": {"wall_seconds": 0.01}}],
                        "audit": {"fixture": {"count": 1}}, "cpu_seconds": 0.02,
                        "episodes": [{"episode_id": "fixture", "role": "train"}],
                        "window_count_gate": True, "reference_yield_gate": True}
        self.patches = [patch.object(producer, "ROOT", self.root),
                        patch.object(producer, "SOURCES", ("research/protocol.yaml", "research/data_contract.json")),
                        patch.object(producer.subprocess, "check_output", side_effect=lambda args, **kw: "" if "status" in args else "a" * 40),
                        patch.object(producer.resource, "setrlimit"),
                        patch.dict(producer.os.environ, {"OPENBLAS_NUM_THREADS": "1", "OMP_NUM_THREADS": "1"})]
        for item in self.patches:
            item.start()
            self.addCleanup(item.stop)

    def run_fixture(self, name, data=None):
        target = self.root / "chess_data" / name
        receipt = self.root / f"{name}.json"
        with patch.object(producer, "build", return_value=copy.deepcopy(self.fixture if data is None else data)):
            result = producer.prepare(target, receipt, run_id=name)
        return target, receipt, result

    def test_success_binds_payload_and_receipt_and_excludes_timing_from_data_identity(self):
        first, receipt, result = self.run_fixture("first")
        changed = copy.deepcopy(self.fixture)
        changed["cpu_seconds"] = 7.9
        changed["roots"][0]["reference"]["wall_seconds"] = 4.3
        second, _, other = self.run_fixture("second", changed)
        self.assertEqual(file_sha256(first / "data.json"), file_sha256(second / "data.json"))
        self.assertEqual(result["data_sha256"], other["data_sha256"])
        self.assertEqual(result["status"], "construction_gates_passed")
        with Ledger(self.root / "chess_data/research_metrics.sqlite") as ledger:
            runs = ledger.snapshot()
            run = next(r for r in runs if r["manifest"]["run_id"] == "first")
            self.assertEqual(run["manifest"]["inputs"]["dataset"], file_sha256(first / "data.json"))
            payload = run["events"][0]["content"]
            self.assertEqual(payload["dimensions"]["receipt_sha256"], file_sha256(receipt))

    def test_failure_and_feasibility_gate_are_retained_without_overwrite(self):
        target = self.root / "chess_data" / "failed"
        with patch.object(producer, "build", side_effect=TimeoutError("fixture cap")):
            with self.assertRaises(TimeoutError):
                producer.prepare(target, self.root / "failed.json", run_id="failed")
        self.assertTrue((target / "failure.json").exists())
        with Ledger(self.root / "chess_data/research_metrics.sqlite") as ledger:
            self.assertEqual(len(ledger.snapshot()[0]["events"]), 2)
        bad = copy.deepcopy(self.fixture); bad["reference_yield_gate"] = False
        target, _, result = self.run_fixture("low-yield", bad)
        self.assertEqual(result["status"], "failed_feasibility_gate")
        with self.assertRaisesRegex(ValueError, "fresh"):
            self.run_fixture("low-yield")

    def test_dirty_source_threads_and_destination_are_rejected_before_generation(self):
        with patch.object(producer.subprocess, "check_output", return_value=" M source.py\n"):
            with self.assertRaisesRegex(ValueError, "clean pinned"):
                producer.prepare(self.root / "chess_data/a", self.root / "a.json", run_id="a")
        with patch.dict(producer.os.environ, {"OMP_NUM_THREADS": "4"}):
            with self.assertRaisesRegex(ValueError, "threads"):
                producer.prepare(self.root / "chess_data/b", self.root / "b.json", run_id="b")
        with self.assertRaisesRegex(ValueError, "chess_data"):
            producer.prepare(self.root / "public", self.root / "c.json", run_id="c")
        self.assertFalse((self.root / "chess_data").exists())


if __name__ == "__main__":
    unittest.main()

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor

from research_ledger import Ledger, file_sha256, measured_objective


def manifest(run_id="test", phase="smoke"):
    return {"run_id": run_id, "phase": phase, "protocol_id": "synthetic-verification-v1",
            "code_commit": "a" * 40, "config": {"synthetic": True},
            "inputs": {"dataset": "b" * 64, "split": "c" * 64, "protocol": "d" * 64},
            "environment": {"python": sys.version.split()[0]}, "arm": "fixture", "seed": 0,
            "required_metrics": {"train_step": ["loss", "gradient_norm"]}}


class ResearchLedgerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.path = self.root / "metrics.sqlite"

    def test_acknowledged_events_survive_process_exit_without_close(self):
        script = """
import json,os,sys
from research_ledger import Ledger
l=Ledger(sys.argv[1]); l.create_run(json.loads(sys.argv[2]))
l.record('test','step:0','train_step',step=0,metrics={'loss':1.0,'gradient_norm':2.0})
os._exit(7)
"""
        result = subprocess.run([sys.executable, "-c", script, str(self.path), json.dumps(manifest())])
        self.assertEqual(result.returncode, 7)
        with Ledger(self.path) as ledger:
            self.assertEqual(len(ledger.snapshot()[0]["events"]), 1)

    def test_idempotency_and_conflicting_replay(self):
        with Ledger(self.path) as ledger:
            ledger.create_run(manifest())
            ledger.create_run(manifest())
            h = ledger.record("test", "x", "measurement", metrics={"value": 0.0})
            self.assertEqual(h, ledger.record("test", "x", "measurement", metrics={"value": 0.0}))
            with self.assertRaisesRegex(ValueError, "changed content"):
                ledger.record("test", "x", "measurement", metrics={"value": 1.0})
            changed = manifest(); changed["seed"] = 99
            with self.assertRaisesRegex(ValueError, "different metadata"):
                ledger.create_run(changed)
            self.assertEqual(len(ledger.snapshot()[0]["events"]), 1)

    def test_concurrent_writers_have_one_contiguous_chain(self):
        with Ledger(self.path) as ledger:
            ledger.create_run(manifest())
        def write(i):
            with Ledger(self.path) as ledger:
                ledger.record("test", f"event:{i}", "measurement", metrics={"index": i})
        with ThreadPoolExecutor(max_workers=4) as pool:
            list(pool.map(write, range(20)))
        with Ledger(self.path) as ledger:
            events = ledger.snapshot()[0]["events"]
        self.assertEqual([e["sequence"] for e in events], list(range(1, 21)))

    def test_rejects_nonfinite_boolean_and_missing_required_metrics(self):
        with Ledger(self.path) as ledger:
            ledger.create_run(manifest())
            for value in [float("nan"), float("inf"), True, "0.0"]:
                with self.subTest(value=value), self.assertRaises(ValueError):
                    ledger.record("test", "bad", "measurement", metrics={"x": value})
            with self.assertRaisesRegex(ValueError, "required metrics"):
                ledger.record("test", "bad", "train_step", metrics={"loss": 1})
            with self.assertRaisesRegex(ValueError, "missing_reason"):
                ledger.record("test", "bad", "measurement", metrics={"tokens": None})
            ledger.record("test", "unknown", "agent_usage", metrics={"tokens": None}, missing_reason="host does not expose usage")

    def test_detects_mutation_and_middle_event_deletion(self):
        with Ledger(self.path) as ledger:
            ledger.create_run(manifest())
            for i in range(3):
                ledger.record("test", str(i), "measurement", metrics={"x": i})
            ledger.db.execute("DELETE FROM events WHERE sequence=2")
            with self.assertRaisesRegex(ValueError, "integrity"):
                ledger.snapshot()
        with Ledger(self.root / "other.sqlite") as ledger:
            ledger.create_run(manifest())
            ledger.db.execute("UPDATE runs SET manifest=?", (json.dumps(dict(manifest(), seed=5)),))
            with self.assertRaisesRegex(ValueError, "integrity"):
                ledger.snapshot()

    def test_locked_export_requires_explicit_bound_release(self):
        with Ledger(self.path) as ledger:
            h = ledger.create_run(manifest(phase="locked"))
            ledger.record("test", "final", "measurement", metrics={"regret": 0.3})
            out = ledger.export(self.root / "exports")
            data = json.loads((out / "snapshot.json").read_text())
            self.assertEqual(data["runs"], [])
            self.assertEqual(data["withheld_run_ids"], ["test"])
            with self.assertRaisesRegex(ValueError, "release"):
                ledger.export(self.root / "exports", release={"reason": "trust me"})
            release = {"reason": "synthetic release fixture", "review_receipt_sha256": "e" * 64,
                       "run_manifest_hashes": {"test": h}}
            out = ledger.export(self.root / "exports", release=release)
            self.assertEqual(len(json.loads((out / "snapshot.json").read_text())["runs"]), 1)

    def test_snapshot_is_stable_checksummed_and_bounded(self):
        with Ledger(self.path) as ledger:
            ledger.create_run(manifest())
            ledger.record("test", "x", "measurement", metrics={"nested": {"h1": [0.1, 0.2]}})
            out = ledger.export(self.root / "exports")
            self.assertEqual(out, ledger.export(self.root / "exports"))
            checksums = json.loads((out / "checksums.json").read_text())
            for name, expected in checksums.items():
                self.assertEqual(file_sha256(out / name), expected)
            with self.assertRaisesRegex(ValueError, "limit"):
                ledger.export(self.root / "tiny", max_bytes=20)
            (out / "events.csv").write_text("corrupted")
            with self.assertRaisesRegex(ValueError, "inconsistent"):
                ledger.export(self.root / "exports")

    def test_scientific_manifest_requires_provenance(self):
        with Ledger(self.path) as ledger:
            m = manifest(phase="development"); m["inputs"] = {}
            with self.assertRaisesRegex(ValueError, "identities"):
                ledger.create_run(m)

    def test_failed_and_nonfinite_objectives_leave_failure_evidence(self):
        class InvalidObjective:
            def __init__(self, raises):
                self.raises = raises

            def loss_grad(self, batch):
                if self.raises:
                    raise RuntimeError("synthetic objective failure")
                return {"arm": "fixture", "loss": float("nan")}, {}

        with Ledger(self.path) as ledger:
            ledger.create_run(manifest())
            for index, raises in enumerate((True, False)):
                with self.assertRaises((RuntimeError, ValueError)):
                    measured_objective(ledger, "test", f"bad:{index}", index, InvalidObjective(raises), None)
            events = ledger.snapshot()[0]["events"]
            self.assertEqual(len(events), 2)
            self.assertEqual([e["content"]["kind"] for e in events], ["failure", "failure"])
            self.assertEqual([e["content"]["dimensions"]["stage"] for e in events], ["objective", "measurement"])
            self.assertTrue(all(e["content"]["missing_reason"] for e in events))

    def test_objective_adapter_records_real_model_metrics_without_changing_outputs(self):
        import numpy as np
        from two_player.v212_model import V212Config, V212Model
        from tests.test_v212_model import synthetic_batch
        model = V212Model(V212Config(seed=9))
        batch = synthetic_batch()
        expected_metrics, expected_gradients = model.loss_grad(batch)
        with Ledger(self.path) as ledger:
            ledger.create_run(manifest())
            metrics, gradients = measured_objective(ledger, "test", "objective:0", 0, model, batch)
            self.assertEqual(metrics, expected_metrics)
            for name, expected in expected_gradients.items():
                np.testing.assert_array_equal(gradients[name], expected)
            event = ledger.snapshot()[0]["events"][0]["content"]
            self.assertIn("valid_target_counts", event["metrics"])
            self.assertIn("latent_roll_loss_by_horizon", event["metrics"])
            self.assertGreaterEqual(event["metrics"]["objective_wall_seconds"], 0)
            m = manifest(); m["code_commit"] = "uncommitted"
            with self.assertRaisesRegex(ValueError, "full code commit"):
                ledger.create_run(m)


if __name__ == "__main__":
    unittest.main()

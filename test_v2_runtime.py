"""Runtime schedule/identity safeguards; no research fitting is performed."""
from collections import Counter
import json
import math
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import numpy as np

from two_player_v2 import runtime
from two_player_v2.model import Config


def fixture_forks():
    return [{"game": game, "root_id": f"{game}-{root}", "split": "train"}
            for game, roots in (("a", 2), ("b", 3))
            for root in range(roots) for _ in range(root+1)]


class V2RuntimeTests(unittest.TestCase):
    def test_schedule_balances_games_and_covers_every_root(self):
        forks = fixture_forks()
        indices, receipt = runtime.epoch_indices(forks, 17, 0)
        games = Counter(forks[i]["game"] for i in indices)
        roots = Counter(forks[i]["root_id"] for i in indices)
        self.assertEqual(games, {"a": 3*runtime.DRAWS, "b": 3*runtime.DRAWS})
        self.assertEqual(len(roots), 5)
        self.assertTrue(all(n >= runtime.DRAWS and n % runtime.DRAWS == 0 for n in roots.values()))
        self.assertEqual(receipt["games"]["a"]["repeated_root_draws"], 1)
        self.assertEqual(receipt["games"]["b"]["repeated_root_draws"], 0)
        self.assertEqual(receipt["unique_forks"], len(set(indices.tolist())))

    def test_pairing_is_seed_epoch_addressed_and_reproducible(self):
        forks = fixture_forks()
        first, metadata = runtime.epoch_indices(forks, 17, 3)
        repeated, second_metadata = runtime.epoch_indices(forks, 17, 3)
        next_epoch, next_metadata = runtime.epoch_indices(forks, 17, 4)
        next_seed, seed_metadata = runtime.epoch_indices(forks, 29, 3)
        np.testing.assert_array_equal(first, repeated)
        self.assertEqual(metadata, second_metadata)
        self.assertNotEqual(metadata["index_sha256"], next_metadata["index_sha256"])
        self.assertNotEqual(metadata["index_sha256"], seed_metadata["index_sha256"])
        self.assertEqual(len(first), len(next_epoch))
        self.assertEqual(len(first), len(next_seed))

    def test_nontraining_samples_and_invalid_epoch_are_rejected(self):
        for split in ("development", "selection", "final"):
            with self.assertRaises(ValueError):
                runtime.epoch_indices([{"game": "a", "root_id": "a", "split": split}], 17, 0)
        for epoch in (-1, True, 1.5):
            with self.assertRaises(ValueError):
                runtime.epoch_indices(fixture_forks(), 17, epoch)
        with self.assertRaises(ValueError):
            runtime.epoch_indices([], 17, 0)

    def test_subset_preserves_missing_horizon_and_legal_masks(self):
        batch = {"valid": np.array([[True, True, False], [True, True, True]]),
                 "legal": np.zeros((2, 3, 65), bool),
                 "x": np.arange(2*3*198).reshape(2, 3, 198)}
        batch["legal"][0, 0, 2] = True
        selected = runtime.subset(batch, np.array([0, 1, 0]))
        np.testing.assert_array_equal(selected["valid"][:, 2], [False, True, False])
        np.testing.assert_array_equal(selected["legal"][:, 0, 2], [True, False, True])
        np.testing.assert_array_equal(selected["x"][2], batch["x"][0])

    def test_resume_requires_exact_epoch_step_schedule(self):
        forks = fixture_forks()
        count = len(runtime.epoch_indices(forks, 17, 0)[0])
        config = Config(seed=17)
        steps = math.ceil(count/config.batch_size)
        model = SimpleNamespace(config=config, epoch=2, step=2*steps)
        runtime.verify_resume(model, forks)
        model.step += 1
        with self.assertRaises(ValueError):
            runtime.verify_resume(model, forks)
        model.epoch = runtime.EPOCHS+1
        model.step = model.epoch*steps
        with self.assertRaises(ValueError):
            runtime.verify_resume(model, forks)

    def test_identity_pins_config_data_source_and_runtime_contract(self):
        manifest = {"dataset_fingerprint": "fixture-data"}
        source = {"model.py": "fixture-hash"}
        first = runtime.identity(Config(seed=17), manifest, source)
        changed = runtime.identity(Config(seed=29), manifest, source)
        self.assertEqual(first["source"], source)
        self.assertEqual(first["data"], "fixture-data")
        self.assertEqual(first["epochs"], runtime.EPOCHS)
        self.assertEqual(first["draws"], runtime.DRAWS)
        self.assertNotEqual(first["config_sha256"], changed["config_sha256"])
        files = runtime.runtime_source()
        for name in ("two_player_v2/model.py", "two_player_v2/evaluate.py", "two_player_v2/runtime.py", "docs/METHOD_V2.md"):
            self.assertIn(name, files)
            self.assertEqual(len(files[name]), 64)

    def test_source_change_fails_before_model_creation(self):
        train = {"manifest": {"dataset_fingerprint": "fixture"}, "forks": fixture_forks()}
        with TemporaryDirectory() as temporary, patch.object(runtime, "runtime_source", return_value={"new": "hash"}), patch.object(runtime, "Model") as model:
            with self.assertRaisesRegex(ValueError, "Source changed"):
                runtime.train_run(Config(), train, {}, Path(temporary)/"run", {"old": "hash"})
            model.assert_not_called()

    def test_exhausted_cap_prevents_first_optimizer_update(self):
        train = {"manifest": {"dataset_fingerprint": "fixture"}, "forks": fixture_forks()}
        source = runtime.runtime_source()
        with TemporaryDirectory() as temporary, patch.object(runtime.Model, "update") as update:
            with self.assertRaises((TimeoutError, ValueError)):
                runtime.train_run(Config(), train, {}, Path(temporary)/"run", source, max_seconds=0)
            update.assert_not_called()

    def test_active_attempt_cannot_resume_with_unaccounted_compute(self):
        train = {"manifest": {"dataset_fingerprint": "fixture"}, "forks": fixture_forks()}
        config = Config()
        source = runtime.runtime_source()
        expected = runtime.identity(config, train["manifest"], source)
        with TemporaryDirectory() as temporary:
            directory = Path(temporary)/"run"
            directory.mkdir()
            # Synthetic untrained checkpoint, explicitly used only to exercise
            # resume admission. No optimizer step is run in this test.
            model = runtime.Model(config)
            model.save(directory/"checkpoint.npz", expected)
            runtime.atomic_json(directory/"history.json", [])
            runtime.atomic_json(directory/"budget.json", {"status": "active", "identity": expected,
                                                         "prior_seconds": 0, "limit_seconds": 180})
            with patch.object(runtime.Model, "update") as update:
                with self.assertRaisesRegex(ValueError, "unaccounted compute"):
                    runtime.train_run(config, train, {}, directory, source, resume=True)
                update.assert_not_called()

    def test_grid_censored_learned_or_control_decision_is_inconclusive(self):
        roots = [{"game": "fixture", "root_id": "root", "trajectory": "trajectory", "split": "development"}]
        fake_data = {"roots": roots, "forks": fixture_forks()}
        fake_arrays = {"x": np.zeros((1, 3, 198))}
        manifest = {"dataset_fingerprint": "fixture"}
        source = {"fixture": "source"}

        def no_fit(config, train, batch, path, source):
            Path(path).mkdir()
            return object(), {"seconds": 0, "checkpoint_sha256": "fixture-only"}

        for bad_control in (False, True):
            def fake_evaluate(roots, model, tracks=None):
                if tracks == ("exact",):
                    statuses = ["error" if bad_control and model is None else "complete"]
                else:
                    statuses = ["complete", "complete" if bad_control else "censored"]
                return [{"root_id": "root", "status": s} for s in statuses]

            with self.subTest(bad_control=bad_control), TemporaryDirectory() as temporary:
                with patch.dict(runtime.os.environ, {"OPENBLAS_NUM_THREADS": "1", "OMP_NUM_THREADS": "1"}), \
                     patch.object(runtime, "runtime_source", return_value=source), \
                     patch.object(runtime, "verify_bytes", return_value=(manifest, b"")), \
                     patch.object(runtime, "load_dataset", return_value=fake_data), \
                     patch.object(runtime, "batch_arrays", return_value=fake_arrays), \
                     patch.object(runtime, "VARIANTS", ("direct",)), \
                     patch.object(runtime, "RATES", (.001,)), \
                     patch.object(runtime, "train_run", side_effect=no_fit), \
                     patch.object(runtime, "evaluate", side_effect=fake_evaluate), \
                     patch.object(runtime, "diagnostics", return_value={}), \
                     patch("builtins.print"):
                    result = runtime.run_grid("fixture-dataset", Path(temporary)/"grid")
                self.assertEqual(result["status"], "inconclusive")
                self.assertEqual(len(result["runs"]), 3)
                self.assertTrue(all(run["status"] == "complete" for run in result["runs"]))
                self.assertEqual(result["selection_predictions"], 0)
                self.assertEqual(result["final_predictions"], 0)
                if bad_control:
                    self.assertEqual(result["control_status_counts"]["error"], 1)
                else:
                    self.assertTrue(all(run["decision_status_counts"]["censored"] == 1 for run in result["runs"]))
                stored = json.loads((Path(temporary)/"grid"/"ledger.json").read_text())
                self.assertEqual(stored["status"], "inconclusive")


if __name__ == "__main__":
    unittest.main()

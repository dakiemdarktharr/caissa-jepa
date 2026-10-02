from dataclasses import asdict
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np

from tests.test_v28_model import observed_root
from two_player.v28_model import Config, METHOD_VERSION, Model
from two_player.v28_train import (RunConfig, _canonical_sha256, _train_epoch,
                                  _runtime_identity, train_dataset,
                                  train_development_dataset)


class V28TrainRuntimeTests(unittest.TestCase):
    def test_run_config_rejects_invalid_epoch_and_shuffle_seed(self):
        for kwargs in ({"epochs": 0}, {"epochs": True}, {"shuffle_seed": -1},
                       {"shuffle_seed": 1.5}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                RunConfig(**kwargs)

    def test_train_epoch_is_deterministic_and_records_order_fingerprint(self):
        records = [observed_root("connect4-gravity-6x7"),
                   observed_root("reversi6"),
                   observed_root("connect4-gravity-6x7")]
        config = Config(variant="reply-jepa", seed=23, latent=4, batch_size=2)
        first = Model(config)
        second = Model(config)
        metrics_a, order_a = _train_epoch(first, records, epoch_index=0, shuffle_seed=91)
        metrics_b, order_b = _train_epoch(second, records, epoch_index=0, shuffle_seed=91)
        self.assertEqual(order_a, order_b)
        self.assertEqual(metrics_a["order_sha256"], metrics_b["order_sha256"])
        self.assertEqual(metrics_a["roots"], 3)
        self.assertEqual(metrics_a["updates"], 2)
        for name in first.params:
            np.testing.assert_array_equal(first.params[name], second.params[name])

    def test_trainer_rejects_nontrain_records_before_model_update(self):
        records = [observed_root("reversi6")]
        records[0]["split"] = "validation"
        model = Model(Config(seed=4, latent=4, batch_size=2))
        before = {key: value.copy() for key, value in model.params.items()}
        with self.assertRaisesRegex(ValueError, "train split"):
            _train_epoch(model, records, epoch_index=0, shuffle_seed=1)
        for key in before:
            np.testing.assert_array_equal(model.params[key], before[key])

    def test_dataset_manifest_must_have_explicit_training_approval(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            (path / "manifest.json").write_text(json.dumps({
                "audit_passed": True, "training_approved": False,
            }), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "explicit training approval"):
                train_dataset(path, path / "model.npz",
                              model_config=Config(seed=3, latent=4, batch_size=2),
                              run_config=RunConfig())
            self.assertFalse((path / "model.npz").exists())

    def test_public_fit_entrypoint_is_manifest_gated_without_public_update_api(self):
        self.assertFalse(hasattr(Model, "update"))
        self.assertFalse(hasattr(__import__("two_player.v28_train",
                                            fromlist=["train_epoch"]), "train_epoch"))
        records = [observed_root("reversi6")]
        model = Model(Config(seed=4, latent=4, batch_size=2))
        before = {key: value.copy() for key, value in model.params.items()}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            (path / "manifest.json").write_text(json.dumps({
                "audit_passed": True, "training_approved": False,
            }), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "explicit training approval"):
                train_dataset(path, path / "model.npz")
        self.assertEqual(model.step, 0)
        for key in before:
            np.testing.assert_array_equal(model.params[key], before[key])

    def test_development_fit_has_separate_scope_and_approval_identity(self):
        records = [observed_root("reversi6")]
        manifest = {"audit": {"audit_passed": True},
                    "artifacts": {"records.jsonl": {"sha256": "a" * 64}},
                    "training_approved": False}
        config = Config(variant="reply-jepa", seed=23, latent=4, batch_size=2)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            data_dir = root / "data"
            data_dir.mkdir()
            (data_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            checkpoint = root / "development.npz"
            with patch("two_player.v28_train.load_development_split",
                       return_value=(records, "b" * 64, "c" * 64)) as loader:
                result = train_development_dataset(
                    data_dir, checkpoint, approval_path=root / "approval.json",
                    model_config=config, run_config=RunConfig(epochs=1, shuffle_seed=91))
            loader.assert_called_once_with(data_dir, "train", root / "approval.json")
            receipt = json.loads(checkpoint.with_suffix(".npz.receipt.json")
                                 .read_text(encoding="utf-8"))
            self.assertEqual(result["fit_scope"], "development-only")
            self.assertEqual(receipt["fit_scope"], "development-only")
            self.assertEqual(receipt["development_approval_sha256"], "c" * 64)
            self.assertEqual(receipt["effective_run"]["fit_scope"], "development-only")
            self.assertFalse(json.loads((data_dir / "manifest.json").read_text())[
                "training_approved"])

    def test_resume_matches_uninterrupted_and_writes_hashed_receipt(self):
        records = [observed_root("connect4-gravity-6x7"),
                   observed_root("reversi6"), observed_root("connect4-gravity-6x7")]
        manifest = {"audit": {"audit_passed": True},
                    "artifacts": {"records.jsonl": {"sha256": "a" * 64}}}
        config = Config(variant="reply-jepa", seed=23, latent=4, batch_size=2)
        run_two = RunConfig(epochs=2, shuffle_seed=91)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            data_dir = root / "data"
            data_dir.mkdir()
            (data_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            uninterrupted = root / "uninterrupted.npz"
            resumed = root / "resumed.npz"
            with patch("two_player.v28_train.load_split", return_value=(records, "b" * 64)):
                train_dataset(data_dir, uninterrupted, model_config=config, run_config=run_two)
                real_train_epoch = _train_epoch
                calls = 0

                def interrupt_after_first_epoch(*args, **kwargs):
                    nonlocal calls
                    calls += 1
                    if calls == 2:
                        raise RuntimeError("simulated interruption after committed epoch")
                    return real_train_epoch(*args, **kwargs)

                with patch("two_player.v28_train._train_epoch", interrupt_after_first_epoch):
                    with self.assertRaisesRegex(RuntimeError, "simulated interruption"):
                        train_dataset(data_dir, resumed, model_config=config,
                                      run_config=run_two)
                train_dataset(data_dir, resumed, model_config=config,
                              run_config=run_two, resume=True)
            receipt_path = resumed.with_suffix(".npz.receipt.json")
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            self.assertEqual(receipt["run_config_sha256"],
                             _canonical_sha256(receipt["effective_run"]))
            identity = {key: receipt[key] for key in
                        ("dataset_sha256", "audit_sha256", "run_config_sha256", "split")}
            left = Model.load(uninterrupted, config, identity)
            right = Model.load(resumed, config, identity)
            self.assertEqual(left.step, right.step)
            for group_name in ("params", "target", "m", "v"):
                for name in getattr(left, group_name):
                    np.testing.assert_array_equal(getattr(left, group_name)[name],
                                                  getattr(right, group_name)[name])
            self.assertEqual(receipt["checkpoint_sha256"],
                             hashlib.sha256(resumed.read_bytes()).hexdigest())
            self.assertEqual(receipt["completed_epochs"], 2)
            self.assertIsNone(receipt["evaluation"])
            self.assertEqual(receipt["effective_run"]["runtime"], _runtime_identity())
            self.assertEqual(receipt["fit_scope"], "approved-training")
            self.assertEqual(len(receipt["effective_run"]["runtime"][
                "requirements_lock_sha256"]), 64)


if __name__ == "__main__":
    unittest.main()

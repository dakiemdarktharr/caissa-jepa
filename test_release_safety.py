"""Regression tests for v7.1 data preservation, stop/resume and packaging."""
import copy
import json
import os
import tempfile
import threading
import time
import unittest
from argparse import Namespace
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
import numpy as np
from runtime_safety import FileLease, atomic_json, checkpoint_commit, restore_committed
from training_runtime import SampleCache
from adversarial_jepa import AdversarialJEPA, dataset_manifest_fingerprint, iter_dataset_games, sample_from_dataset_position
from nnue_baseline import NNUEStyleBaseline
from train_caissa_v7 import train
from arena_protocol import OPENINGS
from arena_store import ArenaHistory
from image_zip_import import zipimageimportworker
import test_model_arena as fixtures


class ReleaseSafetyTests(unittest.TestCase):
    def test_kernel_lock_never_probes_pid_and_recovers(self):
        with tempfile.TemporaryDirectory() as folder, patch("os.kill", side_effect=AssertionError("unsafe")):
            a, b = FileLease(Path(folder)/"lock"), FileLease(Path(folder)/"lock")
            self.assertTrue(a.acquire())
            self.assertFalse(b.acquire())
            a.release()
            self.assertTrue(b.acquire())
            b.release()
            self.assertTrue(a.path.exists())

    def test_committed_generation_restores_optimizer_and_weights(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/"model.npz"
            model = AdversarialJEPA(path, latent_size=8)
            checkpoint_commit(model, {"completed_epochs": 2})
            expected = model.encoder_w.copy()
            model.encoder_w.fill(123)
            model.save()
            self.assertEqual(restore_committed(path)["completed_epochs"], 2)
            np.testing.assert_array_equal(AdversarialJEPA(path, latent_size=8).encoder_w, expected)

    def test_fresh_mode_cannot_silently_load_checkpoint(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/"model.npz"
            path.write_bytes(b"do not overwrite")
            with self.assertRaises(FileExistsError):
                train(Namespace(fixture_only=True, model=str(path), resume=False))
            self.assertEqual(path.read_bytes(), b"do not overwrite")

    def test_h1_skips_disabled_predictors(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            dataset = fixtures.ModelArenaTests().build_dataset(root)
            sample = sample_from_dataset_position(next(iter_dataset_games(dataset))["positions"][0], np.random.default_rng(0))
            model = AdversarialJEPA(root/"h1.npz", latent_size=8, variant="h1")
            original = model._predict
            def predict(latent, actions, horizon):
                self.assertEqual(horizon, 1)
                return original(latent, actions, horizon)
            with patch.object(model, "_predict", side_effect=predict):
                model.train_batch([sample])
                model.evaluate_batch([sample])
            self.assertNotIn("predictor_w2", model.adam_m)

    def test_sparse_nnue_matches_dense_forward_and_gradient(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            dataset = fixtures.ModelArenaTests().build_dataset(root)
            samples = [sample_from_dataset_position(p, np.random.default_rng(0)) for p in next(iter_dataset_games(dataset))["positions"][:4]]
            model = NNUEStyleBaseline(root/"nnue.npz", latent_size=8)
            features, targets = model._prepare_batch(samples)
            indices, sparse_targets, sparse = model._sparse_batch(samples)
            dense = model._forward(features)
            np.testing.assert_allclose(sparse["value"], dense["value"], atol=1e-7)
            gradients = np.random.default_rng(0).normal(size=(len(samples),8)).astype(np.float32)
            sparse_g = np.zeros_like(model.input_w)
            for index, gradient in zip(indices, gradients):
                np.add.at(sparse_g, index, gradient)
            np.testing.assert_allclose(sparse_g, features.T @ gradients, atol=1e-6)

    def test_cache_resume_eta_uses_new_work_only(self):
        with tempfile.TemporaryDirectory() as folder:
            reports = []
            cache = SampleCache(folder,"test",10,reports.append)
            manifest = {"shards":[{"index":0,"complete":True,"bytes":1000,"source_bytes":500,"source_positions":50}]}
            cache._progress(manifest,"preparing_cache",time.monotonic(),1)
            self.assertIsNone(reports[-1]["eta_seconds"])
            self.assertEqual(reports[-1]["cache_rows_per_second"],0)

    def test_cache_cancellation_shuts_workers_and_releases_lease(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            dataset = fixtures.ModelArenaTests().build_dataset(root)
            calls = []
            def cancel(report):
                calls.append(report)
                if len(calls) >= 2:
                    raise KeyboardInterrupt("stop")
            cache = SampleCache(dataset,dataset_manifest_fingerprint(dataset),10,cancel,workers=1)
            start = time.monotonic()
            with self.assertRaises(KeyboardInterrupt):
                cache.prepare()
            self.assertLess(time.monotonic()-start,10)
            with FileLease(cache.lock_path):
                pass

    def test_cache_signature_changes_and_worker_checks_checksum(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            dataset = fixtures.ModelArenaTests().build_dataset(root)
            fingerprint = dataset_manifest_fingerprint(dataset)
            first = SampleCache(dataset,fingerprint,10,workers=1).prepare()
            manifest = json.loads((dataset/"dataset_manifest.json").read_text(encoding="utf-8"))
            shard = dataset/manifest["shards"][0]["path"]
            with shard.open("ab") as handle:
                handle.write(b"\n")
            second = SampleCache(dataset,fingerprint,10,workers=1)
            with self.assertRaises(ValueError):
                second.prepare()
            self.assertNotEqual(first.path,second.path)

    def test_all_frozen_openings_are_legal(self):
        from main import vitriengine, text_thanh_move
        from adversarial_jepa import snapshot_from_fen
        for name, line in OPENINGS:
            engine = vitriengine(snapshot_from_fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"),.01)
            for uci in line.split():
                move = text_thanh_move(uci)
                self.assertIn(move,engine.lay_tat_ca_nuoc_di_hop_le(engine.turn),name)
                engine.thuc_hien_nuoc_di(move)

    def test_zip_rejects_ads_reserved_paths_and_traversal(self):
        for path in ("folder/data:payload.png","../x.png","a/CON.png","a/trailing. /x.png","C:/x.png"):
            self.assertIsNone(zipimageimportworker.safe_member_path(path),path)

    def test_history_index_is_idempotent_and_drops_move_payloads(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/"arena.jsonl"
            result = {"series_id":"a","result":"1-0","move_records":[{"large":"payload"}]}
            path.write_text(json.dumps(result)+"\n",encoding="utf-8")
            store = ArenaHistory(Path(folder)/"history.sqlite")
            store.import_jsonl(path)
            store.import_jsonl(path)
            store.append(result)
            self.assertEqual(len(store),1)
            self.assertNotIn("move_records",store[-1])

    def test_resume_after_mid_epoch_stop_matches_uninterrupted_training(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            dataset = fixtures.ModelArenaTests().build_dataset(root)
            def arguments(path, epochs, resume=False):
                return Namespace(fixture_only=True, model=str(path), dataset=str(dataset), architecture="adversarial-jepa",
                    model_variant="h1", latent_size=8, epochs=epochs, resume=resume,
                    seed=20260903, validation_percent=10, batch_size=2, learning_rate=5e-4,
                    max_train_batches=3, max_validation_batches=1, progress_interval=.01,
                    cache_workers=1, time_budget_hours=.1, allow_dataset_change=False)
            first, second = root/"full.npz", root/"resumed.npz"
            train(arguments(first,2))
            train(arguments(second,1))
            def interrupt(report):
                if report.get("phase") == "train":
                    raise KeyboardInterrupt("test interruption")
            with self.assertRaises(KeyboardInterrupt):
                train(arguments(second,1,True), interrupt)
            train(arguments(second,1,True))
            with np.load(first) as a, np.load(second) as b:
                for name in a.files:
                    np.testing.assert_array_equal(a[name],b[name],err_msg=name)

    def test_deadline_applies_while_waiting_for_shared_cache(self):
        with tempfile.TemporaryDirectory() as folder:
            dataset = fixtures.ModelArenaTests().build_dataset(Path(folder))
            cache = SampleCache(dataset,dataset_manifest_fingerprint(dataset),10,deadline_epoch=time.time()+.05)
            start = time.monotonic()
            with patch.object(cache,"_acquire_lock",return_value=False), self.assertRaises(TimeoutError):
                cache.prepare()
            self.assertLess(time.monotonic()-start,1.5)


if __name__ == "__main__":
    __import__("multiprocessing").freeze_support()
    unittest.main()

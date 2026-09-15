"""Regression coverage for the production junction/cache and integrity failures."""
import copy
import json
import os
from pathlib import Path
import tempfile
import time
import unittest
from argparse import Namespace
from unittest.mock import patch
from adversarial_jepa import dataset_manifest_fingerprint
from dataset_integrity import validate_dataset, derive_dataset, sha256_file
from runtime_safety import atomic_json, checkpoint_commit
from training_runtime import SampleCache
from train_caissa_v7 import train
from research_protocol import canonical_game_identity, confirmation_protocol
import test_model_arena as fixtures


def args(dataset, model):
    return Namespace(fixture_only=True, dataset=str(dataset), model=str(model), architecture="adversarial-jepa",
                     model_variant="h1", epochs=1, batch_size=2, latent_size=8, learning_rate=5e-4,
                     seed=20260903, validation_percent=10, max_train_batches=1, max_validation_batches=1,
                     resume=False, allow_dataset_change=False, progress_interval=.01,
                     cache_workers=1, time_budget_hours=.1)


class PipelineRecoveryTests(unittest.TestCase):
    def test_stale_aggregate_rejected_before_checkpoint_creation(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            dataset = fixtures.ModelArenaTests().build_dataset(root)
            path = dataset / "dataset_manifest.json"
            manifest = json.loads(path.read_text())
            manifest["games"] += 1
            atomic_json(path, manifest)
            model = root / "new.npz"
            with self.assertRaisesRegex(ValueError, "Aggregate games"):
                train(args(dataset, model))
            self.assertFalse(model.exists())
            report = json.loads(model.with_suffix(".training.json").read_text())
            self.assertIn("validate_dataset", report["traceback"])
            self.assertIn("latest_pointer", report["path_diagnostics"])

    def test_derived_dedup_is_read_only_and_version_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            dataset = fixtures.ModelArenaTests().build_dataset(root)
            path = dataset / "dataset_manifest.json"
            manifest = json.loads(path.read_text())
            item = manifest["shards"][0]
            shard = dataset / item["path"]
            shard.write_bytes(shard.read_bytes() * 2)
            item.update(bytes=shard.stat().st_size, sha256=sha256_file(shard))
            atomic_json(path, manifest)
            before = {p: p.read_bytes() for p in dataset.rglob("*") if p.is_file()}
            result = derive_dataset(dataset, root / "derived")
            self.assertEqual(result["actual"]["games"], 1)
            self.assertEqual(result["status"], "PASSED")
            self.assertEqual(before, {p: p.read_bytes() for p in dataset.rglob("*") if p.is_file()})
            with self.assertRaises(FileExistsError):
                derive_dataset(dataset, root / "derived")

    def test_same_length_cache_corruption_rebuilds_only_one_shard(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            dataset = fixtures.ModelArenaTests().build_dataset(root)
            manifest_path = dataset / "dataset_manifest.json"
            manifest = json.loads(manifest_path.read_text())
            first = manifest["shards"][0]
            second = copy.deepcopy(first)
            second["path"] = "shards/second.jsonl"
            (dataset / second["path"]).write_bytes((dataset / first["path"]).read_bytes())
            manifest["shards"].append(second)
            atomic_json(manifest_path, manifest)
            fingerprint = dataset_manifest_fingerprint(dataset)
            cache = SampleCache(dataset, fingerprint, 10, workers=1).prepare()
            bad = cache.path / "shard_00000.bin"
            good = cache.path / "shard_00001.bin"
            good_time = good.stat().st_mtime_ns
            content = bytearray(bad.read_bytes())
            content[-1] ^= 1
            bad.write_bytes(content)
            repaired = SampleCache(dataset, fingerprint, 10, workers=1).prepare()
            self.assertEqual(good.stat().st_mtime_ns, good_time)
            self.assertNotEqual(bad.read_bytes(), bytes(content))
            self.assertTrue(list(repaired.batches("train", 2, 7)))
            metadata_path = repaired.path / "shard_00000.json"
            metadata = json.loads(metadata_path.read_text())
            metadata["records"][0]["offset"] += 1
            atomic_json(metadata_path, metadata)
            SampleCache(dataset, fingerprint, 10, workers=1).prepare()
            self.assertEqual(json.loads(metadata_path.read_text())["records"][0]["offset"], 0)
            self.assertEqual(good.stat().st_mtime_ns, good_time)

    def test_checkpoint_failure_does_not_complete_epoch(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            dataset = fixtures.ModelArenaTests().build_dataset(root)
            model = root / "new.npz"
            calls = []
            def commit(instance, report):
                calls.append(report)
                if len(calls) == 2:
                    raise PermissionError("injected generation failure")
                return checkpoint_commit(instance, report)
            with patch("train_caissa_v7.checkpoint_commit", side_effect=commit):
                with self.assertRaises(PermissionError):
                    train(args(dataset, model))
            report = json.loads(model.with_suffix(".training.json").read_text())
            self.assertEqual(report["completed_epochs"], 0)
            self.assertEqual(report["epochs"], [])
            self.assertEqual(report["trained_steps"], 0)
            self.assertIn("injected generation failure", report["traceback"])

    def test_queue_time_does_not_reduce_training_budget(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            dataset = fixtures.ModelArenaTests().build_dataset(root)
            model = root / "new.npz"
            arguments = args(dataset, model)
            arguments.queue_seconds = 24 * 3600
            train(arguments)
            report = json.loads(model.with_suffix(".training.json").read_text())
            self.assertEqual(report["status"], "COMPLETE")
            self.assertAlmostEqual(report["deadline_epoch"] - report["budget_started_at"], 360, delta=1)
            self.assertEqual(report["queue_seconds"], 24 * 3600)
            self.assertIn("checkpoint_io", report["phase_seconds"])

    def test_ema_ablation_round_trip_and_resume_guard(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            dataset = fixtures.ModelArenaTests().build_dataset(root)
            arguments = args(dataset, root / "no-ema.npz")
            arguments.ema_decay = 0.0
            train(arguments)
            from adversarial_jepa import AdversarialJEPA
            import numpy as np
            model = AdversarialJEPA(arguments.model, variant="h1")
            self.assertEqual(model.ema_decay, 0)
            np.testing.assert_array_equal(model.target_w, model.encoder_w)
            arguments.resume, arguments.ema_decay = True, .995
            with self.assertRaisesRegex(ValueError, "preserve ema_decay"):
                train(arguments)

    def test_locked_plan_excludes_selection_and_test_from_cache(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            dataset = fixtures.ModelArenaTests().build_dataset(root)
            manifest = json.loads((dataset / "dataset_manifest.json").read_text())
            shard = dataset / manifest["shards"][0]["path"]
            row = json.loads(shard.read_text())
            rows, assignments = [], {}
            for index, split in enumerate(("train", "validation", "selection", "test")):
                other = copy.deepcopy(row)
                other["game_hash"] = f"{index:064x}"
                rows.append(other)
                assignments[other["game_hash"]] = split
            shard.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
            manifest["shards"][0].update(bytes=shard.stat().st_size, sha256=sha256_file(shard), games=4, positions=4*len(row["positions"]))
            manifest.update(games=4, positions=4*len(row["positions"]), written_bytes=shard.stat().st_size)
            atomic_json(dataset / "dataset_manifest.json", manifest)
            plan = {"version": 1, "dataset_manifest_sha256": dataset_manifest_fingerprint(dataset), "locked_final_test": True, "assignments": assignments}
            plan_path = root / "plan.json"
            atomic_json(plan_path, plan)
            arguments = args(dataset, root / "research.npz")
            arguments.split_plan = str(plan_path)
            train(arguments)
            report = json.loads((root / "research.training.json").read_text())
            self.assertEqual(report["split_positions"]["train"], len(row["positions"]))
            self.assertEqual(report["split_positions"]["validation"], len(row["positions"]))
            self.assertEqual(report["skipped_samples"], 2*len(row["positions"]))
            self.assertTrue(report["split_plan_sha256"])

    def test_throughput_uses_actual_samples_and_high_resolution_durations(self):
        from training_runtime import TrainingETA
        eta = TrainingETA({"train": 2}, 1)
        eta.observe("train", .0004, 4)
        eta.observe("train", .0002, 1)
        self.assertAlmostEqual(eta.rows_per_second("train"), 5/.0006)

    def test_canonical_identity_ignores_headers_but_not_moves(self):
        game = {"positions": [{"ply": 0, "fen": "board w - - 0 1", "action_uci": "e2e4", "next_fen": "next b - - 0 1"}], "headers": {"Event": "A"}}
        other = copy.deepcopy(game)
        other["headers"]["Event"] = "B"
        self.assertEqual(canonical_game_identity(game), canonical_game_identity(other))
        other["positions"][0]["action_uci"] = "d2d4"
        self.assertNotEqual(canonical_game_identity(game), canonical_game_identity(other))
        self.assertFalse(confirmation_protocol()["ranking_allowed"])


if __name__ == "__main__":
    __import__("multiprocessing").freeze_support()
    unittest.main()

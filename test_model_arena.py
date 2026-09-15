"""Tests for multi-model training metadata and the read-only arena worker."""

import json
import os
import tempfile
import threading
import unittest
from argparse import Namespace
from pathlib import Path

import numpy as np

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from adversarial_jepa import (
    AdversarialJEPA,
    iter_dataset_games,
    sample_from_dataset_position,
)
from fen_dataset_tool import (
    FenDatasetBuilder,
)
from lejepa import LeJEPA
from nnue_baseline import NNUEStyleBaseline
from main import boardwidget, modelmatchwidget, modelmatchworker, vitriengine
from model_registry import arena_model_specs, training_model_specs
from train_caissa_v7 import train


GM_PGN = '''[Event "Arena sample"]
[Date "2026.01.01"]
[White "Alpha"]
[Black "Beta"]
[WhiteTitle "GM"]
[Result "1-0"]

1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 4. Ba4 Nf6 5. O-O Be7 1-0
'''


def verified_arena_fixture(root, models):
    from test_mars_hardening import disjoint_fixture
    from research_dataset import publish_audit
    from runtime_safety import atomic_json
    dataset = disjoint_fixture(root)
    plan_path = root / "audit.json"
    plan = publish_audit(dataset, plan_path)
    assert plan["status"] == "PASSED", plan["errors"]
    sample = sample_from_dataset_position(next(iter_dataset_games(dataset))["positions"][0], np.random.default_rng(0))
    for model in models:
        model.dataset_fingerprint = plan["dataset_fingerprint"]
        model.train_batch([sample])
        model.save()
    atomic_json(root / "chess_data/dataset_location.json", {"path": str(dataset), "split_plan": str(plan_path)})


class ModelArenaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.application = QApplication.instance() or QApplication([])

    def build_dataset(self, root):
        source = root / "games.pgn"
        source.write_text(GM_PGN, encoding="utf-8")
        dataset = root / "fen_dataset"
        builder = FenDatasetBuilder(
            dataset,
            target_bytes=1024 * 1024,
            shard_bytes=32 * 1024,
            allowed_titles={"GM"},
            only_gm_actions=False,
        )
        builder.ingest_path(source, {"name": "arena-test"})
        builder.close("COMPLETE")
        return dataset

    def test_registry_exposes_independent_training_checkpoints(self):
        with tempfile.TemporaryDirectory() as temporary:
            specs = training_model_specs(Path(temporary))
            self.assertEqual(len(specs), 7)
            self.assertEqual(sum(s['architecture'] in ('adversarial-jepa', 'lejepa') for s in specs), 5)
            self.assertEqual(len({str(spec["path"]) for spec in specs}), len(specs))
            self.assertTrue(any(spec["variant"] == "h1" for spec in specs))
            self.assertTrue(any(spec["architecture"] == "policy-value" for spec in specs))
            self.assertTrue(any(spec["architecture"] == "lejepa" for spec in specs))
            self.assertTrue(any(spec["architecture"] == "nnue" for spec in specs))
            self.assertEqual(arena_model_specs(Path(temporary))[0]["id"], "alpha-beta")

    def test_model_variants_have_different_active_horizons(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            h1 = AdversarialJEPA(root / "h1.npz", latent_size=8, variant="h1")
            h12 = AdversarialJEPA(root / "h12.npz", latent_size=8, variant="h1-h2")
            full = AdversarialJEPA(root / "full.npz", latent_size=8, variant="full")
            self.assertEqual(h1.enabled_horizons, (1,))
            self.assertEqual(h12.enabled_horizons, (1, 2))
            self.assertEqual(full.enabled_horizons, (1, 2, 4))
            full.save()
            restored = AdversarialJEPA(root / "full.npz", latent_size=8, variant="full", create_if_missing=False)
            self.assertEqual(restored.variant, "full")

    def test_lejepa_sigreg_trains_without_ema_and_round_trips(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            dataset = self.build_dataset(root)
            game = next(iter_dataset_games(dataset))
            sample = sample_from_dataset_position(
                game["positions"][0], np.random.default_rng(17)
            )
            self.assertIsNotNone(sample)
            model_path = root / "chess_data/lejepa_sigreg.npz"
            model = LeJEPA(model_path, latent_size=8)
            metrics = model.train_batch([sample], learning_rate=0.001)
            self.assertTrue(np.isfinite(metrics["loss"]))
            self.assertTrue(np.isfinite(metrics["sigreg_loss"]))
            self.assertFalse(hasattr(model, "target_w"))
            model.save()
            restored = LeJEPA(
                model_path,
                latent_size=8,
                create_if_missing=False,
            )
            self.assertEqual(restored.trained_steps, 1)
            self.assertEqual(restored.variant, "sigreg")

            trainer_path = root / "chess_data/trainer_lejepa.npz"
            self.assertEqual(
                train(Namespace(fixture_only=True,
                    dataset=str(dataset),
                    model=str(trainer_path),
                    epochs=1,
                    batch_size=2,
                    learning_rate=0.001,
                    latent_size=8,
                    architecture="lejepa",
                    model_variant="sigreg",
                    seed=17,
                    validation_percent=10,
                    max_train_batches=1,
                    max_validation_batches=1,
                    allow_dataset_change=False,
                    resume=False,
                    progress_interval=0.001,
                )),
                0,
            )
            report = json.loads(
                trainer_path.with_suffix(".training.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(report["architecture"], "lejepa")
            self.assertEqual(report["model_variant"], "sigreg")

    def test_nnue_style_trains_round_trips_and_uses_alpha_beta(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            dataset = self.build_dataset(root)
            game = next(iter_dataset_games(dataset))
            sample = sample_from_dataset_position(
                game["positions"][0], np.random.default_rng(23)
            )
            self.assertIsNotNone(sample)

            model_path = root / "chess_data/nnue_style_baseline.npz"
            model = NNUEStyleBaseline(model_path, latent_size=8)
            metrics = model.train_batch([sample], learning_rate=0.001)
            self.assertTrue(all(np.isfinite(value) for value in metrics.values()))
            self.assertGreater(model.hidden_size, 0)
            model.save()

            restored = NNUEStyleBaseline(
                model_path,
                latent_size=8,
                create_if_missing=False,
            )
            self.assertEqual(restored.trained_steps, 1)
            self.assertEqual(restored.variant, "nnue")
            state = sample["state"]
            engine = vitriengine(state, 0.02)
            legal_moves = engine.lay_tat_ca_nuoc_di_hop_le(engine.turn)
            self.assertTrue(np.isfinite(restored.danh_gia_snapshot(state)))
            _, priors, _ = restored.score_legal_moves(state, legal_moves[:4])
            self.assertAlmostEqual(sum(priors), 1.0, places=5)

            trainer_path = root / "chess_data/trainer_nnue.npz"
            self.assertEqual(
                train(Namespace(fixture_only=True,
                    dataset=str(dataset),
                    model=str(trainer_path),
                    epochs=1,
                    batch_size=2,
                    learning_rate=0.001,
                    latent_size=8,
                    architecture="nnue",
                    model_variant="nnue",
                    seed=23,
                    validation_percent=10,
                    max_train_batches=1,
                    max_validation_batches=1,
                    allow_dataset_change=False,
                    resume=False,
                    progress_interval=0.001,
                )),
                0,
            )
            report = json.loads(
                trainer_path.with_suffix(".training.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(report["architecture"], "nnue")
            self.assertEqual(report["model_variant"], "nnue")

            progress = []
            results = []
            worker = modelmatchworker(
                root,
                root / "chess_data/chess_engine.db",
                "nnue-style-v1",
                "alpha-beta",
                threading.Event(),
                move_time=0.05,
                max_plies=14,
            )
            worker.tien_do.connect(progress.append)
            worker.ket_qua.connect(results.append)
            worker.chay()
            moves = [item for item in progress if item["event"] == "MATCH_MOVE"]
            self.assertEqual(len(moves), 14)
            self.assertTrue(any(item["source"] == "NNUE_ALPHA_BETA" for item in moves))
            self.assertEqual(len(results), 1)

    def test_read_only_arena_randomizes_colors_and_emits_legal_moves(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.build_dataset(root)
            checkpoint = root / "chess_data/caissa_a_jepa_h1.npz"
            model = AdversarialJEPA(checkpoint, latent_size=8, variant="h1")
            model.trained_steps = 1
            model.save()
            progress = []
            results = []
            worker = modelmatchworker(
                root,
                root / "chess_data/chess_engine.db",
                "alpha-beta",
                "a-jepa-h1",
                threading.Event(),
                move_time=0.05,
                max_plies=6,
            )
            worker.tien_do.connect(progress.append)
            worker.ket_qua.connect(results.append)
            worker.chay()
            started = next(item for item in progress if item["event"] == "MATCH_STARTED")
            moves = [item for item in progress if item["event"] == "MATCH_MOVE"]
            self.assertEqual({started["white_model_id"], started["black_model_id"]}, {"alpha-beta", "a-jepa-h1"})
            self.assertEqual(len(moves), 6)
            self.assertTrue(all(len(item["move_text"]) in (4, 5) for item in moves))
            self.assertEqual(len(results), 1)
            self.assertIn(results[0]["result"], {"1-0", "0-1", "1/2-1/2", "*"})
            results_path = root / "chess_data/arena_results.jsonl"
            self.assertTrue(results_path.exists())
            stored = json.loads(results_path.read_text(encoding="utf-8").splitlines()[-1])
            self.assertEqual(stored["match_seed"], started["match_seed"])

    def test_series_checkpoint_restores_last_matchup_and_history(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            checkpoint = root / "chess_data/caissa_a_jepa_h1.npz"
            model = AdversarialJEPA(checkpoint, latent_size=8, variant="h1")
            model.save()
            second_checkpoint = root / "chess_data/caissa_a_jepa_v7.npz"
            second_model = AdversarialJEPA(
                second_checkpoint,
                latent_size=8,
                variant="full",
            )
            second_model.save()
            verified_arena_fixture(root, [model, second_model])

            history_path = root / "chess_data/arena_results.jsonl"
            history_path.parent.mkdir(parents=True, exist_ok=True)
            history_path.write_text(
                json.dumps({
                    "series_id": "series-1",
                    "result": "1-0",
                    "first_model_id": "alpha-beta",
                    "second_model_id": "a-jepa-h1",
                    "white_model_id": "alpha-beta",
                    "black_model_id": "a-jepa-h1",
                    "match_seed": 7,
                    "match_number": 4,
                })
                + "\n",
                encoding="utf-8",
            )
            checkpoint_path = root / "chess_data/arena_checkpoint.json"
            checkpoint_path.write_text(
                json.dumps({
                    "version": 1,
                    "status": "STOPPED",
                    "series_id": "series-1",
                    "first_model_id": "alpha-beta",
                    "second_model_id": "a-jepa-h1",
                    "match_number": 4,
                    "matches_started": 4,
                    "matches_completed": 3,
                    "match_seed": 7,
                }),
                encoding="utf-8",
            )

            board = boardwidget(project_dir=root)
            widget = modelmatchwidget(board)
            schedule = widget.build_round_robin_schedule(1)
            self.assertEqual(len(schedule), 6)
            for index in range(0, len(schedule), 2):
                self.assertEqual(schedule[index], schedule[index + 1][::-1])
            self.assertEqual(
                {frozenset(pair) for pair in schedule},
                {
                    frozenset(("alpha-beta", "a-jepa-h1")),
                    frozenset(("alpha-beta", "a-jepa-v7")),
                    frozenset(("a-jepa-h1", "a-jepa-v7")),
                },
            )
            self.assertTrue(widget.last_matchup_available())
            self.assertTrue(widget.continue_button.isEnabled())
            self.assertIn("HISTORY: 1", widget.stats_label.text())

            def capture_replay_pair():
                widget.series_pair = widget.series_replay_pair
                widget.series_replay_pair = None

            widget.start_next_series_match = capture_replay_pair
            widget.continue_last_matchup()
            self.assertTrue(widget.series_running)
            self.assertEqual(widget.series_pair, ("alpha-beta", "a-jepa-h1"))
            self.assertEqual(widget.resume_match_seed, 7)
            self.assertEqual(widget.series_matches_started, 4)

            widget.close()
            board.clock_timer.stop()
            board.close()


if __name__ == "__main__":
    unittest.main(verbosity=2)

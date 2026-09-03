"""Tests for multi-model training metadata and the read-only arena worker."""

import json
import tempfile
import threading
import unittest
from pathlib import Path

from adversarial_jepa import AdversarialJEPA
from fen_dataset_tool import FenDatasetBuilder
from main import modelmatchworker
from model_registry import arena_model_specs, training_model_specs


GM_PGN = '''[Event "Arena sample"]
[Date "2026.01.01"]
[White "Alpha"]
[Black "Beta"]
[WhiteTitle "GM"]
[Result "1-0"]

1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 4. Ba4 Nf6 5. O-O Be7 1-0
'''


class ModelArenaTests(unittest.TestCase):
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
            self.assertGreaterEqual(len(specs), 5)
            self.assertEqual(len({str(spec["path"]) for spec in specs}), len(specs))
            self.assertTrue(any(spec["variant"] == "h1" for spec in specs))
            self.assertTrue(any(spec["architecture"] == "policy-value" for spec in specs))
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


if __name__ == "__main__":
    unittest.main(verbosity=2)

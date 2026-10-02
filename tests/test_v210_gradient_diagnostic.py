import hashlib
import tempfile
import unittest
from pathlib import Path

import numpy as np

from two_player.v28_model import Config, Model, build_batch
from two_player.v28_data import V28_GAMES
from two_player.v210_gradient_diagnostic import (decompose_reply_jepa_gradients,
                                                 load_weights_only,
                                                 encoder_alignment)
from tools.v210_gradient_alignment_diagnostic import _all_screens_passed


def training_root(game_name):
    game = V28_GAMES[game_name]
    state = game.initial()
    action = game.legal_actions(state)[0]
    after = game.transition(state, action)
    reply = game.legal_actions(after)[0]
    leaf = game.transition(after, reply)
    return {"game": game_name, "split": "train",
            "state": {"board": state.board, "player": state.player},
            "action": action, "reply": reply,
            "future2": {"board": leaf.board, "player": leaf.player},
            "value": 0}


class V210GradientDiagnosticTests(unittest.TestCase):
    def test_screen_aggregation_handles_boolean_criteria(self):
        passing = {"screen": {"median": True, "ci": True, "seed_count": True}}
        failing = {"screen": {"median": True, "ci": False, "seed_count": True}}
        self.assertTrue(_all_screens_passed({"connect4": passing, "reversi6": passing}))
        self.assertFalse(_all_screens_passed({"connect4": passing, "reversi6": failing}))

    def test_weights_only_loader_does_not_decode_metadata(self):
        config = Config(variant="reply-jepa", seed=8, latent=4)
        source = Model(config)
        arrays = {"p_" + key: value for key, value in source.params.items()}
        arrays.update({"t_" + key: value for key, value in source.target.items()})
        arrays.update({"m_" + key: value for key, value in source.m.items()})
        arrays.update({"v_" + key: value for key, value in source.v.items()})
        arrays["metadata"] = np.asarray("not valid JSON; contains no readable history")
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "weights.npz"
            np.savez(path, **arrays)
            expected_sha = hashlib.sha256(path.read_bytes()).hexdigest()
            loaded = load_weights_only(path, config, expected_sha)
        for key, value in source.params.items():
            np.testing.assert_array_equal(loaded.params[key], value)
        for key, value in source.target.items():
            np.testing.assert_array_equal(loaded.target[key], value)
        self.assertEqual(loaded.step, 0)

    def test_components_sum_to_existing_gradient_without_updating_model(self):
        for game_name in V28_GAMES:
            with self.subTest(game=game_name):
                batch = build_batch([training_root(game_name)] * 2)
                model = Model(Config(variant="reply-jepa", seed=41, latent=6,
                                     batch_size=2))
                params = {key: value.copy() for key, value in model.params.items()}
                targets = {key: value.copy() for key, value in model.target.items()}
                _, expected = model.loss_grad(batch)
                metrics, components = decompose_reply_jepa_gradients(model, batch)
                self.assertLessEqual(metrics["gradient_sum_relative_error"], 1e-12)
                for key in expected:
                    actual = sum((part[key] for part in components.values()),
                                 np.zeros_like(expected[key]))
                    np.testing.assert_allclose(actual, expected[key],
                                               rtol=1e-12, atol=1e-13)
                for key, value in params.items():
                    np.testing.assert_array_equal(model.params[key], value)
                for key, value in targets.items():
                    np.testing.assert_array_equal(model.target[key], value)
                alignment = encoder_alignment(components)
                self.assertTrue(np.isfinite(alignment["task_norm"]))
                self.assertTrue(np.isfinite(alignment["jepa_norm"]))

    def test_decomposition_rejects_non_jepa_model(self):
        batch = build_batch([training_root("reversi6")])
        model = Model(Config(variant="task-value-dynamics", seed=2, latent=4))
        with self.assertRaises(ValueError):
            decompose_reply_jepa_gradients(model, batch)


if __name__ == "__main__":
    unittest.main()

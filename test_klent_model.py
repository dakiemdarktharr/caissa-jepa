import unittest

import numpy as np

from two_player.games import ACTION_SIZE, FEATURE_SIZE
from two_player.klent_model import (
    KLENTConfig,
    KLENTModel,
    collect_selfplay_batch,
    fit_selfplay_batch,
)


def sample_batch(seed=29):
    rng = np.random.default_rng(seed)
    x = rng.normal(0.0, 0.2, size=(3, FEATURE_SIZE))
    legal = np.zeros((3, ACTION_SIZE), dtype=bool)
    legal[0, [1, 3, 5]] = True
    legal[1, [0, 2]] = True
    legal[2, [4, 6, 8, 10]] = True
    policy_target = np.zeros((3, ACTION_SIZE), dtype=np.float64)
    policy_target[0, [1, 3, 5]] = [0.2, 0.3, 0.5]
    policy_target[1, [0, 2]] = [0.7, 0.3]
    policy_target[2, [4, 6, 8, 10]] = [0.1, 0.2, 0.3, 0.4]
    return {
        "x": x,
        "legal": legal,
        "policy_target": policy_target,
        "action": np.array([3, 0, 8], dtype=np.int64),
        "q_target": np.array([0.4, -0.2, 0.7]),
    }


class CountUpGame:
    """Small acyclic alternating game used only for synthetic validation."""

    name = "count-up-test"

    def initial(self):
        from two_player.games import State
        return State((0,), 1)

    def terminal(self, state):
        if state.board[0] < 7:
            return None
        return -state.player

    def legal_actions(self, state):
        return (0, 1) if self.terminal(state) is None else ()

    def transition(self, state, action):
        from two_player.games import State
        if action not in self.legal_actions(state):
            raise ValueError("illegal count-up action")
        return State((state.board[0] + action + 1,), -state.player)

    def features(self, state):
        result = np.zeros(FEATURE_SIZE, dtype=np.float64)
        result[state.board[0]] = 1.0
        return result


class KLENTModelTests(unittest.TestCase):
    def test_policy_q_outputs_respect_legal_mask_and_normalize(self):
        model = KLENTModel(KLENTConfig(seed=17, latent=8))
        batch = sample_batch()
        policy, q_values = model.predict(batch["x"], batch["legal"])
        self.assertTrue(np.all(np.isfinite(policy)))
        self.assertTrue(np.all(np.isfinite(q_values)))
        np.testing.assert_allclose(policy.sum(axis=1), 1.0)
        self.assertTrue(np.all(policy[~batch["legal"]] == 0.0))
        target, value = model.improvement_target(batch["x"], batch["legal"])
        np.testing.assert_allclose(target.sum(axis=1), 1.0)
        self.assertTrue(np.all(target[~batch["legal"]] == 0.0))
        self.assertEqual(value.shape, (3,))

    def test_shared_encoder_separate_policy_and_q_heads(self):
        model = KLENTModel(KLENTConfig(seed=23, latent=7))
        self.assertEqual(model.params["pw"].shape, (7, ACTION_SIZE))
        self.assertEqual(model.params["qw"].shape, (7, ACTION_SIZE))
        self.assertFalse(np.shares_memory(model.params["pw"], model.params["qw"]))
        self.assertEqual(model.parameter_counts()["active"], model.parameter_counts()["parameters"])

    def test_analytic_gradients_match_finite_differences(self):
        model = KLENTModel(KLENTConfig(seed=31, latent=5))
        batch = sample_batch(43)
        metrics, gradients = model.loss_grad(batch)
        self.assertTrue(np.isfinite(metrics["loss"]))
        eps = 1e-6
        for key, indices in {"ew": [(0, 0)], "eb": [(2,)], "pw": [(1, 3)],
                             "pb": [(5,)], "qw": [(4, 8)], "qb": [(10,)]}.items():
            for index in indices:
                parameter = model.params[key]
                original = parameter[index]
                parameter[index] = original + eps
                plus = model.loss_grad(batch)[0]["loss"]
                parameter[index] = original - eps
                minus = model.loss_grad(batch)[0]["loss"]
                parameter[index] = original
                numerical = (plus - minus) / (2 * eps)
                self.assertAlmostEqual(float(gradients[key][index]), numerical, delta=2e-6)

    def test_update_changes_parameters_and_increments_step(self):
        model = KLENTModel(KLENTConfig(seed=47, latent=6))
        batch = sample_batch(53)
        before = {key: value.copy() for key, value in model.params.items()}
        metrics = model.update(batch)
        self.assertEqual(model.step, 1)
        self.assertTrue(np.isfinite(metrics["gradient_norm"]))
        self.assertGreater(metrics["gradient_norm"], 0.0)
        self.assertTrue(any(not np.array_equal(before[key], model.params[key]) for key in before))

    def test_rejects_illegal_sample_and_empty_legal_row(self):
        model = KLENTModel(KLENTConfig(seed=59, latent=4))
        batch = sample_batch(61)
        batch["action"] = batch["action"].copy()
        batch["action"][0] = 2
        with self.assertRaisesRegex(ValueError, "must be legal"):
            model.loss_grad(batch)
        legal = batch["legal"].copy()
        legal[0] = False
        with self.assertRaisesRegex(ValueError, "each row needs a legal"):
            model.predict(batch["x"], legal)

    def test_selfplay_collection_and_fit_on_finite_toy_game(self):
        game = CountUpGame()
        model = KLENTModel(KLENTConfig(seed=67, latent=8, alpha=0.5, beta=1.0))
        collected = collect_selfplay_batch(game, model, episodes=8, seed=71)
        self.assertEqual(collected["episodes"], 8)
        self.assertGreater(collected["transitions"], 0)
        for trajectory in collected["trajectories"]:
            self.assertTrue(trajectory["terminal_successors"][-1])
            self.assertTrue(np.all(~trajectory["terminal_successors"][:-1]))
            self.assertTrue(np.all(np.isfinite(trajectory["q_target"])))
            self.assertTrue(np.all(trajectory["q_target"] >= -1.0))
            self.assertTrue(np.all(trajectory["q_target"] <= 1.0))
            self.assertTrue(np.all(trajectory["legal"].sum(axis=1) == 2))
        report = fit_selfplay_batch(model, collected, epochs=1, batch_size=8, seed=73)
        self.assertEqual(report["training_examples"], collected["transitions"])
        self.assertGreater(report["optimizer_steps"], 0)
        self.assertTrue(np.isfinite(report["history"][0]["loss"]))


if __name__ == "__main__":
    unittest.main()

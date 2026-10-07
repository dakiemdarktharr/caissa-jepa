import unittest

import numpy as np

from two_player.v212_model import ARMS, V212Config, V212Model, preflight_batch


def synthetic_batch():
    rng = np.random.default_rng(1234)
    n = 3
    legal = np.zeros((n, 65), dtype=bool)
    legal[:, [0, 1, 64]] = True
    policy = np.asarray([0, 1, 64], dtype=np.int64)
    actions = np.zeros((n, 4, 65), dtype=np.float64)
    action_ids = np.asarray([[0, 1, 64, 2], [1, 0, 2, 64], [64, 1, 0, 2]])
    for row in range(n):
        actions[row, np.arange(4), action_ids[row]] = 1.0
    actors = np.tile(np.asarray([1.0, -1.0, 1.0, -1.0]), (n, 1))
    return {
        "x": rng.normal(size=(n, 198)) * 0.1,
        "legal": legal,
        "policy": policy,
        "value": np.asarray([1.0, -1.0, 0.0]),
        "actions": actions,
        "actors": actors,
        "future_x": rng.normal(size=(n, 4, 198)) * 0.1,
        "future_value": rng.choice([-1.0, 0.0, 1.0], size=(n, 4)),
        "transition_exists": np.ones((n, 4), dtype=bool),
        "transition_valid": np.ones((n, 4), dtype=bool),
        "target_exists": np.ones((n, 4), dtype=bool),
        "terminal": np.zeros((n, 4), dtype=bool),
    }


class V212ModelTests(unittest.TestCase):
    def test_six_arm_objectives_are_finite_and_do_not_mutate_parameters(self):
        batch = synthetic_batch()
        for arm in ARMS:
            with self.subTest(arm=arm):
                model = V212Model(V212Config(arm=arm, seed=31))
                before = {key: value.copy() for key, value in model.params.items()}
                metrics, gradients = model.loss_grad(batch)
                self.assertTrue(np.isfinite(metrics["loss"]))
                self.assertTrue(np.isfinite(metrics["gradient_norm"]))
                self.assertEqual(len(metrics["latent_mean"]), 32)
                self.assertEqual(len(metrics["latent_std"]), 32)
                self.assertEqual(len(metrics["covariance_spectrum"]), 32)
                self.assertTrue(np.isfinite(metrics["effective_rank"]))
                self.assertEqual(set(gradients), set(model.params))
                for key in model.params:
                    np.testing.assert_array_equal(model.params[key], before[key])
                    self.assertTrue(np.all(np.isfinite(gradients[key])))
                expected = {
                    "multi-step-jepa": (11_906, 6_368),
                    "single-pair-jepa": (11_906, 6_368),
                    "recursive-raw-state": (18_440, 0),
                    "value-only-latent-rollout": (11_906, 0),
                    "direct-leaf-value": (8_546, 0),
                    "single-horizon-jepa": (11_906, 6_368),
                }[arm]
                self.assertEqual(model.parameter_counts()["online"], expected[0])
                self.assertEqual(model.parameter_counts()["ema_target"], expected[1])
                if arm == "direct-leaf-value":
                    self.assertNotIn("fw", model.params)
                    self.assertEqual(metrics["extra_leaf_encoder_calls"], 3)
                if arm == "recursive-raw-state":
                    self.assertEqual(model.parameter_counts()["online"], 18_440)
                    self.assertEqual(model.parameter_counts()["ema_target"], 0)

    def test_pooled_losses_match_v05_formula_on_uneven_masks(self):
        batch = synthetic_batch()
        batch["target_exists"][0, 3] = False
        batch["transition_exists"][0, 3] = False
        batch["transition_valid"][0, 3] = False
        batch["actions"][0, 3] = 0.0
        batch["actors"][0, 3] = 0.0
        model = V212Model(V212Config(arm="recursive-raw-state", seed=31))
        metrics, _ = model.loss_grad(batch)
        p = model.params
        z = model._encode(batch["x"])
        descriptors = batch["x"][:, 192:198]
        predictions = {}
        values = {}
        for step in range(4):
            if step == 3:
                rows = np.asarray([1, 2])
            else:
                rows = np.arange(3)
            inp = model._predictor_input(z[rows], batch["actions"][rows, step],
                                         batch["actors"][rows, step], descriptors[rows])
            zpred = np.tanh(inp @ p["fw"] + p["fb"])
            xpred = zpred @ p["dw"] + p["db"]
            z = z.copy()
            z[rows] = np.tanh(xpred @ p["ew"] + p["eb"])
            if step + 1 in (1, 2, 4):
                prediction_full = np.zeros((3, 198))
                value_full = np.zeros(3)
                prediction_full[rows] = xpred
                value_full[rows] = model._value(z[rows])[:, 0]
                predictions[step + 1] = prediction_full
                values[step + 1] = value_full
        masks = {1: np.ones(3, dtype=bool), 2: np.ones(3, dtype=bool),
                 4: np.asarray([False, True, True])}
        weights = {1: 1.0, 2: 0.5, 4: 0.25}
        den = sum(weights[h] * int(mask.sum()) for h, mask in masks.items())
        raw_expected = sum(
            weights[h] * np.sum(np.mean((predictions[h][masks[h]]
                                         - batch["future_x"][masks[h], h - 1]) ** 2, axis=1))
            for h in (1, 2, 4)) / den
        outcome_expected = sum(
            weights[h] * np.sum((values[h][masks[h]]
                                 - batch["future_value"][masks[h], h - 1]) ** 2)
            for h in (1, 2, 4)) / den
        self.assertAlmostEqual(metrics["raw_state_loss"], raw_expected, places=12)
        self.assertAlmostEqual(metrics["rollout_value_mse"], outcome_expected, places=12)

    def test_jepa_latent_loss_averages_coordinates_and_pools_targets(self):
        batch = synthetic_batch()
        model = V212Model(V212Config(arm="multi-step-jepa", seed=23))
        metrics, _ = model.loss_grad(batch)
        p = model.params
        descriptors = batch["x"][:, 192:198]
        z = model._encode(batch["x"])
        predicted = {}
        for step in range(4):
            inp = model._predictor_input(z, batch["actions"][:, step],
                                         batch["actors"][:, step], descriptors)
            z = np.tanh(inp @ p["fw"] + p["fb"])
            if step + 1 in (1, 2, 4):
                predicted[step + 1] = z
        weights = {1: 1.0, 2: 0.5, 4: 0.25}
        denominator = len(batch["x"]) * sum(weights.values())
        expected = sum(
            weights[h] * np.sum(np.mean((predicted[h]
                                         - model._encode(batch["future_x"][:, h - 1], target=True)) ** 2,
                                        axis=1))
            for h in (1, 2, 4)) / denominator
        self.assertAlmostEqual(metrics["latent_roll_loss"], expected, places=12)

    def test_pooled_mask_counts_and_invalid_fixed_transition_reject(self):
        batch = synthetic_batch()
        batch["terminal"][0, 0] = True
        batch["target_exists"][0, 1:] = False
        batch["transition_exists"][0, 1:] = False
        batch["transition_valid"][0, 1:] = False
        batch["actions"][0, 1:] = 0.0
        batch["actors"][0, 1:] = 0.0
        batch["target_exists"][1, 3] = False
        batch["transition_exists"][1, 3] = False
        batch["transition_valid"][1, 3] = False
        batch["actions"][1, 3] = 0.0
        batch["actors"][1, 3] = 0.0
        result = preflight_batch(batch)
        self.assertEqual(result["counts"][1]["terminal_masked"], 1)
        self.assertEqual(result["counts"][4]["terminal_masked"], 1)
        self.assertEqual(result["counts"][4]["missing_or_truncated"], 1)
        batch["transition_valid"][1, 2] = False
        result = preflight_batch(batch)
        self.assertEqual(result["counts"][1]["invalid_transition"], 0)
        self.assertEqual(result["counts"][4]["invalid_transition"], 1)
        with self.assertRaisesRegex(ValueError, "invalid selected transition"):
            V212Model().loss_grad(batch)

    def test_terminal_and_truncated_rows_skip_future_model_operations(self):
        batch = synthetic_batch()
        batch["terminal"][0, 0] = True
        batch["target_exists"][0, 1:] = False
        batch["transition_exists"][0, 1:] = False
        batch["transition_valid"][0, 1:] = False
        batch["actions"][0, 1:] = 0.0
        batch["actors"][0, 1:] = 0.0
        batch["target_exists"][1, 3] = False
        batch["transition_exists"][1, 3] = False
        batch["transition_valid"][1, 3] = False
        batch["actions"][1, 3] = 0.0
        batch["actors"][1, 3] = 0.0
        metrics, _ = V212Model(V212Config(arm="recursive-raw-state")).loss_grad(batch)
        self.assertEqual(metrics["executed_predictor_calls"], 6)
        self.assertEqual(metrics["executed_decoder_reencoder_calls"], 6)

    def test_valid_endpoint_keeps_intermediate_prediction_active_without_target(self):
        batch = synthetic_batch()
        # A later exact target can be valid even when an intermediate target
        # is not supervised. The model still needs every transition in its
        # prefix to compute that endpoint prediction.
        batch["target_exists"][0, 2] = False
        masks = preflight_batch(batch)
        self.assertTrue(masks["valid"][4][0])
        self.assertTrue(all(masks["active"][step][0] for step in range(1, 5)))

        for arm in ARMS:
            if arm == "direct-leaf-value":
                continue
            with self.subTest(arm=arm):
                metrics, _ = V212Model(V212Config(arm=arm, seed=31)).loss_grad(batch)
                self.assertEqual(metrics["executed_predictor_calls"], 12)
                if arm == "recursive-raw-state":
                    self.assertEqual(metrics["executed_decoder_reencoder_calls"], 12)
                    self.assertNotEqual(metrics["raw_state_loss_by_horizon"][4], 0.0)

    def test_sampled_gradients_match_finite_difference(self):
        batch = synthetic_batch()
        for arm, key, index in (
            ("multi-step-jepa", "fw", (3, 4)),
            ("recursive-raw-state", "dw", (2, 5)),
            ("value-only-latent-rollout", "vw", (7, 0)),
            ("direct-leaf-value", "ew", (12, 3)),
            ("single-pair-jepa", "fw", (0, 1)),
            ("single-horizon-jepa", "fw", (4, 2)),
        ):
            with self.subTest(arm=arm):
                model = V212Model(V212Config(arm=arm, seed=9))
                metrics, gradients = model.loss_grad(batch)
                original = model.params[key][index]
                epsilon = 1e-6
                model.params[key][index] = original + epsilon
                plus = model.loss_grad(batch)[0]["loss"]
                model.params[key][index] = original - epsilon
                minus = model.loss_grad(batch)[0]["loss"]
                model.params[key][index] = original
                numeric = (plus - minus) / (2.0 * epsilon)
                analytic = gradients[key][index]
                self.assertAlmostEqual(analytic, numeric, delta=2e-5)


if __name__ == "__main__":
    unittest.main()

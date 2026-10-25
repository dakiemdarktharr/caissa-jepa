import unittest

import numpy as np

from two_player.v212_model import ARMS, EMA_ARMS
from two_player.v212_scratch_optimizer import (
    ADAM_EPSILON,
    BETA1,
    BETA2,
    EMA_DECAY,
    GRADIENT_CLIP_NORM,
    LEARNING_RATE,
    scratch_adam_ema_step,
)


class V212ScratchOptimizerTests(unittest.TestCase):
    def test_ema_target_routing_contract_covers_all_frozen_arms(self):
        params = {"ew": np.ones(2), "eb": np.ones(1)}
        grads = {key: np.ones_like(value) for key, value in params.items()}
        zeros = {key: np.zeros_like(value) for key, value in params.items()}
        target = {key: value.copy() for key, value in params.items()}
        for arm in ARMS:
            with self.subTest(arm=arm):
                arm_target = target if arm in EMA_ARMS else {}
                result = scratch_adam_ema_step(arm, params, grads, zeros, zeros,
                                               1, arm_target)
                self.assertEqual(set(result["target"]), set(arm_target))
        for arm in EMA_ARMS:
            with self.subTest(arm=arm, missing_ema=True):
                with self.assertRaisesRegex(ValueError, "EMA contract"):
                    scratch_adam_ema_step(arm, params, grads, zeros, zeros, 1, {})
        for arm in set(ARMS) - set(EMA_ARMS):
            with self.subTest(arm=arm, unexpected_ema=True):
                with self.assertRaisesRegex(ValueError, "EMA contract"):
                    scratch_adam_ema_step(arm, params, grads, zeros, zeros, 1,
                                          target)

    def test_one_step_matches_v05_adam_ema_equations_and_preserves_inputs(self):
        params = {"ew": np.asarray([1.0, -2.0]), "eb": np.asarray([0.5])}
        grads = {"ew": np.asarray([2.0, -1.0]), "eb": np.asarray([0.25])}
        first = {key: np.zeros_like(value) for key, value in params.items()}
        second = {key: np.zeros_like(value) for key, value in params.items()}
        target = {"ew": np.asarray([0.9, -1.9]), "eb": np.asarray([0.4])}
        before = [group[key].copy() for group in (params, grads, first, second, target)
                  for key in group]

        result = scratch_adam_ema_step("multi-step-jepa", params, grads, first,
                                       second, 1, target)
        norm = np.sqrt(sum(np.sum(value ** 2) for value in grads.values()))
        scale = min(1.0, GRADIENT_CLIP_NORM / norm)
        for key in params:
            clipped = grads[key] * scale
            m = (1.0 - BETA1) * clipped
            v = (1.0 - BETA2) * clipped ** 2
            expected = params[key] - LEARNING_RATE * (m / (1.0 - BETA1)) / (
                np.sqrt(v / (1.0 - BETA2)) + ADAM_EPSILON)
            np.testing.assert_allclose(result["parameters"][key], expected)
            np.testing.assert_allclose(result["first_moment"][key], m)
            np.testing.assert_allclose(result["second_moment"][key], v)
            np.testing.assert_allclose(
                result["target"][key],
                EMA_DECAY * target[key] + (1.0 - EMA_DECAY) * expected)
        self.assertAlmostEqual(result["gradient_norm"], norm)
        self.assertEqual(result["clip_scale"], scale)
        self.assertEqual(result["step"], 1)
        after = [group[key] for group in (params, grads, first, second, target)
                 for key in group]
        for old, new in zip(before, after):
            np.testing.assert_array_equal(old, new)

    def test_clips_global_norm_and_computes_multiple_step_bias_correction(self):
        params = {"w": np.asarray([1.0, -1.0])}
        grads = {"w": np.asarray([6.0, 8.0])}
        zeros = {"w": np.zeros(2)}
        result = scratch_adam_ema_step("recursive-raw-state", params, grads,
                                       zeros, zeros, 3, {})
        self.assertAlmostEqual(result["gradient_norm"], 10.0)
        self.assertAlmostEqual(result["clip_scale"], 0.5)
        clipped = grads["w"] * 0.5
        m = (1.0 - BETA1) * clipped
        v = (1.0 - BETA2) * clipped ** 2
        expected = params["w"] - LEARNING_RATE * (m / (1.0 - BETA1 ** 3)) / (
            np.sqrt(v / (1.0 - BETA2 ** 3)) + ADAM_EPSILON)
        np.testing.assert_allclose(result["parameters"]["w"], expected)
        self.assertEqual(result["target"], {})

    def test_rejects_bad_steps_keys_shapes_nonfinite_and_negative_variance(self):
        params = {"ew": np.ones(2), "eb": np.ones(1)}
        grads = {key: np.ones_like(value) for key, value in params.items()}
        zeros = {key: np.zeros_like(value) for key, value in params.items()}
        target = {"ew": np.ones(2), "eb": np.ones(1)}
        cases = (
            (lambda: scratch_adam_ema_step("multi-step-jepa", params, grads,
                                           zeros, zeros, 0, target),
             ValueError),
            (lambda: scratch_adam_ema_step("multi-step-jepa", params,
                                           {"ew": grads["ew"]}, zeros, zeros,
                                           1, target), ValueError),
            (lambda: scratch_adam_ema_step("multi-step-jepa", params,
                                           {"ew": np.ones(3), "eb": grads["eb"]},
                                           zeros, zeros, 1, target), ValueError),
            (lambda: scratch_adam_ema_step("multi-step-jepa", params,
                                           {"ew": np.asarray([np.nan, 1.0]),
                                            "eb": grads["eb"]}, zeros, zeros,
                                           1, target), FloatingPointError),
            (lambda: scratch_adam_ema_step("multi-step-jepa", params, grads,
                                           zeros,
                                           {"ew": -np.ones(2), "eb": zeros["eb"]},
                                           1, target), ValueError),
            (lambda: scratch_adam_ema_step("multi-step-jepa", params, grads,
                                           zeros, zeros, 1,
                                           {"ew": target["ew"]}), ValueError),
            (lambda: scratch_adam_ema_step("recursive-raw-state", params, grads,
                                           zeros, zeros, 1, target), ValueError),
            (lambda: scratch_adam_ema_step("unknown", params, grads, zeros,
                                           zeros, 1, target), ValueError),
        )
        for run, exception in cases:
            with self.subTest(exception=exception):
                with self.assertRaises(exception):
                    run()


if __name__ == "__main__":
    unittest.main()

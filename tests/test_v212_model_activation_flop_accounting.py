import ast
from pathlib import Path
import unittest

import numpy as np

from tools.v212_model_activation_flop_accounting import (
    ARMS, full_valid_batch, inventory,
)


class ModelActivationFlopAccountingTests(unittest.TestCase):
    def test_fully_valid_six_arm_counts(self):
        expected = {
            "multi-step-jepa": (20_800, 16_640, 31_488),
            "single-pair-jepa": (16_704, 12_544, 31_488),
            "recursive-raw-state": (73_536, 18_688, 56_064),
            "value-only-latent-rollout": (14_656, 10_496, 31_488),
            "direct-leaf-value": (8_384, 4_224, 12_672),
            "single-horizon-jepa": (16_704, 12_544, 31_488),
        }
        for arm in ARMS:
            with self.subTest(arm=arm):
                report = full_valid_batch(arm)
                self.assertEqual((report["bias_addition_flops"],
                                  report["tanh_calls_element_count"],
                                  report["tanh_derivative_flops"]),
                                 expected[arm])
                self.assertEqual(report["tanh_derivative_flops"],
                                 3 * sum(report["tanh_derivative_elements_by_call_site"].values()))

    def test_masked_rows_reduce_activations_and_bias_work(self):
        masks = {
            1: np.arange(64) < 4,
            2: np.arange(64) < 2,
            4: np.arange(64) < 1,
        }
        report = inventory("recursive-raw-state", masks)
        self.assertEqual(report["active_prefix_rows"], {1: 4, 2: 2, 3: 1, 4: 1})
        self.assertEqual(report["bias_additions_by_call_site"]["raw_decoder_step_3"],
                         198)
        self.assertEqual(report["tanh_elements_by_call_site"]["predictor_step_4"],
                         32)

    def test_source_tanh_sites_match_the_counted_families(self):
        model_path = Path(__file__).resolve().parents[1] / "two_player" / "v212_model.py"
        tree = ast.parse(model_path.read_text(encoding="utf-8"))
        sites = sorted(
            ast.unparse(node.func)
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "np"
            and node.func.attr == "tanh"
        )
        self.assertEqual(sites, ["np.tanh"] * 4)


if __name__ == "__main__":
    unittest.main()

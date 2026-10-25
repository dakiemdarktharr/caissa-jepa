import ast
from pathlib import Path
import unittest

import numpy as np

from tools.v212_model_square_flop_accounting import (
    ARMS, full_valid_batch, inventory,
)


class ModelSquareFlopAccountingTests(unittest.TestCase):
    def test_full_valid_six_arm_square_operation_totals(self):
        expected = {
            "multi-step-jepa": 38_242,
            "single-pair-jepa": 30_050,
            "recursive-raw-state": 116_712,
            "value-only-latent-rollout": 25_954,
            "direct-leaf-value": 16_002,
            "single-horizon-jepa": 30_050,
        }
        for arm in ARMS:
            with self.subTest(arm=arm):
                report = full_valid_batch(arm)
                self.assertEqual(report["candidate_square_multiplications"], expected[arm])
                self.assertEqual(report["source_square_site_count"], 20)
                self.assertEqual(
                    report["candidate_square_multiplications"],
                    sum(report["square_multiplication_elements_by_site"].values()),
                )

    def test_masks_control_loss_and_shared_prefix_squares(self):
        masks = {
            1: np.arange(64) < 4,
            2: np.arange(64) < 2,
            4: np.arange(64) < 1,
        }
        report = inventory("recursive-raw-state", masks)
        sites = report["square_multiplication_elements_by_site"]
        self.assertEqual(report["active_prefix_rows"], {1: 4, 2: 2, 3: 1, 4: 1})
        self.assertEqual(sites["raw_state_h2.per_horizon_mse"], 2 * 198)
        self.assertEqual(sites["raw_state_h2.pooled_loss"], 2 * 198)
        self.assertEqual(sites["raw_state_reverse.step_3.predictor_tanh_derivative"], 32)
        self.assertEqual(sites["diagnostic.gradient_norm_parameter_squares"], 18_440)

    def test_ast_square_sites_are_explicitly_versioned(self):
        model_path = Path(__file__).resolve().parents[1] / "two_player" / "v212_model.py"
        tree = ast.parse(model_path.read_text(encoding="utf-8"))
        square_nodes = [
            node for node in ast.walk(tree)
            if isinstance(node, ast.BinOp)
            and isinstance(node.op, ast.Pow)
            and isinstance(node.right, ast.Constant)
            and type(node.right.value) is int
            and node.right.value == 2
        ]
        self.assertEqual(len(square_nodes), 20)
        self.assertEqual(
            sorted(ast.unparse(node.left) for node in square_nodes),
            sorted([
                "centered", "shortfall", "offdiag", "root_delta",
                "root_value[:, None]", "delta", "pred[:, None]", "leaf_z",
                "delta", "delta", "pred_value[:, None]", "delta", "delta",
                "delta", "delta", "znext", "pred_z", "states[step][rows]",
                "z0", "g",
            ]),
        )

    def test_rejects_malformed_masks(self):
        with self.assertRaises(ValueError):
            inventory("unknown-arm", {})
        with self.assertRaises(ValueError):
            inventory("multi-step-jepa", {1: np.ones(64, dtype=bool)})


if __name__ == "__main__":
    unittest.main()

import ast
from pathlib import Path
import unittest

import numpy as np

from tools.v212_model_loss_residual_accounting import (
    ARMS, full_valid_batch, inventory,
)


class ModelLossResidualAccountingTests(unittest.TestCase):
    def test_full_valid_six_arm_residual_and_square_shapes(self):
        expected = {
            "multi-step-jepa": (6400, 12736),
            "single-pair-jepa": (2304, 4544),
            "recursive-raw-state": (38272, 76480),
            "value-only-latent-rollout": (256, 448),
            "direct-leaf-value": (128, 128),
            "single-horizon-jepa": (2304, 4544),
        }
        for arm in ARMS:
            with self.subTest(arm=arm):
                report = full_valid_batch(arm)
                self.assertEqual((report["residual_subtraction_flops"],
                                  report["square_operation_elements"]),
                                 expected[arm])
                self.assertEqual(
                    report["flops_if_each_square_is_counted_as_one_multiply"],
                    sum(expected[arm]))

    def test_masks_control_each_horizon_shape(self):
        masks = {
            1: np.arange(64) < 4,
            2: np.arange(64) < 2,
            4: np.arange(64) < 1,
        }
        report = inventory("recursive-raw-state", masks)
        self.assertEqual(report["residual_subtractions_by_loss_site"], {
            "root_value": 64,
            "rollout_value_h1": 4,
            "rollout_value_h2": 2,
            "rollout_value_h4": 1,
            "raw_state_h1": 4 * 198,
            "raw_state_h2": 2 * 198,
            "raw_state_h4": 198,
        })
        self.assertEqual(report["square_operation_elements"],
                         64 + 2 * (4 + 2 + 1) + 2 * 198 * (4 + 2 + 1))

    def test_current_loss_square_sites_remain_in_source(self):
        model_path = Path(__file__).resolve().parents[1] / "two_player" / "v212_model.py"
        tree = ast.parse(model_path.read_text(encoding="utf-8"))
        square_sites = {"root_loss", "leaf_loss", "outcome_by_horizon",
                        "outcome_loss", "raw_by_horizon", "raw_loss",
                        "latent_by_horizon", "rollout_loss"}
        found = set()
        for node in ast.walk(tree):
            if not isinstance(node, (ast.Assign, ast.AugAssign)):
                continue
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            names = set()
            for target in targets:
                if isinstance(target, ast.Name):
                    names.add(target.id)
                elif isinstance(target, ast.Subscript) and isinstance(target.value, ast.Name):
                    names.add(target.value.id)
            if names & square_sites and any(
                    isinstance(child, ast.BinOp) and isinstance(child.op, ast.Pow)
                    for child in ast.walk(node.value)):
                found.update(names & square_sites)
        self.assertEqual(found, square_sites)

    def test_rejects_malformed_inputs(self):
        with self.assertRaises(ValueError):
            inventory("not-an-arm", {})
        with self.assertRaises(ValueError):
            inventory("multi-step-jepa", {1: np.ones(64, dtype=bool)})


if __name__ == "__main__":
    unittest.main()

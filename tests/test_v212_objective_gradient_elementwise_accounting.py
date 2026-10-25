import ast
from pathlib import Path
import unittest

import numpy as np

from tools.v212_objective_gradient_elementwise_accounting import accounting, inventory


class ObjectiveGradientElementwiseAccountingTests(unittest.TestCase):
    def test_full_valid_panel_counts_enabled_target_dimensions(self):
        self.assertEqual(accounting()["panel_total_multiplications_per_arm"], {
            "multi-step-jepa": 3 * 64 * 32,
            "single-pair-jepa": 64 * 32,
            "recursive-raw-state": 3 * 64 * 198,
            "value-only-latent-rollout": 0,
            "direct-leaf-value": 0,
            "single-horizon-jepa": 64 * 32,
        })

    def test_partial_masks_count_only_enabled_valid_rows(self):
        masks = {
            1: np.array([True, False] * 32),
            2: np.array([True] * 8 + [False] * 56),
            4: np.array([True] + [False] * 63),
        }
        raw = inventory("recursive-raw-state", masks)
        self.assertEqual(raw["candidate_multiplications_by_horizon"], {
            1: 32 * 198, 2: 8 * 198, 4: 198,
        })
        latent = inventory("single-pair-jepa", masks)
        self.assertEqual(latent["candidate_multiplications_by_horizon"], {2: 8 * 32})

    def test_source_target_gradient_sites_match_inventory(self):
        source = Path("two_player/v212_model.py").read_text(encoding="utf-8")
        module = ast.parse(source)
        loss_grad = next(
            node for node in ast.walk(module)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name == "loss_grad"
        )
        normalized = ast.unparse(loss_grad)
        for fragment in (
            "raw_feature_grads[horizon - 1][mask] += 2.0 * scale / FEATURE_SIZE * delta",
            "dstate[horizon][mask] += 2.0 * scale / d * delta",
        ):
            self.assertIn(fragment, normalized)

    def test_direct_leaf_h4_guard_is_required(self):
        masks = {h: np.ones(64, dtype=bool) for h in (1, 2, 4)}
        masks[4][:] = False
        with self.assertRaisesRegex(ValueError, "valid H4"):
            inventory("direct-leaf-value", masks)


if __name__ == "__main__":
    unittest.main()

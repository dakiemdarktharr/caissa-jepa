import ast
from pathlib import Path
import unittest

import numpy as np

from tools.v212_objective_scalar_accounting import accounting, inventory
from tools.v212_model_matmul_flop_accounting import ARMS


class ObjectiveScalarAccountingTests(unittest.TestCase):
    def test_full_valid_panel_is_deterministic(self):
        result = accounting()
        self.assertEqual(result["panel_total_operations_per_arm"], {
            "multi-step-jepa": 42,
            "single-pair-jepa": 28,
            "recursive-raw-state": 42,
            "value-only-latent-rollout": 21,
            "direct-leaf-value": 2,
            "single-horizon-jepa": 28,
        })

    def test_sparse_masks_select_only_nonempty_horizons(self):
        masks = {
            1: np.array([True, False] * 32),
            2: np.zeros(64, dtype=bool),
            4: np.array([False, True] * 32),
        }
        result = inventory("single-pair-jepa", masks)
        self.assertEqual(result["valid_rows_by_horizon"], {1: 32, 2: 0, 4: 32})
        self.assertEqual(result["candidate_fp_scalar_operations_per_invocation"], {
            "denominator_weight_multiplications": 4,
            "denominator_python_sum_additions": 4,
            "per_horizon_scale_divisions": 2,
            "pooled_loss_scalar_multiplications": 2,
            "pooled_loss_accumulation_additions": 2,
            "gradient_coefficient_scalar_multiplications": 2,
            "gradient_coefficient_scalar_divisions": 0,
            "combined_objective_additions": 3,
        })

    def test_fixed_64_row_contract_rejects_other_sizes(self):
        masks = {h: np.ones(63, dtype=bool) for h in (1, 2, 4)}
        with self.assertRaises(ValueError):
            inventory(ARMS[0], masks)

    def test_direct_leaf_requires_a_valid_h4_row(self):
        masks = {h: np.ones(64, dtype=bool) for h in (1, 2, 4)}
        masks[4][:] = False
        with self.assertRaisesRegex(ValueError, "valid H4"):
            inventory("direct-leaf-value", masks)

    def test_source_anchors_still_match_counted_scalar_sites(self):
        source = Path("two_player/v212_model.py").read_text(encoding="utf-8")
        module = ast.parse(source)
        loss_grad = next(
            node for node in ast.walk(module)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name == "loss_grad"
        )
        normalized = ast.unparse(loss_grad)
        for fragment in (
            "outcome_den = sum(",
            "target_den = sum(",
            "scale = weight / outcome_den",
            "scale = weight / target_den",
            "outcome_loss += scale * float(np.sum(delta ** 2))",
            "rollout_loss += scale * float(np.sum(delta ** 2) / d)",
            "raw_loss += scale * float(np.sum(delta ** 2) / FEATURE_SIZE)",
            "2.0 * scale / FEATURE_SIZE",
            "2.0 * scale / d",
            "total += outcome_loss + rollout_loss + raw_loss",
            "2.0 / len(pred)",
            "total += leaf_loss",
        ):
            self.assertIn(fragment, normalized)


if __name__ == "__main__":
    unittest.main()

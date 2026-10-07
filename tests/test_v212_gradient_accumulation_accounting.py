import ast
from pathlib import Path
import unittest

import numpy as np

from tools.v212_gradient_accumulation_accounting import accounting, inventory


class GradientAccumulationAccountingTests(unittest.TestCase):
    def test_full_valid_panel_counts_each_arm(self):
        result = accounting()
        self.assertEqual(result["panel_total_additions_per_arm"], {
            "multi-step-jepa": 48709,
            "single-pair-jepa": 44613,
            "recursive-raw-state": 182877,
            "value-only-latent-rollout": 42565,
            "direct-leaf-value": 19043,
            "single-horizon-jepa": 44613,
        })

    def test_active_prefix_uses_union_of_valid_longer_horizons(self):
        masks = {
            1: np.array([True, False] * 32),
            2: np.array([True, False] * 32),
            4: np.array([True] + [False] * 63),
        }
        result = inventory("multi-step-jepa", masks)
        self.assertEqual(result["active_prefix_rows_by_step"], {
            1: 32, 2: 32, 3: 1, 4: 1,
        })
        counts = result["candidate_array_additions_per_invocation"]
        self.assertEqual(counts["latent_target_state_gradient_accumulation_additions"],
                         (32 + 32 + 1) * 32)
        self.assertEqual(counts["recurrent_state_gradient_accumulation_additions"],
                         (32 + 32 + 1 + 1) * 32)

    def test_raw_state_counts_predictor_parameter_buffer_updates(self):
        masks = {h: np.ones(64, dtype=bool) for h in (1, 2, 4)}
        counts = inventory("recursive-raw-state", masks)[
            "candidate_array_additions_per_invocation"
        ]
        self.assertEqual(counts["recurrent_parameter_gradient_buffer_additions"],
                         4 * (2 * 198 * 32 + 198 + 32 + 104 * 32 + 32))

    def test_direct_leaf_requires_valid_h4(self):
        masks = {h: np.ones(64, dtype=bool) for h in (1, 2, 4)}
        masks[4][:] = False
        with self.assertRaisesRegex(ValueError, "valid H4"):
            inventory("direct-leaf-value", masks)

    def test_source_augmented_assignments_match_coverage(self):
        source = Path("two_player/v212_model.py").read_text(encoding="utf-8")
        module = ast.parse(source)
        loss_grad = next(
            node for node in ast.walk(module)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name == "loss_grad"
        )
        normalized = ast.unparse(loss_grad)
        for fragment in (
            "grad['pw'] += z0.T @ dlogits",
            "grad['pb'] += dlogits.sum(axis=0)",
            "dz0 += dlogits @ p['pw'].T",
            "grad['vw'] += z0.T @ droot",
            "grad['vb'] += droot.sum(axis=0)",
            "dz0 += droot @ p['vw'].T",
            "grad['vw'] += leaf_z.T @ dv",
            "grad['ew'] += leaf_x.T @ dz",
            "dstate[h][mask] += dv @ p['vw'].T",
            "raw_feature_grads[horizon - 1][mask] +=",
            "dstate[horizon][mask] +=",
            "dxhat = raw_feature_grads[step - 1][rows] + de @ p['ew'].T",
            "grad['fw'] += inputs[step - 1].T @ dpre",
            "dstate[step - 1][rows] += dpre @ p['fw'][:d].T",
            "dz0 += dstate[0]",
            "grad['ew'] += x.T @ enc_delta",
        ):
            self.assertIn(fragment, normalized)


if __name__ == "__main__":
    unittest.main()

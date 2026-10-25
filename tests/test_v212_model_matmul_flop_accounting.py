import ast
from pathlib import Path
import unittest

import numpy as np

from tools.v212_arm_dense_forward_macs_audit import inventory as forward_inventory
from tools.v212_model_matmul_flop_accounting import (
    ARMS, full_valid_batch, inventory,
)


class ModelMatmulFlopAccountingTests(unittest.TestCase):
    def test_full_valid_projection_forward_matches_static_mac_inventory(self):
        reference = forward_inventory()["arm_dense_forward_macs"]
        expected_all = {
            "multi-step-jepa": 9_097_216,
            "single-pair-jepa": 7_475_200,
            "recursive-raw-state": 26_128_384,
            "value-only-latent-rollout": 6_664_192,
            "direct-leaf-value": 4_329_472,
            "single-horizon-jepa": 7_475_200,
        }
        for arm in ARMS:
            with self.subTest(arm=arm):
                report = full_valid_batch(arm)
                self.assertEqual(report["projection_forward_macs"],
                                 64 * reference[arm])
                self.assertEqual(report["projection_forward_flops"],
                                 2 * report["projection_forward_macs"])
                self.assertEqual(report["all_explicit_matmul_flops"],
                                 expected_all[arm])
                self.assertEqual(report["covariance_matmul_flops"],
                                 262_144)

    def test_source_matmul_sites_match_the_counted_call_families(self):
        model_path = Path(__file__).resolve().parents[1] / "two_player" / "v212_model.py"
        tree = ast.parse(model_path.read_text(encoding="utf-8"))
        expressions = sorted(
            ast.unparse(node)
            for node in ast.walk(tree)
            if isinstance(node, ast.BinOp) and isinstance(node.op, ast.MatMult)
        )
        expected = sorted((
            "centered.T @ centered", "4.0 * centered @ offdiag",
            "x @ p['ew']", "z @ p['vw']", "z0 @ p['pw']",
            "z0.T @ dlogits", "dlogits @ p['pw'].T", "z0.T @ droot",
            "droot @ p['vw'].T", "x.T @ enc_delta", "leaf_z.T @ dv",
            "dv @ p['vw'].T", "dv @ p['vw'].T", "leaf_x.T @ dz",
            "inputs[step - 1].T @ dpre",
            "dpre @ p['fw'][:d].T", "inp @ p['fw']", "states[h][mask].T @ dv",
            "xhat.T @ de", "pred_z.T @ dxhat", "de @ p['ew'].T",
            "dxhat @ p['dw'].T", "pred_z @ p['dw']", "xhat @ p['ew']",
        ))
        self.assertEqual(expressions, expected)

    def test_masked_rows_drive_shared_prefix_and_target_matmuls(self):
        masks = {
            1: np.arange(64) < 4,
            2: np.arange(64) < 2,
            4: np.arange(64) < 1,
        }
        raw = inventory("recursive-raw-state", masks)
        self.assertEqual(raw["horizon_valid_rows"], {1: 4, 2: 2, 4: 1})
        self.assertEqual(raw["active_prefix_rows"], {1: 4, 2: 2, 3: 1, 4: 1})
        self.assertEqual(raw["matmul_macs_by_call_site"]["raw_decoder_forward_step_3"],
                         32 * 198)
        self.assertEqual(raw["matmul_macs_by_call_site"]["raw_decoder_forward_step_4"],
                         32 * 198)

        jepa = inventory("multi-step-jepa", masks)
        self.assertEqual(jepa["matmul_macs_by_call_site"]["ema_target_encoder_forward_h1"],
                         4 * 198 * 32)
        self.assertEqual(jepa["matmul_macs_by_call_site"]["ema_target_encoder_forward_h2"],
                         2 * 198 * 32)
        self.assertEqual(jepa["matmul_macs_by_call_site"]["ema_target_encoder_forward_h4"],
                         198 * 32)

    def test_rejects_unknown_arm_and_malformed_masks(self):
        masks = {h: np.ones(64, dtype=bool) for h in (1, 2, 4)}
        with self.assertRaises(ValueError):
            inventory("unknown", masks)
        with self.assertRaises(ValueError):
            inventory("multi-step-jepa", {1: masks[1], 2: masks[2]})
        with self.assertRaises(ValueError):
            inventory("multi-step-jepa", {1: np.ones(63, dtype=bool),
                                           2: masks[2], 4: masks[4]})
        with self.assertRaises(ValueError):
            inventory("multi-step-jepa", {1: np.ones(64, dtype=int),
                                           2: masks[2], 4: masks[4]})


if __name__ == "__main__":
    unittest.main()

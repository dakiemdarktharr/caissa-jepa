import ast
from pathlib import Path
import unittest

import numpy as np

from tools.v212_model_reduction_shape_accounting import (
    ARMS, full_valid_batch, inventory,
)


class ModelReductionShapeAccountingTests(unittest.TestCase):
    def test_full_valid_recurrent_arms_keep_duplicate_softmax_sums(self):
        expected = {
            "multi-step-jepa": (58_506, 137),
            "single-pair-jepa": (50_318, 135),
            "recursive-raw-state": (186_744, 137),
            "value-only-latent-rollout": (46_224, 134),
            "direct-leaf-value": (36_375, 132),
            "single-horizon-jepa": (50_318, 135),
        }
        for arm in ARMS:
            with self.subTest(arm=arm):
                report = full_valid_batch(arm)
                self.assertEqual((report["candidate_pairwise_additions"],
                                  report["candidate_mean_divisions"]), expected[arm])
                sites = report["reduction_sites"]
                softmax = [row for row in sites if row["site"].startswith(
                    "policy.softmax_denominator_")]
                self.assertEqual(len(softmax), 2)
                self.assertEqual([row["candidate_pairwise_additions"]
                                  for row in softmax], [4096, 4096])
                std = report["latent_std_candidate_operations"]
                self.assertEqual(std["input_shape"], [64, 32])
                self.assertEqual(std["mean_reduction_additions"], 2016)
                self.assertEqual(std["mean_divisions"], 32)
                self.assertEqual(std["deviation_subtractions"], 2048)
                self.assertEqual(std["squared_deviation_square_operations"], 2048)
                self.assertEqual(std["squared_deviation_reduction_additions"], 2016)
                self.assertEqual(std["population_variance_divisions"], 32)
                self.assertEqual(std["sqrt_transcendentals"], 32)
                self.assertEqual(std["candidate_fp_add_subtract_multiply_divide"],
                                 8192)

    def test_direct_leaf_skips_recurrent_loss_reductions(self):
        report = full_valid_batch("direct-leaf-value")
        sites = {row["site"]: row for row in report["reduction_sites"]}
        self.assertEqual(sites["direct_leaf.mse_mean"]["calls"], 1)
        self.assertNotIn("outcome.h1.batch_mean", sites)
        self.assertNotIn("latent.h1.batch_mean", sites)
        self.assertEqual(sites["policy.bias_gradient_sum"]["calls"], 1)
        self.assertEqual(sites["root_value.bias_gradient_sum"]["calls"], 1)

    def test_horizon_masks_and_effective_rank_bound_change_counts(self):
        masks = {
            1: np.arange(64) < 4,
            2: np.arange(64) < 2,
            4: np.arange(64) < 1,
        }
        report = inventory("single-pair-jepa", masks,
                           effective_rank_active=True,
                           effective_rank_nonzero_eigenvalues=3)
        sites = {row["site"]: row for row in report["reduction_sites"]}
        self.assertEqual(sites["outcome.h1.batch_mean"]["calls"], 1)
        self.assertEqual(sites["outcome.h1.batch_mean"]["candidate_pairwise_additions"], 3)
        self.assertEqual(sites["latent.h2.batch_mean"]["input_elements_per_call"], 64)
        self.assertEqual(sites["regularizer.effective_rank_entropy_sum"][
            "candidate_pairwise_additions"], 2)
        self.assertEqual(report["horizon_valid_rows"], {1: 4, 2: 2, 4: 1})

    def test_rejects_invalid_masks_and_active_set_sizes(self):
        full = np.ones(64, dtype=bool)
        with self.assertRaises(ValueError):
            inventory("unknown", {})
        with self.assertRaises(ValueError):
            inventory("multi-step-jepa", {1: full})
        with self.assertRaises(ValueError):
            inventory("multi-step-jepa", {1: full, 2: full, 4: full},
                      effective_rank_nonzero_eigenvalues=33)

    def test_source_retains_two_softmax_denominator_reductions(self):
        model_path = Path(__file__).resolve().parents[1] / "two_player" / "v212_model.py"
        tree = ast.parse(model_path.read_text(encoding="utf-8"))
        calls = [node for node in ast.walk(tree)
                 if isinstance(node, ast.Call)
                 and isinstance(node.func, ast.Attribute)
                 and node.func.attr == "sum"
                 and isinstance(node.func.value, ast.Name)
                 and node.func.value.id == "exp_logits"]
        self.assertEqual(len(calls), 2)

        std_calls = [node for node in ast.walk(tree)
                     if isinstance(node, ast.Call)
                     and isinstance(node.func, ast.Attribute)
                     and node.func.attr == "std"
                     and isinstance(node.func.value, ast.Name)
                     and node.func.value.id == "z0"]
        self.assertEqual(len(std_calls), 1)
        self.assertEqual([(kw.arg, ast.literal_eval(kw.value))
                          for kw in std_calls[0].keywords], [("axis", 0)])


if __name__ == "__main__":
    unittest.main()

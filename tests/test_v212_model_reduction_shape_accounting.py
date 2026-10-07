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
            "multi-step-jepa": (58_507, 137),
            "single-pair-jepa": (50_319, 135),
            "recursive-raw-state": (186_745, 137),
            "value-only-latent-rollout": (46_225, 134),
            "direct-leaf-value": (36_376, 132),
            "single-horizon-jepa": (50_319, 135),
        }
        for arm in ARMS:
            with self.subTest(arm=arm):
                report = full_valid_batch(arm)
                self.assertEqual((report["candidate_additions"],
                                  report["candidate_mean_divisions"]), expected[arm])
                norm_sum = next(row for row in report["reduction_sites"]
                                if row["site"] ==
                                "diagnostic.gradient_norm_python_scalar_sum")
                self.assertEqual(norm_sum["candidate_additions"],
                                 norm_sum["input_elements_per_call"])
                self.assertEqual(norm_sum["candidate_additions"],
                                 report["gradient_tensor_count"])
                sites = report["reduction_sites"]
                softmax = [row for row in sites if row["site"].startswith(
                    "policy.softmax_denominator_")]
                self.assertEqual(len(softmax), 2)
                self.assertEqual([row["candidate_additions"]
                                  for row in softmax], [4096, 4096])
                owner_totals = report["candidate_addition_owner_totals"]
                self.assertEqual(owner_totals["reduction_inventory"],
                                 report["candidate_additions"] - 31)
                self.assertEqual(owner_totals["effective_rank_branch"], 31)
                self.assertEqual(sum(owner_totals.values()),
                                 report["candidate_additions"])
                self.assertEqual(report["candidate_mean_divisions_owner_total"],
                                 report["candidate_mean_divisions"])
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
                std_owners = std["owner_components"]
                self.assertEqual(std_owners["reduction_inventory_mean_additions"],
                                 2016)
                self.assertEqual(std_owners[
                    "reduction_inventory_squared_deviation_additions"], 2016)
                self.assertEqual(std_owners[
                    "reduction_inventory_internal_mean_divisions"], 32)
                self.assertEqual(std_owners["square_inventory_multiplications"],
                                 2048)
                self.assertEqual(std_owners[
                    "latent_std_elementwise_deviation_subtractions"], 2048)
                self.assertEqual(std_owners[
                    "latent_std_population_variance_divisions"], 32)
                self.assertEqual(std_owners["transcendental_sqrt_calls"], 32)

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
        self.assertEqual(sites["outcome.h1.batch_mean"]["candidate_additions"], 3)
        self.assertEqual(sites["latent.h2.batch_mean"]["input_elements_per_call"], 64)
        self.assertEqual(sites["regularizer.effective_rank_entropy_sum"][
            "candidate_additions"], 2)
        self.assertEqual(report["candidate_addition_owner_totals"][
            "effective_rank_branch"], 2)
        self.assertEqual(report["horizon_valid_rows"], {1: 4, 2: 2, 4: 1})

    def test_effective_rank_addition_has_one_owner_on_inactive_branch(self):
        full = np.ones(64, dtype=bool)
        masks = {h: full for h in (1, 2, 4)}
        active = inventory("multi-step-jepa", masks,
                           effective_rank_active=True,
                           effective_rank_nonzero_eigenvalues=7)
        inactive = inventory("multi-step-jepa", masks,
                             effective_rank_active=False,
                             effective_rank_nonzero_eigenvalues=0)
        self.assertEqual(active["candidate_addition_owner_totals"][
            "effective_rank_branch"], 6)
        self.assertEqual(inactive["candidate_addition_owner_totals"][
            "effective_rank_branch"], 0)
        self.assertEqual(active["candidate_addition_owner_totals"][
            "reduction_inventory"], inactive["candidate_addition_owner_totals"][
                "reduction_inventory"])
        for report in (active, inactive):
            self.assertEqual(sum(report["candidate_addition_owner_totals"].values()),
                             report["candidate_additions"])

    def test_rejects_invalid_masks_and_active_set_sizes(self):
        full = np.ones(64, dtype=bool)
        with self.assertRaises(ValueError):
            inventory("unknown", {})
        with self.assertRaises(ValueError):
            inventory("multi-step-jepa", {1: full})
        with self.assertRaises(ValueError):
            inventory("multi-step-jepa", {1: full, 2: full, 4: full},
                      effective_rank_nonzero_eigenvalues=33)
        with self.assertRaisesRegex(ValueError, "requires a selected eigenvalue"):
            inventory("multi-step-jepa", {1: full, 2: full, 4: full},
                      effective_rank_active=True,
                      effective_rank_nonzero_eigenvalues=0)

    def test_source_retains_two_softmax_denominator_reductions(self):
        model_path = Path(__file__).resolve().parents[1] / "two_player" / "v212_model.py"
        tree = ast.parse(model_path.read_text(encoding="utf-8"))
        constants = {
            node.targets[0].id: ast.literal_eval(node.value)
            for node in tree.body
            if isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id in {"LATENT_SIZE"}
        }
        self.assertEqual(constants["LATENT_SIZE"], 32)

        config = next(node for node in tree.body
                      if isinstance(node, ast.ClassDef)
                      and node.name == "V212Config")
        config_guard = next(node for node in ast.walk(config)
                            if isinstance(node, ast.Compare)
                            and ast.unparse(node) == "self.latent != LATENT_SIZE")
        self.assertIsNotNone(config_guard)
        encoder = next(node for node in ast.walk(tree)
                       if isinstance(node, ast.FunctionDef)
                       and node.name == "_encode")
        encoder_return = next(node for node in ast.walk(encoder)
                              if isinstance(node, ast.Return))
        self.assertEqual(ast.unparse(encoder_return.value),
                         "np.tanh(x @ p['ew'] + p['eb'])")
        model_class = next(node for node in tree.body
                           if isinstance(node, ast.ClassDef)
                           and node.name == "V212Model")
        model_init = next(node for node in model_class.body
                          if isinstance(node, ast.FunctionDef)
                          and node.name == "__init__")
        latent_binding = next(node for node in ast.walk(model_init)
                              if isinstance(node, ast.Assign)
                              and any(isinstance(target, ast.Name)
                                      and target.id == "d"
                                      for target in node.targets))
        self.assertEqual(ast.unparse(latent_binding.value), "config.latent")
        params_init = next(node for node in ast.walk(model_init)
                           if isinstance(node, ast.Assign)
                           and any(isinstance(target, ast.Attribute)
                                   and target.attr == "params"
                                   for target in node.targets)
                           and isinstance(node.value, ast.Dict))
        encoder_weight = next(value for key, value in
                              zip(params_init.value.keys,
                                  params_init.value.values)
                              if ast.literal_eval(key) == "ew")
        self.assertEqual(ast.unparse(encoder_weight),
                         "weight(FEATURE_SIZE, d)")
        loss_grad = next(node for node in ast.walk(tree)
                         if isinstance(node, ast.FunctionDef)
                         and node.name == "loss_grad")
        input_assignment = next(node for node in ast.walk(loss_grad)
                                if isinstance(node, ast.Assign)
                                and any(isinstance(target, ast.Name)
                                        and target.id == "x"
                                        for target in node.targets))
        self.assertEqual(ast.unparse(input_assignment.value),
                         "np.asarray(batch['x'], dtype=np.float64)")
        z0_assignment = next(node for node in ast.walk(loss_grad)
                             if isinstance(node, ast.Assign)
                             and any(isinstance(target, ast.Name)
                                     and target.id == "z0"
                                     for target in node.targets))
        self.assertEqual(ast.unparse(z0_assignment.value), "self._encode(x)")

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

        adapter_path = Path(__file__).resolve().parents[1] / "two_player" / "v212_window_batch.py"
        adapter_tree = ast.parse(adapter_path.read_text(encoding="utf-8"))
        batch_constants = {
            node.targets[0].id: ast.literal_eval(node.value)
            for node in adapter_tree.body
            if isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id == "TRAINING_BATCH_SIZE"
        }
        self.assertEqual(batch_constants["TRAINING_BATCH_SIZE"], 64)
        batch_guard = next(node for node in ast.walk(adapter_tree)
                           if isinstance(node, ast.Compare)
                           and ast.unparse(node) ==
                           "len(windows) != TRAINING_BATCH_SIZE")
        self.assertIsNotNone(batch_guard)

        gradient_norm = next(node for node in ast.walk(tree)
                             if isinstance(node, ast.Assign)
                             and any(isinstance(target, ast.Subscript)
                                     and isinstance(target.value, ast.Name)
                                     and target.value.id == "metrics"
                                     and isinstance(target.slice, ast.Constant)
                                     and target.slice.value == "gradient_norm"
                                     for target in node.targets))
        sums = [node for node in ast.walk(gradient_norm.value)
                if isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "sum"]
        self.assertEqual(len(sums), 1)
        self.assertEqual(len(sums[0].args), 1)
        self.assertEqual(sums[0].keywords, [])


if __name__ == "__main__":
    unittest.main()

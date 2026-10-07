import ast
import unittest
from pathlib import Path

from tools.v212_optimizer_flop_accounting import ARMS, EMA_ARMS, accounting
from two_player.v212_model import V212Config, V212Model


class OptimizerFlopAccountingTests(unittest.TestCase):
    def test_parameter_and_ema_coordinates_match_all_six_model_shapes(self):
        report = accounting()
        for arm in ARMS:
            with self.subTest(arm=arm):
                row = report["arms"][arm]
                model = V212Model(V212Config(arm=arm, seed=1))
                self.assertEqual(row["trainable_coordinates"],
                                 model.parameter_counts()["trainable"])
                self.assertEqual(row["trainable_parameter_tensors"],
                                 len(model.params))
                self.assertEqual(row["ema_coordinates"],
                                 model.parameter_counts()["ema_target"])
                self.assertEqual(row["ema_parameter_tensors"],
                                 len(model.target))
                self.assertEqual(row["ema_coordinates"] > 0, arm in EMA_ARMS)

    def test_adam_ema_arithmetic_and_clip_branch_bounds(self):
        report = accounting()
        for arm, row in report["arms"].items():
            with self.subTest(arm=arm):
                n = row["trainable_coordinates"]
                m = row["ema_coordinates"]
                ops = row["floating_point_arithmetic"]
                self.assertEqual(ops["additions"], 4 * n + m)
                self.assertEqual(ops["subtractions"],
                                 n + 2 * row["trainable_parameter_tensors"]
                                 + 2 + row["ema_parameter_tensors"])
                self.assertEqual(ops["multiplications"], 8 * n + 2 * m)
                self.assertEqual(ops["divisions_excluding_clip_scale"], 3 * n)
                self.assertEqual(ops["total_flops"]["norm_gt_5"],
                                 ops["total_flops"]["norm_le_5"] + 1)
                interval = row["twenty_seed_87_update_optimizer_only_flop_interval"]
                self.assertEqual(interval["upper"] - interval["lower"], 20 * 87)

    def test_report_does_not_claim_complete_counter_or_compute_gate(self):
        report = accounting()
        self.assertEqual(report["schedule_updates"], 1740)
        self.assertTrue(any("cannot establish" in item
                            for item in report["limitations"]))

    def test_clipping_branch_matches_source_and_scales_in_both_cases(self):
        report = accounting()
        source_path = (Path(__file__).resolve().parents[1]
                       / "two_player" / "v212_scratch_optimizer.py")
        tree = ast.parse(source_path.read_text(encoding="utf-8"))
        function = next(
            node for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef)
            and node.name == "scratch_adam_ema_step"
        )
        scale_assignment = next(
            node for node in function.body
            if isinstance(node, ast.Assign)
            and any(isinstance(target, ast.Name) and target.id == "clip_scale"
                    for target in node.targets)
        )
        self.assertIsInstance(scale_assignment.value, ast.IfExp)
        self.assertEqual(ast.unparse(scale_assignment.value.test),
                         "gradient_norm > GRADIENT_CLIP_NORM")
        clipped_assignment = next(
            node for node in ast.walk(function)
            if isinstance(node, ast.Assign)
            and any(isinstance(target, ast.Name) and target.id == "clipped"
                    for target in node.targets)
        )
        self.assertEqual(ast.unparse(clipped_assignment.value),
                         "grads[key] * clip_scale")
        self.assertGreater(clipped_assignment.lineno, scale_assignment.lineno)
        parameter_loop = next(
            node for node in function.body
            if isinstance(node, ast.For) and clipped_assignment in node.body
        )
        self.assertIsNotNone(parameter_loop)
        for arm, row in report["arms"].items():
            n = row["trainable_coordinates"]
            branches = row["global_clipping_branch"]
            self.assertEqual(branches["norm_le_5"], {
                "clip_scale_divisions": 0,
                "gradient_scale_multiplications": n,
            })
            self.assertEqual(branches["norm_gt_5"], {
                "clip_scale_divisions": 1,
                "gradient_scale_multiplications": n,
            })


if __name__ == "__main__":
    unittest.main()

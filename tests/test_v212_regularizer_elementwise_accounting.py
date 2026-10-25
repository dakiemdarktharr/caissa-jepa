import ast
from pathlib import Path
import unittest

from tools.v212_regularizer_elementwise_accounting import accounting


class RegularizerElementwiseAccountingTests(unittest.TestCase):
    def test_root_regularizer_candidate_counts_and_scope(self):
        report = accounting()
        self.assertEqual(report["scheduled_updates_per_arm"], 1740)
        one = report["per_invocation"]
        self.assertEqual(one["candidate_fp_array_additions"], 4128)
        self.assertEqual(one["candidate_fp_array_subtractions"], 3104)
        self.assertEqual(one["candidate_fp_array_multiplications"], 6208)
        self.assertEqual(one["candidate_fp_array_divisions"], 5120)
        self.assertEqual(one["candidate_fp_scalar_additions"], 3)
        self.assertEqual(one["candidate_fp_scalar_multiplications"], 4)
        self.assertEqual(one["candidate_fp_scalar_divisions"], 1)
        self.assertEqual(one["integer_scalar_shape_multiplications"], 2)
        self.assertEqual(one["squared_array_elements_owned_by_square_inventory"], 3104)
        self.assertEqual(one["reductions_owned_by_reduction_inventory"], 5)
        self.assertEqual(one["linked_eigensolver_calls_not_counted"], 1)
        self.assertEqual(
            report["schedule_per_arm"]["candidate_fp_array_divisions"],
            5120 * 1740,
        )

    def test_rejects_invalid_schedule_count(self):
        with self.assertRaises(ValueError):
            accounting(0)
        with self.assertRaises(ValueError):
            accounting(True)

    def test_source_shapes_and_expression_sites_match_inventory(self):
        source_path = (Path(__file__).resolve().parents[1]
                       / "two_player" / "v212_model.py")
        tree = ast.parse(source_path.read_text(encoding="utf-8"))
        regularize = next(
            node for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef) and node.name == "_regularize"
        )
        loss_grad = next(
            node for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef) and node.name == "loss_grad"
        )
        self.assertEqual(
            sum(isinstance(node, ast.Call)
                and ast.unparse(node.func) == "np.maximum"
                for node in ast.walk(regularize)),
            2,
        )
        self.assertEqual(
            sum(isinstance(node, ast.Call)
                and ast.unparse(node.func) == "np.linalg.eigvalsh"
                for node in ast.walk(regularize)),
            1,
        )
        dz_assignment = next(
            node for node in regularize.body
            if isinstance(node, ast.Assign)
            and any(isinstance(target, ast.Name) and target.id == "dz"
                    for target in node.targets)
        )
        self.assertEqual(
            ast.unparse(dz_assignment.value),
            "-2.0 * shortfall[None, :] * centered / (d * n * std[None, :])",
        )
        covariance_assignment = next(
            node for node in regularize.body
            if isinstance(node, ast.Assign)
            and any(isinstance(target, ast.Name) and target.id == "covariance"
                    for target in node.targets)
        )
        self.assertEqual(
            ast.unparse(covariance_assignment.value),
            "centered.T @ centered / n",
        )
        covariance_loss_assignment = next(
            node for node in regularize.body
            if isinstance(node, ast.Assign)
            and any(isinstance(target, ast.Name) and target.id == "covariance_loss"
                    for target in node.targets)
        )
        self.assertEqual(
            ast.unparse(covariance_loss_assignment.value),
            "float(np.sum(offdiag ** 2) / d)",
        )
        covariance_gradient = next(
            node for node in ast.walk(regularize)
            if isinstance(node, ast.AugAssign)
            and isinstance(node.target, ast.Name) and node.target.id == "dz"
            and isinstance(node.op, ast.Add)
        )
        self.assertEqual(
            ast.unparse(covariance_gradient.value),
            "4.0 * centered @ offdiag / (n * d)",
        )
        self.assertTrue(any(
            isinstance(node, ast.Assign)
            and any(isinstance(target, (ast.Tuple, ast.List))
                    and any(isinstance(item, ast.Name) and item.id == "dreg"
                            for item in target.elts)
                    for target in node.targets)
            and ast.unparse(node.value).endswith("._regularize(z0)")
            for node in loss_grad.body
        ))
        total_assignment = next(
            node for node in loss_grad.body
            if isinstance(node, ast.Assign)
            and any(isinstance(target, ast.Name) and target.id == "total"
                    for target in node.targets)
        )
        self.assertEqual(
            ast.unparse(total_assignment.value),
            "policy_loss + root_loss + 0.1 * variance_loss + 0.01 * covariance_loss",
        )
        self.assertTrue(any(
            isinstance(node, ast.AugAssign)
            and isinstance(node.target, ast.Name) and node.target.id == "dz0"
            and ast.unparse(node.value) == "0.1 * dreg"
            for node in ast.walk(loss_grad)
        ))


if __name__ == "__main__":
    unittest.main()

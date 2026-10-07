import ast
from pathlib import Path
import unittest

from tools.v212_policy_softmax_accounting import accounting


class PolicySoftmaxAccountingTests(unittest.TestCase):
    def test_fixed_shape_elementwise_and_schedule_counts(self):
        report = accounting()
        self.assertEqual(report["scheduled_updates_per_arm"], 1740)
        one = report["per_invocation"]
        self.assertEqual(one["policy_logit_elements"], 64 * 65)
        self.assertEqual(one["candidate_row_max_comparisons"], 64 * 64)
        self.assertEqual(one["shift_subtractions"], 64 * 65)
        self.assertEqual(one["exp_elements"], 64 * 65)
        self.assertEqual(one["probability_divisions"], 64 * 65)
        self.assertEqual(one["nll_log_elements"], 64)
        self.assertEqual(one["nll_residual_subtractions"], 64)
        self.assertEqual(one["policy_label_gradient_subtractions"], 64)
        self.assertEqual(report["schedule_per_arm"]["exp_elements"], 64 * 65 * 1740)
        self.assertEqual(
            report["schedule_per_arm"][
                "denominator_reduction_invocations_owned_by_reduction_inventory"
            ],
            2 * 1740,
        )

    def test_rejects_invalid_schedule_count(self):
        with self.assertRaises(ValueError):
            accounting(0)
        with self.assertRaises(ValueError):
            accounting(True)

    def test_source_sites_and_shapes_match_inventory(self):
        source_path = Path(__file__).resolve().parents[1] / "two_player" / "v212_model.py"
        tree = ast.parse(source_path.read_text(encoding="utf-8"))
        loss_grad = next(
            node for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef) and node.name == "loss_grad"
        )
        calls = [ast.unparse(node.func) for node in ast.walk(loss_grad)
                 if isinstance(node, ast.Call)]
        self.assertEqual(calls.count("np.where"), 1)
        self.assertEqual(calls.count("np.max"), 1)
        self.assertEqual(calls.count("np.exp"), 1)
        self.assertEqual(calls.count("np.log"), 1)
        exp_assignment = next(
            node for node in loss_grad.body
            if isinstance(node, ast.Assign)
            and any(isinstance(target, ast.Name) and target.id == "exp_logits"
                    for target in node.targets)
        )
        self.assertEqual(ast.unparse(exp_assignment.value), "np.exp(shifted)")
        probability_assignment = next(
            node for node in loss_grad.body
            if isinstance(node, ast.Assign)
            and any(isinstance(target, ast.Name) and target.id == "probs"
                    for target in node.targets)
        )
        self.assertEqual(
            ast.unparse(probability_assignment.value),
            "exp_logits / exp_logits.sum(axis=1, keepdims=True)",
        )
        self.assertEqual(
            sum(isinstance(node, ast.AugAssign)
                and ast.unparse(node.target) == "dlogits[np.arange(n), policy]"
                and isinstance(node.op, ast.Sub)
                for node in ast.walk(loss_grad)),
            1,
        )


if __name__ == "__main__":
    unittest.main()

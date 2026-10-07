import ast
import inspect
import unittest

from tools.v212_preflight_scan_accounting import SCHEMA, accounting
from two_player import v212_model


class PreflightScanAccountingTests(unittest.TestCase):
    def test_64_window_source_cardinalities(self):
        report = accounting()
        self.assertEqual(report["schema"], SCHEMA)
        self.assertEqual(report["batch_size"], 64)
        self.assertEqual(report["model_loss_grad_preflight_calls"], 1)
        self.assertEqual(report["numeric_finite_check_arrays"], 7)
        self.assertEqual(report["numeric_finite_check_elements_by_array"], {
            "x": 12_672,
            "policy": 64,
            "value": 64,
            "actions": 16_640,
            "actors": 256,
            "future_x": 50_688,
            "future_value": 256,
        })
        self.assertEqual(report["numeric_finite_check_elements"], 80_640)
        self.assertEqual(report["action_count_nonzero_input_elements"], 16_640)
        self.assertEqual(report["action_count_nonzero_output_rows"], 256)
        self.assertEqual(report["action_domain_predicate_element_evaluations"], 66_560)
        self.assertEqual(report["action_row_count_predicate_evaluations"], 256)
        self.assertEqual(report["comparison_elements_by_site_family"], {
            "action_range_and_binary_checks": 66_560,
            "policy_index_range": 128,
            "actor_alternation": 192,
            "one_hot_count_domains": 256,
        })
        self.assertEqual(report["array_comparison_element_evaluations"], 67_136)
        self.assertEqual(report["scalar_shape_comparison_site_calls"], 15)
        self.assertEqual(report["finite_array_shape_comparison_calls"], 12)
        self.assertEqual(report["comparison_ast_site_count"], 13)
        self.assertEqual(report["comparison_ast_site_occurrences_per_successful_call"], 24)
        self.assertIn("invalid batches may short-circuit",
                      report["predicate_count_assumption"])
        self.assertFalse(report["coverage"]["complete_preflight_inventory"])
        self.assertTrue(any("dataset-level" in item for item in report["coverage"]["omitted"]))

    def test_rejects_nonpositive_or_noninteger_batch_size(self):
        for value in (0, -1, True, 64.0):
            with self.subTest(value=value), self.assertRaises(ValueError):
                accounting(value)

    def test_source_has_one_preflight_call_per_loss_grad(self):
        tree = ast.parse(inspect.getsource(v212_model))
        classes = [node for node in tree.body if isinstance(node, ast.ClassDef)
                   and node.name == "V212Model"]
        loss_grad = next(node for node in classes[0].body
                         if isinstance(node, ast.FunctionDef) and node.name == "loss_grad")
        calls = [node for node in ast.walk(loss_grad)
                 if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                 and node.func.id == "preflight_batch"]
        self.assertEqual(len(calls), 1)

        preflight = next(node for node in tree.body
                         if isinstance(node, ast.FunctionDef)
                         and node.name == "preflight_batch")
        called_attributes = [node.func.attr for node in ast.walk(preflight)
                             if isinstance(node, ast.Call)
                             and isinstance(node.func, ast.Attribute)]
        self.assertIn("count_nonzero", called_attributes)
        finite_helper = next(node for node in tree.body
                             if isinstance(node, ast.FunctionDef)
                             and node.name == "_finite_array")
        finite_calls = [node.func.attr for node in ast.walk(finite_helper)
                        if isinstance(node, ast.Call)
                        and isinstance(node.func, ast.Attribute)]
        self.assertIn("isfinite", finite_calls)
        self.assertEqual(sum(1 for node in ast.walk(preflight)
                             if isinstance(node, ast.Call)
                             and isinstance(node.func, ast.Name)
                             and node.func.id == "_finite_array"), 12)


if __name__ == "__main__":
    unittest.main()

import ast
import inspect
import unittest
from collections import Counter

from tools.v212_preflight_bitwise_accounting import SCHEMA, accounting
from two_player import v212_model


class PreflightBitwiseAccountingTests(unittest.TestCase):
    def test_64_row_boolean_output_cardinalities(self):
        report = accounting()
        self.assertEqual(report["schema"], SCHEMA)
        self.assertEqual(report["batch_size"], 64)
        self.assertEqual(report["source_bitwise_ast_sites"], 12)
        self.assertEqual(report["output_elements_by_site_family"], {
            "transition_consistency_and_invalid_mask": 512,
            "role_pair_and_alternation_masks": 384,
            "action_range_or": 16_640,
            "action_binary_and": 16_640,
            "horizon_complete_prefix_and": 448,
            "horizon_validity_and": 384,
            "missing_target_count_and_or": 576,
        })
        self.assertEqual(report["total_output_elements"], 35_584)
        self.assertFalse(report["coverage"]["comparison_element_evaluations_counted"])
        self.assertFalse(report["coverage"]["boolean_inversion_elements_counted"])
        self.assertFalse(report["coverage"]["runtime_cost_verified"])
        self.assertFalse(report["coverage"]["complete_preflight_inventory"])

    def test_source_bitwise_sites_match_the_fixed_cardinality_families(self):
        tree = ast.parse(inspect.getsource(v212_model))
        preflight = next(node for node in tree.body
                         if isinstance(node, ast.FunctionDef)
                         and node.name == "preflight_batch")
        sites = [node for node in ast.walk(preflight)
                 if isinstance(node, ast.BinOp)
                 and isinstance(node.op, (ast.BitAnd, ast.BitOr))]
        self.assertEqual(len(sites), 12)
        self.assertEqual(Counter(type(node.op).__name__ for node in sites), {
            "BitAnd": 10,
            "BitOr": 2,
        })
        self.assertEqual(Counter(ast.unparse(node) for node in sites), Counter({
            "transition_valid & ~transition_exists": 1,
            "transition_exists & ~transition_valid": 1,
            "transition_exists[:, 1:] & transition_exists[:, :-1]": 1,
            "(actors[:, 1:] != -actors[:, :-1]) & role_pairs": 1,
            "(actions < 0.0) | (actions > 1.0)": 1,
            "(actions != 0.0) & (actions != 1.0)": 1,
            "transition_exists[:, :horizon] & transition_valid[:, :horizon]": 1,
            "complete & present": 1,
            "complete & present & ~terminal_by_horizon": 1,
            "~terminal_confirmed & ~invalid[:, :horizon].any(axis=1)": 1,
            "~terminal_confirmed & ~invalid[:, :horizon].any(axis=1) & (~complete | ~present)": 1,
            "~complete | ~present": 1,
        }))

    def test_rejects_nonpositive_or_noninteger_batch_size(self):
        for value in (0, -1, True, 64.0):
            with self.subTest(value=value), self.assertRaises(ValueError):
                accounting(value)


if __name__ == "__main__":
    unittest.main()

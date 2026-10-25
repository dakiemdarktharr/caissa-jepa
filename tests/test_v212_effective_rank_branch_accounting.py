import ast
from pathlib import Path
import unittest

from tools.v212_effective_rank_branch_accounting import (
    branch_work, schedule_bounds,
)


class EffectiveRankBranchAccountingTests(unittest.TestCase):
    def test_inactive_and_active_branch_work(self):
        inactive = branch_work(active=False, selected_eigenvalues=0)
        self.assertEqual(inactive["candidate_fp_additions"], 0)
        self.assertEqual(inactive["fp_divisions"], 0)
        self.assertEqual(inactive["log_calls"], 0)
        self.assertEqual(inactive["exp_calls"], 0)
        self.assertEqual(inactive["comparisons"], 1)

        one = branch_work(active=True, selected_eigenvalues=1)
        self.assertEqual(one["candidate_fp_additions"], 0)
        self.assertEqual(one["fp_multiplications"], 1)
        self.assertEqual(one["fp_divisions"], 1)
        self.assertEqual(one["log_calls"], 1)
        self.assertEqual(one["exp_calls"], 1)

        full = branch_work(active=True, selected_eigenvalues=32)
        self.assertEqual(full["candidate_fp_additions"], 31)
        self.assertEqual(full["fp_multiplications"], 32)
        self.assertEqual(full["fp_divisions"], 32)
        self.assertEqual(full["log_calls"], 32)
        self.assertEqual(full["exp_calls"], 1)
        self.assertEqual(full["comparisons"], 33)
        self.assertEqual(full["unary_negations"], 1)

    def test_active_branch_requires_nonempty_selected_spectrum(self):
        with self.assertRaisesRegex(ValueError, "requires a selected eigenvalue"):
            branch_work(active=True, selected_eigenvalues=0)
        with self.assertRaisesRegex(ValueError, "cannot select eigenvalues"):
            branch_work(active=False, selected_eigenvalues=1)

    def test_full_schedule_upper_bound_per_arm(self):
        report = schedule_bounds()
        self.assertEqual(report["scheduled_updates_per_arm"], 1740)
        intervals = report["schedule_interval_per_arm"]
        self.assertEqual(intervals["candidate_fp_additions"], {
            "candidate_fp_additions": 0,
            "upper_candidate_fp_additions": 53_940,
        })
        self.assertEqual(intervals["fp_multiplications"]["upper_fp_multiplications"], 55_680)
        self.assertEqual(intervals["fp_divisions"]["upper_fp_divisions"], 55_680)
        self.assertEqual(intervals["log_calls"]["upper_log_calls"], 55_680)
        self.assertEqual(intervals["exp_calls"]["upper_exp_calls"], 1_740)

    def test_rejects_malformed_branch_and_update_counts(self):
        with self.assertRaises(ValueError):
            branch_work(active=1, selected_eigenvalues=1)
        with self.assertRaises(ValueError):
            branch_work(active=True, selected_eigenvalues=33)
        with self.assertRaises(ValueError):
            schedule_bounds(0)

    def test_source_branch_and_expression_sites_match_formula(self):
        model_path = Path(__file__).resolve().parents[1] / "two_player" / "v212_model.py"
        tree = ast.parse(model_path.read_text(encoding="utf-8"))
        regularize = next(
            node for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef) and node.name == "_regularize"
        )
        comparisons = [
            ast.unparse(node)
            for node in ast.walk(regularize)
            if isinstance(node, ast.Compare)
        ]
        self.assertIn("spectrum_sum <= 1e-12", comparisons)
        self.assertIn("spectrum > 1e-12", comparisons)
        probability_assignment = next(
            node for node in ast.walk(regularize)
            if isinstance(node, ast.Assign)
            and any(isinstance(target, ast.Name) and target.id == "probabilities"
                    for target in node.targets)
        )
        self.assertEqual(
            ast.unparse(probability_assignment.value),
            "spectrum[spectrum > 1e-12] / spectrum_sum",
        )
        rank_assignments = [
            node for node in ast.walk(regularize)
            if isinstance(node, ast.Assign)
            and any(isinstance(target, ast.Name) and target.id == "effective_rank"
                    for target in node.targets)
        ]
        self.assertIn(
            "float(np.exp(-np.sum(probabilities * np.log(probabilities))))",
            [ast.unparse(node.value) for node in rank_assignments],
        )


if __name__ == "__main__":
    unittest.main()

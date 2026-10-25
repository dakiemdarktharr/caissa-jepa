import unittest

from tools.counterplay_gradient_check import run_checks


class CounterplayGradientTests(unittest.TestCase):
    def test_reported_objective_gradient_matches_every_parameter_tensor(self):
        report = run_checks()
        self.assertEqual(report["finite_difference_checks"], 192)
        self.assertEqual(report["coverage_arm_scenarios"], 12)
        self.assertEqual(report["coverage_tensor_count"], 96)
        self.assertFalse(report["failures"], report["failures"][:5])
        self.assertLessEqual(report["worst_normalized_error"], 1.0)
        self.assertEqual(report["mixed_horizon_mask_counts"], {1: 3, 2: 2, 4: 1})
        self.assertTrue(report["synthetic_only"])
        self.assertEqual(report["optimizer_updates"], 0)
        for key, tensors in report["coverage"].items():
            self.assertTrue(tensors, key)
        self.assertEqual(set(report["scenario_activity"]), {
            "variance-active-mixed-masks", "covariance-active-x10-seed9",
        })


if __name__ == "__main__":
    unittest.main()

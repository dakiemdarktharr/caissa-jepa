from __future__ import annotations

import math
import unittest

from tools.v212_root_quality_calibration_audit import (
    BANDS,
    INTEGRATION_INTERVALS,
    _root_covariance_manifest,
    build_manifest,
    conditional_score_mean,
    simpson_integral,
    solve_conditional_eta,
    solve_validity_intercept,
)


class RootQualityCalibrationAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = build_manifest()

    def test_simpson_rule_integrates_standard_normal_moments(self) -> None:
        intervals = INTEGRATION_INTERVALS[-1]
        density = lambda value: math.exp(-0.5 * value * value) / math.sqrt(2 * math.pi)
        self.assertAlmostEqual(simpson_integral(density, intervals), 1.0, places=12)
        self.assertAlmostEqual(
            simpson_integral(lambda value: value * density(value), intervals),
            0.0,
            places=12,
        )
        self.assertAlmostEqual(
            simpson_integral(lambda value: value * value * density(value), intervals),
            1.0,
            places=12,
        )

    def test_slot_variance_split_preserves_p2_margins(self) -> None:
        manifest = _root_covariance_manifest()
        self.assertEqual(manifest["root_quality_pair_margin_variance"], 0.375)
        for band in BANDS:
            row = manifest["bands"][band]
            self.assertTrue(row["positive_definite"])
            for pair, total in row["total_pair_margin_variances"].items():
                self.assertAlmostEqual(
                    row["remaining_pair_margin_variances"][pair], 0.375, places=12
                )
                self.assertAlmostEqual(total, 0.75, places=12)

    def test_manifest_has_proposed_cells_endpoints_and_deterministic_rows(self) -> None:
        manifest = self.manifest
        self.assertIn("no random draws", manifest["status"])
        self.assertEqual(manifest["scenario_counts"], {
            "base_scenarios": 31,
            "added_scenarios": 4,
            "total_scenarios": 35,
            "null_scenarios": 28,
            "alternative_scenarios": 7,
            "outer_mc_endpoints": 63,
        })
        self.assertEqual(len(manifest["conditional_target_rows"]), 120)
        self.assertEqual(len(manifest["quadrature_solutions"]), 4)
        self.assertEqual(manifest, build_manifest())

    def test_intercepts_and_selected_root_moments(self) -> None:
        solved = {
            row["gamma"]: row["by_interval_count"][str(INTEGRATION_INTERVALS[-1])]
            for row in self.manifest["quadrature_solutions"]
            if row["target_mean"] == 0.0
        }
        negative = solved[-1.0]
        positive = solved[1.0]
        for result in (negative, positive):
            self.assertLessEqual(result["validity"]["absolute_residual"], 1e-12)
            self.assertAlmostEqual(result["validity"]["marginal_validity"], 0.40, places=12)
            self.assertGreater(result["selected_root_moments"]["variance"], 0.0)
        self.assertAlmostEqual(
            negative["validity"]["intercept"], positive["validity"]["intercept"], places=12
        )
        self.assertAlmostEqual(
            negative["selected_root_moments"]["mean"],
            -positive["selected_root_moments"]["mean"],
            places=12,
        )
        self.assertLess(negative["selected_root_moments"]["mean"], 0.0)
        self.assertGreater(positive["selected_root_moments"]["mean"], 0.0)

    def test_target_rows_meet_both_integration_and_eta_rules(self) -> None:
        intercepts = {
            gamma: solve_validity_intercept(gamma, INTEGRATION_INTERVALS[-1])["intercept"]
            for gamma in (-1.0, 1.0)
        }
        for solution in self.manifest["quadrature_solutions"]:
            self.assertTrue(solution["converged"])
            self.assertLessEqual(
                max(solution["absolute_order_differences"].values()), 1e-10
            )
        for row in self.manifest["conditional_target_rows"]:
            result = row["solved"]
            self.assertLessEqual(result["absolute_residual"], 1e-10)
            self.assertAlmostEqual(result["target_mean"], row["target_mean"])
            self.assertAlmostEqual(
                conditional_score_mean(
                    result["eta"], row["gamma"], intercepts[row["gamma"]],
                    self.manifest["sigma_rest"], INTEGRATION_INTERVALS[-1]
                ),
                result["achieved_mean"],
                delta=1e-12,
            )

    def test_assurance_and_workload_are_recomputed_for_63_endpoints(self) -> None:
        rows = self.manifest["assurance"]["results"]
        self.assertEqual([row["endpoint_count"] for row in rows], [63, 63])
        self.assertEqual([row["cells"] for row in rows], [35, 35])
        self.assertLess(
            float(rows[0]["dependence_robust_union_lower_bound"]), 0.80
        )
        self.assertGreaterEqual(
            float(rows[1]["dependence_robust_union_lower_bound"]), 0.80
        )
        self.assertEqual(rows[1]["total_inner_bootstrap_replicates"], 6_370_000_000)
        self.assertEqual(rows[1]["max_contrast_evaluations"], 95_550_000_000)

    def test_invalid_inputs_fail_closed(self) -> None:
        with self.assertRaises(ValueError):
            simpson_integral(lambda value: value, 3)
        with self.assertRaises(ValueError):
            solve_validity_intercept(1.0, 3)
        with self.assertRaises(ValueError):
            solve_conditional_eta(1.0, 1.0, -0.49, math.sqrt(1.625), 4096)


if __name__ == "__main__":
    unittest.main()

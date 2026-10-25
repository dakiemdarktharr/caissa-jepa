from __future__ import annotations

import math
import unittest

from tools.v212_root_quality_yield_interaction_audit import (
    ASSURANCE_REPLICATIONS,
    GAMMAS,
    INTEGRATION_INTERVALS,
    PAIR_GROUPS,
    build_manifest,
    selected_root_moments,
    solve_validity_intercept,
)


class RootQualityYieldInteractionAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = build_manifest()

    def test_pair_yield_mixture_preserves_marginal_and_accepted_weights(self) -> None:
        groups = self.manifest["policy_pair_groups"]
        self.assertAlmostEqual(
            sum(group["preselection_weight"] * group["q"] for group in groups),
            0.40,
            places=14,
        )
        self.assertAlmostEqual(groups[0]["accepted_weight"], 0.25, places=15)
        self.assertAlmostEqual(groups[1]["accepted_weight"], 0.75, places=15)
        self.assertAlmostEqual(
            sum(group["accepted_weight"] * group["mean_offset"] for group in groups),
            0.0,
            places=14,
        )

    def test_validity_intercepts_and_selected_roots_are_pair_specific(self) -> None:
        moments = {}
        for group in PAIR_GROUPS:
            for gamma in GAMMAS:
                result = solve_validity_intercept(
                    group["q"], gamma, INTEGRATION_INTERVALS[-1]
                )
                self.assertLessEqual(result["absolute_residual"], 1e-12)
                self.assertAlmostEqual(result["achieved_q"], group["q"], places=12)
                selected = selected_root_moments(
                    group["q"], gamma, result["intercept"], INTEGRATION_INTERVALS[-1]
                )
                moments[(group["q"], gamma)] = selected["mean"]
                self.assertGreater(selected["variance"], 0.0)
        self.assertGreater(moments[(0.20, 1.0)], moments[(0.60, 1.0)])
        self.assertLess(moments[(0.20, -1.0)], moments[(0.60, -1.0)])
        for q in (0.20, 0.60):
            self.assertAlmostEqual(moments[(q, 1.0)], -moments[(q, -1.0)], places=12)

    def test_manifest_has_targets_counts_and_numerical_convergence(self) -> None:
        self.assertEqual(self.manifest["scenario_counts"], {
            "draft_02_base_scenarios": 31,
            "root_quality_isolation_scenarios": 4,
            "interaction_scenarios": 4,
            "total_scenarios": 39,
            "null_scenarios": 30,
            "alternative_scenarios": 9,
            "outer_mc_endpoints": 69,
            "conditional_target_rows": 240,
        })
        self.assertEqual(len(self.manifest["solutions"]), 8)
        self.assertEqual(len(self.manifest["conditional_target_rows"]), 240)
        for solution in self.manifest["solutions"]:
            self.assertTrue(solution["converged"])
            self.assertLessEqual(
                max(solution["absolute_order_differences"].values()), 1e-10
            )
            for moment in ("mean", "second_moment", "variance"):
                self.assertLessEqual(
                    solution["absolute_order_differences"][f"selected_root_{moment}"],
                    1e-10,
                )
            for order in (str(x) for x in INTEGRATION_INTERVALS):
                self.assertLessEqual(
                    solution["by_interval_count"][order]["validity"]["absolute_residual"],
                    1e-12,
                )
                self.assertLessEqual(
                    solution["by_interval_count"][order]["conditional_target"]["absolute_residual"],
                    1e-10,
                )
        for row in self.manifest["accepted_target_checks"]:
            self.assertAlmostEqual(
                row["weighted_pair_conditional_target"],
                row["declared_global_target"],
                places=14,
            )
        self.assertEqual(self.manifest, build_manifest())

    def test_quality_variance_split_preserves_total_p2_pair_variances(self) -> None:
        covariance = self.manifest["root_covariance_manifest"]
        for band in covariance["bands"].values():
            self.assertTrue(band["positive_definite"])
            for pair, total in band["total_pair_margin_variances"].items():
                self.assertAlmostEqual(
                    band["remaining_pair_margin_variances"][pair], 0.375, places=12
                )
                self.assertAlmostEqual(total, 0.75, places=12)

    def test_assurance_and_workload_are_recomputed_for_69_endpoints(self) -> None:
        rows = self.manifest["assurance"]["results"]
        self.assertEqual([row["outer_datasets_per_cell"] for row in rows], list(ASSURANCE_REPLICATIONS))
        self.assertTrue(all(row["endpoint_count"] == 69 for row in rows))
        self.assertTrue(all(row["cells"] == 39 for row in rows))
        bounds = [float(row["dependence_robust_union_lower_bound"]) for row in rows]
        self.assertLess(bounds[2], 0.80)
        self.assertGreaterEqual(bounds[3], 0.80)
        self.assertLess(bounds[4], 0.80)
        self.assertEqual(rows[3]["total_inner_bootstrap_replicates"], 7_195_500_000)
        self.assertEqual(rows[3]["max_contrast_evaluations"], 107_932_500_000)

    def test_invalid_yield_and_target_inputs_fail_closed(self) -> None:
        with self.assertRaises(ValueError):
            solve_validity_intercept(0.0, 1.0, INTEGRATION_INTERVALS[-1])
        with self.assertRaises(ValueError):
            solve_validity_intercept(1.0, 1.0, INTEGRATION_INTERVALS[-1])
        self.assertTrue(math.isfinite(self.manifest["sigma_rest"]))


if __name__ == "__main__":
    unittest.main()

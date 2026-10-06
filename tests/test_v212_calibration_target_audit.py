from __future__ import annotations

import unittest

from tools.v212_calibration_target_audit import (
    BETA,
    CONTRAST_ORDER,
    _base_scenarios,
    build_manifest,
    expected_score_difference,
    solve_eta,
)


class CalibrationTargetAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = build_manifest()
        cls.scenarios = {row["scenario_id"]: row for row in cls.manifest["scenarios"]}

    def test_scenario_inventory_and_determinism(self) -> None:
        self.assertEqual(self.manifest["scenario_count"], 31)
        self.assertEqual(len(_base_scenarios()), 31)
        self.assertEqual(self.manifest, build_manifest())
        self.assertIn("no random", self.manifest["status"])
        self.assertTrue(self.manifest["policy_pair_indices_are_abstract"])
        self.assertIn("proposed convention", self.manifest["reviewable_open_convention"])
        self.assertIn("independent disposition", self.manifest["reviewable_open_convention"])

    def test_null_and_alternative_target_patterns(self) -> None:
        pairs = [f"{v}-{c}" for v, c in CONTRAST_ORDER]
        self.assertEqual(pairs, [f"V{v}-C{c}" for c in range(1, 6) for v in range(1, 3)])
        for index, pair in enumerate(("V1-C1", "V2-C1", "V1-C2"), start=1):
            means = self.scenarios[f"N-ATOMIC-{index:02d}"]["means_by_band"]["low"]
            self.assertEqual([key for key, value in means.items() if value == 0.0], [pair])
        for index in range(1, 6):
            self.assertTrue(all(value == 0 for value in self.scenarios[f"N-GLOBAL-{index:02d}"]["means_by_band"]["low"].values()))
        for index in range(1, 11):
            values = list(self.scenarios[f"N-ATOMIC-{index:02d}"]["means_by_band"]["low"].values())
            self.assertEqual(values.count(0.0), 1)
            self.assertEqual(values.count(0.075), 9)
        for index in range(1, 6):
            means = self.scenarios[f"N-MACRO-{index:02d}"]["means_by_band"]["low"]
            control = f"C{index}"
            self.assertEqual(means[f"V1-{control}"], 0.10)
            self.assertEqual(means[f"V2-{control}"], -0.10)
            self.assertEqual((means[f"V1-{control}"] + means[f"V2-{control}"]) / 2, 0.0)
        for index in range(1, 6):
            means = self.scenarios[f"N-CONTROL-{index:02d}"]["means_by_band"]["low"]
            self.assertEqual(means[f"V1-C{index}"], 0.0)
            self.assertEqual(means[f"V2-C{index}"], 0.0)
        for scenario_id, target in (("A-BOUNDARY", 0.05), ("A-MODERATE", 0.075), ("A-LARGE", 0.10)):
            self.assertEqual(set(self.scenarios[scenario_id]["means_by_band"]["low"].values()), {target})
        self.assertEqual(len(pairs), 10)

    def test_heterogeneous_band_means_and_yield_weights(self) -> None:
        hetero = self.scenarios["A-HETERO"]["means_by_band"]
        self.assertEqual(hetero["low"]["V1-C1"], 0.20)
        self.assertEqual(hetero["middle"]["V1-C1"], 0.10)
        self.assertEqual(hetero["high"]["V1-C1"], 0.0)
        for scenario_id, target in (("N-GLOBAL-YIELD", 0.0), ("A-BOUNDARY-YIELD", 0.05)):
            row = self.scenarios[scenario_id]
            groups = [
                next(entry for entry in row["solved_eta_rows"] if entry["candidate_control"] == "V1-C1" and entry["band"] == "low" and entry["policy_pair_indices"] == list(range(8))),
                next(entry for entry in row["solved_eta_rows"] if entry["candidate_control"] == "V1-C1" and entry["band"] == "low" and entry["policy_pair_indices"] == list(range(8, 16))),
            ]
            self.assertAlmostEqual(0.25 * groups[0]["population_mean_target"] + 0.75 * groups[1]["population_mean_target"], target)
            self.assertEqual([group["slot_validity_q"] for group in groups], [0.20, 0.60])

    def test_every_eta_meets_predeclared_solver_rule(self) -> None:
        rows = [entry for scenario in self.manifest["scenarios"] for entry in scenario["solved_eta_rows"]]
        self.assertGreater(self.manifest["solved_eta_row_count"], 0)
        for entry in rows:
            self.assertLessEqual(entry["absolute_residual"], 1e-10)
            self.assertGreaterEqual(entry["bisection_steps"], 1)
            self.assertLessEqual(entry["bisection_steps"], 256)
            self.assertAlmostEqual(
                expected_score_difference(entry["eta"], entry["tau"], entry["beta"], entry["sigma"]),
                entry["achieved_mean"],
            )

    def test_eta_solver_is_monotone_and_rejects_unattainable_bracket_target(self) -> None:
        points = [-1.0, -0.5, 0.0, 0.5, 1.0]
        values = [expected_score_difference(point, tau=0.4, beta=BETA, sigma=1.5) for point in points]
        self.assertEqual(values, sorted(values))
        result = solve_eta(0.05, tau=0.4, beta=BETA, sigma=1.5)
        self.assertLessEqual(result["absolute_residual"], 1e-10)
        with self.assertRaises(ValueError):
            solve_eta(0.999999999, tau=0.75, beta=BETA, sigma=1.4)


if __name__ == "__main__":
    unittest.main()

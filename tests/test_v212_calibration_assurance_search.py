from __future__ import annotations

import unittest

from tools.v212_calibration_assurance import calculate
from tools.v212_calibration_assurance_search import exact_cutoff_near, scan


class CalibrationAssuranceSearchTests(unittest.TestCase):
    def test_integer_scan_matches_existing_calculator_and_reveals_cutoff_drop(self) -> None:
        result = scan(18_000, 18_600)
        self.assertEqual(result["integer_values_scanned"], 601)
        self.assertEqual(
            result["first_qualifying_within_range"]["outer_datasets_per_cell"],
            18_378,
        )
        rows = {
            row["outer_datasets_per_cell"]: row
            for row in result["high_precision_neighborhood"]
        }
        self.assertTrue(rows[18_378]["decimal_cutoff_valid"])
        self.assertTrue(rows[18_378]["cutoff_matches_reference"])
        self.assertLess(
            float(rows[18_377]["decimal_union_lower_bound"]), 0.80
        )
        self.assertGreater(
            float(rows[18_378]["decimal_union_lower_bound"]), 0.80
        )
        self.assertGreaterEqual(
            float(calculate([18_450], endpoints=69, cells=39)["results"][0][
                "dependence_robust_union_lower_bound"
            ]), 0.80
        )
        at_18_500 = exact_cutoff_near(18_500, 0.06, 0.05 / 69)
        self.assertEqual(at_18_500, 1_007)
        row_18_500 = calculate([18_500], endpoints=69, cells=39)["results"][0]
        self.assertLess(
            float(row_18_500["dependence_robust_union_lower_bound"]), 0.80
        )

    def test_bounds_and_counts_fail_closed(self) -> None:
        for args in ((0, 10), (10, 9)):
            with self.assertRaises(ValueError):
                scan(*args)
        with self.assertRaises(ValueError):
            scan(1, 2, endpoints=0)


if __name__ == "__main__":
    unittest.main()

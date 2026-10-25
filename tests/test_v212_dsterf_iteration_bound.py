from __future__ import annotations

import unittest

from tools.v212_dsterf_iteration_bound import source_bound


class DsterfIterationBoundTests(unittest.TestCase):
    def test_fixed_32_by_32_reference_loop_bound(self):
        report = source_bound()
        self.assertEqual(report["max_iterations"], 960)
        self.assertEqual(report["per_iteration"]["upper_flops"], 444)
        self.assertEqual(report["noniterative_upper_bound"]["upper_flops"], 2257)
        self.assertEqual(
            report["dsterf_source_visible_upper_flops_excluding_powers"], 428497
        )
        self.assertEqual(
            report["dsterf_source_visible_upper_if_each_power_maps_to_multiply"],
            428545,
        )

    def test_dlae2_branch_count_and_explicit_exclusions(self):
        report = source_bound()
        noniterative = report["noniterative_upper_bound"]
        self.assertEqual(noniterative["dlae2_max_calls"], 16)
        self.assertEqual(noniterative["dlae2_flops_per_call_upper_bound"], 13)
        self.assertIn("dlae2.f", source_bound()["dlae2_source_reference"])
        self.assertEqual(noniterative["eigenvalue_completion_search_checks"], 992)
        self.assertEqual(noniterative["initial_block_split_checks"], 31)
        self.assertEqual(
            report["separately_reported_non_flop_arithmetic"]["scalar_power_sites_max"],
            48,
        )
        self.assertIn(
            "DSYTRD blocked/unblocked reduction and its DSYTD2/DLATRD/DSYR2K paths",
            report["excluded_helpers_and_paths"],
        )

    def test_bound_is_only_a_partial_source_bound(self):
        report = source_bound()
        self.assertFalse(report["eligibility"]["complete_eigensolver_bound"])
        self.assertFalse(report["eligibility"]["full_counter"])
        self.assertFalse(report["eligibility"]["parity_eligible"])
        self.assertFalse(report["eligibility"]["profile_or_fit_authorized"])

    def test_input_validation(self):
        for args in ((1, 30), (32, 0), (True, 30), (32, False)):
            with self.subTest(args=args), self.assertRaises(ValueError):
                source_bound(*args)


if __name__ == "__main__":
    unittest.main()

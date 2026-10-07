from __future__ import annotations

import unittest

from tools.v212_dsyevd_driver_source_bound import MATRIX_ORDER, source_bound


class DsyevdDriverSourceBoundTests(unittest.TestCase):
    def test_n32_eigenvalues_only_direct_work_interval(self):
        report = source_bound()
        operations = report["covered_source_arithmetic_interval"]
        self.assertEqual(report["path"]["jobz"], "N")
        self.assertEqual(report["path"]["dsyevd_calls_dsyevd_route"], ["DSYTRD", "DSTERF"])
        self.assertEqual(operations["divisions"], {"minimum": 2, "maximum": 4})
        self.assertEqual(operations["multiplications"], {"minimum": 0, "maximum": 32})
        self.assertEqual(
            operations["combined_add_subtract_multiply_divide"],
            {"minimum": 2, "maximum": 36},
        )
        self.assertEqual(
            report["separately_reported_non_flop_work"]["square_root_calls"],
            {"minimum": 2, "maximum": 2},
        )

    def test_scaling_helpers_are_separate_and_conditional(self):
        calls = source_bound()["source_call_inventory"]
        self.assertEqual(calls["DLAMCH_calls"], 2)
        self.assertEqual(calls["DLANSY_calls"], 1)
        self.assertEqual(calls["DLASCL_calls_for_matrix_scaling"], {"minimum": 0, "maximum": 1})
        self.assertEqual(calls["DSYTRD_calls"], 1)
        self.assertEqual(calls["DSTERF_calls_for_JOBZ_N"], 1)
        self.assertEqual(calls["DSCAL_calls_for_eigenvalue_rescaling"], {"minimum": 0, "maximum": 1})

    def test_bound_does_not_clear_eigensolver_or_profile_gates(self):
        eligibility = source_bound()["eligibility"]
        self.assertFalse(eligibility["complete_dsyevd_bound"])
        self.assertFalse(eligibility["complete_eigensolver_bound"])
        self.assertFalse(eligibility["full_counter"])
        self.assertFalse(eligibility["parity_eligible"])
        self.assertFalse(eligibility["profile_or_fit_authorized"])

    def test_fixed_order_validation(self):
        for n in (1, 31, True, 32.0):
            with self.subTest(n=n), self.assertRaises(ValueError):
                source_bound(n)
        self.assertEqual(source_bound(MATRIX_ORDER)["path"]["matrix_order"], 32)


if __name__ == "__main__":
    unittest.main()

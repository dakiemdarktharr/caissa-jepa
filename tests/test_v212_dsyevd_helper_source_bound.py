import unittest

from tools.v212_dsyevd_helper_source_bound import source_bound


class DsyevdHelperSourceBoundTests(unittest.TestCase):
    def test_dlamch_ieee_reference_arithmetic(self):
        result = source_bound()
        operations = result["covered_source_arithmetic_interval"]
        self.assertEqual(operations["multiplications"], {"minimum": 3, "maximum": 3})
        self.assertEqual(operations["divisions"], {"minimum": 1, "maximum": 1})
        self.assertEqual(
            operations["combined_add_subtract_multiply_divide"],
            {"minimum": 4, "maximum": 4},
        )

    def test_dlansy_scan_is_separate_non_flop_work(self):
        result = source_bound()
        self.assertEqual(result["path"]["dlansy_matrix_entries_scanned"], 528)
        self.assertEqual(result["separately_reported_non_flop_work"]["dlansy_abs_intrinsic_calls"], 528)
        self.assertEqual(result["scope_and_ownership"]["dlansy_add_subtract_multiply_divide"], 0)

    def test_does_not_clear_full_counter_or_profile(self):
        eligibility = source_bound()["eligibility"]
        self.assertFalse(eligibility["complete_eigensolver_bound"])
        self.assertFalse(eligibility["full_counter"])
        self.assertFalse(eligibility["profile_or_fit_authorized"])


if __name__ == "__main__":
    unittest.main()

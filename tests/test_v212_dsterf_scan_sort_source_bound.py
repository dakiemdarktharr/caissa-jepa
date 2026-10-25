import unittest

from tools.v212_dsterf_scan_sort_source_bound import source_bound


class DsterfScanSortSourceBoundTests(unittest.TestCase):
    def test_n32_dlanst_cardinality_and_native_units(self):
        counts = source_bound()["dlanst_norm_m_cardinality_upper"]
        self.assertEqual(counts["calls"], 16)
        self.assertEqual(counts["diagonal_abs_evaluations"], 32)
        self.assertEqual(counts["offdiagonal_abs_evaluations"], 31)
        self.assertEqual(counts["total_abs_evaluations"], 63)
        self.assertEqual(counts["loop_iterations"], 31)
        self.assertEqual(counts["relational_comparison_sites"], 62)
        self.assertEqual(counts["disnan_call_sites"], 62)
        self.assertEqual(counts["add_subtract_multiply_divide_operations"], 0)

    def test_dlasrt_call_is_bounded_but_sort_work_stays_open(self):
        counts = source_bound()["dlasrt_increasing_cardinality_upper"]
        self.assertEqual(counts["successful_path_calls"], 1)
        self.assertEqual(counts["input_elements_per_call"], 32)
        self.assertEqual(counts["insertion_sort_partition_max_length"], 21)
        self.assertEqual(
            counts["quicksort_partition_sizes_upper_path"],
            list(range(32, 21, -1)),
        )
        self.assertEqual(counts["quicksort_scan_data_comparisons"], 594)
        self.assertEqual(counts["median_of_three_data_comparisons"], 33)
        self.assertEqual(
            counts["quicksort_i_lt_j_integer_comparisons_upper"], 297
        )
        self.assertEqual(counts["insertion_sort_data_comparisons_upper"], 496)
        self.assertEqual(counts["data_comparisons_upper"], 1_123)
        self.assertIn("N=32 only", counts["comparison_bound_scope"])

    def test_parameter_validation_and_gate_remain_closed(self):
        for invalid in (True, 1, 0, -2):
            with self.subTest(n=invalid), self.assertRaises(ValueError):
                source_bound(invalid)
        eligibility = source_bound()["eligibility"]
        self.assertFalse(eligibility["complete_dsterf_bound"])
        self.assertFalse(eligibility["complete_eigensolver_bound"])
        self.assertFalse(eligibility["full_counter"])
        self.assertFalse(eligibility["parity_eligible"])
        self.assertFalse(eligibility["profile_or_fit_authorized"])


if __name__ == "__main__":
    unittest.main()

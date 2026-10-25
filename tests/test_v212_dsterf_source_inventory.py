import unittest

from tools.v212_dsterf_source_inventory import source_inventory


class DsterfSourceInventoryTests(unittest.TestCase):
    def test_arithmetic_components_add_without_double_counting(self):
        report = source_inventory()
        components = report["non_overlapping_source_components"]
        candidate = report["conditional_source_arithmetic_candidate"]
        self.assertEqual(components["dsterf_direct_plus_dlae2_arithmetic"], 428_497)
        self.assertEqual(components["setup_dlamch_plus_dlapy2_arithmetic"], 3_844)
        self.assertEqual(components["dlascl_plus_per_call_dlamch_arithmetic"], 368)
        self.assertEqual(components["dlanst_norm_m_arithmetic"], 0)
        self.assertEqual(components["dlasrt_arithmetic"], 0)
        self.assertEqual(candidate["add_subtract_multiply_divide_upper"], 432_709)
        self.assertEqual(candidate["scalar_power_sites_separate"], 1_008)
        self.assertEqual(
            candidate["sensitivity_if_each_power_maps_to_one_multiply"], 433_717
        )
        self.assertEqual(candidate["square_root_calls_separate"], 2_016)

    def test_non_flop_helper_activity_is_reported_in_native_units(self):
        activity = source_inventory()["non_flop_source_activity"]
        self.assertEqual(activity["dlanst_calls_upper"], 16)
        self.assertEqual(activity["dlanst_abs_evaluations_upper"], 63)
        self.assertEqual(activity["dlasrt_array_value_comparisons_upper"], 1_123)
        self.assertEqual(
            activity["dlasrt_partition_i_lt_j_integer_checks_upper"], 297
        )

    def test_composition_does_not_clear_runtime_or_research_gates(self):
        eligibility = source_inventory()["eligibility"]
        self.assertFalse(eligibility["complete_dsterf_bound"])
        self.assertFalse(eligibility["complete_eigensolver_bound"])
        self.assertFalse(eligibility["full_counter"])
        self.assertFalse(eligibility["parity_eligible"])
        self.assertFalse(eligibility["profile_or_fit_authorized"])


if __name__ == "__main__":
    unittest.main()

import unittest

from tools.v212_dsterf_dlascl_source_bound import source_bound


class DsterfDlasclSourceBoundTests(unittest.TestCase):
    def test_n32_scaled_block_and_dlascl_upper(self):
        report = source_bound()
        path = report["path_upper_bounds"]
        arithmetic = report["source_arithmetic_upper"]
        ratios = report["conditional_assumptions"]["ratio_envelopes"]
        self.assertEqual(path["scaled_blocks"], 16)
        self.assertEqual(path["dlascl_calls"], 48)
        self.assertEqual(path["iterations_per_call"], 1)
        self.assertEqual(path["scaled_vector_elements_across_calls"], 80)
        self.assertEqual(arithmetic["dlascl_element_multiplications"], 80)
        self.assertEqual(arithmetic["dlascl_call_scalar_operations"], 192)
        self.assertEqual(arithmetic["dlamch_S_helper_operations"], 96)
        self.assertEqual(arithmetic["add_subtract_multiply_divide"], 368)
        self.assertIn("<2**515", ratios["large_norm_branch"])
        self.assertIn("<2**669", ratios["small_norm_branch"])

    def test_partial_dsterf_aggregate_includes_nonoverlapping_prior_scopes(self):
        combined = source_bound()["combined_partial_dsterf_candidate"]
        self.assertEqual(combined["combined_arithmetic_flops_excluding_powers"], 432_709)
        self.assertEqual(combined["combined_power_sites"], 1_008)
        self.assertEqual(combined["sensitivity_if_each_power_is_one_multiply"], 433_717)
        self.assertEqual(combined["combined_sqrt_calls"], 2_016)

    def test_remains_partial_and_does_not_open_any_gate(self):
        eligibility = source_bound()["eligibility"]
        self.assertFalse(eligibility["complete_dsterf_bound"])
        self.assertFalse(eligibility["complete_eigensolver_bound"])
        self.assertFalse(eligibility["full_counter"])
        self.assertFalse(eligibility["parity_eligible"])
        self.assertFalse(eligibility["profile_or_fit_authorized"])


if __name__ == "__main__":
    unittest.main()

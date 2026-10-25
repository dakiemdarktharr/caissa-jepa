import unittest

from tools.v212_dsterf_helper_source_bound import source_bound


class DsterfHelperSourceBoundTests(unittest.TestCase):
    def test_n32_helper_call_and_operation_totals(self):
        report = source_bound()
        arithmetic = report["source_arithmetic_upper"]
        self.assertEqual(report["helper_calls"]["dlapy2_calls_upper"], 960)
        self.assertEqual(arithmetic["dsterf_setup_dlamch_multiplications"], 3)
        self.assertEqual(arithmetic["dsterf_setup_dlamch_divisions"], 1)
        self.assertEqual(arithmetic["dlapy2_body_arithmetic"], 2_880)
        self.assertEqual(arithmetic["dlapy2_dlamch_O_multiplications"], 960)
        self.assertEqual(arithmetic["add_subtract_multiply_divide"], 3_844)
        self.assertEqual(arithmetic["scalar_square_power_sites_separate"], 960)
        self.assertEqual(arithmetic["sensitivity_if_each_power_is_one_multiply"], 4_804)
        self.assertEqual(arithmetic["square_root_calls_separate"], 960)

    def test_supplement_is_additive_only_to_declared_partial_base(self):
        supplement = source_bound()["supplement_to_dsterf_iteration_bound"]
        self.assertTrue(supplement["additive_to_base_source_scope"])
        self.assertEqual(supplement["combined_partial_arithmetic_flops_excluding_powers"], 432_341)
        self.assertEqual(supplement["combined_power_sites"], 1_008)
        self.assertEqual(supplement["combined_sensitivity_if_each_power_is_one_multiply"], 433_349)
        self.assertEqual(supplement["combined_sqrt_calls"], 2_016)

    def test_does_not_claim_complete_eigensolver_or_open_gates(self):
        eligibility = source_bound()["eligibility"]
        self.assertFalse(eligibility["complete_dsterf_bound"])
        self.assertFalse(eligibility["complete_eigensolver_bound"])
        self.assertFalse(eligibility["full_counter"])
        self.assertFalse(eligibility["parity_eligible"])
        self.assertFalse(eligibility["profile_or_fit_authorized"])


if __name__ == "__main__":
    unittest.main()

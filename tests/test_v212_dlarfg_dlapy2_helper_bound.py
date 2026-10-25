import unittest

from tools.v212_dlarfg_dlapy2_helper_bound import source_bound
from tools.v212_dsytd2_rank_update_bound import source_bound as dsytd2_source_bound


class DlarfgDlapy2HelperBoundTests(unittest.TestCase):
    def test_default_n32_helper_arithmetic_and_separate_sites(self):
        report = source_bound()
        helpers = report["covered_helper_arithmetic"]
        self.assertEqual(report["path"]["dlapy2_calls_upper"], 60)
        self.assertEqual(helpers["dlapy2_body_flops_upper"], 180)
        self.assertEqual(helpers["dlamch_overflow_flops_upper"], 60)
        self.assertEqual(helpers["dlarfg_dlamch_s_and_e_flops_upper"], 90)
        self.assertEqual(helpers["combined_add_subtract_multiply_divide_upper"], 330)
        self.assertEqual(helpers["dlapy2_scalar_square_power_sites_separate"], 60)
        self.assertEqual(helpers["sensitivity_if_each_scalar_square_is_one_multiply"], 390)
        self.assertEqual(helpers["square_root_calls_upper"], 60)

    def test_helper_total_is_additive_to_direct_sites_without_overlap(self):
        ownership = source_bound()["ownership"]
        self.assertTrue(ownership["additional_to_dsytd2_partial_source_bound"])
        self.assertIn("do not add", ownership["dlarfg_direct_scalar_sites"])
        self.assertIn("do not add", ownership["dscal_vector_multiplications"])
        prior = dsytd2_source_bound()[
            "combined_partial_source_flops_excluding_unresolved_helpers"
        ]
        helper = source_bound()["covered_helper_arithmetic"]
        self.assertEqual(prior + helper["combined_add_subtract_multiply_divide_upper"], 59_240)
        self.assertEqual(
            prior + helper["sensitivity_if_each_scalar_square_is_one_multiply"],
            59_300,
        )

    def test_rejects_invalid_call_counts(self):
        for kwargs in (
            {"dlarfg_calls": -1},
            {"dlarfg_calls": True},
            {"dlapy2_calls_per_dlarfg": -1},
            {"dlapy2_calls_per_dlarfg": 1.5},
        ):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                source_bound(**kwargs)

    def test_does_not_authorize_profile_or_claim_complete_counter(self):
        eligibility = source_bound()["eligibility"]
        self.assertFalse(eligibility["complete_eigensolver_bound"])
        self.assertFalse(eligibility["full_counter"])
        self.assertFalse(eligibility["parity_eligible"])
        self.assertFalse(eligibility["profile_or_fit_authorized"])


if __name__ == "__main__":
    unittest.main()

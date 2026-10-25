import unittest

from tools.v212_dnrm2_reference_source_bound import source_bound


class Dnrm2ReferenceSourceBoundTests(unittest.TestCase):
    def test_n32_dlarfg_call_shapes_and_upper_totals(self):
        report = source_bound()
        totals = report["source_arithmetic_upper"]
        summary = report["call_shape_summary"]
        self.assertEqual(summary["total_calls_upper"], 60)
        self.assertEqual(summary["length_one_calls_upper"], 2)
        self.assertEqual(summary["length_greater_than_one_calls_upper"], 58)
        self.assertEqual(totals["add_subtract_multiply_divide"], 2_154)
        self.assertEqual(totals["scalar_square_power_sites_separate"], 1_046)
        self.assertEqual(totals["sensitivity_if_each_power_is_one_multiply"], 3_200)
        self.assertEqual(totals["square_root_calls_separate"], 176)

    def test_length_one_reference_source_is_not_a_fast_return(self):
        report = source_bound()
        first = report["per_reflector"][0]["one_call_upper"]
        self.assertEqual(first["arithmetic_flops"], 4)
        self.assertEqual(first["scalar_square_power_sites"], 1)
        self.assertEqual(first["square_root_calls"], 1)
        self.assertFalse(report["call_shape_summary"]["reference_length_one_fast_return"])

    def test_source_and_binary_paths_are_not_additive(self):
        self.assertFalse(source_bound()["separate_from_binary_candidate"]["additive"])

    def test_rejects_wrong_order_or_invalid_call_bound(self):
        for kwargs in (
            {"n": 31},
            {"calls_per_reflector": -1},
            {"calls_per_reflector": True},
        ):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                source_bound(**kwargs)

    def test_does_not_claim_complete_eigensolver_or_open_gate(self):
        eligibility = source_bound()["eligibility"]
        self.assertFalse(eligibility["complete_eigensolver_bound"])
        self.assertFalse(eligibility["full_counter"])
        self.assertFalse(eligibility["parity_eligible"])
        self.assertFalse(eligibility["profile_or_fit_authorized"])


if __name__ == "__main__":
    unittest.main()

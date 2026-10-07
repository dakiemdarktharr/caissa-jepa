import unittest

from tools.v212_dsyevd_source_inventory import source_inventory


class DsyevdSourceInventoryTests(unittest.TestCase):
    def test_conditional_components_include_dlascl_machine_helper(self):
        report = source_inventory()
        components = report["non_overlapping_components"]
        total = report["conditional_source_arithmetic_interval"]
        self.assertEqual(components["driver_direct_and_dscal"], {
            "minimum": 2,
            "maximum": 36,
        })
        self.assertEqual(components["driver_dlamch_s_and_p_plus_dlansy_m"], 4)
        self.assertEqual(components["conditional_dlascl_body"]["arithmetic_upper_per_call"], 532)
        self.assertEqual(
            components["conditional_dlascl_dlamch_s_helper"]["operations_per_call"],
            2,
        )
        self.assertEqual(
            total["add_subtract_multiply_divide"],
            {"minimum": 6, "maximum": 574},
        )
        self.assertEqual(total["square_root_calls"], {"minimum": 2, "maximum": 2})

    def test_calls_and_helper_work_remain_in_separate_units(self):
        activity = source_inventory()["non_flop_helper_activity"]
        self.assertEqual(activity["dlansy_m_triangle_entries"], 528)
        self.assertEqual(activity["dlascl_matrix_scale_calls"], {"minimum": 0, "maximum": 1})
        self.assertEqual(activity["dscal_rescale_calls"], {"minimum": 0, "maximum": 1})
        self.assertEqual(activity["dscal_rescale_vector_multiplications"], 32)

    def test_driver_inventory_does_not_clear_eigensolver_or_profile_gate(self):
        eligibility = source_inventory()["eligibility"]
        self.assertFalse(eligibility["complete_dsyevd_bound"])
        self.assertFalse(eligibility["complete_eigensolver_bound"])
        self.assertFalse(eligibility["full_counter"])
        self.assertFalse(eligibility["parity_eligible"])
        self.assertFalse(eligibility["profile_or_fit_authorized"])


if __name__ == "__main__":
    unittest.main()

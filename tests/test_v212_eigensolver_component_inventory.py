import unittest

from tools.v212_eigensolver_component_inventory import source_inventory


class EigensolverComponentInventoryTests(unittest.TestCase):
    def test_component_maxima_are_composed_from_disjoint_owners(self):
        report = source_inventory()
        components = report["covered_reference_source_components"]
        total = report["sum_of_component_maxima"]
        self.assertEqual(components["dsyevd_driver_and_conditional_scaling"]["maximum"], 574)
        self.assertEqual(components["dsytd2_rank_updates_and_dlarfg_direct_sites"]["maximum"], 58_910)
        self.assertEqual(components["dlarfg_dlapy2_dlamch_helpers"]["maximum"], 330)
        self.assertEqual(components["dlarfg_dnrm2_helper"]["maximum"], 2_154)
        self.assertEqual(components["dsterf_and_separately_owned_helpers"]["maximum"], 432_709)
        self.assertEqual(total["add_subtract_multiply_divide"], 494_677)
        self.assertEqual(total["power_sites_separate"], 2_114)
        self.assertEqual(total["sensitivity_if_each_power_maps_to_one_multiply"], 496_791)
        self.assertEqual(total["square_root_calls_separate"], 2_254)

    def test_provenance_and_gates_are_not_overstated(self):
        report = source_inventory()
        self.assertIn("mix", report["provenance_caveat"])
        self.assertIn("may not be jointly attainable", report["sum_of_component_maxima"]["interpretation"])
        eligibility = report["eligibility"]
        self.assertFalse(eligibility["complete_eigensolver_bound"])
        self.assertFalse(eligibility["full_counter"])
        self.assertFalse(eligibility["parity_eligible"])
        self.assertFalse(eligibility["graph_freeze"])
        self.assertFalse(eligibility["profile_or_fit_authorized"])


if __name__ == "__main__":
    unittest.main()

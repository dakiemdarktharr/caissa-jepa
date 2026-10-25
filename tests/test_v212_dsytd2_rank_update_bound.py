from __future__ import annotations

import unittest

from tools.v212_dsytd2_rank_update_bound import source_bound


class Dsytd2RankUpdateBoundTests(unittest.TestCase):
    def test_reference_32_by_32_rank_update_subtotal(self):
        report = source_bound()
        self.assertEqual(report["schema"], "caissa.v212.dsytd2-partial-bound.v02")
        self.assertEqual(report["active_reflector_orders_included"], [2, 31])
        self.assertEqual(
            report["reference_rank_update_flops_upper"],
            47_165,
        )
        dlarfg = report["dlarfg_partial_upper_excluding_helper_internals"]
        self.assertEqual(dlarfg["nontrivial_calls_upper"], 30)
        self.assertEqual(dlarfg["vector_elements_per_pass"], 465)
        self.assertEqual(dlarfg["dscal_vector_multiply_flops_upper"], 9_765)
        self.assertEqual(dlarfg["direct_scalar_flops_upper"], 1_980)
        self.assertEqual(dlarfg["partial_flops_upper"], 11_745)
        self.assertEqual(report["combined_partial_source_flops_excluding_unresolved_helpers"], 58_910)
        self.assertEqual(len(report["per_active_order"]), 30)
        self.assertEqual(report["per_active_order"][0]["rank_update_flops_upper"], 40)
        self.assertEqual(report["per_active_order"][-1]["rank_update_flops_upper"], 4_187)

    def test_scope_does_not_claim_complete_eigensolver_or_parity(self):
        eligibility = source_bound()["eligibility"]
        self.assertFalse(eligibility["complete_dsytd2_bound"])
        self.assertFalse(eligibility["complete_eigensolver_bound"])
        self.assertFalse(eligibility["full_counter"])
        self.assertFalse(eligibility["parity_eligible"])
        self.assertFalse(eligibility["profile_or_fit_authorized"])

    def test_input_validation(self):
        for n in (0, 1, 2, True, 32.0):
            with self.subTest(n=n), self.assertRaises(ValueError):
                source_bound(n)


if __name__ == "__main__":
    unittest.main()

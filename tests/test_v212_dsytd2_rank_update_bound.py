from __future__ import annotations

import unittest

from tools.v212_dsytd2_rank_update_bound import source_bound


class Dsytd2RankUpdateBoundTests(unittest.TestCase):
    def test_reference_32_by_32_rank_update_subtotal(self):
        report = source_bound()
        self.assertEqual(report["active_reflector_orders_included"], [2, 31])
        self.assertEqual(
            report["maximum_reference_rank_update_flops_excluding_dlarfg"],
            47_165,
        )
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

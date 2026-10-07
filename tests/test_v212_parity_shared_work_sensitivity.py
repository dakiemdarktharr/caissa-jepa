import unittest

from tools.v212_parity_shared_work_sensitivity import ARMS, sensitivity


class ParitySharedWorkSensitivityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = sensitivity()

    def test_all_valid_subtotals_require_large_common_work_in_dilution_scenario(self):
        report = self.report
        self.assertEqual(report["input_mask_fixture"],
                         "illustrative all-64-valid masks at H1/H2/H4")
        self.assertEqual(report["widest_endpoints"]["max_upper_arm"],
                         "recursive-raw-state")
        self.assertEqual(report["widest_endpoints"]["min_lower_arm"],
                         "direct-leaf-value")
        self.assertEqual(report["common_omitted_flops_required_per_update"],
                         446_264_889)
        common = report["common_omitted_flops_required_per_update"]
        widest = report["widest_endpoints"]
        self.assertLessEqual(
            (widest["max_upper"] + common) * 10_000,
            (widest["min_lower"] + common) * 10_500,
        )
        self.assertGreater(
            (widest["max_upper"] + common - 1) * 10_000,
            (widest["min_lower"] + common - 1) * 10_500,
        )
        self.assertEqual(
            report["common_omitted_flops_if_same_fixture_repeated_for_all_updates"],
            776_500_906_860,
        )
        self.assertFalse(report["coverage"]["parity_decision"])
        self.assertFalse(report["coverage"]["full_counter"])

    def test_tolerance_and_frozen_arm_contract_are_validated(self):
        with self.assertRaisesRegex(ValueError, "tolerance_basis_points"):
            sensitivity(tolerance_basis_points=10_000)
        ledger = {
            "schema": "caissa.v212.partial-flop-owner-ledger.v01",
            "scheduled_updates_not_aggregated": 1,
            "arms": {arm: {"partial_source_candidate_flops": {"lower": 1, "upper": 1}}
                     for arm in ARMS[:-1]},
        }
        with self.assertRaisesRegex(ValueError, "exactly the frozen six arms"):
            sensitivity(ledger)

    def test_invalid_source_interval_is_rejected(self):
        from tools.v212_partial_flop_ledger import accounting

        ledger = accounting()
        ledger["arms"][ARMS[0]]["partial_source_candidate_flops"] = {
            "lower": 3,
            "upper": 2,
        }
        with self.assertRaisesRegex(ValueError, "invalid partial source interval"):
            sensitivity(ledger)


if __name__ == "__main__":
    unittest.main()

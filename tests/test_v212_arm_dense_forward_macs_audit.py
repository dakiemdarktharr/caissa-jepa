import unittest

from tools.v212_arm_dense_forward_macs_audit import inventory, macs


class ArmDenseForwardMacsAuditTests(unittest.TestCase):
    def test_dense_mac_counts_match_declared_shapes_and_horizon_graphs(self):
        report = inventory()
        self.assertEqual(report["arm_dense_forward_macs"], {
            "multi-step-jepa": 37_536,
            "single-pair-jepa": 24_864,
            "recursive-raw-state": 56_544,
            "value-only-latent-rollout": 18_528,
            "direct-leaf-value": 14_816,
            "single-horizon-jepa": 24_864,
        })

    def test_raw_state_delta_is_reported_as_static_mac_difference(self):
        report = inventory()
        counts = report["arm_dense_forward_macs"]
        self.assertEqual(counts["recursive-raw-state"]
                         - counts["multi-step-jepa"], 19_008)
        self.assertAlmostEqual(
            report["relative_to_multi_step_jepa"]["recursive-raw-state"],
            19_008 / 37_536)
        self.assertIn("not a training-FLOP measurement or parity decision",
                      report["limitations"][-1])

    def test_mac_dimension_validation_rejects_bad_shapes(self):
        with self.assertRaises(TypeError):
            macs((104, True))
        with self.assertRaises(ValueError):
            macs((0, 32))


if __name__ == "__main__":
    unittest.main()

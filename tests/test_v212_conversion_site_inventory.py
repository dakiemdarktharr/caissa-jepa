import unittest

from tools.v212_conversion_site_inventory import (
    array_request_cardinality,
    collect_conversion_inventory,
    inventory_sources,
)
from tools.v212_source_counter_reconciliation import reconcile_source


class ConversionSiteInventoryTests(unittest.TestCase):
    def test_inventory_lists_explicit_conversion_calls_without_claiming_runtime_casts(self):
        report = inventory_sources({
            "fixture.py": (
                "x = float(total)\n"
                "y = int(mask.sum())\n"
                "z = np.asarray(batch, dtype=np.float64)\n"
                "a = np.array(batch)\n"
            ),
        })
        module = report["modules"]["fixture.py"]
        self.assertEqual(module["site_count"], 3)
        self.assertEqual(module["sites_by_category"], {
            "numpy_array_dtype_request": 1,
            "python_scalar_float": 1,
            "python_scalar_int": 1,
        })
        array = next(row for row in module["sites"] if row["target"] == "np.asarray")
        self.assertEqual(array["dtype_argument"], "np.float64")
        self.assertFalse(array["runtime_cast_or_copy_proven"])
        self.assertFalse(report["coverage"]["runtime_conversion_behavior_verified"])
        self.assertFalse(report["coverage"]["parity_eligible"])

    def test_current_conversion_sites_are_reconciled_to_partial_owner(self):
        inventory = collect_conversion_inventory()
        crosswalk = reconcile_source()
        indexed = {
            (path, site["line"], site["detail"]): site
            for path, module in crosswalk["modules"].items()
            for site in module["sites"]
            if site["node"] == "Call"
        }
        conversion_sites = 0
        for path, module in inventory["modules"].items():
            for conversion in module["sites"]:
                conversion_sites += 1
                row = indexed[(path, conversion["line"], conversion["target"])]
                self.assertEqual(row["owner"], "tools/v212_conversion_site_inventory.py")
                if conversion["target"] == "np.asarray":
                    self.assertEqual(row["status"], "candidate_owner_partial")
                    self.assertIn("actual cast, hidden copy", row["scope"])
                else:
                    self.assertEqual(row["status"], "reported_separately")
        self.assertGreater(conversion_sites, 0)
        self.assertEqual(sum(
            module["sites_by_category"]["python_scalar_float"]
            for module in inventory["modules"].values()), 18)
        self.assertEqual(sum(
            module["sites_by_category"]["python_scalar_int"]
            for module in inventory["modules"].values()), 14)
        self.assertEqual(sum(
            module["sites_by_category"]["numpy_array_dtype_request"]
            for module in inventory["modules"].values()), 13)
        self.assertFalse(crosswalk["coverage"]["full_counter"])
        self.assertFalse(crosswalk["coverage"]["parity_eligible"])

    def test_array_request_cardinality_is_shape_based_and_keeps_cost_unverified(self):
        report = array_request_cardinality()
        self.assertEqual(report["preflight"]["finite_array_helper_calls"], 12)
        self.assertEqual(report["preflight"]["requested_elements_total"], 98_496)
        self.assertEqual(report["loss_grad"]["common_requested_elements"], 16_960)
        self.assertEqual(report["loss_grad"]["direct_leaf_branch_requested_elements"], 50_944)
        self.assertEqual(report["loss_grad"]["other_arm_branch_requested_elements"], 67_840)
        totals = {
            arm: row["total_requested_asarray_elements"]
            for arm, row in report["per_arm"].items()
        }
        self.assertEqual(totals, {
            "multi-step-jepa": 237_288,
            "single-pair-jepa": 237_288,
            "recursive-raw-state": 257_056,
            "value-only-latent-rollout": 230_920,
            "direct-leaf-value": 200_584,
            "single-horizon-jepa": 237_288,
        })
        self.assertEqual(
            report["per_arm"]["recursive-raw-state"]["explicit_optimizer_copy_output_elements"],
            73_760,
        )
        self.assertFalse(report["eligibility"]["runtime_casts_verified"])
        self.assertFalse(report["eligibility"]["parity_eligible"])


if __name__ == "__main__":
    unittest.main()

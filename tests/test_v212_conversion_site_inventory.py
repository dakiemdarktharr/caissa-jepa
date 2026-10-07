import unittest

from tools.v212_conversion_site_inventory import (
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
                    self.assertIn("actual cast, copy", row["scope"])
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


if __name__ == "__main__":
    unittest.main()

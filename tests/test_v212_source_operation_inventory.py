import unittest

from tools.v212_source_operation_inventory import (
    collect_source_inventory,
    inventory_sources,
)


class SourceOperationInventoryTests(unittest.TestCase):
    def test_inventory_is_deterministic_and_reports_unresolved_syntax(self):
        source = "result = (x @ w + b) ** 2\nif result > 0 and flag:\n    y = f(result[0])\n"
        first = inventory_sources({"fixture.py": source})
        second = inventory_sources({"fixture.py": source})
        self.assertEqual(first, second)
        module = first["modules"]["fixture.py"]
        self.assertEqual(module["binary_operators_by_syntax"], {
            "Add": 1, "MatMult": 1, "Pow": 1,
        })
        self.assertEqual(module["call_targets"][0]["target"], "f")
        self.assertTrue(all(site["semantic_classification"] ==
                            "unresolved_by_syntax_inventory" for site in module["sites"]))
        self.assertFalse(first["coverage"]["complete_operation_semantics"])
        self.assertFalse(first["coverage"]["parity_eligible"])

    def test_inventory_sorts_files_and_calls_and_hashes_source_bytes(self):
        report = inventory_sources({
            "z.py": "b = g(a)\n",
            "a.py": "x = np.mean(y)\n",
        })
        self.assertEqual(list(report["modules"]), ["a.py", "z.py"])
        self.assertEqual(report["modules"]["a.py"]["call_targets"][0]["target"], "np.mean")
        self.assertEqual(report["modules"]["z.py"]["source_sha256"],
                         "07425de44cad3ef2c798c1debd4047907f791b578b945ecc7ba13177b3b32980")

    def test_current_model_and_optimizer_sites_are_included(self):
        report = collect_source_inventory()
        self.assertEqual(set(report["modules"]), {
            "two_player/v212_model.py",
            "two_player/v212_scratch_optimizer.py",
        })
        model = report["modules"]["two_player/v212_model.py"]
        targets = {row["target"] for row in model["call_targets"]}
        self.assertIn("np.linalg.eigvalsh", targets)
        self.assertIn("z0.std", targets)
        self.assertIn("np.count_nonzero", targets)
        self.assertGreater(model["syntax_site_count"], 600)
        self.assertFalse(report["coverage"]["parity_eligible"])


if __name__ == "__main__":
    unittest.main()

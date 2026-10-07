import unittest

from tools.v212_source_counter_reconciliation import reconcile_source


class SourceCounterReconciliationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = reconcile_source()

    def test_every_inventory_site_has_a_source_bound_disposition(self):
        report = self.report
        modules = report["modules"]
        self.assertEqual(set(modules), {
            "two_player/v212_model.py",
            "two_player/v212_scratch_optimizer.py",
        })
        for module in modules.values():
            self.assertEqual(module["syntax_site_count"], len(module["sites"]))
            self.assertTrue(all(site["status"] and "scope" in site for site in module["sites"]))
            self.assertTrue(module["source_sha256"])
        self.assertFalse(report["coverage"]["all_sites_have_a_validated_cost_owner"])
        self.assertFalse(report["coverage"]["parity_eligible"])
        self.assertEqual(sum(report["disposition_counts"].values()),
                         sum(module["syntax_site_count"] for module in modules.values()))
        self.assertEqual(report["crosswalk_sha256"], reconcile_source()["crosswalk_sha256"])
        self.assertIn("<none>", report["candidate_owner_or_none_site_counts"])

    def test_specific_fp_owners_and_blocking_gaps_are_distinguished(self):
        model = self.report["modules"]["two_player/v212_model.py"]["sites"]
        matmuls = [site for site in model if site["node"] == "BinOp"
                   and site["detail"] == "MatMult"]
        squares = [site for site in model if site["node"] == "BinOp"
                   and site["detail"] == "Pow"]
        eigensolvers = [site for site in model if site["node"] == "Call"
                        and site["detail"] == "np.linalg.eigvalsh"]
        self.assertGreater(len(matmuls), 0)
        self.assertTrue(all(site["owner"] == "tools/v212_model_matmul_flop_accounting.py"
                            for site in matmuls))
        self.assertTrue(all(site["owner"] == "tools/v212_model_square_flop_accounting.py"
                            for site in squares))
        self.assertEqual(len(eigensolvers), 1)
        self.assertEqual(eigensolvers[0]["status"], "blocking_unresolved")
        self.assertIsNone(eigensolvers[0]["owner"])

    def test_preflight_is_not_confused_with_loss_graph_or_objective_reductions(self):
        model = self.report["modules"]["two_player/v212_model.py"]["sites"]
        scratch = self.report["modules"]["two_player/v212_scratch_optimizer.py"]["sites"]
        calls = [site for site in model if site["node"] == "Call"]
        count_nonzero = next(site for site in calls if site["detail"] == "np.count_nonzero")
        preflight_any = next(site for site in calls
                             if site["detail"] == "np.any" and site["function"] == "preflight_batch")
        finite_array_all = next(site for site in calls
                                if site["detail"] == "np.all" and site["function"] == "_finite_array")
        finite_array_isfinite = next(site for site in calls
                                     if site["detail"] == "np.isfinite" and site["function"] == "_finite_array")
        dtype_conversion = next(site for site in calls
                                if site["detail"] == "np.asarray" and site["function"] == "_finite_array")
        grad_any = next(site for site in calls
                        if site["detail"].endswith(".any") and site["function"] == "loss_grad")
        self.assertEqual(count_nonzero["status"], "candidate_owner_partial")
        self.assertEqual(preflight_any["status"], "candidate_owner_partial")
        self.assertEqual(finite_array_all["status"], "candidate_owner_partial")
        self.assertEqual(finite_array_isfinite["owner"], "tools/v212_preflight_scan_accounting.py")
        self.assertEqual(dtype_conversion["status"], "explicitly_unresolved")
        self.assertIn("dtype conversion", dtype_conversion["scope"])
        self.assertEqual(grad_any["status"], "explicitly_unresolved_non_fp")
        bool_mask_sum = next(site for site in calls
                             if site["detail"] == "mask.sum" and site["function"] == "loss_grad")
        self.assertEqual(bool_mask_sum["status"], "explicitly_unresolved_non_fp")
        numeric_loss_mean = next(site for site in calls
                                 if site["detail"] == "np.mean" and site["function"] == "loss_grad")
        self.assertEqual(numeric_loss_mean["owner"], "tools/v212_model_reduction_shape_accounting.py")
        optimizer_norm_sum = next(site for site in scratch
                                  if site["node"] == "Call" and site["detail"] == "np.sum")
        self.assertEqual(optimizer_norm_sum["owner"], "tools/v212_optimizer_flop_accounting.py")

    def test_augmented_assignments_have_contextual_candidate_or_unresolved_disposition(self):
        model = self.report["modules"]["two_player/v212_model.py"]["sites"]
        sites = [site for site in model if site["node"] == "AugAssign"]
        self.assertEqual(len(sites), 37)
        owners = {site["target"]: site["owner"] for site in sites}
        self.assertEqual(owners["grad['pw']"], "tools/v212_gradient_accumulation_accounting.py")
        self.assertEqual(owners["dlogits"], "tools/v212_policy_softmax_accounting.py")
        self.assertEqual(owners["metrics['executed_predictor_calls']"], None)
        self.assertTrue(all(site["status"] and site["scope"] for site in sites))


if __name__ == "__main__":
    unittest.main()

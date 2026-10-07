import hashlib
import unittest
from pathlib import Path

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
        self.assertTrue(report["coverage"]["all_analysis_sources_present"])
        self.assertTrue(report["coverage"]["all_candidate_owner_sources_present"])
        referenced_owners = {
            site["owner"]
            for module in modules.values()
            for site in module["sites"]
            if site["owner"] is not None
        }
        self.assertEqual(referenced_owners,
                         set(report["candidate_owner_source_hashes"]))

    def test_report_binds_classifier_inventory_and_candidate_owner_sources(self):
        root = Path(__file__).resolve().parents[1]
        report = self.report
        for path, record in report["analysis_source_hashes"].items():
            self.assertTrue(record["exists"])
            expected = hashlib.sha256((root / path).read_bytes()).hexdigest()
            self.assertEqual(record["source_sha256"], expected)
        for path, record in report["candidate_owner_source_hashes"].items():
            self.assertTrue(record["exists"])
            expected = hashlib.sha256((root / path).read_bytes()).hexdigest()
            self.assertEqual(record["source_sha256"], expected)

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
        self.assertEqual(len(sites), 40)
        owners = {site["target"]: site["owner"] for site in sites}
        self.assertEqual(owners["grad['pw']"], "tools/v212_gradient_accumulation_accounting.py")
        self.assertEqual(owners["dlogits"], "tools/v212_policy_softmax_accounting.py")
        self.assertEqual(owners["metrics['executed_predictor_prefix_invocations']"], None)
        self.assertEqual(owners["metrics['executed_predictor_active_examples']"], None)
        self.assertTrue(all(site["status"] and site["scope"] for site in sites))

    def test_scratch_optimizer_arithmetic_sites_map_to_its_analytical_owner(self):
        scratch = self.report["modules"]["two_player/v212_scratch_optimizer.py"]["sites"]
        arithmetic = [site for site in scratch
                      if site["function"] == "scratch_adam_ema_step"
                      and site["node"] == "BinOp"
                      and site["detail"] in {"Add", "Sub", "Mult", "Div"}]
        self.assertGreater(len(arithmetic), 0)
        self.assertTrue(all(site["status"] == "candidate_owner" for site in arithmetic))
        self.assertTrue(all(site["owner"] == "tools/v212_optimizer_flop_accounting.py"
                            for site in arithmetic))
        self.assertTrue(all("branch interval" in site["scope"] for site in arithmetic))
        self.assertFalse(self.report["coverage"]["all_sites_have_a_validated_cost_owner"])
        self.assertFalse(self.report["coverage"]["full_counter"])

    def test_regularizer_arithmetic_sites_follow_disjoint_subcounter_owners(self):
        model = self.report["modules"]["two_player/v212_model.py"]["sites"]
        sites = [site for site in model if site["function"] == "_regularize"]
        arithmetic = [site for site in sites
                      if site["node"] == "BinOp"
                      and site["detail"] in {"Add", "Sub", "Mult", "Div"}]
        self.assertGreater(len(arithmetic), 0)
        integer_shapes = [site for site in arithmetic
                          if site["source"] in {"d * n", "n * d"}]
        self.assertEqual(len(integer_shapes), 2)
        self.assertTrue(all(site["status"] == "reported_separately"
                            and site["owner"] == "tools/v212_regularizer_elementwise_accounting.py"
                            for site in integer_shapes))
        effective_rank = [site for site in arithmetic
                          if "spectrum" in site["source"] or "probabilities" in site["source"]]
        self.assertEqual(len(effective_rank), 2)
        self.assertTrue(all(site["status"] == "candidate_owner"
                            and site["owner"] == "tools/v212_effective_rank_branch_accounting.py"
                            for site in effective_rank))
        regularizer = [site for site in arithmetic if site not in integer_shapes + effective_rank]
        self.assertTrue(all(site["status"] == "candidate_owner"
                            and site["owner"] == "tools/v212_regularizer_elementwise_accounting.py"
                            for site in regularizer))
        unary = [site for site in sites if site["node"] == "UnaryOp" and site["detail"] == "USub"]
        self.assertEqual(len(unary), 2)
        self.assertTrue(all(site["status"] == "reported_separately" for site in unary))

    def test_loss_graph_arithmetic_is_joined_to_disjoint_partial_owners(self):
        model = self.report["modules"]["two_player/v212_model.py"]["sites"]
        sites = [site for site in model
                 if site["function"] == "loss_grad" and site["node"] == "BinOp"]
        self.assertTrue(sites)
        unresolved_arithmetic = [site for site in sites
                                 if site["detail"] in {"Add", "Sub", "Mult", "Div"}
                                 and site["status"] in {
                                     "explicitly_unresolved",
                                     "explicitly_unresolved_or_context_owned",
                                 }]
        self.assertEqual(unresolved_arithmetic, [])

        by_source = {}
        for site in sites:
            by_source.setdefault(site["source"], []).append(site)

        expected = {
            "masked_logits - np.max(masked_logits, axis=1, keepdims=True)":
                "tools/v212_policy_softmax_accounting.py",
            "root_value - np.asarray(batch['value'], dtype=np.float64)":
                "tools/v212_model_loss_residual_accounting.py",
            "2.0 * scale / FEATURE_SIZE * delta":
                "tools/v212_objective_gradient_elementwise_accounting.py",
            "2.0 * scale / d * delta":
                "tools/v212_objective_gradient_elementwise_accounting.py",
            "0.1 * dreg": "tools/v212_regularizer_elementwise_accounting.py",
            "policy_loss + root_loss + 0.1 * variance_loss + 0.01 * covariance_loss":
                "tools/v212_regularizer_elementwise_accounting.py",
            "dstate[step][rows] * (1.0 - znext ** 2)":
                "tools/v212_model_activation_flop_accounting.py",
            "outcome_loss + rollout_loss + raw_loss":
                "tools/v212_objective_scalar_accounting.py",
            "raw_feature_grads[step - 1][rows] + de @ p['ew'].T":
                "tools/v212_gradient_accumulation_accounting.py",
        }
        for source, owner in expected.items():
            with self.subTest(source=source):
                self.assertIn(source, by_source)
                self.assertTrue(all(site["status"] == "candidate_owner"
                                    and site["owner"] == owner
                                    for site in by_source[source]))

        index_sites = [site for site in sites if site["source"] == "step - 1"]
        self.assertTrue(index_sites)
        self.assertTrue(all(site["status"] == "reported_separately"
                            and site["owner"] is None for site in index_sites))
        bitwise_preflight = [site for site in model
                             if site["function"] == "preflight_batch"
                             and site["node"] == "BinOp"
                             and site["detail"] in {"BitAnd", "BitOr"}]
        self.assertEqual(len(bitwise_preflight), 12)
        self.assertTrue(all(site["status"] == "candidate_owner_partial"
                            and site["owner"] == "tools/v212_preflight_bitwise_accounting.py"
                            for site in bitwise_preflight))
        comparison_preflight = [site for site in model
                                if site["node"] == "Compare"
                                and site.get("function") in {"preflight_batch", "_finite_array"}]
        self.assertEqual(len(comparison_preflight), 13)
        self.assertEqual(sum(site["function"] == "preflight_batch"
                             for site in comparison_preflight), 12)
        self.assertEqual(sum(site["function"] == "_finite_array"
                             for site in comparison_preflight), 1)
        self.assertTrue(all(site["status"] == "candidate_owner_partial"
                            and site["owner"] == "tools/v212_preflight_scan_accounting.py"
                            for site in comparison_preflight))
        self.assertTrue(all("runtime cost remain open" in site["scope"]
                            for site in comparison_preflight))
        inverted_preflight = [site for site in model
                              if site["node"] == "UnaryOp"
                              and site.get("function") == "preflight_batch"
                              and site["detail"] == "Invert"]
        self.assertEqual(len(inverted_preflight), 13)
        self.assertTrue(all(site["status"] == "candidate_owner_partial"
                            and site["owner"] == "tools/v212_preflight_scan_accounting.py"
                            for site in inverted_preflight))
        self.assertTrue(all("runtime cost remain open" in site["scope"]
                            for site in inverted_preflight))
        self.assertFalse(self.report["coverage"]["full_counter"])
        self.assertFalse(self.report["coverage"]["graph_freeze_eligible"])


if __name__ == "__main__":
    unittest.main()

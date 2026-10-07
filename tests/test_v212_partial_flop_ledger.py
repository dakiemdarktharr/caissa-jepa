import unittest

import numpy as np

from tools.v212_model_matmul_flop_accounting import ARMS
from tools.v212_partial_flop_ledger import OWNERSHIP, SCHEMA, accounting


class PartialFlopLedgerTests(unittest.TestCase):
    def test_all_arm_partial_totals_equal_owned_components(self):
        report = accounting()
        self.assertEqual(report["schema"], SCHEMA)
        self.assertEqual(tuple(report["arms"]), ARMS)
        self.assertEqual(report["mask_fixture"],
                         "illustrative all-64-valid masks at H1/H2/H4")
        self.assertEqual(set(OWNERSHIP.values()), {
            *next(iter(report["arms"].values()))["components_candidate_flops"].keys(),
            "optimizer_interval", "effective_rank_interval",
        })
        expected = {
            "multi-step-jepa": {"lower": 9_540_294, "upper": 9_540_390},
            "single-pair-jepa": {"lower": 7_885_496, "upper": 7_885_592},
            "recursive-raw-state": {"lower": 27_130_644, "upper": 27_130_740},
            "value-only-latent-rollout": {"lower": 7_038_991, "upper": 7_039_087},
            "direct-leaf-value": {"lower": 4_588_091, "upper": 4_588_187},
            "single-horizon-jepa": {"lower": 7_885_496, "upper": 7_885_592},
        }
        for details in report["arms"].values():
            components = details["components_candidate_flops"]
            base = sum(components.values())
            branches = details["branch_candidate_flop_intervals"]
            lower = base + branches["effective_rank_interval"]["lower"] \
                + branches["optimizer_interval"]["lower"]
            upper = base + branches["effective_rank_interval"]["upper"] \
                + branches["optimizer_interval"]["upper"]
            self.assertEqual(details["partial_source_candidate_flops"], {
                "lower": lower, "upper": upper,
            })
            self.assertLessEqual(lower, upper)
        self.assertEqual({
            arm: details["partial_source_candidate_flops"]
            for arm, details in report["arms"].items()
        }, expected)
        expected_tanh_calls = {
            "multi-step-jepa": 12,
            "single-pair-jepa": 10,
            "recursive-raw-state": 13,
            "value-only-latent-rollout": 9,
            "direct-leaf-value": 4,
            "single-horizon-jepa": 10,
        }
        expected_nonfp = {
            "multi-step-jepa": (16_640, 11_907, 9, 96_079),
            "single-pair-jepa": (12_544, 11_907, 9, 96_079),
            "recursive-raw-state": (18_688, 18_441, 11, 129_081),
            "value-only-latent-rollout": (10_496, 11_907, 9, 83_343),
            "direct-leaf-value": (4_224, 8_547, 7, 59_823),
            "single-horizon-jepa": (12_544, 11_907, 9, 96_079),
        }
        for arm, details in report["arms"].items():
            known = details["known_nonflop_or_unconverted_work"]
            self.assertEqual(known["tanh_calls"], expected_tanh_calls[arm])
            tanh_elements, sqrt_elements, sqrt_invocations, finite_predicates = expected_nonfp[arm]
            self.assertEqual(known["tanh_elements"], tanh_elements)
            self.assertEqual(known["policy_max_comparisons"], 4_096)
            self.assertEqual(known["policy_exp_elements"], 4_160)
            self.assertEqual(known["policy_log_elements"], 64)
            self.assertEqual(known["regularizer_integer_shape_multiplications"], 2)
            self.assertEqual(known["regularizer_max_comparisons"], 64)
            self.assertEqual(known["regularizer_sqrt_elements"], 32)
            self.assertEqual(known["latent_std_sqrt_elements"], 32)
            self.assertEqual(known["eigvalsh_calls"], 1)
            self.assertEqual(known["effective_rank_comparisons"], [1, 33])
            self.assertEqual(known["effective_rank_log_elements"], [0, 32])
            self.assertEqual(known["effective_rank_log_invocations"], [0, 1])
            self.assertEqual(known["effective_rank_exp_calls"], [0, 1])
            self.assertEqual(known["optimizer_scalar_powers"], 2)
            self.assertEqual(known["optimizer_sqrt_output_elements"], sqrt_elements)
            self.assertEqual(known["optimizer_sqrt_invocations"], sqrt_invocations)
            self.assertEqual(known["optimizer_second_moment_nonnegative_comparisons"],
                             sqrt_elements - 1)
            self.assertEqual(known["optimizer_clip_threshold_comparisons"], 1)
            self.assertEqual(known["optimizer_finite_value_predicates"], finite_predicates)

    def test_ledger_explicitly_withholds_parity_and_graph_freeze(self):
        coverage = accounting()["coverage"]
        self.assertFalse(coverage["complete"])
        self.assertFalse(coverage["parity_eligible"])
        self.assertFalse(coverage["graph_freeze_eligible"])
        self.assertIn("not bounds on total training FLOPs",
                      coverage["interval_semantics"])
        self.assertTrue(any("LAPACK" in x for x in coverage["excluded_or_unresolved"]))

    def test_direct_leaf_h4_guard_is_inherited(self):
        masks = {h: np.ones(64, dtype=bool) for h in (1, 2, 4)}
        masks[4][:] = False
        with self.assertRaisesRegex(ValueError, "valid H4"):
            accounting(masks)

    def test_masked_components_are_source_derived(self):
        masks = {
            1: np.array([True] * 32 + [False] * 32),
            2: np.array([True] * 16 + [False] * 48),
            4: np.array([True] * 8 + [False] * 56),
        }
        report = accounting(masks)
        self.assertEqual(report["mask_fixture"],
                         "caller-supplied masks; must be replay-derived before D03 use")
        self.assertEqual(tuple(report["arms"]), ARMS)
        expected = {
            "multi-step-jepa": {
                "model_matmul_flops": 4_398_592,
                "model_square_multiplications": 22_986,
                "loss_residual_subtractions": 1_912,
                "activation_excluding_squares": 18_720,
                "ordinary_reductions": 45_437,
                "horizon_objective_scalars": 46,
                "gradient_accumulation": 33_861,
                "target_gradient_multiplications": 1_792,
            },
            "single-pair-jepa": {
                "model_matmul_flops": 3_891_712,
                "model_square_multiplications": 20_426,
                "loss_residual_subtractions": 632,
                "activation_excluding_squares": 17_440,
                "ordinary_reductions": 42_879,
                "horizon_objective_scalars": 30,
                "gradient_accumulation": 32_581,
                "target_gradient_multiplications": 512,
            },
            "recursive-raw-state": {
                "model_matmul_flops": 8_555_008,
                "model_square_multiplications": 50_160,
                "loss_residual_subtractions": 11_208,
                "activation_excluding_squares": 35_744,
                "ordinary_reductions": 84_363,
                "horizon_objective_scalars": 46,
                "gradient_accumulation": 107_437,
                "target_gradient_multiplications": 11_088,
            },
            "value-only-latent-rollout": {
                "model_matmul_flops": 3_688_960,
                "model_square_multiplications": 19_402,
                "loss_residual_subtractions": 120,
                "activation_excluding_squares": 16_928,
                "ordinary_reductions": 41_856,
                "horizon_objective_scalars": 22,
                "gradient_accumulation": 32_069,
                "target_gradient_multiplications": 0,
            },
            "direct-leaf-value": {
                "model_matmul_flops": 2_899_456,
                "model_square_multiplications": 14_098,
                "loss_residual_subtractions": 72,
                "activation_excluding_squares": 11_360,
                "ordinary_reductions": 36_653,
                "horizon_objective_scalars": 3,
                "gradient_accumulation": 19_043,
                "target_gradient_multiplications": 0,
            },
            "single-horizon-jepa": {
                "model_matmul_flops": 4_094_464,
                "model_square_multiplications": 21_450,
                "loss_residual_subtractions": 1_144,
                "activation_excluding_squares": 17_952,
                "ordinary_reductions": 43_903,
                "horizon_objective_scalars": 30,
                "gradient_accumulation": 33_093,
                "target_gradient_multiplications": 1_024,
            },
        }
        for arm, component_expectations in expected.items():
            components = report["arms"][arm]["components_candidate_flops"]
            self.assertEqual(
                {key: components[key] for key in component_expectations},
                component_expectations,
            )
            self.assertEqual(components["policy_elementwise"], 12_608)
            self.assertEqual(components["regularizer_elementwise"], 18_568)


if __name__ == "__main__":
    unittest.main()

import unittest

from two_player.v212_pilot import (
    ARMS,
    VARIANTS,
    RandomInferenceModel,
    build_root_schedule,
    create_receipt,
    run_root_arm,
    schedule_sha256,
    verify_receipt,
)


class V212PilotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.roots = build_root_schedule()

    def test_root_schedule_is_deterministic_and_legal(self):
        repeated = build_root_schedule()
        self.assertEqual(schedule_sha256(self.roots), schedule_sha256(repeated))
        self.assertEqual(len(self.roots), len(VARIANTS) * 4)
        for game, root in zip(
            (game for game in VARIANTS for _ in range(4)), self.roots
        ):
            self.assertEqual(root.variant, game.name)
            self.assertIsNone(game.terminal(root.state))
            self.assertTrue(game.legal_actions(root.state))
            self.assertEqual(len(game.features(root.state)), 198)

    def test_initial_weights_are_paired_by_named_module(self):
        candidate = RandomInferenceModel("multi-step-jepa")
        single = RandomInferenceModel("single-pair-jepa")
        raw = RandomInferenceModel("recursive-raw-state-dynamics")
        self.assertTrue((candidate.encoder_w == single.encoder_w).all())
        self.assertTrue((candidate.encoder_w == raw.encoder_w).all())
        self.assertTrue((candidate.predictor_w == single.predictor_w).all())
        self.assertTrue((candidate.value_w == raw.value_w).all())

    def test_all_arms_run_without_outcome_fields(self):
        root = self.roots[0]
        game = VARIANTS[0]
        for arm in ARMS:
            result = run_root_arm(
                game, root, RandomInferenceModel(arm), node_cap=5_000,
                wall_cap_seconds=5.0,
            )
            self.assertEqual(result["variant"], game.name)
            self.assertEqual(result["arm"], arm)
            self.assertEqual(result["completed_depth"], 4)
            self.assertGreater(result["node_visits"], 0)
            self.assertGreaterEqual(result["transition_calls"], 0)
            self.assertTrue(all(value >= 0 for key, value in result.items()
                                if key.endswith("_calls")))
            self.assertFalse({"score", "outcome", "selected_action", "action_values"}
                             & set(result))

    def test_node_cap_stops_without_exceeding_limit(self):
        root = self.roots[0]
        result = run_root_arm(
            VARIANTS[0], root, RandomInferenceModel("multi-step-jepa"),
            node_cap=1, wall_cap_seconds=5.0,
        )
        self.assertEqual(result["node_visits"], 1)
        self.assertEqual(result["completed_depth"], 0)
        self.assertEqual(result["stop_reason"], "node_cap")

    def test_receipt_requires_complete_compute_only_schedule(self):
        results = []
        for root in self.roots:
            for arm in ARMS:
                results.append({
                    "variant": root.variant,
                    "arm": arm,
                    "root_target_ply": root.target_ply,
                    "root_state_sha256": root.state_sha256,
                    "completed_depth": 4,
                    "fallback_used": False,
                    "fallback_action_available": True,
                    "stop_reason": "depth_4_complete",
                    "node_visits": 4,
                    "transition_calls": 3,
                    "encoder_calls": 1,
                    "predictor_calls": 2,
                    "decoder_calls": 0,
                    "value_calls": 1,
                    "model_calls": 4,
                    "terminal_nodes": 0,
                    "wall_seconds": 0.01,
                    "peak_sampled_rss_bytes": 1024,
                })
        receipt = create_receipt(results, self.roots, {
            "protocol": "0" * 64,
            "pilot_source": "1" * 64,
            "runner_source": "2" * 64,
            "rules_source": "3" * 64,
        })
        verify_receipt(receipt)
        receipt["results"][0]["score"] = 1.0
        with self.assertRaises(ValueError):
            verify_receipt(receipt)


if __name__ == "__main__":
    unittest.main()

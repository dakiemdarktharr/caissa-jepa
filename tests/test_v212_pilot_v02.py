import unittest

from two_player.v212_pilot import ARMS, build_root_schedule
from two_player.v212_pilot_v02 import (
    INIT_SEEDS,
    ROOT_COUNT_BY_PLY,
    ROOTS_PER_VARIANT,
    VARIANTS,
    RandomInferenceModel,
    build_root_schedule_v02,
    create_receipt,
    schedule_sha256_v02,
    verify_receipt_v02,
)


class V212PilotV02Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.roots = build_root_schedule_v02()

    def test_schedule_retains_v01_roots_and_has_distinct_variant_states(self):
        original = {(root.variant, root.target_ply): root
                    for root in build_root_schedule()}
        self.assertEqual(len(self.roots), len(VARIANTS) * ROOTS_PER_VARIANT)
        self.assertEqual(schedule_sha256_v02(self.roots),
                         schedule_sha256_v02(build_root_schedule_v02()))
        for scheduled in self.roots:
            root = scheduled.root
            if scheduled.ordinal == 0:
                self.assertEqual(root.state_sha256,
                                 original[(root.variant, root.target_ply)].state_sha256)
        for game in VARIANTS:
            fingerprints = [scheduled.root.state_sha256 for scheduled in self.roots
                            if scheduled.root.variant == game.name]
            self.assertEqual(len(fingerprints), len(set(fingerprints)))

    def test_additional_seed_windows_are_disjoint_and_above_v01_ranges(self):
        starts = [80000 + 64 * index for index in range(48)]
        windows = [set(range(start, start + 64)) for start in starts]
        self.assertEqual(len(set.union(*windows)), 48 * 64)
        self.assertTrue(all(start > 71734 for start in starts))
        for ply, count in ROOT_COUNT_BY_PLY.items():
            self.assertEqual(sum(root.root.target_ply == ply for root in self.roots),
                             len(VARIANTS) * count)
        self.assertEqual(len({(root.root.variant, root.root.target_ply,
                              root.ordinal) for root in self.roots}), len(self.roots))

    def test_weight_modules_are_paired_for_each_initialization(self):
        for seed in INIT_SEEDS:
            candidate = RandomInferenceModel("multi-step-jepa", seed=seed)
            single = RandomInferenceModel("single-pair-jepa", seed=seed)
            raw = RandomInferenceModel("recursive-raw-state-dynamics", seed=seed)
            self.assertTrue((candidate.encoder_w == single.encoder_w).all())
            self.assertTrue((candidate.encoder_w == raw.encoder_w).all())
            self.assertTrue((candidate.predictor_w == single.predictor_w).all())
            self.assertTrue((candidate.value_w == raw.value_w).all())

    def test_receipt_requires_full_compute_only_cell_roster(self):
        results = []
        for scheduled in self.roots:
            for seed in INIT_SEEDS:
                for arm in ARMS:
                    results.append({
                        "root_ordinal": scheduled.ordinal,
                        "initialization_seed": seed,
                        "variant": scheduled.root.variant,
                        "arm": arm,
                        "root_target_ply": scheduled.root.target_ply,
                        "root_state_sha256": scheduled.root.state_sha256,
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
        first_hash = self.roots[0].root.state_sha256
        warmups = {
            f"{seed}:{arm}": {
                "initialization_seed": seed,
                "arm": arm,
                "encoder_calls": 1,
                "predictor_calls": 1,
                "decoder_calls": 0,
                "value_calls": 1,
                "model_calls": 3,
                "transition_calls": 0 if arm == "direct-leaf-value" else 1,
                "wall_seconds": 0.01,
                "warmup_root_state_sha256": first_hash,
            }
            for seed in INIT_SEEDS for arm in ARMS
        }
        receipt = create_receipt(results, self.roots, {
            "protocol": "0" * 64,
            "pilot_source": "1" * 64,
            "runner_source": "2" * 64,
            "shared_pilot_source": "3" * 64,
            "rules_source": "4" * 64,
        }, warmups=warmups, runtime={
            "python": "3.11.9", "numpy": "2.4.6", "platform": "test",
            "machine": "x86_64", "cpu_count": 12,
        })
        verify_receipt_v02(receipt)
        receipt["results"][0]["score"] = 1
        with self.assertRaises(ValueError):
            verify_receipt_v02(receipt)


if __name__ == "__main__":
    unittest.main()

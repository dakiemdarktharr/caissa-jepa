import unittest

from tools.v28_match_power import (
    CHECKPOINT_SEEDS, COMPARISONS, GAMES, MARGIN, MATCHES_PER_CHECKPOINT,
    make_schedule, power_at_planned_blocks, power_scenarios,
    required_independent_blocks,
)


class MatchPowerTests(unittest.TestCase):
    def test_boundary_effect_cannot_be_declared_powered(self):
        with self.assertRaisesRegex(ValueError, "invalid"):
            required_independent_blocks(0.5, MARGIN)

    def test_sample_size_increases_with_variance_and_decreases_with_effect(self):
        low_noise = required_independent_blocks(0.25, 0.15)
        high_noise = required_independent_blocks(0.50, 0.15)
        small_effect = required_independent_blocks(0.50, 0.10)
        large_effect = required_independent_blocks(0.50, 0.20)
        self.assertLess(low_noise, high_noise)
        self.assertGreater(small_effect, large_effect)
        self.assertEqual(required_independent_blocks(0.50, 0.10), 951)
        self.assertEqual(len(power_scenarios()), 9)

    def test_planned_power_reports_marginal_and_dependence_free_joint_bound(self):
        marginal = power_at_planned_blocks(0.50, 0.10, 2400)
        scenario = next(
            row for row in power_scenarios()
            if row["paired_block_sd"] == 0.50 and row["true_effect"] == 0.10
        )
        self.assertAlmostEqual(scenario["marginal_power_at_planned_blocks"], marginal)
        self.assertAlmostEqual(
            scenario["joint_power_lower_bound_both_controls"],
            max(0.0, 1 - len(COMPARISONS) * (1 - marginal)),
        )
        self.assertGreater(scenario["joint_power_lower_bound_both_controls"], 0.98)

    def test_locked_schedule_is_reproducible_and_pairs_both_colors(self):
        first = make_schedule()
        second = make_schedule()
        self.assertEqual(first, second)
        self.assertEqual(len(first), len(GAMES) * len(COMPARISONS)
                         * len(CHECKPOINT_SEEDS) * MATCHES_PER_CHECKPOINT)
        self.assertTrue(all(row["color_assignments"] == [1, -1] for row in first))
        by_dimension = {}
        for row in first:
            key = (row["game"], row["comparison"], row["checkpoint_seed"])
            by_dimension.setdefault(key, set()).add(row["match_seed"])
        self.assertTrue(all(len(seeds) == MATCHES_PER_CHECKPOINT
                            for seeds in by_dimension.values()))
        one_game_comparison = [
            by_dimension[(GAMES[0], COMPARISONS[0], seed)]
            for seed in CHECKPOINT_SEEDS
        ]
        self.assertTrue(all(not (left & right)
                            for i, left in enumerate(one_game_comparison)
                            for right in one_game_comparison[i + 1:]))
        self.assertEqual(len({row["block_id"] for row in first}), len(first))

    def test_duplicate_checkpoint_seeds_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "duplicate"):
            make_schedule(checkpoint_seeds=(17, 17))


if __name__ == "__main__":
    unittest.main()

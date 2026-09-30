import unittest

from tools.v27_match_feasibility import GAME_CONFIGS, PAIRINGS, SEEDS, play, run_probe


class V27MatchFeasibilityTests(unittest.TestCase):
    def test_fixed_seed_match_is_reproducible_and_terminal(self):
        game = GAME_CONFIGS[0][1]
        first = play(game, 31415, "sanity-heuristic", "random")
        second = play(game, 31415, "sanity-heuristic", "random")
        self.assertEqual(first, second)
        self.assertIn(first["outcome_plus_perspective"], (-1, 0, 1))
        self.assertGreater(first["plies"], 0)
        self.assertEqual(len(first["final_state_sha256"]), 64)

    def test_probe_has_complete_paired_seat_schedule(self):
        result = run_probe()
        self.assertEqual(len(result["matches"]), 2 * len(GAME_CONFIGS) * len(PAIRINGS) * len(SEEDS))
        self.assertEqual(set(result["summary"]), {name for name, _ in GAME_CONFIGS})
        for game_name, _ in GAME_CONFIGS:
            rows = [row for row in result["matches"] if row["game"] == game_name]
            self.assertEqual(len(rows), 2 * len(PAIRINGS) * len(SEEDS))
            for pairing in PAIRINGS:
                for base_seed in SEEDS:
                    pair_rows = [row for row in rows if row["pairing"] == f"{pairing[0]}-vs-{pairing[1]}"
                                 and row["seed"] % 10000 == (base_seed + PAIRINGS.index(pairing) * 10000) % 10000]
                    self.assertEqual(len(pair_rows), 2)
                    self.assertEqual({row["seat_swap"] for row in pair_rows}, {False, True})

    def test_match_receipt_records_claim_boundary_and_valid_outcomes(self):
        result = run_probe()
        self.assertIn("not a strength benchmark", result["stage"])
        for row in result["matches"]:
            self.assertIn(row["outcome_plus_perspective"], (-1, 0, 1))
            self.assertGreater(row["plies"], 0)
            self.assertEqual(len(row["final_state_sha256"]), 64)


if __name__ == "__main__":
    unittest.main()

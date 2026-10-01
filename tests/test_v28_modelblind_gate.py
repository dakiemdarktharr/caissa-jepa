import unittest

from two_player.games import State
from tools.v28_modelblind_gate import (
    GAMES, action_to_adapter, action_to_reference, compare_rules,
    depth_two_values, run, schedule_roots,
)


class ModelBlindGateTests(unittest.TestCase):
    def test_padded_and_contiguous_action_encodings_round_trip(self):
        adapter = GAMES["connect4-gravity-4x5"][0]
        for action in (0, 3, 24, 27, 28):
            ref_action = action_to_reference(adapter, action)
            self.assertEqual(action_to_adapter(adapter, ref_action), action)
        reversi = GAMES["reversi6"][0]
        self.assertEqual(action_to_reference(reversi, 64), -1)
        self.assertEqual(action_to_adapter(reversi, -1), 64)

    def test_reference_rules_agree_on_initial_and_random_reachable_states(self):
        for name in GAMES:
            adapter, reference = GAMES[name]
            state = adapter.initial()
            self.assertGreater(compare_rules(adapter, reference, state), 0)
            import random
            rng = random.Random(843)
            for _ in range(8):
                if adapter.terminal(state) is not None:
                    break
                state = adapter.transition(state, rng.choice(adapter.legal_actions(state)))
                self.assertGreater(compare_rules(adapter, reference, state), 0)

    def test_schedule_is_reproducible_and_keeps_duplicate_dispositions(self):
        first, first_rejected, _ = schedule_roots("connect4-gravity-4x5", 12, 51, 900)
        second, second_rejected, _ = schedule_roots("connect4-gravity-4x5", 12, 51, 900)
        self.assertEqual(first, second)
        self.assertEqual(first_rejected, second_rejected)
        self.assertEqual(len(first), 12)
        self.assertTrue(all(row["disposition"] == "scheduled_root" for row in first))
        self.assertTrue(all(row["disposition"] in (
            "terminal_candidate", "duplicate_symmetry_candidate") for row in first_rejected))

    def test_depth_two_oracle_scores_an_immediate_win(self):
        game = GAMES["connect4-gravity-4x5"][0]
        board = [0] * 20
        board[15] = board[16] = board[17] = 1
        state = type(game.initial())(tuple(board), 1)
        values = depth_two_values(game, state)
        self.assertEqual(values[27], 1)

    def test_incomplete_schedule_cannot_pass_quota_or_gate(self):
        report = run("connect4-gravity-4x5", count=2, schedule_seed=51,
                     first_seed=900, nodes=100_000, seconds=0.25,
                     cache=10_000, min_ply=5, max_ply=11,
                     reversi_empty_min=5, reversi_empty_max=8,
                     max_episodes=1)
        self.assertEqual(report["summary"]["scheduled_roots"], 1)
        self.assertFalse(report["summary"]["candidate_quota_pass"])
        self.assertFalse(report["summary"]["oracle_coverage_pass"])
        self.assertFalse(report["summary"]["gate_pass"])

    def test_rule_differential_checks_terminal_status_after_root_action(self):
        class IncorrectTerminal:
            def __init__(self, base):
                self.base = base

            def __getattr__(self, name):
                return getattr(self.base, name)

            def terminal(self, state):
                return None

        adapter = GAMES["connect4-gravity-4x5"][0]
        reference = GAMES["connect4-gravity-4x5"][1]
        board = [0] * 20
        board[15] = board[16] = board[17] = 1
        state = State(tuple(board), 1)
        with self.assertRaisesRegex(AssertionError, "terminal disagreement after root action"):
            compare_rules(IncorrectTerminal(adapter), reference, state)


if __name__ == "__main__":
    unittest.main()

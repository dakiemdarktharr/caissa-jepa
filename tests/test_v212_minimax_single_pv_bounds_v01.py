import unittest

from two_player.games import BoardGame, State, exact_value
from two_player.v212_minimax_single_pv_bounds_v01 import minimax_single_pv_bounds


class MinimaxSinglePVBoundsTests(unittest.TestCase):
    def test_every_budget_contains_oracle_and_bounds_tighten(self):
        game = BoardGame("single-pv-tictactoe", 3, 3, 3)
        state = State((1, -1, 1, 1, -1, 0, 0, 0, 0), player=1)
        exact_actions = {
            action: -exact_value(game, game.transition(state, action))
            for action in game.legal_actions(state)
        }
        exact_root = max(exact_actions.values())
        executed = game.legal_actions(state)[-1]
        exact_regret = exact_root - exact_actions[executed]
        complete = minimax_single_pv_bounds(game, state, executed, 10_000)
        self.assertEqual(complete.root_value.lower, exact_root)
        self.assertEqual(complete.root_value.upper, exact_root)
        self.assertEqual(complete.regret.lower, exact_regret)
        self.assertEqual(complete.regret.upper, exact_regret)

        previous = None
        for budget in range(len(game.legal_actions(state)),
                            complete.transition_count + 1):
            result = minimax_single_pv_bounds(game, state, executed, budget)
            self.assertLessEqual(result.transition_count, budget)
            self.assertEqual(tuple(a for a, _ in result.action_values),
                             game.legal_actions(state))
            self.assertLessEqual(result.root_value.lower, exact_root)
            self.assertGreaterEqual(result.root_value.upper, exact_root)
            self.assertLessEqual(result.regret.lower, exact_regret)
            self.assertGreaterEqual(result.regret.upper, exact_regret)
            for action, interval in result.action_values:
                self.assertLessEqual(interval.lower, exact_actions[action])
                self.assertGreaterEqual(interval.upper, exact_actions[action])
            if previous is not None:
                self.assertGreaterEqual(result.root_value.lower,
                                        previous.root_value.lower)
                self.assertLessEqual(result.root_value.upper,
                                     previous.root_value.upper)
                self.assertGreaterEqual(result.regret.lower,
                                        previous.regret.lower)
                self.assertLessEqual(result.regret.upper,
                                     previous.regret.upper)
            previous = result

    def test_forced_pass_remains_a_complete_rule_transition(self):
        game = BoardGame("single-pv-reversi4", 4, 4, reversi=True)
        board = [1] * 16
        board[5] = 0
        board[6] = -1
        state = State(tuple(board), player=-1)
        exact_root = exact_value(game, state)
        self.assertEqual(game.legal_actions(state), (64,))
        partial = minimax_single_pv_bounds(game, state, 64, 1)
        self.assertEqual(partial.transition_count, 1)
        self.assertEqual(partial.action_values[0][1].lower, -1)
        solved = minimax_single_pv_bounds(game, state, 64, 2)
        self.assertEqual(solved.action_values[0][1].lower, exact_root)
        self.assertEqual(solved.action_values[0][1].upper, exact_root)

    def test_rejects_bool_action_and_budget_below_root_action_count(self):
        game = BoardGame("single-pv-tictactoe", 3, 3, 3)
        with self.assertRaises(ValueError):
            minimax_single_pv_bounds(game, game.initial(), True, 9)
        with self.assertRaises(ValueError):
            minimax_single_pv_bounds(game, game.initial(), 0, 8)


if __name__ == "__main__":
    unittest.main()

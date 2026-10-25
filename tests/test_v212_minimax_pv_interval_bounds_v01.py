import unittest

from two_player.games import BoardGame, State, exact_value
from two_player.v212_minimax_pv_interval_bounds_v01 import (
    minimax_pv_interval_bounds,
)


class MinimaxPVIntervalBoundsTests(unittest.TestCase):
    def test_all_budgets_contain_tiny_oracle_and_tighten_monotonically(self):
        game = BoardGame("interval-pv-tictactoe", 3, 3, 3)
        state = State((1, -1, 1, 1, -1, 0, 0, 0, 0), player=1)
        exact_actions = {
            action: -exact_value(game, game.transition(state, action))
            for action in game.legal_actions(state)
        }
        exact_root = max(exact_actions.values())
        executed = game.legal_actions(state)[-1]
        exact_regret = exact_root - exact_actions[executed]
        complete = minimax_pv_interval_bounds(game, state, executed, 10_000)
        self.assertEqual(complete.root_value.lower, exact_root)
        self.assertEqual(complete.root_value.upper, exact_root)
        self.assertEqual(complete.regret.lower, exact_regret)
        self.assertEqual(complete.regret.upper, exact_regret)
        previous = None
        for budget in range(len(game.legal_actions(state)),
                            complete.transition_count + 1):
            result = minimax_pv_interval_bounds(game, state, executed, budget)
            self.assertLessEqual(result.transition_count, budget)
            self.assertEqual(tuple(a for a, _ in result.action_values),
                             game.legal_actions(state))
            self.assertLessEqual(result.root_value.lower, exact_root)
            self.assertGreaterEqual(result.root_value.upper, exact_root)
            for action, interval in result.action_values:
                self.assertLessEqual(interval.lower, exact_actions[action])
                self.assertGreaterEqual(interval.upper, exact_actions[action])
            self.assertLessEqual(result.regret.lower, exact_regret)
            self.assertGreaterEqual(result.regret.upper, exact_regret)
            if previous is not None:
                self.assertGreaterEqual(result.root_value.lower,
                                        previous.root_value.lower)
                self.assertLessEqual(result.root_value.upper,
                                     previous.root_value.upper)
                self.assertGreaterEqual(result.regret.lower,
                                        previous.regret.lower)
                self.assertLessEqual(result.regret.upper,
                                     previous.regret.upper)
                prior_actions = dict(previous.action_values)
                for action, interval in result.action_values:
                    self.assertGreaterEqual(interval.lower,
                                            prior_actions[action].lower)
                    self.assertLessEqual(interval.upper,
                                         prior_actions[action].upper)
            previous = result

    def test_forced_reversi_pass_is_counted_and_exact_when_resolved(self):
        game = BoardGame("interval-pv-reversi4", 4, 4, reversi=True)
        board = [1] * 16
        board[5] = 0
        board[6] = -1
        state = State(tuple(board), player=-1)
        self.assertEqual(game.legal_actions(state), (64,))
        exact_root = exact_value(game, state)
        unresolved = minimax_pv_interval_bounds(game, state, 64, 1)
        self.assertEqual(unresolved.transition_count, 1)
        self.assertEqual(unresolved.action_values[0][1].lower, -1)
        resolved = minimax_pv_interval_bounds(game, state, 64, 2)
        self.assertLessEqual(resolved.transition_count, 2)
        self.assertEqual(resolved.action_values[0][1].lower, exact_root)
        self.assertEqual(resolved.action_values[0][1].upper, exact_root)

    def test_rejects_boolean_action_and_budget_below_root_enumeration(self):
        game = BoardGame("interval-pv-tictactoe", 3, 3, 3)
        state = game.initial()
        with self.assertRaises(ValueError):
            minimax_pv_interval_bounds(game, state, True, 9)
        with self.assertRaises(ValueError):
            minimax_pv_interval_bounds(game, state, 0, 8)


if __name__ == "__main__":
    unittest.main()

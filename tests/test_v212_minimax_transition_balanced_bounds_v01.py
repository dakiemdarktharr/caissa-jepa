import unittest

from two_player.games import BoardGame, State, exact_value
from two_player.v212_minimax_transition_balanced_bounds_v01 import (
    minimax_transition_balanced_bounds,
)


class MinimaxTransitionBalancedBoundsTests(unittest.TestCase):
    def test_budget_prefixes_contain_exact_values_and_never_exceed_cap(self):
        game = BoardGame("balanced-budget-tictactoe", 3, 3, 3)
        state = State((1, -1, 1,
                       1, -1, 0,
                       0, 0, 0), player=1)
        actions = game.legal_actions(state)
        exact_root = exact_value(game, state)
        exact_actions = {
            action: -exact_value(game, game.transition(state, action))
            for action in actions
        }
        best = max(exact_actions.values())
        executed = actions[-1]
        exact_regret = best - exact_actions[executed]
        complete = minimax_transition_balanced_bounds(game, state, executed,
                                                       100_000)
        previous = None

        for budget in range(len(actions), complete.transition_count + 1):
            result = minimax_transition_balanced_bounds(game, state, executed,
                                                        budget)
            self.assertLessEqual(result.transition_count, budget)
            self.assertEqual(tuple(a for a, _ in result.action_values), actions)
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
                for action, interval in result.action_values:
                    old = dict(previous.action_values)[action]
                    self.assertGreaterEqual(interval.lower, old.lower)
                    self.assertLessEqual(interval.upper, old.upper)
            previous = result

        self.assertEqual(complete.root_value.lower, exact_root)
        self.assertEqual(complete.root_value.upper, exact_root)
        self.assertEqual(complete.regret.lower, exact_regret)
        self.assertEqual(complete.regret.upper, exact_regret)

    def test_complete_root_enumeration_is_minimum_cap(self):
        game = BoardGame("balanced-budget-tictactoe", 3, 3, 3)
        state = game.initial()
        actions = game.legal_actions(state)
        with self.assertRaises(ValueError):
            minimax_transition_balanced_bounds(game, state, actions[0],
                                               len(actions) - 1)
        result = minimax_transition_balanced_bounds(game, state, actions[0],
                                                    len(actions))
        self.assertEqual(result.transition_count, len(actions))
        self.assertTrue(all(interval == (-1, 1) for _, interval in (
            (action, (value.lower, value.upper))
            for action, value in result.action_values)))

    def test_forced_pass_remains_the_only_root_action(self):
        game = BoardGame("balanced-budget-reversi4", 4, 4, reversi=True)
        board = [1] * 16
        board[1 * 4 + 1] = 0
        board[1 * 4 + 2] = -1
        state = State(tuple(board), player=-1)
        exact = exact_value(game, state)
        result = minimax_transition_balanced_bounds(game, state, 64, 2)
        self.assertEqual(tuple(a for a, _ in result.action_values), (64,))
        self.assertEqual(result.transition_count, 2)
        self.assertEqual(result.action_values[0][1].lower, exact)
        self.assertEqual(result.action_values[0][1].upper, exact)


if __name__ == "__main__":
    unittest.main()

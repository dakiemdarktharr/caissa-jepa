import unittest

from two_player.games import BoardGame, State, exact_value
from two_player.v212_minimax_transition_bounds_v01 import (
    minimax_transition_bounds,
)


class MinimaxTransitionBoundsTests(unittest.TestCase):
    def test_every_transition_budget_prefix_is_sound_and_within_cap(self):
        game = BoardGame("transition-budget-tictactoe", 3, 3, 3)
        state = State((1, -1, 1,
                       1, -1, 0,
                       0, 0, 0), player=1)
        root_actions = game.legal_actions(state)
        exact_root = exact_value(game, state)
        exact_actions = {
            action: -exact_value(game, game.transition(state, action))
            for action in root_actions
        }
        best_value = max(exact_actions.values())
        executed = root_actions[-1]
        exact_regret = best_value - exact_actions[executed]
        complete = minimax_transition_bounds(game, state, executed, 100_000)

        previous = None
        for budget in range(len(root_actions), complete.transition_count + 1):
            result = minimax_transition_bounds(game, state, executed, budget)
            self.assertLessEqual(result.transition_count, budget)
            self.assertEqual(tuple(a for a, _ in result.action_values), root_actions)
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
                self.assertGreaterEqual(result.regret.lower, previous.regret.lower)
                self.assertLessEqual(result.regret.upper, previous.regret.upper)
            previous = result

        self.assertEqual(complete.root_value.lower, exact_root)
        self.assertEqual(complete.root_value.upper, exact_root)
        self.assertEqual(complete.regret.lower, exact_regret)
        self.assertEqual(complete.regret.upper, exact_regret)

    def test_forced_pass_and_unresolved_successor_respect_transition_cap(self):
        game = BoardGame("transition-budget-reversi4", 4, 4, reversi=True)
        board = [1] * 16
        board[1 * 4 + 1] = 0
        board[1 * 4 + 2] = -1
        state = State(tuple(board), player=-1)
        exact = exact_value(game, state)

        with self.assertRaises(ValueError):
            minimax_transition_bounds(game, state, 64, 0)
        one_transition = minimax_transition_bounds(game, state, 64, 1)
        self.assertEqual(one_transition.transition_count, 1)
        self.assertEqual(one_transition.action_values[0][1].lower, -1)
        self.assertEqual(one_transition.action_values[0][1].upper, 1)

        two_transitions = minimax_transition_bounds(game, state, 64, 2)
        self.assertEqual(two_transitions.transition_count, 2)
        self.assertEqual(two_transitions.action_values[0][1].lower, exact)
        self.assertEqual(two_transitions.action_values[0][1].upper, exact)

    def test_boolean_and_noninteger_budgets_are_rejected(self):
        game = BoardGame("transition-budget-tictactoe", 3, 3, 3)
        state = game.initial()
        action = game.legal_actions(state)[0]
        for bad_budget in (True, 3.0):
            with self.subTest(budget=bad_budget):
                with self.assertRaises(ValueError):
                    minimax_transition_bounds(game, state, action, bad_budget)


if __name__ == "__main__":
    unittest.main()

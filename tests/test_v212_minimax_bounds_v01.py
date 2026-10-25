import unittest

from two_player.games import BoardGame, State, exact_value
from two_player.v212_minimax_bounds_v01 import minimax_bounds


class MinimaxBoundsTests(unittest.TestCase):
    def test_every_budget_prefix_contains_exact_values_and_regret(self):
        game = BoardGame("interval-tictactoe", 3, 3, 3)
        # Reachable, nonterminal position with both tactical and unresolved
        # continuations. X (+1) to move; the board has four empty cells.
        state = State((1, -1, 1,
                       1, -1, 0,
                       0, 0, 0), player=1)
        self.assertIsNone(game.terminal(state))
        exact_root = exact_value(game, state)
        exact_actions = {
            action: -exact_value(game, game.transition(state, action))
            for action in game.legal_actions(state)
        }
        best_value = max(exact_actions.values())
        executed = game.legal_actions(state)[-1]
        exact_regret = best_value - exact_actions[executed]

        complete = minimax_bounds(game, state, executed, 10_000)
        self.assertEqual(complete.root_value.lower, exact_root)
        self.assertEqual(complete.root_value.upper, exact_root)
        self.assertEqual(complete.regret.lower, exact_regret)
        self.assertEqual(complete.regret.upper, exact_regret)

        previous = None
        for budget in range(complete.expanded_nodes + 1):
            result = minimax_bounds(game, state, executed, budget)
            action_values = dict(result.action_values)
            self.assertEqual(tuple(action_values), game.legal_actions(state))
            self.assertLessEqual(result.root_value.lower, exact_root)
            self.assertGreaterEqual(result.root_value.upper, exact_root)
            for action, interval in result.action_values:
                with self.subTest(budget=budget, action=action):
                    self.assertLessEqual(interval.lower, exact_actions[action])
                    self.assertGreaterEqual(interval.upper, exact_actions[action])
            self.assertLessEqual(result.regret.lower, exact_regret)
            self.assertGreaterEqual(result.regret.upper, exact_regret)
            if previous is not None:
                self.assertGreaterEqual(result.root_value.lower,
                                        previous.root_value.lower)
                self.assertLessEqual(result.root_value.upper,
                                     previous.root_value.upper)
                for action, interval in result.action_values:
                    old = dict(previous.action_values)[action]
                    self.assertGreaterEqual(interval.lower, old.lower)
                    self.assertLessEqual(interval.upper, old.upper)
                self.assertGreaterEqual(result.regret.lower, previous.regret.lower)
                self.assertLessEqual(result.regret.upper, previous.regret.upper)
            previous = result

    def test_unseen_root_children_remain_in_the_interval(self):
        game = BoardGame("interval-tictactoe", 3, 3, 3)
        state = game.initial()
        actions = game.legal_actions(state)
        result = minimax_bounds(game, state, actions[0], 0)
        self.assertEqual(tuple(action for action, _ in result.action_values), actions)
        self.assertTrue(all(interval.lower == -1 and interval.upper == 1
                            for _, interval in result.action_values))
        self.assertEqual(result.expanded_nodes, 0)
        self.assertEqual(result.transition_count, len(actions))

    def test_forced_reversi_pass_is_expanded_as_a_real_transition(self):
        game = BoardGame("interval-reversi4", 4, 4, reversi=True)
        board = [1] * 16
        board[1 * 4 + 1] = 0
        board[1 * 4 + 2] = -1
        state = State(tuple(board), player=-1)
        self.assertEqual(game.legal_actions(state), (64,))
        exact_root = exact_value(game, state)

        unresolved = minimax_bounds(game, state, 64, 0)
        self.assertEqual(unresolved.action_values[0][1].lower, -1)
        self.assertEqual(unresolved.action_values[0][1].upper, 1)
        self.assertEqual(unresolved.transition_count, 1)

        resolved = minimax_bounds(game, state, 64, 1)
        self.assertEqual(resolved.expanded_nodes, 1)
        self.assertEqual(resolved.transition_count, 2)
        self.assertEqual(resolved.action_values[0][1].lower, exact_root)
        self.assertEqual(resolved.action_values[0][1].upper, exact_root)
        self.assertEqual(resolved.regret.lower, 0)
        self.assertEqual(resolved.regret.upper, 0)

    def test_invalid_budget_and_illegal_executed_action_are_rejected(self):
        game = BoardGame("interval-tictactoe", 3, 3, 3)
        state = game.initial()
        with self.assertRaises(ValueError):
            minimax_bounds(game, state, 0, -1)
        with self.assertRaises(ValueError):
            minimax_bounds(game, state, 64, 0)
        with self.assertRaises(ValueError):
            minimax_bounds(game, state, True, 0)


if __name__ == "__main__":
    unittest.main()

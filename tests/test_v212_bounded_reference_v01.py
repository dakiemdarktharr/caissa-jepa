import hashlib
import unittest

from two_player.games import BoardGame, State
from two_player.v212_bounded_reference_v01 import (
    ReferenceBudgetExceeded,
    ReferenceError,
    VALUE_SCALE,
    bounded_reference_values,
)


def _zero(*_args):
    return 0


def _positive_source():
    return hashlib.sha256(b"test evaluator source").hexdigest()


def _positive_config():
    return hashlib.sha256(b"test evaluator config").hexdigest()


def plain_fixed_horizon(game, state, root_player, plies_left, evaluator):
    outcome = game.terminal(state)
    if outcome is not None:
        return root_player * outcome * VALUE_SCALE
    if plies_left == 0:
        return evaluator(game, state, root_player)
    values = [plain_fixed_horizon(
        game, game.transition(state, action), root_player,
        plies_left - 1, evaluator)
        for action in game.legal_actions(state)]
    return max(values) if state.player == root_player else min(values)


class BoundedReferenceTests(unittest.TestCase):
    def test_every_root_action_matches_independent_full_tree_oracle(self):
        game = BoardGame("bounded-reference-tictactoe", 3, 3, 3)
        state = State((1, -1, 1, 1, -1, 0, 0, 0, 0), player=1)
        for depth in (1, 2, 3, 4, 5):
            result = bounded_reference_values(
                game, state, horizon_plies=depth, evaluator=_zero,
                evaluator_source_sha256=_positive_source(),
                evaluator_config_sha256=_positive_config())
            expected = tuple((action, plain_fixed_horizon(
                game, game.transition(state, action), state.player,
                depth - 1, _zero)) for action in game.legal_actions(state))
            with self.subTest(depth=depth):
                self.assertEqual(result.action_values, expected)
                self.assertEqual(result.root_value,
                                 max(value for _, value in expected))
                self.assertEqual(result.best_actions, tuple(
                    action for action, value in expected
                    if value == result.root_value))

    def test_terminal_values_override_leaf_evaluator_and_root_actions_are_full_window(self):
        game = BoardGame("bounded-reference-win", 3, 3, 3)
        state = State((1, 1, 0,
                       -1, -1, 0,
                       0, 0, 0), player=1)
        evaluator = lambda *_: 1234
        result = bounded_reference_values(
            game, state, horizon_plies=1, evaluator=evaluator,
            evaluator_source_sha256=_positive_source(),
            evaluator_config_sha256=_positive_config())
        values = dict(result.action_values)
        self.assertEqual(values[2], VALUE_SCALE)
        self.assertEqual(len(result.action_values), len(game.legal_actions(state)))
        self.assertTrue(all(value in (VALUE_SCALE, 1234)
                            for value in values.values()))
        self.assertEqual(result.root_value, VALUE_SCALE)

    def test_forced_pass_counts_as_a_root_action_and_transition(self):
        game = BoardGame("bounded-reference-reversi4", 4, 4, reversi=True)
        board = [1] * 16
        board[5] = 0
        board[6] = -1
        state = State(tuple(board), player=-1)
        self.assertEqual(game.legal_actions(state), (64,))
        result = bounded_reference_values(
            game, state, horizon_plies=2, evaluator=_zero,
            evaluator_source_sha256=_positive_source(),
            evaluator_config_sha256=_positive_config())
        self.assertEqual(result.action_values[0][0], 64)
        self.assertGreaterEqual(result.transition_count, 1)

    def test_cap_failure_never_returns_partial_root_table(self):
        game = BoardGame("bounded-reference-tictactoe", 3, 3, 3)
        state = game.initial()
        with self.assertRaises(ReferenceBudgetExceeded):
            bounded_reference_values(
                game, state, horizon_plies=4, evaluator=_zero,
                evaluator_source_sha256=_positive_source(),
                evaluator_config_sha256=_positive_config(),
                transition_budget=len(game.legal_actions(state)))

    def test_invalid_evaluator_domain_and_hash_are_rejected(self):
        game = BoardGame("bounded-reference-tictactoe", 3, 3, 3)
        state = game.initial()
        kwargs = {
            "horizon_plies": 1,
            "evaluator_source_sha256": _positive_source(),
            "evaluator_config_sha256": _positive_config(),
        }
        with self.assertRaises(ReferenceError):
            bounded_reference_values(game, state, evaluator=lambda *_: True,
                                     **kwargs)
        with self.assertRaises(ReferenceError):
            bounded_reference_values(game, state, evaluator=lambda *_: VALUE_SCALE,
                                     **kwargs)
        with self.assertRaises(ReferenceError):
            bounded_reference_values(game, state, evaluator=_zero,
                                     evaluator_source_sha256="A" * 64,
                                     evaluator_config_sha256=_positive_config(),
                                     horizon_plies=1)


if __name__ == "__main__":
    unittest.main()

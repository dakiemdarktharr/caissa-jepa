"""Deterministic audit of exact-state feature coordinates proposed for V2.12.

These fixtures validate only the existing rules adapter's feature mapping.
They do not implement or approve a trainer, loss, decoder, or method arm.
"""
import unittest

import numpy as np

from two_player.games import BoardGame, State


class RawStateFeatureContractAuditTests(unittest.TestCase):
    GAMES = (
        BoardGame("connect4-gravity-6x7", 6, 7, 4, gravity=True),
        BoardGame("connect4-gravity-8x8", 8, 8, 4, gravity=True),
        BoardGame("reversi6", 6, 6, 0, reversi=True),
        BoardGame("reversi8", 8, 8, 0, reversi=True),
    )

    def test_feature_planes_padding_and_descriptors_match_coordinate_contract(self):
        for game in self.GAMES:
            with self.subTest(game=game.name):
                board = tuple((index % 3) - 1
                              for index in range(game.rows * game.cols))
                state = State(board, player=-1)
                features = game.features(state)

                self.assertEqual(features.shape, (198,))
                self.assertTrue(np.isfinite(features).all())
                expected_current = np.zeros(64, dtype=np.float64)
                expected_opponent = np.zeros(64, dtype=np.float64)
                expected_in_board = np.zeros(64, dtype=np.float64)
                for row in range(game.rows):
                    for col in range(game.cols):
                        cell = row * 8 + col
                        piece = board[row * game.cols + col]
                        expected_current[cell] = piece == state.player
                        expected_opponent[cell] = piece == -state.player
                        expected_in_board[cell] = 1.0

                np.testing.assert_array_equal(features[0:64], expected_current)
                np.testing.assert_array_equal(features[64:128], expected_opponent)
                np.testing.assert_array_equal(features[128:192], expected_in_board)
                np.testing.assert_array_equal(
                    features[192:198],
                    np.asarray((game.rows / 8, game.cols / 8, game.k / 8,
                                float(not game.reversi), float(game.reversi),
                                float(game.gravity)), dtype=np.float64))

    def test_forced_pass_swaps_side_relative_planes_and_preserves_board_descriptor(self):
        game = BoardGame("fixture-reversi", 4, 4, 0, reversi=True)
        board = [1] * 16
        board[1 * 4 + 1] = 0
        board[1 * 4 + 2] = -1
        state = State(tuple(board), player=-1)
        self.assertEqual(game.legal_actions(state), (64,))

        passed = game.transition(state, 64)
        before = game.features(state)
        after = game.features(passed)

        self.assertEqual(passed.board, state.board)
        self.assertEqual(passed.player, 1)
        np.testing.assert_array_equal(before[0:64], after[64:128])
        np.testing.assert_array_equal(before[64:128], after[0:64])
        np.testing.assert_array_equal(before[128:198], after[128:198])


if __name__ == "__main__":
    unittest.main()

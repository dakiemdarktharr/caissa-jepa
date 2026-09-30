import random
import unittest

from benchmarks.reference_rules import PASS, ReferenceGame
from benchmarks.v27_search_opponent import DepthLimitedOpponent
from two_player.games import BoardGame


CONFIGS = (
    (BoardGame("c4-8x8", 8, 8, 4, gravity=True), ReferenceGame(8, 8, 4, gravity=True)),
    (BoardGame("reversi8", 8, 8, 0, reversi=True), ReferenceGame(8, 8, 0, reversi=True)),
    (BoardGame("connect-6x7", 6, 7, 4), ReferenceGame(6, 7, 4)),
)


def action_to_reference(action, cols):
    if action == 64:
        return PASS
    row, col = divmod(action, 8)
    return row * cols + col


class V27SearchOpponentTests(unittest.TestCase):
    def test_reference_rules_match_project_adapter_over_seeded_trajectories(self):
        for adapter, reference in CONFIGS:
            for seed in (2701, 2702, 2703, 2704):
                with self.subTest(game=adapter.name, seed=seed):
                    rng = random.Random(seed)
                    left, right = adapter.initial(), reference.initial()
                    for _ in range(adapter.rows * adapter.cols + 4):
                        self.assertEqual(left.board, reference.board(right))
                        self.assertEqual(adapter.terminal(left), reference.terminal(right))
                        if adapter.terminal(left) is not None:
                            break
                        left_legal = {action_to_reference(a, adapter.cols)
                                      for a in adapter.legal_actions(left)}
                        self.assertEqual(left_legal, set(reference.legal_actions(right)))
                        action = rng.choice(adapter.legal_actions(left))
                        ref_action = action_to_reference(action, adapter.cols)
                        left = adapter.transition(left, action)
                        right = reference.transition(right, ref_action)
                    else:
                        self.fail("trajectory exceeded the finite game bound")

    def test_search_is_deterministic_legal_and_obeys_node_cap(self):
        for _, reference in CONFIGS:
            state = reference.initial()
            search = DepthLimitedOpponent(reference, max_depth=3, node_limit=250)
            first = search.choose_action(state)
            first_stats = search.stats
            second = search.choose_action(state)
            self.assertEqual(first, second)
            self.assertIn(first, reference.legal_actions(state))
            self.assertLessEqual(first_stats.nodes, 250)
            self.assertLessEqual(search.stats.nodes, 250)
            self.assertGreaterEqual(search.stats.completed_depth, 1)

    def test_search_finds_immediate_connect_win(self):
        game = ReferenceGame(4, 4, 3, gravity=True)
        state = game.initial()
        for action in (12, 13, 8, 9):
            state = game.transition(state, action)
        search = DepthLimitedOpponent(game, max_depth=2, node_limit=1_000)
        action = search.choose_action(state)
        self.assertEqual(action, 4)

    def test_randomized_tie_order_is_reproducible_for_a_seat_seed(self):
        game = ReferenceGame(8, 8, 0, reversi=True)
        state = game.initial()
        first = DepthLimitedOpponent(game, max_depth=2, node_limit=150)
        second = DepthLimitedOpponent(game, max_depth=2, node_limit=150)
        action_a = first.choose_action(state, random.Random(271828))
        action_b = second.choose_action(state, random.Random(271828))
        self.assertEqual(action_a, action_b)
        self.assertIn(action_a, game.legal_actions(state))


if __name__ == "__main__":
    unittest.main()

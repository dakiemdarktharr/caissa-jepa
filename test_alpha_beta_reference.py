"""Exact-value and failure-path tests for the bounded reference alpha-beta solver."""
import random
import unittest
from collections import deque

from benchmarks.alpha_beta_reference import AlphaBetaReferenceSolver
from benchmarks.reference_rules import (PASS, ReferenceBudgetExceeded,
                                         ReferenceGame, ReferenceSolver)
from two_player.games import BoardGame


class AlphaBetaReferenceTests(unittest.TestCase):
    def test_values_match_plain_solver_on_every_reachable_tic_tac_toe_state(self):
        reference = ReferenceGame(3, 3, 3)
        queue = deque([reference.initial()])
        states = {reference.initial()}
        while queue:
            state = queue.popleft()
            for action in reference.legal_actions(state):
                child = reference.transition(state, action)
                if child not in states:
                    states.add(child)
                    queue.append(child)
        fast = AlphaBetaReferenceSolver(reference)
        exact = ReferenceSolver(reference)
        for state in states:
            self.assertEqual(fast.value(state), exact.value(state))
        self.assertEqual(len(states), 5478)

    def test_action_values_match_plain_exact_solver_across_variants(self):
        configs = (
            (3, 3, 3, False, False),
            (4, 4, 3, True, False),
            (4, 4, 0, False, True),
        )
        for rows, cols, k, gravity, reversi in configs:
            with self.subTest(config=(rows, cols, k, gravity, reversi)):
                adapter = BoardGame("fixture", rows, cols, k, gravity, reversi)
                reference = ReferenceGame(rows, cols, k, gravity, reversi)
                fast = AlphaBetaReferenceSolver(reference)
                exact = ReferenceSolver(reference)
                rng = random.Random(20260929 + rows * 100 + cols * 10 + k)
                states = []
                for _ in range(8):
                    state = adapter.initial()
                    for _ply in range(2 * rows * cols):
                        if adapter.terminal(state) is not None:
                            break
                        states.append(reference.from_board(state.board, state.player))
                        action = rng.choice(adapter.legal_actions(state))
                        state = adapter.transition(state, action)
                for state in states:
                    self.assertEqual(fast.action_values(state), exact.action_values(state))
                    self.assertTrue(fast.last_stats["complete"])

    def test_narrow_window_bounds_do_not_corrupt_later_exact_queries(self):
        adapter = BoardGame("fixture", 4, 4, 3, gravity=True)
        reference = ReferenceGame(4, 4, 3, gravity=True)
        state = adapter.initial()
        rng = random.Random(917)
        for _ in range(5):
            state = adapter.transition(state, rng.choice(adapter.legal_actions(state)))
        position = reference.from_board(state.board, state.player)
        fast = AlphaBetaReferenceSolver(reference)
        fast._begin()
        fast._search(position, -1, 0)
        self.assertTrue(fast.table)
        self.assertEqual(fast.action_values(position),
                         ReferenceSolver(reference).action_values(position))

    def test_connect4_4x5_exact_labels_match_plain_solver_on_solved_roots(self):
        adapter = BoardGame("connect4-4x5", 4, 5, 4)
        reference = ReferenceGame(4, 5, 4)
        for seed in (261002, 261005):
            rng = random.Random(seed)
            state = adapter.initial()
            target = rng.choice((7, 8, 9, 10, 11, 12))
            for _ in range(target):
                if adapter.terminal(state) is not None:
                    break
                state = adapter.transition(state, rng.choice(adapter.legal_actions(state)))
            self.assertIsNone(adapter.terminal(state))
            position = reference.from_board(state.board, state.player)
            fast = AlphaBetaReferenceSolver(reference, node_limit=100_000, time_limit=1.)
            # The plain solver is an intentionally unpruned oracle; its timing
            # budget must not match the optimized alpha-beta implementation.
            exact = ReferenceSolver(reference, node_limit=100_000, time_limit=10.)
            self.assertEqual(fast.action_values(position), exact.action_values(position))
            self.assertTrue(fast.last_stats["complete"])
            self.assertTrue(exact.last_stats["complete"])

    def test_pass_terminal_sign_and_fail_closed_budget(self):
        reversi = ReferenceGame(4, 4, 0, reversi=True)
        forced = reversi.from_board((0, 1, -1, -1, -1, -1) + (-1,) * 10)
        solver = AlphaBetaReferenceSolver(reversi)
        self.assertEqual(solver.action_values(forced), {PASS: -1})
        after_pass = reversi.transition(forced, PASS)
        self.assertEqual(solver.value(after_pass), 1)
        terminal = reversi.transition(after_pass, reversi.legal_actions(after_pass)[0])
        self.assertEqual(solver.value(terminal), -1)

        hard_game = ReferenceGame(5, 5, 4)
        hard_state = hard_game.initial()
        bounded = AlphaBetaReferenceSolver(hard_game, node_limit=1, time_limit=1.)
        with self.assertRaises(ReferenceBudgetExceeded):
            bounded.action_values(hard_state)
        self.assertFalse(bounded.last_stats["complete"])


if __name__ == "__main__":
    unittest.main()

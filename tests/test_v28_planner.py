import unittest

from two_player.games import BoardGame, State
from two_player.planner import plan_depth_two


class TwoPlyPlannerTests(unittest.TestCase):
    def test_immediate_winning_action_is_scored_without_reply_or_leaf_model(self):
        game = BoardGame("connect3", 4, 4, 3, gravity=True)
        board = [0] * 16
        board[12] = board[13] = 1  # +1 is one legal move from a bottom-row win.
        state = State(tuple(board), player=1)
        called = []

        result = plan_depth_two(game, state, lambda *args: called.append(args) or -1.0)

        self.assertEqual(result.action, 26)  # row 3, column 2 in padded action encoding.
        self.assertEqual(result.action_values[26], 1.0)
        self.assertGreaterEqual(result.immediate_terminal_actions, 1)
        self.assertEqual(result.root_actions_evaluated, len(result.action_values))
        self.assertEqual(result.nonterminal_leaf_evaluations, len(called))
        self.assertEqual(result.reply_branches_evaluated,
                         result.terminal_reply_branches + result.nonterminal_leaf_evaluations)

    def test_terminal_leaf_uses_root_perspective_and_skips_leaf_model(self):
        game = BoardGame("tic-tac-toe", 3, 3, 3)
        # +1 to move: action 2 wins immediately; other moves permit a reply win.
        board = (1, 1, 0,
                 -1, -1, 0,
                 0, 0, 0)
        state = State(board, player=1)
        result = plan_depth_two(game, state, lambda *_: 0.25)

        self.assertEqual(result.action_values[2], 1.0)
        self.assertEqual(result.action, 2)

    def test_minus_player_terminal_win_and_reply_loss_use_root_perspective(self):
        game = BoardGame("tic-tac-toe", 3, 3, 3)
        minus_wins = State((-1, -1, 0, 1, 1, 0, 0, 0, 0), player=-1)
        win_result = plan_depth_two(game, minus_wins, lambda *_: 0.0)
        self.assertEqual(win_result.action_values[2], 1.0)

        minus_to_move = State((1, 1, 0, -1, -1, 0, 0, 0, 0), player=-1)
        loss_result = plan_depth_two(game, minus_to_move, lambda *_: 0.0)
        self.assertEqual(loss_result.action_values[16], -1.0)

    def test_forced_reversi_pass_is_enumerated_as_an_opponent_reply(self):
        game = BoardGame("reversi4", 4, 4, 0, reversi=True)
        import random
        found = None
        for seed in range(100):
            rng = random.Random(seed)
            state = game.initial()
            while game.terminal(state) is None:
                for action in game.legal_actions(state):
                    child = game.transition(state, action)
                    if (game.terminal(child) is None
                            and game.legal_actions(child) == (64,)):
                        found = (state, action)
                        break
                if found is not None:
                    break
                state = game.transition(state, rng.choice(game.legal_actions(state)))
            if found is not None:
                break
        self.assertIsNotNone(found, "deterministic search should find a reachable forced-pass reply")
        state, _ = found
        scored_replies = []
        result = plan_depth_two(game, state,
                                lambda _root, _action, reply, _leaf:
                                scored_replies.append(reply) or 0.0)
        self.assertGreater(result.reply_branches_evaluated, 0)
        self.assertIn(64, scored_replies)

    def test_terminal_draw_scores_zero(self):
        class DrawTree:
            @staticmethod
            def validate(state):
                return None

            @staticmethod
            def terminal(state):
                return 0 if state.board[0] in (1, 3) else None

            @staticmethod
            def legal_actions(state):
                return (0, 1) if state.board[0] == 0 else (0,) if state.board[0] == 2 else ()

            @staticmethod
            def transition(state, action):
                if state.board[0] == 0:
                    return State((1 if action == 0 else 2,), -1)
                return State((3,), 1)

        result = plan_depth_two(DrawTree(), State((0,), 1), lambda *_: 0.0)
        self.assertEqual(result.action_values, {0: 0.0, 1: 0.0})

    def test_nonterminal_leaf_score_must_be_bounded_and_finite(self):
        game = BoardGame("tic-tac-toe", 3, 3, 3)
        state = game.initial()
        with self.assertRaisesRegex(ValueError, r"finite and in \[-1, 1\]"):
            plan_depth_two(game, state, lambda *_: 1.1)

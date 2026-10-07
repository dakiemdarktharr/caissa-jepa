import unittest

import numpy as np

from two_player.games import BoardGame, State
from two_player.v212_model import preflight_batch
from two_player.v212_trajectory_audit import audit_trajectories
from two_player.v212_window_batch import windows_to_model_batch


class V212WindowBatchTests(unittest.TestCase):
    def test_replayed_windows_materialize_exact_features_masks_and_roles(self):
        game = BoardGame("fixture-c4", 4, 4, k=3, gravity=True)
        actions = (24, 25, 16, 17, 8)
        states = [game.initial()]
        for action in actions:
            states.append(game.transition(states[-1], action))
        outcome = game.terminal(states[-1])
        episodes = [{"game": game.name, "episode_id": "episode-c4",
                     "split": "train", "states": tuple(states),
                     "actions": actions, "outcome": outcome}]
        audit = audit_trajectories(episodes, {game.name: game})

        batch = windows_to_model_batch(audit.windows, {game.name: game})
        masks = preflight_batch(batch)
        self.assertEqual(batch["x"].shape, (5, 198))
        self.assertEqual(batch["actions"].shape, (5, 4, 65))
        self.assertEqual(batch["policy"][0], actions[0])
        np.testing.assert_array_equal(batch["x"][0], game.features(states[0]))
        self.assertTrue(masks["valid"][4][0])
        self.assertIn(4, audit.windows[0].valid_targets)
        self.assertEqual(batch["actors"][0].tolist(), [1.0, -1.0, 1.0, -1.0])
        self.assertEqual(batch["value"][0], states[0].player * outcome)
        self.assertEqual(batch["future_value"][0, 3], states[4].player * outcome)

    def test_forced_pass_is_materialized_as_a_legal_transition(self):
        game = BoardGame("fixture-reversi", 4, 4, reversi=True)
        board = [1] * 16
        board[1 * 4 + 1] = 0
        board[1 * 4 + 2] = -1
        state = State(tuple(board), player=-1)
        passed = game.transition(state, 64)
        ended = game.transition(passed, 1 * 8 + 1)
        outcome = game.terminal(ended)
        episode = {"game": game.name, "episode_id": "episode-pass",
                   "split": "train", "states": (state, passed, ended),
                   "actions": (64, 1 * 8 + 1), "outcome": outcome}
        audit = audit_trajectories([episode], {game.name: game})
        batch = windows_to_model_batch(audit.windows, {game.name: game})
        self.assertTrue(batch["legal"][0, 64])
        self.assertEqual(batch["actions"][0, 0, 64], 1.0)
        self.assertEqual(batch["actors"][0, 0], -1.0)
        self.assertEqual(batch["actors"][0, 1], 1.0)

    def test_short_terminal_draw_window_keeps_exact_zero_label_and_padding_masks(self):
        reversi = BoardGame("fixture-reversi-draw", 4, 4, reversi=True)
        board = [1] * 16
        board[0] = 0
        board[1] = -1
        board[2] = 1
        # The final legal move at 0 flips one disk, leaving an exact 8-8 draw.
        board[3:8] = [-1, 1, 1, -1, -1]
        board[8:] = [-1, -1, 1, 1, -1, 1, -1, -1]
        state = State(tuple(board), player=1)
        terminal = reversi.transition(state, 0)
        self.assertEqual(reversi.terminal(terminal), 0)
        draw_episode = {"game": reversi.name, "episode_id": "episode-draw",
                        "split": "train", "states": (state, terminal),
                        "actions": (0,), "outcome": 0}

        c4 = BoardGame("fixture-c4-support", 4, 4, k=3, gravity=True)
        actions = (24, 25, 16, 17, 8)
        states = [c4.initial()]
        for action in actions:
            states.append(c4.transition(states[-1], action))
        c4_episode = {"game": c4.name, "episode_id": "episode-support",
                      "split": "train", "states": tuple(states),
                      "actions": actions, "outcome": c4.terminal(states[-1])}

        games = {reversi.name: reversi, c4.name: c4}
        audit = audit_trajectories([draw_episode, c4_episode], games)
        batch = windows_to_model_batch(audit.windows, games)
        masks = preflight_batch(batch)
        self.assertEqual(batch["value"][0], 0.0)
        self.assertEqual(batch["future_value"][0, 0], 0.0)
        self.assertTrue(batch["terminal"][0, 0])
        self.assertFalse(batch["transition_exists"][0, 1:].any())
        self.assertFalse(batch["target_exists"][0, 1:].any())
        self.assertEqual(masks["counts"][1]["terminal_masked"], 2)
        audited_draw = audit.windows[0]
        missing_terminal_record = audited_draw.__class__(
            audited_draw.game, audited_draw.episode_id, audited_draw.split,
            audited_draw.episode_outcome, audited_draw.start_ply,
            audited_draw.states, audited_draw.actions, audited_draw.valid_targets,
            ())
        with self.assertRaisesRegex(ValueError, "terminal-target mask mismatch"):
            windows_to_model_batch((missing_terminal_record, *audit.windows[1:]),
                                   games)

    def test_nontrain_window_and_invalid_local_replay_fail_closed(self):
        game = BoardGame("fixture-c4", 4, 4, k=3, gravity=True)
        actions = (24, 25, 16, 17, 8)
        states = [game.initial()]
        for action in actions:
            states.append(game.transition(states[-1], action))
        outcome = game.terminal(states[-1])
        episode = {"game": game.name, "episode_id": "episode-c4",
                   "split": "train", "states": tuple(states),
                   "actions": actions, "outcome": outcome}
        window = audit_trajectories([episode], {game.name: game}).windows[0]
        development = window.__class__(
            window.game, window.episode_id, "development", window.episode_outcome,
            window.start_ply, window.states, window.actions, window.valid_targets,
            window.terminal_targets)
        with self.assertRaisesRegex(ValueError, "required split"):
            windows_to_model_batch((development,), {game.name: game})

        empty_path = window.__class__(
            window.game, window.episode_id, window.split, window.episode_outcome,
            window.start_ply, (window.states[0],), (), (), ())
        with self.assertRaisesRegex(ValueError, "state/action path length"):
            windows_to_model_batch((empty_path,), {game.name: game})

        altered_masks = window.__class__(
            window.game, window.episode_id, window.split, window.episode_outcome,
            window.start_ply, window.states, window.actions, (),
            window.terminal_targets)
        with self.assertRaisesRegex(ValueError, "valid-target mask mismatch"):
            windows_to_model_batch((altered_masks,), {game.name: game})

        altered = list(window.states)
        altered[1] = game.transition(game.initial(), 25)
        corrupted = window.__class__(
            window.game, window.episode_id, window.split, window.episode_outcome,
            window.start_ply, tuple(altered), window.actions, window.valid_targets,
            window.terminal_targets)
        with self.assertRaisesRegex(ValueError, "illegal or altered"):
            windows_to_model_batch((corrupted,), {game.name: game})


if __name__ == "__main__":
    unittest.main()

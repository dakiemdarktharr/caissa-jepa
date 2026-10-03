import unittest
from unittest.mock import patch

from two_player.games import BoardGame, State
from two_player import v212_trajectory_audit
from two_player.v212_trajectory_audit import (
    audit_synthetic_key_records,
    audit_trajectories,
)


class V212TrajectoryAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c4 = BoardGame("fixture-c4", 4, 4, k=3, gravity=True)
        cls.games = {cls.c4.name: cls.c4}

    def terminal_episode(self):
        actions = (24, 25, 16, 17, 8)  # +1 wins vertically on the fifth ply.
        states = [self.c4.initial()]
        for action in actions:
            states.append(self.c4.transition(states[-1], action))
        return {"game": self.c4.name, "episode_id": "terminal-fixture",
                "split": "train", "states": tuple(states),
                "actions": actions, "outcome": 1}

    def test_legal_path_materializes_horizons_and_terminal_exact_target(self):
        episode = self.terminal_episode()
        result = audit_trajectories([episode], self.games)
        self.assertEqual(len(result.windows), 5)
        boundary = next(window for window in result.windows
                        if window.start_ply == 1)
        self.assertIn(2, boundary.valid_targets)
        self.assertIn((4, -1), boundary.terminal_targets)
        self.assertEqual(result.terminal_targets_by_horizon[4], 1)
        self.assertGreater(result.masked_targets_by_horizon[4], 0)

    def test_illegal_replay_and_wrong_terminal_label_fail_closed(self):
        episode = self.terminal_episode()
        illegal_action = dict(episode, actions=(0,) + episode["actions"][1:])
        with self.assertRaisesRegex(ValueError, "Illegal action or transition"):
            audit_trajectories([illegal_action], self.games)

        altered_states = list(episode["states"])
        altered_states[1] = self.c4.transition(self.c4.initial(), 25)
        illegal = dict(episode, states=tuple(altered_states))
        with self.assertRaisesRegex(ValueError, "illegal or altered replay"):
            audit_trajectories([illegal], self.games)
        wrong_outcome = dict(episode, outcome=-1)
        with self.assertRaisesRegex(ValueError, "does not match"):
            audit_trajectories([wrong_outcome], self.games)

    def test_canonical_duplicate_window_is_rejected(self):
        episode = self.terminal_episode()
        mapping = self.c4.transforms()[1]
        transformed_states = []
        transformed_actions = []
        for index, state in enumerate(episode["states"]):
            transformed, _ = self.c4.transform(state, 64, mapping)
            transformed_states.append(State(
                tuple(-value for value in transformed.board),
                -transformed.player,
            ))
            if index < len(episode["actions"]):
                _, action = self.c4.transform(
                    state, episode["actions"][index], mapping)
                transformed_actions.append(action)
        equivalent = dict(episode, episode_id="symmetric-copy",
                          states=tuple(transformed_states),
                          actions=tuple(transformed_actions), outcome=-1)
        with self.assertRaisesRegex(ValueError, "duplicate canonical window"):
            audit_trajectories([episode, equivalent], self.games)

    def test_same_episode_duplicate_signature_is_rejected(self):
        episode = self.terminal_episode()
        with patch.object(v212_trajectory_audit, "_window_signature",
                          return_value="duplicate-fixture"):
            with self.assertRaisesRegex(ValueError, "duplicate canonical window"):
                audit_trajectories([episode], self.games)

    def test_h4_only_overlap_is_rejected(self):
        records = [
            {"split": "train", "state_keys": ("a", "b", "c", "d", "shared-h4")},
            {"split": "development", "state_keys": ("w", "x", "y", "z", "shared-h4")},
        ]
        with self.assertRaisesRegex(ValueError, "overlaps across split"):
            audit_synthetic_key_records(records)

    def test_reversi_forced_pass_is_an_exact_role_switch(self):
        reversi = BoardGame("fixture-reversi", 4, 4, reversi=True)
        games = {reversi.name: reversi}
        board = [1] * 16
        board[1 * 4 + 1] = 0
        board[1 * 4 + 2] = -1
        state = State(tuple(board), player=-1)
        self.assertEqual(reversi.legal_actions(state), (64,))
        passed = reversi.transition(state, 64)
        self.assertEqual(passed.player, 1)
        self.assertIn(1 * 8 + 1, reversi.legal_actions(passed))
        ended = reversi.transition(passed, 1 * 8 + 1)
        outcome = reversi.terminal(ended)
        episode = {"game": reversi.name, "episode_id": "forced-pass-fixture",
                   "split": "train", "states": (state, passed, ended),
                   "actions": (64, 1 * 8 + 1), "outcome": outcome}
        audit = audit_trajectories([episode], games)
        self.assertEqual(audit.windows[0].actions, (64, 1 * 8 + 1))
        self.assertIn((2, -1), audit.windows[0].terminal_targets)

    def test_bad_second_episode_returns_no_partial_window_result(self):
        valid = self.terminal_episode()
        invalid = dict(valid, episode_id="bad-copy", outcome=0)
        with self.assertRaises(ValueError):
            audit_trajectories([valid, invalid], self.games)


if __name__ == "__main__":
    unittest.main()

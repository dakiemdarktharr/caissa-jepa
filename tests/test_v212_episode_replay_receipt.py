import copy
import unittest

from two_player.games import BoardGame
from two_player.v212_episode_replay_receipt import (
    build_episode_replay_receipt,
    validate_episode_replay_receipt,
)


class V212EpisodeReplayReceiptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.game = BoardGame("fixture-c4", 4, 4, k=3, gravity=True)

    def terminal_episode(self):
        actions = (24, 25, 16, 17, 8)
        states = [self.game.initial()]
        for action in actions:
            states.append(self.game.transition(states[-1], action))
        return {
            "game": self.game.name,
            "episode_id": "receipt-terminal-fixture",
            "split": "train",
            "states": tuple(states),
            "actions": actions,
            "outcome": 1,
        }

    def test_receipt_binds_full_replayed_episode_and_all_windows(self):
        episode = self.terminal_episode()
        receipt = build_episode_replay_receipt(episode, self.game)
        self.assertEqual(len(receipt["receipt_sha256"]), 64)
        self.assertEqual(len(receipt["window_records"]), len(episode["actions"]))
        self.assertEqual(
            validate_episode_replay_receipt(receipt, episode, self.game),
            receipt["receipt_sha256"],
        )

    def test_receipt_rejects_changed_episode_or_window_digest(self):
        episode = self.terminal_episode()
        receipt = build_episode_replay_receipt(episode, self.game)
        changed = dict(episode, outcome=-1)
        with self.assertRaisesRegex(ValueError, "outcome does not match terminal rules"):
            validate_episode_replay_receipt(receipt, changed, self.game)

        changed_receipt = copy.deepcopy(receipt)
        changed_receipt["window_records"][0]["payload_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "does not match exact-rule replay"):
            validate_episode_replay_receipt(changed_receipt, episode, self.game)

    def test_receipt_fails_closed_for_illegal_episode_or_unknown_fields(self):
        episode = self.terminal_episode()
        illegal = dict(episode, actions=(0,) + episode["actions"][1:])
        with self.assertRaisesRegex(ValueError, "Illegal action or transition"):
            build_episode_replay_receipt(illegal, self.game)
        with self.assertRaisesRegex(ValueError, "exactly the replay receipt fields"):
            build_episode_replay_receipt(dict(episode, source_path="fixture.json"),
                                         self.game)


if __name__ == "__main__":
    unittest.main()

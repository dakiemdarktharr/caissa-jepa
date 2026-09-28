"""Legal symmetry, pairing and mutation safeguards; no fitting or data scoring."""
from copy import deepcopy
import hashlib
import unittest

import numpy as np

from two_player.games import State
from two_player_v2 import GAMES_V2
from two_player_v21.augmentation import augment, augmentation_plan


def fork_batch(game, root, moves):
    states = [root]
    for action in moves:
        states.append(game.transition(states[-1], action))
    batch = {"x": np.zeros((1, 3, 198)), "valid": np.zeros((1, 3), bool),
             "legal": np.zeros((1, 3, 65), bool), "policy": np.zeros((1, 3, 65)),
             "value": np.zeros((1, 3, 1)), "actions": np.zeros((1, 2, 65)),
             "metadata": {"trajectory": ["fixture"]}}
    for h, state in enumerate(states):
        batch["x"][0, h] = game.features(state)
        batch["valid"][0, h] = True
        legal = list(game.legal_actions(state))
        batch["legal"][0, h, legal] = True
        if legal:
            weight = np.arange(1, len(legal)+1, dtype=float)
            batch["policy"][0, h, legal] = weight/weight.sum()
        outcome = game.terminal(state)
        batch["value"][0, h, 0] = state.player*outcome if outcome is not None else .25*state.player
    for h, action in enumerate(moves):
        batch["actions"][0, h, action] = 1
    return batch, states


class V21AugmentationTests(unittest.TestCase):
    def assert_commutes(self, game, state, actions):
        batch, states = fork_batch(game, state, actions)
        before = deepcopy(batch)
        for transform_id, mapping in enumerate(game.transforms()):
            with self.subTest(game=game.name, transform=transform_id):
                result = augment(batch, [game.name], np.array([transform_id], dtype=np.int64))
                transformed_states = []
                for horizon, original in enumerate(states):
                    transformed, _ = game.transform(original, 64, mapping)
                    transformed_states.append(transformed)
                    np.testing.assert_array_equal(result["x"][0, horizon], game.features(transformed))
                    expected_legal = np.zeros(65, bool)
                    expected_legal[list(game.legal_actions(transformed))] = True
                    np.testing.assert_array_equal(result["legal"][0, horizon], expected_legal)
                    expected_policy = np.zeros(65)
                    for action in game.legal_actions(original):
                        _, changed_action = game.transform(original, action, mapping)
                        expected_policy[changed_action] = batch["policy"][0, horizon, action]
                    np.testing.assert_array_equal(result["policy"][0, horizon], expected_policy)
                    np.testing.assert_array_equal(result["x"][0, horizon, 192:], batch["x"][0, horizon, 192:])
                    self.assertEqual(game.canonical_key(original), game.canonical_key(transformed))
                for h, action in enumerate(actions):
                    _, changed_action = game.transform(states[h], action, mapping)
                    self.assertEqual(int(result["actions"][0, h].argmax()), changed_action)
                    self.assertEqual(game.transition(transformed_states[h], changed_action), transformed_states[h+1])
                np.testing.assert_array_equal(result["value"], batch["value"])
                np.testing.assert_array_equal(result["valid"], batch["valid"])
                np.testing.assert_array_equal(result["x"][~batch["valid"]], batch["x"][~batch["valid"]])
                if len(actions) == 1:
                    np.testing.assert_array_equal(result["actions"][0, 1], np.zeros(65))
                for key in ("x", "valid", "legal", "policy", "value", "actions"):
                    np.testing.assert_array_equal(batch[key], before[key])
                    self.assertFalse(np.shares_memory(batch[key], result[key]))
                result["metadata"]["trajectory"].append("changed")
                self.assertEqual(batch["metadata"], before["metadata"])

    def test_all_gravity_symmetries_commute_with_forks(self):
        game = GAMES_V2["connect4-4x5"]
        self.assertEqual(len(game.transforms()), 2)
        state = game.initial()
        for action in (24, 28, 25, 20):
            state = game.transition(state, action)
        self.assert_commutes(game, state, [26, 12])

    def test_all_reversi_dihedral_symmetries_commute_with_forks(self):
        game = GAMES_V2["reversi6"]
        self.assertEqual(len(game.transforms()), 8)
        state = game.initial()
        rng = np.random.default_rng(512)
        for _ in range(8):
            state = game.transition(state, int(rng.choice(game.legal_actions(state))))
        own = game.legal_actions(state)[0]
        child = game.transition(state, own)
        reply = game.legal_actions(child)[-1]
        self.assert_commutes(game, state, [own, reply])

    def test_terminal_child_missing_h2_remains_zero(self):
        game = GAMES_V2["connect4-4x5"]
        state = game.initial()
        for action in (24, 28, 25, 20, 26, 12):
            state = game.transition(state, action)
        self.assertEqual(game.terminal(game.transition(state, 27)), 1)
        self.assert_commutes(game, state, [27])

    def test_forced_pass_retains_64_for_every_dihedral_symmetry(self):
        game = GAMES_V2["reversi6"]
        state = State((0, 1, -1, -1, -1, -1)+(-1,)*30, 1)
        self.assertEqual(game.legal_actions(state), (64,))
        child = game.transition(state, 64)
        self.assertEqual(game.legal_actions(child), (0,))
        self.assert_commutes(game, state, [64, 0])

    def test_plan_matches_frozen_rng_namespace_and_draw_order(self):
        forks = [{"game": "connect4-4x5", "split": "train"}, {"game": "reversi6", "split": "train"}]
        indices = np.array([1, 0, 1, 1, 0]*100, dtype=np.int64)
        transforms, receipt = augmentation_plan(forks, indices, 17, 3)
        expected_rng = np.random.default_rng(np.random.SeedSequence([17, 3, 2211]))
        expected = np.array([expected_rng.integers(8 if i == 1 else 2) for i in indices], dtype=np.int64)
        np.testing.assert_array_equal(transforms, expected)
        again, same = augmentation_plan(forks, indices, 17, 3)
        np.testing.assert_array_equal(transforms, again)
        self.assertEqual(receipt, same)
        self.assertEqual(receipt["transform_sha256"], hashlib.sha256(expected.astype("<i8").tobytes()).hexdigest())
        self.assertEqual(sum(receipt["transform_counts"].values()), len(indices))
        self.assertEqual(set(transforms[indices == 1]), set(range(8)))
        changed, _ = augmentation_plan(forks, indices, 17, 4)
        self.assertFalse(np.array_equal(transforms, changed))

    def test_batch_mixes_games_without_crossing_rows(self):
        batches = []
        names = []
        for game in GAMES_V2.values():
            state = game.initial()
            a = game.legal_actions(state)[0]
            b = game.legal_actions(game.transition(state, a))[0]
            batch, _ = fork_batch(game, state, [a, b])
            batches.append(batch)
            names.append(game.name)
        keys = ("x", "valid", "legal", "policy", "value", "actions")
        joined = {key: np.concatenate([b[key] for b in batches]) for key in keys}
        together = augment(joined, names, np.array([1, 7]))
        for row, transform in enumerate((1, 7)):
            alone = augment(batches[row], [names[row]], np.array([transform]))
            for key in keys:
                np.testing.assert_array_equal(together[key][row], alone[key][0])

    def test_invalid_schedules_and_nontraining_forks_are_rejected(self):
        game = GAMES_V2["connect4-4x5"]
        state = game.initial()
        batch, _ = fork_batch(game, state, [24, 28])
        for transforms in (np.array([2]), np.array([-1]), np.array([1.0]), np.array([True]), np.array([0, 1])):
            with self.assertRaises(ValueError):
                augment(batch, [game.name], transforms)
        with self.assertRaises(ValueError):
            augment(batch, ["reversi6"], np.array([0]))
        for split in ("development", "selection", "final"):
            with self.assertRaises(ValueError):
                augmentation_plan([{"game": game.name, "split": split}], np.array([0]), 17, 0)
        for indices in (np.array([-1]), np.array([1]), np.array([0.0]), np.array([True])):
            with self.assertRaises(ValueError):
                augmentation_plan([{"game": game.name, "split": "train"}], indices, 17, 0)


if __name__ == "__main__":
    unittest.main()
